describe('Test orcast.org vs orca-904de.web.app', () => {
  it('should compare what is actually running on orcast.org', () => {
    // Test orcast.org specifically
    cy.visit('https://orcast.org/agent-spatial-demo');
    cy.viewport(1400, 900);
    cy.wait(3000);
    
    cy.screenshot('orcast-org-loaded');
    
    // Check for the agent chat interface
    cy.get('body').then($body => {
      // Look for Show Agent Chat button
      const showChatBtn = $body.find('button:contains("Show Agent Chat")');
      const toggleChatBtn = $body.find('.toggle-chat-btn');
      
      if (showChatBtn.length > 0) {
        cy.log('✅ ORCAST.ORG: Show Agent Chat button found');
        cy.get('button:contains("Show Agent Chat")').click();
        cy.wait(1000);
        cy.screenshot('orcast-org-chat-clicked');
        
        // Check if agent interface appears
        if ($body.find('.agent-chat-interface').length > 0) {
          cy.log('✅ ORCAST.ORG: Agent chat interface works!');
          cy.screenshot('orcast-org-chat-working');
        } else {
          cy.log('❌ ORCAST.ORG: Agent chat interface does NOT appear');
          cy.screenshot('orcast-org-chat-failed');
        }
      } else if (toggleChatBtn.length > 0) {
        cy.log('✅ ORCAST.ORG: Toggle chat button found');
        cy.get('.toggle-chat-btn').click();
        cy.wait(1000);
        cy.screenshot('orcast-org-toggle-clicked');
      } else {
        cy.log('❌ ORCAST.ORG: NO agent chat button found at all');
        cy.screenshot('orcast-org-no-chat-button');
      }
      
      // Check what other elements exist
      const elements = [
        '.agent-spatial-demo',
        '.header',
        '.demo-controls', 
        '.agent-interaction-panel',
        '.spatial-forecasts',
        '.forecast-panel',
        'button:contains("Start Agent Orchestration")',
        'button:contains("Generate Map Configuration")'
      ];
      
      elements.forEach(selector => {
        const found = $body.find(selector).length;
        cy.log(`ORCAST.ORG: ${selector} - ${found > 0 ? '✅ FOUND' : '❌ NOT FOUND'} (${found} elements)`);
      });
    });
    
    // Add a visual indicator showing which site we're testing
    cy.window().then((win) => {
      const overlay = win.document.createElement('div');
      overlay.style.position = 'fixed';
      overlay.style.top = '20px';
      overlay.style.left = '20px';
      overlay.style.width = '300px';
      overlay.style.padding = '15px';
      overlay.style.backgroundColor = 'rgba(255, 152, 0, 0.95)';
      overlay.style.color = 'white';
      overlay.style.borderRadius = '8px';
      overlay.style.zIndex = '9999';
      overlay.style.fontSize = '14px';
      overlay.style.border = '2px solid #ff9800';
      
      const showChatExists = win.document.querySelector('button:contains("Show Agent Chat")') !== null;
      const agentInterfaceExists = win.document.querySelector('.agent-chat-interface') !== null;
      
      overlay.innerHTML = `
        <h4>🌐 Testing: orcast.org</h4>
        <p>Agent Chat Button: ${showChatExists ? '✅ Found' : '❌ Missing'}</p>
        <p>Agent Interface: ${agentInterfaceExists ? '✅ Present' : '❌ Missing'}</p>
        <p style="font-size: 12px; margin-top: 10px;">Compare to orca-904de.web.app</p>
      `;
      
      win.document.body.appendChild(overlay);
    });
    
    cy.wait(2000);
    cy.screenshot('orcast-org-final-status');
  });
  
  it('should test orca-904de.web.app for comparison', () => {
    // Test orca-904de.web.app to compare
    cy.visit('https://orca-904de.web.app/agent-spatial-demo');
    cy.viewport(1400, 900);
    cy.wait(3000);
    
    cy.screenshot('orca-904de-loaded');
    
    cy.get('body').then($body => {
      const showChatBtn = $body.find('button:contains("Show Agent Chat")');
      
      if (showChatBtn.length > 0) {
        cy.log('✅ ORCA-904DE: Show Agent Chat button found');
        cy.get('button:contains("Show Agent Chat")').click();
        cy.wait(1000);
        cy.screenshot('orca-904de-chat-clicked');
        
        if ($body.find('.agent-chat-interface').length > 0) {
          cy.log('✅ ORCA-904DE: Agent chat interface works!');
          cy.screenshot('orca-904de-chat-working');
        }
      } else {
        cy.log('❌ ORCA-904DE: NO agent chat button found');
      }
    });
    
    // Add comparison overlay
    cy.window().then((win) => {
      const overlay = win.document.createElement('div');
      overlay.style.position = 'fixed';
      overlay.style.top = '20px';
      overlay.style.right = '20px';
      overlay.style.width = '300px';
      overlay.style.padding = '15px';
      overlay.style.backgroundColor = 'rgba(76, 175, 80, 0.95)';
      overlay.style.color = 'white';
      overlay.style.borderRadius = '8px';
      overlay.style.zIndex = '9999';
      overlay.style.fontSize = '14px';
      overlay.style.border = '2px solid #4caf50';
      
      overlay.innerHTML = `
        <h4>🚀 Testing: orca-904de.web.app</h4>
        <p>This is the newly deployed version</p>
        <p>Agent Chat: Should work here</p>
      `;
      
      win.document.body.appendChild(overlay);
    });
    
    cy.wait(2000);
    cy.screenshot('orca-904de-final-status');
  });
}); 