import {Component, DestroyRef, inject, signal} from '@angular/core';
import {NonNullableFormBuilder, ReactiveFormsModule, Validators} from '@angular/forms';
import {Router} from '@angular/router';
import {finalize} from 'rxjs/operators';
import {takeUntilDestroyed} from '@angular/core/rxjs-interop';

import {InputTextModule} from 'primeng/inputtext';
import {MessageModule} from 'primeng/message';
import {ButtonModule} from 'primeng/button';

import {AuthService} from '../../../services/auth/auth';
import {ROUTES} from '../../../app.routes-paths';

@Component({
  selector: 'app-reset-password',
  standalone: true,
  imports: [ReactiveFormsModule, InputTextModule, MessageModule, ButtonModule],
  templateUrl: './reset-password.html',
  styleUrl: './reset-password.scss',
})
export class ResetPassword {
  private readonly fb = inject(NonNullableFormBuilder);
  private readonly authService = inject(AuthService);
  private readonly router = inject(Router);
  private readonly destroyRef = inject(DestroyRef);

  // State
  readonly submitted = signal(false);
  readonly isSubmitting = signal(false);
  readonly successMessage = signal<string | null>(null);
  readonly errorMessage = signal<string | null>(null);
  readonly submitError = signal<string | null>(null);
  readonly loading = signal(false);

  // Typed Form
  readonly form = this.fb.group({
    email: this.fb.control('', [Validators.required, Validators.email]),
  });

  onSubmit(): void {
    this.submitted.set(true);
    this.successMessage.set(null);
    this.errorMessage.set(null);
    this.submitError.set(null);

    if (this.form.invalid) {
      this.form.markAllAsTouched();
      this.submitError.set('Corrige les erreurs dans le formulaire.');
      return;
    }

    const email = this.form.controls.email.value.trim();
    if (!email) {
      this.submitError.set("L'adresse e-mail est obligatoire.");
      return;
    }

    this.isSubmitting.set(true);

    this.authService
      .requestPasswordReset({email})
      .pipe(
        takeUntilDestroyed(this.destroyRef),
        finalize(() => this.isSubmitting.set(false)),
      )
      .subscribe({
        next: () => {
          // Message “safe” (ne révèle pas si l’email existe)
          this.successMessage.set(
            "Si un compte existe avec cette adresse, un email de réinitialisation a été envoyé.",
          );
        },
        error: (err) => {
          console.error(err);
          this.errorMessage.set('Une erreur est survenue. Veuillez réessayer plus tard.');
        },
      });
  }

  goHome(): void {
    this.router.navigate(ROUTES.home());
  }

}
