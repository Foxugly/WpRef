import {CommonModule} from '@angular/common';
import {Component, computed, inject, input, output} from '@angular/core';
import {FormArray, FormControl, FormGroup, ReactiveFormsModule} from '@angular/forms';

import {ButtonModule} from 'primeng/button';
import {CardModule} from 'primeng/card';
import {CheckboxModule} from 'primeng/checkbox';
import {DividerModule} from 'primeng/divider';
import {EditorModule} from 'primeng/editor';
import {InputNumberModule} from 'primeng/inputnumber';
import {InputTextModule} from 'primeng/inputtext';
import {MultiSelectModule} from 'primeng/multiselect';
import {PanelModule} from 'primeng/panel';
import {SelectModule} from 'primeng/select';
import {TabsModule} from 'primeng/tabs';
import {TooltipModule} from 'primeng/tooltip';

import {MediaSelectorComponent} from '../media-selector/media-selector';
import {
  getAnswerContentControl,
  getAnswerCorrectControl,
  getAnswerMetaGroup,
  getAnswerOptions,
  getTranslationsGroup,
  QuestionEditorForm,
} from '../../services/question/question-editor-form';
import {LangCode} from '../../services/translation/translation';
import {UserService} from '../../services/user/user';
import {getEditorUiText} from '../../shared/i18n/editor-ui-text';

type DomainOption = { id: number; name: string };
type SubjectOption = { code: number; name: string };

@Component({
  selector: 'app-question-editor-form',
  standalone: true,
  templateUrl: './question-editor-form.html',
  styleUrl: './question-editor-form.scss',
  imports: [
    CommonModule,
    ReactiveFormsModule,
    EditorModule,
    TabsModule,
    SelectModule,
    MultiSelectModule,
    CheckboxModule,
    InputTextModule,
    InputNumberModule,
    ButtonModule,
    PanelModule,
    CardModule,
    TooltipModule,
    MediaSelectorComponent,
    DividerModule,
  ],
})
export class QuestionEditorFormComponent {
  private readonly userService = inject(UserService);
  readonly form = input.required<QuestionEditorForm>();
  readonly tabCodes = input<LangCode[]>([]);
  readonly activeLang = input<LangCode | null | undefined>(undefined);
  readonly domainOptions = input<DomainOption[]>([]);
  readonly subjectOptions = input<SubjectOption[]>([]);
  readonly domainReadonlyLabel = input<string | null>(null);
  readonly showDomainSelect = input(true);
  readonly showTranslateAction = input(true);
  readonly showCleanAction = input(true);
  readonly translating = input(false);
  readonly saving = input(false);
  readonly deleting = input(false);
  readonly submitLabel = input('Enregistrer');
  readonly emptyLanguagesMessage = input('Aucune langue active sur ce domaine.');
  readonly submitError = input<string | null>(null);
  readonly practiceTooltip = input<string | null>(null);
  readonly showDeleteAction = input(false);
  readonly showDuplicateAction = input(false);
  readonly deleteLabel = input('Supprimer la question');
  readonly duplicateLabel = input('Dupliquer');
  readonly ui = computed(() => getEditorUiText(this.userService.currentLang));

  readonly tabChanged = output<string | number | undefined>();
  readonly translateActive = output<void>();
  readonly addOptionClicked = output<void>();
  readonly removeOptionClicked = output<number>();
  readonly cancelClicked = output<void>();
  readonly cleanActiveClicked = output<void>();
  readonly deleteClicked = output<void>();
  readonly duplicateClicked = output<void>();
  readonly submitted = output<void>();

  get answerOptions(): FormArray<FormGroup> {
    return getAnswerOptions(this.form());
  }

  translationsGroup(): FormGroup {
    return getTranslationsGroup(this.form());
  }

  answerMetaGroup(index: number): FormGroup {
    return getAnswerMetaGroup(this.form(), index);
  }

  answerCorrectCtrl(index: number): FormControl<boolean> {
    return getAnswerCorrectControl(this.form(), index);
  }

  answerContentCtrl(index: number, lang: LangCode): FormControl<string> {
    return getAnswerContentControl(this.form(), index, lang);
  }

  hasContentContext(): boolean {
    return !this.showDomainSelect() || !!this.form().controls.domain.value;
  }

  submit(): void {
    this.submitted.emit();
  }

  onTabChange(value: string | number | undefined): void {
    this.tabChanged.emit(value);
  }

  onTranslateActive(): void {
    this.translateActive.emit();
  }

  practiceTooltipText(): string | undefined {
    return this.practiceTooltip() ?? undefined;
  }

  onAddOption(): void {
    this.addOptionClicked.emit();
  }

  onRemoveOption(index: number): void {
    this.removeOptionClicked.emit(index);
  }

  onCancel(): void {
    this.cancelClicked.emit();
  }

  onDelete(): void {
    this.deleteClicked.emit();
  }

  onDuplicate(): void {
    this.duplicateClicked.emit();
  }

  onCleanActive(): void {
    this.cleanActiveClicked.emit();
  }
}
