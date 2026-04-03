import {HttpErrorResponse, HttpInterceptorFn} from '@angular/common/http';
import {inject} from '@angular/core';
import {catchError, throwError, timeout} from 'rxjs';
import {environment} from '../environments/environment';
import {BackendStatusService} from './services/status/status';

// Delai max avant de considerer "pas de reponse" (adapter selon besoin)
const REQ_TIMEOUT_MS = 8000;

export const NetworkInterceptor: HttpInterceptorFn = (req, next) => {
  const status = inject(BackendStatusService);

  return next(req).pipe(
    timeout(REQ_TIMEOUT_MS),
    catchError((err: unknown) => {
      // Timeout RxJS "simule" un status 0 pour nous
      if (err instanceof HttpErrorResponse) {
        if (err.status === 0) {
          // Echec de connexion: serveur down, CORS, DNS, etc.
          status.setDown(`API inaccessible. Verifie que l'API tourne sur ${environment.apiBaseUrl}`);
        } else {
          // HTTP valide (ex: 400/401/500), le backend repond
          status.setUp();
        }
      } else {
        // Erreur non-HTTP (timeout operateur, etc.)
        status.setDown('API : delai depasse.');
      }
      return throwError(() => err);
    })
  );
};
