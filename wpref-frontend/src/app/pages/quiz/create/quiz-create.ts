import {CommonModule} from '@angular/common';
import {Component, computed, DestroyRef, inject, OnInit, signal} from '@angular/core';
import {takeUntilDestroyed} from '@angular/core/rxjs-interop';
import {Validators, NonNullableFormBuilder, ReactiveFormsModule} from '@angular/forms';
import {ActivatedRoute} from '@angular/router';
import {firstValueFrom, forkJoin, of} from 'rxjs';
import {finalize} from 'rxjs/operators';

import {Translation} from 'primeng/api';
import {ButtonModule} from 'primeng/button';
import {CardModule} from 'primeng/card';
import {CheckboxModule} from 'primeng/checkbox';
import {PrimeNG} from 'primeng/config';
import {DatePickerModule} from 'primeng/datepicker';
import {DialogModule} from 'primeng/dialog';
import {InputNumberModule} from 'primeng/inputnumber';
import {InputTextModule} from 'primeng/inputtext';
import {SelectModule} from 'primeng/select';
import {ToggleSwitchModule} from 'primeng/toggleswitch';

import {
  DomainReadDto,
  LanguageEnumDto,
  ModeEnumDto,
  QuestionInQuizQuestionDto,
  QuestionReadDto,
  QuizTemplateDto,
  QuizTemplateWriteRequestDto,
  SubjectReadDto,
  VisibilityEnumDto,
} from '../../../api/generated';
import {QuizQuestionLibraryComponent} from '../../../components/quiz-question-library/quiz-question-library';
import {QuizTemplateCompositionComponent} from '../../../components/quiz-template-composition/quiz-template-composition';
import {QuestionPreviewDialogComponent} from '../../../components/question-preview-dialog/question-preview-dialog';
import {QuestionEditorFormComponent} from '../../../components/question-editor-form/question-editor-form';
import {DomainService, DomainTranslations} from '../../../services/domain/domain';
import {
  addQuestionAnswerOption,
  buildQuestionCreatePayload,
  createQuestionEditorForm,
  ensureQuestionTranslationControls,
  getQuestionCorrectCount,
  getQuestionTrGroup,
  isEmptyQuestionHtml,
  isQuestionEditorFormValid,
  QuestionEditorForm,
  uploadQuestionEditorMediaAssets,
} from '../../../services/question/question-editor-form';
import {QuestionService} from '../../../services/question/question';
import {QuizService} from '../../../services/quiz/quiz';
import {QuizTemplateService} from '../../../services/quiz-template/quiz-template';
import {SubjectService} from '../../../services/subject/subject';
import {LangCode, TranslateBatchItem, TranslationService} from '../../../services/translation/translation';
import {UserService} from '../../../services/user/user';
import {selectTranslation} from '../../../shared/i18n/select-translation';
import {QuestionLibraryCard, SelectedQuestionCard, SelectedQuestionRef, SelectedQuizQuestion} from './quiz-template-builder.models';
import {getQuizCreateUiText} from './quiz-create.i18n';

@Component({
  standalone: true,
  selector: 'app-quiz-create',
  imports: [
    CommonModule,
    ReactiveFormsModule,
    ButtonModule,
    CardModule,
    CheckboxModule,
    DatePickerModule,
    DialogModule,
    InputNumberModule,
    InputTextModule,
    QuizQuestionLibraryComponent,
    QuizTemplateCompositionComponent,
    QuestionPreviewDialogComponent,
    QuestionEditorFormComponent,
    SelectModule,
    ToggleSwitchModule,
  ],
  templateUrl: './quiz-create.html',
  styleUrl: './quiz-create.scss',
})
export class QuizCreate implements OnInit {
  readonly questionEmptyLanguagesMessage = "Ce domaine n'a pas de langues actives configurees.";
  readonly questionPracticeTooltip = 'la question sera disponible dans le domaine choisi pour ce quiz.';

  loading = signal(true);
  questionsLoading = signal(false);
  saving = signal(false);
  error = signal<string | null>(null);
  submitError = signal<string | null>(null);

