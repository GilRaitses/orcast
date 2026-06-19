describe('Probability report UI', () => {
  beforeEach(() => {
    cy.visit('/reports');
  });

  it('generates a report with a map and hotspot list', () => {
    cy.get('[data-cy="generate-report"]').should('be.visible').click();

    // Map split view is the hero of the page.
    cy.get('google-map').should('be.visible');

    // CSV export becomes available once a report loads.
    cy.get('[data-cy="download-csv"]', { timeout: 20000 }).should('be.visible');

    // Hotspot list renders with human-readable chance copy.
    cy.get('.hotspot-card').its('length').should('be.gte', 1);
    cy.get('.hotspot-card').first().should('contain.text', 'Chance of sightings');

    // Internal substrate (model_version, report ids) stays out of the default view.
    cy.contains('model_version').should('not.be.visible');
  });
});
