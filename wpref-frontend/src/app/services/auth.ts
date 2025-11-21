import {Injectable} from '@angular/core';
import {HttpClient} from '@angular/common/http';
import {environment, LangCode} from '../../environments/environment';
import {Observable, switchMap, tap} from 'rxjs';
import {UserService, Me} from './user';

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

@Injectable({providedIn: 'root'})
export class AuthService {
  private base = environment.apiBaseUrl;
  private tokenPath = environment.apiTokenPath;
  private passwordResetPath = environment.apiPasswordResetPath;
  private registerPath = environment.apiUserPath;
  private accessKey = 'jwt_access';
  private refreshKey = 'jwt_refresh';
  private userKey = 'username';

  constructor(
    private http: HttpClient,
    private userService: UserService,
  ) {
  }

  getToken(username: string, password: string) {
    const url = new URL(this.tokenPath, this.base).toString();
    return this.http.post<TokenPair>(url, {username, password});
  }


  login(username: string, password: string, remember = false) {
    // NB: SimpleJWT = POST /api/token/
    return this.getToken(username, password)
      .pipe(
        tap(({access, refresh}) => {
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
        }),
        switchMap(() => this.userService.getMe()),
        tap((me: Me) => {
          // getMe() synchronise déjà la langue via syncLanguageFromMe,
          // donc tu n'as rien de plus à faire ici.
          console.log('Connecté en tant que', me.username, 'langue', me.language);
        }),
      );
  }

  register(payload: RegisterPayload): Observable<any> {
    const url = new URL(this.registerPath, this.base).toString();
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