  questionDialogVisible = signal(false);
  questionSaving = signal(false);
  questionTranslating = signal(false);
  questionSubmitError = signal<string | null>(null);
  questionDialogLangs = signal<LangCode[]>([]);
  questionDialogActiveLang = signal<LangCode | null>(null);

  domains = signal<DomainReadDto[]>([]);
  subjects = signal<SubjectReadDto[]>([]);
  questions = signal<QuestionReadDto[]>([]);
  selectedQuestions = signal<SelectedQuizQuestion[]>([]);
  search = signal('');
  currentLang = signal<LanguageEnumDto>(LanguageEnumDto.Fr);
  selectedDomainId = signal(0);
  quizFormValid = signal(false);
  editingTemplateId = signal<number | null>(null);
  originalQuizQuestionIds = signal<number[]>([]);
  previewQuestionId = signal<number | null>(null);

  readonly isAdmin = inject(UserService).isAdmin;
  readonly isEditMode = computed(() => this.editingTemplateId() !== null);

  readonly quizForm = inject(NonNullableFormBuilder).group({
    domain: [0, [Validators.required, Validators.min(1)]],
    title: ['', [Validators.required, Validators.minLength(3), Validators.maxLength(200)]],
    description: [''],
    mode: [ModeEnumDto.Practice, Validators.required],
    active: [true],
    permanent: [true],
    started_at: [null as Date | null],
    ended_at: [null as Date | null],
    with_duration: [false],
    duration: [10, [Validators.required, Validators.min(1)]],
    detail_visibility: [VisibilityEnumDto.Immediate, Validators.required],
    detail_available_at: [null as Date | null],
  });

  questionForm: QuestionEditorForm = createQuestionEditorForm(inject(NonNullableFormBuilder), {
    domainDisabled: true,
  });

  private readonly fb = inject(NonNullableFormBuilder);
  private readonly destroyRef = inject(DestroyRef);
  private readonly route = inject(ActivatedRoute);
  private readonly primeng = inject(PrimeNG);
  private readonly domainService = inject(DomainService);
  private readonly subjectService = inject(SubjectService);
  private readonly questionService = inject(QuestionService);
  private readonly quizTemplateService = inject(QuizTemplateService);
  private readonly quizService = inject(QuizService);
  private readonly translationService = inject(TranslationService);
  private readonly userService = inject(UserService);
  private preserveSelectionOnNextDomainChange = false;

  readonly selectedDomain = computed(() => {
    const domainId = this.selectedDomainId();
    return this.domains().find((domain) => domain.id === domainId) ?? null;
  });

  readonly selectedDomainLabel = computed(() => {
    const domain = this.selectedDomain();
    return domain ? this.getDomainLabel(domain) : null;
  });

  readonly uiText = computed(() => this.getUiText(this.currentLang()));
  readonly datePickerFormat = computed(() => this.uiText().dateFormat);
  readonly pageTitle = computed(() => this.isEditMode() ? this.uiText().editTitle : this.uiText().createTitle);
  readonly pageSubtitle = computed(() => this.isEditMode() ? this.uiText().editSubtitle : this.uiText().createSubtitle);
  readonly submitLabel = computed(() => this.isEditMode() ? this.uiText().saveTemplate : this.uiText().createTemplate);
  readonly modeOptions = computed(() => [
    {label: this.uiText().practiceMode, value: ModeEnumDto.Practice},
    {label: this.uiText().examMode, value: ModeEnumDto.Exam},
  ]);
  readonly visibilityOptions = computed(() => [
    {label: this.uiText().visibilityImmediate, value: VisibilityEnumDto.Immediate},
    {label: this.uiText().visibilityScheduled, value: VisibilityEnumDto.Scheduled},
    {label: this.uiText().visibilityNever, value: VisibilityEnumDto.Never},
  ]);

  readonly domainOptions = computed(() => this.domains().map((domain) => ({
    label: this.domainLabel(domain),
    value: domain.id,
  })));

