import { defineConfig } from 'cypress'

export default defineConfig({
  e2e: {
    baseUrl: 'https://orca-904de.web.app',
    viewportWidth: 1280,
    viewportHeight: 720,
    video: true,
    screenshotOnRunFailure: true,
    defaultCommandTimeout: 15000,
    requestTimeout: 15000,
    responseTimeout: 15000,
    setupNodeEvents(on, config) {
      // implement node event listeners here
      on('task', {
        log(message) {
          console.log(message);
          return null;
        }
      });
    },
    env: {
      backendUrl: 'https://orcast-production-backend-2cvqukvhga-uw.a.run.app',
      gemmaUrl: 'https://cloud-run-gemma-2cvqukvhga-uw.a.run.app'
    },
    specPattern: 'cypress/e2e/**/*.cy.{js,jsx,ts,tsx}',
    supportFile: 'cypress/support/e2e.ts'
  },
  component: {
    devServer: {
      framework: 'angular',
      bundler: 'webpack',
    },
    specPattern: '**/*.cy.ts',
    supportFile: 'cypress/support/component.ts'
  }
}) 