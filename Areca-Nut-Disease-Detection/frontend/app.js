const API_BASE_URL = 'http://localhost:8000/api/v1';

// Backend Status Check
let backendAvailable = false;

async function checkBackendConnection() {
    const statusEl = document.getElementById('backend-status');
    const statusText = statusEl.querySelector('.status-text');
    
    statusEl.style.display = 'inline-flex';
    
    try {
        const response = await fetch(`${API_BASE_URL}/health`, {
            method: 'GET',
            mode: 'cors',
            headers: {
                'Content-Type': 'application/json'
            }
        });
        
        if (response.ok) {
            const data = await response.json();
            backendAvailable = true;
            statusEl.classList.add('connected');
            statusEl.classList.remove('disconnected');
            statusText.textContent = `Backend Connected ${data.cnn_model_enabled ? '• CNN Model Active' : ''}`;
            console.log('✅ Backend connected:', data);
            
            // Load markets once backend is confirmed
            loadAvailableMarkets();
        } else {
            throw new Error('Backend returned error');
        }
    } catch (error) {
        backendAvailable = false;
        statusEl.classList.add('disconnected');
        statusEl.classList.remove('connected');
        statusText.textContent = 'Backend Offline - Start backend server';
        console.error('❌ Backend connection failed:', error);
        
        // Show helpful message
        setTimeout(() => {
            if (!backendAvailable) {
                alert('⚠️ Backend server is not running!\n\nPlease start the backend:\n1. Open terminal in backend folder\n2. Run: start_server.bat\n3. Refresh this page');
            }
        }, 2000);
    }
}

// Check backend on load
checkBackendConnection();

// Recheck every 30 seconds
setInterval(checkBackendConnection, 30000);

// Navigation
document.querySelectorAll('.nav-btn').forEach(btn => {
    btn.addEventListener('click', () => {
        const page = btn.getAttribute('data-page');
        showPage(page);
        
        // Update active button
        document.querySelectorAll('.nav-btn').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        
        // Load page-specific data
        if (page === 'prices') {
            loadAvailableMarkets();
            loadCurrentPrices();
        }
    });
});

function showPage(pageName) {
    document.querySelectorAll('.page').forEach(page => {
        page.classList.remove('active');
    });
    document.getElementById(`${pageName}-page`).classList.add('active');
}

// Price Page Global Variables
let currentChart = null;
let allMarketsData = [];

// Dynamic market data from live API (no hardcoded data)
let MARKETS_BY_STATE = {};

// Load available markets from live API
async function loadAvailableMarkets() {
    const stateSelect = document.getElementById('state-select');
    if (!stateSelect) return;
    
    stateSelect.innerHTML = '<option value="">-- Loading... --</option>';
    
    fetch(API_BASE_URL + '/prices/markets')
        .then(response => response.json())
        .then(data => {
            console.log('Markets API response:', data);
            if (data.success && data.data) {
                MARKETS_BY_STATE = data.data;
                let html = '<option value="">-- Select State --</option>';
                Object.keys(MARKETS_BY_STATE).sort().forEach(state => {
                    html += '<option value="' + state + '">' + state + ' (' + MARKETS_BY_STATE[state].length + ' markets)</option>';
                });
                stateSelect.innerHTML = html;
                console.log('States loaded:', Object.keys(MARKETS_BY_STATE));
            } else {
                stateSelect.innerHTML = '<option value="">-- No data --</option>';
            }
        })
        .catch(error => {
            console.error('Error:', error);
            stateSelect.innerHTML = '<option value="">-- Error --</option>';
        });
}

// Load Districts/Markets by State
function loadDistrictsByState() {
    const stateSelect = document.getElementById('state-select');
    const districtSelect = document.getElementById('district-select');
    const selectedState = stateSelect.value;
    
    // Clear district options
    districtSelect.innerHTML = '<option value="">-- Choose Market --</option>';
    
    if (selectedState && MARKETS_BY_STATE[selectedState]) {
        MARKETS_BY_STATE[selectedState].forEach(market => {
            const option = document.createElement('option');
            option.value = market;
            option.textContent = market;
            districtSelect.appendChild(option);
        });
    }
}

