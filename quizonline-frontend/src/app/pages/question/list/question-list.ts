import {CommonModule} from '@angular/common';
import {Component, computed, inject, OnInit, signal} from '@angular/core';
import {FormsModule} from '@angular/forms';

import {ButtonModule} from 'primeng/button';
import {InputTextModule} from 'primeng/inputtext';
import {MultiSelectModule} from 'primeng/multiselect';
import {TableModule} from 'primeng/table';

import {DomainReadDto, LanguageEnumDto, QuestionReadDto, SubjectReadDto} from '../../../api/generated';
import {QuestionPreviewDialogComponent} from '../../../components/question-preview-dialog/question-preview-dialog';
import {DomainService} from '../../../services/domain/domain';
import {QuestionService} from '../../../services/question/question';
import {SubjectService} from '../../../services/subject/subject';
import {UserService} from '../../../services/user/user';
import {logApiError} from '../../../shared/api/api-errors';
import {selectTranslation} from '../../../shared/i18n/select-translation';
import {getQuestionListUiText, QuestionListUiText} from './question-list.i18n';

type QuestionListRow = {
  id: number;
  question: QuestionReadDto;
  title: string;
  active: boolean;
  modesText: string;
  domainName: string;
  subjectsText: string;
  subjectIds: number[];
};

@Component({
  standalone: true,
  selector: 'app-question-list',
  imports: [
    CommonModule,
    FormsModule,
    ButtonModule,
    InputTextModule,
    MultiSelectModule,
    TableModule,
    QuestionPreviewDialogComponent,
  ],
  templateUrl: './question-list.html',
  styleUrl: './question-list.scss'
})
export class QuestionList implements OnInit {
  readonly text = computed<QuestionListUiText>(() => getQuestionListUiText(this.userService.currentLang));
  totalRecords = signal(0);
  rows = signal(10);
  first = signal(0);
  selectingAll = signal(false);

  questions = signal<QuestionReadDto[]>([]);
  subjects = signal<SubjectReadDto[]>([]);
  currentLang = signal<LanguageEnumDto>(LanguageEnumDto.En);
  q = signal('');
  selectedSubjectIds = signal<number[]>([]);
  previewQuestionId = signal<number | null>(null);
  selectedRows = signal<QuestionListRow[]>([]);

  private questionService = inject(QuestionService);
  private subjectService = inject(SubjectService);
  private userService: UserService = inject(UserService);
  private domainService: DomainService = inject(DomainService);

  readonly subjectOptions = computed<Array<{ label: string; value: number }>>(() => {
    return this.subjects().map((subject) => ({
      label: this.getSubjectTitle(subject),
      value: subject.id,
    }));
  });

  readonly rowsData = computed<QuestionListRow[]>(() => {
    return this.questions().map((question) => this.toRow(question));
  });

  readonly selectedCount = computed(() => this.selectedRows().length);
  readonly allFilteredSelected = computed(() => this.totalRecords() > 0 && this.selectedRows().length === this.totalRecords());
  readonly someFilteredSelected = computed(() => this.selectedRows().length > 0 && !this.allFilteredSelected());

  ngOnInit() {
    this.currentLang.set(this.userService.currentLang ?? LanguageEnumDto.En);
    this.loadSubjects();
    this.loadQuestions(1);
  }

  loadSubjects(): void {
    const currentDomainId = this.userService.currentUser()?.current_domain ?? undefined;
    this.subjectService.list({
      domainId: currentDomainId ?? undefined,
      active: true,
    }).subscribe({
      next: (subjects) => {
        this.subjects.set(subjects);
      },
      error: (err: unknown) => {
        logApiError('question.list.subjects', err);
        this.subjects.set([]);
      }
    });
  }

  loadQuestions(page: number): void {
    const currentDomainId = this.userService.currentUser()?.current_domain ?? undefined;
    this.questionService.listPage({
      search: this.q() || undefined,
      subjectIds: this.selectedSubjectIds(),
      domainId: currentDomainId ?? undefined,
      page,
      pageSize: this.rows(),
    }).subscribe({
      next: (questions) => {
        this.questions.set(questions.results ?? []);
        this.totalRecords.set(questions.count ?? 0);
      },
      error: (err: unknown) => {
        logApiError('question.list.load', err);
        this.questions.set([]);
        this.totalRecords.set(0);
      }
    });
  }

