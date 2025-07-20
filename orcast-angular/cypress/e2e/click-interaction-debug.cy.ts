describe('Click Interaction Debug', () => {
  it('should debug exactly what happens when clicking agent chat button', () => {
    // Capture JavaScript errors
    let jsErrors = [];
    
    cy.visit('https://orca-904de.web.app/agent-spatial-demo');
    cy.viewport(1400, 900);
    
    // Listen for JavaScript errors
    cy.window().then((win) => {
      win.addEventListener('error', (error) => {
        jsErrors.push({
          message: error.message,
          source: error.filename,
          line: error.lineno,
          stack: error.error?.stack
        });
        cy.log('❌ JS Error: ' + error.message);
      });
      
      win.addEventListener('unhandledrejection', (event) => {
        jsErrors.push({
          message: 'Promise rejection: ' + event.reason,
          type: 'promise'
        });
        cy.log('❌ Promise Error: ' + event.reason);
      });
    });
    
    cy.wait(3000);
    cy.screenshot('01-page-loaded');
    
    // Check if Angular is loaded
    cy.window().then((win) => {
      if (win.ng) {
        cy.log('✅ Angular is loaded');
      } else {
        cy.log('❌ Angular NOT loaded');
      }
    });
    
    // Find and test the Show Agent Chat button
    cy.get('body').then($body => {
      if ($body.find('button:contains("Show Agent Chat")').length > 0) {
        cy.log('✅ Show Agent Chat button found');
        
        // Get button details before clicking
        cy.get('button:contains("Show Agent Chat")').then($btn => {
          cy.log('Button text: ' + $btn.text());
          cy.log('Button classes: ' + $btn.attr('class'));
          cy.log('Button disabled: ' + $btn.prop('disabled'));
        });
        
        // Click the button
        cy.get('button:contains("Show Agent Chat")').click();
        cy.wait(1000);
        cy.screenshot('02-after-show-chat-click');
        
        // Check if anything appeared
        cy.get('body').then($bodyAfter => {
          const chatInterface = $bodyAfter.find('.agent-chat-interface');
          const agentTabs = $bodyAfter.find('.agent-tab');
          
          cy.log('Agent chat interface found: ' + (chatInterface.length > 0));
          cy.log('Agent tabs found: ' + agentTabs.length);
          
          if (chatInterface.length > 0) {
            cy.log('✅ Agent chat interface is visible!');
            cy.screenshot('03-chat-interface-working');
            
            // Test clicking an agent tab
            if (agentTabs.length > 0) {
              cy.get('.agent-tab').first().click();
              cy.wait(500);
              cy.screenshot('04-agent-tab-clicked');
              
              // Check for prompt textarea
              cy.get('body').then($bodyWithTab => {
                const textarea = $bodyWithTab.find('.prompt-textarea');
                if (textarea.length > 0) {
                  cy.log('✅ Prompt textarea found');
                  
                  // Try typing in it
                  cy.get('.prompt-textarea').type('Test message for analytics agent');
                  cy.wait(500);
                  cy.screenshot('05-text-typed');
                  
                  // Try clicking send button
                  cy.get('body').then($bodyWithText => {
                    const sendBtn = $bodyWithText.find('.send-prompt-btn');
                    if (sendBtn.length > 0) {
                      cy.log('✅ Send button found');
                      cy.get('.send-prompt-btn').click();
                      cy.wait(2000);
                      cy.screenshot('06-send-clicked');
                    } else {
                      cy.log('❌ Send button NOT found');
                    }
                  });
                } else {
                  cy.log('❌ Prompt textarea NOT found');
                }
              });
            }
          } else {
            cy.log('❌ Agent chat interface did NOT appear after clicking');
          }
        });
      } else {
        cy.log('❌ Show Agent Chat button NOT found');
      }
    });
    
    // Test other buttons
    cy.get('body').then($body => {
      // Test Start Agent Orchestration
      if ($body.find('button:contains("Start Agent Orchestration")').length > 0) {
        cy.log('🔄 Testing Start Agent Orchestration button');
        cy.get('button:contains("Start Agent Orchestration")').click();
        cy.wait(2000);
        cy.screenshot('07-start-agents-clicked');
      }
      
      // Test Generate Map Configuration  
      if ($body.find('button:contains("Generate Map Configuration")').length > 0) {
        cy.log('🔄 Testing Generate Map Configuration button');
        cy.get('button:contains("Generate Map Configuration")').click();
        cy.wait(2000);
        cy.screenshot('08-map-config-clicked');
      }
    });
    
    // Report JavaScript errors
    cy.then(() => {
      if (jsErrors.length > 0) {
        cy.log('❌ JavaScript Errors Found:');
        jsErrors.forEach((error, index) => {
          cy.log(`Error ${index + 1}: ${error.message}`);
        });
        
        // Create error overlay
        cy.window().then((win) => {
          const errorOverlay = win.document.createElement('div');
          errorOverlay.style.position = 'fixed';
          errorOverlay.style.top = '20px';
          errorOverlay.style.left = '20px';
          errorOverlay.style.width = '400px';
          errorOverlay.style.backgroundColor = 'rgba(244, 67, 54, 0.95)';
          errorOverlay.style.color = 'white';
          errorOverlay.style.padding = '20px';
          errorOverlay.style.borderRadius = '8px';
          errorOverlay.style.zIndex = '9999';
          errorOverlay.style.fontSize = '12px';
          
          errorOverlay.innerHTML = `
            <h3>❌ JavaScript Errors (${jsErrors.length})</h3>
            ${jsErrors.map(err => `<p>• ${err.message}</p>`).join('')}
          `;
          
          win.document.body.appendChild(errorOverlay);
        });
      } else {
        cy.log('✅ No JavaScript errors detected');
        
        // Create success overlay
        cy.window().then((win) => {
          const successOverlay = win.document.createElement('div');
          successOverlay.style.position = 'fixed';
          successOverlay.style.top = '20px';
          successOverlay.style.right = '20px';
          successOverlay.style.width = '300px';
          successOverlay.style.backgroundColor = 'rgba(76, 175, 80, 0.95)';
          successOverlay.style.color = 'white';
          successOverlay.style.padding = '15px';
          successOverlay.style.borderRadius = '8px';
          successOverlay.style.zIndex = '9999';
          
          successOverlay.innerHTML = `
            <h4>✅ Interaction Test Results</h4>
            <p>No JavaScript errors detected</p>
            <p>Testing button interactions...</p>
          `;
          
          win.document.body.appendChild(successOverlay);
        });
      }
    });
    
    cy.wait(3000);
    cy.screenshot('09-final-debug-result');
  });
}); 