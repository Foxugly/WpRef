// src/app/components/quiz-question/quiz-question.ts
import {Component, EventEmitter, inject, Input, OnChanges, Output, SimpleChanges,} from '@angular/core';
import {CommonModule} from '@angular/common';
import {DomSanitizer, SafeResourceUrl,} from '@angular/platform-browser';

import {MediaSelectorValue} from '../media-selector/media-selector';
import {CardModule} from 'primeng/card';
import {ChipModule} from 'primeng/chip';
import {CheckboxModule} from 'primeng/checkbox';
import {RadioButtonModule} from 'primeng/radiobutton';
import {ImageModule} from 'primeng/image';
import {ButtonModule} from 'primeng/button';
import {FormsModule} from '@angular/forms';
import {ToggleButtonModule} from 'primeng/togglebutton';
import {QuizNavItem} from '../quiz-nav/quiz-nav';
import {QuestionMediaDto, QuestionReadDto} from '../../api/generated';


export interface AnswerPayload {
  questionId: number;
  index: number;
  selectedOptionIds: number[];
}

@Component({
  standalone: true,
  selector: 'app-quiz-question',
  templateUrl: './quiz-question.html',
  styleUrl: './quiz-question.scss',
  imports: [
    CommonModule,
    FormsModule,
    CardModule,
    ChipModule,
    CheckboxModule,
    RadioButtonModule,
    ImageModule,
    ButtonModule,
    ToggleButtonModule,
  ],
})
export class QuizQuestionComponent implements OnChanges {
  @Input({required: true}) quizNavItem!: QuizNavItem;
  @Input() showCorrectAnswers = false;
  @Input() displayMode: 'preview' | 'exam' = 'preview';
  @Input() hasPrevious = false;
  @Input() hasNext = false;
  @Output() answeredToggled = new EventEmitter<void>();
  @Output() flagToggled = new EventEmitter<boolean>();
  // ➜ nouveaux events pour laisser le parent gérer la navigation
  @Output() goNext = new EventEmitter<AnswerPayload>();
  @Output() goPrevious = new EventEmitter<AnswerPayload>();

  selectedOptionIds: number[] = [];
  // Pour le radio uniquement (choix unique)
  selectedRadioId: number | null = null;

  private sanitizer = inject(DomSanitizer);

  get question(): QuestionReadDto {
    return this.quizNavItem.question;
  }

  get allowMultiple(): boolean {
    return !!this.quizNavItem.question.allow_multiple_correct;
  }

  /** RADIO : choix unique */
  onSelectRadio(optionId: number | null): void {
    this.selectedRadioId = optionId;
    this.selectedOptionIds = optionId == null ? [] : [optionId];
  }

  onNextClick(): void {
    this.goNext.emit(this.buildPayload());
  }

  onPreviousClick(): void {
    this.goPrevious.emit(this.buildPayload());
  }

  /** CHECKBOX : choix multiple */
  onToggleCheckbox(optionId: number | undefined, checked: boolean) {
    if (optionId == null) {
      return;
    }
    if (checked) {
      if (!this.selectedOptionIds.includes(optionId)) {
        this.selectedOptionIds = [...this.selectedOptionIds, optionId];
      }
    } else {
      this.selectedOptionIds = this.selectedOptionIds.filter(id => id !== optionId);
    }
  }

  isChecked(optionId?: number): boolean {
    return optionId != null && this.selectedOptionIds.includes(optionId);
  }

  ngOnChanges(changes: SimpleChanges): void {
    if (changes['quizNavItem'] && this.quizNavItem) {
      // on reset la sélection quand on change de question
      const ids = this.quizNavItem.selectedOptionIds ?? [];

      // On met à jour l'état interne du composant
      this.selectedOptionIds = [...ids];

      if (!this.allowMultiple) {
        // Cas choix unique : on synchronise aussi le radio
        this.selectedRadioId = ids.length ? ids[0] : null;
      }
    }
  }


  mediaSrc(m:  QuestionMediaDto): string {
    // Pour images/vidéos : on part du principe que file est déjà une URL absolue ou relative
    return (m.file as string | null) || m.external_url || '';
  }

  // ---------- Médias ----------

  toYoutubeEmbed(url: string): string {
    try {
      const u = new URL(url);
      // https://www.youtube.com/watch?v=ID
      if (u.hostname.includes('youtube.com')) {
        const v = u.searchParams.get('v');
        if (v) {
          return `https://www.youtube.com/embed/${v}`;
        }
      }
      // https://youtu.be/ID
      if (u.hostname.includes('youtu.be')) {
        const id = u.pathname.replace('/', '');
        if (id) {
          return `https://www.youtube.com/embed/${id}`;
        }
      }
      // fallback : on renvoie l’URL
      return url;
    } catch {
      return url;
    }
  }

  externalSafeUrl(m:  QuestionMediaDto): SafeResourceUrl | null {
    const raw = m.external_url || '';
    if (!raw) return null;
    const embed = this.isYoutubeUrl(raw) ? this.toYoutubeEmbed(raw) : raw;
    return this.sanitizer.bypassSecurityTrustResourceUrl(embed);
  }

  stripOuterP(html: string): string {
    if (!html) return html;
    const trimmed = html.trim();
    let inner = trimmed;
    if (trimmed.startsWith('<p') && trimmed.endsWith('</p>')) {
      const startTagEnd = trimmed.indexOf('>') + 1;
      const endTagStart = trimmed.lastIndexOf('</p>');
      inner = trimmed.substring(startTagEnd, endTagStart).trim();
    }
    inner = inner
      .replace(/&nbsp;/g, ' ')
      .replace(/\u00A0/g, ' ');
    return inner;
  }

  private buildPayload(): AnswerPayload {
    return {
      questionId: this.question.id,
      index: this.quizNavItem.index,
      selectedOptionIds: this.selectedOptionIds, // copie
    };
  }

  private isYoutubeUrl(url: string): boolean {
    return /youtu\.be|youtube\.com/.test(url);
  }
}
