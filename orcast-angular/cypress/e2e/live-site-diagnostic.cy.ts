describe('Live Site Diagnostic - What Actually Works', () => {
  it('should identify what elements exist and work on the live site', () => {
    cy.visit('/agent-spatial-demo');
    cy.viewport(1400, 900);
    cy.wait(3000);
    
    // Log what we can find
    cy.get('body').then($body => {
      // Check if main component exists
      if ($body.find('orcast-agent-spatial-demo').length > 0) {
        cy.log('✅ Main component found: orcast-agent-spatial-demo');
      } else {
        cy.log('❌ Main component NOT found');
      }
      
      // Check for header
      if ($body.find('h1').length > 0) {
        cy.get('h1').first().then($h1 => {
          cy.log('✅ Header found: ' + $h1.text());
        });
      }
      
      // Check for agent chat elements
      if ($body.find('.toggle-chat-btn').length > 0) {
        cy.log('✅ Toggle chat button found');
        cy.get('.toggle-chat-btn').click();
        cy.wait(1000);
        
        if ($body.find('.agent-chat-interface').length > 0) {
          cy.log('✅ Agent chat interface exists');
        } else {
          cy.log('❌ Agent chat interface NOT found after click');
        }
      } else {
        cy.log('❌ Toggle chat button NOT found');
      }
      
      // Check for agent tabs
      if ($body.find('.agent-tab').length > 0) {
        cy.get('.agent-tab').then($tabs => {
          cy.log('✅ Found ' + $tabs.length + ' agent tabs');
          $tabs.each((i, tab) => {
            cy.log('Agent tab ' + i + ': ' + Cypress.$(tab).text());
          });
        });
      } else {
        cy.log('❌ No agent tabs found');
      }
      
      // Check for common panels
      const panelSelectors = [
        '.agent-panel',
        '.forecast-panel', 
        '.data-source-verification',
        '.spatial-forecasts',
        '.agent-messages'
      ];
      
      panelSelectors.forEach(selector => {
        if ($body.find(selector).length > 0) {
          cy.log('✅ Found panel: ' + selector);
        } else {
          cy.log('❌ Panel NOT found: ' + selector);
        }
      });
      
      // Check for buttons
      const buttonTexts = [
        'Start Agent Orchestration',
        'Generate Map Configuration', 
        'Show Agent Chat',
        'Show Forecast'
      ];
      
      buttonTexts.forEach(text => {
        if ($body.find('button:contains("' + text + '")').length > 0) {
          cy.log('✅ Found button: ' + text);
        } else {
          cy.log('❌ Button NOT found: ' + text);
        }
      });
    });
    
    // Take a screenshot of what we actually see
    cy.screenshot('live-site-actual-state', {
      capture: 'viewport',
      overwrite: true
    });
    
    // Try clicking buttons that exist
    cy.get('body').then($body => {
      if ($body.find('button:contains("Start Agent Orchestration")').length > 0) {
        cy.log('🔄 Attempting to click Start Agent Orchestration');
        cy.get('button:contains("Start Agent Orchestration")').click();
        cy.wait(2000);
        cy.screenshot('after-start-agents', { capture: 'viewport' });
      }
      
      if ($body.find('button:contains("Generate Map Configuration")').length > 0) {
        cy.log('🔄 Attempting to click Generate Map Configuration');
        cy.get('button:contains("Generate Map Configuration")').click();
        cy.wait(2000);
        cy.screenshot('after-map-config', { capture: 'viewport' });
      }
    });
    
    // Final diagnostic summary
    cy.window().then((win) => {
      const overlay = win.document.createElement('div');
      overlay.style.position = 'fixed';
      overlay.style.top = '20px';
      overlay.style.left = '20px';
      overlay.style.width = '400px';
      overlay.style.backgroundColor = 'rgba(255, 0, 0, 0.9)';
      overlay.style.color = 'white';
      overlay.style.padding = '20px';
      overlay.style.zIndex = '9999';
      overlay.style.border = '2px solid red';
      overlay.style.borderRadius = '8px';
      
      const title = win.document.createElement('h3');
      title.textContent = '🔍 Live Site Diagnostic Results';
      title.style.margin = '0 0 15px 0';
      overlay.appendChild(title);
      
      const status = win.document.createElement('div');
      status.innerHTML = `
        <p>✅ Site loads: YES</p>
        <p>🤖 Agent interface: Testing...</p>
        <p>📊 Spatial forecasts: ${win.document.querySelector('.spatial-forecasts') ? 'FOUND' : 'NOT FOUND'}</p>
        <p>🗺️ Map config: Testing...</p>
        <p>💬 Chat system: Testing...</p>
      `;
      overlay.appendChild(status);
      
      win.document.body.appendChild(overlay);
    });
    
    cy.wait(3000);
    cy.screenshot('diagnostic-complete', { capture: 'viewport' });
  });
}); 