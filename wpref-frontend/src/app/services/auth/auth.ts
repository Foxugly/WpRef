import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { environment, LangCode } from '../../../environments/environment';
import { Observable, switchMap, tap } from 'rxjs';
import { UserService, Me } from '../user/user';

interface TokenPair {
  access: string;
  refresh: string;
}

export interface RegisterPayload {
  username: string;
  email: string;
  first_name: string;
  last_name: string;
  language: LangCode;
  password: string;
}

@Injectable({ providedIn: 'root' })
export class AuthService {
  private base = environment.apiBaseUrl;
  private tokenPath = environment.apiTokenPath;              // ex: "/api/token/"
  private tokenRefreshPath = environment.apiTokenRefreshPath; // ex: "/api/token/refresh/"
  private passwordResetPath = environment.apiPasswordResetPath;
  private registerPath = environment.apiUserPath;

  // clés de stockage
  private readonly ACCESS_KEY = 'access_token';
  private readonly REFRESH_KEY = 'refresh_token';
  private readonly USER_KEY = 'username';
  private readonly REMEMBER_KEY = 'remember_me';

  // valeurs en mémoire
  private accessToken: string | null = null;
  private refreshToken: string | null = null;

  constructor(
    private http: HttpClient,
    private userService: UserService,
  ) {
    // On regarde d’abord dans localStorage (remember), sinon sessionStorage
    const storedAccess =
      localStorage.getItem(this.ACCESS_KEY) ??
      sessionStorage.getItem(this.ACCESS_KEY);
    const storedRefresh =
      localStorage.getItem(this.REFRESH_KEY) ??
      sessionStorage.getItem(this.REFRESH_KEY);

    this.accessToken = storedAccess;
    this.refreshToken = storedRefresh;
  }

  private buildUrl(path: string): string {
    return new URL(path, this.base).toString();
  }

  private setTokens(access: string, refresh: string, remember: boolean) {
    this.accessToken = access;
    this.refreshToken = refresh;

    // On nettoie d'abord
    localStorage.removeItem(this.ACCESS_KEY);
    localStorage.removeItem(this.REFRESH_KEY);
    sessionStorage.removeItem(this.ACCESS_KEY);
    sessionStorage.removeItem(this.REFRESH_KEY);

    if (remember) {
      localStorage.setItem(this.ACCESS_KEY, access);
      localStorage.setItem(this.REFRESH_KEY, refresh);
      localStorage.setItem(this.REMEMBER_KEY, '1');
    } else {
      sessionStorage.setItem(this.ACCESS_KEY, access);
      sessionStorage.setItem(this.REFRESH_KEY, refresh);
      sessionStorage.removeItem(this.REMEMBER_KEY);
    }
  }

  getToken(username: string, password: string) {
    const url = this.buildUrl(this.tokenPath);
    return this.http.post<TokenPair>(url, { username, password });
  }

  login(username: string, password: string, remember = false) {
    return this.getToken(username, password).pipe(
      tap(({ access, refresh }) => {
        this.setTokens(access, refresh, remember);
        // on stocke le username dans le même storage que les tokens
        if (remember) {
          localStorage.setItem(this.USER_KEY, username);
        } else {
          sessionStorage.setItem(this.USER_KEY, username);
        }
      }),
      switchMap(() => this.userService.getMe()),
      tap((me: Me) => {
        console.log('Connecté en tant que', me.username, 'langue', me.language);
      }),
    );
  }

  register(payload: RegisterPayload): Observable<any> {
    const url = this.buildUrl(this.registerPath);
    return this.http.post(url, payload);
  }

  requestPasswordReset(email: string): Observable<any> {
    const url = this.buildUrl(this.passwordResetPath);
    return this.http.post(url, { email });
  }

  logout() {
    this.accessToken = null;
    this.refreshToken = null;

    localStorage.removeItem(this.ACCESS_KEY);
    localStorage.removeItem(this.REFRESH_KEY);
    localStorage.removeItem(this.USER_KEY);
    localStorage.removeItem(this.REMEMBER_KEY);

    sessionStorage.removeItem(this.ACCESS_KEY);
    sessionStorage.removeItem(this.REFRESH_KEY);
    sessionStorage.removeItem(this.USER_KEY);
  }

  getAccessToken(): string | null {
    return this.accessToken;
  }

  getRefreshToken(): string | null {
    return this.refreshToken;
  }

  refreshTokens() {
    const refresh = this.getRefreshToken();
    if (!refresh) {
      return null;
    }
    const url = this.buildUrl(this.tokenRefreshPath);
    const remember = !!localStorage.getItem(this.REMEMBER_KEY);

    return this.http.post<{ access: string }>(url, { refresh }).pipe(
      tap((res) => {
        this.setTokens(res.access, refresh, remember);
      }),
    );
  }

  isLoggedIn(): boolean {
    return !!this.accessToken;
  }

  getUsername(): string {
    return (
      localStorage.getItem(this.USER_KEY) ??
      sessionStorage.getItem(this.USER_KEY) ??
      'Utilisateur'
    );
  }
}