// Initialize markets on page load
document.addEventListener('DOMContentLoaded', function() {
    // Wait a moment for backend to be ready, then load markets
    setTimeout(() => {
        loadAvailableMarkets();
    }, 1000);
});

// Also try loading when backend connection is confirmed
async function initializeAfterBackendReady() {
    if (backendAvailable) {
        await loadAvailableMarkets();
    }
}

// Check Price for Selected District
async function checkPrice() {
    const stateSelect = document.getElementById('state-select');
    const districtSelect = document.getElementById('district-select');
    const resultSection = document.getElementById('price-result-section');
    
    const state = stateSelect.value;
    const district = districtSelect.value;
    
    if (!state || !district) {
        alert('⚠️ Please select both State and District');
        return;
    }
    
    // Check backend first
    if (!backendAvailable) {
        alert('❌ Backend server is not connected!\n\nPlease start the backend server first.');
        return;
    }
    
    try {
        // Fetch current price for the market (encode both params properly)
        const response = await fetch(
            `${API_BASE_URL}/prices/current?market=${encodeURIComponent(district)}&state=${encodeURIComponent(state)}`
        );
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        
        if (data.success && data.data.length > 0) {
            // Average across all varieties returned for this market
            const allEntries = data.data;
            const avgPrice = Math.round(
                allEntries.reduce((sum, p) => sum + (p.price || p.modal_price || 0), 0) / allEntries.length
            );
            const priceInfo = allEntries[0];
            const avgPricePerKg = (avgPrice / 100).toFixed(2);
            
            // Display current price
            document.getElementById('display-price').textContent = `₹${avgPrice.toLocaleString()}`;
            document.getElementById('display-price-kg').textContent = `₹${avgPricePerKg}`;
            document.getElementById('display-location').textContent = `${priceInfo.market}, ${priceInfo.state}`;
            document.getElementById('display-date').textContent = new Date(priceInfo.date || Date.now()).toLocaleDateString('en-IN', {
                day: 'numeric',
                month: 'short',
                year: 'numeric'
            });
            
            // Trend badge
            const trendBadge = document.getElementById('display-trend-badge');
            const trendIcons = { 'up': '↑', 'down': '↓', 'stable': '→' };
            const trend = priceInfo.trend || 'stable';
            trendBadge.textContent = `${trendIcons[trend] || '→'} Trend: ${trend.toUpperCase()}`;
            trendBadge.className = 'price-trend-badge';

            // Show variety info if multiple varieties
            if (allEntries.length > 1) {
                const varLabel = document.getElementById('display-variety-info');
                if (varLabel) {
                    varLabel.textContent = `Avg. of ${allEntries.length} varieties`;
                    varLabel.style.display = 'inline-block';
                }
            }
            
            // Fetch and display 7-day history
            const historyResponse = await fetch(`${API_BASE_URL}/prices/history/${encodeURIComponent(district)}?days=7`);
            const historyData = await historyResponse.json();
            
            if (historyData.success) {
                renderPriceTrendChart(historyData.data, district);
                
                // Calculate stats
                const prices = historyData.data.map(h => h.price);
                const highPrice = Math.max(...prices);
                const lowPrice = Math.min(...prices);
                const firstPrice = prices[0];
                const lastPrice = prices[prices.length - 1];
                const change = lastPrice - firstPrice;
                const changePercent = ((change / firstPrice) * 100).toFixed(2);
                
                document.getElementById('week-high').textContent = `₹${highPrice.toLocaleString()}`;
                document.getElementById('week-low').textContent = `₹${lowPrice.toLocaleString()}`;
                document.getElementById('week-change').textContent = `${change >= 0 ? '+' : ''}₹${change} (${changePercent}%)`;
                document.getElementById('week-change').style.color = change >= 0 ? '#00b894' : '#ff7675';
            }
            
            // Show results
            resultSection.style.display = 'block';
            resultSection.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
            
        } else {
            alert('❌ Price data not available for the selected market');
        }
    } catch (error) {
        console.error('Error fetching price:', error);
        alert('❌ Error fetching price data. Please try again.');
    }
}

