import { Component, EventEmitter, Input, Output } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ButtonModule } from 'primeng/button';

@Component({
  selector: 'app-question-button',
  standalone: true,
  imports: [CommonModule, ButtonModule],
  templateUrl: './question-button.html',
  styleUrl: './question-button.scss',
})
export class QuestionButton {
  /** Texte du bouton */
  @Input() label = '';

  /** Couleur de fond */
  @Input() backgroundColor?: string;

  /** Couleur de bordure */
  @Input() borderColor?: string;

  /** Largeur de bordure (ex: '1px', '3px') */
  @Input() borderWidth?: string;

  /** Rayon des coins (optionnel) */
  @Input() borderRadius?: string;

  /** Couleur du texte (optionnel) */
  @Input() textColor?: string;

  /** Bouton désactivé */
  @Input() disabled = false;

  /** Événement clic */
  @Output() clicked = new EventEmitter<MouseEvent>();

  onClick(event: MouseEvent) {
    this.clicked.emit(event);
  }

  get styleObject(): Record<string, string> {
    const style: Record<string, string> = {};

    if (this.backgroundColor) {
      style['background'] = this.backgroundColor;
    }

    if (this.borderColor) {
      style['border-color'] = this.borderColor;
      style['border-style'] = 'solid';
    }

    if (this.borderWidth) {
      style['border-width'] = this.borderWidth;
      style['border-style'] = 'solid';
    }

    if (this.borderRadius) {
      style['border-radius'] = this.borderRadius;
    }

    if (this.textColor) {
      style['color'] = this.textColor;
    }

    return style;
  }
}
