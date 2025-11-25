import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Router } from '@angular/router';
import { Observable } from 'rxjs';
import {environment, LangCode} from '../../../environments/environment';
import {Subject} from '../subject/subject'

export interface Question {
  id: number;
  title: string;
  description: string;
  explanation: string;
  allow_multiple_correct: boolean;
  subjects: Subject[];
  media: QuestionMedia[];
  answer_options: AnswerOption[];
  created_at: string;
}

export interface QuestionMedia {
  id?: number;
  kind: 'image' | 'video';
  file?: string | null;
  external_url?: string | null;
  caption: string;
  sort_order: number;
}

export interface AnswerOption {
  id?: number;
  content: string;
  is_correct: boolean;
  sort_order: number;
}


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

  create(data: Partial<Question>): Observable<Question> {
    return this.http.post<Question>(`${this.base}${this.questionPath}`, data);
  }

  update(id: number, data: Partial<Question>): Observable<Question> {
  return this.http.put<Question>(`${this.base}${this.questionPath}${id}/`, data);
}

  retrieve(id: number): Observable<Question> {
    return this.http.get<Question>(`${this.base}${this.questionPath}${id}/`);
  }

  delete(id: number): Observable<void> {
    return this.http.delete<void>(`${this.base}${this.questionPath}${id}/`);
  }
}