// Render Price Trend Chart
function renderPriceTrendChart(history, market) {
    const canvas = document.getElementById('priceCanvas');
    const ctx = canvas.getContext('2d');
    
    // Destroy existing chart
    if (currentChart) {
        currentChart.destroy();
    }
    
    // Prepare data
    const labels = history.map(h => `${h.day_name}\n${h.date.split('-').slice(1).join('/')}`);
    const prices = history.map(h => h.price);
    
    // Create new chart
    currentChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [{
                label: `${market} Price (INR/Quintal)`,
                data: prices,
                borderColor: '#667eea',
                backgroundColor: 'rgba(102, 126, 234, 0.1)',
                borderWidth: 3,
                fill: true,
                tension: 0.4,
                pointRadius: 6,
                pointHoverRadius: 8,
                pointBackgroundColor: '#667eea',
                pointBorderColor: '#fff',
                pointBorderWidth: 2
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: true,
                    position: 'top',
                    labels: {
                        font: { size: 14, weight: 'bold' },
                        color: '#2d3436'
                    }
                },
                tooltip: {
                    backgroundColor: 'rgba(0,0,0,0.8)',
                    padding: 15,
                    titleFont: { size: 15, weight: 'bold' },
                    bodyFont: { size: 14 },
                    callbacks: {
                        label: function(context) {
                            return `Price: ₹${context.parsed.y.toLocaleString()}`;
                        }
                    }
                }
            },
            scales: {
                y: {
                    beginAtZero: false,
                    ticks: {
                        callback: function(value) {
                            return '₹' + value.toLocaleString();
                        },
                        font: { size: 12 },
                        color: '#2d3436'
                    },
                    grid: {
                        color: 'rgba(0, 0, 0, 0.05)'
                    }
                },
                x: {
                    ticks: {
                        font: { size: 12 },
                        color: '#2d3436'
                    },
                    grid: {
                        display: false
                    }
                }
            }
        }
    });
}

// Load All Markets by State
async function loadAllMarketsByState() {
    try {
        const response = await fetch(`${API_BASE_URL}/prices/current`);
        const data = await response.json();
        
        if (data.success) {
            const container = document.getElementById('markets-by-state');
            const marketsByState = {};
            
            // Group markets by state
            data.data.forEach(market => {
                if (!marketsByState[market.state]) {
                    marketsByState[market.state] = [];
                }
                marketsByState[market.state].push(market);
            });
            
            // Display grouped markets
            container.innerHTML = Object.keys(marketsByState).map(state => `
                <div class="state-group">
                    <h4>📍 ${state}</h4>
                    <div class="markets-list">
                        ${marketsByState[state].map(m => `
                            <div class="market-item">
                                <strong>${m.market}</strong>
                                <small>₹${m.price.toLocaleString()} / Quintal</small>
                            </div>
                        `).join('')}
                    </div>
                </div>
            `).join('');
        }
    } catch (error) {
        console.error('Error loading markets:', error);
    }
}

// Load Current Prices
async function loadCurrentPrices() {
    loadAllMarketsByState();
    try {
        // Fetch current prices
        const pricesResponse = await fetch(`${API_BASE_URL}/prices/current`);
        const pricesData = await pricesResponse.json();
        
        if (pricesData.success) {
            allMarketsData = pricesData.data;
            
            // Fetch comparison data
            const comparisonResponse = await fetch(`${API_BASE_URL}/prices/comparison`);
            const comparisonData = await comparisonResponse.json();
            
            if (comparisonData.success) {
                updatePriceOverview(comparisonData.data);
            }
            
            // Display top markets
            displayTopMarkets(allMarketsData.slice(0, 6));
            
            // Display all markets table
            displayAllMarkets(allMarketsData);
            
            // Load initial trend
            showTrend('Mangalore');
        }
    } catch (error) {
        console.error('Error loading prices:', error);
    }
}

