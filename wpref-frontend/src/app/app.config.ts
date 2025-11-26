// src/app/app.config.ts
import { ApplicationConfig } from '@angular/core';
import { provideRouter } from '@angular/router';
import {
  provideHttpClient,
  withFetch,
  withInterceptors,
} from '@angular/common/http';

import { routes } from './app.routes';
import { AuthInterceptor } from './auth-interceptor';
// Si tu as un NetworkInterceptor, garde l'import, sinon commente-le
import { NetworkInterceptor } from './network-interceptor';

export const appConfig: ApplicationConfig = {
  providers: [
    provideRouter(routes),
    provideHttpClient(
      withFetch(),
      withInterceptors([
        AuthInterceptor,
        NetworkInterceptor, // ou enlève-le si tu n'as pas ce fichier
      ]),
    ),
  ],
};
