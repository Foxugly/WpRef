import {Injectable} from '@angular/core';
import {FormArray, FormControl, FormGroup} from '@angular/forms';
import {Router} from '@angular/router';
import {map, Observable} from 'rxjs';

import {ROUTES} from '../../app.routes-paths';
import {
  LanguageEnumDto,
  MediaAssetDto,
  QuestionApi,
  QuestionCreateRequestParams,
  QuestionDestroyRequestParams,
  QuestionListRequestParams,
  QuestionMediaCreateRequestParams,
  QuestionPartialUpdateRequestParams,
  QuestionReadDto,
  QuestionRetrieveRequestParams,
  QuestionUpdateRequestParams,
  QuestionWritePayloadRequestDto,
  PatchedQuestionPartialWritePayloadRequestDto,
} from '../../api/generated';
import {selectTranslation} from '../../shared/i18n/select-translation';
import {LangCode} from '../translation/translation';

export type QuestionTrGroup = FormGroup<{
  title: FormControl<string>;
  description: FormControl<string>;
  explanation: FormControl<string>;
  answer_options: FormArray<AnswerTrGroup>;
}>;

export type AnswerTrGroup = FormGroup<{
  content: FormControl<string>;
}>;

export type QuestionTranslationForm = {
  title: string;
  description: string;
  explanation: string;
};

export type AnswerOptionForm = {
  id?: number;
  is_correct: boolean;
  sort_order: number;
  translations: Record<LangCode, { content: string }>;
};

export type QuestionCreateJsonPayload = {
  domain: number;
  subject_ids: number[];
  allow_multiple_correct: boolean;
  active: boolean;
  is_mode_practice: boolean;
  is_mode_exam: boolean;
  translations: Record<LangCode, QuestionTranslationForm>;
  answer_options: Array<AnswerOptionForm>;
  media_asset_ids: number[];
};

export type QuestionDuplicateDraft = {
  domainId: number;
  subjectIds: number[];
  active: boolean;
  isModePractice: boolean;
  isModeExam: boolean;
  translations: Record<LangCode, QuestionTranslationForm>;
  answerOptions: Array<{
    is_correct: boolean;
    sort_order: number;
    translations: Record<LangCode, { content: string }>;
  }>;
  media: Array<{
    id: number;
    kind: MediaAssetDto['kind'];
    sort_order: number;
    file: string | null;
    external_url: string | null;
  }>;
};

@Injectable({providedIn: 'root'})
export class QuestionService {
  private duplicateDraft: QuestionDuplicateDraft | null = null;

  constructor(private api: QuestionApi, private router: Router) {
  }

  list(params?: {
    search?: string;
    subjectId?: number;
    domainId?: number;
    active?: boolean;
    isModePractice?: boolean;
    isModeExam?: boolean;
  }): Observable<QuestionReadDto[]> {
    const requestParams: QuestionListRequestParams = {
      active: params?.active,
      search: params?.search,
      domain: params?.domainId,
      isModePractice: params?.isModePractice,
      isModeExam: params?.isModeExam,
    };

    return this.api.questionList(requestParams).pipe(map((response) => response.results ?? []));
  }

  retrieve(questionId: number): Observable<QuestionReadDto> {
    const requestParams: QuestionRetrieveRequestParams = {questionId};
    return this.api.questionRetrieve(requestParams);
  }

  create(question: QuestionWritePayloadRequestDto): Observable<QuestionReadDto> {
    const requestParams: QuestionCreateRequestParams = {
      questionWritePayloadRequestDto: question,
    };
    return this.api.questionCreate(requestParams);
  }

  update(qurp: QuestionUpdateRequestParams): Observable<QuestionReadDto> {
    return this.api.questionUpdate(qurp);
  }

  updatePartial(questionId: number, payload: PatchedQuestionPartialWritePayloadRequestDto): Observable<QuestionReadDto> {
    const requestParams: QuestionPartialUpdateRequestParams = {
      questionId,
      patchedQuestionPartialWritePayloadRequestDto: payload,
    };
    return this.api.questionPartialUpdate(requestParams);
  }

  delete(questionId: number): Observable<void> {
    const requestParams: QuestionDestroyRequestParams = {questionId};
    return this.api.questionDestroy(requestParams).pipe(map(() => void 0));
  }

  goList(): void {
    this.router.navigate(ROUTES.question.list());
  }

  goNew(domainId?: number): void {
    this.router.navigate(ROUTES.question.add(), {
      queryParams: domainId ? {domainId} : undefined,
    });
  }

  duplicateToNew(question: QuestionReadDto): void {
    this.duplicateDraft = {
      domainId: question.domain.id,
      subjectIds: question.subjects.map((subject) => subject.id),
      active: !!question.active,
      isModePractice: !!question.is_mode_practice,
      isModeExam: !!question.is_mode_exam,
      translations: Object.fromEntries(
        Object.entries(question.translations ?? {}).map(([lang, value]) => [
          lang,
          {
            title: value?.title ?? '',
            description: value?.description ?? '',
            explanation: value?.explanation ?? '',
          },
        ]),
      ) as Record<LangCode, QuestionTranslationForm>,
      answerOptions: [...(question.answer_options ?? [])]
        .sort((left, right) => (left.sort_order ?? left.id) - (right.sort_order ?? right.id))
        .map((answer, index) => ({
          is_correct: !!answer.is_correct,
          sort_order: answer.sort_order ?? index + 1,
          translations: Object.fromEntries(
            Object.entries(answer.translations ?? {}).map(([lang, value]) => [
              lang,
              {content: value?.content ?? ''},
            ]),
          ) as Record<LangCode, { content: string }>,
        })),
      media: (question.media ?? []).map((media, index) => ({
        id: media.asset.id,
        kind: media.asset.kind,
        sort_order: media.sort_order ?? index + 1,
        file: media.asset.file ?? null,
        external_url: media.asset.external_url ?? null,
      })),
    };

    this.goNew(question.domain.id);
  }

  consumeDuplicateDraft(): QuestionDuplicateDraft | null {
    const draft = this.duplicateDraft;
    this.duplicateDraft = null;
    return draft;
  }

  goEdit(questionId: number): void {
    this.router.navigate(ROUTES.question.edit(questionId));
  }

  goView(questionId: number): void {
    this.router.navigate(ROUTES.question.view(questionId));
  }

  goDelete(questionId: number): void {
    this.router.navigate(ROUTES.question.delete(questionId));
  }

  goBack(): void {
    this.router.navigate(ROUTES.question.list());
  }

  goSubjectEdit(subjectId: number): void {
    this.router.navigate(ROUTES.subject.edit(subjectId));
  }

  getQuestionTranslationForm(question: QuestionReadDto, lang: LanguageEnumDto): QuestionTranslationForm {
    const tr = question.translations as Record<string, QuestionTranslationForm> | undefined;
    return (
      selectTranslation<QuestionTranslationForm>(tr ?? {}, lang) ??
      {title: '', description: '', explanation: ''}
    );
  }

  questionMediaCreate(param: QuestionMediaCreateRequestParams): Observable<MediaAssetDto> {
    return this.api.questionMediaCreate(param);
  }
}
