import { bootstrapApplication } from '@angular/platform-browser';
import { provideRouter } from '@angular/router';
import { provideHttpClient, withFetch, withInterceptors } from '@angular/common/http';
import { routes } from './app/app.routes';
import { App } from './app/app';
import { AuthInterceptor } from '../src/app/auth-interceptor';
import { NetworkInterceptor } from './app/network-interceptor';

bootstrapApplication(App, {
  providers: [
    provideRouter(routes),
    // HttpClient + fetch + interceptor JWT (standalone)
    provideHttpClient(withFetch(), withInterceptors([AuthInterceptor, NetworkInterceptor])),
  ],
});
