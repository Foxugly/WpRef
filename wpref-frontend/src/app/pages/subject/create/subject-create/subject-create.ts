import { Component, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormBuilder, Validators, ReactiveFormsModule } from '@angular/forms';
import { Router } from '@angular/router';
import { Api } from '../../../../services/api';

@Component({
  standalone: true,
  selector: 'app-subject-create',
  imports: [CommonModule, ReactiveFormsModule],
  templateUrl: './subject-create.html',
  styleUrl: './subject-create.scss'
})
export class SubjectCreate {
  private fb = inject(FormBuilder);
  private api = inject(Api);
  private router = inject(Router);

  form = this.fb.nonNullable.group({
    name: ['', [Validators.required, Validators.minLength(2)]],
    description: ['']
  });

  save() {
    if (this.form.invalid) { this.form.markAllAsTouched(); return; }
    this.api.createSubject(this.form.value).subscribe({
      next: () => this.router.navigate(['/subject'])
    });
  }
}