  readonly subjectOptions = computed<Array<{name: string; code: number}>>(() => {
    const domainId = this.selectedDomainId();
    const lang = this.currentLang();

    return this.subjects()
      .filter((subject) => subject.domain === domainId)
      .map((subject) => ({
        code: subject.id,
        name: this.getSubjectLabel(subject, lang),
      }))
      .sort((left, right) => left.name.localeCompare(right.name));
  });

  readonly availableQuestions = computed(() => {
    const selectedIds = new Set(this.selectedQuestions().map((entry) => entry.question.id));
    const term = this.search().trim().toLowerCase();

    return this.questions()
      .filter((question) => !selectedIds.has(question.id))
      .filter((question) => {
        if (!term) {
          return true;
        }

        const haystack = [
          this.getQuestionTitle(question),
          ...question.subjects.map((subject) => this.getSubjectLabel(subject, this.currentLang())),
        ]
          .join(' ')
          .toLowerCase();

        return haystack.includes(term);
      });
  });
  readonly availableQuestionCards = computed<QuestionLibraryCard[]>(() =>
    this.availableQuestions().map((question) => ({
      question,
      title: this.getQuestionTitle(question),
      subjectsLabel: this.getQuestionSubjects(question),
    })),
  );
  readonly selectedQuestionCards = computed<SelectedQuestionCard[]>(() =>
    this.selectedQuestions().map((item) => ({
      item,
      questionId: item.question.id,
      title: this.getQuestionTitle(item.question),
      subjectsLabel: this.getQuestionSubjects(item.question),
    })),
  );

  readonly canSave = computed(() => {
    return this.isAdmin() &&
      !this.saving() &&
      !!this.selectedDomainId() &&
      this.quizFormValid() &&
      this.selectedQuestions().length > 0;
  });

  ngOnInit(): void {
    const rawTemplateId = this.route.snapshot.paramMap.get('templateId');
    const templateId = rawTemplateId ? Number(rawTemplateId) : null;
    if (rawTemplateId && !Number.isFinite(templateId)) {
      this.error.set('Identifiant de template invalide.');
      this.loading.set(false);
      return;
    }
    this.editingTemplateId.set(templateId);

    this.userService.lang$
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe((lang) => {
        this.currentLang.set(lang as LanguageEnumDto);
        this.applyDatePickerLocale(lang as LanguageEnumDto);
      });

    this.quizForm.controls.permanent.valueChanges
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe((isPermanent) => {
        if (isPermanent) {
          this.quizForm.controls.started_at.disable({emitEvent: false});
          this.quizForm.controls.ended_at.disable({emitEvent: false});
          this.quizForm.controls.started_at.setValue(null, {emitEvent: false});
          this.quizForm.controls.ended_at.setValue(null, {emitEvent: false});
        } else {
          this.quizForm.controls.started_at.enable({emitEvent: false});
          this.quizForm.controls.ended_at.enable({emitEvent: false});
        }
      });

    this.quizForm.controls.detail_visibility.valueChanges
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe((visibility) => {
        if (visibility === VisibilityEnumDto.Scheduled) {
          this.quizForm.controls.detail_available_at.enable({emitEvent: false});
        } else {
          this.quizForm.controls.detail_available_at.disable({emitEvent: false});
          this.quizForm.controls.detail_available_at.setValue(null, {emitEvent: false});
        }
      });

    this.quizForm.controls.with_duration.valueChanges
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe((enabled) => {
        if (enabled) {
          this.quizForm.controls.duration.enable({emitEvent: false});
        } else {
          this.quizForm.controls.duration.disable({emitEvent: false});
          this.quizForm.controls.duration.setValue(10, {emitEvent: false});
        }
      });
    this.quizForm.controls.started_at.disable({emitEvent: false});
    this.quizForm.controls.ended_at.disable({emitEvent: false});
    this.quizForm.controls.detail_available_at.disable({emitEvent: false});
    this.quizForm.controls.duration.disable({emitEvent: false});

    this.quizForm.controls.domain.valueChanges
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe((value) => {
        const domainId = Number(value ?? 0);
        this.selectedDomainId.set(domainId);
        this.onDomainSelected(domainId);
      });

    this.quizForm.statusChanges
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe(() => this.quizFormValid.set(this.quizForm.valid));

    this.selectedDomainId.set(Number(this.quizForm.controls.domain.value ?? 0));
    this.quizFormValid.set(this.quizForm.valid);

    this.loading.set(true);
    forkJoin({
      domains: this.domainService.list(),
      subjects: this.subjectService.list(),
      template: templateId ? this.quizTemplateService.retrieve(templateId) : of(null),
    })
      .pipe(
        takeUntilDestroyed(this.destroyRef),
        finalize(() => this.loading.set(false)),
      )
      .subscribe({
        next: ({domains, subjects, template}) => {
          this.domains.set(domains ?? []);
          this.subjects.set(subjects ?? []);

          if (template) {
            this.patchTemplate(template);
            return;
          }

          const preferredDomain = this.userService.currentUser()?.current_domain;
          const defaultDomainId =
            domains.find((domain) => domain.id === preferredDomain)?.id ??
            (domains.length === 1 ? domains[0].id : 0);

          if (defaultDomainId) {
            this.quizForm.controls.domain.setValue(defaultDomainId);
          }
        },
        error: (err) => {
          console.error(err);
          this.error.set('Impossible de charger les donnees du template.');
        },
      });
  }

