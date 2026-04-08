import {ApplicationConfig} from '@angular/core';
import {provideRouter} from '@angular/router';
import {provideHttpClient, withFetch, withInterceptors,} from '@angular/common/http';
import {routes} from './app.routes';
import {providePrimeNG} from 'primeng/config';
import {MessageService} from 'primeng/api';
import Aura from '@primeng/themes/aura';
import {AuthInterceptor} from './auth-interceptor';
import {NetworkInterceptor} from './network-interceptor';
//import { provideAnimationsAsync } from '@angular/platform-browser/animations/async';
import {provideNoopAnimations} from '@angular/platform-browser/animations';
import {Configuration} from './api/generated/configuration';
import {resolveApiBaseUrl} from './shared/api/runtime-api-base-url';

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
        new Configuration({basePath: resolveApiBaseUrl()}),
    },
    provideNoopAnimations(),
    // 🔹 Configuration du thème PrimeNG
    providePrimeNG({
      theme: {
        preset: Aura, //AuraLight
      }
    }),
    MessageService,
  ],
};
