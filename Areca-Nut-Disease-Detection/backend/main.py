from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime, timedelta
import random
import io
from PIL import Image
import json

# Import live price fetcher
try:
    from price_fetcher import PriceFetcher
    LIVE_PRICES_AVAILABLE = True
except ImportError:
    LIVE_PRICES_AVAILABLE = False
    print("Warning: price_fetcher module not found. Using mock data only.")

# Import CNN model
try:
    from model import get_model, is_model_available
    CNN_MODEL_AVAILABLE = is_model_available()
except ImportError:
    CNN_MODEL_AVAILABLE = False
    print("Warning: model module not found. Using mock disease detection.")

app = FastAPI(title="Arecanut Agri Assistant API", version="1.0.0")

# Initialize price fetcher
if LIVE_PRICES_AVAILABLE:
    price_fetcher = PriceFetcher()
    print("[OK] Live government price API integration enabled")
else:
    price_fetcher = None
    print("[WARN] Using mock price data only")

# Initialize CNN model
if CNN_MODEL_AVAILABLE:
    disease_model = get_model()
    print("[OK] CNN disease detection model loaded")
else:
    disease_model = None
    print("[WARN] Using mock disease detection")

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==================== DATA MODELS ====================

class GuidanceRequest(BaseModel):
    soil_type: Optional[str] = None
    rainfall_mm: Optional[float] = None
    fertilizer_used: Optional[str] = None
    plant_age_months: Optional[int] = None
    previous_yield_kg: Optional[float] = None

# ==================== MOCK DATA ====================

