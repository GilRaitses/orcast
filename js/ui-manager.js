// ORCAST UI Controller
// Handles tab switching, interface updates, and general UI management

class UIController {
    constructor() {
        this.activeTab = 'map';
        this.orcastMap = null;
    }

    initialize() {
        this.setupTabNavigation();
        this.updateTimestamp();
        this.hideLoadingScreen();
        
        // Initialize components
        window.apiTester.setupAPIButtons();
    }

    setMapInstance(mapInstance) {
        this.orcastMap = mapInstance;
    }

    setupTabNavigation() {
        document.querySelectorAll('.tab-button').forEach(button => {
            button.addEventListener('click', (e) => {
                const tabName = e.target.textContent.toLowerCase().replace(/[^a-z]/g, '');
                this.switchTab(tabName, e.target);
            });
        });
    }

    switchTab(tabName, buttonElement) {
        // Hide all tab contents
        document.querySelectorAll('.tab-content').forEach(tab => {
            tab.classList.remove('active');
        });
        
        // Remove active class from all tab buttons
        document.querySelectorAll('.tab-button').forEach(btn => {
            btn.classList.remove('active');
        });
        
        // Show selected tab content
        const tabMap = {
            'probabilitymap': 'map',
            'datasources': 'data',
            'backendinspection': 'inspection',
            'analyticsmodeling': 'analytics'
        };
        
        const targetTab = tabMap[tabName] || tabName;
        const tabElement = document.getElementById(targetTab + '-tab');
        if (tabElement) {
            tabElement.classList.add('active');
        }
        
        // Add active class to clicked button
        if (buttonElement) {
            buttonElement.classList.add('active');
        }
        
        this.activeTab = targetTab;
    }

    updateTimestamp() {
        const now = new Date();
        document.getElementById('time').textContent = now.toLocaleTimeString();
        
        // Update every minute
        setTimeout(() => this.updateTimestamp(), 60000);
    }

    hideLoadingScreen() {
        setTimeout(() => {
            const loading = document.getElementById('loading');
            if (loading) {
                loading.classList.add('hidden');
                console.log('ORCAST map loaded successfully!');
            }
        }, 1000);
    }

    showInfo() {
        alert('ORCAST - Orca Behavioral Analysis\n\nReal-time probability mapping using machine learning and biologging data from the San Juan Islands.\n\nDeveloped for marine conservation research.');
    }

    // Global functions that need to be accessible from HTML
    setupGlobalFunctions() {
        window.switchTab = (tabName, event) => this.switchTab(tabName, event?.target);
        window.showInfo = () => this.showInfo();
        window.testEndpoint = (endpoint, responseId) => window.apiTester.testEndpoint(endpoint, responseId);
        
        // Map control functions
        if (this.orcastMap) {
            window.setTimeUnit = (unit) => this.orcastMap.setTimeUnit(unit);
            window.navigateRelative = (offset) => this.orcastMap.navigateRelative(offset);
            window.updateThreshold = (value) => this.orcastMap.updateThreshold(value);
            window.updateTimeFromSlider = (value) => {
                this.orcastMap.currentPeriodOffset = parseInt(value);
                this.orcastMap.updatePeriodDisplay();
                this.orcastMap.updateHeatmapData();
            };
        }
    }
}

// Export for use
window.uiController = new UIController(); 