import {CommonModule} from '@angular/common';
import {Component, input, output} from '@angular/core';
import {ButtonModule} from 'primeng/button';
import {TableModule} from 'primeng/table';
import {QuizTemplateListItem} from '../../pages/quiz/list/quiz-list.models';

@Component({
  selector: 'app-quiz-template-table',
  imports: [CommonModule, ButtonModule, TableModule],
  templateUrl: './quiz-template-table.html',
  styleUrl: './quiz-template-table.scss',
})
export class QuizTemplateTableComponent {
  readonly title = input.required<string>();
  readonly description = input.required<string>();
  readonly kind = input<'created' | 'public'>('created');
  readonly templates = input<QuizTemplateListItem[]>([]);
  readonly loading = input(false);
  readonly creatingTemplateId = input<number | null>(null);

  readonly createFromTemplate = output<number>();
  readonly openAssign = output<QuizTemplateListItem>();
  readonly openResults = output<QuizTemplateListItem>();
  readonly edit = output<number>();
  readonly remove = output<number>();

  isCreatedTable(): boolean {
    return this.kind() === 'created';
  }

  emptyMessage(): string {
    return this.isCreatedTable() ? 'Aucun template cree.' : 'Aucun template public.';
  }

  canStartTemplate(template: QuizTemplateListItem): boolean {
    return !!template.active && !!template.can_answer;
  }
}
