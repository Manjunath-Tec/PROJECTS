# 🌿 Arecanut Agri Assistant

A smart farming web application for **arecanut (betel nut) farmers** in India. It combines a CNN-based plant disease detection model with live market price tracking and agronomic guidance — all in a clean, mobile-friendly web interface.

---

## 📋 Table of Contents

- [Features](#-features)
- [How It Works](#-how-it-works)
- [Project Structure](#-project-structure)
- [Tech Stack](#-tech-stack)
- [Prerequisites](#-prerequisites)
- [Installation & Setup](#-installation--setup)
- [Running the Application](#-running-the-application)
- [API Reference](#-api-reference)
- [CNN Disease Model](#-cnn-disease-model)
- [Dataset](#-dataset)
- [Known Limitations](#-known-limitations)
- [Contributing](#-contributing)
- [License](#-license)

---

## ✨ Features

| Feature | Description |
|---|---|
| 🔬 **Disease Detection** | Upload a photo of your arecanut plant; the system identifies diseases and recommends treatment |
| 💰 **Live Market Prices** | Real-time arecanut market prices across Karnataka, Kerala, and Assam |
| 📊 **Price History & Comparison** | View 7-day trends and compare prices across markets |
| 🌱 **Farming Guidance** | Get NPK fertilizer dosage and irrigation recommendations based on plant age, soil type, and rainfall |
| 📱 **Responsive UI** | Works on desktop and mobile browsers |
| 🔔 **Notifications Page** | Dedicated alerts and updates dashboard |

---

## 🔄 How It Works

```
User (Browser)
     │
     ▼
Frontend (HTML + CSS + JS)          ← Served on port 3000
     │   REST API calls via fetch()
     ▼
Backend (FastAPI / Python)          ← Runs on port 8000
     ├── Disease Detection
     │       ├── CNN model (TensorFlow .h5) — if TF installed
     │       └── Fallback: color-analysis mock detection
     ├── Market Prices
     │       ├── data.gov.in / Agmarknet API (live)
     │       └── Fallback: curated static market data
     └── Farming Guidance
             └── Rule-based NPK + irrigation calculator
```

### Disease Detection Flow

1. User uploads a plant image via the frontend.
2. Frontend `POST`s the image to `/api/v1/disease/detect`.
3. Backend tries the **TensorFlow CNN model** (`best_arecanut_fast_model.h5`).
4. If TensorFlow is unavailable, falls back to a **color-analysis heuristic**.
5. Returns disease name, confidence score, severity, symptoms, and treatment.

### Price Data Flow

1. Frontend requests `/api/v1/prices/current`.
2. Backend attempts to fetch from the **data.gov.in government API**.
3. If the API is unreachable, uses a **curated fallback dataset** of real arecanut markets.

---

## 📁 Project Structure

```
BBLM/
├── START_APP.bat               ← One-click launcher (starts both servers + opens browser)
├── train_model.py              ← CNN model training script
├── .gitignore
├── README.md
│
├── backend/
│   ├── main.py                 ← FastAPI application (all API routes)
│   ├── model.py                ← CNN model loader and inference wrapper
│   ├── price_fetcher.py        ← Government API integration + fallback data
│   ├── requirements.txt        ← Python dependencies
│   ├── start_server.bat        ← Start backend only
│   └── best_arecanut_fast_model.h5  ← Trained CNN weights (not in git, see below)
│
├── frontend/
│   ├── index.html              ← Main application page
│   ├── notifications.html      ← Notifications / alerts page
│   ├── app.js                  ← All frontend logic (disease, prices, guidance)
│   ├── styles.css              ← Full stylesheet
│   ├── config.js               ← API base URL and endpoint configuration
│   └── start_frontend.bat      ← Start frontend server only
│
└── Dataset/                    ← Training images (not in git — large files)
    ├── Arecanut_dataset/
    └── final_testing-*/
```

> **Note:** `best_arecanut_fast_model.h5` and the `Dataset/` folder are excluded from git (`.gitignore`) because they are large binary files. See [CNN Disease Model](#-cnn-disease-model) for how to obtain or train the model.

---

## 🛠 Tech Stack

### Backend
- **Python 3.10+**
- **FastAPI** — REST API framework
- **Uvicorn** — ASGI server
- **TensorFlow / Keras** — CNN model inference *(optional)*
- **Pillow** — Image processing
- **Requests** — Government API calls

### Frontend
- **Vanilla HTML5 / CSS3 / JavaScript** — No framework dependencies
- **Fetch API** — REST calls to backend
- **Python `http.server`** — Simple static file server for local development

---

## 🔧 Prerequisites

- **Python 3.10, 3.11, or 3.12** — *Recommended*
  - Python 3.13+ works for all features **except** CNN model inference (TensorFlow is not yet compatible)
- **pip** (comes with Python)
- A modern web browser (Chrome, Firefox, Edge)

Check your Python version:
```bash
python --version
```

---

## 📦 Installation & Setup

### 1. Clone the repository

```bash
git clone https://github.com/<your-username>/BBLM.git
cd BBLM
```

### 2. (Recommended) Create a virtual environment

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS / Linux
python3 -m venv venv
source venv/bin/activate
```

### 3. Install backend dependencies

```bash
cd backend
pip install -r requirements.txt
```

### 4. (Optional) Enable CNN disease detection

CNN inference requires TensorFlow, which supports **Python ≤ 3.12**.

```bash
pip install tensorflow==2.15.0
```

Then place the trained model file inside the `backend/` folder:
```
backend/best_arecanut_fast_model.h5
```

If you don't have the `.h5` file, you can train it yourself — see [CNN Disease Model](#-cnn-disease-model).

---

## ▶️ Running the Application

### Option A — One-click launcher (Windows)

Double-click **`START_APP.bat`** in the project root.

It will:
1. Detect your Python installation
2. Install missing dependencies automatically
3. Start the backend on **port 8000**
4. Start the frontend on **port 3000**
5. Open your browser at `http://localhost:3000`

---

### Option B — Manual (any OS)

**Terminal 1 — Start the backend:**
```bash
cd backend
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

**Terminal 2 — Start the frontend:**
```bash
cd frontend
python -m http.server 3000
```

**Open in browser:**
```
http://localhost:3000
```

---

### URLs at a glance

| Service | URL |
|---|---|
| Frontend App | http://localhost:3000 |
| Backend API | http://localhost:8000 |
| Interactive API Docs (Swagger) | http://localhost:8000/docs |
| Alternative API Docs (ReDoc) | http://localhost:8000/redoc |

---

## 📡 API Reference

All endpoints are prefixed with `/api/v1`.

### Health

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/v1/health` | Returns server status and feature flags |

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2024-01-01T12:00:00",
  "live_prices_enabled": true,
  "cnn_model_enabled": false
}
```

---

### Disease Detection

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/v1/disease/detect` | Upload plant image, get disease diagnosis |
| `GET` | `/api/v1/diseases` | List all diseases in the database |
| `GET` | `/api/v1/diseases/{disease_key}` | Get info for a specific disease |
| `GET` | `/api/v1/model/info` | CNN model metadata |

**POST `/api/v1/disease/detect`**

Request: `multipart/form-data` with field `image` (any image format).

```bash
curl -X POST http://localhost:8000/api/v1/disease/detect \
  -F "image=@my_plant_photo.jpg"
```

Response:
```json
{
  "success": true,
  "disease_name": "Mahali Koleroga (Fruit Rot)",
  "confidence": 0.87,
  "severity": "high",
  "model_type": "CNN",
  "symptoms": ["Water-soaked lesions on nuts", "Premature nut drop"],
  "description": "Serious fungal disease...",
  "treatment": ["Spray Bordeaux mixture (1%) before monsoon", "..."]
}
```

**Detectable Disease Classes (CNN model):**

| Key | Display Name | Severity |
|---|---|---|
| `healthy_leaf` | Healthy Leaf | None |
| `healthy_nut` | Healthy Nut | None |
| `healthy_trunk` | Healthy Trunk | None |
| `healthy_foot` | Healthy Foot/Base | None |
| `bud_borer` | Bud Borer | High |
| `mahali_koleroga` | Mahali Koleroga (Fruit Rot) | High |
| `yellow_leaf_disease` | Yellow Leaf Disease (YLD) | High |
| `stem_bleeding` | Stem Bleeding | Medium |
| `stem_cracking` | Stem Cracking | Medium |

---

### Market Prices

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/v1/prices/current` | Current prices (filter by `?market=` or `?state=`) |
| `GET` | `/api/v1/prices/history/{market}` | 7-day price history for a market |
| `GET` | `/api/v1/prices/markets` | All available markets grouped by state |
| `GET` | `/api/v1/prices/comparison` | Highest / lowest / average across all markets |

**Example:**
```bash
# Prices for Karnataka only
curl "http://localhost:8000/api/v1/prices/current?state=Karnataka"

# 7-day history for Shimoga
curl "http://localhost:8000/api/v1/prices/history/Shimoga"
```

---

### Farming Guidance

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/v1/guidance/predict` | Get fertilizer + irrigation recommendations |

**Request body (JSON):**
```json
{
  "soil_type": "laterite",
  "rainfall_mm": 2500,
  "plant_age_months": 60,
  "fertilizer_used": "NPK",
  "previous_yield_kg": 8.5
}
```

**Response:**
```json
{
  "success": true,
  "recommendation": {
    "fertilizer": "NPK 100:40:140",
    "dosage_kg": 0.28,
    "irrigation_liters": 25,
    "note": "Apply in 3 splits: May, September, and January"
  }
}
```

---

## 🤖 CNN Disease Model

The model is a **Convolutional Neural Network (CNN)** trained on arecanut plant images to classify 9 conditions (4 healthy, 5 diseases).

### Model Details

| Parameter | Value |
|---|---|
| Architecture | Custom CNN (Keras Sequential) |
| Input size | 224 × 224 × 3 (RGB) |
| Output classes | 9 |
| File | `best_arecanut_fast_model.h5` |
| Framework | TensorFlow / Keras |

### Training the Model Yourself

If you have the dataset, run:

```bash
python train_model.py
```

This will:
- Load images from `Dataset/Arecanut_dataset/`
- Train the CNN
- Save the best weights to `best_arecanut_fast_model.h5`

### Model Not Available?

Without the `.h5` file or TensorFlow, the app **still works** — it falls back to a color-analysis heuristic that approximates detection based on the green channel ratio in the uploaded image. It is less accurate but functional for demonstration purposes.

---

## 📊 Dataset

The training dataset contains labeled images of arecanut plants across 9 classes stored in `Dataset/Arecanut_dataset/`. This folder is **excluded from git** due to file size.

To obtain the dataset, contact the project maintainer or use your own labeled images with the same folder structure:

```
Dataset/
└── Arecanut_dataset/
    ├── Healthy_Leaf/
    ├── Healthy_Nut/
    ├── Healthy_Trunk/
    ├── Mahali_Koleroga/
    ├── Stem_bleeding/
    ├── bud borer/
    ├── healthy_foot/
    ├── stem cracking/
    └── yellow leaf disease/
```

---

## ⚠️ Known Limitations

| Limitation | Detail |
|---|---|
| TensorFlow + Python 3.13/3.14 | TensorFlow does not yet support Python 3.13+. Use Python 3.11 or 3.12 for full CNN inference. |
| Historical price data | The government API does not provide historical data; 7-day history is simulated from current price ± 3% variation. |
| Price freshness | Live prices depend on data.gov.in availability. If the API is down, fallback static prices are shown. |
| Disease detection accuracy | The CNN model is trained on a limited dataset. Real-world accuracy may vary. |

---

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/my-feature`
3. Make your changes and commit: `git commit -m "Add my feature"`
4. Push: `git push origin feature/my-feature`
5. Open a Pull Request

### Development Notes

- Backend auto-reloads on file changes when using `--reload` flag with uvicorn.
- Frontend is plain HTML/JS — just refresh the browser after any changes.
- API docs are auto-generated at `http://localhost:8000/docs`.

---

## 📄 License

This project is intended for academic and research use. Contact the project author for commercial licensing inquiries.

---

<p align="center">Built for arecanut farmers across India 🌿</p>
