import { Component, OnInit, inject } from '@angular/core';

import { FormBuilder, Validators, ReactiveFormsModule } from '@angular/forms';
import { ActivatedRoute, Router, RouterLink } from '@angular/router';
import { SubjectService, Subject } from '../../../services/subject/subject';
import { Question } from '../../../services/question/question';
import {Editor} from 'primeng/editor';
import {InputTextModule} from 'primeng/inputtext';
import {Button} from 'primeng/button';


@Component({
  standalone: true,
  selector: 'app-subject-edit',
  imports: [RouterLink, ReactiveFormsModule, Editor, InputTextModule, Button],
  templateUrl: './subject-edit.html',
  styleUrl: './subject-edit.scss'
})
export class SubjectEdit implements OnInit {
  private fb = inject(FormBuilder);
  private route = inject(ActivatedRoute);
  private router = inject(Router);
  private subjectService = inject(SubjectService);

  id!: number;
  questions: Question[] = [];

  form = this.fb.nonNullable.group({
    name: ['', [Validators.required, Validators.minLength(2)]],
    description: ['']
  });

  ngOnInit() {
    this.id = Number(this.route.snapshot.paramMap.get('id'));
    this.subjectService.retrieve(this.id).subscribe((s: Subject) => {
      this.form.patchValue({ name: s.name, description: s.description || '' });
      this.questions = s.questions || [];
    });
  }

  save() {
    if (this.form.invalid) { this.form.markAllAsTouched(); return; }
    this.subjectService.update(this.id, this.form.value).subscribe({
      next: () => this.router.navigate(['/subject/list'])
    });
  }

 goEdit(id: number) {
    this.router.navigate(['/question', id, 'edit']);
  }

  goDelete(id: number) {
    this.router.navigate(['/question', id, 'delete']);
  }
}