// Update Price Overview Stats
function updatePriceOverview(comparison) {
    document.getElementById('highest-price').textContent = `₹${comparison.highest.price.toLocaleString()}`;
    document.getElementById('lowest-price').textContent = `₹${comparison.lowest.price.toLocaleString()}`;
    document.getElementById('average-price').textContent = `₹${comparison.average.toLocaleString()}`;
    document.getElementById('total-markets').textContent = comparison.total_markets;
}

// Display Top Markets
function displayTopMarkets(markets) {
    const container = document.getElementById('top-markets');
    
    const trendIcons = {
        'up': '↑',
        'down': '↓',
        'stable': '→'
    };
    
    container.innerHTML = markets.map(market => `
        <div class="market-card">
            <div class="market-name">${market.market}</div>
            <div class="market-location">📍 ${market.state} • ${market.region}</div>
            <div class="market-price">₹${market.price.toLocaleString()}</div>
            <div class="market-price-label">per Quintal (₹${market.price_per_kg}/kg)</div>
            <div class="market-trend ${market.trend}">
                ${trendIcons[market.trend]} ${market.trend.toUpperCase()}
            </div>
        </div>
    `).join('');
}

// Display All Markets Table
function displayAllMarkets(markets) {
    const container = document.getElementById('all-markets-table');
    
    const trendIcons = {
        'up': '↑',
        'down': '↓',
        'stable': '→'
    };
    
    container.innerHTML = `
        <div class="table-row table-header">
            <div>Market</div>
            <div>State</div>
            <div>Region</div>
            <div>Price (Quintal)</div>
            <div>Trend</div>
        </div>
        ${markets.map(market => `
            <div class="table-row">
                <div><strong>${market.market}</strong></div>
                <div>${market.state}</div>
                <div>${market.region}</div>
                <div><strong>₹${market.price.toLocaleString()}</strong></div>
                <div class="market-trend ${market.trend}">${trendIcons[market.trend]} ${market.trend}</div>
            </div>
        `).join('')}
    `;
}

// Show Price Trend Chart
async function showTrend(market) {
    try {
        // Update button states
        document.querySelectorAll('.trend-btn').forEach(btn => {
            btn.classList.remove('active');
            if (btn.getAttribute('data-market') === market) {
                btn.classList.add('active');
            }
        });
        
        // Fetch history
        const response = await fetch(`${API_BASE_URL}/prices/history/${market}?days=7`);
        const data = await response.json();
        
        if (data.success) {
            renderPriceChart(data.data, market);
        }
    } catch (error) {
        console.error('Error loading trend:', error);
    }
}

// Render Price Chart
function renderPriceChart(history, market) {
    const canvas = document.getElementById('priceCanvas');
    const ctx = canvas.getContext('2d');
    
    // Destroy existing chart
    if (currentChart) {
        currentChart.destroy();
    }
    
    // Prepare data
    const labels = history.map(h => `${h.day_name}\n${h.date.split('-').slice(1).join('/')}`);
    const prices = history.map(h => h.price);
    
    // Create new chart
    currentChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [{
                label: `${market} Price (INR/Quintal)`,
                data: prices,
                borderColor: '#667eea',
                backgroundColor: 'rgba(102, 126, 234, 0.1)',
                borderWidth: 3,
                fill: true,
                tension: 0.4,
                pointRadius: 5,
                pointHoverRadius: 7,
                pointBackgroundColor: '#667eea',
                pointBorderColor: '#fff',
                pointBorderWidth: 2
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: true,
                    position: 'top',
                },
                tooltip: {
                    backgroundColor: 'rgba(0,0,0,0.8)',
                    padding: 12,
                    titleFont: { size: 14 },
                    bodyFont: { size: 13 },
                    callbacks: {
                        label: function(context) {
                            return `Price: ₹${context.parsed.y.toLocaleString()}`;
                        }
                    }
                }
            },
            scales: {
                y: {
                    beginAtZero: false,
                    ticks: {
                        callback: function(value) {
                            return '₹' + value.toLocaleString();
                        }
                    },
                    grid: {
                        color: 'rgba(0, 0, 0, 0.05)'
                    }
                },
                x: {
                    grid: {
                        display: false
                    }
                }
            }
        }
    });
}

