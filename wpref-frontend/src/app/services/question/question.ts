import {Injectable} from '@angular/core';
import {map, Observable} from 'rxjs';
import {MediaSelectorValue} from '../../components/media-selector/media-selector';

import {ROUTES} from '../../app.routes-paths'
import {Router} from '@angular/router';
import {
  QuestionAnswerOptionReadDto,
  QuestionReadDto,
  QuestionApi, QuestionListRequestParams, QuestionCreateRequestParams, QuestionUpdateRequestParams,
  QuestionPartialUpdateRequestParams, QuestionRetrieveRequestParams, QuestionDestroyRequestParams
} from '../../api/generated';

export interface QuestionFormValue {
  title: string;
  description: string;
  explanation: string;
  allow_multiple_correct: boolean;
  active: boolean;
  is_mode_practice: boolean;
  is_mode_exam: boolean;

  subjectIds: number[];

  answerOptions: QuestionAnswerOptionReadDto[];

  media: MediaSelectorValue[]; // inclut File éventuel
}

export type QuestionCreatePayload = QuestionFormValue;
export type QuestionUpdatePayload = Partial<QuestionFormValue>;


@Injectable({providedIn: 'root',})
export class QuestionService {
  constructor(private api: QuestionApi, private router: Router) {
  }

  // LIST
  list(params?: { name?: string; search?: string }): Observable<Array<QuestionReadDto>> {
    const payload : QuestionListRequestParams = {title:params?.name, search:params?.search}
    return this.api.questionList(payload);
  }

  // CREATE (multipart / form)
  create(payload: QuestionCreateRequestParams): Observable<QuestionReadDto> {
    return this.api.questionCreate(payload);
  }

  // UPDATE (PUT)
  update(payload: QuestionUpdateRequestParams): Observable<QuestionReadDto> {
    return this.api.questionUpdate(payload);
  }

  // UPDATE (PATCH)
  updatePartial(payload: QuestionPartialUpdateRequestParams): Observable<QuestionReadDto> {
    return this.api.questionPartialUpdate(payload);
  }

  // RETRIEVE
  retrieve(questionId: number): Observable<QuestionReadDto> {
    const payload:QuestionRetrieveRequestParams = {questionId:questionId};
    return this.api.questionRetrieve(payload);
  }

  // DELETE
  delete(questionId: number): Observable<void> {
    const payload:QuestionDestroyRequestParams = {questionId:questionId};
    return this.api.questionDestroy(payload).pipe(map(() => void 0));
  }

  // --------------------------
  // Navigation (UI only)
  // --------------------------
  goBack(): void {
    this.router.navigate(ROUTES.question.list());
  }

  goList(): void {
    this.router.navigate(ROUTES.question.list());
  }

  goView(questionId: number): void {
    this.router.navigate(ROUTES.question.view(questionId));
  }

  goNew(): void {
    this.router.navigate(ROUTES.question.add());
  }

  goEdit(questionId: number): void {
    this.router.navigate(ROUTES.question.edit(questionId));
  }

  goDelete(questionId: number): void {
    this.router.navigate(ROUTES.question.delete(questionId));
  }

  goSubjectEdit(subjectId: number): void {
    this.router.navigate(ROUTES.subject.edit(subjectId));
  }

  private cleanIds(ids: any): number[] {
    return Array.isArray(ids)
      ? ids
        .filter((id) => id !== null && id !== undefined && id !== '')
        .map((id) => Number(id))
        .filter((id) => Number.isFinite(id))
      : [];
  }

  private mapAnswerOptions(answerOptions: QuestionAnswerOptionReadDto[] | undefined) {
    return (answerOptions ?? []).map((opt, index) => ({
      content: opt.content,
     // is_correct: !!opt.is_correct, TODO
      sort_order: opt.sort_order ?? index + 1,
    }));
  }

  /**
   * Construit :
   * - mediaMeta: liste JSON (externals + fichiers)
   * - mediaFiles: File[] dans le même ordre que les entrées "fichier"
   *
   * Variante simple : on ajoute les fichiers comme items kind=image/video sans external_url
   * et on garde l'ordre UI via sort_order.
   *
   * Si tu veux un mapping exact meta ↔ fichier, on peut ajouter file_index dans le JSON.
   */
  private mapMedia(mediaItems: MediaSelectorValue[] | undefined): { mediaMeta: any[]; mediaFiles: File[] } {
    const items = Array.isArray(mediaItems) ? mediaItems : [];

    const mediaFiles: File[] = [];
    const mediaMeta = items.map((m, index) => {
      const sort_order = m.sort_order ?? index + 1;

      if (m.kind === 'external') {
        return {
          kind: 'external',
          external_url: m.external_url ?? null,
          sort_order,
        };
      }

      // image/video
      if (m.file instanceof File) {
        const file_index = mediaFiles.push(m.file) - 1;
        return {
          kind: m.kind,          // 'image' | 'video'
          sort_order,
          file_index,            // ✅ optionnel mais très pratique côté backend
        };
      }

      // image/video sans nouveau fichier (ex: déjà existant côté backend)
      // garde un placeholder sans file_index
      return {
        kind: m.kind,
        sort_order,
      };
    });
    return {mediaMeta, mediaFiles};
  }
}
