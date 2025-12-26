import {Injectable} from '@angular/core';
import {map, Observable} from 'rxjs';
import {MediaSelectorValue} from '../../components/media-selector/media-selector';
import {
  QuestionApi,
  QuestionCreateRequestParams,
  QuestionPartialUpdateRequestParams,
  QuestionUpdateRequestParams
} from '../../api/generated/api/question.service';
import {QuestionDto} from '../../api/generated/model/question';
import {ROUTES} from '../../app.routes-paths'
import {Router} from '@angular/router';
import {QuestionAnswerOptionDto} from '../../api/generated';

type QuestionUpdateBodyParams = Omit<QuestionUpdateRequestParams, 'questionId'>;
type QuestionPartialBodyParams = Omit<QuestionPartialUpdateRequestParams, 'questionId'>;



export interface QuestionFormValue {
  title: string;
  description: string;
  explanation: string;
  allow_multiple_correct: boolean;
  active: boolean;
  is_mode_practice: boolean;
  is_mode_exam: boolean;

  subjectIds: number[];

  answerOptions: QuestionAnswerOptionDto[];

  media: MediaSelectorValue[]; // inclut File éventuel
}

export type QuestionCreatePayload = QuestionFormValue;
export type QuestionUpdatePayload = Partial<QuestionFormValue>;


@Injectable({providedIn: 'root',})
export class QuestionService {
  constructor(private api: QuestionApi, private router: Router) {
  }

  // LIST
  list(params?: { search?: string }): Observable<Array<QuestionDto>> {
    return this.api.questionList({search: params?.search});
  }

  // CREATE (multipart / form)
  create(payload: QuestionCreatePayload): Observable<QuestionDto> {
    const req: QuestionCreateRequestParams = this.toRequestParams(payload);
    return this.api.questionCreate(req);
  }

  // UPDATE (PUT)
  update(questionId: number, payload: QuestionCreatePayload): Observable<QuestionDto> {
    const req: QuestionUpdateBodyParams = this.toRequestParams(payload);
    return this.api.questionUpdate({questionId, ...req});
  }

  // UPDATE (PATCH)
  updatePartial(questionId: number, payload: QuestionUpdatePayload): Observable<QuestionDto> {
    const req: QuestionPartialBodyParams = this.toRequestParamsPartial(payload);
    return this.api.questionPartialUpdate({questionId, ...req});
  }

  // RETRIEVE
  retrieve(questionId: number): Observable<QuestionDto> {
    return this.api.questionRetrieve({questionId});
  }

  // DELETE
  delete(questionId: number): Observable<void> {
    // l'API générée retourne "any" sur delete ; on caste proprement
    return this.api.questionDestroy({questionId}).pipe(map(() => void 0));
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

  private mapAnswerOptions(answerOptions: QuestionAnswerOptionDto[] | undefined) {
    return (answerOptions ?? []).map((opt, index) => ({
      content: opt.content,
      is_correct: !!opt.is_correct,
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

  private toRequestParams(payload: QuestionCreatePayload): QuestionCreateRequestParams {
    const subjectIds = this.cleanIds(payload.subjectIds);

    const answerOptionsPayload = this.mapAnswerOptions(payload.answerOptions);

    const {mediaMeta, mediaFiles} = this.mapMedia(payload.media);

    return {
      title: payload.title ?? '',
      description: payload.description ?? '',
      // explanation: payload.explanation ?? '', // ajoute si ton RequestParams le supporte
      subjectIds, // ou subject_ids selon ton généré
      answerOptions: JSON.stringify(answerOptionsPayload),
      media: JSON.stringify(mediaMeta),

      // ✅ N fichiers (selon le nom généré)
      mediaFiles, // <— si ton generated RequestParams expose un champ array de fichiers
    };
  }

  private toRequestParamsPartial(payload: QuestionUpdatePayload): QuestionPartialBodyParams {
    const out: QuestionPartialBodyParams = {};

    if (payload.title !== undefined) out.title = payload.title;
    if (payload.description !== undefined) out.description = payload.description;
    // if (payload.explanation !== undefined) out.explanation = payload.explanation;
    if (payload.subjectIds !== undefined) {
      out.subjectIds = this.cleanIds(payload.subjectIds);
    }

    if (payload.answerOptions !== undefined) {
      out.answerOptions = JSON.stringify(this.mapAnswerOptions(payload.answerOptions));
    }

    if (payload.media !== undefined) {
      const {mediaMeta, mediaFiles} = this.mapMedia(payload.media);
      out.media = JSON.stringify(mediaMeta);
      out.mediaFiles = mediaFiles; // ✅ si supporté par le client généré
    }

    return out;
  }

}