// Search Markets
document.getElementById('market-search')?.addEventListener('input', async function(e) {
    const query = e.target.value.toLowerCase();
    
    if (query.length < 2) {
        displayAllMarkets(allMarketsData);
        return;
    }
    
    const filtered = allMarketsData.filter(market => 
        market.market.toLowerCase().includes(query) ||
        market.state.toLowerCase().includes(query) ||
        market.region.toLowerCase().includes(query)
    );
    
    displayAllMarkets(filtered);
});

// Show Detailed Cultivation Guide
function showDetailedGuide() {
    const detailedGuide = document.getElementById('detailed-guide');
    const button = document.querySelector('.btn-full-guide');
    
    if (detailedGuide.style.display === 'none') {
        detailedGuide.style.display = 'block';
        button.textContent = '🔼 Hide Detailed Guide';
        detailedGuide.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    } else {
        detailedGuide.style.display = 'none';
        button.textContent = '🔽 View Detailed Guide';
    }
}

// Legacy function for backward compatibility
async function getPrices() {
    await loadCurrentPrices();
}

// Get Farming Guidance (Legacy - kept for compatibility)
async function getGuidance() {
    // Show guidance page instead
    showPage('guidance');
    document.querySelectorAll('.nav-btn').forEach(b => b.classList.remove('active'));
    const guidanceBtn = document.querySelector('.nav-btn[data-page="guidance"]');
    if (guidanceBtn) guidanceBtn.classList.add('active');
}

// Disease Detection
async function detectDisease() {
    const fileInput = document.getElementById('disease-image');
    const resultBox = document.getElementById('disease-result');
    
    if (!fileInput.files || !fileInput.files[0]) {
        resultBox.innerHTML = '<div class="error">⚠️ Please select an image first</div>';
        return;
    }
    
    // Show loading state
    resultBox.innerHTML = `
        <div class="disease-result-card">
            <div class="loading">
                <div style="font-size: 3rem; margin-bottom: 1rem;">🔍</div>
                <p>Analyzing image with AI model...</p>
                <p style="font-size: 0.9rem; color: #636e72;">This may take a few seconds</p>
            </div>
        </div>
    `;
    
    try {
        const formData = new FormData();
        formData.append('image', fileInput.files[0]);
        
        const response = await fetch(`${API_BASE_URL}/disease/detect`, {
            method: 'POST',
            body: formData
        });
        
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.detail || 'Detection failed');
        }
        
        const data = await response.json();
        
        // Determine emoji based on severity
        const severityEmoji = {
            'none': '✅',
            'low': '🟡',
            'medium': '🟠',
            'high': '🔴',
            'unknown': '❓'
        };
        
        // Determine confidence class
        const confidenceClass = data.confidence >= 0.75 ? '' : 'low';
        
        // Generate treatment list HTML
        const treatmentHTML = data.treatment.map(item => `<li>${item}</li>`).join('');
        
        // Generate symptoms HTML if available
        const symptomsHTML = data.symptoms && data.symptoms.length > 0 ? `
            <div class="symptoms-section">
                <h3>🔬 Detected Symptoms</h3>
                <ul class="symptoms-list">
                    ${data.symptoms.map(symptom => `<li>✓ ${symptom}</li>`).join('')}
                </ul>
            </div>
        ` : '';
        
        // Display results
        resultBox.innerHTML = `
            <div class="disease-result-card">
                <div class="disease-header">
                    <div class="disease-name">
                        ${severityEmoji[data.severity]} ${data.disease_name}
                    </div>
                    <div class="confidence-badge ${confidenceClass}">
                        ${(data.confidence * 100).toFixed(1)}% Confident
                    </div>
                </div>
                
                ${data.severity !== 'none' ? `
                    <div class="severity-indicator ${data.severity}">
                        <strong>Severity:</strong> ${data.severity.toUpperCase()}
                    </div>
                ` : ''}
                
                ${symptomsHTML}
                
                <div class="disease-description">
                    <strong>📖 Description:</strong><br>
                    ${data.description}
                </div>
                
                <div class="treatment-section">
                    <h3>💊 Recommended Treatment</h3>
                    <ul class="treatment-list">
                        ${treatmentHTML}
                    </ul>
                </div>
                
                ${data.model_type === 'placeholder' ? `
                    <p style="margin-top: 1.5rem; padding: 1rem; background: #fff3cd; border-radius: 8px; color: #856404;">
                        <strong>⚠️ Note:</strong> Results are from a simulation model. For accurate diagnosis, please train and deploy a real ML model.
                    </p>
                ` : ''}
            </div>
        `;
        
        // Scroll to results
        resultBox.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
        
    } catch (error) {
        resultBox.innerHTML = `
            <div class="disease-result-card">
                <div class="error">
                    <h3>❌ Error</h3>
                    <p>${error.message}</p>
                    <p style="margin-top: 1rem; font-size: 0.9rem;">Please try again with a different image.</p>
                </div>
            </div>
        `;
    }
}

