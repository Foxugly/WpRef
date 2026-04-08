import {Component, computed, inject, OnInit, signal} from '@angular/core';
import {FormsModule} from '@angular/forms';
import {forkJoin} from 'rxjs';
import {SubjectService, SubjectTranslationDto} from '../../../services/subject/subject';
import {ButtonModule} from 'primeng/button';
import {InputTextModule} from 'primeng/inputtext';
import {PaginatorModule} from 'primeng/paginator';
import {TableModule} from 'primeng/table';
import {LanguageEnumDto, SubjectDetailDto, SubjectReadDto} from '../../../api/generated';
import {StripPPipe} from '../../../shared/pipes/strip-p.pipe';
import {selectTranslation } from '../../../shared/i18n/select-translation';
import {UserService} from '../../../services/user/user';
import {DomainService} from '../../../services/domain/domain';
import {logApiError} from '../../../shared/api/api-errors';

type SubjectListRow = SubjectReadDto & {
  name: string;
  description: string;
  domainName: string;
  questionsCount: number;
};

@Component({
  standalone: true,
  selector: 'app-subject-list',
  imports: [FormsModule, ButtonModule, InputTextModule, PaginatorModule, TableModule, StripPPipe],
  templateUrl: './subject-list.html',
  styleUrl: './subject-list.scss'
})
export class SubjectList implements OnInit {
  private subjectService: SubjectService = inject(SubjectService);
  private userService: UserService = inject(UserService);
  private domainService: DomainService = inject(DomainService);

  subjects = signal<SubjectReadDto[]>([]);
  questionCounts = signal<Record<number, number>>({});
  q = signal('');
  currentLang = computed((): LanguageEnumDto => this.userService.currentLang);
  rowsData = computed<SubjectListRow[]>(() => this.subjects().map((subject) => this.toRow(subject)));

  rows = 10;

  getSTDto(d: SubjectReadDto): SubjectTranslationDto {
    return <SubjectTranslationDto>selectTranslation<SubjectTranslationDto>(
      d.translations as unknown as Record<string, SubjectTranslationDto>,
      this.currentLang(),
    );
  }

  getName(d: SubjectReadDto): string {
    const t = this.getSTDto(d);
    return t?.name ?? '';
  }

  getDescription(d: SubjectReadDto): string {
    const t = this.getSTDto(d);
    return t?.description ?? '';
  }

  getDomain(d: SubjectReadDto): string {
    const t = this.getSTDto(d);
    return t?.domain?.name ?? `Domain #${d.domain}`;
  }

  goDomain(domainId: number): void {
    this.domainService.goEdit(domainId);
  }

  ngOnInit() {
    this.load();
  }

  load() {
    const currentDomainId = this.userService.currentUser()?.current_domain ?? undefined;
    this.subjectService.list({
      search: this.q() || undefined,
      domainId: currentDomainId ?? undefined,
    }).subscribe({
      next: (subjects) => {
        this.subjects.set(subjects);

        if (!subjects.length) {
          this.questionCounts.set({});
          return;
        }

        forkJoin(
          subjects.map((subject) => this.subjectService.detail(subject.id)),
        ).subscribe({
          next: (details) => {
            this.questionCounts.set(this.buildSubjectQuestionCounts(details));
          },
          error: (err: unknown) => {
            logApiError('subject.list.counts', err);
            this.questionCounts.set({});
          },
        });
      },
      error: (err: unknown) => {
        logApiError('subject.list.load', err);
        this.subjects.set([]);
        this.questionCounts.set({});
      }
    });
  }

  onSearchChange(term: string) {
    this.q.set(term);
    this.load();
  }

  goNew() {
    this.subjectService.goNew();
  }

  goEdit(id: number) {
    this.subjectService.goEdit(id);
  }

  goDelete(id: number) {
    this.subjectService.goDelete(id);
  }

  getQuestionCount(subjectId: number): number {
    return this.questionCounts()[subjectId] ?? 0;
  }

  private buildSubjectQuestionCounts(details: SubjectDetailDto[]): Record<number, number> {
    return details.reduce<Record<number, number>>((counts, detail) => {
      counts[detail.id] = detail.questions?.length ?? 0;
      return counts;
    }, {});
  }

  private toRow(subject: SubjectReadDto): SubjectListRow {
    return {
      ...subject,
      name: this.getName(subject),
      description: this.getDescription(subject),
      domainName: this.getDomain(subject),
      questionsCount: this.getQuestionCount(subject.id),
    };
  }
}
