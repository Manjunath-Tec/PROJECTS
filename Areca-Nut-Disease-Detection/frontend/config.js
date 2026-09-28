// API Configuration
const CONFIG = {
    // Backend API URL - change this if running on different port or host
    API_BASE_URL: 'http://localhost:8000/api/v1',
    
    // API Endpoints
    ENDPOINTS: {
        HEALTH: '/health',
        PRICES_CURRENT: '/prices/current',
        PRICES_HISTORY: '/prices/history',
        PRICES_COMPARISON: '/prices/comparison',
        DISEASE_DETECT: '/disease/detect',
        GUIDANCE_PREDICT: '/guidance/predict',
        DISEASES_ALL: '/diseases',
        MODEL_INFO: '/model/info'
    },
    
    // Check if backend is accessible
    async checkBackendHealth() {
        try {
            const response = await fetch(`${this.API_BASE_URL}/health`);
            const data = await response.json();
            return data.status === 'healthy';
        } catch (error) {
            console.error('Backend health check failed:', error);
            return false;
        }
    }
};

// Export for use in other scripts
if (typeof module !== 'undefined' && module.exports) {
    module.exports = CONFIG;
}
