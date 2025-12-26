import {Component} from '@angular/core';

import {AbstractControl, FormBuilder, FormGroup, ReactiveFormsModule, Validators,} from '@angular/forms';
import {AuthService} from '../../../services/auth/auth';
import {InputTextModule} from 'primeng/inputtext';
import {PasswordModule} from 'primeng/password';

@Component({
  selector: 'app-register',
  standalone: true,
  imports: [ReactiveFormsModule, InputTextModule, PasswordModule],
  templateUrl: './register.html',
  styleUrls: ['./register.scss'],
})
export class Register {
  form!: FormGroup;
  submitted = false;
  isSubmitting = false;
  successMessage = '';
  errorMessage = '';
  hide = true; // 👈 booléen simple

  constructor(
    private fb: FormBuilder,
    private authService: AuthService,
  ) {
    this.form = this.fb.nonNullable.group(
      {
        username: ['', [Validators.required]],
        email: ['', [Validators.required, Validators.email]],
        first_name: ['', [Validators.required]],
        last_name: ['', [Validators.required]],
        language: ['en', [Validators.required]],
        password: ['', [Validators.required, Validators.minLength(8)]],
        confirm_password: ['', [Validators.required]],
      },
      {
        // ✅ validateur de groupe pour matcher password / confirm_password
        validators: [this.passwordsMatchValidator],
      },
    );
  }

  // ----- Validateur custom -----

  private passwordsMatchValidator(group: AbstractControl) {
    const pwd = group.get('password')?.value;
    const confirm = group.get('confirm_password')?.value;

    if (pwd && confirm && pwd !== confirm) {
      group.get('confirm_password')?.setErrors({passwordMismatch: true});
    } else {
      const errors = group.get('confirm_password')?.errors;
      if (errors && errors['passwordMismatch']) {
        // on retire uniquement l'erreur passwordMismatch
        delete errors['passwordMismatch'];
        if (Object.keys(errors).length === 0) {
          group.get('confirm_password')?.setErrors(null);
        } else {
          group.get('confirm_password')?.setErrors(errors);
        }
      }
    }
    return null;
  }

  // ----- Raccourci pour le template -----

  get f() {
    return this.form.controls;
  }

  toggleHide() {
    this.hide = !this.hide;
  }

  // ----- Soumission -----

  onSubmit(): void {
    this.submitted = true;
    this.successMessage = '';
    this.errorMessage = '';

    if (this.form.invalid) {
      this.form.markAllAsTouched();
      return;
    }

    this.isSubmitting = true;

    const {username, email, first_name, last_name, language, password} =
      this.form.getRawValue();

    this.authService
      .register({
        username,
        email,
        first_name,
        last_name,
        language,
        password,
      })
      .subscribe({
        next: () => {
          this.isSubmitting = false;
          this.successMessage = 'Votre compte a été créé. Vous pouvez maintenant vous connecter. Gérer via mail '; // TODO
          this.form.reset();
          this.submitted = false;
        },
        error: (err) => {
          console.error(err);
          this.isSubmitting = false;
          // À adapter en fonction de la réponse DRF (erreurs de validation, etc.)
          this.errorMessage =
            "L'inscription a échoué. Vérifiez les informations et réessayez.";
        },
      });
  }
}
