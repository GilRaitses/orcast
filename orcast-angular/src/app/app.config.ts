import { ApplicationConfig, provideZoneChangeDetection } from '@angular/core';
import { provideRouter } from '@angular/router';
import { provideHttpClient } from '@angular/common/http';
import { provideGoogleMaps } from '@angular/google-maps';

import { routes } from './app.routes';

export const appConfig: ApplicationConfig = {
  providers: [
    provideZoneChangeDetection({ eventCoalescing: true }), 
    provideRouter(routes),
    provideHttpClient(),
    provideGoogleMaps('AIzaSyD9aM6oj1wpVG-VungMtIpyNWeHp3Q7XjU')
  ]
};
