import {Component, computed, DestroyRef, inject, OnInit, signal} from '@angular/core';
import {CommonModule} from '@angular/common';
import {FormBuilder, FormControl, FormGroup, ReactiveFormsModule, Validators} from '@angular/forms';
import {takeUntilDestroyed} from '@angular/core/rxjs-interop';

import {forkJoin, of} from 'rxjs';
import {catchError, finalize} from 'rxjs/operators';

import {ButtonModule} from 'primeng/button';
import {CardModule} from 'primeng/card';

import {
  CustomUserReadDto,
  DomainWriteRequestDto,
  LanguageEnumDto,
  LanguageReadDto,
} from '../../../api/generated';

import {DomainService, DomainTranslations} from '../../../services/domain/domain';
import {UserService} from '../../../services/user/user';
import {isLangCode, LangCode, TranslationService} from '../../../services/translation/translation';
import {LanguageService} from '../../../services/language/language';
import {
  buildLocalizedTextRecord,
  getLocalizedTextGroup,
  syncLocalizedTextControls,
} from '../../../shared/forms/localized-text-form';
import {logApiError, userFacingApiMessage} from '../../../shared/api/api-errors';
import {isEmptyRichText} from '../../../shared/html/is-empty-rich-text';
import {DomainEditorFormComponent} from '../../../components/domain-editor-form/domain-editor-form';
import {getEditorUiText} from '../../../shared/i18n/editor-ui-text';

type UserOption = { label: string; value: number };
type DomainWritePayload = DomainWriteRequestDto & {
  owner: number | null;
  translations: DomainTranslations;
};

@Component({
  selector: 'app-domain-create',
  standalone: true,
  imports: [
    CommonModule,
    ReactiveFormsModule,
    ButtonModule,
    CardModule,
    DomainEditorFormComponent,
  ],
  templateUrl: './domain-create.html',
  styleUrl: './domain-create.scss',
})
export class DomainCreate implements OnInit {
  readonly ui = computed(() => getEditorUiText(this.userService.currentLang));
  loading = signal(true);
  submitError = signal<string | null>(null);
  translating = signal(false);

  languages = signal<LanguageReadDto[]>([]);
  staffOptions = signal<UserOption[]>([]);

  availableStaff = signal<UserOption[]>([]);
  selectedStaff = signal<UserOption[]>([]);

  tabCodes = signal<LangCode[]>([]);
  activeTab = signal<LangCode | undefined>(undefined);

  ownerOptions = signal<UserOption[]>([]);
  langCodeOptions = computed<Array<{ label: string; value: LangCode }>>(() => {
    return (this.languages() ?? [])
      .filter(l => l.active)
      .filter((l): l is (typeof l & { code: LangCode }) => isLangCode(l.code))
      .map(l => ({
        label: l.name || l.code.toUpperCase(),
        value: l.code,
      }));
  });
  langIdByCode = computed<Record<string, number>>(() => {
    const map: Record<string, number> = {};
    for (const l of this.languages()) {
      if (typeof l.code === 'string' && typeof l.id === 'number') map[l.code] = l.id;
    }
    return map;
  });
  private prevCodes = new Set<LangCode>();
  private fb = inject(FormBuilder);
  form = this.fb.group({
    active: new FormControl<boolean>(true, {nonNullable: true}),
    owner: new FormControl<number | null>(null),
    staff: new FormControl<number[]>([], {nonNullable: true}),

    allowed_language_codes: new FormControl<LangCode[]>([], {
      nonNullable: true,
      validators: [Validators.required],
    }),

    translations: this.fb.group({}) as FormGroup,
  });
  private destroyRef = inject(DestroyRef);
  private languageService = inject(LanguageService);
  private userService = inject(UserService);
  private domainService = inject(DomainService);
  private translator = inject(TranslationService);

