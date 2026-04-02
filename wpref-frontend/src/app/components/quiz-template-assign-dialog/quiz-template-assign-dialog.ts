import {CommonModule} from '@angular/common';
import {Component, input, output} from '@angular/core';
import {FormsModule} from '@angular/forms';
import {CheckboxModule} from 'primeng/checkbox';
import {ButtonModule} from 'primeng/button';
import {DialogModule} from 'primeng/dialog';
import {CustomUserReadDto, QuizTemplateDto} from '../../api/generated';

@Component({
  selector: 'app-quiz-template-assign-dialog',
  imports: [CommonModule, FormsModule, CheckboxModule, ButtonModule, DialogModule],
  templateUrl: './quiz-template-assign-dialog.html',
  styleUrl: './quiz-template-assign-dialog.scss',
})
export class QuizTemplateAssignDialogComponent {
  visible = input(false);
  template = input<QuizTemplateDto | null>(null);
  users = input<CustomUserReadDto[]>([]);
  selectedRecipientIds = input<number[]>([]);
  assigning = input(false);

  visibleChange = output<boolean>();
  selectedRecipientIdsChange = output<number[]>();
  submitted = output<void>();
  cancel = output<void>();

  onVisibleChange(value: boolean): void {
    this.visibleChange.emit(value);
  }

  onRecipientsChange(value: number[] | null | undefined): void {
    this.selectedRecipientIdsChange.emit(value ?? []);
  }

  toggleRecipient(userId: number, checked: boolean): void {
    const current = this.selectedRecipientIds();
    if (checked) {
      if (!current.includes(userId)) {
        this.selectedRecipientIdsChange.emit([...current, userId]);
      }
      return;
    }

    this.selectedRecipientIdsChange.emit(current.filter((id) => id !== userId));
  }

  onCancel(): void {
    this.cancel.emit();
  }

  onSubmit(): void {
    this.submitted.emit();
  }
}
