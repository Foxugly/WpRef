import {Injectable} from '@angular/core';
import {HttpClient} from '@angular/common/http';
import {Router} from '@angular/router';
import {environment} from '../../../environments/environment';
import {Observable} from 'rxjs';
import {Question} from '../question/question';
import {AnswerPayload} from '../../components/quiz-question/quiz-question';

export interface QuizSubjectCreatePayload {
  subject_ids: number[];
  max_questions: number;
  with_duration: boolean;
  duration: number | null;
}

export interface QuizSession {
  id: number;
  user: string;
  title: string;
  //description:string;
  is_closed: boolean;
  subject_ids: number[];
  mode: string;
  max_questions: number;
  duration: number;
  with_duration: boolean;
  timer: number | null;
  questions: Question[];
  created_at: string;
  started_at: string;
  expired_at: string;
}

export interface QuizAttemptOptionDto {
  id: number;
  content: string;
  is_selected: boolean;
  is_correct?: boolean;
}

export interface QuizAttemptDetailDto {
  quiz_id: string;
  quiz_title: string;
  question_id: number;
  question_order: number;
  title: string;
  description: string;
  options: QuizAttemptOptionDto[];
}


@Injectable({
  providedIn: 'root',
})
export class QuizService {
  private base = environment.apiBaseUrl;
  private quizPath = environment.apiQuizPath;
  private payload: QuizSubjectCreatePayload | null = null;

  constructor(private http: HttpClient, private router: Router) {
  }

  goList(): void {
    this.router.navigate(['/quiz', 'list']);
  }

  startQuizSession(id: number): Observable<QuizSession> {
    return this.http.post<QuizSession>(`${this.base}${this.quizPath}${id}/start/`, {});
  }

  goStart(id: number): void {
    this.startQuizSession(id).subscribe({
      next: (session) => {
        this.router.navigate(['/quiz', id, 'questions']);
      },
      error: (err) => {
        console.error('Erreur startQuizSession', err);
      },
    });
  }


  goView(id: number): void {
    this.router.navigate(['/quiz', id]);
  }

  goQuestion(id: number): void {
    this.router.navigate(['/quiz', id, 'questions']);
  }

  getQuestionCountBySubjects(subjectIds: number[]) {
    return this.http.post<{ count: number }>(
      `${this.base}quiz/subject-question-count/`,
      {subject_ids: subjectIds}
    );
  }

  generateQuizSession(qscp: QuizSubjectCreatePayload) {
    return this.http.post<{ count: number }>(`${this.base}quiz/generate/`, qscp);
  }

  listQuizSession(params?: { search?: string }): Observable<QuizSession[]> {
    return this.http.get<QuizSession[]>(
      `${this.base}${this.quizPath}`,
      {
        params: params?.search ? {search: params.search} : {}
      }
    );
  }

  retrieveSession(id: number): Observable<QuizSession> {
    return this.http.get<QuizSession>(`${this.base}${this.quizPath}${id}/summary/`);
  }

  saveAnswer(quiz_id: number, payload: AnswerPayload) {
    const url = `${this.base}${this.quizPath}${quiz_id}/attempt/${payload.index}/`;
    const mypayload = {
      "selected_option_ids": payload.selectedOptionIds
    }
    return this.http.post<any>(url, mypayload, {observe: 'response'});
  }


  getAnswer(quiz_id: number, questionOrder: number) {
    const url = `${this.base}${this.quizPath}${quiz_id}/attempt/${questionOrder}/`;
    return this.http.get<QuizAttemptDetailDto>(url);
  }
}
