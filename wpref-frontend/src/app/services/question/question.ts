import {Injectable} from '@angular/core';
import {Router} from '@angular/router';
import {map, Observable} from 'rxjs';

import {ROUTES} from '../../app.routes-paths';

import {
  LanguageEnumDto, MediaAssetDto,
  QuestionApi,
  QuestionCreateRequestParams, QuestionMediaCreateRequestParams,
  QuestionReadDto,
  QuestionUpdateRequestParams,
  QuestionWriteRequestDto,
} from '../../api/generated';

import {LangCode} from '../translation/translation';
import {MediaSelectorValue} from '../../components/media-selector/media-selector';
import {FormArray, FormControl, FormGroup} from '@angular/forms';
import {selectTranslation} from '../../shared/i18n/select-translation';

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


@Injectable({providedIn: 'root'})
export class QuestionService {
  constructor(private api: QuestionApi, private router: Router) {
  }

  // ==========
  // API
  // ==========

  list(params?: { search?: string; subjectId?: number; domainId?: number }): Observable<QuestionReadDto[]> {
    // si ton client généré n'expose pas ces params,
    // garde "as any" mais idéalement adapte aux vrais noms
    return this.api.questionList({
      search: params?.search,
      subjectId: params?.subjectId,
      domainId: params?.domainId,
    } as any);
  }

  retrieve(questionId: number): Observable<QuestionReadDto> {
    return this.api.questionRetrieve({questionId} as any);
  }

  create(qwrdto: QuestionWriteRequestDto): Observable<QuestionReadDto> {
    console.log(qwrdto);
    return this.api.questionCreate({questionWriteRequestDto:qwrdto} as QuestionCreateRequestParams);
  }

  update(qurp: QuestionUpdateRequestParams): Observable<QuestionReadDto> {
    return this.api.questionUpdate(qurp);
  }

  delete(questionId: number): Observable<void> {
    return this.api.questionDestroy({questionId} as any).pipe(map(() => void 0));
  }

  // ==========
  // Navigation
  // ==========

  goList(): void {
    this.router.navigate(ROUTES.question.list());
  }

  goNew(domainId?: number): void {
    this.router.navigate(ROUTES.question.add(), {
      queryParams: domainId ? {domainId} : undefined,
    });
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

  // ==========
  // Builders
  // ==========

  getQuestionTranslationForm(question: QuestionReadDto, lang: LanguageEnumDto): QuestionTranslationForm {
    const tr = question.translations as Record<string, QuestionTranslationForm> | undefined;
    return (
      selectTranslation<QuestionTranslationForm>(tr ?? {}, lang) ??
      {title: '', description: '', explanation: ''}
    );
  }

  questionMediaCreate(param:QuestionMediaCreateRequestParams):Observable<MediaAssetDto> {
    return this.api.questionMediaCreate(param);
  }
}