// Helper function to handle image preview
function handleImagePreview(file, sourceInputId) {
    if (!file) return;
    
    // Validate file type
    if (!file.type.startsWith('image/')) {
        alert('Please select an image file');
        return;
    }
    
    // Validate file size (10MB)
    if (file.size > 10 * 1024 * 1024) {
        alert('File size exceeds 10MB limit');
        return;
    }
    
    // Show preview
    const reader = new FileReader();
    reader.onload = function(event) {
        const previewImg = document.getElementById('preview-img');
        const imagePreview = document.getElementById('image-preview');
        const uploadOptions = document.querySelector('.upload-options');
        const uploadHint = document.querySelector('.upload-hint-text');
        
        previewImg.src = event.target.result;
        imagePreview.style.display = 'block';
        if (uploadOptions) uploadOptions.style.display = 'none';
        if (uploadHint) uploadHint.style.display = 'none';
        
        // Sync files between inputs
        const fileInput = document.getElementById('disease-image');
        const cameraInput = document.getElementById('camera-input');
        
        if (sourceInputId === 'camera-input' && fileInput) {
            const dataTransfer = new DataTransfer();
            dataTransfer.items.add(file);
            fileInput.files = dataTransfer.files;
        } else if (sourceInputId === 'disease-image' && cameraInput) {
            const dataTransfer = new DataTransfer();
            dataTransfer.items.add(file);
            cameraInput.files = dataTransfer.files;
        }
    };
    reader.readAsDataURL(file);
}

// File input preview with image display
document.getElementById('disease-image').addEventListener('change', function(e) {
    const file = e.target.files[0];
    handleImagePreview(file, 'disease-image');
});

// Camera input preview with image display
const cameraInput = document.getElementById('camera-input');
if (cameraInput) {
    cameraInput.addEventListener('change', function(e) {
        const file = e.target.files[0];
        handleImagePreview(file, 'camera-input');
    });
}

// Remove image function
function removeImage() {
    const fileInput = document.getElementById('disease-image');
    const cameraInput = document.getElementById('camera-input');
    const imagePreview = document.getElementById('image-preview');
    const uploadOptions = document.querySelector('.upload-options');
    const uploadHint = document.querySelector('.upload-hint-text');
    const resultBox = document.getElementById('disease-result');
    
    fileInput.value = '';
    if (cameraInput) cameraInput.value = '';
    imagePreview.style.display = 'none';
    if (uploadOptions) uploadOptions.style.display = 'grid';
    if (uploadHint) uploadHint.style.display = 'block';
    resultBox.innerHTML = '';
}

