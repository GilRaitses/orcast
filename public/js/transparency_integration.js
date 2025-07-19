// OrCast Transparency Integration
// Integrates the forecast transparency engine with the main OrCast UI

class TransparencyUIManager {
    constructor() {
        this.currentForecast = null;
        this.isVisible = false;
        this.autoRefreshInterval = null;
        
        this.initializeUI();
    }
    
    initializeUI() {
        // Add transparency panel to existing UI
        this.createTransparencyPanel();
        this.setupEventListeners();
        this.loadTransparencyCSS();
    }
    
    loadTransparencyCSS() {
        // Load transparency CSS if not already loaded
        if (!document.querySelector('link[href="transparency_ui.css"]')) {
            const link = document.createElement('link');
            link.rel = 'stylesheet';
            link.href = 'transparency_ui.css';
            document.head.appendChild(link);
        }
    }
    
    createTransparencyPanel() {
        // Create the transparency panel HTML structure
        const panelHTML = `
            <div id="transparencyPanel" class="transparency-panel" style="display: none;">
                <div class="transparency-header">
                    <div class="transparency-icon">ANALYZE</div>
                    <div class="transparency-title">
                        <h3>Prediction Transparency</h3>
                        <div class="transparency-subtitle">Understanding your orca encounter prediction</div>
                    </div>
                    <div class="transparency-timestamp" id="forecastTimestamp">
                        Updated: --
                    </div>
                </div>
                
                <!-- Loading State -->
                <div id="transparencyLoading" class="transparency-loading">
                    <div class="loading-spinner-large"></div>
                    <div>Analyzing environmental conditions and orca behavior patterns...</div>
                </div>
                
                <!-- Main Content -->
                <div id="transparencyContent" style="display: none;">
                    <!-- Prediction Summary -->
                    <div class="prediction-summary">
                        <div class="prediction-probability">
                            <div class="probability-value" id="probabilityValue">--</div>
                            <div class="probability-label">Encounter Probability</div>
                        </div>
                        <div class="prediction-details">
                            <div class="confidence-bar">
                                <div class="confidence-label">
                                    <span>Confidence Level</span>
                                    <span id="confidenceValue">--</span>
                                </div>
                                <div class="confidence-track">
                                    <div class="confidence-fill" id="confidenceFill" style="width: 0%;"></div>
                                </div>
                            </div>
                            <div class="timeframe-badge" id="timeframeBadge">Next 4 hours</div>
                        </div>
                    </div>
                    
                    <!-- Environmental Conditions -->
                    <div class="environmental-conditions" id="environmentalConditions">
                        <!-- Populated dynamically -->
                    </div>
                    
                    <!-- Factor Analysis -->
                    <div class="factor-analysis">
                        <div class="factor-section" id="primaryFactorsSection">
                            <div class="factor-section-title">
                                <div class="factor-icon primary">TARGET</div>
                                <span>Primary Factors</span>
                            </div>
                            <div class="factor-list" id="primaryFactors">
                                <!-- Populated dynamically -->
                            </div>
                        </div>
                        
                        <div class="factor-section" id="supportingFactorsSection">
                            <div class="factor-section-title">
                                <div class="factor-icon supporting">➕</div>
                                <span>Supporting Factors</span>
                            </div>
                            <div class="factor-list" id="supportingFactors">
                                <!-- Populated dynamically -->
                            </div>
                        </div>
                        
                        <div class="factor-section" id="limitingFactorsSection">
                            <div class="factor-section-title">
                                <div class="factor-icon limiting">WARNING</div>
                                <span>Limiting Factors</span>
                            </div>
                            <div class="factor-list" id="limitingFactors">
                                <!-- Populated dynamically -->
                            </div>
                        </div>
                    </div>
                    
                    <!-- Confidence Breakdown -->
                    <div class="expandable-section">
                        <div class="expandable-header" onclick="toggleExpanded('confidenceBreakdown')">
                            <div class="expandable-title">ANALYZE Confidence Breakdown</div>
                            <div class="expandable-toggle">▼</div>
                        </div>
                        <div class="expandable-content" id="confidenceBreakdown">
                            <div class="confidence-breakdown">
                                <div class="confidence-title">How We Calculate Confidence</div>
                                <div class="confidence-components" id="confidenceComponents">
                                    <!-- Populated dynamically -->
                                </div>
                            </div>
                        </div>
                    </div>
                    
                    <!-- Recommendations -->
                    <div class="recommendations" id="recommendationsSection">
                        <div class="recommendations-title">
                            <span>IDEA</span>
                            <span>Recommendations</span>
                        </div>
                        <div class="recommendation-list" id="recommendationList">
                            <!-- Populated dynamically -->
                        </div>
                    </div>
                    
                    <!-- Transparency Metadata -->
                    <div class="expandable-section">
                        <div class="expandable-header" onclick="toggleExpanded('transparencyMetadata')">
                            <div class="expandable-title">ANALYZE Data Sources & Methodology</div>
                            <div class="expandable-toggle">▼</div>
                        </div>
                        <div class="expandable-content" id="transparencyMetadata">
                            <div class="transparency-metadata">
                                <div class="metadata-section">
                                    <div class="metadata-title">Fully Transparent Data Sources</div>
                                    <div class="metadata-list" id="transparentSources">
                                        <!-- Populated dynamically -->
                                    </div>
                                </div>
                                
                                <div class="metadata-section">
                                    <div class="metadata-title">Partially Open Sources</div>
                                    <div class="metadata-list" id="partialSources">
                                        <!-- Populated dynamically -->
                                    </div>
                                </div>
                                
                                <div class="metadata-section">
                                    <div class="metadata-title">Proprietary Algorithms</div>
                                    <div class="metadata-list" id="proprietarySources">
                                        <!-- Populated dynamically -->
                                    </div>
                                </div>
                                
                                <div class="metadata-section">
                                    <div class="metadata-title">Limitations & Uncertainties</div>
                                    <ul class="limitations-list" id="limitationsList">
                                        <!-- Populated dynamically -->
                                    </ul>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
                
                <!-- Control Buttons -->
                <div class="transparency-controls" style="margin-top: 1rem; text-align: center;">
                    <button onclick="transparencyUI.refreshForecast()" class="ai-btn" style="margin-right: 0.5rem;">
                        REFRESH Refresh
                    </button>
                    <button onclick="transparencyUI.toggleAutoRefresh()" class="ai-btn" id="autoRefreshBtn">
                        ⏰ Auto-refresh: OFF
                    </button>
                    <button onclick="transparencyUI.hide()" class="ai-btn" style="margin-left: 0.5rem;">
                        ✖️ Close
                    </button>
                </div>
            </div>
        `;
        
        // Add to controls panel or create new section
        const controlsPanel = document.querySelector('.controls-panel');
        if (controlsPanel) {
            controlsPanel.insertAdjacentHTML('afterbegin', panelHTML);
        } else {
            // Fallback: add to body
            document.body.insertAdjacentHTML('beforeend', panelHTML);
        }
    }
    
