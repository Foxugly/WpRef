import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Router } from '@angular/router';
import { Observable } from 'rxjs';
import {environment, LangCode} from '../../../environments/environment';
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

  constructor(private http: HttpClient, private router: Router) {}

  list(params?: { search?: string }): Observable<Question[]> {
  return this.http.get<Question[]>(
    `${this.base}${this.questionPath}`,
    {
      params: params?.search ? { search: params.search } : {}
    }
  );
}

  create(data:QuestionCreatePayload): Observable<Question> {
    return this.http.post<Question>(`${this.base}${this.questionPath}`, data);
  }

  update(id: number, data: FormData): Observable<Question> {
  return this.http.put<Question>(`${this.base}${this.questionPath}${id}/`, data);
}

  retrieve(id: number): Observable<Question> {
    return this.http.get<Question>(`${this.base}${this.questionPath}${id}/`);
  }

  delete(id: number): Observable<void> {
    return this.http.delete<void>(`${this.base}${this.questionPath}${id}/`);
  }
}