  ngOnInit(): void {
    this.loading.set(true);
    forkJoin({
      languages: this.languageService.list().pipe(catchError(() => of([] as LanguageReadDto[]))),
      users: this.userService.list().pipe(catchError(() => of([] as CustomUserReadDto[]))),
    })
      .pipe(
        takeUntilDestroyed(this.destroyRef),
        finalize(() => this.loading.set(false)),
      )
      .subscribe({
        next: ({languages, users}) => {
          // 1) Languages
          const activeLangs = (languages ?? []).filter(l => l.active);
          this.languages.set(activeLangs);

          // 2) Users options
          const opts: UserOption[] = (users ?? [])
            .filter(u => typeof u.id === 'number')
            .map(u => ({label: u.username, value: u.id}));

          this.staffOptions.set(opts);
          this.ownerOptions.set(opts);

          //  3) Owner
          this.setOwnerFromCurrentUser();

          // 4) Default language = current user lang (UserService.currentLang())
          const userLangStr = this.userService.currentLang;
          const userLang = (typeof userLangStr === 'string' && isLangCode(userLangStr))
            ? userLangStr
            : undefined;


          const fallbackLang = activeLangs
            .map(l => String(l.code))
            .find(isLangCode);

          const initCodes: LangCode[] =
            userLang && activeLangs.some(l => String(l.code) === userLang)
              ? [userLang]
              : (fallbackLang ? [fallbackLang] : []);

          this.form.controls.allowed_language_codes.setValue(initCodes, {emitEvent: false});

          this.tabCodes.set(initCodes);
          this.syncTranslationControls(initCodes.map(String));
          this.prevCodes = new Set(initCodes);
          this.activeTab.set(initCodes.length ? initCodes[0] : undefined);
          // PickList initial
          this.recomputePickList();
        },
        error: (err) => {
          logApiError('domain.create.load-initial', err);
          this.submitError.set(userFacingApiMessage(err, 'Erreur lors du chargement initial.'));
        },
      });

    // Langues -> tabs + controls dynamiques + tab actif
    this.form.controls.allowed_language_codes.valueChanges
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe((codes) => {
        const next = (codes ?? []).filter(isLangCode);
        this.tabCodes.set(next);
        this.syncTranslationControls(next.map(String));
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

    // Staff -> recompute picklist
    this.form.controls.staff.valueChanges
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

    const current = this.form.controls.staff.value ?? [];
    const currentSet = new Set(current);
    const fixedSet = new Set(fixedIds);

    const same =
      currentSet.size === fixedSet.size &&
      [...currentSet].every(v => fixedSet.has(v));

    if (!same) {
      this.form.controls.staff.setValue(fixedIds);
      this.form.controls.staff.markAsDirty();
    }
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
      logApiError('domain.create.translate', e);
      this.submitError.set(userFacingApiMessage(e, 'Erreur lors de la traduction.'));
    } finally {
      this.translating.set(false);
    }
  }

  submit(): void {
    this.submitError.set(null);

    if (this.form.invalid) {
      this.form.markAllAsTouched();
      this.submitError.set('Le formulaire contient des erreurs.');
      return;
    }

    const dto = this.buildDto();
    if (!dto.allowed_languages || !dto.allowed_languages.length) {
      this.submitError.set("Impossible de déterminer les IDs des langues (liste des langues non chargée ?).");
      return;
    }

    this.domainService.create(dto)
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe({
        next: () => this.domainService.goList(),
        error: (err) => {
          logApiError('domain.create.submit', err);
          this.submitError.set(userFacingApiMessage(err, 'Erreur backend lors de la création.'));
        },
      });
  }

  goList(): void {
    this.domainService.goList();
  }

  private translationsGroup(): FormGroup {
    return this.form.get('translations') as FormGroup;
  }

  private buildDto(): DomainWritePayload {
    const codes = this.form.controls.allowed_language_codes.value ?? [];
    const idMap = this.langIdByCode();

    const allowed_languages = codes
      .map(c => idMap[String(c)])
      .filter((id): id is number => typeof id === 'number');

    const translations = buildLocalizedTextRecord(this.translationsGroup()) as DomainTranslations;
    return {
      active: this.form.controls.active.value ?? true,
      owner: this.form.controls.owner.value ?? null,
      staff: this.form.controls.staff.value ?? [],
      allowed_languages,
      translations,
    };
  }

  private syncTranslationControls(codes: string[]): void {
    syncLocalizedTextControls(this.fb, this.translationsGroup(), codes);
  }

  private recomputePickList(): void {
    // sécurité : ensure current user in staff
    const meId = this.userService.currentUser()?.id;
    if (typeof meId === 'number') {
      const current = this.form.controls.staff.value ?? [];
      if (!current.includes(meId)) {
        this.form.controls.staff.setValue([...current, meId], {emitEvent: false});
      }
    }

    const all = this.staffOptions();
    const selectedIds = new Set(this.form.controls.staff.value ?? []);

    this.selectedStaff.set(all.filter(o => selectedIds.has(o.value)));
    this.availableStaff.set(all.filter(o => !selectedIds.has(o.value)));
  }


  private setOwnerFromCurrentUser(): void {
    const me = this.userService.currentUser();
    const id = me?.id;
    if (typeof id === 'number') {
      this.form.controls.owner.setValue(id);
      this.form.controls.owner.disable({emitEvent: false}); // readonly
      const current = this.form.controls.staff.value ?? [];
      if (!current.includes(id)) {
        this.form.controls.staff.setValue([...current, id], {emitEvent: false});
      }
    }

  }
}
