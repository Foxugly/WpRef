import { Component, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { Router, RouterLink } from '@angular/router';
import { SubjectService } from '../../../services/subject/subject';
import {Editor} from 'primeng/editor';
import {InputTextModule} from 'primeng/inputtext';
import {Button} from 'primeng/button';

@Component({
  standalone: true,
  selector: 'app-subject-create',
  imports: [CommonModule, RouterLink, ReactiveFormsModule, Editor, Button, InputTextModule],
  templateUrl: './subject-create.html',
  styleUrl: './subject-create.scss',
})
export class SubjectCreate {
  // Injections
  private fb = inject(FormBuilder);
  private router = inject(Router);
  private subjectService = inject(SubjectService);

  // Formulaire
  form = this.fb.nonNullable.group({
    name: ['', [Validators.required, Validators.minLength(2)]],
    description: [''],
  });

  save() {
    if (this.form.invalid) {
      this.form.markAllAsTouched();
      return;
    }

    this.subjectService.create(this.form.value).subscribe({
      next: () => this.router.navigate(['/subject/list']),
    });
  }
}
