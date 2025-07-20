describe('Agent Chat Button Test', () => {
  it('should test if the Show Agent Chat button actually works', () => {
    // Go to live site
    cy.visit('https://orca-904de.web.app/agent-spatial-demo');
    cy.viewport(1400, 900);
    cy.wait(3000);
    
    // Check for JavaScript errors
    cy.window().then((win) => {
      win.addEventListener('error', (e) => {
        cy.log('❌ JavaScript Error: ' + e.message);
      });
    });
    
    // Take initial screenshot
    cy.screenshot('01-initial-load');
    
    // Look for the Show Agent Chat button with different possible selectors
    const buttonSelectors = [
      'button:contains("Show Agent Chat")',
      '.toggle-chat-btn', 
      'button[class*="toggle"]',
      'button[class*="chat"]'
    ];
    
    let buttonFound = false;
    
    buttonSelectors.forEach((selector, index) => {
      cy.get('body').then($body => {
        if ($body.find(selector).length > 0) {
          cy.log('✅ Found button with selector: ' + selector);
          buttonFound = true;
          
          // Click the button
          cy.get(selector).first().click({force: true});
          cy.wait(1000);
          
          // Take screenshot after click
          cy.screenshot('02-after-button-click-' + index);
          
          // Check if agent chat interface appears
          const chatSelectors = [
            '.agent-chat-interface',
            '.agent-selector',
            '.agent-tab',
            '[class*="agent-chat"]'
          ];
          
          chatSelectors.forEach(chatSelector => {
            cy.get('body').then($body2 => {
              if ($body2.find(chatSelector).length > 0) {
                cy.log('✅ Agent chat interface appeared: ' + chatSelector);
                cy.screenshot('03-chat-interface-visible');
              } else {
                cy.log('❌ Agent chat interface NOT found: ' + chatSelector);
              }
            });
          });
        } else {
          cy.log('❌ Button NOT found with selector: ' + selector);
        }
      });
    });
    
    // If no button found, take a debug screenshot and log page content
    if (!buttonFound) {
      cy.get('body').then($body => {
        cy.log('❌ No Show Agent Chat button found anywhere!');
        cy.log('Page content preview:', $body.text().substring(0, 500));
        cy.screenshot('debug-no-button-found');
      });
    }
    
    // Check if specific agent elements exist
    const agentSelectors = [
      '.agent-tab',
      '.agent-name', 
      '.analytics',
      '.spatial',
      '[class*="agent"]'
    ];
    
    agentSelectors.forEach(selector => {
      cy.get('body').then($body => {
        const count = $body.find(selector).length;
        if (count > 0) {
          cy.log('✅ Found ' + count + ' elements with selector: ' + selector);
        } else {
          cy.log('❌ No elements found with selector: ' + selector);
        }
      });
    });
    
    // Add a visual indicator of the test result
    cy.window().then((win) => {
      const overlay = win.document.createElement('div');
      overlay.style.position = 'fixed';
      overlay.style.bottom = '20px';
      overlay.style.right = '20px';
      overlay.style.width = '300px';
      overlay.style.padding = '15px';
      overlay.style.backgroundColor = buttonFound ? 'rgba(76, 175, 80, 0.9)' : 'rgba(244, 67, 54, 0.9)';
      overlay.style.color = 'white';
      overlay.style.borderRadius = '8px';
      overlay.style.zIndex = '9999';
      overlay.style.fontSize = '14px';
      
      overlay.innerHTML = `
        <h4>${buttonFound ? '✅ Button Found' : '❌ Button Missing'}</h4>
        <p>Agent Chat Interface: ${buttonFound ? 'Testing...' : 'Cannot test - button missing'}</p>
        <p>Site: https://orca-904de.web.app</p>
      `;
      
      win.document.body.appendChild(overlay);
    });
    
    cy.wait(2000);
    cy.screenshot('04-final-test-result');
  });
}); 