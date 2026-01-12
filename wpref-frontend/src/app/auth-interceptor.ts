// src/app/auth-interceptor.ts
import {HttpErrorResponse, HttpInterceptorFn} from '@angular/common/http';
import {inject} from '@angular/core';
import {catchError, switchMap, throwError} from 'rxjs';

import {AuthService} from './services/auth/auth';
import {environment} from '../environments/environment';

// Petit helper pour savoir si l’URL vise notre backend API
function isApiUrl(url: string): boolean {

  const base = environment.apiBaseUrl.replace(/\/+$/, ''); // enlever les / de fin
  const cleaned = url.replace(/\/+$/, '');

  // 1) URL absolue vers notre backend
  if (cleaned.startsWith(base)) {
    return true;
  }

  // 2) URL relative /api/...
  if (cleaned.startsWith('/api/')) {
    return true;
  }

  return false;
}

// Pour éviter de boucler sur /api/token et /api/token/refresh
function isAuthEndpoint(url: string): boolean {
  return (
    url.includes('/api/token') ||
    url.includes('/api/user/password/reset') // éventuellement d’autres endpoints d’auth
  );
}

export const AuthInterceptor: HttpInterceptorFn = (req, next) => {
  const auth = inject(AuthService);

  const accessToken = auth.getAccessToken();
  let authReq = req;

  const apiRequest = isApiUrl(req.url);

  // On n’ajoute Authorization QUE pour les appels API
  if (accessToken && apiRequest) {
    authReq = req.clone({
      setHeaders: {
        Authorization: `Bearer ${accessToken}`,
      },
    });
  }

  return next(authReq).pipe(
    catchError((error: HttpErrorResponse) => {
      // Si ce n’est pas un 401 ou pas une requête API → on laisse passer
      if (error.status !== 401 || !apiRequest) {
        return throwError(() => error);
      }

      // Si le 401 vient déjà d’un endpoint d’auth (login/refresh/etc.) → pas de refresh
      if (isAuthEndpoint(authReq.url)) {
        return throwError(() => error);
      }

      // 401 sur l’API → on tente un refresh
      const refresh$ = auth.refreshTokens();
      if (!refresh$) {
        auth.logout(); // on nettoie les tokens
        return throwError(() => error);
      }

      return refresh$.pipe(
        switchMap(() => {
          const newAccessToken = auth.getAccessToken();

          const retryReq = newAccessToken
            ? authReq.clone({
              setHeaders: {
                Authorization: `Bearer ${newAccessToken}`,
              },
            })
            : authReq;

          return next(retryReq);
        }),
        catchError((refreshError: HttpErrorResponse) => {
          // échec du refresh → logout + propagation de l’erreur
          auth.logout();
          return throwError(() => refreshError);
        }),
      );
    }),
  );
};
