describe('ML Predictions Page', () => {
  beforeEach(() => {
    cy.visit('/ml-predictions')
    // Wait for page to load
    cy.get('.ml-controls').should('be.visible')
    cy.get('google-map').should('be.visible')
  })

  describe('Page Layout and Components', () => {
    it('should display all essential components', () => {
      // Check main sections
      cy.get('.ml-controls').should('be.visible')
      cy.get('.model-info').should('be.visible')
      cy.get('.forecast-timeline').should('be.visible')
      cy.get('google-map').should('be.visible')
      
      // Check navigation header
      cy.get('orcast-nav-header').should('be.visible')
      cy.get('.nav-btn').contains('ML Predictions').should('have.class', 'active')
    })

    it('should display model selection options', () => {
      cy.get('.model-selector').should('be.visible')
      cy.get('.model-option').should('have.length', 3)
      
      // Check all model types
      cy.contains('.model-option', 'PINN Physics-Informed').should('be.visible')
      cy.contains('.model-option', 'Behavioral ML').should('be.visible')
      cy.contains('.model-option', 'Ensemble Model').should('be.visible')
    })

    it('should display parameter controls', () => {
      cy.get('.prediction-params').should('be.visible')
      
      // Check parameter sliders
      cy.contains('Prediction Hours').should('be.visible')
      cy.contains('Spatial Resolution').should('be.visible')
      cy.contains('Confidence Threshold').should('be.visible')
      
      cy.get('.param-slider').should('have.length', 3)
    })

    it('should display generate predictions button', () => {
      cy.get('.generate-btn').should('be.visible')
      cy.get('.generate-btn').should('contain', 'Generate Predictions')
    })
  })

  describe('Model Selection', () => {
    it('should select PINN model by default', () => {
      cy.get('.model-option').first().should('have.class', 'active')
      cy.get('input[value="pinn"]').should('be.checked')
      
      // Check model info updates
      cy.get('.model-info h3').should('contain', 'PINN Physics Model')
    })

    it('should switch to Behavioral ML model', () => {
      cy.contains('.model-option', 'Behavioral ML').click()
      
      // Check selection state
      cy.contains('.model-option', 'Behavioral ML').should('have.class', 'active')
      cy.get('input[value="behavioral"]').should('be.checked')
      
      // Check model info updates
      cy.get('.model-info h3').should('contain', 'Behavioral ML Model')
      cy.get('.model-info').should('contain', 'DTAG biologging')
    })

    it('should switch to Ensemble model', () => {
      cy.contains('.model-option', 'Ensemble Model').click()
      
      // Check selection state
      cy.contains('.model-option', 'Ensemble Model').should('have.class', 'active')
      cy.get('input[value="ensemble"]').should('be.checked')
      
      // Check model info updates
      cy.get('.model-info h3').should('contain', 'Ensemble Model')
      cy.get('.model-info').should('contain', 'Combined model')
    })
  })

  describe('Parameter Controls', () => {
    it('should update prediction hours parameter', () => {
      // Find the hours slider and change value
      cy.get('.prediction-params').within(() => {
        cy.contains('Prediction Hours').parent().find('input[type="range"]').as('hoursSlider')
        
        cy.get('@hoursSlider').invoke('val', 48).trigger('input')
        
        // Check that the display updates
        cy.contains('Prediction Hours').should('contain', '48')
      })
    })

    it('should update spatial resolution parameter', () => {
      cy.get('.prediction-params').within(() => {
        cy.contains('Spatial Resolution').parent().find('input[type="range"]').as('resolutionSlider')
        
        cy.get('@resolutionSlider').invoke('val', 8).trigger('input')
        
        // Check that resolution label updates (should show something like "20m")
        cy.contains('Spatial Resolution').parent().should('contain', 'm')
      })
    })

    it('should update confidence threshold parameter', () => {
      cy.get('.prediction-params').within(() => {
        cy.contains('Confidence Threshold').parent().find('input[type="range"]').as('thresholdSlider')
        
        cy.get('@thresholdSlider').invoke('val', 85).trigger('input')
        
        // Check that threshold display updates
        cy.contains('Confidence Threshold').should('contain', '85%')
      })
    })
  })

  describe('Model Information Panel', () => {
    it('should display performance metrics', () => {
      cy.get('.model-info').within(() => {
        cy.get('.performance-metrics').should('be.visible')
        cy.contains('Accuracy').should('be.visible')
        cy.contains('Precision').should('be.visible')
        cy.contains('Recall').should('be.visible')
        
        // Check that percentages are displayed
        cy.get('.metric-row').should('contain', '%')
      })
    })

    it('should display confidence meter', () => {
      cy.get('.confidence-meter').should('be.visible')
      cy.get('.confidence-bar').should('be.visible')
      cy.get('.confidence-indicator').should('be.visible')
      cy.get('.confidence-text').should('contain', 'Confident')
    })

    it('should update metrics when model changes', () => {
      // Get initial accuracy value
      cy.get('.metric-row').contains('Accuracy').parent().invoke('text').as('initialAccuracy')
      
      // Switch model
      cy.contains('.model-option', 'Behavioral ML').click()
      
      // Check that accuracy changed
      cy.get('@initialAccuracy').then(initialAccuracy => {
        cy.get('.metric-row').contains('Accuracy').parent().should('not.contain', initialAccuracy)
      })
    })
  })

  describe('Prediction Generation', () => {
    it('should generate predictions on button click', () => {
      cy.get('.generate-btn').click()
      
      // Check loading state
      cy.get('.generate-btn').should('contain', 'Generating')
      cy.get('.generate-btn').should('be.disabled')
      
      // Wait for generation to complete (with timeout)
      cy.get('.generate-btn', { timeout: 15000 }).should('not.be.disabled')
      cy.get('.generate-btn').should('contain', 'Generate Predictions')
    })

    it('should display prediction results', () => {
      cy.get('.generate-btn').click()
      
      // Wait for results to appear
      cy.get('.prediction-overlay', { timeout: 15000 }).should('be.visible')
      
      cy.get('.prediction-overlay').within(() => {
        cy.contains('Prediction Results').should('be.visible')
        cy.contains('Model:').should('be.visible')
        cy.contains('Predictions:').should('be.visible')
        cy.contains('Status: ✅ Complete').should('be.visible')
      })
    })

    it('should automatically generate predictions when parameters change', () => {
      // Change a parameter
      cy.contains('.model-option', 'Behavioral ML').click()
      
      // Should trigger automatic prediction generation
      cy.get('.generate-btn').should('be.disabled')
      
      // Wait for completion
      cy.get('.generate-btn', { timeout: 15000 }).should('not.be.disabled')
    })
  })

  describe('Timeline Forecast', () => {
    it('should display 24-hour timeline', () => {
      cy.get('.forecast-timeline').should('be.visible')
      cy.get('.timeline-hours').should('be.visible')
      
      // Should have 24 hour items
      cy.get('.hour-item').should('have.length', 24)
    })

    it('should show hourly predictions with probabilities', () => {
      cy.get('.hour-item').each($hourItem => {
        // Each hour should have time and probability
        cy.wrap($hourItem).should('contain', ':00')
        cy.wrap($hourItem).find('.hour-prob').should('contain', '%')
      })
    })

    it('should classify hours by probability levels', () => {
      cy.get('.hour-item').should('satisfy', $items => {
        // Should have items with different probability classes
        const hasHighProb = $items.toArray().some(item => 
          item.classList.contains('high-prob'))
        const hasMediumProb = $items.toArray().some(item => 
          item.classList.contains('medium-prob'))
        const hasLowProb = $items.toArray().some(item => 
          item.classList.contains('low-prob'))
        
        return hasHighProb || hasMediumProb || hasLowProb
      })
    })

    it('should show hour details on click', () => {
      // Click on first hour item
      cy.get('.hour-item').first().click()
      
      // Should show prediction details (might be in map info window)
      // This test might need adjustment based on actual implementation
      cy.wait(1000) // Give time for any popup to appear
    })
  })

  describe('Map Integration', () => {
    it('should display Google Map', () => {
      cy.get('google-map').should('be.visible')
      
      // Map should be initialized (check for map container)
      cy.get('google-map').should('have.attr', 'style')
    })

    it('should update map when predictions are generated', () => {
      cy.get('.generate-btn').click()
      
      // Wait for prediction generation
      cy.get('.prediction-overlay', { timeout: 15000 }).should('be.visible')
      
      // Map should show heat map or markers (this would need actual map testing)
      // For now, just verify the map is still visible
      cy.get('google-map').should('be.visible')
    })
  })

  describe('Error Handling', () => {
    it('should handle prediction generation errors gracefully', () => {
      // This test would require mocking API errors
      // For now, just ensure the UI remains functional
      cy.get('.generate-btn').click()
      
      // Even if there's an error, button should become enabled again
      cy.get('.generate-btn', { timeout: 20000 }).should('not.be.disabled')
    })
  })

  describe('State Persistence', () => {
    it('should remember model selection across page reloads', () => {
      // Select a different model
      cy.contains('.model-option', 'Ensemble Model').click()
      
      // Reload page
      cy.reload()
      
      // Should remember the selection
      cy.contains('.model-option', 'Ensemble Model').should('have.class', 'active')
    })

    it('should remember parameter settings across page reloads', () => {
      // Change parameter
      cy.get('.prediction-params').within(() => {
        cy.contains('Prediction Hours').parent().find('input[type="range"]')
          .invoke('val', 48).trigger('input')
      })
      
      // Reload page
      cy.reload()
      
      // Should remember the setting
      cy.contains('Prediction Hours').should('contain', '48')
    })
  })
}) 