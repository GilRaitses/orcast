import { Routes } from '@angular/router';

export const routes: Routes = [
  {
    path: '',
    redirectTo: '/dashboard',
    pathMatch: 'full'
  },
  {
    path: 'dashboard',
    loadComponent: () => import('./components/map-dashboard/map-dashboard.component').then(c => c.MapDashboardComponent)
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
    path: '**',
    redirectTo: '/dashboard'
  }
];
