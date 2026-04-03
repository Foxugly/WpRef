import {CommonModule} from '@angular/common';
import {Component, computed, DestroyRef, inject, OnInit, signal} from '@angular/core';
import {ActivatedRoute} from '@angular/router';
import {NonNullableFormBuilder, ReactiveFormsModule} from '@angular/forms';
import {takeUntilDestroyed} from '@angular/core/rxjs-interop';
import {firstValueFrom, forkJoin} from 'rxjs';
import {finalize} from 'rxjs/operators';

import {ButtonModule} from 'primeng/button';
import {DomainReadDto, LanguageEnumDto, QuestionReadDto, SubjectReadDto} from '../../../api/generated';
import {QuestionEditorFormComponent} from '../../../components/question-editor-form/question-editor-form';
import {
  addQuestionAnswerOption,
  buildQuestionPatchPayload,
  clearQuestionTranslationTab,
  createQuestionEditorForm,
  getAnswerContentControl,
  getQuestionCorrectCount,
  getQuestionTrGroup,
  isEmptyQuestionHtml,
  isQuestionEditorFormValid,
  populateQuestionEditorForm,
  QuestionEditorForm,
  removeQuestionAnswerOption,
  uploadQuestionEditorMediaAssets,
} from '../../../services/question/question-editor-form';
import {QuestionService} from '../../../services/question/question';
import {SubjectService} from '../../../services/subject/subject';
import {LangCode, TranslateBatchItem, TranslationService} from '../../../services/translation/translation';
import {UserService} from '../../../services/user/user';
import {selectTranslation} from '../../../shared/i18n/select-translation';
import {getEditorUiText} from '../../../shared/i18n/editor-ui-text';

@Component({
  standalone: true,
  selector: 'app-question-edit',
  templateUrl: './question-edit.html',
  styleUrl: './question-edit.scss',
  imports: [
    CommonModule,
    ReactiveFormsModule,
    ButtonModule,
    QuestionEditorFormComponent,
  ],
})
export class QuestionEdit implements OnInit {
  readonly ui = computed(() => getEditorUiText(this.userService.currentLang));
  id!: number;
  readonly emptyLanguagesMessage = 'Aucune langue active sur ce domaine.';

  loading = signal(true);
  saving = signal(false);
  deleting = signal(false);
  error = signal<string | null>(null);
  submitError = signal<string | null>(null);
  success = signal<string | null>(null);

  question = signal<QuestionReadDto | null>(null);
  subjects = signal<SubjectReadDto[]>([]);
  domainLangs = signal<LangCode[]>([]);
  activeLang = signal<LangCode | null>(null);
  currentLang = signal<LanguageEnumDto>(LanguageEnumDto.Fr);
  translating = signal(false);
  translateOverwrite = signal(false);

  private fb = inject(NonNullableFormBuilder);
  form: QuestionEditorForm = createQuestionEditorForm(this.fb, {domainDisabled: true});

  private destroyRef = inject(DestroyRef);
  private route = inject(ActivatedRoute);
  private questionService = inject(QuestionService);
  private subjectService = inject(SubjectService);
  private translator = inject(TranslationService);
  private userService = inject(UserService);

  readonly filteredSubjects = computed(() => {
    const domainId = this.question()?.domain.id;
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

  ngOnInit(): void {
    this.currentLang.set(this.userService.currentLang ?? LanguageEnumDto.Fr);

    this.id = Number(
      this.route.snapshot.paramMap.get('questionId') ??
      this.route.snapshot.paramMap.get('id'),
    );

    if (!this.id || Number.isNaN(this.id)) {
      this.loading.set(false);
      this.error.set('Identifiant de question invalide.');
      return;
    }

    this.loadData();
  }

  tabCodes(): LangCode[] {
    return this.domainLangs();
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

  goBack(): void {
    this.questionService.goBack();
  }

  goView(questionId: number): void {
    this.questionService.goView(questionId);
  }

  duplicateQuestion(): void {
    const question = this.question();
    if (!question) {
      return;
    }
    this.questionService.duplicateToNew(question);
  }

  clearActiveTab(): void {
    const lang = this.activeLang();
    if (!lang) {
      return;
    }
    clearQuestionTranslationTab(this.form, lang);
  }

  answerContentCtrl(index: number, lang: LangCode) {
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

  async deleteQuestion(): Promise<void> {
    this.error.set(null);
    this.submitError.set(null);
    this.success.set(null);

    const confirmed = window.confirm('Supprimer cette question ?');
    if (!confirmed) {
      return;
    }

    this.deleting.set(true);

    try {
      await firstValueFrom(this.questionService.delete(this.id));
      this.questionService.goList();
    } catch (err: any) {
      if (err?.error && typeof err.error === 'object') {
        this.submitError.set(JSON.stringify(err.error));
      } else {
        this.submitError.set('Erreur lors de la suppression de la question.');
      }
    } finally {
      this.deleting.set(false);
    }
  }

  async save(): Promise<void> {
    this.error.set(null);
    this.submitError.set(null);
    this.success.set(null);

    if (!isQuestionEditorFormValid(this.form, this.domainLangs())) {
      this.submitError.set(
        'Merci de completer le titre et toutes les reponses dans chaque langue du domaine.',
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
      const payload = buildQuestionPatchPayload(this.form, this.domainLangs(), mediaAssetIds);

      await firstValueFrom(this.questionService.updatePartial(this.id, payload));

      this.success.set('Question mise a jour avec succes.');
      this.goView(this.id);
    } catch (err: any) {
      if (err?.error && typeof err.error === 'object') {
        this.submitError.set(JSON.stringify(err.error));
      } else {
        this.submitError.set("Erreur lors de l'enregistrement de la question.");
      }
    } finally {
      this.saving.set(false);
    }
  }

  getDomainLabel(domain: DomainReadDto): string {
    const label = selectTranslation<{ name: string }>(
      domain.translations as Record<string, { name: string }>,
      this.currentLang(),
    );
    return label?.name ?? `Domain #${domain.id}`;
  }

  private loadData(): void {
    this.loading.set(true);
    this.error.set(null);

    forkJoin({
      subjects: this.subjectService.list(),
      question: this.questionService.retrieve(this.id),
    })
      .pipe(
        takeUntilDestroyed(this.destroyRef),
        finalize(() => this.loading.set(false)),
      )
      .subscribe({
        next: ({subjects, question}) => {
          this.subjects.set(subjects ?? []);
          this.question.set(question);
          const langs = populateQuestionEditorForm(this.fb, this.form, question);
          this.domainLangs.set(langs);
          this.activeLang.set(langs[0] ?? null);

          if (this.form.controls.answer_options.length === 0) {
            addQuestionAnswerOption(this.fb, this.form, langs);
            addQuestionAnswerOption(this.fb, this.form, langs);
          }
        },
        error: () => {
          this.error.set('Impossible de charger la question.');
        },
      });
  }
}
