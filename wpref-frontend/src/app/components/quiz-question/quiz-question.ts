import {
  Component,
  DestroyRef,
  EventEmitter,
  inject,
  Input,
  OnChanges,
  Output,
  signal,
  SimpleChanges,
} from '@angular/core';
import {takeUntilDestroyed} from '@angular/core/rxjs-interop';
import {CommonModule} from '@angular/common';
import {DomSanitizer, SafeResourceUrl} from '@angular/platform-browser';
import {CardModule} from 'primeng/card';
import {ChipModule} from 'primeng/chip';
import {CheckboxModule} from 'primeng/checkbox';
import {RadioButtonModule} from 'primeng/radiobutton';
import {ImageModule} from 'primeng/image';
import {ButtonModule} from 'primeng/button';
import {FormsModule} from '@angular/forms';
import {ToggleButtonModule} from 'primeng/togglebutton';
import {QuizNavItem} from '../quiz-nav/quiz-nav';
import {
  LanguageEnumDto,
  QuestionAnswerOptionReadDto,
  QuestionMediaReadDto,
  QuestionReadDto
} from '../../api/generated';
import {UserService} from '../../services/user/user';
import {isYoutubeUrl, toYoutubeEmbedUrl} from '../../shared/media/youtube';

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
  userService: UserService = inject(UserService);

  @Input({required: true}) quizNavItem!: QuizNavItem;
  @Input() showCorrectAnswers = false;
  @Input() readonlyMode = false;
  @Input() displayMode: 'preview' | 'exam' = 'preview';
  @Input() hasPrevious = false;
  @Input() hasNext = false;
  @Input() showFooter = true;

  @Output() answeredToggled = new EventEmitter<void>();
  @Output() flagToggled = new EventEmitter<boolean>();
  @Output() reportRequested = new EventEmitter<void>();
  @Output() goNext = new EventEmitter<AnswerPayload>();
  @Output() goPrevious = new EventEmitter<AnswerPayload>();
  @Output() goBack = new EventEmitter<void>();
  @Output() finish = new EventEmitter<AnswerPayload>();

  currentLang = signal<LanguageEnumDto>(LanguageEnumDto.Fr);
  selectedOptionIds: number[] = [];
  selectedRadioId: number | null = null;

  private sanitizer = inject(DomSanitizer);
  private destroyRef = inject(DestroyRef);

  constructor() {
    this.currentLang.set(this.userService.currentLang ?? LanguageEnumDto.Fr);
    this.userService.lang$
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe((lang) => {
        this.currentLang.set(lang ?? LanguageEnumDto.Fr);
      });
  }

  get question(): QuestionReadDto {
    return this.quizNavItem.question;
  }

  get allowMultiple(): boolean {
    return !!this.quizNavItem.question.allow_multiple_correct;
  }

  onSelectRadio(optionId: number | null): void {
    if (this.readonlyMode) {
      return;
    }
    this.selectedRadioId = optionId;
    this.selectedOptionIds = optionId == null ? [] : [optionId];
  }

  onNextClick(): void {
    if (this.readonlyMode) {
      if (this.hasNext) {
        this.goNext.emit(this.buildPayload());
        return;
      }
      this.finish.emit(this.buildPayload());
      return;
    }
    const payload = this.buildPayload();
    if (this.hasNext) {
      this.goNext.emit(payload);
      return;
    }
    this.finish.emit(payload);
  }

  onPreviousClick(): void {
    this.goPrevious.emit(this.buildPayload());
  }

  onBackClick(): void {
    this.goBack.emit();
  }

  onToggleCheckbox(optionId: number | undefined, checked: boolean): void {
    if (this.readonlyMode) {
      return;
    }
    if (optionId == null) {
      return;
    }

    if (checked) {
      if (!this.selectedOptionIds.includes(optionId)) {
        this.selectedOptionIds = [...this.selectedOptionIds, optionId];
      }
      return;
    }

    this.selectedOptionIds = this.selectedOptionIds.filter(id => id !== optionId);
  }

  isChecked(optionId?: number): boolean {
    if (optionId == null) {
      return false;
    }

    const source = this.readonlyMode
      ? (this.quizNavItem?.selectedOptionIds ?? this.selectedOptionIds)
      : this.selectedOptionIds;

    return source.includes(optionId);
  }

  isCorrectOption(option: QuestionAnswerOptionReadDto): boolean {
    return option.is_correct === true;
  }

  hasCorrection(option: QuestionAnswerOptionReadDto): boolean {
    return option.is_correct === true || option.is_correct === false;
  }

  isSelectedWrongOption(option: QuestionAnswerOptionReadDto): boolean {
    return this.hasCorrection(option) && this.isChecked(option.id) && !this.isCorrectOption(option);
  }

  answerLineClass(option: QuestionAnswerOptionReadDto): string {
    if (this.canShowCorrectionState() && this.hasCorrection(option) && this.isCorrectOption(option)) {
      return 'answer-line answer-line--correct';
    }

    if (this.canShowCorrectionState() && this.isSelectedWrongOption(option)) {
      return 'answer-line answer-line--wrong';
    }

    if (this.readonlyMode) {
      return 'answer-line answer-line--readonly';
    }

    return 'answer-line';
  }

  ngOnChanges(changes: SimpleChanges): void {
    if (!changes['quizNavItem'] || !this.quizNavItem) {
      return;
    }

    const ids = this.quizNavItem.selectedOptionIds ?? [];
    this.selectedOptionIds = [...ids];
    this.selectedRadioId = ids.length ? ids[0] : null;
  }

  mediaSrc(m: QuestionMediaReadDto): string {
    return (m.asset.file as string | null) || m.asset.external_url || '';
  }

  externalSafeUrl(m: QuestionMediaReadDto): SafeResourceUrl | null {
    const raw = m.asset.external_url || '';
    const embed = toYoutubeEmbedUrl(raw);

    if (!embed) {
      return null;
    }

    return this.sanitizer.bypassSecurityTrustResourceUrl(embed);
  }

  externalLinkUrl(m: QuestionMediaReadDto): string | null {
    return m.asset.external_url || null;
  }

  isYoutubeMedia(m: QuestionMediaReadDto): boolean {
    return isYoutubeUrl(m.asset.external_url || '');
  }

  stripOuterP(html: string): string {
    if (!html) {
      return html;
    }

    const trimmed = html.trim();
    let inner = trimmed;

    if (trimmed.startsWith('<p') && trimmed.endsWith('</p>')) {
      const startTagEnd = trimmed.indexOf('>') + 1;
      const endTagStart = trimmed.lastIndexOf('</p>');
      inner = trimmed.substring(startTagEnd, endTagStart).trim();
    }

    return inner
      .replace(/&nbsp;/g, ' ')
      .replace(/\u00A0/g, ' ');
  }

  protected getT(question: QuestionReadDto): any {
    const lang: LanguageEnumDto = this.currentLang();
    const translations: any = question.translations;
    return translations?.[lang] ?? Object.values(translations ?? {})[0] ?? null;
  }

  protected getTitle(question: QuestionReadDto): string {
    return this.getT(question)?.title?.trim() ?? '';
  }

  protected getDescription(question: QuestionReadDto): string {
    return this.getT(question)?.description?.trim() ?? '';
  }

  protected getExplanation(question: QuestionReadDto): string {
    return this.getT(question)?.explanation?.trim() ?? '';
  }

  protected getAnswerContent(option: QuestionAnswerOptionReadDto): string {
    const lang = this.currentLang();
    const current = option.translations?.[lang]?.content?.trim();

    if (current) {
      return current;
    }

    const fallback = Object.values(option.translations ?? {})
      .map((translation) => translation.content?.trim())
      .find((content) => !!content);

    return fallback ?? option.content ?? '';
  }

  protected canShowCorrectionState(): boolean {
    return this.readonlyMode || (this.displayMode === 'preview' && this.showCorrectAnswers);
  }

  private buildPayload(): AnswerPayload {
    return {
      questionId: this.question.id,
      index: this.quizNavItem.index,
      selectedOptionIds: this.selectedOptionIds,
    };
  }
}
