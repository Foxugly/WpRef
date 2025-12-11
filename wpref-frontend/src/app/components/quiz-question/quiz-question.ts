// src/app/components/quiz-question/quiz-question.ts
import {Component, EventEmitter, inject, Input, OnChanges, Output, SimpleChanges,} from '@angular/core';
import {CommonModule} from '@angular/common';
import {DomSanitizer, SafeResourceUrl,} from '@angular/platform-browser';

import {Question} from '../../services/question/question';
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
  @Output() answeredToggled = new EventEmitter<void>();

  singleSelected: any = null;
  multiSelected: Record<number, boolean> = {};
  /** Sélection locale, juste pour l’affichage (aucun call backend ici) */
  multipleSelection: boolean[] = [];
  singleSelectionIndex: number | null = null;
  private sanitizer = inject(DomSanitizer);

  get question(): Question {
    return this.quizNavItem.question;
  }

  get allowMultiple(): boolean {
    return !!this.quizNavItem.question.allow_multiple_correct;
  }

  isMultiChecked(i: number): boolean {
    return this.multiSelected[i] ?? false;
  }

  ngOnChanges(changes: SimpleChanges): void {
    if (changes['quizNavItem'] && this.quizNavItem) {
      const len = this.quizNavItem.question.answer_options?.length ?? 0;
      this.multipleSelection = Array(len).fill(false);
      this.singleSelectionIndex = null;
    }
  }

  public onSelectSingle(opt: any) {
    this.singleSelected = opt;
  }

  public onToggleMulti(index: number, checked: boolean) {
    this.multiSelected[index] = checked;
  }

  // ---------- Médias ----------

  mediaSrc(m: MediaSelectorValue): string {
    // Pour images/vidéos : on part du principe que file est déjà une URL absolue ou relative
    return (m.file as string | null) || m.external_url || '';
  }

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

  externalSafeUrl(m: MediaSelectorValue): SafeResourceUrl | null {
    const raw = m.external_url || '';
    if (!raw) return null;
    const embed = this.isYoutubeUrl(raw) ? this.toYoutubeEmbed(raw) : raw;
    return this.sanitizer.bypassSecurityTrustResourceUrl(embed);
  }

  onToggleCheckbox(index: number): void {
    this.multipleSelection[index] = !this.multipleSelection[index];
  }

  // ---------- Sélection réponses (démo UI) ----------
  onSelectRadio(index: number): void {
    this.singleSelectionIndex = index;
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

  private isYoutubeUrl(url: string): boolean {
    return /youtu\.be|youtube\.com/.test(url);
  }
}
