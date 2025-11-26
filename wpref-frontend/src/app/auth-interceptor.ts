// src/app/auth-interceptor.ts
import {
  HttpInterceptorFn,
  HttpErrorResponse,
  HttpRequest,
} from '@angular/common/http';
import { inject } from '@angular/core';
import { AuthService } from './services/auth/auth';
import { catchError, switchMap, throwError } from 'rxjs';

const API_PREFIX = '/api/';

function isApiRequest(req: HttpRequest<unknown>): boolean {
  // Assez simple : on regarde si l'URL contient "/api/"
  return req.url.includes(API_PREFIX);
}

function isAuthEndpoint(req: HttpRequest<unknown>): boolean {
  const url = req.url;
  return (
    url.includes('/api/token/') ||              // login
    url.includes('/api/token/refresh/') ||      // refresh
    url.includes('/api/user/password/reset')    // reset password
  );
}

export const AuthInterceptor: HttpInterceptorFn = (req, next) => {
  const auth = inject(AuthService);

  let authReq = req;

  // 1) Ajouter le Bearer UNIQUEMENT pour les vraies requêtes API,
  //    et pas pour les endpoints d'auth / reset
  if (isApiRequest(req) && !isAuthEndpoint(req)) {
    const accessToken = auth.getAccessToken();
    if (accessToken) {
      authReq = req.clone({
        setHeaders: {
          Authorization: `Bearer ${accessToken}`,
        },
      });
    }
  }

  return next(authReq).pipe(
    catchError((error: HttpErrorResponse) => {
      // Si ce n'est pas un 401 → on remonte l'erreur telle quelle
      if (error.status !== 401) {
        return throwError(() => error);
      }

      // On ne tente PAS de refresh si :
      //  - ce n'est pas une requête API
      //  - OU c'est déjà un endpoint d'auth
      if (!isApiRequest(authReq) || isAuthEndpoint(authReq)) {
        return throwError(() => error);
      }

      // 2) Tenter un refresh
      const refresh$ = auth.refreshTokens();
      if (!refresh$) {
        auth.logout();
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
          auth.logout();
          return throwError(() => refreshError);
        }),
      );
    }),
  );
};