# Disease database - Updated with actual 9 training classes
DISEASES = {
    "bud_borer": {
        "name": "Bud Borer",
        "severity": "high",
        "symptoms": [
            "Holes in young buds",
            "Wilting of growing tips",
            "Damaged spindle leaves",
            "Larvae visible in bud"
        ],
        "description": "Pest damage caused by borer insects attacking the growing bud, leading to severe damage.",
        "treatment": [
            "Apply insecticides like Quinalphos",
            "Remove and destroy infected buds",
            "Use pheromone traps",
            "Inject insecticide into bud if possible",
            "Regular monitoring and early detection"
        ]
    },
    "healthy_foot": {
        "name": "Healthy Foot/Base",
        "severity": "none",
        "symptoms": [
            "Strong, firm trunk base",
            "No discoloration",
            "No cracks or lesions",
            "Normal growth"
        ],
        "description": "The foot/base of the arecanut palm appears healthy with no signs of disease or damage.",
        "treatment": [
            "Continue regular care",
            "Maintain proper drainage",
            "Monitor for any changes",
            "Keep area clean and weed-free",
            "Regular inspection"
        ]
    },
    "healthy_leaf": {
        "name": "Healthy Leaf",
        "severity": "none",
        "symptoms": [
            "Vibrant green color",
            "No spots or discoloration",
            "Normal leaf structure",
            "Good turgor pressure"
        ],
        "description": "The arecanut leaf appears healthy with no signs of disease or pest damage.",
        "treatment": [
            "Continue regular fertilization",
            "Maintain proper irrigation",
            "Monitor for early disease signs",
            "Keep field sanitation",
            "Preventive sprays during monsoon"
        ]
    },
    "healthy_nut": {
        "name": "Healthy Nut",
        "severity": "none",
        "symptoms": [
            "Normal nut development",
            "No splitting or cracking",
            "Good size and color",
            "Firm texture"
        ],
        "description": "The arecanut fruit/nut appears healthy with proper development and no disease signs.",
        "treatment": [
            "Continue proper care",
            "Maintain balanced nutrition",
            "Adequate water supply",
            "Monitor for pest damage",
            "Harvest at proper maturity"
        ]
    },
    "healthy_trunk": {
        "name": "Healthy Trunk",
        "severity": "none",
        "symptoms": [
            "Clean, smooth bark",
            "No bleeding or oozing",
            "No cracks or lesions",
            "Uniform color"
        ],
        "description": "The trunk of the arecanut palm appears healthy with no signs of disease or damage.",
        "treatment": [
            "Regular inspection",
            "Avoid mechanical damage",
            "Maintain field hygiene",
            "Proper nutrition",
            "Monitor for any changes"
        ]
    },
    "mahali_koleroga": {
        "name": "Mahali Koleroga (Fruit Rot)",
        "severity": "high",
        "symptoms": [
            "Water-soaked lesions on nuts",
            "White fungal growth",
            "Premature nut drop",
            "Rotting of fruits",
            "Rapid spread during monsoon"
        ],
        "description": "Serious fungal disease causing severe fruit rot, especially during rainy season. Can lead to significant yield loss.",
        "treatment": [
            "Spray Bordeaux mixture (1%) before monsoon",
            "Use Copper Oxychloride (0.25%) at 15-day intervals",
            "Improve field drainage",
            "Remove and destroy infected nuts",
            "Ensure proper air circulation"
        ]
    },
    "stem_cracking": {
        "name": "Stem Cracking",
        "severity": "medium",
        "symptoms": [
            "Vertical or horizontal cracks on stem",
            "Bark splitting",
            "Exposed inner tissue",
            "Possible secondary infections"
        ],
        "description": "Physical damage or disease causing cracks in the stem, making the palm vulnerable to infections.",
        "treatment": [
            "Apply Bordeaux paste on cracks",
            "Ensure proper nutrition (especially boron)",
            "Improve water management",
            "Protect from mechanical damage",
            "Apply wound sealants"
        ]
    },
    "stem_bleeding": {
        "name": "Stem Bleeding",
        "severity": "medium",
        "symptoms": [
            "Dark brown patches on stem",
            "Oozing of reddish-brown liquid",
            "Cracking of bark",
            "Yellowing of leaves in severe cases"
        ],
        "description": "Fungal disease causing bleeding lesions on the stem, weakening the palm structure.",
        "treatment": [
            "Scrape affected area and apply Bordeaux paste",
            "Root feeding with Tridemorph (2ml per liter)",
            "Improve soil drainage",
            "Avoid injury to stem during cultivation",
            "Apply systemic fungicides"
        ]
    },
    "yellow_leaf_disease": {
        "name": "Yellow Leaf Disease (YLD)",
        "severity": "high",
        "symptoms": [
            "Yellowing of leaves starting from tips",
            "Stunted growth",
            "Premature nut fall",
            "Reduced vigor"
        ],
        "description": "A phytoplasma disease causing yellowing of leaves and significant yield loss. Transmitted by insects.",
        "treatment": [
            "Remove and destroy infected plants immediately",
            "Apply root feeding with Tetracycline (0.5g per plant)",
            "Control insect vectors using approved insecticides",
            "Maintain field sanitation",
            "Use disease-free planting material"
        ]
    },
    # Legacy entries for backward compatibility
    "yellow_leaf": {
        "name": "Yellow Leaf Disease (YLD)",
        "severity": "high",
        "symptoms": [
            "Yellowing of leaves starting from tips",
            "Stunted growth",
            "Premature nut fall",
            "Reduced vigor"
        ],
        "description": "A phytoplasma disease causing yellowing of leaves and significant yield loss. Transmitted by insects.",
        "treatment": [
            "Remove and destroy infected plants immediately",
            "Apply root feeding with Tetracycline (0.5g per plant)",
            "Control insect vectors using approved insecticides",
            "Maintain field sanitation",
            "Use disease-free planting material"
        ]
    },
    "koleroga": {
        "name": "Koleroga (Fruit Rot)",
        "severity": "high",
        "symptoms": [
            "Water-soaked lesions on nuts",
            "White fungal growth on surface",
            "Premature nut drop",
            "Rotting of young fruits"
        ],
        "description": "Fungal disease causing severe fruit rot during monsoon season, leading to significant crop loss.",
        "treatment": [
            "Spray Bordeaux mixture (1%) before monsoon",
            "Use Copper Oxychloride (0.25%) at 15-day intervals",
            "Improve field drainage",
            "Remove infected nuts immediately",
            "Ensure proper air circulation"
        ]
    },
    "bud_rot": {
        "name": "Bud Rot",
        "severity": "high",
        "symptoms": [
            "Rotting of the spindle leaf",
            "Drooping of younger leaves",
            "Foul smell from growing point",
            "Crown rotting in advanced stages"
        ],
        "description": "Serious disease affecting the growing point of the palm, often fatal if not treated early.",
        "treatment": [
            "Remove infected spindle and apply Bordeaux paste",
            "Spray Metalaxyl + Mancozeb (0.25%)",
            "Ensure proper drainage around palm",
            "Avoid overhead irrigation",
            "Apply preventive fungicide sprays"
        ]
    },
    "leaf_spot": {
        "name": "Leaf Spot Disease",
        "severity": "low",
        "symptoms": [
            "Circular brown spots on leaves",
            "Leaf yellowing around spots",
            "Premature leaf fall",
            "Reduced photosynthesis"
        ],
        "description": "Common fungal disease causing spotting on leaves, usually manageable with proper care.",
        "treatment": [
            "Spray Mancozeb (0.25%) or Copper Oxychloride",
            "Remove and destroy infected leaves",
            "Maintain proper plant spacing for air circulation",
            "Apply balanced fertilization",
            "Avoid overhead watering"
        ]
    },
    "stem_bleeding": {
        "name": "Stem Bleeding",
        "severity": "medium",
        "symptoms": [
            "Dark brown patches on stem",
            "Oozing of reddish-brown liquid",
            "Cracking of bark",
            "Yellowing of leaves in severe cases"
        ],
        "description": "Fungal disease causing bleeding lesions on the stem, weakening the palm structure.",
        "treatment": [
            "Scrape affected area and apply Bordeaux paste",
            "Root feeding with Tridemorph (2ml per liter)",
            "Improve soil drainage",
            "Avoid injury to stem during cultivation",
            "Apply systemic fungicides"
        ]
    },
    "healthy": {
        "name": "Healthy Plant",
        "severity": "none",
        "symptoms": [
            "Vibrant green leaves",
            "No discoloration or spots",
            "Normal growth pattern",
            "Healthy nut development"
        ],
        "description": "Your arecanut plant appears healthy with no signs of disease. Continue regular maintenance.",
        "treatment": [
            "Continue regular fertilization schedule",
            "Maintain proper irrigation",
            "Monitor for early disease symptoms",
            "Keep field clean and weed-free",
            "Apply preventive sprays during monsoon"
        ]
    },
    "anabe_roga": {
        "name": "Anabe Roga (Mahali)",
        "severity": "medium",
        "symptoms": [
            "Small brown lesions on nuts",
            "Nut splitting and cracking",
            "Reduced nut quality",
            "Premature nut fall"
        ],
        "description": "A disease affecting nut quality, causing splitting and premature dropping of nuts.",
        "treatment": [
            "Spray Bordeaux mixture during flowering",
            "Improve field drainage",
            "Remove infected nuts",
            "Apply copper-based fungicides",
            "Maintain proper nutrition"
        ]
    },
    "mahali": {
        "name": "Mahali Disease",
        "severity": "high",
        "symptoms": [
            "Necrotic lesions on leaves",
            "Premature leaf yellowing",
            "Stunted plant growth",
            "Reduced nut production"
        ],
        "description": "Serious disease affecting overall plant health and productivity.",
        "treatment": [
            "Remove and destroy infected plant parts",
            "Apply systemic fungicides",
            "Improve plant nutrition",
            "Ensure adequate spacing",
            "Monitor and control insect vectors"
        ]
    },
    "inflorescence_dieback": {
        "name": "Inflorescence Dieback",
        "severity": "high",
        "symptoms": [
            "Browning of flower clusters",
            "Drying of inflorescence",
            "Failure of nut setting",
            "Complete drying of flower stalks"
        ],
        "description": "Disease affecting flowering structures, leading to significant yield loss.",
        "treatment": [
            "Spray fungicides during flowering season",
            "Remove infected inflorescence",
            "Improve air circulation",
            "Apply balanced fertilization",
            "Control insect pests"
        ]
    }
}

