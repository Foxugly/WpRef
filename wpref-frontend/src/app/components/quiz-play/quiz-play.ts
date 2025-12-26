import {Component} from '@angular/core';
import {QuizNav, QuizNavItem} from '../quiz-nav/quiz-nav';
import {Question} from '../../services/question/question';

function createEmptyQuestion(id: number, title: string = ""): Question {
  return {
    id: id,
    index: 0,
    title: title,
    description: "question",
    explanation: "parce que",
    allow_multiple_correct: true,
    active: true,
    is_mode_practice: true,
    is_mode_exam: false,
    subjects: [],
    media: [],
    answer_options: [],
    created_at: new Date().toISOString()
  };
}

@Component({
  selector: 'app-quiz-play',
  standalone: true,
  imports: [QuizNav],
  templateUrl: './quiz-play.html',
  styleUrl: './quiz-play.scss',
})
export class QuizPlay {
  questionNavItems: QuizNavItem[] = Array.from({length: 23}).map(
    (_, i): QuizNavItem => ({
      index: i + 1,
      id: i + 1,                // ← identifiant interne fictif
      answered: false,
      flagged: false,
      question: createEmptyQuestion(i + 1, `Question ${i + 1}`)
    })
  );

  currentQuestionIndex = 1;

  onQuestionSelected(index: number): void {
    this.currentQuestionIndex = index;
    // charger la question, etc.
  }

  markAnswered(index: number): void {
    const i = this.questionNavItems.findIndex((q) => q.index === index);
    if (i === -1) return;

    const old = this.questionNavItems[i];
    const updated: QuizNavItem = {
      ...old,
      answered: true,
      flagged: old.flagged, // si tu veux enlever le flag quand répondu
    };

    // ⚠️ recréer un nouveau tableau pour déclencher le change detection
    this.questionNavItems = [
      ...this.questionNavItems.slice(0, i),
      updated,
      ...this.questionNavItems.slice(i + 1),
    ];
  }

  toggleFlag(index: number): void {
    const i = this.questionNavItems.findIndex((q) => q.index === index);
    if (i === -1) return;
    const old = this.questionNavItems[i];
    const updated: QuizNavItem = {
      ...old,
      flagged: !old.flagged,
      // éventuel comportement : une question flaggée peut être non répondue
      answered: old.answered,
    };
    this.questionNavItems = [
      ...this.questionNavItems.slice(0, i),
      updated,
      ...this.questionNavItems.slice(i + 1),
    ];
  }
}
