import {Injectable} from '@angular/core';
import {HttpClient} from '@angular/common/http';
import {Router} from '@angular/router';
import {Observable} from 'rxjs';
import {environment} from '../../../environments/environment';
import {Subject} from '../subject/subject'
import {MediaSelectorValue} from '../../components/media-selector/media-selector';

export interface Question {
  id: number;
  title: string;
  description: string;
  explanation: string;
  allow_multiple_correct: boolean;
  is_mode_practice: boolean;
  is_mode_exam: boolean;
  subjects: Subject[];
  media: MediaSelectorValue[];
  answer_options: AnswerOption[];
  created_at: string;
}

export interface AnswerOption {
  id?: number;
  content: string;
  is_correct: boolean;
  sort_order: number;
}

export interface QuestionCreatePayload {
  title: string;
  description: string;
  explanation: string;
  allow_multiple_correct: boolean;
  is_mode_practice: boolean;
  is_mode_exam: boolean;
  subject_ids: number[];
  answer_options: AnswerOption[];
  media: MediaSelectorValue[];
}

/** Ce qu'on envoie en PUT/PATCH (ici on garde le même) */
export type QuestionUpdatePayload = QuestionCreatePayload;

@Injectable({
  providedIn: 'root',
})
export class QuestionService {
  private base = environment.apiBaseUrl;
  private questionPath = environment.apiQuestionPath;

  constructor(private http: HttpClient, private router: Router) {
  }

  list(params?: { search?: string }): Observable<Question[]> {
    return this.http.get<Question[]>(
      `${this.base}${this.questionPath}`,
      {
        params: params?.search ? {search: params.search} : {}
      }
    );
  }

  create(payload: QuestionCreatePayload): Observable<Question> {
    const formData = this.buildFormData(payload);
    return this.http.post<Question>(`${this.base}${this.questionPath}`, formData);
  }

  update(id: number, payload: QuestionUpdatePayload): Observable<Question> {
    const formData = this.buildFormData(payload);
    return this.http.put<Question>(`${this.base}${this.questionPath}${id}/`, formData);
  }

  retrieve(id: number): Observable<Question> {
    return this.http.get<Question>(`${this.base}${this.questionPath}${id}/`);
  }

  delete(id: number): Observable<void> {
    return this.http.delete<void>(`${this.base}${this.questionPath}${id}/`);
  }


  private buildFormData(payload: QuestionCreatePayload | QuestionUpdatePayload): FormData {
    const formData = new FormData();

    // ---- subject_ids → nombres propres ----
    const subjectIds: number[] = Array.isArray(payload.subject_ids)
      ? payload.subject_ids
        .filter((id: any) => id !== null && id !== undefined && id !== '')
        .map((id: any) => Number(id))
        .filter((id: number) => Number.isFinite(id))
      : [];

    // ---- réponses ----
    const answerOptions: AnswerOption[] = payload.answer_options ?? [];

    const answerOptionsPayload = answerOptions.map((opt, index) => ({
      content: opt.content,
      is_correct: !!opt.is_correct,
      sort_order: opt.sort_order ?? index + 1,
    }));

    // ---- médias ----
    const mediaItems: MediaSelectorValue[] = Array.isArray(payload.media)
      ? payload.media
      : [];

    const mediaPayload = mediaItems.map((m, index) => ({
      id: m.id ?? null,
      kind: m.kind,
      external_url: m.external_url ?? null,
      sort_order: m.sort_order ?? index + 1,
      has_file: m.file instanceof File,
    }));
    // ---- champs simples ----
    formData.append('title', payload.title ?? '');
    formData.append('description', payload.description ?? '');
    formData.append('explanation', payload.explanation ?? '');
    formData.append('allow_multiple_correct', String(!!payload.allow_multiple_correct));
    formData.append('is_mode_practice', String(!!payload.is_mode_practice));
    formData.append('is_mode_exam', String(!!payload.is_mode_exam));
    // subject_ids : plusieurs valeurs
    subjectIds.forEach((id: number) => {
      formData.append('subject_ids', String(id));
    });
    // réponses & médias en JSON
    formData.append('answer_options', JSON.stringify(answerOptionsPayload));
    formData.append('media', JSON.stringify(mediaPayload));

    // fichiers
    mediaItems.forEach((m) => {
      if ((m.kind === 'image' || m.kind === 'video') && m.file instanceof File) {
        formData.append('media_files', m.file, m.file.name);
      }
    });
    return formData;
  }
}
