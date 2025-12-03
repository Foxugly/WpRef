import {Component, inject, OnInit, signal} from '@angular/core';
import {CommonModule} from '@angular/common';
import {FormBuilder, FormGroup, ReactiveFormsModule} from '@angular/forms';

import {Subject, SubjectService} from '../../../services/subject/subject';

import {MultiSelectModule} from 'primeng/multiselect';
import {InputNumberModule} from 'primeng/inputnumber';
import {Checkbox} from 'primeng/checkbox';
import {ButtonModule} from 'primeng/button';
import {CardModule} from 'primeng/card';

export interface QuizSubjectCreatePayload {
  subject_ids: number[];
  n_question: number;
  with_timer: boolean;
  timer: number | null;
}

@Component({
  standalone: true,
  selector: 'app-home-subject',
  templateUrl: './home-subject.html',
  styleUrl: './home-subject.scss',
  imports: [CommonModule, ReactiveFormsModule, MultiSelectModule, InputNumberModule, Checkbox, ButtonModule, CardModule],
})
export class QuizSubjectHome implements OnInit {
  loading = signal(false);
  saving = signal(false);
  error = signal<string | null>(null);
  success = signal<string | null>(null);
  subjects = signal<Subject[]>([]);
  //selectedSubjectIds: number[] = [];
  private subjectService = inject(SubjectService);
  private fb = inject(FormBuilder);
  // Formulaire principal
  form: FormGroup = this.fb.group({
    subject_ids: [[] as number[]],
    n_questions: [10],
    with_timer: [true],
    timer: [10],
  });

  get subjectOptions(): { name: string; code: number }[] {
    return this.subjects().map((s) => ({
      name: s.name,
      code: s.id,
    }));
  }

  ngOnInit(): void {
    this.loadSubjects();
  }

  generate_quiz(): void {
    this.error.set(null);
    this.success.set(null);
    if (this.form.invalid) {
      this.form.markAllAsTouched();
      return;
    }
    this.saving.set(true);
    const raw = this.form.value as QuizSubjectCreatePayload;
    // TODO: appel backend /quiz/start ou autre
    /* this.questionService.create(raw).subscribe({
      next: () => {
        this.saving.set(false);
        this.success.set('Question créée avec succès.');
      },
      error: (err) => {
        console.error('Erreur création question', err);
        if (err.error && typeof err.error === 'object') {
          this.error.set(JSON.stringify(err.error));
        } else {
          this.error.set("Erreur lors de l'enregistrement de la question.");
        }
        this.saving.set(false);
      },
    });*/

    this.saving.set(false);
    this.success.set('Quiz prêt à démarrer (simulation).');
  }

  private setMaxQuestions(maxQuestions: number): void {
    // si la valeur actuelle dépasse le nouveau max, on la ramène
    const ctrl = this.form.get('n_questions');
    const span = document.getElementById('label_n_questions');
    if (span) {
      span.textContent = `(max: ${maxQuestions})`;
    }
    const current = ctrl?.value ?? 0;
    if (current > maxQuestions) {
      ctrl?.setValue(maxQuestions);
    }
  }

  onChangeSubjects():void{
    console.log("onChangeSubjects");
    const selectedIds = this.form.get('subject_ids')?.value as number[];
    console.log(selectedIds);
    // TODO APPEL /quiz/n/ avec
    this.setMaxQuestions(42);
  }

  private loadSubjects(): void {
    this.subjectService.list().subscribe({
      next: (subs: Subject[]) => this.subjects.set(subs),
      error: (err) => {
        console.error('Erreur chargement sujets', err);
      },
    });
  }
}
