import {Component, DestroyRef, inject, OnInit, signal} from '@angular/core';
import {takeUntilDestroyed} from '@angular/core/rxjs-interop';
import {ActivatedRoute} from '@angular/router';
import {finalize, forkJoin} from 'rxjs';
import {FormsModule} from '@angular/forms';
import {DialogModule} from 'primeng/dialog';
import {TextareaModule} from 'primeng/textarea';
import {ButtonModule} from 'primeng/button';
import {AnswerPayload, QuizQuestionComponent} from '../../../components/quiz-question/quiz-question';
import {QuizNav, QuizNavItem} from '../../../components/quiz-nav/quiz-nav';
import {
  QuizDto,
  QuizQuestionAnswerWriteRequestDto,
} from '../../../api/generated';
import {QuizService} from '../../../services/quiz/quiz';
import {
  applyQuizAnswers,
  buildQuizNavItems,
  findQuizNavItem,
  updateQuizNavItem,
} from '../../../shared/quiz/quiz-session-state';
import {logApiError, userFacingApiMessage} from '../../../shared/api/api-errors';
import {QuizAlertService} from '../../../services/quiz-alert/quiz-alert';

@Component({
  selector: 'app-quiz-question-view',
  imports: [
    FormsModule,
    DialogModule,
    TextareaModule,
    ButtonModule,
    QuizQuestionComponent,
    QuizNav,
  ],
  templateUrl: './question-view.html',
  styleUrl: './question-view.scss',
})
export class QuizQuestionView implements OnInit {
  quiz_id!: number;
  index = 1;
  loading = signal(false);
  error = signal<string | null>(null);
  quizSession = signal<QuizDto | null>(null);
  quizNavItem = signal<QuizNavItem | null>(null);
  quizNavItems = signal<QuizNavItem[]>([]);
  remainingSeconds = signal<number | null>(null);
  autoClosing = signal(false);
  reportDialogVisible = signal(false);
  reportMessage = signal('');
  reportSaving = signal(false);
  protected showCorrect = false;
  protected reviewMode = false;

  private readonly route = inject(ActivatedRoute);
  private readonly quizService = inject(QuizService);
  private readonly quizAlertService = inject(QuizAlertService);
  private readonly destroyRef = inject(DestroyRef);
  private timerId: number | null = null;

  constructor() {
    this.destroyRef.onDestroy(() => this.clearTimer());
  }

  ngOnInit(): void {
    this.quiz_id = Number(this.route.snapshot.paramMap.get('quiz_id'));
    if (!this.quiz_id || Number.isNaN(this.quiz_id)) {
      this.error.set('Identifiant de quiz invalide.');
      return;
    }

    this.loadQuizSession();
  }

  onNextQuestion(payload: AnswerPayload): void {
    if (this.reviewMode) {
      this.goQuestionNext(payload.index);
      return;
    }
    this.persistAnswer(payload, () => {
      this.goQuestionNext(payload.index);
    });
  }

  onPreviousQuestion(payload: AnswerPayload): void {
    if (this.reviewMode) {
      this.goQuestionPrev(payload.index);
      return;
    }
    this.persistAnswer(payload, () => {
      this.goQuestionPrev(payload.index);
    });
  }

  onFinishQuiz(payload: AnswerPayload): void {
    if (this.reviewMode) {
      this.quizService.goView(this.quiz_id);
      return;
    }
    this.persistAnswer(payload, () => {
      this.closeQuizAndRedirect();
    });
  }

  onQuestionSelected(index: number): void {
    this.changeQuestion(index);
  }

  goBackToQuiz(): void {
    this.quizService.goView(this.quiz_id);
  }

  openReportDialog(): void {
    this.reportMessage.set('');
    this.reportDialogVisible.set(true);
  }

  closeReportDialog(): void {
    this.reportDialogVisible.set(false);
  }

  submitAlert(): void {
    const current = this.quizNavItem();
    const body = this.reportMessage().trim();
    if (!current || !body) {
      return;
    }

    this.reportSaving.set(true);
    this.quizAlertService.create({
      quiz_id: this.quiz_id,
      question_id: current.question.id,
      body,
    })
      .pipe(
        takeUntilDestroyed(this.destroyRef),
        finalize(() => this.reportSaving.set(false)),
      )
      .subscribe({
        next: () => {
          this.reportDialogVisible.set(false);
          this.reportMessage.set('');
          this.quizAlertService.refreshUnreadCount().subscribe();
        },
        error: (err: unknown) => {
          logApiError('quiz.question.alert', err);
          this.error.set(userFacingApiMessage(err, 'Impossible d’envoyer cette alerte.'));
        },
      });
  }

  toggleFlag(): void {
    this.setCurrentItem({
      flagged: !this.quizNavItem()?.flagged,
    });
  }

  protected hasQuestionNext(index: number): boolean {
    return index < this.quizNavItems().length;
  }

  protected hasQuestionPrev(index: number): boolean {
    return index > 1;
  }

  protected hasTimer(): boolean {
    const session = this.quizSession();
    return Boolean(session?.with_duration && session?.ended_at);
  }

  protected formattedRemainingTime(): string {
    const totalSeconds = this.remainingSeconds();
    if (totalSeconds == null) {
      return '--:--';
    }

    const hours = Math.floor(totalSeconds / 3600);
    const minutes = Math.floor((totalSeconds % 3600) / 60);
    const seconds = totalSeconds % 60;

    if (hours > 0) {
      return `${this.padTime(hours)}:${this.padTime(minutes)}:${this.padTime(seconds)}`;
    }

    return `${this.padTime(minutes)}:${this.padTime(seconds)}`;
  }

  private goQuestionNext(index: number): void {
    if (this.hasQuestionNext(index)) {
      this.changeQuestion(index + 1);
    }
  }