  goBack(): void {
    this.quizService.goList();
  }

  onSearchInput(event: Event): void {
    const target = event.target as HTMLInputElement | null;
    this.search.set(target?.value ?? '');
  }

  addExistingQuestion(question: QuestionReadDto): void {
    this.selectedQuestions.update((items) => [
      ...items,
      {
        question,
        weight: 1,
        sort_order: items.length + 1,
      },
    ]);
    this.submitError.set(null);
  }

  removeSelectedQuestion(index: number): void {
    this.selectedQuestions.update((items) => {
      const next = items.filter((_, itemIndex) => itemIndex !== index);
      return this.renumberSelectedQuestions(next);
    });
  }

  openQuestionPreview(question: SelectedQuestionRef): void {
    this.previewQuestionId.set(question.id);
  }

  openQuestionPreviewById(questionId: number): void {
    this.previewQuestionId.set(questionId);
  }

  closeQuestionPreview(): void {
    this.previewQuestionId.set(null);
  }

  moveSelectedQuestion(index: number, direction: -1 | 1): void {
    this.selectedQuestions.update((items) => {
      const targetIndex = index + direction;
      if (targetIndex < 0 || targetIndex >= items.length) {
        return items;
      }

      const next = [...items];
      [next[index], next[targetIndex]] = [next[targetIndex], next[index]];
      return this.renumberSelectedQuestions(next);
    });
  }

  onWeightChange(index: number, event: Event): void {
    const target = event.target as HTMLInputElement | null;
    const parsed = Number(target?.value ?? 1);
    const nextWeight = Number.isFinite(parsed) && parsed > 0 ? Math.floor(parsed) : 1;

    this.selectedQuestions.update((items) => items.map((item, itemIndex) => (
      itemIndex === index
        ? {...item, weight: nextWeight}
        : item
    )));
  }

  openQuestionDialog(): void {
    if (!this.selectedDomainId()) {
      this.submitError.set("Sélectionne d'abord un domaine pour composer le quiz.");
      return;
    }

    this.questionSubmitError.set(null);
    this.resetQuestionDialog();
    this.questionDialogVisible.set(true);
  }

  closeQuestionDialog(): void {
    this.questionDialogVisible.set(false);
  }

  onQuestionDialogTabChange(value: string | number | undefined): void {
    if (value === undefined || value === null) {
      return;
    }
    this.questionDialogActiveLang.set(String(value) as LangCode);
  }

  addQuestionOption(): void {
    addQuestionAnswerOption(this.fb, this.questionForm, this.questionDialogLangs());
  }

