import {Injectable} from '@angular/core';
import {Observable, switchMap, tap} from 'rxjs';

import {TokenApi} from '../../api/generated/api/token.service';
import {AuthApi} from '../../api/generated/api/auth.service';
import {UserApi} from '../../api/generated/api/user.service';

import {TokenObtainPairDto} from '../../api/generated/model/token-obtain-pair';
import {TokenRefreshDto} from '../../api/generated/model/token-refresh';
import {CustomUserCreateDto} from '../../api/generated/model/custom-user-create';
import {CustomUserReadDto} from '../../api/generated/model/custom-user-read';

import {
  MeDto,
  PasswordChangeDto,
  PasswordResetConfirmDto,
  PasswordResetOKDto,
  PasswordResetRequestDto
} from '../../api/generated';
import {UserService} from '../user/user';


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
    //private userService: UserService,
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

  /**
   * POST /api/token/
   * Signature générée : tokenCreate({ tokenObtainPairDto })
   */
  getToken(username: string, password: string): Observable<TokenObtainPairDto> {
    const tokenObtainPairDto = {username, password} as TokenObtainPairDto;
    return this.tokenApi.tokenCreate({tokenObtainPairDto});
  }

  /**
   * Login = tokenCreate -> store -> userService.getMe()
   */
  login(username: string, password: string, remember = false): Observable<MeDto> {
    return this.getToken(username, password).pipe(
      tap((dto) => {
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
    const refresh = this.getRefreshToken();
    if (!refresh) return null;

    const tokenRefreshDto = {refresh} as TokenRefreshDto;

    return this.tokenApi.tokenRefreshCreate({tokenRefreshDto}).pipe(
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
  register(payload: CustomUserCreateDto): Observable<CustomUserReadDto> {
    const customUserCreateDto: CustomUserCreateDto = {
      username: payload.username,
      email: payload.email,
      first_name: payload.first_name,
      last_name: payload.last_name,
      password: payload.password,
      // is_staff/is_superuser/is_active: non envoyés
    };

    return this.userApi.userCreate({customUserCreateDto});
  }

  // -------------------------
  // OpenAPI-aligned calls
  // -------------------------

  /**
   * POST /api/user/password/reset/
   * Signature générée : userPasswordResetCreate({ passwordResetRequestDto })
   */
  requestPasswordReset(email: string): Observable<any> {
    const passwordResetRequestDto: PasswordResetRequestDto = {email};
    return this.authApi.userPasswordResetCreate({passwordResetRequestDto});
  }

  /**
   * POST /api/user/password/reset/confirm/
   */
  confirmPasswordReset(dto: PasswordResetConfirmDto): Observable<PasswordResetOKDto> {
    return this.authApi.userPasswordResetConfirmCreate({
      passwordResetConfirmDto: dto,
    });
  }

  /**
   * POST /api/user/password/change/
   */
  changePassword(payload: PasswordChangeDto): Observable<any> {
    return this.authApi.userPasswordChangeCreate({
      passwordChangeDto: payload,
    });
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
