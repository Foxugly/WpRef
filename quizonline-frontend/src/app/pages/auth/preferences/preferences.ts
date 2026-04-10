import {CommonModule} from '@angular/common';
import {Component, DestroyRef, inject, OnInit, signal} from '@angular/core';
import {takeUntilDestroyed} from '@angular/core/rxjs-interop';
import {FormBuilder, FormsModule, ReactiveFormsModule, Validators} from '@angular/forms';
import {Router} from '@angular/router';
import {finalize, forkJoin, of} from 'rxjs';
import {switchMap} from 'rxjs/operators';
import {ButtonModule} from 'primeng/button';
import {CardModule} from 'primeng/card';
import {DialogModule} from 'primeng/dialog';
import {InputTextModule} from 'primeng/inputtext';
import {SelectModule} from 'primeng/select';
import {CustomUserReadDto, DomainReadDto, LanguageEnumDto} from '../../../api/generated';
import {DomainService, DomainTranslations} from '../../../services/domain/domain';
import {UserService} from '../../../services/user/user';
import {getUiText} from '../../../shared/i18n/ui-text';

@Component({
  selector: 'app-preferences',
  standalone: true,
  imports: [
    CommonModule,
    FormsModule,
    ReactiveFormsModule,
    ButtonModule,
    CardModule,
    DialogModule,
    InputTextModule,
    SelectModule,
  ],
  templateUrl: './preferences.html',
  styleUrls: ['./preferences.scss'],
})
export class Preferences implements OnInit {
  private readonly fb = inject(FormBuilder);
  private readonly userService = inject(UserService);
  private readonly domainService = inject(DomainService);
  private readonly destroyRef = inject(DestroyRef);
  private readonly router = inject(Router);

  readonly loading = signal(true);
  readonly saving = signal(false);
  readonly error = signal<string | null>(null);
  readonly success = signal<string | null>(null);
  readonly availableDomains = signal<DomainReadDto[]>([]);
  readonly visibleDomains = signal<DomainReadDto[]>([]);
  readonly currentUser = signal<CustomUserReadDto | null>(null);
  readonly linkDialogVisible = signal(false);
  readonly selectedDomainIdsToLink = signal<number[]>([]);

  readonly form = this.fb.nonNullable.group({
    username: [{value: '', disabled: true}],
    email: ['', [Validators.email]],
    first_name: [''],
    last_name: [''],
    language: [LanguageEnumDto.En, [Validators.required]],
  });

  get ui() {
    return getUiText(this.userService.currentLang);
  }

  get languageOptions() {
    return [
      {label: 'Français', value: LanguageEnumDto.Fr},
      {label: 'Nederlands', value: LanguageEnumDto.Nl},
      {label: 'English', value: LanguageEnumDto.En},
      {label: 'Italiano', value: LanguageEnumDto.It},
      {label: 'Español', value: LanguageEnumDto.Es},
    ];
  }

  get roleLabel(): string {
    const me = this.currentUser();
    if (!me) {
      return '-';
    }
    if (me.is_superuser) {
      return this.ui.preferences.roleSuperuser;
    }
    if (me.is_staff) {
      return this.ui.preferences.roleStaff;
    }
    return this.ui.preferences.roleUser;
  }

  get visibleDomainEntries() {
    const me = this.currentUser();
    if (!me) {
      return [];
    }

    return this.visibleDomains().map((domain) => {
      const isOwner = domain.owner?.id === me.id;
      const isDomainManager = !isOwner && (domain.managers ?? []).some((user) => user.id === me.id);
      const isLinkedOnly = !isOwner && !isDomainManager;
      return {
        id: domain.id,
        name: this.getDomainLabel(domain),
        role: isOwner
          ? this.ui.preferences.roleOwner
          : (isDomainManager ? this.ui.preferences.roleStaff : this.ui.preferences.roleMember),
        ownerName: domain.owner?.username || '-',
        isCurrent: me.current_domain === domain.id,
        canSetCurrent: me.current_domain !== domain.id,
        canUnlink: isLinkedOnly,
        canDelete: isOwner,
      };
    });
  }

  get linkableDomainEntries() {
    const linkedIds = new Set(this.visibleDomains().map((domain) => domain.id));
    return this.availableDomains()
      .filter((domain) => !linkedIds.has(domain.id))
      .map((domain) => ({
        id: domain.id,
        name: this.getDomainLabel(domain),
      }));
  }

  ngOnInit(): void {
    this.loading.set(true);
    forkJoin({
      me: this.userService.currentUser()
        ? of(this.userService.currentUser() as CustomUserReadDto)
        : this.userService.getMe(),
      availableDomains: this.domainService.availableForLinking(),
      visibleDomains: this.domainService.list(),
    })
      .pipe(
        takeUntilDestroyed(this.destroyRef),
        finalize(() => this.loading.set(false)),
      )
      .subscribe({
        next: ({me, availableDomains, visibleDomains}) => {
          const currentUser = Array.isArray(me) ? me[0] : me;
          this.currentUser.set(currentUser);
          this.availableDomains.set(availableDomains ?? []);
          this.visibleDomains.set(visibleDomains ?? []);
          this.form.patchValue({
            username: currentUser.username ?? '',
            email: currentUser.email ?? '',
            first_name: currentUser.first_name ?? '',
            last_name: currentUser.last_name ?? '',
            language: currentUser.language ?? LanguageEnumDto.En,
          });
        },
        error: () => {
          this.error.set(this.ui.preferences.loadError);
        },
      });
  }

