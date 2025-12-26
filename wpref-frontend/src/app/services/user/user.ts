// src/app/services/user.service.ts
import {computed, Injectable, signal} from '@angular/core';
import {BehaviorSubject, Observable, tap} from 'rxjs';
import {UserApi} from '../../api/generated/api/user.service';
import {LanguageEnumDto} from '../../api/generated/model/language-enum';
import {MeDto} from '../../api/generated/model/me';

@Injectable({providedIn: 'root'})
export class UserService {
  // --------- Méthode moderne : on stocke /me dans un signal ---------
  currentUser = signal<MeDto | null>(null);
  isAdmin = computed(() => {
    const me: MeDto | null = this.currentUser();
    return !!me && (me.is_staff || me.is_superuser);
  });
  private readonly STORAGE_KEY = 'preferredLang';
  private currentLangSubject = new BehaviorSubject<LanguageEnumDto>(this.loadInitialLang());
  readonly lang$ = this.currentLangSubject.asObservable();

  constructor(private userApi: UserApi,) {
    // appliquer la langue au chargement
    this.applyLang(this.currentLangSubject.value);
  }

  /** Met à jour la langue côté frontend (Subject + localStorage + <html lang>) */
  setLocalLanguage(lang: LanguageEnumDto) {
    this.currentLangSubject.next(lang);
    localStorage.setItem(this.STORAGE_KEY, String(lang));
    this.applyLang(lang);
  }

  /** À appeler après un GET /me pour synchroniser la langue locale */
  syncLanguageFromMe(me: MeDto) {
    if (me.language) {
      this.setLocalLanguage(me.language);
    }
  }

  // -------- Appels HTTP /me --------

  getMe(): Observable<MeDto> {
    return this.userApi.userMeRetrieve().pipe(
      tap((me: MeDto) => {
        this.currentUser.set(me);
        this.syncLanguageFromMe(me);
      }),
    );
  }

  updateMeLanguage(language: LanguageEnumDto): Observable<MeDto> {
    return this.userApi.userMePartialUpdate({
      patchedMeDto: {language},
    }).pipe(
      tap((me: MeDto) => this.syncLanguageFromMe(me)),
    );
  }

  private loadInitialLang(): LanguageEnumDto {
    const stored = localStorage.getItem(this.STORAGE_KEY);
    return stored === LanguageEnumDto.En || stored === LanguageEnumDto.Fr || stored === LanguageEnumDto.Nl
    ? (stored === LanguageEnumDto.En ? LanguageEnumDto.En : stored === LanguageEnumDto.Fr ? LanguageEnumDto.Fr : LanguageEnumDto.Nl)
    : LanguageEnumDto.En;
  }

  private applyLang(lang: LanguageEnumDto) {
    document.documentElement.lang = String(lang);
  }
}
