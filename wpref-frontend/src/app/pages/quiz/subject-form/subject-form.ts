import {Component, EventEmitter, inject, Input, OnInit, Output, signal} from '@angular/core';
import {CommonModule} from '@angular/common';
import {FormBuilder, FormGroup, ReactiveFormsModule} from '@angular/forms';


import {MultiSelectModule} from 'primeng/multiselect';
import {InputNumberModule} from 'primeng/inputnumber';
import {CheckboxModule} from 'primeng/checkbox';
import {ButtonModule} from 'primeng/button';
import {CardModule} from 'primeng/card';

import {Subject, SubjectService} from '../../../services/subject/subject';
import {QuizSubjectCreatePayload} from '../../../services/quiz/quiz';

@Component({
  standalone: true,
  selector: 'app-quiz-subject-form',
  templateUrl: './subject-form.html',
  styleUrl: './subject-form.scss',
  imports: [CommonModule, ReactiveFormsModule, MultiSelectModule, InputNumberModule, CheckboxModule, ButtonModule, CardModule],
})
export class QuizSubjectForm implements OnInit {
  loading = signal(false);
  error = signal<string | null>(null);

  @Input() saving = false;
  @Input() success: string | null = null;

  @Output() generate = new EventEmitter<QuizSubjectCreatePayload>();
  @Output() subjectsChange = new EventEmitter<number[]>();
  subjects = signal<Subject[]>([]);
  private subjectService = inject(SubjectService);
  private fb = inject(FormBuilder);
  // Formulaire principal
  form: FormGroup = this.fb.group({
    subject_ids: [[] as number[]],
    max_questions: [10],
    with_duration: [true],
    duration: [10],
  });

  private _maxQuestions: number | null = null;

  get maxQuestions(): number | null {
    return this._maxQuestions;
  }

  @Input() set maxQuestions(value: number | null) {
    this._maxQuestions = value;
    if (value != null) {
      this.applyMaxQuestions(value);
    }
  }

  get subjectOptions(): { name: string; code: number }[] {
    return this.subjects().map((s) => ({
      name: s.name,
      code: s.id,
    }));
  }

  submitForm(): void {
    this.onSubmit();
  }

  ngOnInit(): void {
    this.loadSubjects();
  }

  onSubmit(): void {
    this.error.set(null);
    if (this.form.invalid) {
      this.form.markAllAsTouched();
      return;
    }
    const raw = this.form.value as QuizSubjectCreatePayload;
    this.generate.emit(raw);
  }

  onChangeSubjects(): void {
    const selectedIds = this.form.get('subject_ids')?.value as number[];
    this.subjectsChange.emit(selectedIds);
  }

  private applyMaxQuestions(maxQuestions: number): void {
    const ctrl = this.form.get('n_questions');
    const current = ctrl?.value ?? 0;
    if (current > maxQuestions) {
      ctrl?.setValue(maxQuestions);
    }
  }

  private loadSubjects(): void {
    this.loading.set(true);
    this.subjectService.list().subscribe({
      next: (subs: Subject[]) => {
        this.subjects.set(subs);
        this.loading.set(false);
      },
      error: (err) => {
        console.error('Erreur chargement sujets', err);
        this.loading.set(false);
        this.error.set("Erreur lors du chargement des sujets.");
      },
    });
  }
}
