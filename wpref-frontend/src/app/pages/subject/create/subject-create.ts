import {Component, inject} from '@angular/core';

import {FormBuilder, ReactiveFormsModule, Validators} from '@angular/forms';
import {SubjectService} from '../../../services/subject/subject';
import {Editor} from 'primeng/editor';
import {InputTextModule} from 'primeng/inputtext';
import {Button} from 'primeng/button';
import {SubjectCreateRequestParams, SubjectWriteRequestDto} from '../../../api/generated';

@Component({
  standalone: true,
  selector: 'app-subject-create',
  imports: [ReactiveFormsModule, Editor, Button, InputTextModule],
  templateUrl: './subject-create.html',
  styleUrl: './subject-create.scss',
})
export class SubjectCreate {
  // Injections
  private fb = inject(FormBuilder);
  // Formulaire
  form = this.fb.nonNullable.group({
    name: ['', [Validators.required, Validators.minLength(2)]],
    description: [''],
  });
  private subjectService = inject(SubjectService);

  goBack(): void {
    this.subjectService.goBack();
  }

  save() {
    if (this.form.invalid) {
      this.form.markAllAsTouched();
      return;
    }
    const payload: SubjectCreateRequestParams = {subjectWriteRequestDto:this.form.value as SubjectWriteRequestDto};
    this.subjectService.create(payload).subscribe({
      next: () => this.subjectService.goList(),
    });
  }
}
