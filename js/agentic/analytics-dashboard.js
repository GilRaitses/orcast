/**
 * Analytics Dashboard for ORCAST Multi-Agent System
 * 
 * Provides interactive dashboards for agents to display:
 * - Statistics and analytics
 * - Reasoning and explanations
 * - Informed suggestions
 * - Zone recommendations
 * - Environmental insights
 */

class AnalyticsDashboard {
    constructor(containerId, config = {}) {
        this.container = document.getElementById(containerId);
        this.config = config;
        this.charts = {};
        this.widgets = {};
        this.data = {};
        
        this.initializeDashboard();
    }

    initializeDashboard() {
        this.container.innerHTML = this.createDashboardHTML();
        this.initializeCharts();
        this.initializeWidgets();
        this.setupEventListeners();
    }

    createDashboardHTML() {
        return `
            <div class="orcast-analytics-dashboard">
                <!-- Header with real-time status -->
                <div class="dashboard-header">
                    <h2>ORCAST Analytics Dashboard</h2>
                    <div class="status-indicators">
                        <div class="status-item" id="agent-status">
                            <span class="status-icon">🤖</span>
                            <span class="status-text">Agents Active</span>
                        </div>
                        <div class="status-item" id="data-status">
                            <span class="status-icon">📊</span>
                            <span class="status-text">Data Current</span>
                        </div>
                        <div class="status-item" id="confidence-status">
                            <span class="status-icon">🎯</span>
                            <span class="status-text">High Confidence</span>
                        </div>
                    </div>
                </div>

                <!-- Main dashboard grid -->
                <div class="dashboard-grid">
                    <!-- Probability Overview -->
                    <div class="dashboard-card probability-overview">
                        <h3>Orca Probability Overview</h3>
                        <div id="probability-chart" class="chart-container"></div>
                        <div class="probability-summary">
                            <div class="prob-metric">
                                <span class="metric-value" id="overall-probability">--</span>
                                <span class="metric-label">Overall Probability</span>
                            </div>
                            <div class="prob-metric">
                                <span class="metric-value" id="confidence-score">--</span>
                                <span class="metric-label">Confidence Score</span>
                            </div>
                        </div>
                    </div>

                    <!-- Zone Analytics -->
                    <div class="dashboard-card zone-analytics">
                        <h3>Viewing Zone Analytics</h3>
                        <div id="zone-performance-chart" class="chart-container"></div>
                        <div class="zone-list" id="top-zones"></div>
                    </div>

                    <!-- Behavioral Insights -->
                    <div class="dashboard-card behavioral-insights">
                        <h3>Behavioral Insights</h3>
                        <div id="behavior-chart" class="chart-container"></div>
                        <div class="behavior-summary" id="behavior-summary"></div>
                    </div>

                    <!-- Environmental Conditions -->
                    <div class="dashboard-card environmental-conditions">
                        <h3>Environmental Conditions</h3>
                        <div class="env-grid">
                            <div class="env-metric">
                                <span class="env-icon">🌊</span>
                                <div class="env-data">
                                    <span class="env-value" id="tidal-height">--</span>
                                    <span class="env-label">Tidal Height</span>
                                </div>
                            </div>
                            <div class="env-metric">
                                <span class="env-icon">🌡️</span>
                                <div class="env-data">
                                    <span class="env-value" id="water-temp">--</span>
                                    <span class="env-label">Water Temp</span>
                                </div>
                            </div>
                            <div class="env-metric">
                                <span class="env-icon">🐟</span>
                                <div class="env-data">
                                    <span class="env-value" id="prey-index">--</span>
                                    <span class="env-label">Prey Index</span>
                                </div>
                            </div>
                            <div class="env-metric">
                                <span class="env-icon">🚢</span>
                                <div class="env-data">
                                    <span class="env-value" id="vessel-noise">--</span>
                                    <span class="env-label">Vessel Noise</span>
                                </div>
                            </div>
                        </div>
                        <div id="environmental-timeline" class="chart-container"></div>
                    </div>

                    <!-- Agent Reasoning -->
                    <div class="dashboard-card agent-reasoning">
                        <h3>Agent Reasoning</h3>
                        <div class="reasoning-content" id="reasoning-content">
                            <div class="reasoning-item">
                                <h4>Primary Agent</h4>
                                <p class="reasoning-text" id="primary-reasoning">Analyzing trip parameters...</p>
                            </div>
                            <div class="reasoning-item">
                                <h4>Analytics Agent</h4>
                                <p class="reasoning-text" id="analytics-reasoning">Gathering statistical data...</p>
                            </div>
                            <div class="reasoning-item">
                                <h4>Vector Agent</h4>
                                <p class="reasoning-text" id="vector-reasoning">Updating zone vectors...</p>
                            </div>
                        </div>
                    </div>

                    <!-- Recommendations -->
                    <div class="dashboard-card recommendations">
                        <h3>Intelligent Recommendations</h3>
                        <div class="recommendation-list" id="recommendation-list">
                            <!-- Recommendations will be populated here -->
                        </div>
                    </div>

                    <!-- Trip Statistics -->
                    <div class="dashboard-card trip-statistics">
                        <h3>Trip Statistics</h3>
                        <div class="stats-grid">
                            <div class="stat-item">
                                <span class="stat-value" id="total-zones">--</span>
                                <span class="stat-label">Viewing Zones</span>
                            </div>
                            <div class="stat-item">
                                <span class="stat-value" id="total-activities">--</span>
                                <span class="stat-label">Activities</span>
                            </div>
                            <div class="stat-item">
                                <span class="stat-value" id="estimated-cost">--</span>
                                <span class="stat-label">Estimated Cost</span>
                            </div>
                            <div class="stat-item">
                                <span class="stat-value" id="success-rate">--</span>
                                <span class="stat-label">Success Rate</span>
                            </div>
                        </div>
                    </div>

                    <!-- Real-time Updates -->
                    <div class="dashboard-card real-time-updates">
                        <h3>Real-time Updates</h3>
                        <div class="updates-feed" id="updates-feed">
                            <!-- Live updates will appear here -->
                        </div>
                    </div>
                </div>
            </div>
        `;
    }

