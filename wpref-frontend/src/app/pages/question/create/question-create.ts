import {CommonModule} from '@angular/common';
import {Component, computed, DestroyRef, effect, inject, OnInit, signal} from '@angular/core';
import {ActivatedRoute} from '@angular/router';
import {FormControl, NonNullableFormBuilder, ReactiveFormsModule} from '@angular/forms';
import {takeUntilDestroyed} from '@angular/core/rxjs-interop';
import {firstValueFrom, forkJoin} from 'rxjs';
import {finalize} from 'rxjs/operators';

import {ButtonModule} from 'primeng/button';
import {CardModule} from 'primeng/card';

import {DomainReadDto, LanguageEnumDto, SubjectReadDto} from '../../../api/generated';
import {QuestionEditorFormComponent} from '../../../components/question-editor-form/question-editor-form';
import {DomainOption, DomainService, DomainTranslations} from '../../../services/domain/domain';
import {
  addQuestionAnswerOption,
  buildQuestionCreatePayload,
  clearQuestionTranslationTab,
  createQuestionEditorForm,
  ensureQuestionTranslationControls,
  getAnswerContentControl,
  getQuestionCorrectCount,
  getQuestionTrGroup,
  isEmptyQuestionHtml,
  isQuestionEditorFormValid,
  populateQuestionEditorFormFromDraft,
  QuestionEditorForm,
  resetQuestionTranslationsOnly,
  syncLangAnswerArraysWithRoot,
  uploadQuestionEditorMediaAssets,
  removeQuestionAnswerOption,
} from '../../../services/question/question-editor-form';
import {QuestionService} from '../../../services/question/question';
import {SubjectService} from '../../../services/subject/subject';
import {LangCode, TranslateBatchItem, TranslationService} from '../../../services/translation/translation';
import {UserService} from '../../../services/user/user';
import {selectTranslation} from '../../../shared/i18n/select-translation';
import {getEditorUiText} from '../../../shared/i18n/editor-ui-text';

@Component({
  standalone: true,
  selector: 'app-question-create',
  templateUrl: './question-create.html',
  styleUrl: './question-create.scss',
  imports: [
    CommonModule,
    ReactiveFormsModule,
    ButtonModule,
    CardModule,
    QuestionEditorFormComponent,
  ],
})
export class QuestionCreate implements OnInit {
  readonly ui = computed(() => getEditorUiText(this.userService.currentLang));
  readonly emptyLanguagesMessage = "Ce domaine n'a pas de langues actives configurees.";
  readonly practiceTooltip = 'la question sera publique et selectionnable pour les quizzes generes.';

  loading = signal(true);
  domainLoading = signal(false);
  saving = signal(false);
  translating = signal(false);

  error = signal<string | null>(null);
  submitError = signal<string | null>(null);

  readonly isLocked = computed(
    () => this.loading() || this.domainLoading() || this.saving() || this.translating(),
  );

  domains = signal<DomainReadDto[]>([]);
  subjects = signal<SubjectReadDto[]>([]);
  selectedDomainId = signal<number>(0);
  domainLangs = signal<LangCode[]>([]);
  activeLang = signal<LangCode | null>(null);
  currentLang = signal<LanguageEnumDto>(LanguageEnumDto.En);
  translateOverwrite = signal(false);

  readonly domainOptions = computed<DomainOption[]>(() => {
    const lang = this.currentLang();
    return this.domains().map((domain) => ({
      id: domain.id,
      name: this.getDomainLabel(domain, lang),
    }));
  });

  readonly filteredSubjects = computed(() => {
    const domainId = this.selectedDomainId();
    if (!domainId) {
      return [];
    }
    return this.subjects().filter((subject) => subject.domain === domainId);
  });

  readonly subjectOptions = computed<Array<{ name: string; code: number }>>(() => {
    const lang = this.currentLang();
    return this.filteredSubjects().map((subject) => {
      const translation = selectTranslation<{ name: string }>(
        subject.translations as Record<string, { name: string }>,
        lang,
      );
      return {
        name: translation?.name ?? `Subject #${subject.id}`,
        code: subject.id,
      };
    });
  });

  readonly subjectsDisabled = computed(() => {
    return this.isLocked() || !this.selectedDomainId() || this.subjectOptions().length === 0;
  });

  private fb = inject(NonNullableFormBuilder);
  form: QuestionEditorForm = createQuestionEditorForm(this.fb, {subjectIdsDisabled: true});

  private destroyRef = inject(DestroyRef);
  private route = inject(ActivatedRoute);
  private domainService = inject(DomainService);
  private subjectService = inject(SubjectService);
  private questionService = inject(QuestionService);
  private translator = inject(TranslationService);
  private userService = inject(UserService);

