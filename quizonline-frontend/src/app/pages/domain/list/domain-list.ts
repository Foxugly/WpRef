import {Component, computed, inject, OnInit, signal} from '@angular/core';
import {FormsModule} from '@angular/forms';
import {ButtonModule} from 'primeng/button';
import {InputTextModule} from 'primeng/inputtext';
import {PaginatorModule} from 'primeng/paginator';
import {TableModule} from 'primeng/table';
import {DomainReadDto, LanguageEnumDto} from '../../../api/generated';
import {DomainService, DomainTranslationDto} from '../../../services/domain/domain';
import {StripPPipe} from '../../../shared/pipes/strip-p.pipe';
import {selectTranslation} from '../../../shared/i18n/select-translation';
import {UserService} from '../../../services/user/user';
import {logApiError} from '../../../shared/api/api-errors';

type LangCode = `${LanguageEnumDto}`;
type DomainListRow = DomainReadDto & {
  name: string;
  description: string;
  subjectsCount: number;
  questionsCount: number;
};

@Component({
  selector: 'app-domain-list',
  imports: [FormsModule, ButtonModule, InputTextModule, PaginatorModule, TableModule, StripPPipe],
  templateUrl: './domain-list.html',
  styleUrl: './domain-list.scss',
})
export class DomainList implements OnInit {
  private domainService = inject(DomainService);
  private userService: UserService = inject(UserService);

  domains = signal<DomainReadDto[]>([]);
  q = signal('');
  currentLang = computed(() => this.userService.currentLang);
  rowsData = computed<DomainListRow[]>(() => this.domains().map((domain) => this.toRow(domain)));

  rows = 10;

  getDTDto(d: DomainReadDto): DomainTranslationDto {
    return <DomainTranslationDto>selectTranslation<DomainTranslationDto>(
      d.translations as unknown as Record<string, DomainTranslationDto>,
      this.currentLang(),
    );
  }

  getName(d: DomainReadDto): string {
    const t = this.getDTDto(d);
    return t?.name ?? '';
  }

  getDescription(d: DomainReadDto): string {
    const t = this.getDTDto(d);
    return t?.description ?? '';
  }

  ngOnInit() {
    this.load();
  }

  load() {
    this.domainService.list({search: this.q() || undefined}).subscribe({
      next: (domains) => {
        this.domains.set(domains);
      },
      error: (err: unknown) => {
        logApiError('domain.list.load', err);
        this.domains.set([]);
      }
    });
  }

  onSearchChange(term: string) {
    this.q.set(term);
    this.load();
  }

  goNew() {
    this.domainService.goNew();
  }

  goEdit(id: number) {
    this.domainService.goEdit(id);
  }

  goDelete(id: number) {
    this.domainService.goDelete(id);
  }

  private toRow(domain: DomainReadDto): DomainListRow {
    const domainWithCounts = domain as DomainReadDto & { subjects_count?: number; questions_count?: number };
    return {
      ...domain,
      name: this.getName(domain),
      description: this.getDescription(domain),
      subjectsCount: domainWithCounts.subjects_count ?? 0,
      questionsCount: domainWithCounts.questions_count ?? 0,
    };
  }
}
