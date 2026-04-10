import {Component, computed, DestroyRef, inject, OnInit, signal} from '@angular/core';
import {ActivatedRoute} from '@angular/router';
import {FormBuilder, FormControl, FormGroup, ReactiveFormsModule, Validators} from '@angular/forms';
import {takeUntilDestroyed} from '@angular/core/rxjs-interop';

import {forkJoin, of} from 'rxjs';
import {catchError, finalize} from 'rxjs/operators';

import {ButtonModule} from 'primeng/button';

import {DomainService, DomainTranslations} from '../../../services/domain/domain';
import {UserService} from '../../../services/user/user';
import {LanguageService} from '../../../services/language/language';
import {isLangCode, LangCode, TranslationService} from '../../../services/translation/translation';
import {
  buildLocalizedTextRecord,
  getLocalizedTextGroup,
  patchLocalizedTextRecord,
  syncLocalizedTextControls,
} from '../../../shared/forms/localized-text-form';
import {logApiError, userFacingApiMessage} from '../../../shared/api/api-errors';
import {isEmptyRichText} from '../../../shared/html/is-empty-rich-text';
import {DomainEditorFormComponent} from '../../../components/domain-editor-form/domain-editor-form';
import {getEditorUiText} from '../../../shared/i18n/editor-ui-text';

import {
  CustomUserReadDto,
  DomainDetailDto,
  DomainWriteRequestDto,
  LanguageEnumDto,
  LanguageReadDto,
  UserSummaryDto,
} from '../../../api/generated';

type UserOption = { label: string; value: number };
type DomainUserRef = UserSummaryDto;
type DomainWritePayload = DomainWriteRequestDto & {
  owner?: number;
  translations: DomainTranslations;
};


function asNumber(x: unknown): number | null {
  return typeof x === 'number' && Number.isFinite(x) ? x : null;
}

function getUserId(userRef: DomainUserRef | null | undefined): number | null {
  return asNumber(userRef?.id);
}

@Component({
  standalone: true,
  selector: 'app-domain-edit',
  imports: [
    ReactiveFormsModule,
    ButtonModule,
    DomainEditorFormComponent,
  ],
  templateUrl: './domain-edit.html',
  styleUrl: './domain-edit.scss',
})
export class DomainEdit implements OnInit {
  readonly ui = computed(() => getEditorUiText(this.userService.currentLang));
  id!: number;

  loading = signal(true);
  submitError = signal<string | null>(null);
  translating = signal(false);

  domain = signal<DomainDetailDto | null>(null);

  // global languages (for selectButton options + code->id mapping)
  languages = signal<LanguageReadDto[]>([]);

  // users for owner/staff
  ownerOptions = signal<UserOption[]>([]);
  managersOptions = signal<UserOption[]>([]);
  availableStaff = signal<UserOption[]>([]);
  selectedStaff = signal<UserOption[]>([]);
  canEditOwner = signal(false);

  // tabs (code-based)
  tabCodes = signal<LangCode[]>([]);
  activeTab = signal<LangCode | undefined>(undefined);
  // options for selectButton
  langCodeOptions = computed<Array<{ label: string; value: LangCode }>>(() => {
    return (this.languages() ?? [])
      .filter(l => l.active)
      .map(l => {
        const code = String(l.code) as LangCode;
        return {
          label: l.name || code.toUpperCase(),
          value: code,
        };
      })
      .filter(o => isLangCode(o.value));
  });
  // code -> id (for allowed_languages payload)
  langIdByCode = computed<Record<string, number>>(() => {
    const map: Record<string, number> = {};
    for (const l of this.languages()) {
      if (typeof l.code === 'string' && typeof l.id === 'number') {
        map[l.code] = l.id;
      }
    }
    return map;
  });
  private prevCodes = new Set<LangCode>();
  private fb = inject(FormBuilder);
  form = this.fb.group({
    active: new FormControl<boolean>(true, {nonNullable: true}),
    owner: new FormControl<number | null>(null),
    managers: new FormControl<number[]>([], {nonNullable: true}),

    allowed_language_codes: new FormControl<LangCode[]>([], {
      nonNullable: true,
      validators: [Validators.required],
    }),

    translations: this.fb.group({}) as FormGroup,
  });
  private route = inject(ActivatedRoute);
  private destroyRef = inject(DestroyRef);

  private domainService = inject(DomainService);
  private userService = inject(UserService);
  currentLang = computed(() => this.userService.currentLang);
  private languageService = inject(LanguageService);
  private translator = inject(TranslationService);

