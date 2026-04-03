import {CommonModule} from '@angular/common';
import {Component, EventEmitter, Input, Output} from '@angular/core';
import {FormsModule} from '@angular/forms';

import {ButtonModule} from 'primeng/button';
import {MultiSelectModule} from 'primeng/multiselect';

import {QuestionReadDto} from '../../api/generated';
import {QuestionLibraryCard} from '../../pages/quiz/create/quiz-template-builder.models';
import {QuizCreateUiText} from '../../pages/quiz/create/quiz-create.i18n';

@Component({
  selector: 'app-quiz-question-library',
  standalone: true,
  imports: [
    CommonModule,
    FormsModule,
    ButtonModule,
    MultiSelectModule,
  ],
  templateUrl: './quiz-question-library.html',
  styleUrl: './quiz-question-library.scss',
})
export class QuizQuestionLibraryComponent {
  @Input({required: true}) texts!: QuizCreateUiText;
  @Input() selectedDomainId = 0;
  @Input() loading = false;
  @Input() search = '';
  @Input() items: QuestionLibraryCard[] = [];
  @Input() subjectOptions: Array<{name: string; code: number}> = [];
  @Input() selectedSubjectIds: number[] = [];

  @Output() searchChanged = new EventEmitter<Event>();
  @Output() selectedSubjectIdsChange = new EventEmitter<number[]>();
  @Output() createQuestion = new EventEmitter<void>();
  @Output() previewQuestion = new EventEmitter<QuestionReadDto>();
  @Output() addQuestion = new EventEmitter<QuestionReadDto>();
}
