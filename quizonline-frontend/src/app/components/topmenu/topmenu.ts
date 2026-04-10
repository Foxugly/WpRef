import {Component, DestroyRef, inject, OnInit, signal, ViewChild} from '@angular/core';
import {takeUntilDestroyed} from '@angular/core/rxjs-interop';
import {filter} from 'rxjs/operators';
import {NavigationEnd, Router, RouterLink, RouterLinkActive} from '@angular/router';
import {ButtonModule} from 'primeng/button';
import {Menu} from 'primeng/menu';
import {MenuItem} from 'primeng/api';

import {CustomUserReadDto, DomainReadDto, LanguageEnumDto} from '../../api/generated';
import {UserService} from '../../services/user/user';
import {LangSelectComponent} from '../lang-select/lang-select';
import {UserMenuComponent} from '../user-menu/user-menu';
import {SupportedLanguage} from '../../../environments/language';
import {ROUTES} from '../../app.routes-paths';
import {QuizAlertService} from '../../services/quiz-alert/quiz-alert';
import {getUiText} from '../../shared/i18n/ui-text';
import {DomainService, DomainTranslations} from '../../services/domain/domain';

declare global {
  interface Window {
    __APP__?: {
      name: string;
      version: string;
      author: string;
      year: string;
      logoSvg: string;
      logoIco: string;
      logoPng: string;
    };
  }
}

type NavItem = {
  label: string;
  link: readonly string[];
  accent?: boolean;
};

@Component({
  selector: 'app-topmenu',
  standalone: true,
  imports: [
    ButtonModule,
    Menu,
    RouterLink,
    RouterLinkActive,
    LangSelectComponent,
    UserMenuComponent,
  ],
  templateUrl: './topmenu.html',
  styleUrl: './topmenu.scss',
})
export class TopMenuComponent implements OnInit {
  @ViewChild('domainMenu') private readonly domainMenu?: Menu;

  private readonly router = inject(Router);
  private readonly userService = inject(UserService);
  private readonly domainService = inject(DomainService);
  private readonly quizAlertService = inject(QuizAlertService);
  private readonly destroyRef = inject(DestroyRef);
  app = window.__APP__!;
  currentLang: SupportedLanguage = this.userService.currentLang;
  readonly visibleDomains = signal<DomainReadDto[]>([]);

  get ui() {
    return getUiText(this.userService.currentLang);
  }

  get currentUser(): CustomUserReadDto | null {
    return this.userService.currentUser();
  }

  get currentDomainLabel(): string {
    return this.currentUser?.current_domain_title?.trim() || this.ui.topmenu.noDomains;
  }

  get canManageCurrentDomain(): boolean {
    const me = this.currentUser;
    if (!me) {
      return false;
    }
    if (me.is_superuser) {
      return true;
    }

    const currentDomainId = me.current_domain;
    if (!currentDomainId) {
      return false;
    }

    const currentDomain = this.visibleDomains().find((domain) => domain.id === currentDomainId);
    if (!currentDomain) {
      return false;
    }

    return currentDomain.owner?.id === me.id || (currentDomain.managers ?? []).some((user) => user.id === me.id);
  }

  get canAccessDomainsMenu(): boolean {
    const me = this.currentUser;
    if (!me) {
      return false;
    }
    if (me.is_superuser) {
      return true;
    }

    return this.visibleDomains().some(
      (domain) => domain.owner?.id === me.id || (domain.managers ?? []).some((user) => user.id === me.id),
    );
  }

  get navItems(): NavItem[] {
    const isAuthenticated = !!this.currentUser;
    const items: NavItem[] = [
    ];

    if (isAuthenticated) {
      items.push({
        label: this.ui.topmenu.quiz,
        link: ROUTES.quiz.list(),
      });
    }

    if (this.canManageCurrentDomain) {
      items.unshift(
        {
          label: this.ui.topmenu.subjects,
          link: ROUTES.subject.list(),
        },
        {
          label: this.ui.topmenu.questions,
          link: ROUTES.question.list(),
        },
      );
    }

    if (this.canAccessDomainsMenu) {
      items.unshift(
        {
          label: this.ui.topmenu.domains,
          link: ROUTES.domain.list(),
        },
      );
    }

    if (this.currentUser?.is_superuser) {
      items.unshift({
        label: 'Users',
        link: ROUTES.user.list(),
      });
    }

    items.push({
      label: this.ui.topmenu.about,
      link: ['/about'],
    });

    return items;
  }

