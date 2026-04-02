import {HttpClient} from '@angular/common/http';
import {computed, Injectable, signal} from '@angular/core';
import {BehaviorSubject, Observable, tap} from 'rxjs';

import {LanguageEnumDto} from '../../api/generated/model/language-enum';
import {PatchedCustomUserProfileUpdateRequestDto} from '../../api/generated/model/patched-custom-user-profile-update-request';
import {CustomUserReadDto} from '../../api/generated/model/custom-user-read';
import {isSupportedLanguage, SupportedLanguage} from '../../../environments/language';
import {resolveApiBaseUrl} from '../../shared/api/runtime-api-base-url';

@Injectable({providedIn: 'root'})
export class UserService {
  currentUser = signal<CustomUserReadDto | null>(null);
  requiresPasswordChange = computed(() => this.shouldForcePasswordChange());
  isAdmin = computed(() => {
    const me = this.currentUser();
    return !!me && (me.is_staff || me.is_superuser);
  });

  private readonly STORAGE_KEY = 'lang';
  private readonly apiBaseUrl = `${resolveApiBaseUrl().replace(/\/+$/, '')}/api/user`;
  private readonly _lang$ = new BehaviorSubject<SupportedLanguage>(this.loadInitialLang());
  readonly lang$ = this._lang$.asObservable();

  constructor(private http: HttpClient) {
    this.applyLang(this._lang$.value);
  }

  get currentLang(): SupportedLanguage {
    return this._lang$.value;
  }

  shouldForcePasswordChange(user: CustomUserReadDto | null | undefined = this.currentUser()): boolean {
    return !!user && (
      user.must_change_password === true || user.new_password_asked === true
    );
  }

  shouldConfirmEmail(user: CustomUserReadDto | null | undefined = this.currentUser()): boolean {
    return !!user && user.email_confirmed === false;
  }

  list(): Observable<CustomUserReadDto[]> {
    return this.http.get<CustomUserReadDto[]>(`${this.apiBaseUrl}/`);
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
