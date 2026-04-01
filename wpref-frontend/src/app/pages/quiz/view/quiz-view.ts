import {Component, computed, DestroyRef, inject, OnInit, signal} from '@angular/core';
import {takeUntilDestroyed} from '@angular/core/rxjs-interop';
import {ActivatedRoute} from '@angular/router';
import {finalize} from 'rxjs';
import {Button} from 'primeng/button';
import {TagModule} from 'primeng/tag';
import {QuizDto} from '../../../api/generated';
import {QuizService} from '../../../services/quiz/quiz';
import {UserService} from '../../../services/user/user';
import {logApiError, userFacingApiMessage} from '../../../shared/api/api-errors';

@Component({
  selector: 'app-view',
  imports: [
    Button,
    TagModule,
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

    const facts: Array<{label: string; value: string}> = [
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
    this.quizService.goStart(this.id);
  }

  goQuestion(): void {
    this.quizService.goQuestion(this.id);
  }

  protected formatDateTime(value: string | null | undefined): string {
    if (!value) {
      return QuizView.FALLBACK_LABEL;
    }

    const date = new Date(value);
    if (Number.isNaN(date.getTime())) {
      return QuizView.FALLBACK_LABEL;
    }

    return new Intl.DateTimeFormat(this.userService.currentLang, {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
    }).format(date);
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
