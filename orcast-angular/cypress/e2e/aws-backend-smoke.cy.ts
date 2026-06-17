describe('AWS backend smoke', () => {
  const backendUrl = Cypress.env('backendUrl');

  it('health and core API endpoints respond', () => {
    cy.request('GET', `${backendUrl}/health`).then(response => {
      expect(response.status).to.eq(200);
      expect(response.body.status).to.be.oneOf(['healthy', 'degraded']);
      expect(response.body.sightings_loaded).to.be.greaterThan(0);
    });

    cy.request('GET', `${backendUrl}/api/sightings`).then(response => {
      expect(response.status).to.eq(200);
      expect(response.body.total_count).to.be.greaterThan(0);
    });

    cy.request('GET', `${backendUrl}/api/hotspots`).then(response => {
      expect(response.status).to.eq(200);
      expect(response.body.hotspots[0].probability).to.be.within(0, 1);
    });

    cy.request('POST', `${backendUrl}/forecast/quick`, {
      lat: 48.5158,
      lng: -123.1526
    }).then(response => {
      expect(response.status).to.eq(200);
      expect(response.body.prediction.probability).to.be.within(0, 1);
    });

    cy.request('POST', `${backendUrl}/api/reports/probability`, {
      min_confidence: 0
    }).then(response => {
      expect(response.status).to.eq(200);
      expect(response.body.report.report_id).to.match(/^report_/);
      expect(response.body.report.hotspots.length).to.be.greaterThan(0);
    });
  });
});