// Camera variables
let cameraStream = null;
let currentFacingMode = 'environment'; // Start with rear camera
let capturedImageBlob = null;

// Open camera function
async function openCamera() {
    const modal = document.getElementById('camera-modal');
    const video = document.getElementById('camera-video');
    
    if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
        alert('Camera access is not supported in your browser. Please use the "Choose from Gallery" option instead.');
        return;
    }
    
    try {
        modal.style.display = 'flex';
        
        // Request camera access
        cameraStream = await navigator.mediaDevices.getUserMedia({
            video: { facingMode: currentFacingMode },
            audio: false
        });
        
        video.srcObject = cameraStream;
        video.style.display = 'block';
        
    } catch (error) {
        console.error('Camera access error:', error);
        modal.style.display = 'none';
        alert('Unable to access camera. Please check permissions and try again, or use "Choose from Gallery" instead.');
    }
}

// Close camera function
function closeCamera() {
    const modal = document.getElementById('camera-modal');
    const video = document.getElementById('camera-video');
    const canvas = document.getElementById('camera-canvas');
    
    if (cameraStream) {
        cameraStream.getTracks().forEach(track => track.stop());
        cameraStream = null;
    }
    
    video.style.display = 'block';
    canvas.style.display = 'none';
    document.getElementById('capture-btn').style.display = 'inline-block';
    document.getElementById('flip-camera-btn').style.display = 'inline-block';
    document.getElementById('use-photo-btn').style.display = 'none';
    document.getElementById('retake-btn').style.display = 'none';
    
    modal.style.display = 'none';
    capturedImageBlob = null;
}

// Flip camera (front/rear)
async function flipCamera() {
    currentFacingMode = currentFacingMode === 'environment' ? 'user' : 'environment';
    
    if (cameraStream) {
        cameraStream.getTracks().forEach(track => track.stop());
    }
    
    const video = document.getElementById('camera-video');
    
    try {
        cameraStream = await navigator.mediaDevices.getUserMedia({
            video: { facingMode: currentFacingMode },
            audio: false
        });
        video.srcObject = cameraStream;
    } catch (error) {
        console.error('Error flipping camera:', error);
        alert('Unable to switch camera');
    }
}

// Capture photo function
function capturePhoto() {
    const video = document.getElementById('camera-video');
    const canvas = document.getElementById('camera-canvas');
    const context = canvas.getContext('2d');
    
    // Set canvas dimensions to match video
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    
    // Draw video frame to canvas
    context.drawImage(video, 0, 0, canvas.width, canvas.height);
    
    // Show canvas, hide video
    video.style.display = 'none';
    canvas.style.display = 'block';
    
    // Update buttons
    document.getElementById('capture-btn').style.display = 'none';
    document.getElementById('flip-camera-btn').style.display = 'none';
    document.getElementById('use-photo-btn').style.display = 'inline-block';
    document.getElementById('retake-btn').style.display = 'inline-block';
    
    // Convert canvas to blob
    canvas.toBlob(blob => {
        capturedImageBlob = blob;
    }, 'image/jpeg', 0.95);
}

// Retake photo function
function retakePhoto() {
    const video = document.getElementById('camera-video');
    const canvas = document.getElementById('camera-canvas');
    
    video.style.display = 'block';
    canvas.style.display = 'none';
    
    document.getElementById('capture-btn').style.display = 'inline-block';
    document.getElementById('flip-camera-btn').style.display = 'inline-block';
    document.getElementById('use-photo-btn').style.display = 'none';
    document.getElementById('retake-btn').style.display = 'none';
    
    capturedImageBlob = null;
}