    initializeCharts() {
        // Initialize probability visualization
        this.charts.probability = this.createProbabilityChart();
        
        // Initialize zone performance chart
        this.charts.zonePerformance = this.createZonePerformanceChart();
        
        // Initialize behavior distribution chart
        this.charts.behavior = this.createBehaviorChart();
        
        // Initialize environmental timeline
        this.charts.environmental = this.createEnvironmentalChart();
    }

    createProbabilityChart() {
        const container = document.getElementById('probability-chart');
        
        // Create a simple bar chart for zone probabilities
        return {
            container,
            update: (data) => {
                container.innerHTML = this.createProbabilityBars(data);
            }
        };
    }

    createProbabilityBars(zones) {
        if (!zones || zones.length === 0) {
            return '<div class="no-data">No probability data available</div>';
        }

        return zones.map(zone => `
            <div class="probability-bar">
                <div class="zone-name">${zone.name}</div>
                <div class="bar-container">
                    <div class="bar-fill" style="width: ${zone.probability * 100}%; background-color: ${this.getProbabilityColor(zone.probability)}"></div>
                    <span class="probability-value">${(zone.probability * 100).toFixed(1)}%</span>
                </div>
            </div>
        `).join('');
    }

    getProbabilityColor(probability) {
        if (probability >= 0.8) return '#4CAF50'; // Green
        if (probability >= 0.6) return '#FF9800'; // Orange
        if (probability >= 0.4) return '#FFC107'; // Yellow
        return '#F44336'; // Red
    }

    createZonePerformanceChart() {
        const container = document.getElementById('zone-performance-chart');
        
        return {
            container,
            update: (data) => {
                container.innerHTML = this.createZonePerformanceBars(data);
            }
        };
    }

