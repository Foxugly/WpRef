import {inject, Injectable} from '@angular/core';
import {HttpClient} from '@angular/common/http';
import {environment} from '../../environments/environment';
import {Observable} from 'rxjs';
import {tap} from 'rxjs/operators';

interface TokenPair {
  access: string;
  refresh: string;
}

export interface RegisterPayload {
  username: string;
  email: string;
  first_name: string;
  last_name: string;
  password: string;
}

@Injectable({providedIn: 'root'})
export class AuthService {
  private http = inject(HttpClient);
  private base = environment.apiBaseUrl;
  private tokenPath = environment.apiTokenPath;
  private passwordResetPath = environment.apiPasswordResetPath
  private registerPath = environment.apiRegisterPath
  private accessKey = 'jwt_access';
  private refreshKey = 'jwt_refresh';
  private userKey = 'username';

  getToken(username: string, password: string) {
    const url = new URL(this.tokenPath, this.base).toString();
    return this.http.post<TokenPair>(url, {username, password});
  }

  login(username: string, password: string, remember = false) {
    // NB: SimpleJWT = POST /api/token/
    return this.getToken(username, password)
      .pipe(tap(({access, refresh}) => {
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

  register(payload: RegisterPayload): Observable<any> {
    const url = new URL(this.passwordResetPath, this.base).toString();
    return this.http.post(url, payload);
  }

  requestPasswordReset(email: string): Observable<any> {
    const url = new URL(this.passwordResetPath, this.base).toString();
    return this.http.post(url, {email});
  }

  logout() {
    localStorage.removeItem(this.accessKey);
    localStorage.removeItem(this.refreshKey);
  }

  token(): string | null {
    return localStorage.getItem(this.accessKey);
  }

  isLoggedIn(): boolean {
    return !!this.token();
  }

  getUsername(): string {
    return localStorage.getItem('username') || 'Utilisateur';
  }
}
