import {Component, inject, OnInit, signal} from '@angular/core';

import {FormArray, FormBuilder, FormGroup, ReactiveFormsModule, Validators,} from '@angular/forms';
import {Router, RouterLink} from '@angular/router';
import {QuestionService} from '../../../services/question/question';
import {Subject, SubjectService} from '../../../services/subject/subject';

import {Editor} from 'primeng/editor';
import {CheckboxModule} from 'primeng/checkbox';
import {InputTextModule} from 'primeng/inputtext';
import {InputNumberModule} from 'primeng/inputnumber';
import {ButtonModule} from 'primeng/button';
import {MultiSelectModule} from 'primeng/multiselect';
import {SelectItem} from 'primeng/api';
import {PanelModule} from 'primeng/panel';

// Interfaces alignées sur ton serializer DRF
export interface Question {
  id: number;
  title: string;
  description: string;
  explanation: string;
  allow_multiple_correct: boolean;
  is_mode_practice: boolean;
  is_mode_exam: boolean;
  subjects: Subject[];
  media: QuestionMedia[];
  answer_options: AnswerOption[];
  created_at: string;
}

export interface QuestionMedia {
  id?: number;
  // ✅ on aligne avec tes kindOptions: image, video, audio, external
  kind: 'image' | 'video' | 'audio' | 'external';
  file?: string | null;
  external_url?: string | null;
  caption: string;
  sort_order: number;
}

export interface AnswerOption {
  id?: number;
  content: string;
  is_correct: boolean;
  sort_order: number;
}

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

    media: this.fb.group({
      kind: ['image'],
      file: [null],
      external_url: [''],
      caption: [''],
    }),
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

  /*get kindOptions(): MultiSelectOption[] {
    return [
      { value: 'image', label: 'Image' },
      { value: 'video', label: 'Vidéo' },
      { value: 'audio', label: 'Audio' },
      { value: 'external', label: 'Lien externe' },
    ];
  }*/

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

  onFileSelected(event: any): void {
    const file = event.target.files[0];
    if (file) {
      this.form.get('media.file')?.setValue(file);
    }
  }

  // ------------- Fichier media -------------

  save(): void {
    this.error.set(null);
    this.success.set(null);

    if (this.form.invalid) {
      this.form.markAllAsTouched();
      return;
    }

    this.saving.set(true);

    const raw = this.form.value as any;

    // subject_ids venant du multi-select seront des strings → on force en nombres
    const subjectIds = (raw.subject_ids || []).map((id: any) =>
      Number(id),
    ) as number[];

    const media = raw.media || {};

    const payload = {
      title: raw.title,
      description: raw.description,
      explanation: raw.explanation,
      allow_multiple_correct: raw.allow_multiple_correct,
      is_mode_practice: raw.is_mode_practice,
      is_mode_exam: raw.is_mode_exam,
      subject_ids: subjectIds,
      answer_options: raw.answer_options,
      kind: media['kind'],
      caption: media['caption'] ?? '',
      external_url: media['external_url'] ?? '',
      file: media['file'] ?? '',
    };

    this.questionService.create(payload).subscribe({
      next: () => {
        this.saving.set(false);
        this.success.set('Question créée avec succès.');
        this.router.navigate(['/questions']);
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