  removeQuestionOption(index: number): void {
    if (this.questionForm.controls.answer_options.length <= 2) {
      return;
    }

    this.questionForm.controls.answer_options.removeAt(index);
    for (const lang of this.questionDialogLangs()) {
      const answers = (getQuestionTrGroup(this.questionForm, lang).controls.answer_options);
      answers.removeAt(index);
    }

    this.questionForm.controls.answer_options.controls.forEach((control, controlIndex) => {
      control.get('sort_order')?.setValue(controlIndex + 1);
    });
  }

  async translateNewQuestion(): Promise<void> {
    const sourceLang = this.questionDialogActiveLang();
    if (!sourceLang) {
      return;
    }

    this.questionTranslating.set(true);
    this.questionSubmitError.set(null);

    try {
      const sourceGroup = getQuestionTrGroup(this.questionForm, sourceLang);
      const sourceTitle = sourceGroup.controls.title.value ?? '';
      const sourceDescription = sourceGroup.controls.description.value ?? '';
      const sourceExplanation = sourceGroup.controls.explanation.value ?? '';

      for (const targetLang of this.questionDialogLangs()) {
        if (targetLang === sourceLang) {
          continue;
        }

        const targetGroup = getQuestionTrGroup(this.questionForm, targetLang);
        const items: TranslateBatchItem[] = [];

        if (!(targetGroup.controls.title.value ?? '').trim()) {
          items.push({key: 'title', text: sourceTitle, format: 'text'});
        }
        if (isEmptyQuestionHtml(targetGroup.controls.description.value ?? '')) {
          items.push({key: 'description', text: sourceDescription, format: 'html'});
        }
        if (isEmptyQuestionHtml(targetGroup.controls.explanation.value ?? '')) {
          items.push({key: 'explanation', text: sourceExplanation, format: 'html'});
        }

        for (let index = 0; index < this.questionForm.controls.answer_options.length; index += 1) {
          const control = targetGroup.controls.answer_options.at(index).controls.content;
          if (!(control.value ?? '').trim()) {
            const sourceContent = sourceGroup.controls.answer_options.at(index).controls.content.value ?? '';
            items.push({key: `ans_${index}`, text: sourceContent, format: 'html'});
          }
        }

        if (!items.length) {
          continue;
        }

        const translated = await this.translationService.translateBatch(sourceLang, targetLang, items);
        if (translated['title'] !== undefined) {
          targetGroup.controls.title.setValue(translated['title']);
        }
        if (translated['description'] !== undefined) {
          targetGroup.controls.description.setValue(translated['description']);
        }
        if (translated['explanation'] !== undefined) {
          targetGroup.controls.explanation.setValue(translated['explanation']);
        }

        for (let index = 0; index < this.questionForm.controls.answer_options.length; index += 1) {
          const key = `ans_${index}`;
          if (translated[key] !== undefined) {
            targetGroup.controls.answer_options.at(index).controls.content.setValue(translated[key]);
          }
        }
      }
    } catch (error) {
      console.error(error);
      queueMicrotask(() => {
        this.submitError.set(this.formatApiError(error, 'Erreur lors de la creation du quiz.'));
      });
      this.questionSubmitError.set('Erreur lors de la traduction de la question.');
    } finally {
      this.questionTranslating.set(false);
    }
  }