# No hardcoded market data - using live API only

# ==================== HELPER FUNCTIONS ====================
# (Using live API data - no mock price generation needed)

def detect_disease_from_image(image: Image.Image) -> dict:
    """
    Detect disease using CNN model or fallback to mock detection
    """
    # Try using CNN model first
    if CNN_MODEL_AVAILABLE and disease_model:
        try:
            # Use CNN model for prediction
            prediction = disease_model.predict(image)
            disease_key = prediction["disease_key"]
            confidence = prediction["confidence"]
            
            # Get disease info from database
            if disease_key in DISEASES:
                disease_info = DISEASES[disease_key]
                
                return {
                    "disease_name": disease_info["name"],
                    "confidence": confidence,
                    "severity": disease_info["severity"],
                    "symptoms": disease_info["symptoms"],
                    "description": disease_info["description"],
                    "treatment": disease_info["treatment"],
                    "model_type": "CNN",
                    "top_predictions": prediction.get("top_predictions", [])
                }
        except Exception as e:
            print(f"CNN model prediction failed: {e}. Falling back to mock detection.")
    
    # Fallback: Mock disease detection
    # Analyze image characteristics
    width, height = image.size
    
    # Convert to RGB if needed
    if image.mode != 'RGB':
        image = image.convert('RGB')
    
    # Get average color to simulate analysis
    pixels = list(image.getdata())
    avg_color = [sum(x) / len(pixels) for x in zip(*pixels)]
    
    # Calculate "health score" based on green dominance
    green_ratio = avg_color[1] / sum(avg_color) if sum(avg_color) > 0 else 0
    
    # Simulate disease detection
    if green_ratio > 0.38:
        disease_key = "healthy"
        confidence = random.uniform(0.75, 0.95)
    elif green_ratio < 0.30:
        diseases_list = ["yellow_leaf", "leaf_spot", "stem_bleeding"]
        disease_key = random.choice(diseases_list)
        confidence = random.uniform(0.65, 0.85)
    else:
        diseases_list = ["koleroga", "bud_rot", "leaf_spot"]
        disease_key = random.choice(diseases_list)
        confidence = random.uniform(0.60, 0.80)
    
    disease_info = DISEASES[disease_key]
    
    return {
        "disease_name": disease_info["name"],
        "confidence": round(confidence, 2),
        "severity": disease_info["severity"],
        "symptoms": disease_info["symptoms"],
        "description": disease_info["description"],
        "treatment": disease_info["treatment"],
        "model_type": "mock"
    }

