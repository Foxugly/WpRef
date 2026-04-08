import {Component, computed, DestroyRef, inject, OnInit, signal} from '@angular/core';
import {takeUntilDestroyed} from '@angular/core/rxjs-interop';
import {ActivatedRoute} from '@angular/router';
import {finalize} from 'rxjs';
import {QuizDto} from '../../../api/generated';
import {QuizSummaryFact, QuizSummaryHeroComponent} from '../../../components/quiz-summary-hero/quiz-summary-hero';
import {QuizService} from '../../../services/quiz/quiz';
import {UserService} from '../../../services/user/user';
import {logApiError, userFacingApiMessage} from '../../../shared/api/api-errors';
import {formatLocalizedDateTime} from '../../../shared/i18n/date-time';

@Component({
  selector: 'app-view',
  imports: [
    QuizSummaryHeroComponent,
  ],
  templateUrl: './quiz-view.html',
  styleUrl: './quiz-view.scss',
})
export class QuizView implements OnInit {
  private static readonly FALLBACK_LABEL = '-';

  id!: number;
  loading = signal(false);
  error = signal<string | null>(null);
  quizSession = signal<QuizDto | null>(null);

  private readonly route = inject(ActivatedRoute);
  private readonly quizService = inject(QuizService);
  private readonly userService = inject(UserService);
  private readonly destroyRef = inject(DestroyRef);

  readonly status = computed(() => {
    const session = this.quizSession();
    if (!session) {
      return {label: QuizView.FALLBACK_LABEL, severity: 'secondary' as const};
    }
    if (!session.started_at) {
      return {label: 'Pret', severity: 'secondary' as const};
    }
    if (session.can_answer) {
      return {label: 'En cours', severity: 'warn' as const};
    }
    return {label: 'Termine', severity: 'success' as const};
  });
  readonly scoreLabel = computed(() => {
    const session = this.quizSession();
    if (!session || session.earned_score == null || session.max_score == null) {
      return QuizView.FALLBACK_LABEL;
    }
    return `${session.earned_score} / ${session.max_score}`;
  });
  readonly timerLabel = computed(() => {
    const session = this.quizSession();
    if (!session) {
      return QuizView.FALLBACK_LABEL;
    }
    return session.with_duration ? `${session.duration} min` : 'Sans limite';
  });
  readonly scoreMetaLabel = computed(() => {
    const session = this.quizSession();
    if (!session || session.correct_answers == null || session.total_answers == null) {
      return QuizView.FALLBACK_LABEL;
    }

    return `${session.correct_answers} bonnes reponses sur ${session.total_answers}`;
  });
  readonly summaryFacts = computed(() => {
    const session = this.quizSession();
    if (!session) {
      return [];
    }

    const facts: QuizSummaryFact[] = [
      {label: 'Timer', value: this.timerLabel()},
    ];

    if (session.created_at) {
      facts.push({label: 'Cree le', value: this.formatDateTime(session.created_at)});
    }
    if (session.started_at) {
      facts.push({label: 'Demarre le', value: this.formatDateTime(session.started_at)});
    }
    if (!session.can_answer && session.ended_at) {
      facts.push({label: 'Cloture le', value: this.formatDateTime(session.ended_at)});
    }

    return facts;
  });
  readonly canReview = computed(() => {
    const session = this.quizSession();
    if (!session?.started_at) {
      return false;
    }

    return !session.can_answer;
  });

  ngOnInit(): void {
    this.id = Number(this.route.snapshot.paramMap.get('id'));
    if (!this.id || Number.isNaN(this.id)) {
      this.error.set('Identifiant de quiz invalide.');
      return;
    }

    this.loadQuizSession();
  }

  goBack(): void {
    this.quizService.goList();
  }

  goStart(): void {
    this.quizService.goStart(this.id, (err: unknown) => {
      logApiError('quiz.view.start', err);
      this.error.set(userFacingApiMessage(err, 'Impossible de démarrer ce quiz.'));
    });
  }

  goQuestion(): void {
    this.quizService.goQuestion(this.id);
  }

  protected formatDateTime(value: string | null | undefined): string {
    return formatLocalizedDateTime(value, this.userService.currentLang) ?? QuizView.FALLBACK_LABEL;
  }

  private loadQuizSession(): void {
    this.loading.set(true);
    this.error.set(null);

    this.quizService
      .retrieveQuiz(this.id)
      .pipe(
        takeUntilDestroyed(this.destroyRef),
        finalize(() => this.loading.set(false)),
      )
      .subscribe({
        next: (quizSession: QuizDto) => {
          this.quizSession.set(quizSession);
        },
        error: (err: unknown) => {
          logApiError('quiz.view.load-session', err);
          this.error.set(userFacingApiMessage(err, 'Impossible de charger ce quiz.'));
        },
      });
  }
}
