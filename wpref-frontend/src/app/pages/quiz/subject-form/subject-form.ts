import {CommonModule} from '@angular/common';
import {Component, computed, DestroyRef, EventEmitter, inject, Input, OnInit, Output, signal} from '@angular/core';
import {takeUntilDestroyed} from '@angular/core/rxjs-interop';
import {NonNullableFormBuilder, ReactiveFormsModule} from '@angular/forms';
import {finalize} from 'rxjs';
import {ButtonModule} from 'primeng/button';
import {CardModule} from 'primeng/card';
import {InputNumberModule} from 'primeng/inputnumber';
import {InputTextModule} from 'primeng/inputtext';
import {MessageModule} from 'primeng/message';
import {MultiSelectModule} from 'primeng/multiselect';
import {SelectModule} from 'primeng/select';
import {ToggleSwitchModule} from 'primeng/toggleswitch';
import {DomainReadDto, SubjectReadDto} from '../../../api/generated';
import {DomainService, DomainTranslations} from '../../../services/domain/domain';
import {QuizSubjectCreatePayload} from '../../../services/quiz/quiz';
import {SubjectService} from '../../../services/subject/subject';
import {UserService} from '../../../services/user/user';
import {logApiError, userFacingApiMessage} from '../../../shared/api/api-errors';
import {selectTranslation} from '../../../shared/i18n/select-translation';

type QuizSubjectFormModel = {
  title: string;
  domain_id: number;
  subject_ids: number[];
  max_questions: number;
  with_duration: boolean;
  duration: number;
};

@Component({
  standalone: true,
  selector: 'app-quiz-subject-form',
  templateUrl: './subject-form.html',
  styleUrl: './subject-form.scss',
  imports: [
    CommonModule,
    ReactiveFormsModule,
    MultiSelectModule,
    SelectModule,
    InputNumberModule,
    InputTextModule,
    ToggleSwitchModule,
    ButtonModule,
    CardModule,
    MessageModule,
  ],
})
export class QuizSubjectForm implements OnInit {
  loading = signal(false);
  error = signal<string | null>(null);
  domains = signal<DomainReadDto[]>([]);
  subjects = signal<SubjectReadDto[]>([]);

  @Input() saving = false;
  @Input() success: string | null = null;
  @Output() generate = new EventEmitter<QuizSubjectCreatePayload>();
  @Output() subjectsChange = new EventEmitter<number[]>();

  private readonly domainService = inject(DomainService);
  private readonly subjectService = inject(SubjectService);
  private readonly userService = inject(UserService);
  private readonly fb = inject(NonNullableFormBuilder);
  private readonly destroyRef = inject(DestroyRef);
  private defaultDomainId = 0;

  currentLang = computed(() => this.userService.currentLang);
  readonly availableQuestionCount = signal(0);
  readonly questionCountLimit = computed(() => this.availableQuestionCount());
  readonly questionCountMin = computed(() => (this.availableQuestionCount() > 0 ? 1 : 0));
  form = this.fb.group({
    title: this.fb.control(''),
    domain_id: this.fb.control(0),
    subject_ids: this.fb.control<number[]>({value: [], disabled: true}),
    max_questions: this.fb.control(0),
    with_duration: this.fb.control(true),
    duration: this.fb.control(10),
  });

  private _maxQuestions: number | null = null;

  get maxQuestions(): number | null {
    return this._maxQuestions;
  }

  @Input() set maxQuestions(value: number | null) {
    this._maxQuestions = value;
    this.applyMaxQuestions(value);
  }

  get domainOptions(): {name: string; code: number}[] {
    const lang = this.currentLang();

    return this.domains().map((domain) => ({
      name: this.getDomainLabel(domain, lang),
      code: domain.id,
    }));
  }

  get subjectOptions(): {name: string; code: number}[] {
    const lang = this.currentLang();
    const domainId = this.form.controls.domain_id.getRawValue();

    return this.subjects()
      .filter((subject) => subject.domain === domainId)
      .map((subject: SubjectReadDto) => {
      const translation = selectTranslation<{name: string}>(
        subject.translations as Record<string, {name: string}>,
        lang,
      );

      return {
        name: translation?.name ?? '',
        code: subject.id,
      };
    });
  }

  ngOnInit(): void {
    this.syncSubjectControlState(this.form.controls.domain_id.getRawValue());
    this.form.controls.domain_id.valueChanges
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe((domainId) => {
        this.syncSubjectControlState(domainId);
        this.form.controls.subject_ids.setValue([], {emitEvent: false});
        this.applyMaxQuestions(0);
        this.subjectsChange.emit([]);
      });

    this.form.controls.with_duration.valueChanges
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe((enabled) => {
        if (enabled) {
          this.form.controls.duration.enable({emitEvent: false});
          if (this.form.controls.duration.getRawValue() < 1) {
            this.form.controls.duration.setValue(10, {emitEvent: false});
          }
          return;
        }

        this.form.controls.duration.disable({emitEvent: false});
      });

    this.loadData();
  }