  async saveNewQuestion(): Promise<void> {
    this.questionSubmitError.set(null);

    if (!isQuestionEditorFormValid(this.questionForm, this.questionDialogLangs(), {requireDomain: true})) {
      this.questionSubmitError.set(
        'Complète le titre dans chaque langue et toutes les réponses avant de créer la question.',
      );
      this.questionForm.markAllAsTouched();
      return;
    }

    if (getQuestionCorrectCount(this.questionForm) === 0) {
      this.questionSubmitError.set('Il faut cocher au moins une réponse correcte.');
      return;
    }

    this.questionSaving.set(true);

    try {
      const mediaAssetIds = await uploadQuestionEditorMediaAssets(
        this.questionForm.controls.media.value ?? [],
        (params) => this.questionService.questionMediaCreate(params),
      );
      const payload = buildQuestionCreatePayload(
        this.questionForm,
        this.questionDialogLangs(),
        mediaAssetIds,
      );

      const createdQuestion = await firstValueFrom(this.questionService.create(payload));
      this.questions.update((questions) => [createdQuestion, ...questions]);
      this.addExistingQuestion(createdQuestion);
      this.closeQuestionDialog();
    } catch (error) {
      console.error(error);
      this.questionSubmitError.set("Erreur lors de la création de la question.");
    } finally {
      this.questionSaving.set(false);
    }
  }

  async saveQuiz(): Promise<void> {
    this.submitError.set(null);
    this.error.set(null);

    if (!this.isAdmin()) {
      this.submitError.set('La composition de quiz est réservée aux administrateurs.');
      return;
    }

    if (!this.canSave()) {
      this.quizForm.markAllAsTouched();
      this.submitError.set('Complète le quiz et ajoute au moins une question.');
      return;
    }

    this.saving.set(true);
    let quizTemplateId: number | null = null;

    try {
      if (this.isEditMode()) {
        const templateId = this.editingTemplateId();
        if (!templateId) {
          throw new Error('Template introuvable.');
        }
        const template = await firstValueFrom(
          this.quizTemplateService.update(templateId, this.buildQuizTemplatePayload()),
        );
        quizTemplateId = template.id;
        await this.syncTemplateQuestions(template.id);
      } else {
        const template = await firstValueFrom(
          this.quizTemplateService.create(this.buildQuizTemplatePayload()),
        );
        quizTemplateId = template.id;
        await this.syncTemplateQuestions(template.id);
      }
      this.quizService.goList();
    } catch (error) {
      console.error(error);
      this.submitError.set(
        this.isEditMode()
          ? 'Erreur lors de la mise a jour du template.'
          : 'Erreur lors de la creation du template.',
      );

      if (quizTemplateId && !this.isEditMode()) {
        try {
          await firstValueFrom(this.quizTemplateService.destroy(quizTemplateId));
        } catch (cleanupError) {
          console.error('Erreur suppression template orphelin', cleanupError);
        }
      }
    } finally {
      this.saving.set(false);
    }
  }

  getQuestionTitle(question: SelectedQuestionRef): string {
    if ('title' in question && typeof question.title === 'string' && question.title.trim()) {
      return question.title.trim();
    }

    const translation = 'translations' in question
      ? selectTranslation<{title: string}>(
        question.translations as Record<string, {title: string}>,
        this.currentLang(),
      )
      : null;
    return translation?.title?.trim() || `Question #${question.id}`;
  }

  getQuestionSubjects(question: SelectedQuestionRef): string {
    if (!('subjects' in question) || !Array.isArray(question.subjects)) {
      return '';
    }

    return question.subjects
      .map((subject) => this.getSubjectLabel(subject, this.currentLang()))
      .join(', ');
  }

  domainLabel(domain: DomainReadDto): string {
    return this.getDomainLabel(domain);
  }

  protected onDomainSelected(domainId: number): void {
    this.submitError.set(null);
    this.error.set(null);
    this.questions.set([]);

    const hadSelection = this.selectedQuestions().length > 0;
    if (hadSelection && !this.preserveSelectionOnNextDomainChange) {
      this.selectedQuestions.set([]);
      this.submitError.set('Le changement de domaine a réinitialisé la composition du quiz.');
    }
    this.preserveSelectionOnNextDomainChange = false;

    if (!domainId) {
      this.questionDialogLangs.set([]);
      this.questionDialogActiveLang.set(null);
      return;
    }

    this.resetQuestionDialog();
    this.questionsLoading.set(true);
    this.questionService.list({domainId, active: true})
      .pipe(
        takeUntilDestroyed(this.destroyRef),
        finalize(() => this.questionsLoading.set(false)),
      )
      .subscribe({
        next: (questions) => {
          this.questions.set(questions ?? []);
        },
        error: (error) => {
          console.error(error);
          this.error.set('Impossible de charger les questions du domaine sélectionné.');
        },
      });
  }

