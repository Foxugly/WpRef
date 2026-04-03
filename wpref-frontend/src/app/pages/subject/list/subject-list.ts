import {Component, computed, inject, OnInit, signal} from '@angular/core';
import {FormsModule} from '@angular/forms';
import {SubjectService, SubjectTranslationDto} from '../../../services/subject/subject';
import {ButtonModule} from 'primeng/button';
import {InputTextModule} from 'primeng/inputtext';
import {PaginatorModule} from 'primeng/paginator';
import {TableModule} from 'primeng/table';
import {LanguageEnumDto, SubjectReadDto} from '../../../api/generated';
import {StripPPipe} from '../../../shared/pipes/strip-p.pipe';
import {selectTranslation } from '../../../shared/i18n/select-translation';
import {UserService} from '../../../services/user/user';
import {DomainService} from '../../../services/domain/domain';
import {logApiError} from '../../../shared/api/api-errors';

@Component({
  standalone: true,
  selector: 'app-subject-list',
  imports: [FormsModule, ButtonModule, InputTextModule, PaginatorModule, TableModule, StripPPipe,],
  templateUrl: './subject-list.html',
  styleUrl: './subject-list.scss'
})
export class SubjectList implements OnInit {
  private subjectService : SubjectService = inject(SubjectService);
  private userService : UserService = inject(UserService);
  private domainService : DomainService = inject(DomainService)

  subjects = signal<SubjectReadDto[]>([]);
  q = signal('');
  currentLang = computed(():LanguageEnumDto => this.userService.currentLang);

  getSTDto(d:SubjectReadDto): SubjectTranslationDto{
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

  goDomain(domainId: number): void{
    this.domainService.goEdit(domainId);
  }
  // 📌 Pagination
  first = 0;  // index de départ
  rows = 10;  // nombre de lignes par page

  ngOnInit() {
    this.load();
  }

  load() {
    const currentDomainId = this.userService.currentUser()?.current_domain ?? undefined;
    this.subjectService
      .list({
        search: this.q() || undefined,
        domainId: currentDomainId ?? undefined,
      })
      .subscribe({
        next: (subs: SubjectReadDto[]) => {
          this.subjects.set(subs);
          this.first = 0;  // retour à la première page à chaque recherche
        },
        error: (err: unknown) => {
          logApiError('subject.list.load', err);
          this.subjects.set([]);
        }
      });
  }

  onSearchChange(term: string) {
    this.q.set(term);
    this.load();
  }

  // Liste paginée pour la page courante
  get pagedSubjects(): SubjectReadDto[] {
    const all = this.subjects() || [];
    return all.slice(this.first, this.first + this.rows);
  }

  // Handler appelé par p-paginator
  onPageChange(event: any) {
    this.first = event.first;
    this.rows = event.rows;
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
}
