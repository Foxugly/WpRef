import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { environment } from '../../environments/environment';
import { tap } from 'rxjs/operators';

interface TokenPair { access: string; refresh: string; }

@Injectable({ providedIn: 'root' })
export class AuthService {
  private http = inject(HttpClient);
  private base = environment.apiBaseUrl;
  private accessKey = 'jwt_access';
  private refreshKey = 'jwt_refresh';
  private userKey = 'username';

  login(username: string, password: string, remember = false) {
    // NB: SimpleJWT = POST /api/token/
    return this.http.post<TokenPair>(`${this.base.replace('/api','')}/api/token/`, { username, password })
      .pipe(tap(({ access, refresh }) => {
        // stockage
        if (remember) {
          localStorage.setItem(this.accessKey, access);
          localStorage.setItem(this.refreshKey, refresh);
          localStorage.setItem(this.userKey, username);
        } else {
          sessionStorage.setItem(this.accessKey, access);
          sessionStorage.setItem(this.refreshKey, refresh);
          sessionStorage.setItem(this.userKey, username);
        }
      }));
  }

  logout() {
    localStorage.removeItem(this.accessKey);
    localStorage.removeItem(this.refreshKey);
  }

  token(): string | null { return localStorage.getItem(this.accessKey); }
  isLoggedIn(): boolean { return !!this.token();}
  getUsername(): string { return localStorage.getItem('username') || 'Utilisateur'; }
}