    setupEventListeners() {
        // Add transparency toggle to existing hotspots section
        this.addTransparencyToggle();
        
        // Listen for map clicks to update transparency
        if (window.map) {
            window.map.addListener('click', (e) => {
                this.updateForecastForLocation({
                    lat: e.latLng.lat(),
                    lng: e.latLng.lng()
                });
            });
        }
        
        // Auto-refresh setup
        this.setupAutoRefresh();
    }
    
    addTransparencyToggle() {
        // Add transparency button to hotspots section
        const hotspotsSection = document.querySelector('#hotspotsList');
        if (hotspotsSection && hotspotsSection.parentElement) {
            const toggleButton = document.createElement('button');
            toggleButton.className = 'ai-btn';
            toggleButton.style.width = '100%';
            toggleButton.style.marginTop = '1rem';
            toggleButton.innerHTML = 'ANALYZE Explain Predictions';
            toggleButton.onclick = () => this.toggle();
            
            hotspotsSection.parentElement.appendChild(toggleButton);
        }
    }
    
    async show() {
        const panel = document.getElementById('transparencyPanel');
        if (panel) {
            panel.style.display = 'block';
            this.isVisible = true;
            
            // Load forecast for current location or default
            const location = window.clickedLocation || { lat: 48.5, lng: -123.0 };
            await this.updateForecastForLocation(location);
        }
    }
    
    hide() {
        const panel = document.getElementById('transparencyPanel');
        if (panel) {
            panel.style.display = 'none';
            this.isVisible = false;
            this.stopAutoRefresh();
        }
    }
    
    toggle() {
        if (this.isVisible) {
            this.hide();
        } else {
            this.show();
        }
    }
    
    async updateForecastForLocation(location) {
        if (!this.isVisible) return;
        
        // Show loading state
        this.showLoading();
        
        try {
            // Get explainable forecast from transparency engine
            const forecast = await window.forecastTransparency.getExplainableForecast(location);
            
            if (forecast.success) {
                this.currentForecast = forecast;
                this.renderForecast(forecast);
                this.updateTimestamp();
            } else {
                this.showError(forecast.error);
            }
        } catch (error) {
            console.error('Error getting forecast:', error);
            this.showError('Unable to load forecast analysis');
        }
    }
    
    showLoading() {
        document.getElementById('transparencyLoading').style.display = 'block';
        document.getElementById('transparencyContent').style.display = 'none';
    }
    