# ==================== API ENDPOINTS ====================

@app.get("/")
async def root():
    return {
        "message": "Arecanut Agri Assistant API",
        "version": "1.0.0",
        "status": "running"
    }

@app.get("/api/v1/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "service": "Arecanut Agri Assistant API",
        "live_prices_enabled": LIVE_PRICES_AVAILABLE,
        "cnn_model_enabled": CNN_MODEL_AVAILABLE
    }

# ==================== PRICE ENDPOINTS ====================

@app.get("/api/v1/prices/current")
async def get_current_prices(
    market: Optional[str] = None, 
    state: Optional[str] = None
):
    """Get current market prices - tries live govt API first, falls back to reference data"""
    current_date = datetime.now()
    prices = []
    
    if LIVE_PRICES_AVAILABLE and price_fetcher:
        try:
            # Use get_cached_or_fetch: tries data.gov.in → Agmarknet scrape → static fallback
            live_prices = price_fetcher.get_cached_or_fetch(state=state)
            
            if live_prices:
                for price_data in live_prices:
                    # Filter by market if specified
                    if market and price_data.get("market", "").lower() != market.lower():
                        continue
                    
                    # Add trend calculation
                    price_data["trend"] = "stable"
                    price_data["region"] = price_data.get("district", "Unknown")
                    price_data["date"] = current_date.strftime("%Y-%m-%d")
                    
                    prices.append(price_data)
                
                if prices:
                    # Determine overall source label
                    sources = set(p.get("source", "") for p in prices)
                    if "data.gov.in" in sources:
                        data_source = "live_government_api"
                    elif "agmarknet.gov.in" in sources:
                        data_source = "live_agmarknet_scrape"
                    else:
                        data_source = "reference_data"

                    return {
                        "success": True,
                        "data": prices,
                        "count": len(prices),
                        "source": data_source
                    }
        except Exception as e:
            print(f"Error fetching prices: {e}")
    
    # Fallback: always use static reference prices so the app never returns 404
    if not prices:
        from price_fetcher import _static_prices
        static = _static_prices(state)
        if market:
            static = [p for p in static if p.get("market", "").lower() == market.lower()]
        current_date_str = datetime.now().strftime("%Y-%m-%d")
        for p in static:
            p["trend"] = "stable"
            p["region"] = p.get("district", "Unknown")
            p["date"] = current_date_str
        if not static:
            raise HTTPException(status_code=404, detail="No price data for that market.")
        return {
            "success": True,
            "data": static,
            "count": len(static),
            "source": "reference_data"
        }

    return {
        "success": True,
        "data": prices,
        "count": len(prices),
        "source": "reference_data"
    }

