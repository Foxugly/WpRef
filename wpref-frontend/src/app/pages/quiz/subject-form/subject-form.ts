import {Component, computed, EventEmitter, inject, Input, OnInit, Output, signal} from '@angular/core';
import {CommonModule} from '@angular/common';
import {FormBuilder, FormGroup, ReactiveFormsModule} from '@angular/forms';


import {MultiSelectModule} from 'primeng/multiselect';
import {InputNumberModule} from 'primeng/inputnumber';
import {CheckboxModule} from 'primeng/checkbox';
import {ButtonModule} from 'primeng/button';
import {CardModule} from 'primeng/card';

import {SubjectService} from '../../../services/subject/subject';
import {QuizSubjectCreatePayload} from '../../../services/quiz/quiz';
import {SubjectReadDto} from '../../../api/generated';
import {UserService} from '../../../services/user/user';
import {selectTranslation} from '../../../shared/i18n/select-translation';

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
  subjects = signal<SubjectReadDto[]>([]);
  private subjectService = inject(SubjectService);
  private userService: UserService = inject(UserService);
  currentLang = computed(() => this.userService.currentLang);
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
    const lang = this.currentLang(); // ou this.currentLang si ce n’est pas un signal

    return this.subjects().map((s: SubjectReadDto) => {
      const t = selectTranslation<{ name: string }>(
        s.translations as Record<string, { name: string }>,
        lang,
      );

      return {
        name: t?.name ?? '',
        code: s.id,
      };
    });
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
      next: (subs: SubjectReadDto[]) => {
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
