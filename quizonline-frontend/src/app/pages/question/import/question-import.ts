import {CommonModule} from '@angular/common';
import {Component, computed, inject, OnInit, signal} from '@angular/core';
import {firstValueFrom} from 'rxjs';

import {ButtonModule} from 'primeng/button';
import {CardModule} from 'primeng/card';
import {FileUploadModule} from 'primeng/fileupload';
import {MessageService} from 'primeng/api';

import {
  LocalizedAnswerOptionTranslationRequestDto,
  LocalizedQuestionTranslationRequestDto,
  QuestionAnswerOptionWritePayloadRequestDto,
  QuestionWritePayloadRequestDto,
  LanguageEnumDto,
} from '../../../api/generated';
import {QuestionService} from '../../../services/question/question';
import {UserService} from '../../../services/user/user';
import {getQuestionImportUiText, QuestionImportUiText} from './question-import.i18n';

type QuestionImportFile = {
  questions: QuestionWritePayloadRequestDto[];
};

@Component({
  standalone: true,
  selector: 'app-question-import',
  templateUrl: './question-import.html',
  styleUrl: './question-import.scss',
  imports: [
    CommonModule,
    ButtonModule,
    CardModule,
    FileUploadModule,
  ],
})
export class QuestionImport implements OnInit {
  readonly text = computed<QuestionImportUiText>(() => getQuestionImportUiText(this.currentLang()));
  readonly hasValidFile = computed(() => this.validationErrors().length === 0 && this.questions().length > 0);

  importing = signal(false);
  selectedFileName = signal<string | null>(null);
  questions = signal<QuestionWritePayloadRequestDto[]>([]);
  validationErrors = signal<string[]>([]);

  private questionService = inject(QuestionService);
  private userService = inject(UserService);
  private messageService = inject(MessageService);
  private currentLang = signal<LanguageEnumDto>(LanguageEnumDto.En);

  ngOnInit(): void {
    this.currentLang.set(this.userService.currentLang ?? LanguageEnumDto.En);
  }

  goBack(): void {
    this.questionService.goList();
  }

  cancel(): void {
    this.questionService.goList();
  }

  async onFileSelected(event: { files?: File[] }): Promise<void> {
    const file = event.files?.[0];
    if (!file) {
      return;
    }

    this.selectedFileName.set(file.name);

    try {
      const content = await file.text();
      const raw = JSON.parse(content) as unknown;
      const {questions, errors} = this.parseImportFile(raw);

      this.questions.set(questions);
      this.validationErrors.set(errors);

      if (errors.length === 0) {
        this.showToast('success', this.text().formatValid, this.text().fileValidated(questions.length));
      } else {
        this.showToast('error', this.text().formatInvalid, errors[0]);
      }
    } catch {
      this.questions.set([]);
      this.validationErrors.set([this.text().invalidJson]);
      this.showToast('error', this.text().formatInvalid, this.text().invalidJson);
    }
  }

  clearSelection(): void {
    this.selectedFileName.set(null);
    this.questions.set([]);
    this.validationErrors.set([]);
  }

  downloadExample(): void {
    const blob = new Blob([JSON.stringify(this.buildExampleFile(), null, 2)], {
      type: 'application/json;charset=utf-8',
    });
    const url = URL.createObjectURL(blob);
    const anchor = document.createElement('a');
    anchor.href = url;
    anchor.download = 'question-import-example.json';
    anchor.click();
    URL.revokeObjectURL(url);
  }

  async importQuestions(): Promise<void> {
    if (!this.hasValidFile() || this.importing()) {
      return;
    }

    this.importing.set(true);

    try {
      const results = await Promise.allSettled(
        this.questions().map((question) => firstValueFrom(this.questionService.create(question))),
      );

      const failedIndices = results
        .map((result, index) => (result.status === 'rejected' ? index + 1 : null))
        .filter((index): index is number => index !== null);
      const successCount = results.length - failedIndices.length;

      if (failedIndices.length === 0) {
        this.showToast('success', this.text().importDone, this.text().importSuccess(successCount));
        this.questionService.goList();
        return;
      }

      this.showToast(
        successCount > 0 ? 'warn' : 'error',
        this.text().importPartialTitle,
        successCount > 0
          ? this.text().importPartialMessage(successCount, failedIndices.length)
          : this.text().importFailure(failedIndices[0]),
      );
    } finally {
      this.importing.set(false);
    }
  }