@app.get("/api/v1/prices/history/{market}")
async def get_price_history(market: str, days: int = 7):
    """Get price history for a specific market from live API"""
    # First get current price for this market
    current_price = None
    market_state = None
    
    if LIVE_PRICES_AVAILABLE and price_fetcher:
        try:
            live_prices = price_fetcher.get_cached_or_fetch()
            for price_data in live_prices:
                if price_data.get("market", "").lower() == market.lower():
                    current_price = price_data.get("price", 0)
                    market_state = price_data.get("state", "Unknown")
                    break
        except Exception as e:
            print(f"Error fetching price for history: {e}")
    
    if not current_price:
        raise HTTPException(status_code=404, detail=f"Market '{market}' not found in live data")
    
    # Generate historical trend based on current live price
    # Note: Government API doesn't provide historical data, so we simulate trend
    history = []
    current_date = datetime.now()
    
    for i in range(days):
        date = current_date - timedelta(days=i)
        # Simulate slight variation for historical data
        variation = random.uniform(-0.03, 0.03)
        historical_price = int(current_price * (1 + variation))
        
        history.append({
            "date": date.strftime("%Y-%m-%d"),
            "day_name": date.strftime("%a"),
            "price": historical_price,
            "price_per_kg": round(historical_price / 100, 2)
        })
    
    # Reverse to show oldest first
    history.reverse()
    
    return {
        "success": True,
        "market": market,
        "state": market_state,
        "data": history
    }

@app.get("/api/v1/prices/markets")
async def get_available_markets():
    """
    Get all available markets grouped by state — built from LIVE price data.
    Returns real market names so the frontend dropdowns always match actual records.
    """
    if LIVE_PRICES_AVAILABLE and price_fetcher:
        try:
            # Fetch all live prices (no state filter → all states)
            all_prices = price_fetcher.get_cached_or_fetch()

            if all_prices:
                # Build state → sorted unique market names from actual live data
                markets_by_state: dict = {}
                for p in all_prices:
                    state  = p.get("state", "Unknown")
                    market = p.get("market", "Unknown")
                    if state not in markets_by_state:
                        markets_by_state[state] = set()
                    markets_by_state[state].add(market)

                # Convert sets to sorted lists
                markets_by_state = {
                    state: sorted(list(mkts))
                    for state, mkts in sorted(markets_by_state.items())
                }

                # Determine source label
                src = all_prices[0].get("source", "reference_data")
                source_label = (
                    "live_government_api"   if src == "data.gov.in"       else
                    "live_agmarknet_scrape" if src == "agmarknet.gov.in"  else
                    "reference_data"
                )

                return {
                    "success": True,
                    "data": markets_by_state,
                    "source": source_label,
                    "total_markets": sum(len(v) for v in markets_by_state.values())
                }
        except Exception as e:
            print(f"Error fetching markets: {e}")

    # Fallback: always build market list from static reference data
    from price_fetcher import _static_prices, STATIC_PRICES
    static_markets: dict = {}
    for item in STATIC_PRICES:
        s = item["state"]
        m = item["market"]
        if s not in static_markets:
            static_markets[s] = set()
        static_markets[s].add(m)
    static_markets = {
        s: sorted(list(mkts))
        for s, mkts in sorted(static_markets.items())
    }
    return {
        "success": True,
        "data": static_markets,
        "source": "reference_data",
        "total_markets": sum(len(v) for v in static_markets.values())
    }


@app.delete("/api/v1/prices/cache")
async def clear_price_cache():
    """Force-clear the price cache so the next request fetches fresh live data"""
    import os
    cache_cleared = False
    try:
        cache_path = os.path.join(os.path.dirname(__file__), "price_cache.json")
        if not os.path.exists(cache_path):
            cache_path = "price_cache.json"   # fallback: relative
        if os.path.exists(cache_path):
            os.remove(cache_path)
            cache_cleared = True
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Could not clear cache: {e}")
    return {
        "success": True,
        "cache_cleared": cache_cleared,
        "message": "Cache cleared. Next /api/v1/prices/current call will fetch live data."
    }

