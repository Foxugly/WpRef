import {Component, inject, OnInit, signal} from '@angular/core';

import {FormArray, FormBuilder, FormGroup, ReactiveFormsModule, Validators,} from '@angular/forms';
import {Router, RouterLink} from '@angular/router';
import {QuestionService, AnswerOption, QuestionCreatePayload} from '../../../services/question/question';
import {Subject, SubjectService} from '../../../services/subject/subject';

import {Editor} from 'primeng/editor';
import {CheckboxModule} from 'primeng/checkbox';
import {InputTextModule} from 'primeng/inputtext';
import {InputNumberModule} from 'primeng/inputnumber';
import {ButtonModule} from 'primeng/button';
import {MultiSelectModule} from 'primeng/multiselect';
import {PanelModule} from 'primeng/panel';
import {MediaSelectorComponent, MediaSelectorValue} from '../../../components/media-selector/media-selector';

@Component({
  standalone: true,
  selector: 'app-question-create',
  templateUrl: './question-create.html',
  styleUrl: './question-create.scss',
  imports: [
    RouterLink,
    ReactiveFormsModule,
    Editor,
    CheckboxModule,
    InputTextModule,
    InputNumberModule,
    ButtonModule,
    MultiSelectModule,
    PanelModule,
    MediaSelectorComponent,

  ],
})
export class QuestionCreate implements OnInit {
  // États
  loading = signal(false);
  saving = signal(false);
  error = signal<string | null>(null);
  success = signal<string | null>(null);
  subjects = signal<Subject[]>([]);
  // Injections
  private fb = inject(FormBuilder);
  // Formulaire principal
  form: FormGroup = this.fb.group({
    title: ['', Validators.required],
    description: [''],
    explanation: [''],
    allow_multiple_correct: [false],
    is_mode_practice: [true],
    is_mode_exam: [false],
    // on envoie subject_ids au backend (write_only dans ton serializer)
    subject_ids: [[] as number[]],
    answer_options: this.fb.array([]),
    media: [[] as MediaSelectorValue[]],
  });
  private router = inject(Router);
  private questionService = inject(QuestionService);
  private subjectService = inject(SubjectService);

  // ------------- Getters pratiques -------------

  get subjectOptions(): { name: string; code: number }[] {
    return this.subjects().map((s) => ({
      name: s.name,
      code: s.id,
    }));
  }


  get answerOptions(): FormArray {
    return this.form.get('answer_options') as FormArray;
  }

  // ------------- Lifecycle -------------

  ngOnInit(): void {
    this.loadSubjects();

    // on ajoute au moins 2 réponses par défaut
    if (this.answerOptions.length === 0) {
      this.addOption();
      this.addOption();
    }
  }

  // ------------- Data loading -------------

  addOption(): void {
    const index = this.answerOptions.length;
    this.answerOptions.push(
      this.fb.group({
        content: ['', Validators.required],
        is_correct: [false],
        sort_order: [index + 1], // 1-based
      }),
    );
  }

  // ------------- Gestion des réponses -------------

  removeOption(index: number): void {
    if (this.answerOptions.length <= 2) {
      // ton clean() backend impose min 2 réponses → on protège un peu côté front
      return;
    }
    this.answerOptions.removeAt(index);
    // re-numérotation des sort_order
    this.answerOptions.controls.forEach((ctrl, i) =>
      ctrl.get('sort_order')?.setValue(i + 1),
    );
  }

  // Si tu veux un bouton "Cette réponse est la seule correcte"
  setOnlyCorrect(index: number): void {
    const allowMultiple = this.form.get('allow_multiple_correct')?.value;
    if (!allowMultiple) {
      this.answerOptions.controls.forEach((ctrl, i) => {
        ctrl.get('is_correct')?.setValue(i === index);
      });
    } else {
      // si plusieurs autorisées, on toggle simplement la case
      const current = this.answerOptions.at(index).get('is_correct')?.value;
      this.answerOptions.at(index).get('is_correct')?.setValue(!current);
    }
  }

  save(): void {
  this.error.set(null);
  this.success.set(null);

  if (this.form.invalid) {
    this.form.markAllAsTouched();
    return;
  }

  this.saving.set(true);

  const raw = this.form.value as any;

  // subject_ids
  const subjectIds: number[] = Array.isArray(raw.subject_ids)
    ? raw.subject_ids
        .filter((id: any) => id !== null && id !== undefined && id !== '')
        .map((id: any) => Number(id))
        .filter((id: number) => Number.isFinite(id))
    : [];

  // réponses
  const answerOptions: AnswerOption[] = raw.answer_options ?? [];

  // médias depuis le media-selector
  const mediaSelectorItems: MediaSelectorValue[] = Array.isArray(raw.media)
    ? raw.media
    : [];

  const media: MediaSelectorValue[] = mediaSelectorItems.map((m, idx) => {
    const sortOrder = m.sort_order ?? idx + 1;

    const externalUrl =
      m.kind === 'external'
        ? (m.external_url || (typeof m.file === 'string' ? m.file : null))
        : null;

    return {
      kind: m.kind,
      sort_order: sortOrder,
      file: null,              // on ne gère pas encore l’upload binaire
      external_url: externalUrl,
    };
  });

  const payload: QuestionCreatePayload = {
    title: raw.title,
    description: raw.description,
    explanation: raw.explanation,
    allow_multiple_correct: raw.allow_multiple_correct,
    is_mode_practice: raw.is_mode_practice,
    is_mode_exam: raw.is_mode_exam,
    subject_ids: subjectIds,
    answer_options: answerOptions,
    media,
  };

  this.questionService.create(payload).subscribe({
    next: () => {
      this.saving.set(false);
      this.success.set('Question créée avec succès.');
      this.router.navigate(['/question/list']);
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
  });
}

  // ------------- Submit -------------

  private loadSubjects(): void {
    this.subjectService.list().subscribe({
      next: (subs: Subject[]) => this.subjects.set(subs),
      error: (err) => {
        console.error('Erreur chargement sujets', err);
      },
    });
  }
}