  onSearchChange(term: string) {
    this.q.set(term);
    this.first.set(0);
    this.selectedRows.set([]);
    this.loadQuestions(1);
  }

  onSubjectsChange(ids: number[] | null | undefined): void {
    this.selectedSubjectIds.set(ids ?? []);
    this.first.set(0);
    this.selectedRows.set([]);
    this.loadQuestions(1);
  }

  onSelectionChange(rows: QuestionListRow[]): void {
    this.selectedRows.set(rows);
  }

  toggleSelectAllFiltered(checked: boolean): void {
    if (!checked) {
      this.selectedRows.set([]);
      return;
    }

    const currentDomainId = this.userService.currentUser()?.current_domain ?? undefined;
    this.selectingAll.set(true);
    this.questionService.list({
      search: this.q() || undefined,
      subjectIds: this.selectedSubjectIds(),
      domainId: currentDomainId ?? undefined,
    }).subscribe({
      next: (questions) => {
        this.selectedRows.set((questions ?? []).map((question) => this.toRow(question)));
      },
      error: (err: unknown) => {
        logApiError('question.list.select-all', err);
        this.selectingAll.set(false);
      },
      complete: () => this.selectingAll.set(false),
    });
  }

  goNew(): void {
    this.questionService.goNew();
  }

  goImport(): void {
    this.questionService.goImport();
  }

  exportRows(): void {
    const currentDomainId = this.userService.currentUser()?.current_domain ?? undefined;
    const selected = this.selectedRows();
    if (!currentDomainId || !selected.length) {
      return;
    }

    const questionIds = selected.map(row => row.id);
    this.questionService.exportStructured(currentDomainId, questionIds).subscribe({
      next: ({blob, filename}) => {
        const url = URL.createObjectURL(blob);
        const anchor = document.createElement('a');
        anchor.href = url;
        anchor.download = filename;
        anchor.click();
        URL.revokeObjectURL(url);
      },
      error: (err: unknown) => {
        logApiError('question.list.export', err);
      },
    });
  }

  onPageChange(event: { first?: number; rows?: number; page?: number }): void {
    this.first.set(event.first ?? 0);
    this.rows.set(event.rows ?? this.rows());
    this.loadQuestions((event.page ?? 0) + 1);
  }

  goView(id: number): void {
    this.previewQuestionId.set(id);
  }

  closePreview(): void {
    this.previewQuestionId.set(null);
  }

  goEdit(id: number): void {
    this.questionService.goEdit(id);
  }

  goDelete(id: number): void {
    this.questionService.goDelete(id);
  }

  goSubject(id: number): void {
    this.questionService.goSubjectEdit(id);
  }

  goDomain(domainId: number): void {
    this.domainService.goEdit(domainId);
  }

  getTitle(dto: QuestionReadDto): string {
    const tr = dto.translations as Record<string, { title?: string }>;
    const lang = String(this.currentLang()).toLowerCase();
    return tr?.[lang]?.title ?? `Question #${dto.id}`;
  }

  getDomain(dto: DomainReadDto): string {
    const t = selectTranslation<{ name: string }>(
      dto.translations as Record<string, { name: string }>,
      this.currentLang(),
    );
    return t?.name ?? `Domain #${dto.id}`;
  }

  getModes(dto: QuestionReadDto): string[] {
    const modes: string[] = [];
    if (dto.is_mode_practice) {
      modes.push(this.text().practice);
    }
    if (dto.is_mode_exam) {
      modes.push(this.text().exam);
    }
    return modes;
  }

  getSubjectTitle(dto: SubjectReadDto): string {
    const t = selectTranslation<{ name: string }>(
      dto.translations as Record<string, { name: string }>,
      this.currentLang(),
    );
    return t?.name ?? `Subject #${dto.id}`;
  }

  private toRow(question: QuestionReadDto): QuestionListRow {
    return {
      id: question.id,
      question,
      title: this.getTitle(question),
      active: !!question.active,
      modesText: this.getModes(question).join(', '),
      domainName: this.getDomain(question.domain),
      subjectsText: (question.subjects ?? []).map((subject) => this.getSubjectTitle(subject)).join(', '),
      subjectIds: (question.subjects ?? []).map((subject) => subject.id),
    };
  }
}
