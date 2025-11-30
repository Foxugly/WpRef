// src/app/components/quiz-question/quiz-question.ts
import {
  Component,
  Input,
  OnChanges,
  SimpleChanges,
  inject,
} from '@angular/core';
import { CommonModule } from '@angular/common';
import {
  DomSanitizer,
  SafeResourceUrl,
} from '@angular/platform-browser';

import {Question} from '../../services/question/question';
import {MediaSelectorValue} from '../media-selector/media-selector';
import { CardModule } from 'primeng/card';
import { ChipModule } from 'primeng/chip';
import { CheckboxModule } from 'primeng/checkbox';
import { RadioButtonModule } from 'primeng/radiobutton';
import { ImageModule } from 'primeng/image';
import { ButtonModule } from 'primeng/button';
import { FormsModule } from '@angular/forms';
import {Panel} from 'primeng/panel';

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
    Panel,
  ],
})
export class QuizQuestionComponent implements OnChanges {
  @Input({ required: true }) question!: Question;
  singleSelected: any = null;
  multiSelected: Record<number, boolean> = {};

  private sanitizer = inject(DomSanitizer);

  /** Sélection locale, juste pour l’affichage (aucun call backend ici) */
  multipleSelection: boolean[] = [];
  singleSelectionIndex: number | null = null;

  get allowMultiple(): boolean {
    return !!this.question?.allow_multiple_correct;
  }

  ngOnChanges(changes: SimpleChanges): void {
    if (changes['question'] && this.question) {
      const len = this.question.answer_options?.length ?? 0;
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

  private isYoutubeUrl(url: string): boolean {
    return /youtu\.be|youtube\.com/.test(url);
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

  // ---------- Sélection réponses (démo UI) ----------

  onToggleCheckbox(index: number): void {
    this.multipleSelection[index] = !this.multipleSelection[index];
  }

  onSelectRadio(index: number): void {
    this.singleSelectionIndex = index;
  }
}

