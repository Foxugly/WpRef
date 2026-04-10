import {HttpClient} from '@angular/common/http';
import {computed, Injectable, signal} from '@angular/core';
import {BehaviorSubject, map, Observable, tap} from 'rxjs';

import {UserApi} from '../../api/generated';
import {LanguageEnumDto} from '../../api/generated/model/language-enum';
import {PatchedCustomUserProfileUpdateRequestDto} from '../../api/generated/model/patched-custom-user-profile-update-request';
import {CustomUserReadDto} from '../../api/generated/model/custom-user-read';
import {isSupportedLanguage, SupportedLanguage} from '../../../environments/language';
import {resolveApiBaseUrl} from '../../shared/api/runtime-api-base-url';

export type AdminUserDto = CustomUserReadDto & {
  nb_domain_max?: number;
};

export type AdminUserCreatePayload = {
  username: string;
  email?: string;
  first_name?: string;
  last_name?: string;
  password: string;
  language?: LanguageEnumDto;
  nb_domain_max?: number;
};

export type AdminUserUpdatePayload = {
  email?: string;
  first_name?: string;
  last_name?: string;
  language?: LanguageEnumDto;
  password?: string;
  is_active?: boolean;
  password_change_required?: boolean;
  nb_domain_max?: number;
};

@Injectable({providedIn: 'root'})
export class UserService {
  currentUser = signal<CustomUserReadDto | null>(null);
  requiresPasswordChange = computed(() => this.shouldForcePasswordChange());
  isAdmin = computed(() => {
    const me = this.currentUser();
    return !!me && (me.is_staff || me.is_superuser);
  });
  isSuperuser = computed(() => this.currentUser()?.is_superuser === true);

  private readonly STORAGE_KEY = 'lang';
  private readonly apiBaseUrl = `${resolveApiBaseUrl().replace(/\/+$/, '')}/api/user`;
  private readonly _lang$ = new BehaviorSubject<SupportedLanguage>(this.loadInitialLang());
  readonly lang$ = this._lang$.asObservable();

  constructor(private http: HttpClient, private userApi: UserApi) {
    this.applyLang(this._lang$.value);
  }

  get currentLang(): SupportedLanguage {
    return this._lang$.value;
  }

  shouldForcePasswordChange(user: CustomUserReadDto | null | undefined = this.currentUser()): boolean {
    return !!user && user.password_change_required === true;
  }

  shouldConfirmEmail(user: CustomUserReadDto | null | undefined = this.currentUser()): boolean {
    return !!user && user.email_confirmed === false;
  }

  list(): Observable<CustomUserReadDto[]> {
    return this.http.get<CustomUserReadDto[] | {results?: CustomUserReadDto[]}>(`${this.apiBaseUrl}/`).pipe(
      map((response) => Array.isArray(response) ? response : (response.results ?? [])),
    );
  }

  listAdmin(): Observable<AdminUserDto[]> {
    return this.userApi.userList().pipe(
      map((response) => response.results ?? []),
    );
  }

  retrieveAdmin(userId: number): Observable<AdminUserDto> {
    return this.http.get<AdminUserDto>(`${this.apiBaseUrl}/${userId}/`);
  }

  createAdmin(payload: AdminUserCreatePayload): Observable<AdminUserDto> {
    return this.http.post<AdminUserDto>(`${this.apiBaseUrl}/`, payload);
  }

  updateAdmin(userId: number, payload: AdminUserUpdatePayload): Observable<AdminUserDto> {
    return this.http.patch<AdminUserDto>(`${this.apiBaseUrl}/${userId}/`, payload);
  }

  deleteAdmin(userId: number): Observable<void> {
    return this.http.delete<void>(`${this.apiBaseUrl}/${userId}/`);
  }

  setLang(lang: SupportedLanguage) {
    this._lang$.next(lang);
    localStorage.setItem(this.STORAGE_KEY, String(lang));
    this.applyLang(lang);
  }

  setFromApi(lang: LanguageEnumDto | null | undefined): void {
    if (lang && isSupportedLanguage(lang)) {
      this.setLang(lang);
      return;
    }
    this.setLang(LanguageEnumDto.En);
  }

  syncLanguageFromMe(me: CustomUserReadDto) {
    if (me.language) {
      this.setLang(me.language);
    }
  }

  getMe(): Observable<CustomUserReadDto> {
    return this.http.get<CustomUserReadDto>(`${this.apiBaseUrl}/me/`).pipe(
      tap((me) => {
        this.currentUser.set(me);
        this.syncLanguageFromMe(me);
      }),
    );
  }

  updateMeLanguage(language: LanguageEnumDto): Observable<CustomUserReadDto> {
    return this.updateMeProfile({language}).pipe(
      tap((me) => this.syncLanguageFromMe(me)),
    );
  }

  updateMeProfile(payload: PatchedCustomUserProfileUpdateRequestDto): Observable<CustomUserReadDto> {
    return this.http.patch<CustomUserReadDto>(`${this.apiBaseUrl}/me/`, payload).pipe(
      tap((me) => {
        this.currentUser.set(me);
        this.syncLanguageFromMe(me);
      }),
    );
  }

  setCurrentDomain(domainId: number | null): Observable<CustomUserReadDto> {
    return this.http.post<CustomUserReadDto>(`${this.apiBaseUrl}/me/current-domain/`, {
      domain_id: domainId,
    }).pipe(
      tap((me) => {
        this.currentUser.set(me);
        this.syncLanguageFromMe(me);
      }),
    );
  }

  private loadInitialLang(): SupportedLanguage {
    const stored = localStorage.getItem(this.STORAGE_KEY);
    if (stored && isSupportedLanguage(stored)) {
      return stored;
    }
    return LanguageEnumDto.En;
  }

  private applyLang(lang: LanguageEnumDto) {
    document.documentElement.lang = String(lang);
  }
}
