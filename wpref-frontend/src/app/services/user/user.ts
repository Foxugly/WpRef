// src/app/services/user.service.ts
import {computed, Injectable, signal} from '@angular/core';
import {BehaviorSubject, Observable, tap} from 'rxjs';
import {CustomUserReadDto, LanguageEnumDto, UserApi, UserMePartialUpdateRequestParams} from '../../api/generated';
import {isSupportedLanguage, SupportedLanguage} from '../../../environments/language';


@Injectable({providedIn: 'root'})
export class UserService {
  // --------- Méthode moderne : on stocke /me dans un signal ---------
  currentUser = signal<CustomUserReadDto | null>(null);
  isAdmin = computed(() => {
    const me: CustomUserReadDto | null = this.currentUser();
    return !!me && (me.is_staff || me.is_superuser);
  });
  private readonly STORAGE_KEY = 'lang';
  private readonly _lang$ = new BehaviorSubject<SupportedLanguage>(this.loadInitialLang());
  readonly lang$ = this._lang$.asObservable();

  constructor(private userApi: UserApi) {
    // appliquer la langue au chargement
    this.applyLang(this._lang$.value);
  }

  get currentLang(): SupportedLanguage {
    return this._lang$.value;
  }

  /** Met à jour la langue côté frontend (Subject + localStorage + <html lang>) */
  setLang(lang: SupportedLanguage) {
    this._lang$.next(lang);
    localStorage.setItem(this.STORAGE_KEY, String(lang));
    this.applyLang(lang);
  }

  setFromApi(lang: LanguageEnumDto | null | undefined): void {
    if (lang && isSupportedLanguage(lang)) {
      this.setLang(lang);
    } else {
      this.setLang(LanguageEnumDto.En);
    }
  }

  /** À appeler après un GET /me pour synchroniser la langue locale */
  syncLanguageFromMe(me: CustomUserReadDto) {
    if (me.language) {
      this.setLang(me.language);
    }
  }

  // -------- Appels HTTP /me --------

  getMe(): Observable<CustomUserReadDto> {
    return this.userApi.userMeRetrieve().pipe(
      tap((me: CustomUserReadDto) => {
        this.currentUser.set(me);
        this.syncLanguageFromMe(me);
      }),
    );
  }

  updateMeLanguage(language: LanguageEnumDto): Observable<CustomUserReadDto> {
    const payload: UserMePartialUpdateRequestParams = {patchedCustomUserReadRequestDto: {language: language}};
    return this.userApi.userMePartialUpdate(payload).pipe(
      tap((me: CustomUserReadDto) => this.syncLanguageFromMe(me)),
    );
  }

  private loadInitialLang(): SupportedLanguage { // TODO
    const stored = localStorage.getItem(this.STORAGE_KEY);
    if (stored && isSupportedLanguage(stored)) return stored;
    return LanguageEnumDto.En;
  }

  private applyLang(lang: LanguageEnumDto) {
    document.documentElement.lang = String(lang);
  }
}
