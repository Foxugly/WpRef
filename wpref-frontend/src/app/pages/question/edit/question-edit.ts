import {Component, inject, OnInit, signal} from '@angular/core';
import {FormArray, FormBuilder, FormGroup, ReactiveFormsModule, Validators,} from '@angular/forms';
import {ActivatedRoute, Router, RouterLink} from '@angular/router';
import {Question, QuestionCreatePayload, QuestionService,} from '../../../services/question/question';
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
  selector: 'app-question-edit',
  templateUrl: './question-edit.html',
  styleUrl: './question-edit.scss',
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
    MediaSelectorComponent
  ],
})
export class QuestionEdit implements OnInit {
  id!: number;
  loading = signal(false);
  saving = signal(false);
  error = signal<string | null>(null);
  success = signal<string | null>(null);
  subjects = signal<Subject[]>([]);
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
  private route = inject(ActivatedRoute);
  private router = inject(Router);
  private questionService = inject(QuestionService);
  private subjectService = inject(SubjectService);

  get subjectOptions(): { name: string; code: number }[] {
    return this.subjects().map((s) => ({
      name: s.name,
      code: s.id,
    }));
  }

  get answerOptions(): FormArray {
    return this.form.get('answer_options') as FormArray;
  }

  ngOnInit(): void {
    this.id = Number(this.route.snapshot.paramMap.get('id'));
    this.loadSubjects();
    this.loadQuestion();
  }

  addOption(): void {
    const index = this.answerOptions.length;
    this.answerOptions.push(
      this.fb.group({
        content: ['', Validators.required],
        is_correct: [false],
        sort_order: [index + 1],
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

  save(): void {
    this.error.set(null);
    this.success.set(null);
    if (this.form.invalid) {
      this.form.markAllAsTouched();
      return;
    }
    this.saving.set(true);
    // Le form a la même shape que QuestionCreatePayload
    const raw = this.form.value as QuestionCreatePayload;
    this.questionService.update(this.id, raw).subscribe({
      next: () => {
        this.saving.set(false);
        this.success.set('Question mise à jour avec succès.');
        this.router.navigate(['/question/list']);
      },
      error: (err) => {
        console.error('Erreur update question', err);
        if (err.error && typeof err.error === 'object') {
          this.error.set(JSON.stringify(err.error));
        } else {
          this.error.set("Erreur lors de l'enregistrement de la question.");
        }
        this.saving.set(false);
      },
    });
  }

  goBack(): void {
    this.router.navigate(['/question/list']);
  }

  goView(id: number) {
    this.router.navigate(['/question', id, 'view']);
  }

  private loadSubjects(): void {
    this.subjectService.list().subscribe({
      next: (subs: Subject[]) => {
        this.subjects.set(subs);
      },
      error: (err) => {
        console.error('Erreur chargement sujets', err);
      },
    });
  }

  private loadQuestion(): void {
    this.loading.set(true);
    this.error.set(null);

    this.questionService.retrieve(this.id).subscribe({
      next: (q: Question) => {
        const subjectIds = q.subjects?.map((s) => s.id) ?? [];
        // réponses
        this.answerOptions.clear();
        q.answer_options.forEach((opt) => {
          this.answerOptions.push(
            this.fb.group({
              content: [opt.content, Validators.required],
              is_correct: [opt.is_correct],
              sort_order: [opt.sort_order],
            }),
          );
        });

        if (this.answerOptions.length === 0) {
          this.addOption();
          this.addOption();
        }

        // médias → MediaSelectorValue[] pour le composant
        const mediaSelectorItems: MediaSelectorValue[] = (q.media || []).map(
          (m, idx) => ({
            id: m.id,
            kind: m.kind,
            sort_order: m.sort_order ?? idx + 1,
            file: m.file ?? null,               // string (URL) côté backend
            external_url: m.external_url ?? null,
          }),
        );

        this.form.patchValue({
          title: q.title,
          description: q.description,
          explanation: q.explanation,
          allow_multiple_correct: q.allow_multiple_correct,
          is_mode_practice: q.is_mode_practice,
          is_mode_exam: q.is_mode_exam,
          subject_ids: subjectIds,
          media: mediaSelectorItems,
        });

        this.loading.set(false);
      },
      error: (err) => {
        console.error('Erreur chargement question', err);
        this.error.set("Impossible de charger la question.");
        this.loading.set(false);
      },
    });
  }
}
