import {ApplicationConfig} from '@angular/core';
import {provideRouter} from '@angular/router';
import {provideHttpClient, withFetch, withInterceptors,} from '@angular/common/http';
import {routes} from './app.routes';
import {providePrimeNG} from 'primeng/config';
import Aura from '@primeng/themes/aura';
//import AuraLight from '@primeng/themes/aura-light';
import {AuthInterceptor} from './auth-interceptor';
import {NetworkInterceptor} from './network-interceptor';


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
    // 🔹 Configuration du thème PrimeNG
    providePrimeNG({
      theme: {
        preset: Aura, //AuraLight
      }
    }),
  ],
};
