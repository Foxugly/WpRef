import {Component} from '@angular/core';
import {ButtonModule} from 'primeng/button';
import {QuizNav, QuizNavItem} from '../quiz-nav/quiz-nav';

@Component({
  selector: 'app-quiz-play',
  standalone: true,
  imports: [QuizNav, ButtonModule],
  templateUrl: './quiz-play.html',
  styleUrl: './quiz-play.scss',
})
export class QuizPlayComponent {
  questionNavItems: QuizNavItem[] = [];
  currentQuestionIndex = 1;

  onQuestionSelected(index: number): void {
    this.currentQuestionIndex = index;
  }

  markAnswered(index: number): void {
    const i = this.questionNavItems.findIndex((q) => q.index === index);
    if (i === -1) return;
    this.questionNavItems[i] = {...this.questionNavItems[i], answered: true};
    this.questionNavItems = [...this.questionNavItems];
  }

  toggleFlag(index: number): void {
    const i = this.questionNavItems.findIndex((q) => q.index === index);
    if (i === -1) return;
    this.questionNavItems[i] = {...this.questionNavItems[i], flagged: !this.questionNavItems[i].flagged};
    this.questionNavItems = [...this.questionNavItems];
  }
}