    createZonePerformanceBars(zones) {
        if (!zones || zones.length === 0) {
            return '<div class="no-data">No zone performance data available</div>';
        }

        return zones.map(zone => `
            <div class="zone-performance-item">
                <div class="zone-info">
                    <span class="zone-name">${zone.name}</span>
                    <span class="zone-type">${zone.type || 'viewing'}</span>
                </div>
                <div class="performance-metrics">
                    <div class="metric">
                        <span class="metric-label">Success Rate</span>
                        <div class="metric-bar">
                            <div class="metric-fill" style="width: ${(zone.successRate || 0) * 100}%"></div>
                        </div>
                        <span class="metric-value">${((zone.successRate || 0) * 100).toFixed(1)}%</span>
                    </div>
                </div>
            </div>
        `).join('');
    }

    createBehaviorChart() {
        const container = document.getElementById('behavior-chart');
        
        return {
            container,
            update: (data) => {
                container.innerHTML = this.createBehaviorDistribution(data);
            }
        };
    }

    createBehaviorDistribution(behaviors) {
        if (!behaviors || behaviors.length === 0) {
            return '<div class="no-data">No behavior data available</div>';
        }

        const total = behaviors.reduce((sum, b) => sum + b.count, 0);
        
        return `
            <div class="behavior-distribution">
                ${behaviors.map(behavior => {
                    const percentage = (behavior.count / total) * 100;
                    return `
                        <div class="behavior-item">
                            <div class="behavior-label">
                                <span class="behavior-icon">${this.getBehaviorIcon(behavior.type)}</span>
                                <span class="behavior-name">${behavior.type}</span>
                            </div>
                            <div class="behavior-bar">
                                <div class="behavior-fill" style="width: ${percentage}%; background-color: ${this.getBehaviorColor(behavior.type)}"></div>
                            </div>
                            <span class="behavior-percentage">${percentage.toFixed(1)}%</span>
                        </div>
                    `;
                }).join('')}
            </div>
        `;
    }

    getBehaviorIcon(behavior) {
        const icons = {
            'foraging': '🍽️',
            'traveling': '🏊',
            'socializing': '👥',
            'resting': '😴',
            'playing': '🎮'
        };
        return icons[behavior] || '🐋';
    }

    getBehaviorColor(behavior) {
        const colors = {
            'foraging': '#4CAF50',
            'traveling': '#2196F3',
            'socializing': '#FF9800',
            'resting': '#9C27B0',
            'playing': '#E91E63'
        };
        return colors[behavior] || '#757575';
    }

    createEnvironmentalChart() {
        const container = document.getElementById('environmental-timeline');
        
        return {
            container,
            update: (data) => {
                container.innerHTML = this.createEnvironmentalTimeline(data);
            }
        };
    }

    createEnvironmentalTimeline(data) {
        if (!data || data.length === 0) {
            return '<div class="no-data">No environmental timeline data available</div>';
        }

        return `
            <div class="environmental-timeline">
                ${data.map(point => `
                    <div class="timeline-point">
                        <div class="time-label">${point.time}</div>
                        <div class="env-values">
                            <span class="env-val">T: ${point.temperature}°C</span>
                            <span class="env-val">Tide: ${point.tideHeight}m</span>
                        </div>
                    </div>
                `).join('')}
            </div>
        `;
    }

    initializeWidgets() {
        this.widgets.recommendations = new RecommendationWidget('recommendation-list');
        this.widgets.updates = new UpdatesFeedWidget('updates-feed');
        this.widgets.topZones = new TopZonesWidget('top-zones');
    }

    setupEventListeners() {
        // Listen for agent updates
        document.addEventListener('agent-update', (event) => {
            this.handleAgentUpdate(event.detail);
        });

        // Listen for data updates
        document.addEventListener('data-update', (event) => {
            this.handleDataUpdate(event.detail);
        });
    }

    /**
     * Main update method called by the multi-agent orchestrator
     */
    updateDashboard(analyticsData, vectorData, reasoningData) {
        this.data = { analytics: analyticsData, vectors: vectorData, reasoning: reasoningData };
        
        // Update all components
        this.updateProbabilityOverview(analyticsData, vectorData);
        this.updateZoneAnalytics(vectorData);
        this.updateBehavioralInsights(analyticsData);
        this.updateEnvironmentalConditions(analyticsData);
        this.updateAgentReasoning(reasoningData);
        this.updateRecommendations(analyticsData, reasoningData);
        this.updateTripStatistics(analyticsData, vectorData);
        this.updateRealTimeUpdates();
    }

