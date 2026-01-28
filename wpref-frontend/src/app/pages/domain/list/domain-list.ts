import {Component, computed, inject, OnInit, signal} from '@angular/core';
import {FormsModule} from '@angular/forms';
import {Button} from 'primeng/button';
import {InputTextModule} from 'primeng/inputtext';
import {PaginatorModule} from 'primeng/paginator';
import {TableModule} from 'primeng/table';
import {DomainReadDto, LanguageEnumDto, SubjectReadDto} from '../../../api/generated';
import {DomainService, DomainTranslationDto} from '../../../services/domain/domain';
import {StripPPipe} from '../../../shared/pipes/strip-p.pipe';
import {selectTranslation} from '../../../shared/i18n/select-translation';
import {UserService} from '../../../services/user/user';


type LangCode = `${LanguageEnumDto}`;

@Component({
  selector: 'app-domain-list',
  imports: [FormsModule, Button, InputTextModule, PaginatorModule, TableModule, StripPPipe],
  templateUrl: './domain-list.html',
  styleUrl: './domain-list.scss',
})
export class DomainList implements OnInit{
  private domainService = inject(DomainService);
  private userService : UserService = inject(UserService);
  domains = signal<DomainReadDto[]>([]);
  q = signal('');
  currentLang = computed(() => this.userService.currentLang);

  getDTDto(d: SubjectReadDto): DomainTranslationDto{
    return <DomainTranslationDto>selectTranslation<DomainTranslationDto>(
      d.translations as unknown as Record<string, DomainTranslationDto>,
      this.currentLang(),
    );
  }
  getName(d: SubjectReadDto): string {
    const t= this.getDTDto(d);
    return t?.name ?? '';
  }

  getDescription(d: SubjectReadDto): string {
    const t= this.getDTDto(d);
    return t?.description ?? '';
  }


  // 📌 Pagination
  first = 0;  // index de départ
  rows = 10;  // nombre de lignes par page

  ngOnInit() {
    this.load();
  }

  load() {
    this.domainService
      .list({search: this.q() || undefined})
      .subscribe({
        next: (doms: DomainReadDto[]) => {
          this.domains.set(doms);
          this.first = 0;  // retour à la première page à chaque recherche
        },
        error: (err: unknown) => {
          console.error('Erreur lors du chargement des sujets', err);
          this.domains.set([]);
        }
      });
  }

  onSearchChange(term: string) {
    this.q.set(term);
    this.load();
  }

  // Liste paginée pour la page courante
  get pagedDomains(): DomainReadDto[] {
    const all = this.domains() || [];
    return all.slice(this.first, this.first + this.rows);
  }

  // Handler appelé par p-paginator
  onPageChange(event: any) {
    this.first = event.first;
    this.rows = event.rows;
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
}