  private parseImportFile(raw: unknown): { questions: QuestionWritePayloadRequestDto[]; errors: string[] } {
    const errors: string[] = [];

    if (!raw || typeof raw !== 'object' || Array.isArray(raw)) {
      return {questions: [], errors: [this.text().rootObjectError]};
    }

    const payload = raw as Partial<QuestionImportFile>;
    if (!Array.isArray(payload.questions)) {
      return {questions: [], errors: [this.text().questionsArrayError]};
    }

    const normalizedQuestions = payload.questions.map((question, index) =>
      this.normalizeQuestion(question, index + 1, errors),
    );

    return {
      questions: normalizedQuestions.filter((question): question is QuestionWritePayloadRequestDto => question !== null),
      errors,
    };
  }

  private normalizeQuestion(
    question: QuestionWritePayloadRequestDto | undefined,
    itemNumber: number,
    errors: string[],
  ): QuestionWritePayloadRequestDto | null {
    if (!question || typeof question !== 'object') {
      errors.push(this.text().questionObjectError(itemNumber));
      return null;
    }

    if (!Number.isInteger(question.domain) || question.domain <= 0) {
      errors.push(this.text().questionDomainError(itemNumber));
    }

    const translations = this.normalizeQuestionTranslations(question.translations, itemNumber, errors);
    const answers = this.normalizeAnswerOptions(question.answer_options, itemNumber, errors);
    const subjectIds = this.normalizeNumberArray(question.subject_ids, this.text().questionSubjectsError(itemNumber), errors);
    const mediaAssetIds = this.normalizeNumberArray(question.media_asset_ids, this.text().questionMediaError(itemNumber), errors);

    if (!translations || !answers) {
      return null;
    }

    return {
      domain: question.domain,
      translations,
      allow_multiple_correct: !!question.allow_multiple_correct,
      active: question.active ?? true,
      is_mode_practice: !!question.is_mode_practice,
      is_mode_exam: !!question.is_mode_exam,
      subject_ids: subjectIds ?? [],
      answer_options: answers,
      media_asset_ids: mediaAssetIds ?? [],
    };
  }

  private normalizeQuestionTranslations(
    translations: { [key: string]: LocalizedQuestionTranslationRequestDto } | undefined,
    itemNumber: number,
    errors: string[],
  ): { [key: string]: LocalizedQuestionTranslationRequestDto } | null {
    if (!translations || typeof translations !== 'object' || Array.isArray(translations)) {
      errors.push(this.text().questionTranslationsError(itemNumber));
      return null;
    }

    const entries = Object.entries(translations);
    if (entries.length === 0) {
      errors.push(this.text().questionTranslationsError(itemNumber));
      return null;
    }

    const normalized: { [key: string]: LocalizedQuestionTranslationRequestDto } = {};

    for (const [lang, value] of entries) {
      if (!value || typeof value !== 'object') {
        errors.push(this.text().questionTranslationShapeError(itemNumber, lang));
        continue;
      }

      if (typeof value.title !== 'string' || typeof value.description !== 'string' || typeof value.explanation !== 'string') {
        errors.push(this.text().questionTranslationShapeError(itemNumber, lang));
        continue;
      }

      normalized[lang] = {
        title: value.title,
        description: value.description,
        explanation: value.explanation,
      };
    }

    return Object.keys(normalized).length > 0 ? normalized : null;
  }

