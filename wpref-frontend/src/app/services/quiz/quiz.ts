import {Injectable} from '@angular/core';
import {Router} from '@angular/router';
import {catchError, Observable, of, switchMap, throwError} from 'rxjs';
import {
  CreateQuizInputRequestDto, GenerateFromSubjectsInputRequestDto,
  QuizAnswerApi,
  QuizApi,
  QuizDto,
  QuizQuestionAnswerDto,
  QuizQuestionAnswerWriteRequestDto,
  QuizTemplateApi, QuizTemplateDto, QuizTemplateGenerateFromSubjectsCreateRequestParams,
  SubjectApi,
} from '../../api/generated';
import {HttpResponse} from '@angular/common/http';


export interface QuizSubjectCreatePayload {
  subject_ids: number[];
  max_questions: number;
  with_duration: boolean;
  duration: number | null;
}

@Injectable({
  providedIn: 'root',
})
export class QuizService {
  constructor(private quizApi: QuizApi,
              private qtApi: QuizTemplateApi,
              private subjectApi: SubjectApi,
              private answerApi: QuizAnswerApi,
              private router: Router) {
  }

  goList(): void {
    this.router.navigate(['/quiz', 'list']);
  }

  startQuiz(id: number, cqir: CreateQuizInputRequestDto): Observable<QuizDto> {
    return this.quizApi.quizStartCreate({quizId: id, createQuizInputRequestDto: cqir});
  }

  goStart(id: number, cqir: CreateQuizInputRequestDto): void {
    this.startQuiz(id, cqir).subscribe({
      next: (session: QuizDto): void => {
        // TODO
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

  getQuestionCountBySubjects(subjectIds: number[]): Observable<{ count: number }> {
    return of({count: 0}); //this.questionApi.questionCountBySubjects(subjectIds); // TODO
  }

  generateQuiz(gen: GenerateFromSubjectsInputRequestDto): Observable<QuizTemplateDto> {
    const payload :QuizTemplateGenerateFromSubjectsCreateRequestParams = {generateFromSubjectsInputRequestDto:gen};
    return this.qtApi.quizTemplateGenerateFromSubjectsCreate(payload)
  }

  listQuiz(params?: {name?: string;  search?: string }): Observable<QuizDto[]> {
    return this.quizApi.quizList({name:params?.name, search:params?.search});
  }

  retrieveQuiz(id: number): Observable<QuizDto> {
    return this.quizApi.quizRetrieve({quizId: id});
  }

  saveAnswer(quizId: number, payload: QuizQuestionAnswerWriteRequestDto) {
    if (payload.question_order == null) {
      return null;
    }
    const questionOrder: number = payload.question_order;
    if (questionOrder == null) {
      return throwError(() => new Error('question_order is required'));
    }

    // 1) On tente de récupérer la réponse existante
    return this.answerApi.quizAnswerRetrieve(
      {quizId, answerId: questionOrder},
      'response'
    ).pipe(
      // 2) Si elle existe => update
      switchMap((resp: HttpResponse<QuizQuestionAnswerDto>) => {
        const body = resp.body;
        if (!body) {
          // sécurité: si backend renvoie 200 sans body, on force le fallback create/update
          return this.answerApi.quizAnswerUpdate(
            {
              quizId,
              answerId: questionOrder,
              quizQuestionAnswerWriteRequestDto: payload,
            },
            'response'
          );
        }

        return this.answerApi.quizAnswerUpdate(
          {
            quizId,
            answerId: body.question_order ?? questionOrder, // ou questionOrder directement
            quizQuestionAnswerWriteRequestDto: payload,
          },
          'response'
        );
      }),

      // 3) Si retrieve échoue (404 typiquement) => create
      catchError((err: any) => {
        // Option: ne créer que si 404, sinon rethrow
        if (err?.status && err.status !== 404) {
          return throwError(() => err);
        }

        return this.answerApi.quizAnswerCreate(
          {quizId, quizQuestionAnswerWriteRequestDto: payload},
          'response'
        );
      })
    );
  }


  getAnswer(quiz_id: number, question_order: number) {
    return this.answerApi.quizAnswerRetrieve({answerId: question_order, quizId: quiz_id})
  }

  goSubject() {
    this.router.navigate(['/quiz/subject']);
  }
}
