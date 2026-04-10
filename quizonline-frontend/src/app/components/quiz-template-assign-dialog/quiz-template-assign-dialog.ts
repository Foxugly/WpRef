import {CommonModule} from '@angular/common';
import {Component, computed, input, output, signal} from '@angular/core';
import {FormsModule} from '@angular/forms';
import {CheckboxModule} from 'primeng/checkbox';
import {ButtonModule} from 'primeng/button';
import {DialogModule} from 'primeng/dialog';
import {InputTextModule} from 'primeng/inputtext';
import {TagModule} from 'primeng/tag';
import {QuizTemplateDto} from '../../api/generated';
import {AssignableRecipient} from '../../pages/quiz/list/quiz-list.models';
import {QuizListUiText} from '../../pages/quiz/list/quiz-list.i18n';

@Component({
  selector: 'app-quiz-template-assign-dialog',
  imports: [CommonModule, FormsModule, CheckboxModule, ButtonModule, DialogModule, InputTextModule, TagModule],
  templateUrl: './quiz-template-assign-dialog.html',
  styleUrl: './quiz-template-assign-dialog.scss',
})
export class QuizTemplateAssignDialogComponent {
  visible = input(false);
  template = input<QuizTemplateDto | null>(null);
  users = input<AssignableRecipient[]>([]);
  selectedRecipientIds = input<number[]>([]);
  assigning = input(false);
  texts = input.required<QuizListUiText>();
  search = signal('');
  roleFilter = signal<'all' | AssignableRecipient['role']>('all');

  visibleChange = output<boolean>();
  selectedRecipientIdsChange = output<number[]>();
  submitted = output<void>();
  cancel = output<void>();

  readonly filteredUsers = computed(() => {
    const term = this.search().trim().toLowerCase();
    const role = this.roleFilter();
    return this.users().filter((user) => {
      const matchesRole = role === 'all' || user.role === role;
      const matchesTerm = !term || user.username.toLowerCase().includes(term);
      return matchesRole && matchesTerm;
    });
  });

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
    this.search.set('');
    this.roleFilter.set('all');
    this.cancel.emit();
  }

  onSubmit(): void {
    this.submitted.emit();
  }

  roleLabel(role: AssignableRecipient['role']): string {
    const labels = this.texts().assignDialog;
    if (role === 'owner') {
      return labels.roleOwner;
    }
    if (role === 'manager') {
      return labels.roleStaff;
    }
    return labels.roleMember;
  }

  roleSeverity(role: AssignableRecipient['role']): 'contrast' | 'info' | 'success' {
    if (role === 'owner') {
      return 'contrast';
    }
    if (role === 'manager') {
      return 'info';
    }
    return 'success';
  }

  setRoleFilter(role: 'all' | AssignableRecipient['role']): void {
    this.roleFilter.set(role);
  }

  selectAllVisible(): void {
    const selected = new Set(this.selectedRecipientIds());
    for (const user of this.filteredUsers()) {
      selected.add(user.id);
    }
    this.selectedRecipientIdsChange.emit([...selected]);
  }

  clearVisibleSelection(): void {
    const visibleIds = new Set(this.filteredUsers().map((user) => user.id));
    this.selectedRecipientIdsChange.emit(
      this.selectedRecipientIds().filter((id) => !visibleIds.has(id)),
    );
  }
}