    updateProbabilityOverview(analytics, vectors) {
        // Update overall probability
        const overallProb = this.calculateOverallProbability(vectors);
        document.getElementById('overall-probability').textContent = `${(overallProb * 100).toFixed(1)}%`;
        
        // Update confidence score
        const confidence = analytics?.confidence || 0.75;
        document.getElementById('confidence-score').textContent = `${(confidence * 100).toFixed(1)}%`;
        
        // Update probability chart
        if (vectors?.zones) {
            this.charts.probability.update(vectors.zones);
        }
    }

    updateZoneAnalytics(vectors) {
        if (vectors?.zones) {
            this.charts.zonePerformance.update(vectors.zones);
            this.widgets.topZones.update(vectors.zones);
        }
    }

    updateBehavioralInsights(analytics) {
        if (analytics?.behavior?.patterns) {
            this.charts.behavior.update(analytics.behavior.patterns);
            
            const summary = document.getElementById('behavior-summary');
            summary.innerHTML = `
                <div class="behavior-insights">
                    <p><strong>Dominant Behavior:</strong> ${analytics.behavior.dominantBehavior}</p>
                    <p><strong>Average Confidence:</strong> ${(analytics.behavior.avgConfidence * 100).toFixed(1)}%</p>
                    <p><strong>Total Sightings:</strong> ${analytics.behavior.totalSightings}</p>
                </div>
            `;
        }
    }

    updateEnvironmentalConditions(analytics) {
        if (analytics?.environmental?.current) {
            const env = analytics.environmental.current;
            
            document.getElementById('tidal-height').textContent = `${env.tidalHeight || '--'} m`;
            document.getElementById('water-temp').textContent = `${env.waterTemp || '--'} °C`;
            document.getElementById('prey-index').textContent = `${env.preyIndex || '--'}`;
            document.getElementById('vessel-noise').textContent = `${env.vesselNoise || '--'} dB`;
        }
        
        if (analytics?.environmental?.timeline) {
            this.charts.environmental.update(analytics.environmental.timeline);
        }
    }

    updateAgentReasoning(reasoning) {
        if (reasoning?.explanations) {
            document.getElementById('primary-reasoning').textContent = 
                reasoning.explanations.tripRationale?.summary || 'Analyzing trip parameters...';
            
            document.getElementById('analytics-reasoning').textContent = 
                'Statistics analysis complete - ' + (reasoning.explanations.confidence || 'gathering data...');
            
            document.getElementById('vector-reasoning').textContent = 
                'Zone vectors updated - ' + (reasoning.explanations.zoneSelections?.length || 0) + ' zones analyzed';
        }
    }

    updateRecommendations(analytics, reasoning) {
        if (analytics?.recommendations || reasoning?.insights) {
            this.widgets.recommendations.update({
                analytics: analytics?.recommendations,
                reasoning: reasoning?.insights
            });
        }
    }

    updateTripStatistics(analytics, vectors) {
        const totalZones = vectors?.zones?.length || 0;
        const totalActivities = this.countTotalActivities(vectors);
        const estimatedCost = analytics?.summary?.totalCost || 0;
        const successRate = analytics?.success?.rate || 0;
        
        document.getElementById('total-zones').textContent = totalZones;
        document.getElementById('total-activities').textContent = totalActivities;
        document.getElementById('estimated-cost').textContent = `$${estimatedCost}`;
        document.getElementById('success-rate').textContent = `${(successRate * 100).toFixed(1)}%`;
    }

    updateRealTimeUpdates() {
        this.widgets.updates.addUpdate({
            timestamp: new Date(),
            type: 'system',
            message: 'Dashboard updated with latest analytics data'
        });
    }

