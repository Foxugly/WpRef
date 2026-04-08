import {Component, EventEmitter, Input, Output} from '@angular/core';
import {CommonModule} from '@angular/common';
import {PanelModule} from 'primeng/panel';
import {QuestionButton} from '../question-button/question-button';
import {QuestionReadDto} from '../../api/generated';


export interface QuizNavItem {
  index: number;
  id: number;
  answered: boolean;
  flagged: boolean;
  question: QuestionReadDto;
  selectedOptionIds?: number[];
}

@Component({
  selector: 'app-quiz-nav',
  standalone: true,
  imports: [CommonModule, PanelModule, QuestionButton],
  templateUrl: './quiz-nav.html',
  styleUrl: './quiz-nav.scss',
})
export class QuizNav {
  /** Liste des questions */
  @Input() items: QuizNavItem[] = [];

  /** Nombre de colonnes (boutons par ligne) */
  @Input() columns = 5;
  @Input() reviewMode = false;

  /** Événement émis au clic sur un bouton */
  @Output() questionSelected = new EventEmitter<number>();

  onClick(item: QuizNavItem): void {
    this.questionSelected.emit(item.index);
  }

  /** Couleur de fond selon l'état de la question */
  getBackgroundColor(item: QuizNavItem): string {
    const reviewState = this.getReviewState(item);
    if (reviewState === 'correct') {
      return '#dcfce7';
    }
    if (reviewState === 'wrong') {
      return '#fee2e2';
    }
    if (item.answered) {
      // Question répondue : bleu très léger
      return '#e3f2fd';
    }
    // par défaut : gris clair
    return '#f2f2f2';
  }

  /** Couleur de bordure selon l'état de la question */
  getBorderColor(item: QuizNavItem): string {
    const reviewState = this.getReviewState(item);
    if (reviewState === 'correct') {
      return '#16a34a';
    }
    if (reviewState === 'wrong') {
      return '#dc2626';
    }
    if (item.flagged) {
      return '#d32f2f'; // rouge pour marquée
    }
    if (item.answered) {
      return '#1976d2'; // bleu pour répondue
    }
    return '#cccccc'; // gris léger par défaut
  }

  /** Épaisseur de bordure selon l'état de la question */
  getBorderWidth(item: QuizNavItem): string {
    if (this.getReviewState(item) !== 'neutral') {
      return '2px';
    }
    if (item.flagged) {
      return '3px';
    }
    if (item.answered) {
      return '2px';
    }
    return '1px';
  }

  getTextColor(item: QuizNavItem): string {
    const reviewState = this.getReviewState(item);
    if (reviewState === 'correct') return '#166534';
    if (reviewState === 'wrong') return '#991b1b';
    if (item.flagged) return '#b71c1c';      // rouge foncé
    if (item.answered) return '#0d47a1';     // bleu foncé
    return '#333333';                        // gris foncé par défaut
  }

  private getReviewState(item: QuizNavItem): 'correct' | 'wrong' | 'neutral' {
    if (!this.reviewMode || !item.answered) {
      return 'neutral';
    }

    const options = item.question.answer_options ?? [];
    const hasCorrection = options.some((option) => option.is_correct === true || option.is_correct === false);
    if (!hasCorrection) {
      return 'neutral';
    }

    const selected = new Set(item.selectedOptionIds ?? []);
    const correct = new Set(
      options
        .filter((option) => option.is_correct)
        .map((option) => option.id)
        .filter((id): id is number => id != null),
    );

    if (selected.size !== correct.size) {
      return 'wrong';
    }

    for (const id of correct) {
      if (!selected.has(id)) {
        return 'wrong';
      }
    }

    return 'correct';
  }
}