  save(): void {
    this.error.set(null);
    this.success.set(null);

    if (this.form.invalid) {
      this.form.markAllAsTouched();
      return;
    }

    const me = this.currentUser();
    if (!me) {
      this.error.set(this.ui.preferences.userMissing);
      return;
    }

    const raw = this.form.getRawValue();
    this.saving.set(true);

    this.userService.updateMeProfile({
        email: raw.email || '',
        first_name: raw.first_name || '',
        last_name: raw.last_name || '',
        language: raw.language,
      })
      .pipe(switchMap((updatedUser) => forkJoin({
        profile: of(updatedUser),
        visibleDomains: this.domainService.list(),
      })))
      .pipe(
        takeUntilDestroyed(this.destroyRef),
        finalize(() => this.saving.set(false)),
      )
      .subscribe({
        next: ({profile, visibleDomains}) => {
          const updatedUser = Array.isArray(profile) ? profile[0] : profile;
          this.currentUser.set(updatedUser);
          this.visibleDomains.set(visibleDomains ?? []);
          this.form.patchValue({
            username: updatedUser.username ?? '',
            email: updatedUser.email ?? '',
            first_name: updatedUser.first_name ?? '',
            last_name: updatedUser.last_name ?? '',
            language: updatedUser.language ?? LanguageEnumDto.En,
          });
          this.success.set(this.ui.preferences.saveSuccess);
        },
        error: () => {
          this.error.set(this.ui.preferences.saveError);
        },
      });
  }

  goChangePassword(): void {
    void this.router.navigate(['/change-password']);
  }

  openLinkDomainsDialog(): void {
    this.selectedDomainIdsToLink.set([]);
    this.linkDialogVisible.set(true);
  }

  closeLinkDomainsDialog(): void {
    this.linkDialogVisible.set(false);
    this.selectedDomainIdsToLink.set([]);
  }

  toggleDomainToLink(domainId: number): void {
    const current = this.selectedDomainIdsToLink();
    this.selectedDomainIdsToLink.set(
      current.includes(domainId)
        ? current.filter((id) => id !== domainId)
        : [...current, domainId],
    );
  }

  linkSelectedDomains(): void {
    const me = this.currentUser();
    const selected = this.selectedDomainIdsToLink();
    if (!me || selected.length === 0) {
      this.closeLinkDomainsDialog();
      return;
    }
    const managed_domain_ids = Array.from(new Set([...(me.managed_domain_ids ?? []), ...selected]));
    this.persistLinkedDomains(managed_domain_ids, true);
  }

  setCurrentDomain(domainId: number): void {
    this.error.set(null);
    this.success.set(null);
    this.saving.set(true);
    this.userService.setCurrentDomain(domainId)
      .pipe(
        switchMap((profile) => forkJoin({
          profile: of(profile),
          visibleDomains: this.domainService.list(),
        })),
        takeUntilDestroyed(this.destroyRef),
        finalize(() => this.saving.set(false)),
      )
      .subscribe({
        next: ({profile, visibleDomains}) => {
          this.currentUser.set(profile);
          this.visibleDomains.set(visibleDomains ?? []);
          this.success.set(this.ui.preferences.saveSuccess);
        },
        error: () => {
          this.error.set(this.ui.preferences.saveError);
        },
      });
  }

  unlinkDomain(domainId: number): void {
    const me = this.currentUser();
    if (!me) {
      return;
    }
    const managed_domain_ids = (me.managed_domain_ids ?? []).filter((id) => id !== domainId);
    this.persistLinkedDomains(managed_domain_ids, false);
  }

  deleteOwnedDomain(domainId: number): void {
    this.error.set(null);
    this.success.set(null);
    this.saving.set(true);
    this.domainService.delete(domainId)
      .pipe(
        switchMap(() => forkJoin({
          profile: this.userService.getMe(),
          visibleDomains: this.domainService.list(),
          availableDomains: this.domainService.availableForLinking(),
        })),
        takeUntilDestroyed(this.destroyRef),
        finalize(() => this.saving.set(false)),
      )
      .subscribe({
        next: ({profile, visibleDomains, availableDomains}) => {
          this.currentUser.set(profile);
          this.visibleDomains.set(visibleDomains ?? []);
          this.availableDomains.set(availableDomains ?? []);
          this.success.set(this.ui.preferences.deleteDomainSuccess);
        },
        error: () => {
          this.error.set(this.ui.preferences.deleteDomainError);
        },
      });
  }

  private persistLinkedDomains(managed_domain_ids: number[], closeDialog: boolean): void {
    this.error.set(null);
    this.success.set(null);
    this.saving.set(true);
    this.userService.updateMeProfile({managed_domain_ids})
      .pipe(
        switchMap((profile) => forkJoin({
          profile: of(profile),
          visibleDomains: this.domainService.list(),
          availableDomains: this.domainService.availableForLinking(),
        })),
        takeUntilDestroyed(this.destroyRef),
        finalize(() => this.saving.set(false)),
      )
      .subscribe({
        next: ({profile, visibleDomains, availableDomains}) => {
          this.currentUser.set(profile);
          this.visibleDomains.set(visibleDomains ?? []);
          this.availableDomains.set(availableDomains ?? []);
          if (closeDialog) {
            this.closeLinkDomainsDialog();
          }
          this.success.set(this.ui.preferences.saveSuccess);
        },
        error: () => {
          this.error.set(this.ui.preferences.saveError);
        },
      });
  }

  private getDomainLabel(domain: DomainReadDto): string {
    const translations = domain.translations as DomainTranslations | undefined;
    const lang = this.userService.currentLang;
    const current = translations?.[lang]?.name?.trim();
    if (current) {
      return current;
    }

    for (const fallback of [LanguageEnumDto.Fr, LanguageEnumDto.En, LanguageEnumDto.Nl]) {
      const value = translations?.[fallback]?.name?.trim();
      if (value) {
        return value;
      }
    }

    return `Domain #${domain.id}`;
  }
}
