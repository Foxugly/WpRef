// src/app/pages/login/login.component.ts
import { Component, signal, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { Router, RouterLink  } from '@angular/router';
import { AuthService } from '../../services/auth';
import { Api } from '../../services/api';

@Component({
  standalone: true,
  selector: 'app-login',
  imports: [CommonModule, ReactiveFormsModule, RouterLink],
  templateUrl: './login.html',
  styleUrl: './login.scss'
})
export class Login {
  private fb = inject(FormBuilder);
  private auth = inject(AuthService);
  private router = inject(Router);

  hide = signal(true);
  loading = signal(false);
  errorMsg = signal<string | null>(null);

  form = this.fb.nonNullable.group({
    username: ['', [Validators.required, Validators.minLength(3)]],
    password: ['', [Validators.required, Validators.minLength(4)]],
    remember: [true]
  });

  get f() { return this.form.controls; }

  toggleHide() { this.hide.update(v => !v); }

  submit() {
    this.errorMsg.set(null);
    if (this.form.invalid) {
      this.form.markAllAsTouched();
      return;
    }
    this.loading.set(true);
    const { username, password, remember } = this.form.getRawValue();
    this.auth.login(username, password, remember).subscribe({
      next: () => {
        this.loading.set(false);
        this.router.navigate(['/subjects']);
      },
      error: (err) => {
        this.loading.set(false);
        // Message convivial
        this.errorMsg.set(err?.error?.detail || 'Identifiants invalides. Réessaie.');
      }
    });
  }
}
