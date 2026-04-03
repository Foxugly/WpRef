import {CommonModule} from '@angular/common';
import {Component, EventEmitter, Input, Output} from '@angular/core';
import {FormsModule} from '@angular/forms';

import {ButtonModule} from 'primeng/button';
import {InputNumberModule} from 'primeng/inputnumber';
import {TooltipModule} from 'primeng/tooltip';

import {SelectedQuestionCard} from '../../pages/quiz/create/quiz-template-builder.models';
import {QuizCreateUiText} from '../../pages/quiz/create/quiz-create.i18n';

@Component({
  selector: 'app-quiz-template-composition',
  standalone: true,
  imports: [
    CommonModule,
    FormsModule,
    ButtonModule,
    InputNumberModule,
    TooltipModule,
  ],
  templateUrl: './quiz-template-composition.html',
  styleUrl: './quiz-template-composition.scss',
})
export class QuizTemplateCompositionComponent {
  @Input() items: SelectedQuestionCard[] = [];
  @Input({required: true}) texts!: QuizCreateUiText;

  @Output() previewQuestion = new EventEmitter<number>();
  @Output() moveQuestion = new EventEmitter<{index: number; direction: -1 | 1}>();
  @Output() removeQuestion = new EventEmitter<number>();
  @Output() weightChanged = new EventEmitter<{index: number; event: Event}>();
  @Output() weightSet = new EventEmitter<{index: number; value: number}>();
}