  ngOnInit(): void {
    const rawId = this.route.snapshot.paramMap.get('id');
    const id = Number(rawId);
    if (!Number.isFinite(id)) {
      this.submitError.set("ID invalide.");
      this.loading.set(false);
      return;
    }
    this.id = id;
    this.loading.set(true);
    this.submitError.set(null);

    // 1) Load all: domain + users + languages (each with its own catchError)
    forkJoin({
      domain: this.domainService.detail(this.id).pipe(
        catchError((err) => {
          logApiError('domain.edit.load-domain', err);
          return of(null as DomainDetailDto | null);
        }),
      ),
      users: this.userService.list().pipe(
        catchError((err) => {
          logApiError('domain.edit.load-users', err);
          return of([] as CustomUserReadDto[]);
        }),
      ),
      languages: this.languageService.list().pipe(
        catchError((err) => {
          logApiError('domain.edit.load-languages', err);
          return of([] as LanguageReadDto[]);
        }),
      ),
    })
      .pipe(
        takeUntilDestroyed(this.destroyRef),
        finalize(() => this.loading.set(false)),
      )
      .subscribe(({domain, users, languages}) => {
        if (!domain) {
          this.submitError.set("Impossible de charger le domaine.");
          return;
        }

        this.domain.set(domain);
        const me = this.userService.currentUser();
        this.canEditOwner.set(
          !!me && (me.is_superuser || domain.owner?.id === me.id),
        );

        // 2) Set global active languages
        const activeLangs = (languages ?? []).filter(l => l.active);
        this.languages.set(activeLangs);

        // 3) Build user options
        const opts: UserOption[] = (users ?? [])
          .filter(u => typeof u.id === 'number')
          .map(u => ({label: u.username, value: u.id}));

        this.ownerOptions.set(opts);
        this.managersOptions.set(opts);

        this.patchMetaFromDto(domain);
        this.recomputePickList();
        const activeSet = new Set(activeLangs.map(l => String(l.code)));
        const initialCodes = Array.from(new Set(
          (domain.allowed_languages ?? [])
            .map(l => l.code)
            .filter(isLangCode)
            .filter(c => activeSet.has(c))
        ));
        if (!initialCodes.length) {
          this.activeTab.set(undefined);
          return;
        }
        this.form.controls.allowed_language_codes.setValue(initialCodes, {emitEvent: false});
        this.tabCodes.set(initialCodes);
        this.syncTranslationControls(initialCodes.map(String));
        this.prevCodes = new Set(initialCodes);
        const pref = this.currentLang();
        const prefCode = typeof pref === 'string' && isLangCode(pref) ? pref : undefined;
        this.activeTab.set(
          (prefCode && initialCodes.includes(prefCode) ? prefCode : initialCodes[0]) ?? undefined
        );
      });

    // 2) User-driven changes only (tabs + controls + activeTab rules)
    this.form.controls.allowed_language_codes.valueChanges
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe((codes) => {
        const next = (codes ?? []).filter(isLangCode);
        // update UI + controls
        this.tabCodes.set(next);
        this.syncTranslationControls(next.map(String));

        // active tab rules
        const current = this.activeTab();
        const added = next.find(c => !this.prevCodes.has(c));
        const removedActive = !!current && !next.includes(current);

        if (!current && added) {
          this.activeTab.set(added);
        } else if (removedActive) {
          this.activeTab.set(next.length ? next[0] : undefined);
        } else if (!next.length) {
          this.activeTab.set(undefined);
        }

        this.prevCodes = new Set(next);
      });

    // Staff -> sync picklist if form.staff changes
    this.form.controls.managers.valueChanges
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe(() => this.recomputePickList());
  }

  onTabValueChange(v: string | number | undefined): void {
    this.activeTab.set(v as LangCode | undefined);
  }

  langGroup(code: string): FormGroup {
    return getLocalizedTextGroup(this.translationsGroup(), code);
  }

  onStaffPickListChange(): void {
    const meId = this.userService.currentUser()?.id;

    const ids = this.selectedStaff().map(o => o.value);
    const fixedIds =
      typeof meId === 'number' && !ids.includes(meId) ? [...ids, meId] : ids;

    const current = this.form.controls.managers.value ?? [];
    const currentSet = new Set(current);
    const fixedSet = new Set(fixedIds);

    const same =
      currentSet.size === fixedSet.size &&
      [...currentSet].every(v => fixedSet.has(v));

    if (!same) {
      this.form.controls.managers.setValue(fixedIds);
      this.form.controls.managers.markAsDirty();
    }
  }