  get domainMenuItems(): MenuItem[] {
    const me = this.currentUser;
    if (!me) {
      return [];
    }

    const owned = this.visibleDomains().filter((domain) => domain.owner?.id === me.id);
    const staffed = this.visibleDomains().filter(
      (domain) => domain.owner?.id !== me.id && (domain.managers ?? []).some((user) => user.id === me.id),
    );
    const linked = this.visibleDomains().filter(
      (domain) => domain.owner?.id !== me.id && !(domain.managers ?? []).some((user) => user.id === me.id),
    );

    return [
      ...this.buildDomainSection(this.ui.topmenu.ownedDomains, owned),
      {separator: true},
      ...this.buildDomainSection(this.ui.topmenu.staffDomains, staffed),
      {separator: true},
      ...this.buildDomainSection(this.ui.topmenu.linkedDomains, linked),
      {separator: true},
      {
        label: this.ui.topmenu.preferences,
        icon: 'pi pi-cog',
        command: () => void this.router.navigate(['/preferences']),
      },
    ];
  }

  ngOnInit(): void {
    this.refreshUserContext();
    this.router.events
      .pipe(filter((event) => event instanceof NavigationEnd))
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe(() => this.refreshUserContext());
  }

  onLangChange(lang: SupportedLanguage): void {
    this.currentLang = lang;
    this.userService.setLang(lang);

    const reloadCurrentPage = () => window.location.reload();

    if (!this.userService.currentUser()) {
      reloadCurrentPage();
      return;
    }

    this.userService.updateMeLanguage(lang).subscribe({
      next: reloadCurrentPage,
      error: reloadCurrentPage,
    });
  }

  toggleDomainMenu(event: Event): void {
    this.domainMenu?.toggle(event);
  }

  goHome(): void {
    void this.router.navigate(ROUTES.home());
  }

  goAlerts(): void {
    void this.router.navigate(ROUTES.quiz.alerts());
  }

  get unreadAlertCount(): number {
    return this.quizAlertService.unreadCount();
  }

  private buildDomainSection(label: string, domains: DomainReadDto[]): MenuItem[] {
    const items: MenuItem[] = [
      {
        label,
        disabled: true,
        styleClass: 'domain-menu__section',
      },
    ];

    if (!domains.length) {
      items.push({
        label: this.ui.topmenu.noDomains,
        disabled: true,
        styleClass: 'domain-menu__empty',
      });
      return items;
    }

    return items.concat(domains.map((domain) => ({
      label: this.getDomainLabel(domain),
      icon: this.currentUser?.current_domain === domain.id ? 'pi pi-check' : undefined,
      command: () => this.changeCurrentDomain(domain.id),
    })));
  }

  private changeCurrentDomain(domainId: number): void {
    this.userService.setCurrentDomain(domainId).subscribe({
      next: () => window.location.reload(),
    });
  }

  private getDomainLabel(domain: DomainReadDto): string {
    const translations = domain.translations as DomainTranslations | undefined;
    const lang = this.userService.currentLang;
    const current = translations?.[lang]?.name?.trim();
    if (current) {
      return current;
    }

    for (const fallback of [LanguageEnumDto.Fr, LanguageEnumDto.En, LanguageEnumDto.Nl, LanguageEnumDto.It, LanguageEnumDto.Es]) {
      const value = translations?.[fallback]?.name?.trim();
      if (value) {
        return value;
      }
    }

    return `Domain #${domain.id}`;
  }

  private refreshUserContext(): void {
    const me = this.userService.currentUser();
    if (me) {
      this.refreshUnreadCount();
      this.refreshVisibleDomains();
      return;
    }

    this.userService.getMe().subscribe({
      next: () => {
        this.refreshUnreadCount();
        this.refreshVisibleDomains();
      },
      error: () => {
        this.quizAlertService.clearUnreadCount();
        this.visibleDomains.set([]);
      },
    });
  }

  private refreshVisibleDomains(): void {
    if (!this.userService.currentUser()) {
      this.visibleDomains.set([]);
      return;
    }

    this.domainService.list().subscribe({
      next: (domains) => this.visibleDomains.set(domains),
      error: () => this.visibleDomains.set([]),
    });
  }

  private refreshUnreadCount(): void {
    if (!this.userService.currentUser()) {
      this.quizAlertService.clearUnreadCount();
      return;
    }

    this.quizAlertService.refreshUnreadCount().subscribe({
      error: () => this.quizAlertService.clearUnreadCount(),
    });
  }
}