  prepareForOpen(): void {
    const defaultDomainId = this.defaultDomainId;
    this.error.set(null);
    this.form.reset({
      title: this.buildDefaultTitle(),
      domain_id: defaultDomainId,
      subject_ids: [],
      max_questions: 0,
      with_duration: true,
      duration: 10,
    });
    this.syncSubjectControlState(defaultDomainId);
    this.form.controls.duration.enable({emitEvent: false});
    this.applyMaxQuestions(0);
  }

  submitForm(): void {
    this.onSubmit();
  }

  onSubmit(): void {
    this.error.set(null);
    if (this.form.invalid) {
      this.form.markAllAsTouched();
      return;
    }

    const rawValue = this.form.getRawValue() as QuizSubjectFormModel;
    if (!rawValue.title.trim()) {
      this.error.set('Le titre du quiz est requis.');
      return;
    }

    if (!rawValue.domain_id) {
      this.error.set('Le domaine est requis.');
      return;
    }

    if (!rawValue.subject_ids.length) {
      this.error.set('Selectionne au moins un sujet.');
      return;
    }

    if (rawValue.max_questions < 1) {
      this.error.set('Le nombre de questions doit etre superieur a zero.');
      return;
    }

    this.generate.emit({
      title: rawValue.title.trim(),
      subject_ids: rawValue.subject_ids,
      max_questions: rawValue.max_questions,
      with_duration: rawValue.with_duration,
      duration: rawValue.with_duration ? rawValue.duration : null,
    });
  }

  onChangeSubjects(): void {
    this.error.set(null);
    this.subjectsChange.emit(this.form.controls.subject_ids.getRawValue());
  }

  private applyMaxQuestions(maxQuestions: number | null): void {
    const normalizedMax = Math.max(maxQuestions ?? 0, 0);
    this.availableQuestionCount.set(normalizedMax);

    if (normalizedMax > 0) {
      this.form.controls.max_questions.enable({emitEvent: false});
      this.form.controls.max_questions.setValidators([]);
      this.form.controls.max_questions.updateValueAndValidity({emitEvent: false});
      const current = this.form.controls.max_questions.getRawValue();
      const nextValue = current > 0 ? Math.min(current, normalizedMax) : normalizedMax;
      this.form.controls.max_questions.setValue(nextValue, {emitEvent: false});
      return;
    }

    this.form.controls.max_questions.setValidators([]);
    this.form.controls.max_questions.updateValueAndValidity({emitEvent: false});
    this.form.controls.max_questions.setValue(0, {emitEvent: false});
    this.form.controls.max_questions.disable({emitEvent: false});
  }

  private loadData(): void {
    this.loading.set(true);
    this.error.set(null);

    this.domainService
      .list()
      .pipe(
        takeUntilDestroyed(this.destroyRef),
      )
      .subscribe({
        next: (domains: DomainReadDto[]) => {
          this.domains.set(domains);

          const preferredDomain = this.userService.currentUser()?.current_domain;
          const defaultDomainId =
            domains.find((domain) => domain.id === preferredDomain)?.id ??
            (domains.length === 1 ? domains[0].id : 0);

          this.defaultDomainId = defaultDomainId;
          if (defaultDomainId) {
            this.form.controls.domain_id.setValue(defaultDomainId);
          }
          this.prepareForOpen();
        },
        error: (err: unknown) => {
          logApiError('quiz.subject-form.load-domains', err);
          this.error.set(userFacingApiMessage(err, 'Erreur lors du chargement des domaines.'));
        },
      });

    this.subjectService
      .list()
      .pipe(
        takeUntilDestroyed(this.destroyRef),
        finalize(() => this.loading.set(false)),
      )
      .subscribe({
        next: (subjects: SubjectReadDto[]) => {
          this.subjects.set(subjects);
        },
        error: (err: unknown) => {
          logApiError('quiz.subject-form.load-subjects', err);
          this.error.set(userFacingApiMessage(err, 'Erreur lors du chargement des sujets.'));
        },
      });
  }

  private getDomainLabel(domain: DomainReadDto, lang: string): string {
    const translations = domain.translations as DomainTranslations | undefined;
    return translations?.[lang]?.name?.trim() || `Domain #${domain.id}`;
  }

  private syncSubjectControlState(domainId: number): void {
    if (domainId) {
      this.form.controls.subject_ids.enable({emitEvent: false});
      return;
    }

    this.form.controls.subject_ids.disable({emitEvent: false});
  }

  private buildDefaultTitle(): string {
    const stamp = this.formatTimestamp(new Date());
    const user = this.userService.currentUser();
    const userLabel = [user?.first_name?.trim(), user?.last_name?.trim()]
      .filter((value): value is string => !!value)
      .join('-') || user?.username || 'user';

    return `${stamp}-quiz-${userLabel}`;
  }

  private formatTimestamp(date: Date): string {
    const parts = [
      date.getFullYear().toString(),
      (date.getMonth() + 1).toString().padStart(2, '0'),
      date.getDate().toString().padStart(2, '0'),
      date.getHours().toString().padStart(2, '0'),
      date.getMinutes().toString().padStart(2, '0'),
      date.getSeconds().toString().padStart(2, '0'),
    ];

    return parts.join('');
  }
}
