import {Component, DestroyRef, inject, signal} from '@angular/core';
import {ActivatedRoute, Router, RouterLink} from '@angular/router';
import {AbstractControl, NonNullableFormBuilder, ReactiveFormsModule, Validators} from '@angular/forms';
import {takeUntilDestroyed} from '@angular/core/rxjs-interop';
import {finalize} from 'rxjs/operators';

import {ButtonModule} from 'primeng/button';
import {MessageModule} from 'primeng/message';
import {PasswordModule} from 'primeng/password';

import {AuthService} from '../../../services/auth/auth';
import {ROUTES} from '../../../app.routes-paths';

@Component({
  selector: 'app-reset-password-confirm',
  standalone: true,
  imports: [ReactiveFormsModule, RouterLink, PasswordModule, MessageModule, ButtonModule],
  templateUrl: './reset-password-confirm.html',
  styleUrl: './reset-password-confirm.scss',
})
export class ResetPasswordConfirmPage {
  private readonly fb = inject(NonNullableFormBuilder);
  private readonly authService = inject(AuthService);
  private readonly route = inject(ActivatedRoute);
  private readonly router = inject(Router);
  private readonly destroyRef = inject(DestroyRef);

  readonly submitted = signal(false);
  readonly isSubmitting = signal(false);
  readonly successMessage = signal<string | null>(null);
  readonly errorMessage = signal<string | null>(null);
  readonly invalidLink = signal(false);

  private uid = '';
  private token = '';

  readonly form = this.fb.group(
    {
      new_password1: this.fb.control('', [Validators.required, Validators.minLength(8)]),
      new_password2: this.fb.control('', [Validators.required]),
    },
    {
      validators: [ResetPasswordConfirmPage.passwordsMatchValidator],
    },
  );

  constructor() {
    this.route.paramMap.pipe(takeUntilDestroyed(this.destroyRef)).subscribe((params) => {
      this.uid = params.get('uid') ?? '';
      this.token = params.get('token') ?? '';
      this.invalidLink.set(!this.uid || !this.token);
      this.successMessage.set(null);
      this.errorMessage.set(
        !this.uid || !this.token ? 'Lien de réinitialisation invalide ou incomplet.' : null,
      );
    });
  }

  get f() {
    return this.form.controls;
  }

  private static passwordsMatchValidator(control: AbstractControl) {
    const pwd = control.get('new_password1')?.value;
    const confirmCtrl = control.get('new_password2');
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
        delete current['passwordMismatch'];
        confirmCtrl.setErrors(Object.keys(current).length ? current : null);
      }
    }

    return null;
  }

  onSubmit(): void {
    this.submitted.set(true);
    this.successMessage.set(null);
    this.errorMessage.set(null);

    if (this.invalidLink()) {
      this.errorMessage.set('Lien de réinitialisation invalide ou expiré.');
      return;
    }

    if (this.form.invalid) {
      this.form.markAllAsTouched();
      return;
    }

    this.isSubmitting.set(true);
    const payload = {
      uid: this.uid,
      token: this.token,
      ...this.form.getRawValue(),
    };

    this.authService
      .confirmPasswordReset(payload)
      .pipe(
        takeUntilDestroyed(this.destroyRef),
        finalize(() => this.isSubmitting.set(false)),
      )
      .subscribe({
        next: () => {
          this.successMessage.set('Votre mot de passe a été réinitialisé. Vous pouvez vous connecter.');
          this.form.reset();
          this.submitted.set(false);
        },
        error: (err) => {
          this.errorMessage.set(this.formatError(err));
        },
      });
  }

  goLogin(): void {
    this.router.navigate(ROUTES.auth.login());
  }

  private formatError(err: any): string {
    const data = err?.error;

    if (typeof data?.detail === 'string' && data.detail.trim()) {
      return data.detail;
    }

    if (data && typeof data === 'object') {
      for (const key of ['new_password1', 'new_password2', 'token', 'uid', 'non_field_errors']) {
        const value = data[key];
        if (Array.isArray(value) && typeof value[0] === 'string') {
          return value[0];
        }
        if (typeof value === 'string') {
          return value;
        }
      }
    }

    return 'Impossible de réinitialiser le mot de passe.';
  }
}
