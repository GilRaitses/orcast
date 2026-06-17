import { defineConfig } from 'cypress'

const backendUrl = process.env.CYPRESS_BACKEND_URL || 'http://localhost:8080'

export default defineConfig({
  e2e: {
    baseUrl: process.env.CYPRESS_BASE_URL || 'http://localhost:4200',
    viewportWidth: 1280,
    viewportHeight: 720,
    video: true,
    screenshotOnRunFailure: true,
    defaultCommandTimeout: 15000,
    requestTimeout: 15000,
    responseTimeout: 15000,
    setupNodeEvents(on, config) {
      on('task', {
        log(message) {
          console.log(message);
          return null;
        },
        copyScreenshot({ from, to }: { from: string; to: string }) {
          const fs = require('fs');
          const path = require('path');

          const sourcePath = path.resolve(from);
          const destPath = path.resolve(to);

          try {
            const destDir = path.dirname(destPath);
            if (!fs.existsSync(destDir)) {
              fs.mkdirSync(destDir, { recursive: true });
            }
            fs.copyFileSync(sourcePath, destPath);
            console.log(`Screenshot copied: ${from} -> ${to}`);
            return null;
          } catch (error) {
            console.error('Failed to copy screenshot:', error);
            return null;
          }
        }
      });
    },
    env: {
      backendUrl,
      gemmaUrl: 'https://cloud-run-gemma-2cvqukvhga-uw.a.run.app'
    },
    specPattern: 'cypress/e2e/**/*.cy.{js,jsx,ts,tsx}',
    excludeSpecPattern: 'cypress/e2e/legacy/**',
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
