import {Component, EventEmitter, Input, Output} from '@angular/core';
import {CommonModule} from '@angular/common';
import {PanelModule} from 'primeng/panel';
import {QuestionButton} from '../question-button/question-button';
import {Question} from '../../services/question/question';

export interface QuizNavItem {
  index: number;
  id: number;
  answered: boolean;
  flagged: boolean;
  question: Question;
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

  /** Événement émis au clic sur un bouton */
  @Output() questionSelected = new EventEmitter<number>();

  onClick(item: QuizNavItem): void {
    this.questionSelected.emit(item.index);
  }

  /** Couleur de fond selon l'état de la question */
  getBackgroundColor(item: QuizNavItem): string {
    /*if (item.flagged) {
      // Question marquée : fond clair
      return '#fff7f7';
    }*/
    if (item.answered) {
      // Question répondue : bleu très léger
      return '#e3f2fd';
    }
    // par défaut : gris clair
    return '#f2f2f2';
  }

  /** Couleur de bordure selon l'état de la question */
  getBorderColor(item: QuizNavItem): string {
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
    if (item.flagged) {
      return '3px';
    }
    if (item.answered) {
      return '2px';
    }
    return '1px';
  }

  getTextColor(item: QuizNavItem): string {
    if (item.flagged) return '#b71c1c';      // rouge foncé
    if (item.answered) return '#0d47a1';     // bleu foncé
    return '#333333';                        // gris foncé par défaut
  }

}
