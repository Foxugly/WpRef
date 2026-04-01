import {Injectable} from '@angular/core';
import {Router} from '@angular/router';
import {map, Observable, of, switchMap} from 'rxjs';
import {
  CreateQuizInputRequestDto,
  GenerateFromSubjectsInputRequestDto,
  QuestionApi,
  QuizAnswerApi,
  QuizApi,
  QuizDto,
  QuizListDto,
  QuizQuestionAnswerDto,
  QuizQuestionAnswerWriteRequestDto,
  QuizTemplateApi,
  QuizTemplateDto,
  QuizTemplateGenerateFromSubjectsCreateRequestParams,
} from '../../api/generated';

export interface QuizSubjectCreatePayload {
  title: string;
  subject_ids: number[];
  max_questions: number;
  with_duration: boolean;
  duration: number | null;
}

@Injectable({
  providedIn: 'root',
})
export class QuizService {
  constructor(
    private quizApi: QuizApi,
    private qtApi: QuizTemplateApi,
    private questionApi: QuestionApi,
    private answerApi: QuizAnswerApi,
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

  goStart(id: number): void {
    this.startQuiz(id).subscribe({
      next: (session: QuizDto): void => {
        this.goQuestion(session.id);
      },
      error: (err: unknown): void => {
        console.error('Erreur startQuizSession', err);
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

    const selected = new Set(subjectIds);
    return this.questionApi.questionList({active: true}).pipe(
      map((questions) => ({
        count: questions.filter((question) =>
          question.subjects.some((subject) => selected.has(subject.id)),
        ).length,
      })),
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
    return this.quizApi.quizList({name: params?.name, search: params?.search});
  }

  listTemplates(): Observable<QuizTemplateDto[]> {
    return this.qtApi.quizTemplateList();
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
    return this.answerApi.quizAnswerList({quizId});
  }

  goSubject(): void {
    this.router.navigate(['/quiz/quick']);
  }
}
