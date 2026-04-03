import {CommonModule} from '@angular/common';
import {Component, computed, inject, input, output} from '@angular/core';
import {FormGroup, FormsModule, ReactiveFormsModule} from '@angular/forms';

import {ButtonModule} from 'primeng/button';
import {CardModule} from 'primeng/card';
import {EditorModule} from 'primeng/editor';
import {InputTextModule} from 'primeng/inputtext';
import {SelectModule} from 'primeng/select';
import {TabsModule} from 'primeng/tabs';

import {UserService} from '../../services/user/user';
import {getEditorUiText} from '../../shared/i18n/editor-ui-text';

type DomainOption = { id: number; name: string };

@Component({
  selector: 'app-subject-editor-form',
  standalone: true,
  templateUrl: './subject-editor-form.html',
  styleUrl: './subject-editor-form.scss',
  imports: [
    CommonModule,
    FormsModule,
    ReactiveFormsModule,
    EditorModule,
    TabsModule,
    SelectModule,
    ButtonModule,
    InputTextModule,
    CardModule,
  ],
})
export class SubjectEditorFormComponent {
  private readonly userService = inject(UserService);
  readonly form = input.required<FormGroup>();
  readonly tabCodes = input<string[]>([]);
  readonly activeLang = input<string | undefined>(undefined);
  readonly translating = input(false);
  readonly loading = input(false);
  readonly submitError = input<string | null>(null);
  readonly showDomainSelect = input(false);
  readonly selectedDomainId = input<number>(0);
  readonly domainOptions = input<DomainOption[]>([]);
  readonly emptyLanguagesMessage = input('Ce domaine n a pas de langues configurees.');
  readonly submitLabel = input('Enregistrer');
  readonly ui = computed(() => getEditorUiText(this.userService.currentLang));

  readonly tabChange = output<string | number | undefined>();
  readonly translateActive = output<void>();
  readonly domainChange = output<number>();
  readonly submitForm = output<void>();
  readonly cancel = output<void>();

  langGroup(code: string): FormGroup {
    return this.form().get(['translations', code]) as FormGroup;
  }

  submit(): void {
    this.submitForm.emit();
  }

  onCancel(): void {
    this.cancel.emit();
  }

  onTabChange(value: string | number | undefined): void {
    this.tabChange.emit(value);
  }

  onTranslateActive(): void {
    this.translateActive.emit();
  }

  onDomainChange(value: number): void {
    this.domainChange.emit(value);
  }

  showTranslations(): boolean {
    return !this.showDomainSelect() || !!this.selectedDomainId();
  }
}
