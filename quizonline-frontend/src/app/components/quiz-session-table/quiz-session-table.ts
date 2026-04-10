import {CommonModule} from '@angular/common';
import {Component, inject, input, output} from '@angular/core';
import {ButtonModule} from 'primeng/button';
import {TableModule} from 'primeng/table';
import {UserQuizListItem} from '../../pages/quiz/list/quiz-list.models';
import {UserService} from '../../services/user/user';
import {formatLocalizedDateTime} from '../../shared/i18n/date-time';

@Component({
  selector: 'app-quiz-session-table',
  imports: [CommonModule, ButtonModule, TableModule],
  templateUrl: './quiz-session-table.html',
  styleUrl: './quiz-session-table.scss',
})
export class QuizSessionTableComponent {
  readonly quizzes = input<UserQuizListItem[]>([]);
  readonly loading = input(false);

  readonly viewQuiz = output<number>();
  private readonly userService = inject(UserService);

  statusLabel(status: UserQuizListItem['status']): string {
    if (status === 'answered') {
      return 'Repondu';
    }
    if (status === 'in_progress') {
      return 'En cours';
    }
    return 'Non commence';
  }

  formatDateTime(value: string | null | undefined): string {
    return formatLocalizedDateTime(value, this.userService.currentLang) ?? '-';
  }
}
