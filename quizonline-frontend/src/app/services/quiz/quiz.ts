import {Injectable} from '@angular/core';
import {HttpClient} from '@angular/common/http';
import {Router} from '@angular/router';
import {map, Observable, of, switchMap} from 'rxjs';
import {
  CreateQuizInputRequestDto,
  GenerateFromSubjectsInputRequestDto,
  PaginatedQuizAssignmentListListDto,
  QuestionApi,
  QuizAnswerApi,
  QuizAssignmentListDto,
  QuizApi,
  QuizDto,
  QuizListDto,
  QuizQuestionAnswerDto,
  QuizQuestionAnswerWriteRequestDto,
  QuizTemplateApi,
  QuizTemplateDto,
  QuizTemplateGenerateFromSubjectsCreateRequestParams,
} from '../../api/generated';
import {resolveApiBaseUrl} from '../../shared/api/runtime-api-base-url';

export interface QuizSubjectCreatePayload {
  title: string;
  subject_ids: number[];
  max_questions: number;
  with_duration: boolean;
  duration: number | null;
}

export type QuizTemplateAssignmentSessionDto = QuizAssignmentListDto;

@Injectable({
  providedIn: 'root',
})
export class QuizService {
  private readonly apiBaseUrl = `${resolveApiBaseUrl().replace(/\/+$/, '')}/api`;

  constructor(
    private quizApi: QuizApi,
    private qtApi: QuizTemplateApi,
    private questionApi: QuestionApi,
    private answerApi: QuizAnswerApi,
    private http: HttpClient,
    private router: Router,
  ) {}

  goList(): void {
    this.router.navigate(['/quiz', 'list']);
  }

  startQuiz(id: number): Observable<QuizDto> {
    return this.quizApi.quizStartCreate({quizId: id});
  }

  createQuizFromTemplate(quizTemplateId: number): Observable<QuizDto> {
    return this.quizApi.quizCreate({
      createQuizInputRequestDto: {quiz_template_id: quizTemplateId},
    });
  }

  closeQuiz(id: number): Observable<QuizDto> {
    return this.quizApi.quizCloseCreate({quizId: id});
  }

  goStart(id: number, onError?: (err: unknown) => void): void {
    this.startQuiz(id).subscribe({
      next: (session: QuizDto): void => {
        this.goQuestion(session.id);
      },
      error: (err: unknown): void => {
        if (onError) {
          onError(err);
        } else {
          console.error('Erreur startQuizSession', err);
        }
      },
    });
  }

  goView(id: number): void {
    this.router.navigate(['/quiz', id]);
  }

  goCompose(): void {
    this.router.navigate(['/quiz', 'add']);
  }

  goQuestion(id: number): void {
    this.router.navigate(['/quiz', id, 'questions']);
  }

  getQuestionCountBySubjects(subjectIds: number[]): Observable<{ count: number }> {
    if (!subjectIds.length) {
      return of({count: 0});
    }

    return this.questionApi.questionList({
      active: true,
      isModePractice: true,
      subjectIds,
      pageSize: 1,
    }).pipe(
      map((response) => ({count: response.count})),
    );
  }

  generateQuiz(payload: GenerateFromSubjectsInputRequestDto): Observable<QuizDto> {
    const params: QuizTemplateGenerateFromSubjectsCreateRequestParams = {
      generateFromSubjectsInputRequestDto: payload,
    };
    return this.qtApi.quizTemplateGenerateFromSubjectsCreate(params).pipe(
      switchMap((quizTemplate) => this.createQuizFromTemplate(quizTemplate.id)),
    );
  }

  listQuiz(params?: {name?: string; search?: string}): Observable<QuizListDto[]> {
    return this.quizApi.quizList({name: params?.name, search: params?.search}).pipe(
      map((response) => response.results ?? []),
    );
  }

  listTemplates(): Observable<QuizTemplateDto[]> {
    return this.qtApi.quizTemplateList().pipe(map((response) => response.results ?? []));
  }

  assignTemplateToUsers(quizTemplateId: number, userIds: number[]): Observable<QuizListDto[]> {
    return this.http.post<QuizListDto[]>(`${this.apiBaseUrl}/quiz/bulk-create-from-template/`, {
      quiz_template_id: quizTemplateId,
      user_ids: userIds,
    });
  }

  listTemplateSessions(quizTemplateId: number): Observable<QuizAssignmentListDto[]> {
    return this.qtApi.quizTemplateSessionsList({qtId: quizTemplateId}).pipe(
      map((response: QuizAssignmentListDto[] | PaginatedQuizAssignmentListListDto) => {
        if (Array.isArray(response)) {
          return response;
        }
        return response.results ?? [];
      }),
    );
  }

  deleteQuiz(id: number): Observable<void> {
    return this.quizApi.quizDestroy({quizId: id}).pipe(
      map(() => void 0),
    );
  }

  retrieveQuiz(id: number): Observable<QuizDto> {
    return this.quizApi.quizRetrieve({quizId: id});
  }

  saveAnswer(
    quizId: number,
    payload: QuizQuestionAnswerWriteRequestDto,
  ): Observable<QuizQuestionAnswerDto> {
    if (payload.question_order == null) {
      throw new Error('question_order is required');
    }

    return this.answerApi.quizAnswerCreate({quizId, quizQuestionAnswerWriteRequestDto: payload});
  }

  listAnswers(quizId: number): Observable<QuizQuestionAnswerDto[]> {
    return this.answerApi.quizAnswerList({quizId}).pipe(map((response) => response.results ?? []));
  }

  goSubject(): void {
    this.router.navigate(['/quiz/quick']);
  }
}
