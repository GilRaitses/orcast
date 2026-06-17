describe('Async Backend Data Loading Debug', () => {
  let apiErrors: any[] = [];
  let consoleErrors: any[] = [];
  let networkRequests: any[] = [];

  beforeEach(() => {
    apiErrors = [];
    consoleErrors = [];
    networkRequests = [];
    
    // Intercept all HTTP requests
    cy.intercept('**', (req) => {
      networkRequests.push({
        url: req.url,
        method: req.method,
        timestamp: new Date()
      });
    }).as('allRequests');
  });

  it('should analyze all async calls and backend data loading across components', () => {
    cy.visit('https://orca-904de.web.app/agent-spatial-demo');
    cy.viewport(1400, 900);
    
    // Capture JavaScript errors and console logs
    cy.window().then((win) => {
      // Override console methods to capture errors
      const originalError = win.console.error;
      const originalWarn = win.console.warn;
      const originalLog = win.console.log;
      
      win.console.error = function(...args) {
        consoleErrors.push({ type: 'error', message: args.join(' '), timestamp: new Date() });
        originalError.apply(win.console, args);
      };
      
      win.console.warn = function(...args) {
        consoleErrors.push({ type: 'warn', message: args.join(' '), timestamp: new Date() });
        originalWarn.apply(win.console, args);
      };
      
      win.console.log = function(...args) {
        const message = args.join(' ');
        if (message.includes('❌') || message.includes('Error') || message.includes('Failed')) {
          consoleErrors.push({ type: 'log_error', message, timestamp: new Date() });
        }
        originalLog.apply(win.console, args);
      };
      
      // Capture unhandled promise rejections
      win.addEventListener('unhandledrejection', (event) => {
        apiErrors.push({
          type: 'unhandled_promise_rejection',
          message: event.reason.toString(),
          timestamp: new Date()
        });
      });
      
      // Capture JavaScript errors
      win.addEventListener('error', (event) => {
        apiErrors.push({
          type: 'javascript_error',
          message: event.message,
          filename: event.filename,
          line: event.lineno,
          timestamp: new Date()
        });
      });
    });

    cy.wait(3000);
    cy.screenshot('01-initial-load-with-monitoring');

    // Test 1: Agent Orchestrator Service async calls
    cy.log('🔍 Testing Agent Orchestrator async calls...');
    cy.get('button:contains("Start Agent Orchestration")').click();
    cy.wait(5000); // Give time for async operations
    cy.screenshot('02-agent-orchestration-started');

    // Test 2: Map Configuration Service async calls  
    cy.log('🔍 Testing Map Configuration Service async calls...');
    cy.get('button:contains("Generate Map Configuration")').click();
    cy.wait(3000);
    cy.screenshot('03-map-config-generated');

    // Test 3: Agent Chat async calls
    cy.log('🔍 Testing Agent Chat async calls...');
    cy.get('button:contains("Show Agent Chat")').then($btn => {
      if ($btn.is(':visible')) {
        cy.wrap($btn).click();
        cy.wait(1000);
        
        // Try each agent type
        const agents = ['📊 Analytics Agent', '🗺️ Spatial Forecast Agent', '🐋 Whale Research Agent'];
        agents.forEach((agentName, index) => {
          cy.get('body').then($body => {
            if ($body.find(`.agent-tab:contains("${agentName}")`).length > 0) {
              cy.get(`.agent-tab:contains("${agentName}")`).click();
              cy.wait(500);
              
              // Send a test prompt to trigger async backend calls
              if ($body.find('.prompt-textarea').length > 0) {
                cy.get('.prompt-textarea').clear().type(`Test backend call ${index + 1}`);
                
                if ($body.find('.send-prompt-btn').length > 0) {
                  cy.get('.send-prompt-btn').click();
                  cy.wait(2000); // Wait for async response
                }
              }
            }
          });
        });
        
        cy.screenshot('04-agent-chat-tested');
      }
    });

    // Test 4: Direct backend API calls
    cy.log('🔍 Testing direct backend API endpoints...');
    cy.request({
      url: 'https://orcast-production-backend-2cvqukvhga-uw.a.run.app/health',
      failOnStatusCode: false
    }).then((response) => {
      if (response.status !== 200) {
        apiErrors.push({
          type: 'backend_health_check_failed',
          status: response.status,
          body: response.body
        });
      }
    });

    // Test 5: Check for data loading in components
    cy.log('🔍 Checking component data loading...');
    cy.get('body').then($body => {
      // Check spatial forecasts
      const forecastItems = $body.find('.forecast-item').length;
      if (forecastItems === 0) {
        apiErrors.push({
          type: 'no_spatial_forecasts_loaded',
          message: 'No forecast items found in DOM'
        });
      }
      
      // Check agent messages
      const agentMessages = $body.find('.agent-messages .message').length;
      if (agentMessages === 0) {
        apiErrors.push({
          type: 'no_agent_messages_loaded', 
          message: 'No agent messages found in DOM'
        });
      }
      
      // Check map configuration
      const mapConfig = $body.find('.config-overlay').length;
      if (mapConfig === 0) {
        apiErrors.push({
          type: 'no_map_config_loaded',
          message: 'No map configuration overlay found'
        });
      }
    });

    cy.wait(2000);

    // Test 6: Analyze network requests
    cy.then(() => {
      cy.log('🔍 Analyzing network requests...');
      
      const backendCalls = networkRequests.filter(req => 
        req.url.includes('orcast-production-backend') || 
        req.url.includes('gemma') ||
        req.url.includes('/api/') ||
        req.url.includes('/forecast/') ||
        req.url.includes('/predictions/')
      );
      
      if (backendCalls.length === 0) {
        apiErrors.push({
          type: 'no_backend_requests_made',
          message: 'No backend API requests detected',
          totalRequests: networkRequests.length
        });
      }
      
      cy.log(`📊 Total network requests: ${networkRequests.length}`);
      cy.log(`📊 Backend API calls: ${backendCalls.length}`);
    });

    // Generate comprehensive error report
    cy.then(() => {
      const totalErrors = apiErrors.length + consoleErrors.length;
      
      cy.window().then((win) => {
        const reportOverlay = win.document.createElement('div');
        reportOverlay.style.position = 'fixed';
        reportOverlay.style.top = '20px';
        reportOverlay.style.left = '20px';
        reportOverlay.style.width = '600px';
        reportOverlay.style.maxHeight = '80vh';
        reportOverlay.style.overflowY = 'auto';
        reportOverlay.style.backgroundColor = totalErrors > 0 ? 'rgba(244, 67, 54, 0.95)' : 'rgba(76, 175, 80, 0.95)';
        reportOverlay.style.color = 'white';
        reportOverlay.style.padding = '20px';
        reportOverlay.style.borderRadius = '8px';
        reportOverlay.style.zIndex = '9999';
        reportOverlay.style.fontSize = '12px';
        reportOverlay.style.fontFamily = 'monospace';
        
        let reportHTML = `
          <h3>${totalErrors > 0 ? '❌' : '✅'} Async Backend Debug Report</h3>
          <p><strong>Total Issues Found:</strong> ${totalErrors}</p>
          <p><strong>Network Requests:</strong> ${networkRequests.length}</p>
          <p><strong>Console Errors:</strong> ${consoleErrors.length}</p>
          <p><strong>API Errors:</strong> ${apiErrors.length}</p>
          <hr style="margin: 15px 0; border-color: rgba(255,255,255,0.3);">
        `;
        
        if (apiErrors.length > 0) {
          reportHTML += '<h4>🚨 API Errors:</h4>';
          apiErrors.forEach((error, index) => {
            reportHTML += `<div style="margin: 8px 0; padding: 8px; background: rgba(0,0,0,0.3); border-radius: 4px;">
              <strong>${index + 1}. ${error.type}</strong><br>
              ${error.message || error.status || 'Unknown error'}<br>
              <small>${error.timestamp ? error.timestamp.toLocaleTimeString() : ''}</small>
            </div>`;
          });
        }
        
        if (consoleErrors.length > 0) {
          reportHTML += '<h4>📝 Console Errors:</h4>';
          consoleErrors.slice(0, 5).forEach((error, index) => {
            reportHTML += `<div style="margin: 5px 0; padding: 5px; background: rgba(0,0,0,0.3); border-radius: 3px;">
              <strong>${error.type}:</strong> ${error.message.substring(0, 100)}...
            </div>`;
          });
          if (consoleErrors.length > 5) {
            reportHTML += `<p><em>... and ${consoleErrors.length - 5} more</em></p>`;
          }
        }
        
        if (totalErrors === 0) {
          reportHTML += `
            <h4>✅ All Systems Working:</h4>
            <ul>
              <li>No JavaScript errors detected</li>
              <li>No unhandled promise rejections</li>
              <li>Backend health check passed</li>
              <li>Component data loading verified</li>
            </ul>
          `;
        }
        
        reportHTML += `
          <hr style="margin: 15px 0; border-color: rgba(255,255,255,0.3);">
          <h4>🔧 Recommended Actions:</h4>
          <ul>
            <li>Check async/await patterns in services</li>
            <li>Verify backend API endpoints are accessible</li>
            <li>Review error handling in HTTP calls</li>
            <li>Test promise rejection handling</li>
            <li>Validate data loading in ngOnInit methods</li>
          </ul>
        `;
        
        reportOverlay.innerHTML = reportHTML;
        win.document.body.appendChild(reportOverlay);
      });
    });

    cy.wait(3000);
    cy.screenshot('05-final-async-debug-report');

    // Log all findings
    cy.then(() => {
      cy.log('🔍 ASYNC DEBUG SUMMARY:');
      cy.log(`Total API Errors: ${apiErrors.length}`);
      cy.log(`Total Console Errors: ${consoleErrors.length}`);
      cy.log(`Total Network Requests: ${networkRequests.length}`);
      
      if (apiErrors.length > 0) {
        cy.log('🚨 API ERRORS FOUND:');
        apiErrors.forEach((error, index) => {
          cy.log(`${index + 1}. ${error.type}: ${error.message || 'Unknown'}`);
        });
      }
      
      if (consoleErrors.length > 0) {
        cy.log('📝 CONSOLE ERRORS FOUND:');
        consoleErrors.slice(0, 3).forEach((error, index) => {
          cy.log(`${index + 1}. ${error.type}: ${error.message.substring(0, 50)}...`);
        });
      }
    });
  });
}); 