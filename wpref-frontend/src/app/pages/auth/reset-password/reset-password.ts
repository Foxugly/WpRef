import {Component} from '@angular/core';
import {CommonModule} from '@angular/common';
import {FormBuilder, FormGroup, ReactiveFormsModule, Validators} from '@angular/forms';
import {AuthService} from '../../../services/auth';

@Component({
  selector: 'app-reset-password',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule],
  templateUrl: './reset-password.html',
  styleUrl: './reset-password.css',
})
export class ResetPassword {
  form!: FormGroup;
  submitted = false;
  isSubmitting = false;
  successMessage = '';
  errorMessage = '';

  constructor(
    private fb: FormBuilder,
    private authService: AuthService,
  ) {
    this.form = this.fb.nonNullable.group({
      email: ['', [Validators.required, Validators.email]],
    });
  }

  onSubmit() {
    this.submitted = true;
    this.successMessage = '';
    this.errorMessage = '';

    if (this.form.invalid) {
      this.form.markAllAsTouched();
      return;
    }

    this.isSubmitting = true;
    const email = this.form.value.email as string;

    this.authService.requestPasswordReset(email).subscribe({
      next: () => {
        this.isSubmitting = false;
        this.successMessage =
          "Si un compte existe avec cette adresse, un email de réinitialisation a été envoyé.";
      },
      error: (err) => {
        console.error(err);
        this.isSubmitting = false;
        this.errorMessage =
          "Une erreur est survenue. Veuillez réessayer plus tard.";
      },
    });
  }
}