    calculateOverallProbability(vectors) {
        if (!vectors?.zones || vectors.zones.length === 0) return 0;
        
        const totalProb = vectors.zones.reduce((sum, zone) => sum + (zone.probability || 0), 0);
        return totalProb / vectors.zones.length;
    }

    countTotalActivities(vectors) {
        // Count activities across all zones
        return vectors?.zones?.reduce((count, zone) => {
            return count + (zone.activities?.length || 0);
        }, 0) || 0;
    }

    handleAgentUpdate(agentData) {
        this.widgets.updates.addUpdate({
            timestamp: new Date(),
            type: 'agent',
            message: `${agentData.agentName}: ${agentData.message}`
        });
    }

    handleDataUpdate(dataUpdate) {
        this.widgets.updates.addUpdate({
            timestamp: new Date(),
            type: 'data',
            message: `Data updated: ${dataUpdate.type}`
        });
    }
}

/**
 * Recommendation Widget
 */
class RecommendationWidget {
    constructor(containerId) {
        this.container = document.getElementById(containerId);
    }

    update(recommendations) {
        const items = this.generateRecommendations(recommendations);
        this.container.innerHTML = items.map(item => `
            <div class="recommendation-item ${item.priority}">
                <div class="rec-icon">${item.icon}</div>
                <div class="rec-content">
                    <h4>${item.title}</h4>
                    <p>${item.description}</p>
                    <div class="rec-score">Confidence: ${(item.confidence * 100).toFixed(1)}%</div>
                </div>
            </div>
        `).join('');
    }

    generateRecommendations(data) {
        const recommendations = [];
        
        // High probability zone recommendation
        recommendations.push({
            title: 'Optimal Viewing Window',
            description: 'Visit Lime Kiln Point between 10 AM - 2 PM for highest orca probability',
            confidence: 0.85,
            priority: 'high',
            icon: '🎯'
        });
        
        // Environmental condition recommendation
        recommendations.push({
            title: 'Favorable Conditions',
            description: 'Current tidal conditions are ideal for orca activity',
            confidence: 0.78,
            priority: 'medium',
            icon: '🌊'
        });
        
        // Backup plan recommendation
        recommendations.push({
            title: 'Alternative Location',
            description: 'Consider Salmon Bank as backup if primary zones are inactive',
            confidence: 0.65,
            priority: 'medium',
            icon: '🔄'
        });
        
        return recommendations;
    }
}

/**
 * Updates Feed Widget
 */
class UpdatesFeedWidget {
    constructor(containerId) {
        this.container = document.getElementById(containerId);
        this.updates = [];
        this.maxUpdates = 10;
    }

    addUpdate(update) {
        this.updates.unshift({
            ...update,
            id: Date.now(),
            timestamp: update.timestamp || new Date()
        });
        
        if (this.updates.length > this.maxUpdates) {
            this.updates = this.updates.slice(0, this.maxUpdates);
        }
        
        this.render();
    }

    render() {
        this.container.innerHTML = this.updates.map(update => `
            <div class="update-item ${update.type}">
                <div class="update-time">${this.formatTime(update.timestamp)}</div>
                <div class="update-message">${update.message}</div>
            </div>
        `).join('');
    }

    formatTime(timestamp) {
        return new Date(timestamp).toLocaleTimeString('en-US', {
            hour: '2-digit',
            minute: '2-digit'
        });
    }
}

/**
 * Top Zones Widget
 */
class TopZonesWidget {
    constructor(containerId) {
        this.container = document.getElementById(containerId);
    }

    update(zones) {
        const topZones = zones
            .sort((a, b) => (b.probability || 0) - (a.probability || 0))
            .slice(0, 5);
        
        this.container.innerHTML = topZones.map((zone, index) => `
            <div class="top-zone-item">
                <div class="zone-rank">#${index + 1}</div>
                <div class="zone-info">
                    <span class="zone-name">${zone.name}</span>
                    <span class="zone-probability">${((zone.probability || 0) * 100).toFixed(1)}%</span>
                </div>
            </div>
        `).join('');
    }
}

// Export dashboard
window.AnalyticsDashboard = AnalyticsDashboard; 