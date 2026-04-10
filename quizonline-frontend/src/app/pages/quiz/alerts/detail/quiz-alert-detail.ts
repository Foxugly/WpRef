import {CommonModule} from '@angular/common';
import {Component, DestroyRef, inject, OnInit, signal} from '@angular/core';
import {takeUntilDestroyed} from '@angular/core/rxjs-interop';
import {FormsModule} from '@angular/forms';
import {ActivatedRoute, RouterLink} from '@angular/router';
import {Observable, finalize} from 'rxjs';
import {ButtonModule} from 'primeng/button';
import {CardModule} from 'primeng/card';
import {TextareaModule} from 'primeng/textarea';
import {TagModule} from 'primeng/tag';
import {ToggleSwitchModule} from 'primeng/toggleswitch';
import {LanguageEnumDto} from '../../../../api/generated';
import {ROUTES} from '../../../../app.routes-paths';
import {QuizAlertService, QuizAlertThreadDetailDto} from '../../../../services/quiz-alert/quiz-alert';
import {UserService} from '../../../../services/user/user';
import {logApiError, userFacingApiMessage} from '../../../../shared/api/api-errors';
import {
  canSendReply,
  canShowComposer,
  formatQuizAlertMessageDate,
  isClosedThread,
} from './quiz-alert-detail.helpers';

@Component({
  selector: 'app-quiz-alert-detail',
  standalone: true,
  imports: [
    CommonModule,
    FormsModule,
    RouterLink,
    ButtonModule,
    CardModule,
    TextareaModule,
    TagModule,
    ToggleSwitchModule,
  ],
  templateUrl: './quiz-alert-detail.html',
  styleUrl: './quiz-alert-detail.scss',
})
export class QuizAlertDetail implements OnInit {
  readonly loading = signal(true);
  readonly saving = signal(false);
  readonly thread = signal<QuizAlertThreadDetailDto | null>(null);
  readonly error = signal<string | null>(null);
  readonly replyBody = signal('');

  protected readonly routes = ROUTES;
  private readonly route = inject(ActivatedRoute);
  private readonly quizAlertService = inject(QuizAlertService);
  private readonly destroyRef = inject(DestroyRef);
  private readonly userService = inject(UserService);

  ngOnInit(): void {
    this.load();
  }

  load(): void {
    const alertId = Number(this.route.snapshot.paramMap.get('alertId'));
    if (!alertId || Number.isNaN(alertId)) {
      this.error.set('Identifiant de message invalide.');
      this.loading.set(false);
      return;
    }

    this.loading.set(true);
    this.error.set(null);
    this.quizAlertService.retrieve(alertId)
      .pipe(
        takeUntilDestroyed(this.destroyRef),
        finalize(() => this.loading.set(false)),
      )
      .subscribe({
        next: (thread) => {
          this.thread.set(thread);
          this.quizAlertService.refreshUnreadCount().subscribe({error: () => {}});
        },
        error: (err: unknown) => {
          logApiError('quiz.alerts.detail', err);
          this.error.set(userFacingApiMessage(err, 'Impossible de charger ce message.'));
          this.thread.set(null);
        },
      });
  }

  sendReply(): void {
    const thread = this.thread();
    const body = this.replyBody().trim();
    if (!thread || !body) {
      return;
    }

    this.runThreadRequest(
      this.quizAlertService.postMessage(thread.id, body),
      'quiz.alerts.reply',
      'Impossible d\'envoyer ce message.',
      () => {
        this.replyBody.set('');
        this.load();
      },
    );
  }

  toggleReporterReplyAllowed(allowed: boolean): void {
    const thread = this.thread();
    if (!thread || !thread.can_manage) {
      return;
    }

    this.runThreadRequest(
      this.quizAlertService.update(thread.id, {reporter_reply_allowed: allowed}),
      'quiz.alerts.update',
      'Impossible de modifier cette conversation.',
      (updatedThread) => {
        this.thread.set(updatedThread);
      },
      () => this.load(),
    );
  }

  closeThread(): void {
    const thread = this.thread();
    if (!thread || !thread.can_manage || thread.status === 'closed') {
      return;
    }

    this.runThreadRequest(
      this.quizAlertService.close(thread.id),
      'quiz.alerts.close',
      'Impossible de clôturer cette conversation.',
      (updatedThread) => {
        this.thread.set(updatedThread);
      },
    );
  }

  reopenThread(): void {
    const thread = this.thread();
    if (!thread || !thread.can_manage || thread.status !== 'closed') {
      return;
    }

    this.runThreadRequest(
      this.quizAlertService.reopen(thread.id),
      'quiz.alerts.reopen',
      'Impossible de rouvrir cette conversation.',
      (updatedThread) => {
        this.thread.set(updatedThread);
      },
    );
  }

  statusSeverity(thread: QuizAlertThreadDetailDto): 'success' | 'danger' | 'contrast' {
    return thread.status === 'open' ? 'success' : 'contrast';
  }

  formatMessageDate(value: string): string {
    return formatQuizAlertMessageDate(value, this.currentLang());
  }

  isClosed(thread: QuizAlertThreadDetailDto | null): boolean {
    return isClosedThread(thread);
  }

  canShowComposer(thread: QuizAlertThreadDetailDto | null): boolean {
    return canShowComposer(thread);
  }

  canSendReply(thread: QuizAlertThreadDetailDto | null): boolean {
    return canSendReply(thread);
  }

  counterpartUsername(thread: QuizAlertThreadDetailDto): string {
    const me = this.userService.currentUser();
    if (!me) {
      return '';
    }
    if (thread.owner === me.id) {
      return thread.reporter_summary?.username || '';
    }
    return thread.owner_summary?.username || '';
  }

  isAssignmentIntroMessage(thread: QuizAlertThreadDetailDto, messageId: number): boolean {
    return thread.kind === 'assignment' && thread.messages[0]?.id === messageId;
  }

  assignmentIntroText(body: string): string {
    const sanitized = body
      .replace(/https?:\/\/\S+/gi, '')
      .replace(/\s+/g, ' ')
      .trim();

    if (!sanitized) {
      return 'Un nouveau quiz vous a été assigné :';
    }

    if (sanitized.endsWith(':')) {
      return sanitized;
    }

    if (sanitized.endsWith('.')) {
      return `${sanitized.slice(0, -1)} :`;
    }

    return `${sanitized} :`;
  }

  private currentLang(): LanguageEnumDto {
    return this.userService.currentLang ?? LanguageEnumDto.En;
  }

  private runThreadRequest<T>(
    request$: Observable<T>,
    errorKey: string,
    fallbackMessage: string,
    onSuccess: (result: T) => void,
    onError?: () => void,
  ): void {
    this.saving.set(true);
    request$
      .pipe(
        takeUntilDestroyed(this.destroyRef),
        finalize(() => this.saving.set(false)),
      )
      .subscribe({
        next: (result) => {
          onSuccess(result);
        },
        error: (err: unknown) => {
          logApiError(errorKey, err);
          this.error.set(userFacingApiMessage(err, fallbackMessage));
          onError?.();
        },
      });
  }
}