@app.get("/api/v1/prices/comparison")
async def get_price_comparison():
    """Get price comparison across markets from live API"""
    current_date = datetime.now()
    prices = []
    
    if LIVE_PRICES_AVAILABLE and price_fetcher:
        try:
            live_prices = price_fetcher.get_cached_or_fetch()
            for price_data in live_prices:
                prices.append({
                    "market": price_data.get("market", "Unknown"),
                    "state": price_data.get("state", "Unknown"),
                    "price": price_data.get("price", 0)
                })
        except Exception as e:
            print(f"Error fetching prices for comparison: {e}")
    
    if not prices:
        raise HTTPException(status_code=404, detail="No live price data available")
    
    # Calculate statistics
    price_values = [p["price"] for p in prices]
    highest = max(prices, key=lambda x: x["price"])
    lowest = min(prices, key=lambda x: x["price"])
    average = sum(price_values) / len(price_values)
    
    return {
        "success": True,
        "data": {
            "highest": highest,
            "lowest": lowest,
            "average": int(average),
            "total_markets": len(prices),
            "date": current_date.strftime("%Y-%m-%d")
        }
    }

# ==================== DISEASE DETECTION ENDPOINT ====================

@app.post("/api/v1/disease/detect")
async def detect_disease(image: UploadFile = File(...)):
    """Detect disease from uploaded image"""
    
    # Validate file type
    if not image.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File must be an image")
    
    try:
        # Read image
        contents = await image.read()
        img = Image.open(io.BytesIO(contents))
        
        # Detect disease
        result = detect_disease_from_image(img)
        
        return {
            "success": True,
            **result
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing image: {str(e)}")

# ==================== GUIDANCE ENDPOINT ====================

@app.post("/api/v1/guidance/predict")
async def get_guidance(request: GuidanceRequest):
    """Get farming guidance based on parameters"""
    
    # Mock recommendation logic
    recommendations = {
        "fertilizer": "NPK 100:40:140",
        "dosage_kg": 0.28,
        "irrigation_liters": 25,
        "note": "Apply in 3 splits: May, September, and January"
    }
    
    # Adjust based on inputs
    if request.plant_age_months:
        if request.plant_age_months < 36:
            recommendations["fertilizer"] = "NPK 50:20:70"
            recommendations["dosage_kg"] = 0.15
            recommendations["note"] = "Young plant - reduced dosage recommended"
        elif request.plant_age_months > 120:
            recommendations["fertilizer"] = "NPK 120:50:160"
            recommendations["dosage_kg"] = 0.32
            recommendations["note"] = "Mature plant - higher dosage for better yield"
    
    if request.rainfall_mm:
        if request.rainfall_mm < 1000:
            recommendations["irrigation_liters"] = 40
        elif request.rainfall_mm > 3000:
            recommendations["irrigation_liters"] = 15
    
    return {
        "success": True,
        "recommendation": recommendations
    }

# ==================== DISEASES INFO ENDPOINT ====================

@app.get("/api/v1/diseases")
async def get_all_diseases():
    """Get information about all diseases"""
    return {
        "success": True,
        "data": DISEASES
    }

@app.get("/api/v1/diseases/{disease_key}")
async def get_disease_info(disease_key: str):
    """Get information about a specific disease"""
    if disease_key not in DISEASES:
        raise HTTPException(status_code=404, detail="Disease not found")
    
    return {
        "success": True,
        "data": DISEASES[disease_key]
    }

# ==================== MODEL INFO ENDPOINT ====================

@app.get("/api/v1/model/info")
async def get_model_info():
    """Get information about the loaded CNN model"""
    if not CNN_MODEL_AVAILABLE or not disease_model:
        return {
            "success": False,
            "model_loaded": False,
            "message": "CNN model not available. Using mock disease detection."
        }
    
    try:
        model_info = disease_model.get_model_info()
        return {
            "success": True,
            "model_loaded": True,
            **model_info
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