  save(): void {
    this.submitError.set(null);

    if (this.form.invalid) {
      this.form.markAllAsTouched();
      this.submitError.set("Le formulaire contient des erreurs.");
      return;
    }

    const payload = this.buildPayload();

    if (!payload.allowed_languages?.length) {
      this.submitError.set("Sélectionne au moins une langue valide.");
      return;
    }

    this.domainService.update(this.id, payload)
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe({
        next: () => this.goList(),
        error: (err) => {
          logApiError('domain.edit.submit', err);
          this.submitError.set(userFacingApiMessage(err, "Erreur lors de l'enregistrement."));
        },
      });
  }

  goList(): void {
    this.domainService.goList();
  }

  async translateFrom(sourceLang: string): Promise<void> {
    const codes = Object.keys(this.translationsGroup().controls);
    if (!codes.includes(sourceLang)) return;

    this.translating.set(true);
    this.submitError.set(null);

    try {
      const source = this.langGroup(sourceLang);
      const sourceName = (source.get('name') as FormControl<string>).value ?? '';
      const sourceDesc = (source.get('description') as FormControl<string>).value ?? '';

      for (const targetLang of codes) {
        if (targetLang === sourceLang) continue;

        const target = this.langGroup(targetLang);
        const nameCtrl = target.get('name') as FormControl<string>;
        const descCtrl = target.get('description') as FormControl<string>;

        const needName = !(nameCtrl.value ?? '').trim();
        const needDesc = isEmptyRichText(descCtrl.value ?? '');

        const items: Array<{ key: string; text: string; format: 'text' | 'html' }> = [];
        if (needName) items.push({key: 'name', text: sourceName, format: 'text'});
        if (needDesc) items.push({key: 'description', text: sourceDesc, format: 'html'});

        if (!items.length) continue;

        const out = await this.translator.translateBatch(sourceLang, targetLang, items);

        if (needName && out['name'] !== undefined) nameCtrl.setValue(out['name']);
        if (needDesc && out['description'] !== undefined) descCtrl.setValue(out['description']);
      }
    } catch (e) {
      logApiError('domain.edit.translate', e);
      this.submitError.set(userFacingApiMessage(e, 'Erreur lors de la traduction.'));
    } finally {
      this.translating.set(false);
    }
  }

  // --- helpers ---
  private translationsGroup(): FormGroup {
    return this.form.get('translations') as FormGroup;
  }

  private patchMetaFromDto(dto: DomainDetailDto): void {
    const ownerId = getUserId(dto.owner);

    const managerIds = (dto.managers ?? [])
      .map((userRef) => getUserId(userRef))
      .filter((id): id is number => id !== null);

    this.form.patchValue({
      active: dto.active ?? true,
      owner: ownerId,
      managers: managerIds,
    });
  }

  private syncTranslationControls(codes: string[]): void {
    const tg = this.translationsGroup();
    syncLocalizedTextControls(this.fb, tg, codes);

    // patch values from DTO for all wanted codes (stable, no emit)
    const dto = this.domain();
    if (dto) {
      const tr = (dto.translations ?? {}) as DomainTranslations;
      patchLocalizedTextRecord(tg, codes, tr);
    }
  }

  private buildPayload(): DomainWritePayload {
    const codes = this.form.controls.allowed_language_codes.value ?? [];
    const idMap = this.langIdByCode();
    const owner = this.form.controls.owner.value;

    const allowed_languages = codes
      .map(c => idMap[String(c)])
      .filter((id): id is number => typeof id === 'number');

    const translations = buildLocalizedTextRecord(this.translationsGroup()) as DomainTranslations;

    return {
      active: this.form.controls.active.value,
      managers: this.form.controls.managers.value,
      allowed_languages,
      translations,
      ...(typeof owner === 'number' ? { owner } : {}),
    };
  }

  private ensureMeInStaff(emitEvent: boolean): number | null {
    const meId = this.userService.currentUser()?.id;
    if (typeof meId !== 'number') return null;

    const current = this.form.controls.managers.value ?? [];
    if (!current.includes(meId)) {
      this.form.controls.managers.setValue([...current, meId], {emitEvent});
    }
    return meId;
  }

  private recomputePickList(): void {
    this.ensureMeInStaff(false);

    const all = this.managersOptions();
    const selectedIds = new Set(this.form.controls.managers.value ?? []);

    this.selectedStaff.set(all.filter(o => selectedIds.has(o.value)));
    this.availableStaff.set(all.filter(o => !selectedIds.has(o.value)));
  }
}
