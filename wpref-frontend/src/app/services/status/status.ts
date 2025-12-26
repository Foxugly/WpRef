import {Injectable, signal} from '@angular/core';

@Injectable({providedIn: 'root'})
export class BackendStatusService {
  backendUp = signal<boolean | null>(null);  // null = inconnu, true = OK, false = KO
  lastError = signal<string | null>(null);

  setUp() {
    this.backendUp.set(true);
    this.lastError.set(null);
  }

  setDown(msg = 'API inaccessible (serveur arrêté, CORS ou réseau).') {
    this.backendUp.set(false);
    this.lastError.set(msg);
  }
}
