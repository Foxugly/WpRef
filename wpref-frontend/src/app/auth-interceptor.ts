// auth-interceptor.ts
import { HttpInterceptorFn, HttpErrorResponse } from '@angular/common/http';
import { inject } from '@angular/core';
import { AuthService } from './services/auth/auth';
import { catchError, switchMap, throwError } from 'rxjs';

export const AuthInterceptor: HttpInterceptorFn = (req, next) => {
  const auth = inject(AuthService);

  const accessToken = auth.getAccessToken();
  let authReq = req;

  if (accessToken) {
    authReq = req.clone({
      setHeaders: {
        Authorization: `Bearer ${accessToken}`,
      },
    });
  }

  return next(authReq).pipe(
    catchError((error: HttpErrorResponse) => {
      // Pas de 401 → on remonte l'erreur telle quelle
      if (error.status !== 401) {
        return throwError(() => error);
      }

      // 401 → on tente un refresh
      const refresh$ = auth.refreshTokens();
      if (!refresh$) {
        // pas de refresh token → on se déconnecte
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
          // échec du refresh → logout + propagation de l'erreur
          auth.logout();
          return throwError(() => refreshError);
        }),
      );
    }),
  );
};