  private goQuestionPrev(index: number): void {
    if (this.hasQuestionPrev(index)) {
      this.changeQuestion(index - 1);
    }
  }

  private persistAnswer(payload: AnswerPayload, afterSave?: () => void): void {
    if (this.isAnswerLocked()) {
      this.error.set('Le temps du quiz est écoulé.');
      this.closeQuizAndRedirect(true);
      return;
    }

    const answerPayload: QuizQuestionAnswerWriteRequestDto = {
      question_id: payload.questionId,
      question_order: payload.index,
      selected_options: payload.selectedOptionIds,
    };

    this.quizService
      .saveAnswer(this.quiz_id, answerPayload)
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe({
        next: () => {
          this.setCurrentItem({
            answered: true,
            selectedOptionIds: payload.selectedOptionIds,
          });
          afterSave?.();
        },
        error: (err: unknown): void => {
          logApiError('quiz.question.save-answer', err);
          this.error.set(
            this.isTimedOut()
              ? 'Le temps du quiz est écoulé.'
              : userFacingApiMessage(err, "Impossible d'enregistrer cette réponse."),
          );
          if (this.isTimedOut()) {
            this.closeQuizAndRedirect(true);
          }
        },
      });
  }

  private changeQuestion(index: number): void {
    const item = findQuizNavItem(this.quizNavItems(), index);
    if (!item) {
      return;
    }

    this.index = index;
    this.quizNavItem.set(item);
  }

  private setCurrentItem(changes: Partial<QuizNavItem>): void {
    const current = this.quizNavItem();
    if (!current) {
      return;
    }

    const updatedItems = updateQuizNavItem(this.quizNavItems(), current.index, changes);
    this.quizNavItems.set(updatedItems);
    this.quizNavItem.set(findQuizNavItem(updatedItems, current.index));
  }

  private loadQuizSession(): void {
    this.loading.set(true);
    this.error.set(null);

    forkJoin({
      session: this.quizService.retrieveQuiz(this.quiz_id),
      answers: this.quizService.listAnswers(this.quiz_id),
    })
      .pipe(
        takeUntilDestroyed(this.destroyRef),
        finalize(() => this.loading.set(false)),
      )
      .subscribe({
        next: ({session, answers}) => {
          const readonlySession = !!session.started_at && !session.can_answer;
          this.reviewMode = readonlySession;
          this.showCorrect = session.answer_correctness_state === 'full';

          const navItems = applyQuizAnswers(buildQuizNavItems(session.questions), answers);
          if (!navItems.length) {
            this.error.set('Ce quiz ne contient aucune question.');
            return;
          }

          this.quizSession.set(session);
          this.quizNavItems.set(navItems);
          this.syncTimer(session);
          this.changeQuestion(1);
        },
        error: (err: unknown) => {
          logApiError('quiz.question.load-session', err);
          this.error.set(userFacingApiMessage(err, 'Impossible de charger ce quiz.'));
        },
      });
  }

  private syncTimer(session: QuizDto): void {
    this.clearTimer();

    if (!session.with_duration || !session.ended_at || !session.active) {
      this.remainingSeconds.set(null);
      return;
    }

    this.updateRemainingSeconds(session.ended_at);
    if ((this.remainingSeconds() ?? 0) <= 0) {
      this.handleTimerExpired();
      return;
    }

    this.timerId = window.setInterval(() => {
      const currentSession = this.quizSession();
      if (!currentSession?.ended_at) {
        this.clearTimer();
        return;
      }

      this.updateRemainingSeconds(currentSession.ended_at);
      if ((this.remainingSeconds() ?? 0) <= 0) {
        this.handleTimerExpired();
      }
    }, 1000);
  }

  private updateRemainingSeconds(endedAt: string): void {
    const targetTime = new Date(endedAt).getTime();
    if (Number.isNaN(targetTime)) {
      this.remainingSeconds.set(null);
      return;
    }

    const deltaMs = targetTime - Date.now();
    this.remainingSeconds.set(Math.max(0, Math.ceil(deltaMs / 1000)));
  }

  private handleTimerExpired(): void {
    this.clearTimer();
    this.remainingSeconds.set(0);
    this.error.set('Le temps du quiz est écoulé. Clôture automatique en cours.');
    this.closeQuizAndRedirect(true);
  }

  private closeQuizAndRedirect(triggeredByTimer = false): void {
    if (this.autoClosing()) {
      return;
    }

    this.autoClosing.set(true);
    this.clearTimer();

    this.quizService
      .closeQuiz(this.quiz_id)
      .pipe(
        takeUntilDestroyed(this.destroyRef),
        finalize(() => this.autoClosing.set(false)),
      )
      .subscribe({
        next: (session) => {
          this.quizSession.set(session);
          this.quizService.goView(this.quiz_id);
        },
        error: (err: unknown): void => {
          logApiError('quiz.question.close-quiz', err);
          if (triggeredByTimer) {
            this.quizService.goView(this.quiz_id);
            return;
          }
          this.error.set(userFacingApiMessage(err, 'Impossible de clôturer ce quiz.'));
        },
      });
  }

  private clearTimer(): void {
    if (this.timerId == null) {
      return;
    }

    window.clearInterval(this.timerId);
    this.timerId = null;
  }

  private isAnswerLocked(): boolean {
    return this.reviewMode || this.autoClosing() || this.isTimedOut();
  }

  private isTimedOut(): boolean {
    const session = this.quizSession();
    if (!session?.with_duration || !session.ended_at) {
      return false;
    }

    return new Date(session.ended_at).getTime() <= Date.now();
  }

  private padTime(value: number): string {
    return value.toString().padStart(2, '0');
  }

}
