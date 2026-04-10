import {CommonModule} from '@angular/common';
import {Component, computed, DestroyRef, inject, OnInit, signal} from '@angular/core';
import {takeUntilDestroyed} from '@angular/core/rxjs-interop';
import {FormsModule} from '@angular/forms';
import {ActivatedRoute, Router} from '@angular/router';
import {catchError, finalize, forkJoin, map, of, switchMap} from 'rxjs';
import {ButtonModule} from 'primeng/button';
import {InputTextModule} from 'primeng/inputtext';
import {TableModule} from 'primeng/table';
import {QuizAssignmentListDto, QuizTemplateDto} from '../../../api/generated';
import {ROUTES} from '../../../app.routes-paths';
import {QuizService} from '../../../services/quiz/quiz';
import {logApiError, userFacingApiMessage} from '../../../shared/api/api-errors';

@Component({
  selector: 'app-quiz-template-results-page',
  standalone: true,
  imports: [CommonModule, FormsModule, ButtonModule, InputTextModule, TableModule],
  templateUrl: './quiz-template-results.html',
  styleUrl: './quiz-template-results.scss',
})
export class QuizTemplateResultsPage implements OnInit {
  readonly loading = signal(true);
  readonly error = signal<string | null>(null);
  readonly template = signal<QuizTemplateDto | null>(null);
  readonly sessions = signal<QuizAssignmentListDto[]>([]);
  readonly search = signal('');

  private readonly route = inject(ActivatedRoute);
  private readonly router = inject(Router);
  private readonly quizService = inject(QuizService);
  private readonly destroyRef = inject(DestroyRef);

  readonly filteredSessions = computed(() => {
    const term = this.normalize(this.search());
    if (!term) {
      return this.sessions();
    }

    return this.sessions().filter((quiz) =>
      this.normalize([
        quiz.user_summary?.username,
        quiz.quiz_template_title,
        quiz.mode,
        quiz.created_at,
        quiz.started_at,
        quiz.ended_at,
        String(quiz.id),
      ].join(' ')).includes(term),
    );
  });

  ngOnInit(): void {
    this.load();
  }

  load(): void {
    this.loading.set(true);
    this.error.set(null);

    this.route.paramMap.pipe(
      takeUntilDestroyed(this.destroyRef),
      map((params) => Number(params.get('templateId'))),
      switchMap((templateId) => {
        if (!Number.isFinite(templateId) || templateId <= 0) {
          throw new Error('Invalid template id');
        }
        return forkJoin({
          sessions: this.quizService.listTemplateSessions(templateId),
          template: this.quizService.listTemplates().pipe(
            map((templates) => templates.find((item) => item.id === templateId) ?? null),
            catchError(() => of(null)),
          ),
        });
      }),
      finalize(() => this.loading.set(false)),
    ).subscribe({
      next: ({sessions, template}) => {
        this.sessions.set(sessions);
        this.template.set(template);
      },
      error: (err: unknown) => {
        logApiError('quiz.template-results.load', err);
        this.sessions.set([]);
        this.template.set(null);
        this.error.set(userFacingApiMessage(err, 'Impossible de charger les resultats des quiz envoyes.'));
      },
    });
  }

  goBack(): void {
    void this.router.navigate(ROUTES.quiz.list());
  }

  goView(quizId: number): void {
    void this.router.navigate(ROUTES.quiz.view(quizId));
  }

  goDelete(quizId: number): void {
    const templateId = this.template()?.id ?? null;
    void this.router.navigate(ROUTES.quiz.deleteSession(quizId, templateId));
  }

  statusLabel(quiz: QuizAssignmentListDto): string {
    if (quiz.ended_at) {
      return 'Repondu';
    }
    if (quiz.started_at) {
      return 'En cours';
    }
    return 'Non commence';
  }

  formatDateTime(value: string | null | undefined): string {
    if (!value) {
      return '-';
    }

    const date = new Date(value);
    if (Number.isNaN(date.getTime())) {
      return '-';
    }

    return date.toLocaleString(undefined, {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
    });
  }

  private normalize(value: string | null | undefined): string {
    return (value ?? '').trim().toLocaleLowerCase();
  }
}
