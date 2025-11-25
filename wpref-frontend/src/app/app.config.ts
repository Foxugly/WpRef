import {
  ApplicationConfig,
  provideBrowserGlobalErrorListeners,
  provideZoneChangeDetection,
} from '@angular/core';
import { provideRouter } from '@angular/router';
import { routes } from './app.routes';

import { provideHttpClient, withFetch, withInterceptors } from '@angular/common/http';
import { AuthInterceptor } from './auth-interceptor';
import { NetworkInterceptor } from './network-interceptor';

export const appConfig: ApplicationConfig = {
  providers: [
    provideBrowserGlobalErrorListeners(),
    provideZoneChangeDetection({ eventCoalescing: true }),

    // Routing standalone
    provideRouter(routes),

    // HttpClient + Fetch + JWT + Network interceptor
    provideHttpClient(
      withFetch(),
      withInterceptors([
        AuthInterceptor,
        NetworkInterceptor
      ])
    ),
  ],
};
