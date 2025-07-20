import { Routes } from '@angular/router';

export const routes: Routes = [
  {
    path: '',
    loadComponent: () => import('./components/agent-spatial-demo/agent-spatial-demo.component').then(c => c.AgentSpatialDemoComponent)
  },
  {
    path: 'agent-spatial-demo',
    loadComponent: () => import('./components/agent-spatial-demo/agent-spatial-demo.component').then(c => c.AgentSpatialDemoComponent)
  },
  {
    path: 'live-demo',
    loadComponent: () => import('./components/live-ai-demo/live-ai-demo.component').then(c => c.LiveAIDemoComponent)
  },
  {
    path: 'main-map',
    loadComponent: () => import('./components/main-map/main-map.component').then(c => c.MainMapComponent)
  },
  {
    path: 'dashboard',
    loadComponent: () => import('./components/map-dashboard/map-dashboard.component').then(c => c.MapDashboardComponent)
  },
  {
    path: 'agent-demo',
    loadComponent: () => import('./components/agent-demo/agent-demo.component').then(c => c.AgentDemoComponent)
  },
  {
    path: 'automated-demo',
    loadComponent: () => import('./components/automated-demo/automated-demo.component').then(c => c.AutomatedDemoComponent)
  },
  {
    path: '**',
    redirectTo: '/'
  }
];
