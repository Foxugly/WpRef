import {HttpErrorResponse, HttpInterceptorFn} from '@angular/common/http';
import {inject} from '@angular/core';
import {catchError, throwError, timeout} from 'rxjs';
import {BackendStatusService} from './services/status/status';

// délai max avant de considérer "pas de réponse" (adapter selon besoin)
const REQ_TIMEOUT_MS = 8000;

export const NetworkInterceptor: HttpInterceptorFn = (req, next) => {
  const status = inject(BackendStatusService);

  return next(req).pipe(
    timeout(REQ_TIMEOUT_MS),
    catchError((err: unknown) => {
      // Timeout RxJS "simule" un status 0 pour nous
      if (err instanceof HttpErrorResponse) {
        if (err.status === 0) {
          // échec de connexion: serveur down, CORS, DNS, etc.
          status.setDown('API inaccessible. Vérifie que Django tourne sur http://127.0.0.1:8000');
        } else {
          // HTTP valide (ex: 400/401/500), le backend répond
          status.setUp();
        }
      } else {
        // Erreur non-HTTP (timeout opérateur, etc.)
        status.setDown('API : délai dépassé.');
      }
      return throwError(() => err);
    })
  );
};