  private buildQuizTemplatePayload(): QuizTemplateWriteRequestDto {
    return {
      domain: this.selectedDomainId(),
      title: this.quizForm.controls.title.value.trim(),
      description: this.quizForm.controls.description.value.trim(),
      mode: this.quizForm.controls.mode.value,
      max_questions: this.selectedQuestions().length,
      permanent: this.quizForm.controls.permanent.value,
      started_at: this.toIsoDateTime(this.quizForm.controls.started_at.value),
      ended_at: this.toIsoDateTime(this.quizForm.controls.ended_at.value),
      with_duration: this.quizForm.controls.with_duration.value,
      duration: this.quizForm.controls.with_duration.value
        ? Number(this.quizForm.controls.duration.value || 10)
        : 10,
      active: this.quizForm.controls.active.value,
      result_visibility: VisibilityEnumDto.Immediate,
      detail_visibility: this.quizForm.controls.detail_visibility.value,
      detail_available_at: this.toIsoDateTime(this.quizForm.controls.detail_available_at.value),
    };
  }

  private async syncTemplateQuestions(templateId: number): Promise<void> {
    const currentItems = [...this.selectedQuestions()];
    const currentIds = new Set(
      currentItems
        .map((item) => item.quiz_question_id)
        .filter((id): id is number => typeof id === 'number'),
    );

    for (const removedId of this.originalQuizQuestionIds().filter((id) => !currentIds.has(id))) {
      await firstValueFrom(this.quizTemplateService.removeQuestion(templateId, removedId));
    }

    for (const item of currentItems) {
      const payload = {
        question_id: item.question.id,
        sort_order: item.sort_order,
        weight: item.weight,
      };

      if (item.quiz_question_id) {
        await firstValueFrom(
          this.quizTemplateService.updateQuestion(templateId, item.quiz_question_id, payload),
        );
      } else {
        const created = await firstValueFrom(
          this.quizTemplateService.addQuestion(templateId, payload),
        );
        item.quiz_question_id = created.id;
      }
    }

    this.selectedQuestions.set(this.renumberSelectedQuestions(currentItems));
    this.originalQuizQuestionIds.set(
      currentItems
        .map((item) => item.quiz_question_id)
        .filter((id): id is number => typeof id === 'number'),
    );
  }

  private patchTemplate(template: QuizTemplateDto): void {
    this.selectedQuestions.set(
      (template.quiz_questions ?? []).map((quizQuestion) => ({
        quiz_question_id: quizQuestion.id,
        question: quizQuestion.question,
        sort_order: quizQuestion.sort_order ?? 1,
        weight: quizQuestion.weight ?? 1,
      })),
    );
    this.originalQuizQuestionIds.set((template.quiz_questions ?? []).map((quizQuestion) => quizQuestion.id));

    this.preserveSelectionOnNextDomainChange = true;
    this.quizForm.patchValue({
      domain: Number(template.domain ?? 0),
      title: template.title ?? '',
      description: template.description ?? '',
      mode: template.mode ?? ModeEnumDto.Practice,
      active: template.active ?? true,
      permanent: template.permanent ?? true,
      started_at: this.fromIsoDateTime(template.started_at),
      ended_at: this.fromIsoDateTime(template.ended_at),
      with_duration: template.with_duration ?? false,
      duration: template.duration ?? 10,
      detail_visibility: template.detail_visibility ?? VisibilityEnumDto.Immediate,
      detail_available_at: this.fromIsoDateTime(template.detail_available_at),
    });
  }

