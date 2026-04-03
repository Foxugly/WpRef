import {Injectable, signal} from '@angular/core';
import {HttpClient} from '@angular/common/http';
import {Observable, tap} from 'rxjs';
import {resolveApiBaseUrl} from '../../shared/api/runtime-api-base-url';

export interface AlertUserSummary {
  id: number;
  username: string;
}

export interface QuizAlertMessageDto {
  id: number;
  author: number;
  author_summary: AlertUserSummary | null;
  body: string;
  created_at: string;
  is_mine: boolean;
  is_unread: boolean;
}

export interface QuizAlertThreadListDto {
  id: number;
  quiz: number;
  kind: 'question' | 'assignment';
  question_id: number | null;
  question_order: number | null;
  question_title: string;
  quiz_template_title: string;
  reported_language: string;
  status: 'open' | 'closed';
  reporter_reply_allowed: boolean;
  last_message_at: string;
  created_at: string;
  unread: boolean;
  unread_count: number;
  last_message_preview: string;
}

export interface QuizAlertThreadDetailDto extends QuizAlertThreadListDto {
  reporter: number;
  reporter_summary: AlertUserSummary | null;
  owner: number;
  owner_summary: AlertUserSummary | null;
  closed_at: string | null;
  closed_by: number | null;
  messages: QuizAlertMessageDto[];
  can_reply: boolean;
  can_manage: boolean;
}

export interface QuizAlertCreatePayload {
  quiz_id: number;
  question_id: number;
  body: string;
}

@Injectable({providedIn: 'root'})
export class QuizAlertService {
  readonly unreadCount = signal(0);
  private readonly baseUrl = `${resolveApiBaseUrl().replace(/\/+$/, '')}/api/quiz/alerts`;

  constructor(private readonly http: HttpClient) {}

  list(): Observable<QuizAlertThreadListDto[]> {
    return this.http.get<QuizAlertThreadListDto[]>(`${this.baseUrl}/`);
  }

  retrieve(alertId: number): Observable<QuizAlertThreadDetailDto> {
    return this.http.get<QuizAlertThreadDetailDto>(`${this.baseUrl}/${alertId}/`);
  }

  create(payload: QuizAlertCreatePayload): Observable<QuizAlertThreadDetailDto> {
    return this.http.post<QuizAlertThreadDetailDto>(`${this.baseUrl}/`, payload);
  }

  postMessage(alertId: number, body: string): Observable<QuizAlertMessageDto> {
    return this.http.post<QuizAlertMessageDto>(`${this.baseUrl}/${alertId}/message/`, {body});
  }

  update(alertId: number, payload: {reporter_reply_allowed: boolean}): Observable<QuizAlertThreadDetailDto> {
    return this.http.patch<QuizAlertThreadDetailDto>(`${this.baseUrl}/${alertId}/`, payload);
  }

  close(alertId: number): Observable<QuizAlertThreadDetailDto> {
    return this.http.post<QuizAlertThreadDetailDto>(`${this.baseUrl}/${alertId}/close/`, {});
  }

  reopen(alertId: number): Observable<QuizAlertThreadDetailDto> {
    return this.http.post<QuizAlertThreadDetailDto>(`${this.baseUrl}/${alertId}/reopen/`, {});
  }

  refreshUnreadCount(): Observable<{count: number}> {
    return this.http.get<{count: number}>(`${this.baseUrl}/unread-count/`).pipe(
      tap((response) => this.unreadCount.set(response.count ?? 0)),
    );
  }

  clearUnreadCount(): void {
    this.unreadCount.set(0);
  }
}