    hideLoading() {
        document.getElementById('transparencyLoading').style.display = 'none';
        document.getElementById('transparencyContent').style.display = 'block';
    }
    
    showError(message) {
        const panel = document.getElementById('transparencyPanel');
        panel.innerHTML = `
            <div class="transparency-header">
                <div class="transparency-icon">ERROR</div>
                <div class="transparency-title">
                    <h3>Forecast Analysis Error</h3>
                    <div class="transparency-subtitle">${message}</div>
                </div>
            </div>
            <div style="text-align: center; padding: 2rem;">
                <button onclick="transparencyUI.refreshForecast()" class="ai-btn">
                    RETRY Try Again
                </button>
            </div>
        `;
    }
    
    renderForecast(forecast) {
        this.hideLoading();
        
        // Update prediction summary
        this.renderPredictionSummary(forecast.prediction);
        
        // Update environmental conditions
        this.renderEnvironmentalConditions(forecast.context.current);
        
        // Update factor analysis
        this.renderFactorAnalysis(forecast.explanation);
        
        // Update confidence breakdown
        this.renderConfidenceBreakdown(forecast.confidence);
        
        // Update recommendations
        this.renderRecommendations(forecast.recommendations);
        
        // Update transparency metadata
        this.renderTransparencyMetadata(forecast.transparency);
    }
    
    renderPredictionSummary(prediction) {
        const probabilityValue = document.getElementById('probabilityValue');
        const confidenceValue = document.getElementById('confidenceValue');
        const confidenceFill = document.getElementById('confidenceFill');
        const timeframeBadge = document.getElementById('timeframeBadge');
        
        if (probabilityValue) {
            probabilityValue.textContent = `${Math.round(prediction.probability * 100)}%`;
        }
        
        if (confidenceValue && confidenceFill) {
            const confidence = Math.round(prediction.confidence * 100);
            confidenceValue.textContent = `${confidence}%`;
            confidenceFill.style.width = `${confidence}%`;
        }
        
        if (timeframeBadge) {
            timeframeBadge.textContent = `Next ${prediction.timeframe}`;
        }
    }
    
    renderEnvironmentalConditions(conditions) {
        const container = document.getElementById('environmentalConditions');
        if (!container) return;
        
        const conditionsData = [
            {
                icon: '🌤️',
                title: 'Weather',
                value: conditions.weather.cloudCover < 30 ? 'Clear' : 
                       conditions.weather.cloudCover > 70 ? 'Overcast' : 'Partly Cloudy',
                description: `${conditions.weather.cloudCover}% cloud cover`
            },
            {
                icon: 'WATER',
                title: 'Tidal State',
                value: conditions.tidal.trend.charAt(0).toUpperCase() + conditions.tidal.trend.slice(1),
                description: `${conditions.tidal.strength} ${conditions.tidal.trend} tide`
            },
            {
                icon: '🌙',
                title: 'Lunar Phase',
                value: conditions.lunar.phase.charAt(0).toUpperCase() + conditions.lunar.phase.slice(1),
                description: `${Math.round(conditions.lunar.illumination * 100)}% illuminated`
            },
            {
                icon: 'DEPTH',
                title: 'Visibility',
                value: conditions.weather.visibility > 10 ? 'Excellent' :
                       conditions.weather.visibility > 5 ? 'Good' : 'Poor',
                description: `${conditions.weather.visibility} km range`
            }
        ];
        
        container.innerHTML = conditionsData.map(condition => `
            <div class="condition-card">
                <div class="condition-icon">${condition.icon}</div>
                <div class="condition-title">${condition.title}</div>
                <div class="condition-value">${condition.value}</div>
                <div class="condition-description">${condition.description}</div>
            </div>
        `).join('');
    }
    
    renderFactorAnalysis(explanation) {
        this.renderFactorList('primaryFactors', explanation.primaryFactors, 'primary');
        this.renderFactorList('supportingFactors', explanation.supportingFactors, 'supporting');
        this.renderFactorList('limitingFactors', explanation.limitingFactors, 'limiting');
    }
    
    renderFactorList(containerId, factors, type) {
        const container = document.getElementById(containerId);
        if (!container) return;
        
        if (factors.length === 0) {
            container.innerHTML = '<div style="text-align: center; color: rgba(255,255,255,0.6); padding: 1rem;">No significant factors identified</div>';
            return;
        }
        
        container.innerHTML = factors.map(factor => `
            <div class="factor-item ${type}">
                <div class="factor-header">
                    <div class="factor-name">${factor.factor}</div>
                    <div class="factor-weight ${factor.weight}">${factor.weight}</div>
                </div>
                <div class="factor-explanation">${factor.explanation}</div>
                <div class="transparency-indicator">
                    <div class="transparency-dot ${factor.transparency}"></div>
                    <span>${factor.transparency} transparency</span>
                </div>
            </div>
        `).join('');
    }
    
