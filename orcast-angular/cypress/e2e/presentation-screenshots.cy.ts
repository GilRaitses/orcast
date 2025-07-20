describe('ORCAST Presentation Screenshots', () => {
  beforeEach(() => {
    // Set a larger viewport for presentation screenshots
    cy.viewport(1400, 900);
  });

  it('should capture screenshots of all presentation slides', () => {
    // First, let's try to access the presentation from the local file system
    // We'll need to serve the HTML file locally or copy it to the web app
    
    // For now, let's create a simple approach by visiting the local file
    // Note: This might need adjustment based on how the presentation is served
    
    cy.visit('http://localhost:8080/ORCAST_Project_Overview.html', { failOnStatusCode: false })
      .then(() => {
        // Wait for presentation to load
        cy.wait(3000);
        
        // Check if reveal.js is available
        cy.window().should('have.property', 'Reveal');
        
        // Get total number of slides
        cy.window().then((win) => {
          const reveal = (win as any).Reveal;
          const totalSlides = reveal.getTotalSlides();
          
          // Screenshot each slide
          for (let i = 0; i < totalSlides; i++) {
            cy.window().then((win) => {
              const reveal = (win as any).Reveal;
              reveal.slide(i);
            });
            
            // Wait for slide transition
            cy.wait(1000);
            
            // Take screenshot with meaningful name
            cy.screenshot(`slide-${String(i + 1).padStart(2, '0')}-${getSlideTitle(i)}`);
          }
        });
      });
  });

  // Helper function to generate slide titles for filenames
  function getSlideTitle(slideIndex: number): string {
    const slideTitles = [
      'title-slide',
      'orcast-advanced-ai-platform',
      'gemma-agent-architecture', 
      'user-journey-interactive-demo',
      'advanced-ai-services-sindy',
      'hmc-sampling-uncertainty',
      'fourier-neural-operators',
      'real-time-map-overlay',
      'gpu-infrastructure-pinns',
      'live-demo-videos',
      'live-platform-questions'
    ];
    
    return slideTitles[slideIndex] || `slide-${slideIndex + 1}`;
  }

  it('should capture screenshots with different viewport sizes', () => {
    const viewports = [
      { width: 1400, height: 900, name: 'desktop' },
      { width: 1024, height: 768, name: 'tablet' },
      { width: 375, height: 667, name: 'mobile' }
    ];

    viewports.forEach((viewport) => {
      cy.viewport(viewport.width, viewport.height);
      
      cy.visit('http://localhost:8080/ORCAST_Project_Overview.html', { failOnStatusCode: false })
        .then(() => {
          cy.wait(3000);
          
          cy.window().then((win) => {
            const reveal = (win as any).Reveal;
            const totalSlides = reveal.getTotalSlides();
            
            // Take a few key slides for each viewport
            const keySlides = [0, 1, 2, 8]; // Title, Overview, Architecture, Conclusion
            
            keySlides.forEach((slideIndex) => {
              if (slideIndex < totalSlides) {
                reveal.slide(slideIndex);
                cy.wait(1000);
                cy.screenshot(`${viewport.name}-slide-${slideIndex + 1}`);
              }
            });
          });
        });
    });
  });
}); 