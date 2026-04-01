import {CommonModule} from '@angular/common';
import {Component, DestroyRef, inject, signal, ViewChild} from '@angular/core';
import {takeUntilDestroyed} from '@angular/core/rxjs-interop';
import {ButtonModule} from 'primeng/button';
import {QuizSubjectCreatePayload, QuizService} from '../../../services/quiz/quiz';
import {QuizSubjectForm} from '../subject-form/subject-form';
import {logApiError, userFacingApiMessage} from '../../../shared/api/api-errors';

@Component({
  standalone: true,
  selector: 'app-quiz-quick-page',
  imports: [CommonModule, ButtonModule, QuizSubjectForm],
  templateUrl: './quiz-quick.html',
  styleUrl: './quiz-quick.scss',
})
export class QuizQuickPage {
  @ViewChild(QuizSubjectForm) private subjectForm?: QuizSubjectForm;

  saving = signal(false);
  success = signal<string | null>(null);
  maxQuestions = signal<number | null>(null);

  private readonly quizService = inject(QuizService);
  private readonly destroyRef = inject(DestroyRef);

  onGenerate(payload: QuizSubjectCreatePayload): void {
    this.saving.set(true);
    this.success.set(null);

    this.quizService
      .generateQuiz(payload)
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe({
        next: (quiz) => {
          this.saving.set(false);
          this.quizService.goView(quiz.id);
        },
        error: (err: unknown) => {
          this.saving.set(false);
          logApiError('quiz.quick.generate', err);
          this.success.set(userFacingApiMessage(err, 'Impossible de generer ce quiz.'));
        },
      });
  }

  onSubjectsChange(ids: number[]): void {
    this.quizService
      .getQuestionCountBySubjects(ids)
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe({
        next: (data) => this.maxQuestions.set(data.count),
        error: (err: unknown) => {
          logApiError('quiz.quick.questions-count', err);
          this.maxQuestions.set(null);
        },
      });
  }

  goBack(): void {
    this.quizService.goList();
  }

  submit(): void {
    this.subjectForm?.submitForm();
  }
}