    renderConfidenceBreakdown(confidence) {
        const container = document.getElementById('confidenceComponents');
        if (!container) return;
        
        const components = Object.entries(confidence.components).map(([key, component]) => ({
            name: key.charAt(0).toUpperCase() + key.slice(1),
            ...component
        }));
        
        container.innerHTML = components.map(component => `
            <div class="confidence-component">
                <div class="component-label">
                    <span>IDEA</span>
                    <span class="component-weight">Environmental Match</span>
                </div>
                <div class="component-value">${Math.round(component.score * 100)}%</div>
                <div class="component-bar">
                    <div class="component-fill" style="width: ${component.score * 100}%;"></div>
                </div>
                <div class="component-explanation">${component.explanation}</div>
            </div>
        `).join('');
    }
    
    renderRecommendations(recommendations) {
        const container = document.getElementById('recommendationList');
        if (!container) return;
        
        if (recommendations.length === 0) {
            document.getElementById('recommendationsSection').style.display = 'none';
            return;
        }
        
        document.getElementById('recommendationsSection').style.display = 'block';
        
        container.innerHTML = recommendations.map(rec => `
            <div class="recommendation-item">
                <div class="recommendation-priority ${rec.priority}">${rec.priority.toUpperCase()}</div>
                <div class="recommendation-content">
                    <div class="recommendation-text">${rec.text}</div>
                    <div class="recommendation-action">${rec.action}</div>
                </div>
            </div>
        `).join('');
    }
    
    renderTransparencyMetadata(transparency) {
        // Data sources
        this.renderMetadataList('transparentSources', transparency.dataSource.fullyOpen, 'transparent');
        this.renderMetadataList('partialSources', transparency.dataSource.partiallyOpen, 'partial');
        this.renderMetadataList('proprietarySources', transparency.dataSource.proprietary, 'proprietary');
        
        // Limitations
        const limitationsList = document.getElementById('limitationsList');
        if (limitationsList) {
            limitationsList.innerHTML = transparency.limitations.map(limitation => 
                `<li>${limitation}</li>`
            ).join('');
        }
    }
    
    renderMetadataList(containerId, items, type) {
        const container = document.getElementById(containerId);
        if (!container) return;
        
        container.innerHTML = items.map(item => 
            `<div class="metadata-tag ${type}">${item}</div>`
        ).join('');
    }
    
    updateTimestamp() {
        const timestamp = document.getElementById('forecastTimestamp');
        if (timestamp) {
            const now = new Date();
            timestamp.textContent = `Updated: ${now.toLocaleTimeString()}`;
        }
    }
    
    async refreshForecast() {
        const location = window.clickedLocation || { lat: 48.5, lng: -123.0 };
        await this.updateForecastForLocation(location);
    }
    
    setupAutoRefresh() {
        // Auto-refresh every 5 minutes when active
        this.autoRefreshInterval = null;
    }
    
    toggleAutoRefresh() {
        const button = document.getElementById('autoRefreshBtn');
        
        if (this.autoRefreshInterval) {
            clearInterval(this.autoRefreshInterval);
            this.autoRefreshInterval = null;
            button.textContent = '⏰ Auto-refresh: OFF';
        } else {
            this.autoRefreshInterval = setInterval(() => {
                if (this.isVisible) {
                    this.refreshForecast();
                }
            }, 5 * 60 * 1000); // 5 minutes
            button.textContent = '⏰ Auto-refresh: ON';
        }
    }
    
    stopAutoRefresh() {
        if (this.autoRefreshInterval) {
            clearInterval(this.autoRefreshInterval);
            this.autoRefreshInterval = null;
            
            const button = document.getElementById('autoRefreshBtn');
            if (button) {
                button.textContent = '⏰ Auto-refresh: OFF';
            }
        }
    }
}

// Global function for expandable sections
function toggleExpanded(sectionId) {
    const content = document.getElementById(sectionId);
    const header = content.previousElementSibling;
    const toggle = header.querySelector('.expandable-toggle');
    
    if (content.classList.contains('expanded')) {
        content.classList.remove('expanded');
        toggle.classList.remove('expanded');
        content.style.display = 'none';
    } else {
        content.classList.add('expanded');
        toggle.classList.add('expanded');
        content.style.display = 'block';
    }
}

// Initialize transparency UI when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    // Wait for other components to load
    setTimeout(() => {
        window.transparencyUI = new TransparencyUIManager();
    }, 1000);
});

// Export for external use
window.TransparencyUIManager = TransparencyUIManager; 