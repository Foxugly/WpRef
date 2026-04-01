import {CommonModule} from '@angular/common';
import {Component, computed, DestroyRef, inject, OnInit, signal} from '@angular/core';
import {takeUntilDestroyed} from '@angular/core/rxjs-interop';
import {FormsModule} from '@angular/forms';
import {RouterLink} from '@angular/router';
import {finalize} from 'rxjs';
import {ButtonModule} from 'primeng/button';
import {CardModule} from 'primeng/card';
import {InputTextModule} from 'primeng/inputtext';
import {SelectModule} from 'primeng/select';
import {TagModule} from 'primeng/tag';
import {QuizAlertService, QuizAlertThreadListDto} from '../../../../services/quiz-alert/quiz-alert';
import {ROUTES} from '../../../../app.routes-paths';
import {logApiError, userFacingApiMessage} from '../../../../shared/api/api-errors';

type AlertStatusFilter = 'all' | 'open' | 'closed';
type AlertReadFilter = 'all' | 'unread' | 'read';

@Component({
  selector: 'app-quiz-alert-list',
  standalone: true,
  imports: [CommonModule, FormsModule, RouterLink, ButtonModule, CardModule, InputTextModule, SelectModule, TagModule],
  templateUrl: './quiz-alert-list.html',
  styleUrl: './quiz-alert-list.scss',
})
export class QuizAlertList implements OnInit {
  readonly loading = signal(true);
  readonly error = signal<string | null>(null);
  readonly threads = signal<QuizAlertThreadListDto[]>([]);
  readonly search = signal('');
  readonly statusFilter = signal<AlertStatusFilter>('all');
  readonly readFilter = signal<AlertReadFilter>('all');

  protected readonly routes = ROUTES;
  protected readonly statusOptions = [
    {label: 'Tous', value: 'all'},
    {label: 'Ouverts', value: 'open'},
    {label: 'Fermés', value: 'closed'},
  ];
  protected readonly readOptions = [
    {label: 'Tous', value: 'all'},
    {label: 'Non lus', value: 'unread'},
    {label: 'Lus', value: 'read'},
  ];
  private readonly quizAlertService = inject(QuizAlertService);
  private readonly destroyRef = inject(DestroyRef);
  readonly filteredThreads = computed(() => {
    const search = this.normalize(this.search());
    const status = this.statusFilter();
    const readFilter = this.readFilter();

    return this.threads().filter((thread) => {
      if (status !== 'all' && thread.status !== status) {
        return false;
      }

      if (readFilter === 'unread' && thread.unread_count <= 0) {
        return false;
      }

      if (readFilter === 'read' && thread.unread_count > 0) {
        return false;
      }

      if (!search) {
        return true;
      }

      return this.normalize([
        thread.question_title,
        thread.quiz_template_title,
        thread.last_message_preview,
        thread.reported_language,
        String(thread.question_id),
        String(thread.question_order),
      ].join(' ')).includes(search);
    });
  });

  ngOnInit(): void {
    this.load();
  }

  load(): void {
    this.loading.set(true);
    this.error.set(null);
    this.quizAlertService.list()
      .pipe(
        takeUntilDestroyed(this.destroyRef),
        finalize(() => this.loading.set(false)),
      )
      .subscribe({
        next: (threads) => {
          this.threads.set(threads);
          this.quizAlertService.refreshUnreadCount().subscribe();
        },
        error: (err: unknown) => {
          logApiError('quiz.alerts.list', err);
          this.error.set(userFacingApiMessage(err, 'Impossible de charger les alertes.'));
          this.threads.set([]);
        },
      });
  }

  statusSeverity(thread: QuizAlertThreadListDto): 'danger' | 'success' | 'contrast' {
    if (thread.unread_count > 0) {
      return 'danger';
    }
    return thread.status === 'open' ? 'success' : 'contrast';
  }

  statusLabel(thread: QuizAlertThreadListDto): string {
    if (thread.unread_count > 0) {
      return 'Non lu';
    }
    return thread.status === 'open' ? 'Ouverte' : 'Clôturée';
  }

  private normalize(value: string): string {
    return value.toLocaleLowerCase().trim();
  }
}
