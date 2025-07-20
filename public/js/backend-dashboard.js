/**
 * Backend API Dashboard - ORCAST Real Data Only
 * Loads cleaned data from Firestore and BigQuery only - NO artificial data
 */

class BackendDashboard {
    constructor() {
        this.endpoints = {
            predictions: '/api/predictions',
            sightings: '/api/sightings', 
            environmental: '/api/environmental',
            status: '/api/status'
        };
        
        this.dashboardData = {};
        this.updateInterval = 30000; // 30 seconds
        this.isInitialized = false;
        
        this.initializeDashboard();
    }

    async initializeDashboard() {
        console.log('🔄 Initializing ORCAST Backend Dashboard (Real Data Only)...');
        
        // Create dashboard UI
        this.createDashboardCards();
        
        // Load all real data
        await this.loadAllRealData();
        
        // Set up auto-refresh
        this.setupAutoRefresh();
        
        this.isInitialized = true;
        console.log('✅ Backend Dashboard initialized with real data');
    }

    createDashboardCards() {
        const dashboardGrid = document.getElementById('dashboardGrid');
        
        dashboardGrid.innerHTML = `
            <!-- Real Predictions Card -->
            <div class="dashboard-card" id="predictions-card">
                <div class="card-header">
                    <h4>🎯 Predictions</h4>
                    <div class="status-indicator" id="predictions-status"></div>
                </div>
                <div class="data-summary" id="predictions-content">
                    <div class="summary-value" id="totalZones">-</div>
                    <div class="summary-label">Active Zones</div>
                </div>
            </div>

            <!-- Real Sightings Card -->  
            <div class="dashboard-card" id="sightings-card">
                <div class="card-header">
                    <h4>👁️ Sightings</h4>
                    <div class="status-indicator" id="sightings-status"></div>
                </div>
                <div class="data-summary" id="sightings-content">
                    <div class="summary-value" id="recentSightings">-</div>
                    <div class="summary-label">Last 24h</div>
                </div>
            </div>

            <!-- Environmental Data Card -->
            <div class="dashboard-card" id="environmental-card">
                <div class="card-header">
                    <h4>🌊 Environment</h4>
                    <div class="status-indicator" id="environmental-status"></div>
                </div>
                <div class="data-summary" id="environmental-content">
                    <div class="summary-value" id="tidalHeight">-</div>
                    <div class="summary-label">Tidal Height</div>
                </div>
            </div>

            <!-- System Status Card -->
            <div class="dashboard-card" id="system-card">
                <div class="card-header">
                    <h4>⚡ System</h4>
                    <div class="status-indicator" id="system-status"></div>
                </div>
                <div class="data-summary" id="system-content">
                    <div class="summary-value" id="responseTime">-</div>
                    <div class="summary-label">Response Time</div>
                </div>
            </div>
        `;
    }

    async loadAllRealData() {
        console.log('📡 Loading real data from Firestore/BigQuery...');
        
        const loadPromises = Object.entries(this.endpoints).map(([key, endpoint]) => 
            this.loadRealEndpointData(key, endpoint)
        );
        
        try {
            const results = await Promise.allSettled(loadPromises);
            results.forEach((result, index) => {
                const key = Object.keys(this.endpoints)[index];
                if (result.status === 'rejected') {
                    console.error(`Failed to load ${key}:`, result.reason);
                    this.updateStatus(key, 'error');
                } else {
                    console.log(`✅ Loaded real ${key} data`);
                    this.updateStatus(key, 'success');
                }
            });
        } catch (error) {
            console.error('Error loading real data:', error);
        }
    }

    async loadRealEndpointData(key, endpoint) {
        const startTime = Date.now();
        
        try {
            this.updateStatus(key, 'loading');
            
            // Fetch real data from API endpoints
            const response = await fetch(endpoint, {
                method: 'GET',
                headers: {
                    'Accept': 'application/json',
                    'Content-Type': 'application/json'
                }
            });
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            const data = await response.json();
            const responseTime = Date.now() - startTime;
            
            // Store real data
            this.dashboardData[key] = {
                data: data,
                responseTime: responseTime,
                lastUpdated: new Date(),
                status: 'success'
            };
            
            // Update UI with real data
            this.updateCardWithRealData(key, data);
            this.updateStatus(key, 'success');
            
            return { status: 'success', responseTime };
            
        } catch (error) {
            console.error(`Error loading real ${endpoint} data:`, error);
            
            this.dashboardData[key] = {
                error: error.message,
                lastUpdated: new Date(),
                status: 'error'
            };
            
            this.updateCardWithRealData(key, null, error.message);
            this.updateStatus(key, 'error');
            
            throw error;
        }
    }

    updateCardWithRealData(key, data, error = null) {
        if (error) {
            const contentEl = document.getElementById(`${key}-content`);
            if (contentEl) {
                contentEl.innerHTML = `
                    <div style="color: #e53e3e; font-size: 0.8rem;">
                        Error: ${error}
                    </div>
                `;
            }
            return;
        }

        // Update cards with real data from Firestore/BigQuery
        switch (key) {
            case 'predictions':
                if (data && data.data) {
                    document.getElementById('totalZones').textContent = data.data.totalZones || 0;
                }
                break;
                
            case 'sightings':
                if (data && data.sightings) {
                    document.getElementById('recentSightings').textContent = data.sightings.length || 0;
                }
                break;
                
            case 'environmental':
                if (data && data.environmentalData) {
                    const tidalHeight = data.environmentalData.tidalHeight || 0;
                    document.getElementById('tidalHeight').textContent = `${tidalHeight.toFixed(1)}m`;
                }
                break;
                
            case 'status':
                if (data && data.responseTime) {
                    document.getElementById('responseTime').textContent = `${data.responseTime}ms`;
                }
                break;
        }
    }

    updateStatus(key, status) {
        const statusEl = document.getElementById(`${key}-status`);
        if (statusEl) {
            statusEl.className = `status-indicator ${status}`;
        }
    }

    setupAutoRefresh() {
        // Refresh real data every 30 seconds
        setInterval(() => {
            if (this.isInitialized) {
                console.log('🔄 Auto-refreshing real data...');
                this.loadAllRealData();
            }
        }, this.updateInterval);
    }

    // Get real data for external components
    getRealData(key) {
        return this.dashboardData[key] || null;
    }
    
    // Manual refresh
    async refreshAllRealData() {
        console.log('🔄 Manual refresh of real data...');
        await this.loadAllRealData();
    }
}

// Make available globally
window.BackendDashboard = BackendDashboard; 