  constructor() {
    effect(() => {
      const locked = this.isLocked();

      if (locked) {
        this.form.controls.domain.disable({emitEvent: false});
      } else {
        this.form.controls.domain.enable({emitEvent: false});
      }

      const enableSubjects = !locked && !!this.selectedDomainId() && this.subjectOptions().length > 0;
      if (enableSubjects) {
        this.form.controls.subject_ids.enable({emitEvent: false});
      } else {
        this.form.controls.subject_ids.disable({emitEvent: false});
      }
    });
  }

  tabCodes(): LangCode[] {
    return this.domainLangs();
  }

  ngOnInit(): void {
    this.currentLang.set(this.userService.currentLang ?? LanguageEnumDto.Fr);

    this.form.controls.domain.valueChanges
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe((value) => this.onDomainChange(Number(value ?? 0)));

    this.loading.set(true);
    forkJoin({
      domains: this.domainService.list(),
      subjects: this.subjectService.list(),
    })
      .pipe(
        takeUntilDestroyed(this.destroyRef),
        finalize(() => this.loading.set(false)),
      )
      .subscribe({
        next: ({domains, subjects}) => {
          this.domains.set(domains ?? []);
          this.subjects.set(subjects ?? []);
          this.tryApplyDuplicateDraft();
        },
        error: (err) => {
          console.error(err);
          this.error.set('Impossible de charger les donnees initiales.');
        },
      });

    const queryDomainId = Number(this.route.snapshot.queryParamMap.get('domainId') ?? 0);
    if (queryDomainId > 0) {
      this.form.controls.domain.setValue(queryDomainId);
    }
  }

  goList(): void {
    this.questionService.goList();
  }

  goBack(): void {
    this.questionService.goBack();
  }

  clearActiveTab(): void {
    const lang = this.activeLang();
    if (!lang) {
      return;
    }
    clearQuestionTranslationTab(this.form, lang);
  }

  onTabChange(value: string | number | undefined): void {
    if (value === undefined || value === null) {
      return;
    }
    const code = String(value) as LangCode;
    if (!this.domainLangs().includes(code)) {
      return;
    }
    this.activeLang.set(code);
  }

  addOption(): void {
    addQuestionAnswerOption(this.fb, this.form, this.domainLangs());
  }

  removeOption(index: number): void {
    removeQuestionAnswerOption(this.form, this.domainLangs(), index);
  }

  answerContentCtrl(index: number, lang: LangCode): FormControl<string> {
    return getAnswerContentControl(this.form, index, lang);
  }

  async translateFromActiveTab(): Promise<void> {
    const source = this.activeLang();
    if (!source) {
      return;
    }
    await this.translateFrom(source);
  }

  async translateFrom(sourceLang: LangCode): Promise<void> {
    const codes = this.tabCodes();
    if (!codes.includes(sourceLang)) {
      return;
    }

    this.translating.set(true);
    this.submitError.set(null);

    try {
      const sourceGroup = getQuestionTrGroup(this.form, sourceLang);
      const sourceTitle = sourceGroup.controls.title.value ?? '';
      const sourceDescription = sourceGroup.controls.description.value ?? '';
      const sourceExplanation = sourceGroup.controls.explanation.value ?? '';
      const overwrite = this.translateOverwrite();

      for (const targetLang of codes) {
        if (targetLang === sourceLang) {
          continue;
        }

        const targetGroup = getQuestionTrGroup(this.form, targetLang);
        const items: TranslateBatchItem[] = [];

        const needsTitle = overwrite || !(targetGroup.controls.title.value ?? '').trim();
        if (needsTitle) {
          items.push({key: 'title', text: sourceTitle, format: 'text'});
        }

        const needsDescription = overwrite || isEmptyQuestionHtml(targetGroup.controls.description.value ?? '');
        if (needsDescription) {
          items.push({key: 'description', text: sourceDescription, format: 'html'});
        }

        const needsExplanation = overwrite || isEmptyQuestionHtml(targetGroup.controls.explanation.value ?? '');
        if (needsExplanation) {
          items.push({key: 'explanation', text: sourceExplanation, format: 'html'});
        }

        for (let i = 0; i < this.form.controls.answer_options.length; i += 1) {
          const targetControl = this.answerContentCtrl(i, targetLang);
          const needsAnswer = overwrite || isEmptyQuestionHtml(targetControl.value ?? '');
          if (!needsAnswer) {
            continue;
          }

          const sourceControl = this.answerContentCtrl(i, sourceLang);
          items.push({key: `ans_${i}`, text: sourceControl.value ?? '', format: 'html'});
        }

        if (!items.length) {
          continue;
        }

        const translated = await this.translator.translateBatch(sourceLang, targetLang, items);

        if (needsTitle && translated['title'] !== undefined) {
          targetGroup.controls.title.setValue(translated['title']);
          targetGroup.controls.title.markAsDirty();
        }
        if (needsDescription && translated['description'] !== undefined) {
          targetGroup.controls.description.setValue(translated['description']);
          targetGroup.controls.description.markAsDirty();
        }
        if (needsExplanation && translated['explanation'] !== undefined) {
          targetGroup.controls.explanation.setValue(translated['explanation']);
          targetGroup.controls.explanation.markAsDirty();
        }

        for (let i = 0; i < this.form.controls.answer_options.length; i += 1) {
          const key = `ans_${i}`;
          if (translated[key] === undefined) {
            continue;
          }
          const targetControl = this.answerContentCtrl(i, targetLang);
          targetControl.setValue(translated[key]);
          targetControl.markAsDirty();
        }
      }
    } catch (error) {
      console.error(error);
      this.submitError.set('Erreur lors de la traduction.');
    } finally {
      this.translating.set(false);
    }
  }