  private resetQuestionDialog(): void {
    const domain = this.selectedDomain();
    const domainId = this.selectedDomainId();

    this.questionForm = createQuestionEditorForm(this.fb, {domainDisabled: true});
    this.questionForm.controls.domain.setValue(domainId);
    this.questionForm.controls.domain.disable({emitEvent: false});
    this.questionForm.controls.active.setValue(true);
    this.questionForm.controls.is_mode_practice.setValue(true);
    this.questionForm.controls.is_mode_exam.setValue(false);

    const langs = (domain?.allowed_languages ?? [])
      .filter((language) => !!language.active)
      .map((language) => language.code)
      .filter((code): code is LangCode => !!code);

    const resolvedLangs = langs.length ? langs : [LanguageEnumDto.Fr as LangCode];
    this.questionDialogLangs.set(resolvedLangs);
    this.questionDialogActiveLang.set(resolvedLangs[0] ?? null);

    ensureQuestionTranslationControls(this.fb, this.questionForm, resolvedLangs);
    addQuestionAnswerOption(this.fb, this.questionForm, resolvedLangs);
    addQuestionAnswerOption(this.fb, this.questionForm, resolvedLangs);
  }

  private formatApiError(error: unknown, fallback = 'Erreur inconnue.'): string {
    if (error instanceof Error && error.message) {
      return error.message;
    }

    const apiError = error as {
      error?: unknown;
      message?: string;
    };

    if (typeof apiError?.error === 'string' && apiError.error.trim()) {
      return apiError.error;
    }

    if (apiError?.error && typeof apiError.error === 'object') {
      const details = Object.entries(apiError.error as Record<string, unknown>)
        .map(([key, value]) => {
          if (Array.isArray(value)) {
            return `${key}: ${value.join(', ')}`;
          }
          if (value && typeof value === 'object') {
            return `${key}: ${JSON.stringify(value)}`;
          }
          return `${key}: ${String(value)}`;
        })
        .join(' | ');

      if (details) {
        return details;
      }
    }

    if (apiError?.message) {
      return apiError.message;
    }

    return fallback;
  }

  private toIsoDateTime(value: Date | string | null): string | null {
    if (!value) {
      return null;
    }

    const date = value instanceof Date ? value : new Date(value);
    return Number.isNaN(date.getTime()) ? null : date.toISOString();
  }

  private fromIsoDateTime(value: string | null | undefined): Date | null {
    if (!value) {
      return null;
    }

    const date = new Date(value);
    return Number.isNaN(date.getTime()) ? null : date;
  }

  private applyDatePickerLocale(lang: LanguageEnumDto): void {
    const text = this.getUiText(lang);
    const translation: Translation = {
      dayNames: text.dayNames,
      dayNamesShort: text.dayNamesShort,
      dayNamesMin: text.dayNamesMin,
      monthNames: text.monthNames,
      monthNamesShort: text.monthNamesShort,
      today: text.today,
      clear: text.clear,
      weekHeader: text.weekHeader,
      dateFormat: text.dateFormat,
    };

    this.primeng.setTranslation(translation);
  }

  private getUiText(lang: LanguageEnumDto) {
    return getQuizCreateUiText(lang);
  }

  private renumberSelectedQuestions(items: SelectedQuizQuestion[]): SelectedQuizQuestion[] {
    return items.map((item, index) => ({
      ...item,
      sort_order: index + 1,
    }));
  }

  private getDomainLabel(domain: DomainReadDto): string {
    const translations = domain.translations as DomainTranslations | undefined;
    const current = translations?.[this.currentLang()]?.name?.trim();
    if (current) {
      return current;
    }

    for (const fallback of [LanguageEnumDto.Fr, LanguageEnumDto.En, LanguageEnumDto.Nl]) {
      const value = translations?.[fallback]?.name?.trim();
      if (value) {
        return value;
      }
    }

    return `Domain #${domain.id}`;
  }

  private getSubjectLabel(
    subject: SubjectReadDto | QuestionReadDto['subjects'][number],
    lang: LanguageEnumDto,
  ): string {
    const translation = selectTranslation<{name: string}>(
      subject.translations as Record<string, {name: string}>,
      lang,
    );
    return translation?.name?.trim() || `Sujet #${subject.id}`;
  }
}
