import {Component, inject, OnInit, signal} from '@angular/core';
import {FormsModule} from '@angular/forms';
import {QuestionService} from '../../../services/question/question';
import {Button} from 'primeng/button';
import {InputTextModule} from 'primeng/inputtext';
import {CommonModule} from '@angular/common';
import {PaginatorModule} from 'primeng/paginator';
import {TableModule} from 'primeng/table';
import {DomainReadDto, LanguageEnumDto, QuestionReadDto, SubjectReadDto} from '../../../api/generated';
import {UserService} from '../../../services/user/user';
import {selectTranslation} from '../../../shared/i18n/select-translation';
import {TooltipModule} from 'primeng/tooltip';
import {DomainService} from '../../../services/domain/domain';


@Component({
  standalone: true,
  selector: 'app-question-list',
  imports: [CommonModule, FormsModule, Button, InputTextModule, PaginatorModule, TableModule, TooltipModule ],
  templateUrl: './question-list.html',
  styleUrl: './question-list.scss'
})
export class QuestionList implements OnInit {
  questions = signal<QuestionReadDto[]>([]);
  currentLang = signal<LanguageEnumDto>(LanguageEnumDto.En);
  q = signal('');
  // 👉 ÉTAT DE PAGINATION
  first = 0;           // index de départ (offset)
  rows = 10;           // nb de lignes par page
  private questionService = inject(QuestionService);
  private userService:UserService = inject(UserService);
  private domainService:DomainService = inject(DomainService);

  ngOnInit() {
    this.currentLang.set(this.userService.currentLang ?? LanguageEnumDto.En);
    this.load();
  }

  load() {
    this.questionService
      .list({search: this.q() || undefined})
      .subscribe({
        next: (subs: QuestionReadDto[]) => {
          this.questions.set(subs);
          this.first = 0;
        },
        error: (err: unknown) => {
          console.error('Erreur lors du chargement des questions', err);
          this.questions.set([]);
        }
      });
  }

  onSearchChange(term: string) {
    this.q.set(term);
    this.load();
  }

  get pagedQuestions(): QuestionReadDto[] {
    const all = this.questions() || [];
    return all.slice(this.first, this.first + this.rows);
  }

  onPageChange(event: any) {
    this.first = event.first;   // index de départ
    this.rows = event.rows;     // nb d’items par page
  }

  goNew(): void {
    this.questionService.goNew();
  }

  goView(id: number): void {
    this.questionService.goView(id);
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

  goDomain(domain_id:number):void{
    return this.domainService.goEdit(domain_id);
  }


  getTitle(dto:QuestionReadDto):string{
    const tr = dto.translations as Record<string, { title?: string }>;
    const lang = String(this.currentLang()).toLowerCase();
    return tr?.[lang]?.title ?? `Question #${dto.id}`;
  }

  getDomain(dto:DomainReadDto):string{
    const t = selectTranslation<{ name: string }>(
    dto.translations as Record<string, { name: string }>,
    this.currentLang(),
  );
  return t?.name ?? `Domain #${dto.id}`;
  }

  getDescription(dto:QuestionReadDto):string{
    const tr = dto.translations as Record<string, { description?: string }>;
    const lang = String(this.currentLang()).toLowerCase();
    return tr?.[lang]?.description ?? `Description #${dto.id}`;
  }

  getSubjectTitle(dto: SubjectReadDto): string {
  const t = selectTranslation<{ name: string }>(
    dto.translations as Record<string, { name: string }>,
    this.currentLang(),
  );
  return t?.name ?? `Subject #${dto.id}`;
}
}
