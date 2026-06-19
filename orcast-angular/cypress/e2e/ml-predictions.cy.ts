describe('Score grid page', () => {
  beforeEach(() => {
    cy.visit('/ml-predictions');
    cy.get('.grid-controls').should('be.visible');
    cy.get('google-map').should('be.visible');
  });

  it('shows probability map controls without fake model selector', () => {
    cy.get('.grid-controls h3').should('contain', 'Probability map');
    cy.get('.model-selector').should('not.exist');
    cy.get('.forecast-timeline').should('not.exist');
    cy.get('.model-info').should('not.exist');
    cy.contains('PINN').should('not.exist');
  });

  it('shows parameter sliders and generate button', () => {
    cy.contains('Hours').should('be.visible');
    cy.contains('Radius').should('be.visible');
    cy.contains('Min probability').should('be.visible');
    cy.get('.param-slider').should('have.length', 3);
    cy.get('.generate-btn').should('contain', 'Load probability map');
  });

  it('loads results from the API', () => {
    cy.get('.generate-btn').click();
    cy.get('.results-panel', { timeout: 15000 }).should('be.visible');
    cy.get('.results-panel').within(() => {
      cy.contains('Grid points').should('be.visible');
      cy.contains('Max probability').should('be.visible');
      cy.contains('Model').should('not.exist');
    });
  });

  it('redirects /score-grid to the same page', () => {
    cy.visit('/score-grid');
    cy.url().should('include', '/ml-predictions');
    cy.get('.grid-controls h3').should('contain', 'Probability map');
  });

  it('highlights Score grid in nav', () => {
    cy.get('orcast-nav-header .nav-btn').contains('Score grid').should('have.class', 'active');
  });
});
