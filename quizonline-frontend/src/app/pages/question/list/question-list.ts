import {CommonModule} from '@angular/common';
import {Component, computed, inject, OnInit, signal} from '@angular/core';
import {FormsModule} from '@angular/forms';
import {forkJoin} from 'rxjs';

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
  readonly text = computed(() => this.getText());
  totalRecords = signal(0);
  rows = signal(10);
  first = signal(0);

  questions = signal<QuestionReadDto[]>([]);
  subjects = signal<SubjectReadDto[]>([]);
  currentLang = signal<LanguageEnumDto>(LanguageEnumDto.En);
  q = signal('');
  selectedSubjectIds = signal<number[]>([]);
  previewQuestionId = signal<number | null>(null);

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
    return this.questions().map((question) => ({
      id: question.id,
      question,
      title: this.getTitle(question),
      active: !!question.active,
      modesText: this.getModes(question).join(', '),
      domainName: this.getDomain(question.domain),
      subjectsText: (question.subjects ?? []).map((subject) => this.getSubjectTitle(subject)).join(', '),
      subjectIds: (question.subjects ?? []).map((subject) => subject.id),
    }));
  });

  readonly filteredRows = computed<QuestionListRow[]>(() => {
    return this.rowsData();
  });

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
    this.loadQuestions(1);
  }

  onSubjectsChange(ids: number[] | null | undefined): void {
    this.selectedSubjectIds.set(ids ?? []);
    this.first.set(0);
    this.loadQuestions(1);
  }

  goNew(): void {
    this.questionService.goNew();
  }

  goImport(): void {
    this.questionService.goImport();
  }

  exportRows(): void {
    const headers = [
      'id',
      'title',
      'active',
      'modes',
      'domain',
      'subjects',
    ];
    const lines = this.filteredRows().map((row) => [
      row.id,
      row.title,
      row.active ? 'true' : 'false',
      row.modesText,
      row.domainName,
      row.subjectsText,
    ]);
    const csv = [
      headers.join(','),
      ...lines.map((line) => line.map((value) => this.escapeCsv(String(value ?? ''))).join(',')),
    ].join('\n');

    const blob = new Blob([csv], {type: 'text/csv;charset=utf-8;'});
    const url = URL.createObjectURL(blob);
    const anchor = document.createElement('a');
    anchor.href = url;
    anchor.download = 'questions-export.csv';
    anchor.click();
    URL.revokeObjectURL(url);
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

  private escapeCsv(value: string): string {
    const escaped = value.replace(/"/g, '""');
    return `"${escaped}"`;
  }

  private getText() {
    switch (this.userService.currentLang) {
      case LanguageEnumDto.Fr:
        return {
          title: 'Questions',
          subtitle: 'Recherche, liste et actions',
          searchPlaceholder: 'Rechercher...',
          subjectsPlaceholder: 'Filtrer par sujets',
          newQuestion: 'Nouveau',
          importQuestions: 'Importer',
          exportQuestions: 'Exporter',
          titleCol: 'Titre',
          activeCol: 'Actif',
          modesCol: 'Modes',
          domainsCol: 'Domaines',
          subjectsCol: 'Sujets',
          actionsCol: 'Actions',
          practice: 'Pratique',
          exam: 'Examen',
        };
      case LanguageEnumDto.Nl:
        return {
          title: 'Vragen',
          subtitle: 'Zoeken, lijst en acties',
          searchPlaceholder: 'Zoeken...',
          subjectsPlaceholder: 'Filter op onderwerpen',
          newQuestion: 'Nieuw',
          importQuestions: 'Importeren',
          exportQuestions: 'Exporteren',
          titleCol: 'Titel',
          activeCol: 'Actief',
          modesCol: 'Modi',
          domainsCol: 'Domeinen',
          subjectsCol: 'Onderwerpen',
          actionsCol: 'Acties',
          practice: 'Oefening',
          exam: 'Examen',
        };
      case LanguageEnumDto.It:
        return {
          title: 'Domande',
          subtitle: 'Ricerca, elenco e azioni',
          searchPlaceholder: 'Cerca...',
          subjectsPlaceholder: 'Filtra per argomenti',
          newQuestion: 'Nuovo',
          importQuestions: 'Importa',
          exportQuestions: 'Esporta',
          titleCol: 'Titolo',
          activeCol: 'Attiva',
          modesCol: 'Modalita',
          domainsCol: 'Domini',
          subjectsCol: 'Argomenti',
          actionsCol: 'Azioni',
          practice: 'Pratica',
          exam: 'Esame',
        };
      case LanguageEnumDto.Es:
        return {
          title: 'Preguntas',
          subtitle: 'Busqueda, lista y acciones',
          searchPlaceholder: 'Buscar...',
          subjectsPlaceholder: 'Filtrar por temas',
          newQuestion: 'Nuevo',
          importQuestions: 'Importar',
          exportQuestions: 'Exportar',
          titleCol: 'Titulo',
          activeCol: 'Activo',
          modesCol: 'Modos',
          domainsCol: 'Dominios',
          subjectsCol: 'Temas',
          actionsCol: 'Acciones',
          practice: 'Practica',
          exam: 'Examen',
        };
      case LanguageEnumDto.En:
      default:
        return {
          title: 'Questions',
          subtitle: 'Search, list and actions',
          searchPlaceholder: 'Search...',
          subjectsPlaceholder: 'Filter by subjects',
          newQuestion: 'New',
          importQuestions: 'Import',
          exportQuestions: 'Export',
          titleCol: 'Title',
          activeCol: 'Active',
          modesCol: 'Modes',
          domainsCol: 'Domains',
          subjectsCol: 'Subjects',
          actionsCol: 'Actions',
          practice: 'Practice',
          exam: 'Exam',
        };
    }
  }
}
