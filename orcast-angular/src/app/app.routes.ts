import { Routes } from '@angular/router';

export const routes: Routes = [
  {
    path: '',
    loadComponent: () => import('./components/landing/landing.component').then(c => c.LandingComponent)
  },
  {
    path: 'partners',
    loadComponent: () => import('./components/partners/partners.component').then(c => c.PartnersComponent)
  },
  {
    path: 'live-demo',
    loadComponent: () => import('./components/live-ai-demo/live-ai-demo.component').then(c => c.LiveAIDemoComponent)
  },
  {
    path: 'historical',
    loadComponent: () => import('./components/historical-sightings/historical-sightings.component').then(c => c.HistoricalSightingsComponent)
  },
  {
    path: 'realtime',
    loadComponent: () => import('./components/realtime-detection/realtime-detection.component').then(c => c.RealtimeDetectionComponent)
  },
  {
    path: 'ml-predictions',
    loadComponent: () => import('./components/ml-predictions/ml-predictions.component').then(c => c.MLPredictionsComponent)
  },
  {
    path: 'score-grid',
    redirectTo: 'ml-predictions',
    pathMatch: 'full'
  },
  {
    path: 'reports',
    loadComponent: () => import('./components/probability-report/probability-report.component').then(c => c.ProbabilityReportComponent)
  },
  {
    path: 'plan',
    loadComponent: () => import('./components/trip-planner/trip-planner.component').then(c => c.TripPlannerComponent)
  },
  {
    path: 'contribute',
    loadComponent: () => import('./components/contribute/contribute.component').then(c => c.ContributeComponent)
  },
  // Archived demo/agent routes — quarantined from the public UI.
  // These components carried legacy ORCAST/multi-agent copy and are no longer
  // linked from nav, landing, or footer. Redirect direct hits to live pages.
  { path: 'agent-spatial-demo', redirectTo: 'reports', pathMatch: 'full' },
  { path: 'agent-demo', redirectTo: 'reports', pathMatch: 'full' },
  { path: 'main-map', redirectTo: 'historical', pathMatch: 'full' },
  { path: 'dashboard', redirectTo: 'reports', pathMatch: 'full' },
  { path: 'automated-demo', redirectTo: '', pathMatch: 'full' },
  {
    path: '**',
    redirectTo: '/'
  }
];
