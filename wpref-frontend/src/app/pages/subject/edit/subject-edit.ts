import {Component, inject, OnInit} from '@angular/core';

import {FormBuilder, ReactiveFormsModule, Validators} from '@angular/forms';
import {ActivatedRoute} from '@angular/router';
import {Subject, SubjectService} from '../../../services/subject/subject';
import {Question, QuestionService} from '../../../services/question/question';
import {Editor} from 'primeng/editor';
import {InputTextModule} from 'primeng/inputtext';
import {Button} from 'primeng/button';


@Component({
  standalone: true,
  selector: 'app-subject-edit',
  imports: [ReactiveFormsModule, Editor, InputTextModule, Button],
  templateUrl: './subject-edit.html',
  styleUrl: './subject-edit.scss'
})
export class SubjectEdit implements OnInit {
  id!: number;
  questions: Question[] = [];
  private fb = inject(FormBuilder);
  form = this.fb.nonNullable.group({
    name: ['', [Validators.required, Validators.minLength(2)]],
    description: ['']
  });
  private route = inject(ActivatedRoute);
  private subjectService = inject(SubjectService);
  private questionService = inject(QuestionService);

  ngOnInit() {
    this.id = Number(this.route.snapshot.paramMap.get('id'));
    this.subjectService.retrieve(this.id).subscribe((s: Subject) => {
      this.form.patchValue({name: s.name, description: s.description || ''});
      this.questions = s.questions || [];
    });
  }

  save() {
    if (this.form.invalid) {
      this.form.markAllAsTouched();
      return;
    }
    this.subjectService.update(this.id, this.form.value).subscribe({
      next: () => this.goList()
    });
  }

  goQuestionNew(): void {
    this.questionService.goNew();
  }

  goQuestionEdit(id: number) {
    this.questionService.goEdit(id);
  }

  goQuestionDelete(id: number) {
    this.questionService.goDelete(id);
  }

  goBack(): void {
    this.subjectService.goBack();
  }

  goList(): void {
    this.subjectService.goList();
  }
}
