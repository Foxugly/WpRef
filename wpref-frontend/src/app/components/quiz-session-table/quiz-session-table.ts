import {CommonModule, DatePipe} from '@angular/common';
import {Component, input, output} from '@angular/core';
import {ButtonModule} from 'primeng/button';
import {TableModule} from 'primeng/table';
import {UserQuizListItem} from '../../pages/quiz/list/quiz-list.models';

@Component({
  selector: 'app-quiz-session-table',
  imports: [CommonModule, DatePipe, ButtonModule, TableModule],
  templateUrl: './quiz-session-table.html',
  styleUrl: './quiz-session-table.scss',
})
export class QuizSessionTableComponent {
  readonly quizzes = input<UserQuizListItem[]>([]);
  readonly loading = input(false);

  readonly viewQuiz = output<number>();

  statusLabel(status: UserQuizListItem['status']): string {
    return status === 'answered' ? 'Repondu' : 'En cours';
  }
}
