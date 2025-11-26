import {Component, inject, OnInit, signal} from '@angular/core';
import {CommonModule} from '@angular/common';
//import { RouterLink } from '@angular/router';
import {CKEditorModule} from '@ckeditor/ckeditor5-angular';
import ClassicEditor from '@ckeditor/ckeditor5-build-classic';
import {MultiSelectComponent, MultiSelectOption} from '../../../components/multi-select/multi-select';
import {FormArray, FormBuilder, FormGroup, ReactiveFormsModule, Validators,} from '@angular/forms';
import {ActivatedRoute, Router} from '@angular/router';

import {QuestionService} from '../../../services/question/question';
import {Subject, SubjectService} from '../../../services/subject/subject';

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
  kind: 'image' | 'video';
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
  selector: 'app-question-edit',
  templateUrl: './question-create.html',
  styleUrl: './question-create.scss',
  imports: [CommonModule, ReactiveFormsModule, CKEditorModule, MultiSelectComponent],
})
export class QuestionCreate implements OnInit {
  public Editor: any = ClassicEditor;
  private fb = inject(FormBuilder);
  private route = inject(ActivatedRoute);
  private router = inject(Router);
  private questionService = inject(QuestionService);
  private subjectService = inject(SubjectService);


  questionId!: number;

  loading = signal(false);
  saving = signal(false);
  error = signal<string | null>(null);
  success = signal<string | null>(null);

  subjects = signal<Subject[]>([]);

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
    })
  });

  get subjectOptions(): MultiSelectOption[] {
    return this.subjects().map((s) => ({
      value: s.id,
      label: `${s.name} (${s.slug})`,
    }));
  }

  get kindOptions(): MultiSelectOption[] {
    return [
      {value: 'image', label: 'Image'},
      {value: 'video', label: 'Vidéo'},
      {value: 'audio', label: 'Audio'},
      {value: 'external', label: 'Lien externe'},
    ];
  }

  get answerOptions(): FormArray {
    return this.form.get('answer_options') as FormArray;
  }

  ngOnInit(): void {
    this.questionId = Number(this.route.snapshot.paramMap.get('id'));
    this.loadSubjects();
  }

  private loadSubjects(): void {
    this.subjectService.list().subscribe({
      next: (subs: Subject[]) => this.subjects.set(subs),
      error: (err) => {
        console.error('Erreur chargement sujets', err);
      },
    });
  }

  addOption(): void {
    const index = this.answerOptions.length;
    this.answerOptions.push(
      this.fb.group({
        content: ['', Validators.required],
        is_correct: [false],
        sort_order: [index+1],
      })
    );
  }

  removeOption(index: number): void {
    if (this.answerOptions.length <= 2) {
      // ton clean() backend impose min 2 réponses → on protège un peu côté front
      return;
    }
    this.answerOptions.removeAt(index);
    // re-numérotation des sort_order
    this.answerOptions.controls.forEach((ctrl, i) =>
      ctrl.get('sort_order')?.setValue(i)
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

  onSubmit(): void {
    this.error.set(null);
    this.success.set(null);

    if (this.form.invalid) {
      this.form.markAllAsTouched();
      return;
    }

    this.saving.set(true);

    const raw = this.form.value;

    // subject_ids venant du multi-select seront des strings → on force en nombres
    const subjectIds = (raw.subject_ids || []).map((id: any) =>
      Number(id)
    ) as number[];

    const media = raw.media;

    const payload = {
      title: raw.title,
      description: raw.description,
      explanation: raw.explanation,
      allow_multiple_correct: raw.allow_multiple_correct,
      is_mode_practice: raw.is_mode_practice,
      is_mode_exam: raw.is_mode_exam,
      subject_ids: subjectIds,
      answer_options: raw.answer_options,
      kind: media.kind,
      caption: media.caption ?? '',
      external_url: media.external_url ?? '',
      file: media.file ?? ''
    };

    this.questionService.create(payload).subscribe({
      next: () => {
        this.saving.set(false);
        this.success.set('Question créée avec succès.');
        // par ex. retour à la liste :
        this.router.navigate(['/questions']);
      },
      error: (err) => {
        console.error('Erreur création question', err);
        // le serializer DRF peut renvoyer message_dict → on simplifie pour l’afficher
        if (err.error && typeof err.error === 'object') {
          this.error.set(JSON.stringify(err.error));
        } else {
          this.error.set("Erreur lors de l'enregistrement de la question.");
        }
        this.saving.set(false);
      },
    });
  }
}

