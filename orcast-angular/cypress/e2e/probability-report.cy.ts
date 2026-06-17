describe('Probability report UI', () => {
  beforeEach(() => {
    cy.visit('/reports');
  });

  it('generates a report and exposes CSV download', () => {
    cy.get('[data-cy="generate-report"]').should('be.visible').click();
    cy.get('[data-cy="download-csv"]', { timeout: 20000 }).should('be.visible');
    cy.get('h2').invoke('text').should('match', /^report_/);
  });
});
