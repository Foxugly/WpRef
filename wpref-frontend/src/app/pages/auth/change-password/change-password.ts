import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { UserService } from '../../../services/user';

import {
  FormBuilder,
  FormGroup,
  ReactiveFormsModule,
  Validators,
  AbstractControl,
} from '@angular/forms';

@Component({
  selector: 'app-change-password',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule],
  templateUrl: './change-password.html',
  styleUrl: './change-password.scss',
})
export class ChangePassword {
  form!: FormGroup;
  submitted = false;
  isSubmitting = false;
  successMessage = '';
  errorMessage = '';

  constructor(
    private fb: FormBuilder,
    private userService: UserService
  ) {
    this.form = this.fb.nonNullable.group(
      {
        old_password: ['', [Validators.required]],
        new_password: ['', [Validators.required, Validators.minLength(8)]],
        confirm_new_password: ['', [Validators.required]],
      },
      {
        validators: [this.passwordsMatchValidator],
      },
    );
  }

  // --- Validateur custom pour comparer les 2 nouveaux mots de passe ---
  private passwordsMatchValidator(group: AbstractControl) {
    const newPwd = group.get('new_password')?.value;
    const confirm = group.get('confirm_new_password')?.value;

    if (newPwd && confirm && newPwd !== confirm) {
      group.get('confirm_new_password')?.setErrors({ passwordMismatch: true });
    } else {
      const ctrl = group.get('confirm_new_password');
      if (!ctrl) return null;

      const errors = ctrl.errors;
      if (errors && errors['passwordMismatch']) {
        delete errors['passwordMismatch'];
        ctrl.setErrors(Object.keys(errors).length ? errors : null);
      }
    }
    return null;
  }

  // Raccourci pour le template
  get f() {
    return this.form.controls;
  }

  onSubmit(): void {
    this.submitted = true;
    this.successMessage = '';
    this.errorMessage = '';

    if (this.form.invalid) {
      this.form.markAllAsTouched();
      return;
    }

    this.isSubmitting = true;

    // 🔴 AVANT : const { old_password, new_password1, new_password2 } = ...
    // ✅ MAINTENANT : on récupère les vrais noms des contrôles
    const { old_password, new_password  } = this.form.getRawValue();


    this.userService.requestPasswordChange(
      old_password, new_password).subscribe({
      next: () => {
        this.isSubmitting = false;
        this.successMessage = 'Votre mot de passe a été modifié.';
        this.form.reset();
        this.submitted = false;
      },
      error: (err) => {
        this.isSubmitting = false;
        console.error(err);

        // Petit traitement des erreurs typiques DRF
        if (err.status === 400 && err.error) {
          const e = err.error;
          if (e.old_password && Array.isArray(e.old_password)) {
            this.errorMessage = e.old_password.join(' ');
            return;
          }
          if (e.new_password1 && Array.isArray(e.new_password1)) {
            this.errorMessage = e.new_password1.join(' ');
            return;
          }
          if (e.non_field_errors && Array.isArray(e.non_field_errors)) {
            this.errorMessage = e.non_field_errors.join(' ');
            return;
          }
        }

        this.errorMessage =
          "Une erreur est survenue lors de la modification du mot de passe.";
      },
    });
  }
}
