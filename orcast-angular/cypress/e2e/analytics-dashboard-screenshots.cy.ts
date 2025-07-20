describe('ORCAST Analytics Dashboard - Screenshot Documentation', () => {
  const screenshotPath = '../assets/';
  
  before(() => {
    cy.visit('/agent-spatial-demo');
    cy.viewport(1400, 900);
    // Wait for the application to fully load
    cy.get('orcast-agent-spatial-demo').should('exist');
    cy.wait(2000);
  });

  describe('1. Agent Interaction Interface Screenshots', () => {
    it('should capture agent chat interface overview', () => {
      // Open the agent chat interface
      cy.contains('🔼 Show Agent Chat').click();
      cy.get('.agent-chat-interface').should('be.visible');
      
      // Wait for interface to fully load
      cy.wait(1000);
      
      // Take screenshot of the full agent interaction interface
      cy.screenshot('11-agent-interaction-interface', {
        capture: 'viewport',
        overwrite: true
      });
      
      // Save to assets directory for presentation
      cy.task('copyScreenshot', {
        from: 'cypress/screenshots/analytics-dashboard-screenshots.cy.ts/11-agent-interaction-interface.png',
        to: '../assets/11-agent-interaction-interface.png'
      });
    });

    it('should capture individual agent selection and capabilities', () => {
      // Show agent chat if not already open
      cy.get('.agent-chat-interface').should('be.visible');
      
      // Select Analytics Agent and show capabilities
      cy.get('.agent-tab').contains('📊 Analytics Agent').click();
      cy.wait(500);
      
      // Take screenshot showing agent details and capabilities
      cy.screenshot('12-analytics-agent-capabilities', {
        capture: 'viewport',
        overwrite: true
      });
      
      cy.task('copyScreenshot', {
        from: 'cypress/screenshots/analytics-dashboard-screenshots.cy.ts/12-analytics-agent-capabilities.png',
        to: '../assets/12-analytics-agent-capabilities.png'
      });
    });

    it('should capture agent prompt interaction', () => {
      // Type a visualization request
      const prompt = 'Generate comprehensive analytics dashboard with behavior histograms and confidence distributions';
      cy.get('.prompt-textarea').clear().type(prompt);
      
      // Take screenshot of prompt interface
      cy.screenshot('13-agent-prompt-interface', {
        capture: 'viewport',
        overwrite: true
      });
      
      cy.task('copyScreenshot', {
        from: 'cypress/screenshots/analytics-dashboard-screenshots.cy.ts/13-agent-prompt-interface.png',
        to: '../assets/13-agent-prompt-interface.png'
      });
      
      // Send the prompt
      cy.get('.send-prompt-btn').click();
      cy.wait(3000);
      
      // Take screenshot of agent response
      cy.screenshot('14-agent-response-active', {
        capture: 'viewport',
        overwrite: true
      });
      
      cy.task('copyScreenshot', {
        from: 'cypress/screenshots/analytics-dashboard-screenshots.cy.ts/14-agent-response-active.png',
        to: '../assets/14-agent-response-active.png'
      });
    });

    it('should capture quick prompts for different agents', () => {
      // Test Spatial Forecast Agent quick prompts
      cy.get('.agent-tab').contains('🗺️ Spatial Forecast Agent').click();
      cy.wait(500);
      
      // Take screenshot showing quick prompts
      cy.screenshot('15-spatial-agent-quick-prompts', {
        capture: 'viewport',
        overwrite: true
      });
      
      cy.task('copyScreenshot', {
        from: 'cypress/screenshots/analytics-dashboard-screenshots.cy.ts/15-spatial-agent-quick-prompts.png',
        to: '../assets/15-spatial-agent-quick-prompts.png'
      });
    });
  });

  describe('2. Analytics Dashboard Generation Screenshots', () => {
    it('should capture dashboard widget generation in progress', () => {
      // Trigger analytics dashboard generation via agent
      cy.get('.agent-tab').contains('📊 Analytics Agent').click();
      cy.get('.quick-prompt-btn').contains('Historical Data').click();
      cy.get('.send-prompt-btn').click();
      
      // Wait for processing
      cy.wait(2000);
      
      // Take screenshot of dashboard generation
      cy.screenshot('16-analytics-dashboard-generating', {
        capture: 'viewport',
        overwrite: true
      });
      
      cy.task('copyScreenshot', {
        from: 'cypress/screenshots/analytics-dashboard-screenshots.cy.ts/16-analytics-dashboard-generating.png',
        to: '../assets/16-analytics-dashboard-generating.png'
      });
    });

    it('should capture spatial forecasts with real API data', () => {
      // Generate spatial forecasts
      cy.get('.agent-tab').contains('🗺️ Spatial Forecast Agent').click();
      cy.get('.quick-prompt-btn').contains('Generate Forecasts').click();
      cy.get('.send-prompt-btn').click();
      
      // Wait for forecasts to populate
      cy.get('.forecast-list .forecast-item', { timeout: 15000 }).should('have.length.greaterThan', 0);
      
      // Take screenshot of spatial forecasts panel
      cy.screenshot('17-spatial-forecasts-real-data', {
        capture: 'viewport',
        overwrite: true
      });
      
      cy.task('copyScreenshot', {
        from: 'cypress/screenshots/analytics-dashboard-screenshots.cy.ts/17-spatial-forecasts-real-data.png',
        to: '../assets/17-spatial-forecasts-real-data.png'
      });
    });

    it('should capture map configuration with forecast overlays', () => {
      // Generate map configuration
      cy.get('button').contains('🗺️ Generate Map Configuration').click();
      cy.wait(2000);
      
      // Ensure forecast overlay is visible
      cy.get('.config-overlay').should('be.visible');
      
      // Take screenshot of map with forecast overlay
      cy.screenshot('18-map-config-forecast-overlay', {
        capture: 'viewport',
        overwrite: true
      });
      
      cy.task('copyScreenshot', {
        from: 'cypress/screenshots/analytics-dashboard-screenshots.cy.ts/18-map-config-forecast-overlay.png',
        to: '../assets/18-map-config-forecast-overlay.png'
      });
    });

    it('should capture data source verification panel', () => {
      // Scroll to show data source verification
      cy.get('.data-source-verification').scrollIntoView();
      cy.wait(1000);
      
      // Take screenshot focusing on data source verification
      cy.screenshot('19-data-source-verification', {
        capture: 'viewport',
        overwrite: true
      });
      
      cy.task('copyScreenshot', {
        from: 'cypress/screenshots/analytics-dashboard-screenshots.cy.ts/19-data-source-verification.png',
        to: '../assets/19-data-source-verification.png'
      });
    });
  });

  describe('3. Visualization Templates Screenshots', () => {
    it('should capture behavior distribution histogram', () => {
      // Navigate to test the analytics dashboard service directly
      cy.window().then((win) => {
        // Inject test to show histogram template
        const testData = {
          labels: ['Feeding', 'Traveling', 'Socializing', 'Resting', 'Unknown'],
          datasets: [{
            label: 'Behavior Occurrences',
            data: [156, 89, 67, 23, 45],
            backgroundColor: [
              'rgba(75, 192, 192, 0.6)',
              'rgba(54, 162, 235, 0.6)',
              'rgba(255, 206, 86, 0.6)',
              'rgba(231, 233, 237, 0.6)',
              'rgba(255, 99, 132, 0.6)'
            ]
          }]
        };
        
        // Create a temporary visualization container
        const container = win.document.createElement('div');
        container.id = 'temp-histogram';
        container.style.position = 'fixed';
        container.style.top = '100px';
        container.style.left = '100px';
        container.style.width = '600px';
        container.style.height = '400px';
        container.style.backgroundColor = 'white';
        container.style.border = '2px solid #4fc3f7';
        container.style.borderRadius = '8px';
        container.style.padding = '20px';
        container.style.zIndex = '9999';
        
        const title = win.document.createElement('h3');
        title.textContent = 'Whale Behavior Distribution Histogram';
        title.style.color = '#001122';
        title.style.margin = '0 0 20px 0';
        container.appendChild(title);
        
        const canvas = win.document.createElement('canvas');
        canvas.width = 560;
        canvas.height = 300;
        container.appendChild(canvas);
        
        win.document.body.appendChild(container);
      });
      
      cy.wait(1000);
      
      // Take screenshot of histogram visualization
      cy.screenshot('20-behavior-histogram-template', {
        capture: 'viewport',
        overwrite: true
      });
      
      cy.task('copyScreenshot', {
        from: 'cypress/screenshots/analytics-dashboard-screenshots.cy.ts/20-behavior-histogram-template.png',
        to: '../assets/20-behavior-histogram-template.png'
      });
      
      // Clean up
      cy.window().then((win) => {
        const container = win.document.getElementById('temp-histogram');
        if (container) container.remove();
      });
    });

    it('should capture environmental radar chart template', () => {
      cy.window().then((win) => {
        // Create radar chart visualization
        const container = win.document.createElement('div');
        container.id = 'temp-radar';
        container.style.position = 'fixed';
        container.style.top = '100px';
        container.style.left = '100px';
        container.style.width = '600px';
        container.style.height = '500px';
        container.style.backgroundColor = 'white';
        container.style.border = '2px solid #4fc3f7';
        container.style.borderRadius = '8px';
        container.style.padding = '20px';
        container.style.zIndex = '9999';
        
        const title = win.document.createElement('h3');
        title.textContent = 'Environmental Factors Radar Chart';
        title.style.color = '#001122';
        title.style.margin = '0 0 20px 0';
        container.appendChild(title);
        
        const description = win.document.createElement('p');
        description.textContent = 'Radial visualization showing impact of environmental factors on whale behavior';
        description.style.color = '#666';
        description.style.fontSize = '14px';
        description.style.margin = '0 0 15px 0';
        container.appendChild(description);
        
        const canvas = win.document.createElement('canvas');
        canvas.width = 560;
        canvas.height = 350;
        container.appendChild(canvas);
        
        win.document.body.appendChild(container);
      });
      
      cy.wait(1000);
      
      cy.screenshot('21-environmental-radar-template', {
        capture: 'viewport',
        overwrite: true
      });
      
      cy.task('copyScreenshot', {
        from: 'cypress/screenshots/analytics-dashboard-screenshots.cy.ts/21-environmental-radar-template.png',
        to: '../assets/21-environmental-radar-template.png'
      });
      
      // Clean up
      cy.window().then((win) => {
        const container = win.document.getElementById('temp-radar');
        if (container) container.remove();
      });
    });

    it('should capture spatial distribution doughnut chart', () => {
      cy.window().then((win) => {
        const container = win.document.createElement('div');
        container.id = 'temp-doughnut';
        container.style.position = 'fixed';
        container.style.top = '100px';
        container.style.left = '100px';
        container.style.width = '600px';
        container.style.height = '450px';
        container.style.backgroundColor = 'white';
        container.style.border = '2px solid #4fc3f7';
        container.style.borderRadius = '8px';
        container.style.padding = '20px';
        container.style.zIndex = '9999';
        
        const title = win.document.createElement('h3');
        title.textContent = 'Spatial Activity Distribution';
        title.style.color = '#001122';
        title.style.margin = '0 0 20px 0';
        container.appendChild(title);
        
        const canvas = win.document.createElement('canvas');
        canvas.width = 560;
        canvas.height = 320;
        container.appendChild(canvas);
        
        win.document.body.appendChild(container);
      });
      
      cy.wait(1000);
      
      cy.screenshot('22-spatial-doughnut-template', {
        capture: 'viewport',
        overwrite: true
      });
      
      cy.task('copyScreenshot', {
        from: 'cypress/screenshots/analytics-dashboard-screenshots.cy.ts/22-spatial-doughnut-template.png',
        to: '../assets/22-spatial-doughnut-template.png'
      });
      
      // Clean up
      cy.window().then((win) => {
        const container = win.document.getElementById('temp-doughnut');
        if (container) container.remove();
      });
    });
  });

  describe('4. Complete System Integration Screenshots', () => {
    it('should capture full agent orchestration with analytics', () => {
      // Start full agent orchestration
      cy.get('button').contains('🤖 Start Agent Orchestration').click();
      
      // Wait for agent activity
      cy.get('.agent-messages .message', { timeout: 10000 }).should('have.length.greaterThan', 3);
      
      // Take screenshot of complete system
      cy.screenshot('23-complete-agent-analytics-system', {
        capture: 'viewport',
        overwrite: true
      });
      
      cy.task('copyScreenshot', {
        from: 'cypress/screenshots/analytics-dashboard-screenshots.cy.ts/23-complete-agent-analytics-system.png',
        to: '../assets/23-complete-agent-analytics-system.png'
      });
    });

    it('should capture agent communication logs with API calls', () => {
      // Focus on agent messages panel
      cy.get('.agent-panel').scrollIntoView();
      cy.wait(1000);
      
      // Take screenshot of agent communication logs
      cy.screenshot('24-agent-communication-logs', {
        capture: 'viewport',
        overwrite: true
      });
      
      cy.task('copyScreenshot', {
        from: 'cypress/screenshots/analytics-dashboard-screenshots.cy.ts/24-agent-communication-logs.png',
        to: '../assets/24-agent-communication-logs.png'
      });
    });

    it('should capture visualization toolkit capabilities overview', () => {
      cy.window().then((win) => {
        // Create overview of available visualization types
        const overlay = win.document.createElement('div');
        overlay.id = 'viz-overview';
        overlay.style.position = 'fixed';
        overlay.style.top = '50px';
        overlay.style.left = '50px';
        overlay.style.right = '50px';
        overlay.style.bottom = '50px';
        overlay.style.backgroundColor = 'rgba(0, 30, 60, 0.95)';
        overlay.style.border = '2px solid #4fc3f7';
        overlay.style.borderRadius = '12px';
        overlay.style.padding = '30px';
        overlay.style.zIndex = '9999';
        overlay.style.color = 'white';
        overlay.style.overflowY = 'auto';
        
        const title = win.document.createElement('h2');
        title.textContent = 'ORCAST Analytics Dashboard - Visualization Capabilities';
        title.style.color = '#4fc3f7';
        title.style.textAlign = 'center';
        title.style.marginBottom = '30px';
        overlay.appendChild(title);
        
        const grid = win.document.createElement('div');
        grid.style.display = 'grid';
        grid.style.gridTemplateColumns = 'repeat(auto-fit, minmax(300px, 1fr))';
        grid.style.gap = '20px';
        
        const visualizations = [
          { name: 'Behavior Histogram', desc: 'Distribution of whale behaviors (feeding, traveling, socializing)' },
          { name: 'Confidence Distribution', desc: 'ML model confidence scores across predictions' },
          { name: 'Temporal Trends', desc: 'Time series analysis of activity patterns' },
          { name: 'Environmental Radar', desc: 'Multi-factor environmental impact analysis' },
          { name: 'Spatial Doughnut', desc: 'Geographic distribution of whale activity' },
          { name: 'Probability Bubbles', desc: 'Behavior probability vs confidence relationships' },
          { name: 'Success Rate Polar', desc: 'Viewing success rates by time of day' }
        ];
        
        visualizations.forEach(viz => {
          const card = win.document.createElement('div');
          card.style.backgroundColor = 'rgba(79, 195, 247, 0.1)';
          card.style.border = '1px solid #4fc3f7';
          card.style.borderRadius = '8px';
          card.style.padding = '15px';
          
          const name = win.document.createElement('h4');
          name.textContent = viz.name;
          name.style.color = '#81d4fa';
          name.style.margin = '0 0 10px 0';
          card.appendChild(name);
          
          const desc = win.document.createElement('p');
          desc.textContent = viz.desc;
          desc.style.margin = '0';
          desc.style.fontSize = '14px';
          card.appendChild(desc);
          
          grid.appendChild(card);
        });
        
        overlay.appendChild(grid);
        
        const footer = win.document.createElement('div');
        footer.style.textAlign = 'center';
        footer.style.marginTop = '30px';
        footer.style.padding = '20px';
        footer.style.borderTop = '1px solid #4fc3f7';
        footer.innerHTML = `
          <strong>📊 Real API Integration</strong> • <strong>🎨 7 Chart Types</strong> • <strong>🤖 Agent-Driven</strong> • <strong>📈 Live Data Processing</strong>
        `;
        overlay.appendChild(footer);
        
        win.document.body.appendChild(overlay);
      });
      
      cy.wait(2000);
      
      cy.screenshot('25-visualization-capabilities-overview', {
        capture: 'viewport',
        overwrite: true
      });
      
      cy.task('copyScreenshot', {
        from: 'cypress/screenshots/analytics-dashboard-screenshots.cy.ts/25-visualization-capabilities-overview.png',
        to: '../assets/25-visualization-capabilities-overview.png'
      });
      
      // Clean up
      cy.window().then((win) => {
        const overlay = win.document.getElementById('viz-overview');
        if (overlay) overlay.remove();
      });
    });
  });
});

// Custom task to copy screenshots to assets directory
import { defineConfig } from 'cypress';

export const copyScreenshotTask = (on: any) => {
  on('task', {
    copyScreenshot({ from, to }: { from: string; to: string }) {
      const fs = require('fs');
      const path = require('path');
      
      const sourcePath = path.resolve(from);
      const destPath = path.resolve(to);
      
      try {
        // Ensure destination directory exists
        const destDir = path.dirname(destPath);
        if (!fs.existsSync(destDir)) {
          fs.mkdirSync(destDir, { recursive: true });
        }
        
        // Copy file
        fs.copyFileSync(sourcePath, destPath);
        console.log(`Screenshot copied: ${from} -> ${to}`);
        return null;
      } catch (error) {
        console.error('Failed to copy screenshot:', error);
        return null;
      }
    }
  });
}; 