  async save(): Promise<void> {
    this.error.set(null);
    this.submitError.set(null);

    if (!isQuestionEditorFormValid(this.form, this.domainLangs(), {requireDomain: true})) {
      this.error.set(
        'Merci de selectionner un domaine et de completer au minimum le titre dans chaque langue et toutes les reponses.',
      );
      this.form.markAllAsTouched();
      return;
    }

    if (getQuestionCorrectCount(this.form) === 0) {
      this.submitError.set('Il faut cocher au moins une reponse correcte.');
      return;
    }

    this.saving.set(true);

    try {
      const mediaAssetIds = await uploadQuestionEditorMediaAssets(
        this.form.controls.media.value ?? [],
        (params) => this.questionService.questionMediaCreate(params),
      );
      const payload = buildQuestionCreatePayload(this.form, this.domainLangs(), mediaAssetIds);

      await firstValueFrom(this.questionService.create(payload));
      this.goList();
    } catch (error) {
      console.error('Erreur creation question', error);
      this.submitError.set("Erreur lors de l'enregistrement de la question.");
    } finally {
      this.saving.set(false);
    }
  }

  protected onDomainChange(domainId: number): void {
    this.error.set(null);
    this.submitError.set(null);
    this.selectedDomainId.set(domainId);

    this.form.controls.subject_ids.setValue([]);
    resetQuestionTranslationsOnly(this.form);
    this.domainLangs.set([]);
    this.activeLang.set(null);

    if (!domainId || domainId <= 0) {
      return;
    }

    this.domainLoading.set(true);
    this.domainService
      .retrieve(domainId)
      .pipe(
        takeUntilDestroyed(this.destroyRef),
        finalize(() => this.domainLoading.set(false)),
      )
      .subscribe({
        next: (domain) => {
          const codes = (domain.allowed_languages ?? [])
            .filter((language) => !!language.active)
            .map((language) => language.code)
            .filter((code): code is LangCode => !!code);

          const langs = codes.length ? codes : [LanguageEnumDto.Fr as unknown as LangCode];
          this.domainLangs.set(langs);

          ensureQuestionTranslationControls(this.fb, this.form, langs);
          if (this.form.controls.answer_options.length === 0) {
            addQuestionAnswerOption(this.fb, this.form, langs);
            addQuestionAnswerOption(this.fb, this.form, langs);
          } else {
            syncLangAnswerArraysWithRoot(this.fb, this.form, langs);
          }

          this.activeLang.set(langs[0] ?? null);
        },
        error: (error) => {
          console.error(error);
          this.error.set('Impossible de charger le domaine selectionne.');
        },
      });
  }

  private tryApplyDuplicateDraft(): void {
    const draft = this.questionService.consumeDuplicateDraft();
    if (!draft) {
      return;
    }

    this.selectedDomainId.set(draft.domainId);

    const domain = this.domains().find((item) => item.id === draft.domainId);
    const codes = (domain?.allowed_languages ?? [])
      .filter((language) => !!language.active)
      .map((language) => language.code)
      .filter((code): code is LangCode => !!code);

    const langs = codes.length ? codes : (Object.keys(draft.translations) as LangCode[]);
    this.domainLangs.set(langs);
    populateQuestionEditorFormFromDraft(this.fb, this.form, draft, langs);
    this.activeLang.set(langs[0] ?? null);
  }

  private getDomainLabel(domain: DomainReadDto, lang: LanguageEnumDto): string {
    const translations = domain.translations as DomainTranslations | undefined;
    const current = translations?.[lang]?.name?.trim();
    if (current) {
      return current;
    }

    const fallbacks: LanguageEnumDto[] = [LanguageEnumDto.Fr, LanguageEnumDto.En, LanguageEnumDto.Nl];
    for (const fallback of fallbacks) {
      const value = translations?.[fallback]?.name?.trim();
      if (value) {
        return value;
      }
    }

    return `Domain #${domain.id}`;
  }
}
