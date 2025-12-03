import {Injectable} from '@angular/core';
import {HttpClient} from '@angular/common/http';
import {Router} from '@angular/router';
import {environment} from '../../../environments/environment';
import {Observable} from 'rxjs';
import {Question} from '../question/question';

export interface QuizSubjectCreatePayload {
  subject_ids: number[];
  n_question: number;
  with_timer: boolean;
  timer: number | null;
}

export interface QuizSession {
  id: number;
  user : string;
  title: string;
  is_closed: boolean;
  subject_ids: number[];
  nb_questions : number;
  max_duration : number;
  with_timer: boolean;
  timer: number | null;
  questions: Question[];
  created_at: string;
  started_at: string;
  closed_at: string;
}

@Injectable({
  providedIn: 'root',
})
export class QuizService {
  private base = environment.apiBaseUrl;
  private quizPath = environment.apiQuizPath;

  constructor(private http: HttpClient, private router: Router) {
  }

  goNew():void{
    this.router.navigate(['/quiz/list']);
  }

  goList():void{
    this.router.navigate(['/quiz/list']);
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
}
