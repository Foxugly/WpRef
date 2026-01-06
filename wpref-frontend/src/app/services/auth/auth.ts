import {Injectable} from '@angular/core';
import {Observable, switchMap, tap} from 'rxjs';

import {UserService} from '../user/user';
import {
  AuthApi,
  CustomUserCreateRequestDto,
  CustomUserReadDto,
  PasswordChangeRequestDto,
  PasswordResetConfirmRequestDto,
  PasswordResetOKDto,
  PasswordResetRequestRequestDto,
  TokenApi,
  TokenObtainPairDto,
  TokenObtainPairRequestDto,
  TokenRefreshDto,
  TokenRefreshRequestDto,
  UserApi
} from '../../api/generated';

@Injectable({providedIn: 'root'})
export class AuthService {
  // --- storage keys
  private readonly ACCESS_KEY = 'access_token';
  private readonly REFRESH_KEY = 'refresh_token';
  private readonly USER_KEY = 'username';
  private readonly REMEMBER_KEY = 'remember_me';

  // --- in-memory cache
  private accessToken: string | null = null;
  private refreshToken: string | null = null;


  constructor(
    private tokenApi: TokenApi,
    private authApi: AuthApi,
    private userApi: UserApi,
    private userService: UserService
  ) {
    const storedAccess =
      localStorage.getItem(this.ACCESS_KEY) ??
      sessionStorage.getItem(this.ACCESS_KEY);

    const storedRefresh =
      localStorage.getItem(this.REFRESH_KEY) ??
      sessionStorage.getItem(this.REFRESH_KEY);

    this.accessToken = storedAccess;
    this.refreshToken = storedRefresh;
  }

  // -------------------------
  // Storage helpers

  get authenticated(): boolean {
    return this.isLoggedIn();
  }

  getToken(payload: TokenObtainPairRequestDto): Observable<TokenObtainPairDto> {
    console.log("getToken");
    return this.tokenApi.tokenCreate({tokenObtainPairRequestDto: payload});
  }


  login(username: string, password: string, remember = false): Observable<CustomUserReadDto> {
    console.log("login");
    const payload: TokenObtainPairRequestDto = {username, password};
    return this.getToken(payload).pipe(
      tap((dto: TokenObtainPairDto) => {
        this.setTokens(dto.access, dto.refresh, remember);
        this.setUsername(username, remember);
      }),
      //switchMap(() => this.userService.getMe()),
      switchMap(() => this.userService.getMe()),
    );
  }

  /**
   * POST /api/token/refresh/
   * Signature générée : tokenRefreshCreate({ tokenRefreshDto })
   */
  refreshTokens(): Observable<TokenRefreshDto> | null {
    const refresh: string | null = this.getRefreshToken();
    if (!refresh) return null;
    const payload: TokenRefreshRequestDto = {refresh};
    return this.tokenApi.tokenRefreshCreate({
      tokenRefreshRequestDto: payload
    }).pipe(
      tap((dto) => {
        const remember = this.rememberEnabled();
        this.setTokens(dto.access, refresh, remember);
      }),
    );
  }

  /**
   * POST /api/user/  (création ouverte)
   * Signature générée : userCreate({ customUserCreateDto })
   */
  register(payload: CustomUserCreateRequestDto): Observable<CustomUserReadDto> {
    return this.userApi.userCreate({customUserCreateRequestDto: payload});
  }

  // -------------------------
  // OpenAPI-aligned calls
  // -------------------------

  requestPasswordReset(payload: PasswordResetRequestRequestDto): Observable<PasswordResetOKDto> {
    return this.authApi.userPasswordResetCreate({passwordResetRequestRequestDto: payload});
  }

  confirmPasswordReset(payload: PasswordResetConfirmRequestDto): Observable<PasswordResetOKDto> {
    return this.authApi.userPasswordResetConfirmCreate({passwordResetConfirmRequestDto: payload});
  }

  changePassword(payload: PasswordChangeRequestDto): Observable<PasswordResetOKDto> {
    return this.authApi.userPasswordChangeCreate({passwordChangeRequestDto: payload});
  }

  // -------------------------
  logout(): void {
    this.accessToken = null;
    this.refreshToken = null;
    this.clearStoredAuth();
    this.userService.currentUser.set(null);

  }

  // -------------------------
  getAccessToken(): string | null {
    return this.accessToken;
  }

  getRefreshToken(): string | null {
    return this.refreshToken;
  }

  isLoggedIn(): boolean {
    return !!this.accessToken;
  }

  // -------------------------
  // Session helpers

  getUsername(): string {
    return (
      localStorage.getItem(this.USER_KEY) ??
      sessionStorage.getItem(this.USER_KEY) ??
      'Utilisateur'
    );
  }

  // -------------------------
  // Getters / state

  // -------------------------
  private clearStoredAuth(): void {
    localStorage.removeItem(this.ACCESS_KEY);
    localStorage.removeItem(this.REFRESH_KEY);
    localStorage.removeItem(this.USER_KEY);
    localStorage.removeItem(this.REMEMBER_KEY);

    sessionStorage.removeItem(this.ACCESS_KEY);
    sessionStorage.removeItem(this.REFRESH_KEY);
    sessionStorage.removeItem(this.USER_KEY);
    sessionStorage.removeItem(this.REMEMBER_KEY);
  }

  private clearStoredTokensOnly(): void {
    localStorage.removeItem(this.ACCESS_KEY);
    localStorage.removeItem(this.REFRESH_KEY);
    sessionStorage.removeItem(this.ACCESS_KEY);
    sessionStorage.removeItem(this.REFRESH_KEY);
  }

  private setTokens(access: string, refresh: string, remember: boolean): void {
    this.accessToken = access;
    this.refreshToken = refresh;

    this.clearStoredTokensOnly();

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

  private setUsername(username: string, remember: boolean): void {
    if (remember) localStorage.setItem(this.USER_KEY, username);
    else sessionStorage.setItem(this.USER_KEY, username);
  }

  private rememberEnabled(): boolean {
    return !!localStorage.getItem(this.REMEMBER_KEY);
  }
}
