import {CommonModule} from '@angular/common';
import {Component, input, output} from '@angular/core';
import {ButtonModule} from 'primeng/button';
import {TableModule} from 'primeng/table';
import {QuizTemplateListItem} from '../../pages/quiz/list/quiz-list.models';
import {TooltipModule} from 'primeng/tooltip';
import {QuizListUiText} from '../../pages/quiz/list/quiz-list.i18n';

@Component({
  selector: 'app-quiz-template-table',
  imports: [CommonModule, ButtonModule, TableModule, TooltipModule],
  templateUrl: './quiz-template-table.html',
  styleUrl: './quiz-template-table.scss',
})
export class QuizTemplateTableComponent {
  readonly templates = input<QuizTemplateListItem[]>([]);
  readonly loading = input(false);
  readonly creatingTemplateId = input<number | null>(null);
  readonly uiText = input.required<QuizListUiText>();

  readonly createFromTemplate = output<number>();
  readonly openAssign = output<QuizTemplateListItem>();
  readonly openResults = output<QuizTemplateListItem>();
  readonly edit = output<number>();
  readonly remove = output<number>();

  emptyMessage(): string {
    return this.uiText().templates.empty;
  }

  canStartTemplate(template: QuizTemplateListItem): boolean {
    return !!template.active && !!template.can_answer;
  }

  modeLabel(mode: string | null | undefined): string {
    if (mode === 'exam') {
      return this.uiText().templates.modeExam;
    }
    if (mode === 'practice') {
      return this.uiText().templates.modePractice;
    }
    return mode || '-';
  }

  boolLabel(value: boolean | null | undefined): string {
    return value ? this.uiText().templates.yes : this.uiText().templates.no;
  }

  availabilityLabel(template: QuizTemplateListItem): string {
    if (template.permanent) {
      return this.uiText().templates.permanent;
    }

    const start = this.formatDateTime(template.started_at);
    const end = this.formatDateTime(template.ended_at);

    if (start && end) {
      return `${start} - ${end}`;
    }
    if (start) {
      return `${start} -`;
    }
    if (end) {
      return `- ${end}`;
    }
    return this.uiText().templates.permanent;
  }

  private formatDateTime(value: string | null | undefined): string {
    if (!value) {
      return '';
    }

    const date = new Date(value);
    if (Number.isNaN(date.getTime())) {
      return '';
    }

    return date.toLocaleString(undefined, {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
    });
  }
}
