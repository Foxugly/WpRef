// src/app/services/user.service.ts
import {Injectable, signal} from '@angular/core';
import {HttpClient} from '@angular/common/http';
import {BehaviorSubject, Observable, tap} from 'rxjs';
import {environment, LangCode} from '../../../environments/environment';


export interface Me {
  id: number;
  username: string;
  email: string;
  first_name: string;
  last_name: string;
  language: LangCode;
  is_staff: boolean;
  is_superuser: boolean;
}

@Injectable({providedIn: 'root'})
export class UserService {
  private base = environment.apiBaseUrl;
  private urlUserPreferencesPath = environment.apiUserPreferencesPath;
  private urlUserPasswordChangePath = environment.apiPasswordChangePath
  private readonly STORAGE_KEY = 'preferredLang';

   // --------- Méthode moderne : on stocke /me dans un signal ---------
  currentUser = signal<Me | null>(null);
  // -------- Gestion de la langue (ex-LanguageService) --------

  private currentLangSubject = new BehaviorSubject<LangCode>(this.loadInitialLang());
  currentLang$ = this.currentLangSubject.asObservable();

  constructor(private http: HttpClient) {
    // appliquer la langue au chargement
    this.applyLang(this.currentLangSubject.value);
  }

  private loadInitialLang(): LangCode {
    const stored = localStorage.getItem(this.STORAGE_KEY) as LangCode | null;
    return stored ?? 'en';
  }

  private applyLang(lang: LangCode) {
    document.documentElement.lang = lang;
  }

  /** Met à jour la langue côté frontend (Subject + localStorage + <html lang>) */
  setLocalLanguage(lang: LangCode) {
    this.currentLangSubject.next(lang);
    localStorage.setItem(this.STORAGE_KEY, lang);
    this.applyLang(lang);
  }

  /** À appeler après un GET /me pour synchroniser la langue locale */
  syncLanguageFromMe(me: Me) {
    if (me.language) {
      this.setLocalLanguage(me.language);
    }
  }

  // -------- Appels HTTP /me --------

  private buildMeUrl(): string {
    return new URL(this.urlUserPreferencesPath, this.base).toString();
  }

  getMe(): Observable<Me> {
    const url = this.buildMeUrl();
    return this.http.get<Me>(url).pipe(
      tap(me => {
        this.currentUser.set(me);
        this.syncLanguageFromMe(me);
      }), // on en profite pour synchroniser
    );
  }

  // ================================================================
  //                 MÉTHODE isAdmin()
  // ================================================================

  isAdmin(): boolean {
    const me = this.currentUser();
    return !!me && (me.is_staff || me.is_superuser);
  }

  // ================================================================
  //                 UPDATE LANG
  // ================================================================

  updateMeLanguage(language: LangCode): Observable<Me> {
    const url = this.buildMeUrl();
    return this.http.patch<Me>(url, {language}).pipe(
      tap(me => this.syncLanguageFromMe(me)),
    );
  }

  // ================================================================
  //                 PASSWORD CHANGE
  // ================================================================
  requestPasswordChange(old_password: string, new_password: string): Observable<any> {
    const url = new URL(this.urlUserPasswordChangePath, this.base).toString();
    return this.http.post(url, {old_password: old_password, new_password: new_password});
  }
}
