import {Component, inject, OnInit, signal} from '@angular/core';
import {FormsModule} from '@angular/forms';
import {QuestionService} from '../../../services/question/question';
import {ButtonModule} from 'primeng/button';
import {InputTextModule} from 'primeng/inputtext';
import {CommonModule} from '@angular/common';
import {PaginatorModule} from 'primeng/paginator';
import {TableModule} from 'primeng/table';
import {DomainReadDto, LanguageEnumDto, QuestionReadDto, SubjectReadDto} from '../../../api/generated';
import {UserService} from '../../../services/user/user';
import {selectTranslation} from '../../../shared/i18n/select-translation';
import {DomainService} from '../../../services/domain/domain';
import {logApiError} from '../../../shared/api/api-errors';
import {QuestionPreviewDialogComponent} from '../../../components/question-preview-dialog/question-preview-dialog';


@Component({
  standalone: true,
  selector: 'app-question-list',
  imports: [
    CommonModule,
    FormsModule,
    ButtonModule,
    InputTextModule,
    PaginatorModule,
    TableModule,
    QuestionPreviewDialogComponent,
  ],
  templateUrl: './question-list.html',
  styleUrl: './question-list.scss'
})
export class QuestionList implements OnInit {
  questions = signal<QuestionReadDto[]>([]);
  currentLang = signal<LanguageEnumDto>(LanguageEnumDto.En);
  q = signal('');
  previewQuestionId = signal<number | null>(null);
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
    const currentDomainId = this.userService.currentUser()?.current_domain ?? undefined;
    this.questionService
      .list({
        search: this.q() || undefined,
        domainId: currentDomainId ?? undefined,
      })
      .subscribe({
        next: (subs: QuestionReadDto[]) => {
          this.questions.set(subs);
          this.first = 0;
        },
        error: (err: unknown) => {
          logApiError('question.list.load', err);
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

  getModes(dto: QuestionReadDto): string[] {
    const modes: string[] = [];
    if (dto.is_mode_practice) {
      modes.push('Pratique');
    }
    if (dto.is_mode_exam) {
      modes.push('Examen');
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
}
