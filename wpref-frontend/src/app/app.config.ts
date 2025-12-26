import {ApplicationConfig} from '@angular/core';
import {provideRouter} from '@angular/router';
import {provideHttpClient, withFetch, withInterceptors,} from '@angular/common/http';
import {routes} from './app.routes';
import {providePrimeNG} from 'primeng/config';
import Aura from '@primeng/themes/aura';
import {AuthInterceptor} from './auth-interceptor';
import {NetworkInterceptor} from './network-interceptor';
//import { provideAnimationsAsync } from '@angular/platform-browser/animations/async';
import {provideNoopAnimations} from '@angular/platform-browser/animations';
import {Configuration} from './api/generated/configuration';
import {environment} from '../environments/environment';

export const appConfig: ApplicationConfig = {
  providers: [
    provideRouter(routes),
    provideHttpClient(
      withFetch(),
      withInterceptors([AuthInterceptor, NetworkInterceptor,]),
    ),
    {
      provide: Configuration,
      useFactory: () =>
        new Configuration({basePath: environment.apiBaseUrl}),
    },
    provideNoopAnimations(),
    // 🔹 Configuration du thème PrimeNG
    providePrimeNG({
      theme: {
        preset: Aura, //AuraLight
      }
    }),
  ],
};
