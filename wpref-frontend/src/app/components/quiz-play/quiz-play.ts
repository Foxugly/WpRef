import {Component} from '@angular/core';
import {QuizNav, QuizNavItem} from '../quiz-nav/quiz-nav';

@Component({
  selector: 'app-quiz-play',
  standalone: true,
  imports: [QuizNav],
  templateUrl: './quiz-play.html',
  styleUrl: './quiz-play.scss',
})
export class QuizPlay {
  questions: QuizNavItem[] = Array.from({length: 23}).map((_, i) => ({
    index: i + 1,
    answered: false,
    flagged: false,
  }));

  currentQuestionIndex = 1;

  onQuestionSelected(index: number): void {
    this.currentQuestionIndex = index;
    // charger la question, etc.
  }

  markAnswered(index: number): void {
    console.log('markAnswered', index);

    const i = this.questions.findIndex((q) => q.index === index);
    if (i === -1) return;

    const old = this.questions[i];
    const updated: QuizNavItem = {
      ...old,
      answered: true,
      flagged: old.flagged, // si tu veux enlever le flag quand répondu
    };

    // ⚠️ recréer un nouveau tableau pour déclencher le change detection
    this.questions = [
      ...this.questions.slice(0, i),
      updated,
      ...this.questions.slice(i + 1),
    ];
  }

  toggleFlag(index: number): void {
    console.log('toggleFlag', index);

    const i = this.questions.findIndex((q) => q.index === index);
    if (i === -1) return;

    const old = this.questions[i];
    const updated: QuizNavItem = {
      ...old,
      flagged: !old.flagged,
      // éventuel comportement : une question flaggée peut être non répondue
      answered: old.answered,
    };

    this.questions = [
      ...this.questions.slice(0, i),
      updated,
      ...this.questions.slice(i + 1),
    ];
  }
}
