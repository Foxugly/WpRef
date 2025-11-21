import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import {
  FormBuilder,
  FormGroup,
  ReactiveFormsModule,
  Validators,
  AbstractControl,
} from '@angular/forms';
import { AuthService } from '../../../services/auth';

@Component({
  selector: 'app-register',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule],
  templateUrl: './register.html',
  styleUrls: ['./register.css'],
})
export class Register {
  form!: FormGroup;
  submitted = false;
  isSubmitting = false;
  successMessage = '';
  errorMessage = '';

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
      group.get('confirm_password')?.setErrors({ passwordMismatch: true });
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

    const { username, email, first_name, last_name, password } =
      this.form.getRawValue();

    this.authService
      .register({
        username,
        email,
        first_name,
        last_name,
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
