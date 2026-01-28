import {Component, OnInit} from '@angular/core';
import {
  AbstractControl,
  FormBuilder,
  FormGroup,
  ReactiveFormsModule,
  ValidationErrors,
  Validators,
} from '@angular/forms';
import {finalize} from 'rxjs/operators';

import {InputTextModule} from 'primeng/inputtext';
import {PasswordModule} from 'primeng/password';

import {AuthService} from '../../../services/auth/auth';
import {LanguageService} from '../../../services/language/language';
import {LanguageReadDto} from '../../../api/generated';
import {ButtonModule} from 'primeng/button';
import {ROUTES} from '../../../app.routes-paths';
import {Router} from '@angular/router';
import {SelectModule} from 'primeng/select';

@Component({
  selector: 'app-register',
  standalone: true,
  imports: [ReactiveFormsModule, InputTextModule, PasswordModule, ButtonModule, SelectModule],
  templateUrl: './register.html',
  styleUrls: ['./register.scss'],
})
export class Register implements OnInit {
  app = window.__APP__!;

  form: FormGroup;

  submitted = false;
  isSubmitting = false;

  successMessage = '';
  errorMessage = '';

  // Langues backend
  languages: LanguageReadDto[] = [];
  loadingLanguages = false;

  constructor(
    private fb: FormBuilder,
    private authService: AuthService,
    private languageService: LanguageService,
    private router: Router,
  ) {
    this.form = this.fb.nonNullable.group(
      {
        username: ['', [Validators.required]],
        email: ['', [Validators.required, Validators.email]],
        first_name: ['', [Validators.required]],
        last_name: ['', [Validators.required]],
        language: ['', [Validators.required]], // <- valeur fixée après chargement
        password: ['', [Validators.required, Validators.minLength(8)]],
        confirm_password: ['', [Validators.required]],
      },
      {validators: [Register.passwordsMatchValidator]},
    );
  }

  // ----- Helper template -----
  get f() {
    return this.form.controls;
  }

  // ----- Validator password/confirm (set error on confirm_password) -----
  private static passwordsMatchValidator(control: AbstractControl): ValidationErrors | null {
    const pwd = control.get('password')?.value;
    const confirmCtrl = control.get('confirm_password');
    const confirm = confirmCtrl?.value;

    if (!confirmCtrl) return null;
    if (!pwd || !confirm) return null;

    if (pwd !== confirm) {
      const current = confirmCtrl.errors ?? {};
      if (!current['passwordMismatch']) {
        confirmCtrl.setErrors({...current, passwordMismatch: true});
      }
    } else {
      const current = confirmCtrl.errors ?? {};
      if (current['passwordMismatch']) {
        const {passwordMismatch, ...rest} = current;
        confirmCtrl.setErrors(Object.keys(rest).length ? rest : null);
      }
    }

    return null;
  }

  ngOnInit(): void {
    this.loadLanguages();
  }

  // ----- Submit -----
  onSubmit(): void {
    this.submitted = true;
    this.successMessage = '';
    this.errorMessage = '';

    this.form.updateValueAndValidity();

    if (this.form.invalid) {
      this.form.markAllAsTouched();
      return;
    }

    this.isSubmitting = true;

    const {username, email, first_name, last_name, language, password} =
      this.form.getRawValue();

    this.authService
      .register({username, email, first_name, last_name, language, password})
      .pipe(finalize(() => (this.isSubmitting = false)))
      .subscribe({
        next: () => {
          this.successMessage =
            'Votre compte a été créé. Vous pouvez maintenant vous connecter.';
          this.submitted = false;

          // reset propre + remettre langue par défaut
          this.form.reset();
          const defaultLang = this.languages[0]?.code ?? 'en';
          this.form.get('language')?.setValue(String(defaultLang));
        },
        error: (err) => {
          console.error(err);
          this.errorMessage = this.formatRegisterError(err);
        },
      });
  }

  // ----- Langues (backend) -----
  private loadLanguages(): void {
    this.loadingLanguages = true;

    this.languageService
      .list()
      .pipe(finalize(() => (this.loadingLanguages = false)))
      .subscribe({
        next: (langs) => {
          // Some generated DTOs may have active?: boolean; if not present, this keeps all.
          const active = (langs ?? []).filter((l: any) => l?.active !== false);
          this.languages = active;

          // Default language (if empty)
          if (!this.form.get('language')?.value) {
            const defaultLang = active[0]?.code ?? 'en';
            this.form.get('language')?.setValue(String(defaultLang));
          }
        },
        error: (err) => {
          console.error(err);
          this.languages = [];
          this.errorMessage = "Impossible de charger la liste des langues. Réessayez.";

          // Fallback safe
          if (!this.form.get('language')?.value) {
            this.form.get('language')?.setValue('en');
          }
        },
      });
  }

  // ----- DRF error formatting (best-effort) -----
  private formatRegisterError(err: any): string {
    const data = err?.error;

    // DRF: {"detail": "..."}
    if (typeof data?.detail === 'string' && data.detail.trim()) {
      return data.detail;
    }

    // DRF: field errors {"email": ["..."], "username": ["..."]}
    if (data && typeof data === 'object') {
      const keys = Object.keys(data);
      if (keys.length) {
        const k = keys[0];
        const v = data[k];
        if (Array.isArray(v) && typeof v[0] === 'string') return v[0];
        if (typeof v === 'string') return v;
      }
    }

    return "L'inscription a échoué. Vérifiez les informations et réessayez.";
  }
  goRegister(): void {
    this.router.navigate(ROUTES.auth.register());
  }

  goLogin(): void {
    this.router.navigate(ROUTES.auth.login());
  }
}