// Use captured photo function
function useCapturedPhoto() {
    if (!capturedImageBlob) return;
    
    // Create a file from the blob
    const file = new File([capturedImageBlob], 'camera-photo.jpg', { type: 'image/jpeg' });
    
    // Set to file input
    const fileInput = document.getElementById('disease-image');
    const dataTransfer = new DataTransfer();
    dataTransfer.items.add(file);
    fileInput.files = dataTransfer.files;
    
    // Show preview
    handleImagePreview(file, 'disease-image');
    
    // Close camera
    closeCamera();
}

// Get Farming Guidance
async function getGuidance() {
    const resultBox = document.getElementById('guidance-result');
    
    const requestData = {
        soil_type: document.getElementById('soil-type').value || null,
        rainfall_mm: parseFloat(document.getElementById('rainfall').value) || null,
        fertilizer_used: document.getElementById('fertilizer').value || null,
        plant_age_months: parseInt(document.getElementById('plant-age').value) || null,
        previous_yield_kg: parseFloat(document.getElementById('previous-yield').value) || null
    };
    
    resultBox.innerHTML = '<div class="loading">🌱 Generating recommendations...</div>';
    
    try {
        const response = await fetch(`${API_BASE_URL}/guidance/predict`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(requestData)
        });
        
        const data = await response.json();
        
        resultBox.innerHTML = `
            <h3>📋 Recommendations</h3>
            <div class="recommendation">
                <h4>💊 Fertilizer</h4>
                <p><strong>${data.recommendation.fertilizer}</strong></p>
                <p>Dosage: ${data.recommendation.dosage_kg} kg per plant</p>
            </div>
            <div class="recommendation">
                <h4>💧 Irrigation</h4>
                <p>${data.recommendation.irrigation_liters} liters per plant</p>
            </div>
            ${data.recommendation.note ? `<p><small>Note: ${data.recommendation.note}</small></p>` : ''}
        `;
    } catch (error) {
        resultBox.innerHTML = `<div class="error">Error: ${error.message}</div>`;
    }
}

// Navigation Helper Functions
function openDiseaseCheck() {
    showPage('disease');
    document.querySelectorAll('.nav-btn').forEach(b => b.classList.remove('active'));
    document.querySelector('.nav-btn[data-page="disease"]').classList.add('active');
}

function openLivePrice() {
    showPage('prices');
    document.querySelectorAll('.nav-btn').forEach(b => b.classList.remove('active'));
    document.querySelector('.nav-btn[data-page="prices"]').classList.add('active');
    loadCurrentPrices();
}

function openTreatmentGuide() {
    showPage('treatment');
    document.querySelectorAll('.nav-btn').forEach(b => b.classList.remove('active'));
    // Add active state if treatment nav button exists
    const treatmentBtn = document.querySelector('.nav-btn[data-page="treatment"]');
    if (treatmentBtn) treatmentBtn.classList.add('active');
}

// Load Live Prices on Home Page
async function loadHomePrices() {
    const priceBox = document.getElementById('home-prices');
    
    try {
        const response = await fetch(`${API_BASE_URL}/prices`);
        const data = await response.json();
        
        if (data.data && data.data.length > 0) {
            priceBox.innerHTML = data.data.map(item => `
                <div class="price-item">
                    <div>
                        <strong>${item.commodity}</strong><br>
                        <small>${item.district}, ${item.state}</small><br>
                        <small>${new Date(item.timestamp).toLocaleDateString()}</small>
                    </div>
                    <div class="price">₹${item.price}/${item.unit.split('/')[1]}</div>
                </div>
            `).join('');
        } else {
            priceBox.innerHTML = '<p>No price data available</p>';
        }
    } catch (error) {
        priceBox.innerHTML = '<p>Unable to load prices</p>';
    }
}

// Check API health on load
async function checkAPIHealth() {
    try {
        const response = await fetch(`${API_BASE_URL}/health/`);
        const data = await response.json();
        console.log('API Status:', data);
    } catch (error) {
        console.warn('API not available:', error.message);
    }
}

// Initialize on page load
checkAPIHealth();
