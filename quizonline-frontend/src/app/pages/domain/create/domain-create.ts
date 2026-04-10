import {Component, computed, DestroyRef, effect, inject, OnInit, signal} from '@angular/core';
import {CommonModule} from '@angular/common';
import {FormBuilder, FormControl, FormGroup, ReactiveFormsModule, Validators} from '@angular/forms';
import {takeUntilDestroyed} from '@angular/core/rxjs-interop';

import {forkJoin, of} from 'rxjs';
import {catchError, finalize} from 'rxjs/operators';

import {ButtonModule} from 'primeng/button';
import {CardModule} from 'primeng/card';
import {MessageService} from 'primeng/api';

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
  owner?: number;
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
  managersOptions = signal<UserOption[]>([]);

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
    managers: new FormControl<number[]>([], {nonNullable: true}),

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
  private messageService = inject(MessageService);
  private lastToastMessage: string | null = null;

  constructor() {
    effect(() => {
      const detail = this.submitError();
      if (!detail || detail === this.lastToastMessage) {
        return;
      }

      this.lastToastMessage = detail;
      this.messageService.add({
        severity: 'error',
        summary: this.localizedSummary(),
        detail: this.localizeDetail(detail),
      });
    });
  }

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

          this.managersOptions.set(opts);
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
          const detail = userFacingApiMessage(err, this.toastText().loadFailed);
          this.submitError.set(detail);
          this.showErrorToast(detail);
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
      const detail = userFacingApiMessage(e, this.toastText().translateFailed);
      this.submitError.set(detail);
      this.showErrorToast(detail);
    } finally {
      this.translating.set(false);
    }
  }

  submit(): void {
    this.submitError.set(null);

    if (this.form.invalid) {
      this.form.markAllAsTouched();
      this.showErrorToast(this.toastText().invalidForm);
      this.submitError.set('Le formulaire contient des erreurs.');
      return;
    }

    const dto = this.buildDto();
    if (!dto.allowed_languages || !dto.allowed_languages.length) {
      this.showErrorToast(this.toastText().missingLanguages);
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
    const owner = this.form.controls.owner.value;

    const allowed_languages = codes
      .map(c => idMap[String(c)])
      .filter((id): id is number => typeof id === 'number');

    const translations = buildLocalizedTextRecord(this.translationsGroup()) as DomainTranslations;
    return {
      active: this.form.controls.active.value ?? true,
      managers: this.form.controls.managers.value ?? [],
      allowed_languages,
      translations,
      ...(typeof owner === 'number' ? { owner } : {}),
    };
  }

  private syncTranslationControls(codes: string[]): void {
    syncLocalizedTextControls(this.fb, this.translationsGroup(), codes);
  }

  private recomputePickList(): void {
    // sécurité : ensure current user in staff
    const meId = this.userService.currentUser()?.id;
    if (typeof meId === 'number') {
      const current = this.form.controls.managers.value ?? [];
      if (!current.includes(meId)) {
        this.form.controls.managers.setValue([...current, meId], {emitEvent: false});
      }
    }

    const all = this.managersOptions();
    const selectedIds = new Set(this.form.controls.managers.value ?? []);

    this.selectedStaff.set(all.filter(o => selectedIds.has(o.value)));
    this.availableStaff.set(all.filter(o => !selectedIds.has(o.value)));
  }


  private setOwnerFromCurrentUser(): void {
    const me = this.userService.currentUser();
    const id = me?.id;
    if (typeof id === 'number') {
      this.form.controls.owner.setValue(id);
      this.form.controls.owner.disable({emitEvent: false}); // readonly
      const current = this.form.controls.managers.value ?? [];
      if (!current.includes(id)) {
        this.form.controls.managers.setValue([...current, id], {emitEvent: false});
      }
    }

  }

  private localizedSummary(): string {
    switch (this.userService.currentLang) {
      case LanguageEnumDto.Nl:
        return 'Fout';
      case LanguageEnumDto.It:
        return 'Errore';
      case LanguageEnumDto.Es:
      case LanguageEnumDto.En:
        return 'Error';
      case LanguageEnumDto.Fr:
      default:
        return 'Erreur';
    }
  }

  private localizeDetail(detail: string): string {
    switch (detail) {
      case 'Le formulaire contient des erreurs.':
        return this.msg('The form contains errors.', 'Le formulaire contient des erreurs.', 'Het formulier bevat fouten.', 'Il modulo contiene errori.', 'El formulario contiene errores.');
      case "Impossible de dÃ©terminer les IDs des langues (liste des langues non chargÃ©e ?).":
        return this.msg('Unable to determine language IDs.', "Impossible de determiner les IDs des langues.", 'Kan de taal-IDs niet bepalen.', 'Impossibile determinare gli ID delle lingue.', 'No se pueden determinar los IDs de los idiomas.');
      case 'Erreur lors du chargement initial.':
        return this.msg('Failed to load initial data.', 'Erreur lors du chargement initial.', 'Fout bij het laden van de begingegevens.', 'Errore durante il caricamento iniziale.', 'Error al cargar los datos iniciales.');
      case 'Erreur lors de la traduction.':
        return this.msg('Translation failed.', 'Erreur lors de la traduction.', 'Fout tijdens het vertalen.', 'Errore durante la traduzione.', 'Error durante la traduccion.');
      case 'Erreur backend lors de la crÃ©ation.':
        return this.msg('Backend error while creating.', 'Erreur backend lors de la creation.', 'Backendfout bij het aanmaken.', 'Errore backend durante la creazione.', 'Error del backend al crear.');
      default:
        return detail;
    }
  }

  private msg(en: string, fr: string, nl: string, it: string, es: string): string {
    switch (this.userService.currentLang) {
      case LanguageEnumDto.Nl:
        return nl;
      case LanguageEnumDto.It:
        return it;
      case LanguageEnumDto.Es:
        return es;
      case LanguageEnumDto.En:
        return en;
      case LanguageEnumDto.Fr:
      default:
        return fr;
    }
  }

  private showErrorToast(detail: string): void {
    this.messageService.add({
      severity: 'error',
      summary: this.localizedSummary(),
      detail: this.localizeDetail(detail),
    });
  }

  private toastText(): {loadFailed: string; translateFailed: string; invalidForm: string; missingLanguages: string; saveFailed: string} {
    return {
      loadFailed: 'Erreur lors du chargement initial.',
      translateFailed: 'Erreur lors de la traduction.',
      invalidForm: 'Le formulaire contient des erreurs.',
      missingLanguages: "Impossible de dÃ©terminer les IDs des langues (liste des langues non chargÃ©e ?).",
      saveFailed: 'Erreur backend lors de la crÃ©ation.',
    };
  }
}
