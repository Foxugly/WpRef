import {CommonModule} from '@angular/common';
import {Component, computed, DestroyRef, inject, OnInit, signal} from '@angular/core';
import {takeUntilDestroyed} from '@angular/core/rxjs-interop';
import {FormsModule} from '@angular/forms';
import {Router} from '@angular/router';
import {catchError, finalize, forkJoin, map, of} from 'rxjs';
import {TabsModule} from 'primeng/tabs';
import {ButtonModule} from 'primeng/button';
import {InputTextModule} from 'primeng/inputtext';
import {LanguageEnumDto, QuizListDto} from '../../../api/generated';
import {QuizSessionTableComponent} from '../../../components/quiz-session-table/quiz-session-table';
import {QuizTemplateTableComponent} from '../../../components/quiz-template-table/quiz-template-table';
import {QuizTemplateAssignDialogComponent} from '../../../components/quiz-template-assign-dialog/quiz-template-assign-dialog';
import {QuizService} from '../../../services/quiz/quiz';
import {UserService} from '../../../services/user/user';
import {logApiError, userFacingApiMessage} from '../../../shared/api/api-errors';
import {AssignableRecipient, QuizTemplateListItem, UserQuizListItem} from './quiz-list.models';
import {DomainService} from '../../../services/domain/domain';
import {DomainReadDto, UserSummaryDto} from '../../../api/generated';
import {getQuizListUiText} from './quiz-list.i18n';
import {ROUTES} from '../../../app.routes-paths';

type DomainReadWithMembers = DomainReadDto & {
  members?: UserSummaryDto[];
};

@Component({
  selector: 'app-quiz-list',
  imports: [
    CommonModule,
    FormsModule,
    ButtonModule,
    InputTextModule,
    TabsModule,
    QuizTemplateTableComponent,
    QuizSessionTableComponent,
    QuizTemplateAssignDialogComponent,
  ],
  templateUrl: './quiz-list.html',
  styleUrl: './quiz-list.scss',
})
export class QuizListPage implements OnInit {
  templates = signal<QuizTemplateListItem[]>([]);
  domains = signal<DomainReadDto[]>([]);
  myQuizzes = signal<UserQuizListItem[]>([]);
  assignableUsers = signal<AssignableRecipient[]>([]);
  activeTab = signal<'templates' | 'sessions'>('templates');
  currentUserId = signal<number | null>(null);
  q = signal('');
  loading = signal(false);
  success = signal<string | null>(null);
  creatingTemplateId = signal<number | null>(null);
  assignDialogVisible = signal(false);
  selectedTemplate = signal<QuizTemplateListItem | null>(null);
  selectedRecipientIds = signal<number[]>([]);
  assigning = signal(false);

  private readonly quizService = inject(QuizService);
  private readonly userService = inject(UserService);
  private readonly router = inject(Router);
  private readonly destroyRef = inject(DestroyRef);
  private readonly domainService = inject(DomainService);

  readonly canComposeTemplate = computed(() => this.domains().some((domain) => this.canManageDomain(domain)));
  readonly canCreateQuickTemplate = computed(() => this.domains().length > 0);
  readonly currentLang = computed(() => this.userService.currentLang ?? LanguageEnumDto.Fr);
  readonly uiText = computed(() => getQuizListUiText(this.currentLang()));

  readonly filteredTemplates = computed(() => {
    const term = this.normalize(this.q());
    return this.templates().filter((template) =>
      !term || this.matchesSearch(term, template.title, template.description ?? '', template.mode ?? ''),
    );
  });

  readonly filteredMyQuizzes = computed(() => {
    const term = this.normalize(this.q());
    if (!term) {
      return this.myQuizzes();
    }

    return this.myQuizzes().filter((quiz) =>
      this.matchesSearch(term, quiz.quiz_template_title, quiz.quiz_template_description, quiz.mode),
    );
  });

  ngOnInit(): void {
    this.load();
  }

  setActiveTab(value: string | number | undefined): void {
    this.activeTab.set(value === 'sessions' ? 'sessions' : 'templates');
  }

  load(): void {
    this.loading.set(true);
    this.loadQuizListData()
      .pipe(
        takeUntilDestroyed(this.destroyRef),
        finalize(() => this.loading.set(false)),
      )
      .subscribe({
        next: ({currentUserId, templates, myQuizzes, domains}) => {
          this.currentUserId.set(currentUserId);
          this.domains.set(domains);
          this.templates.set(templates);
          this.myQuizzes.set(myQuizzes);
        },
        error: (err: unknown) => {
          logApiError('quiz.list.load', err);
          this.success.set(userFacingApiMessage(err, this.uiText().messages.loadError));
          this.currentUserId.set(null);
          this.domains.set([]);
          this.templates.set([]);
          this.myQuizzes.set([]);
        },
      });
  }

  goNew(): void {
    this.quizService.goSubject();
  }

  goCompose(): void {
    this.quizService.goCompose();
  }

  goEditTemplate(templateId: number): void {
    this.router.navigate(['/quiz/template', templateId, 'edit']);
  }

  goDeleteTemplate(templateId: number): void {
    this.router.navigate(['/quiz/template', templateId, 'delete']);
  }

  openAssignDialog(template: QuizTemplateListItem): void {
    this.selectedTemplate.set(template);
    this.selectedRecipientIds.set([]);
    this.assignableUsers.set(this.buildAssignableUsers(template));
    this.assignDialogVisible.set(true);
    this.success.set(null);
  }