  private normalizeAnswerOptions(
    answers: QuestionAnswerOptionWritePayloadRequestDto[] | undefined,
    itemNumber: number,
    errors: string[],
  ): QuestionAnswerOptionWritePayloadRequestDto[] | null {
    if (!Array.isArray(answers) || answers.length < 2) {
      errors.push(this.text().questionAnswersError(itemNumber));
      return null;
    }

    let correctCount = 0;
    const normalized = answers.map<QuestionAnswerOptionWritePayloadRequestDto | null>((answer, index) => {
      if (!answer || typeof answer !== 'object') {
        errors.push(this.text().answerShapeError(itemNumber, index + 1));
        return null;
      }

      const translations = this.normalizeAnswerTranslations(answer.translations, itemNumber, index + 1, errors);
      if (!translations) {
        return null;
      }

      if (answer.is_correct) {
        correctCount += 1;
      }

      return {
        is_correct: !!answer.is_correct,
        sort_order: Number.isInteger(answer.sort_order) ? answer.sort_order : index + 1,
        translations,
      };
    });

    if (correctCount === 0) {
      errors.push(this.text().questionCorrectAnswerError(itemNumber));
    }

    const validAnswers = normalized.filter((answer): answer is QuestionAnswerOptionWritePayloadRequestDto => answer !== null);
    return validAnswers.length === answers.length ? validAnswers : null;
  }

  private normalizeAnswerTranslations(
    translations: { [key: string]: LocalizedAnswerOptionTranslationRequestDto } | undefined,
    itemNumber: number,
    answerNumber: number,
    errors: string[],
  ): { [key: string]: LocalizedAnswerOptionTranslationRequestDto } | null {
    if (!translations || typeof translations !== 'object' || Array.isArray(translations)) {
      errors.push(this.text().answerTranslationsError(itemNumber, answerNumber));
      return null;
    }

    const entries = Object.entries(translations);
    if (entries.length === 0) {
      errors.push(this.text().answerTranslationsError(itemNumber, answerNumber));
      return null;
    }

    const normalized: { [key: string]: LocalizedAnswerOptionTranslationRequestDto } = {};
    for (const [lang, value] of entries) {
      if (!value || typeof value !== 'object' || typeof value.content !== 'string') {
        errors.push(this.text().answerTranslationShapeError(itemNumber, answerNumber, lang));
        continue;
      }

      normalized[lang] = {content: value.content};
    }

    return Object.keys(normalized).length > 0 ? normalized : null;
  }

  private normalizeNumberArray(
    value: number[] | undefined,
    errorMessage: string,
    errors: string[],
  ): number[] | null {
    if (value === undefined) {
      return [];
    }

    if (!Array.isArray(value) || value.some((item) => !Number.isInteger(item) || item <= 0)) {
      errors.push(errorMessage);
      return null;
    }

    return value;
  }

  private buildExampleFile(): QuestionImportFile {
    return {
      questions: [
        {
          domain: 1,
          subject_ids: [2],
          allow_multiple_correct: false,
          active: true,
          is_mode_practice: true,
          is_mode_exam: false,
          translations: {
            fr: {
              title: 'Capitale de la Belgique',
              description: '<p>Choisis la bonne reponse.</p>',
              explanation: '<p>Bruxelles est la capitale de la Belgique.</p>',
            },
            en: {
              title: 'Capital of Belgium',
              description: '<p>Choose the correct answer.</p>',
              explanation: '<p>Brussels is the capital of Belgium.</p>',
            },
          },
          answer_options: [
            {
              is_correct: true,
              sort_order: 1,
              translations: {
                fr: {content: '<p>Bruxelles</p>'},
                en: {content: '<p>Brussels</p>'},
              },
            },
            {
              is_correct: false,
              sort_order: 2,
              translations: {
                fr: {content: '<p>Anvers</p>'},
                en: {content: '<p>Antwerp</p>'},
              },
            },
          ],
          media_asset_ids: [],
        },
      ],
    };
  }

  private showToast(severity: 'success' | 'error' | 'warn', summary: string, detail: string): void {
    this.messageService.add({
      severity,
      summary,
      detail,
    });
  }

}