  closeAssignDialog(): void {
    this.assignDialogVisible.set(false);
    this.selectedTemplate.set(null);
    this.selectedRecipientIds.set([]);
  }

  submitAssignments(): void {
    const template = this.selectedTemplate();
    const userIds = this.selectedRecipientIds();
    if (!template || !userIds.length) {
      return;
    }

    this.assigning.set(true);
    this.quizService.assignTemplateToUsers(template.id, userIds)
      .pipe(
        takeUntilDestroyed(this.destroyRef),
        finalize(() => this.assigning.set(false)),
      )
      .subscribe({
        next: (created) => {
          this.success.set(this.uiText().messages.assignSuccess(created.length));
          this.closeAssignDialog();
          void this.router.navigate(ROUTES.quiz.list());
        },
        error: (err: unknown) => {
          logApiError('quiz.list.assign-template', err);
          this.success.set(userFacingApiMessage(err, this.uiText().messages.assignError));
        },
      });
  }

  goResults(templateId: number): void {
    void this.router.navigate(ROUTES.quiz.templateResults(templateId));
  }

  createFromTemplate(templateId: number): void {
    this.creatingTemplateId.set(templateId);
    this.quizService
      .createQuizFromTemplate(templateId)
      .pipe(
        takeUntilDestroyed(this.destroyRef),
        finalize(() => this.creatingTemplateId.set(null)),
      )
      .subscribe({
        next: (quiz) => this.quizService.goView(quiz.id),
        error: (err: unknown) => {
          logApiError('quiz.list.create-session', err);
          this.success.set(userFacingApiMessage(err, this.uiText().messages.createError));
        },
      });
  }

  goView(id: number): void {
    this.quizService.goView(id);
  }

  private getCurrentUser() {
    const currentUser = this.userService.currentUser();
    if (currentUser) {
      return of(currentUser);
    }

    return this.userService.getMe().pipe(catchError(() => of(null)));
  }

  private loadQuizListData() {
    return forkJoin({
      templates: this.quizService.listTemplates(),
      quizzes: this.quizService.listQuiz(),
      domains: this.domainService.list(),
      me: this.getCurrentUser(),
    }).pipe(
      map(({templates, quizzes, domains, me}) => {
        const currentUserId = me?.id ?? null;
        const normalizedTemplates = (templates as QuizTemplateListItem[])
          .map((template) => this.decorateTemplate(template, domains, me))
          .sort((left, right) => left.title.localeCompare(right.title));
        const myQuizSessions = me ? quizzes.filter((quiz) => quiz.user === me.id) : [];

        return {
          currentUserId,
          domains,
          templates: normalizedTemplates,
          myQuizzes: myQuizSessions.map((quiz) => this.toUserQuizListItem(quiz)),
        };
      }),
    );
  }

  private toUserQuizListItem(quiz: QuizListDto): UserQuizListItem {
    return {
      ...quiz,
      status: quiz.ended_at ? 'answered' : (quiz.started_at ? 'in_progress' : 'not_started'),
    };
  }

  private matchesSearch(term: string, ...values: string[]): boolean {
    return values.some((value) => this.normalize(value).includes(term));
  }

  private decorateTemplate(
    template: QuizTemplateListItem,
    domains: DomainReadDto[],
    me: { id: number; is_staff?: boolean; is_superuser?: boolean } | null,
  ): QuizTemplateListItem {
    const domain = domains.find((item) => item.id === template.domain);
    const managesDomain = !!me && !!domain && this.canManageDomain(domain);
    const isCreator = !!me && template.created_by === me.id;

    return {
      ...template,
      ownerLabel: template.created_by_username || (template.created_by ? `User #${template.created_by}` : '-'),
      canManage: managesDomain,
      canAssign: managesDomain,
      canEdit: managesDomain,
      canDelete: managesDomain || isCreator,
      canViewResults: managesDomain,
    };
  }

  private buildAssignableUsers(template: QuizTemplateListItem): AssignableRecipient[] {
    const domain = this.domains().find((item) => item.id === template.domain) as DomainReadWithMembers | undefined;
    if (!domain) {
      return [];
    }

    const currentUserId = this.currentUserId();
    const recipients = new Map<number, AssignableRecipient>();
    const addRecipient = (user: UserSummaryDto | null | undefined, role: AssignableRecipient['role']) => {
      if (!user || user.id === currentUserId) {
        return;
      }
      const existing = recipients.get(user.id);
      if (existing) {
        if (existing.role === 'member' && role !== 'member') {
          recipients.set(user.id, {...existing, role});
        }
        return;
      }
      recipients.set(user.id, {id: user.id, username: user.username, role});
    };

    addRecipient(domain.owner, 'owner');
    for (const managerUser of domain.managers ?? []) {
      addRecipient(managerUser, 'manager');
    }
    for (const member of domain.members ?? []) {
      addRecipient(member, 'member');
    }

    return [...recipients.values()].sort((left, right) => left.username.localeCompare(right.username));
  }

  private canManageDomain(domain: DomainReadDto): boolean {
    const me = this.userService.currentUser();
    if (!me) {
      return false;
    }
    if (me.is_superuser) {
      return true;
    }
    return domain.owner?.id === me.id || (domain.managers ?? []).some((user) => user.id === me.id);
  }

  private normalize(value: string | null | undefined): string {
    return (value ?? '').trim().toLocaleLowerCase();
  }
}
