import {Component, computed, DestroyRef, inject, OnInit, signal} from '@angular/core';
import {CommonModule} from '@angular/common';
import {FormBuilder, FormControl, FormGroup, ReactiveFormsModule, Validators} from '@angular/forms';
import {takeUntilDestroyed} from '@angular/core/rxjs-interop';

import {forkJoin, of} from 'rxjs';
import {catchError, finalize} from 'rxjs/operators';

import {TabsModule} from 'primeng/tabs';
import {Editor} from 'primeng/editor';
import {InputTextModule} from 'primeng/inputtext';
import {Button, ButtonModule} from 'primeng/button';
import {ToggleSwitchModule} from 'primeng/toggleswitch';
import {SelectModule} from 'primeng/select';
import {PickListModule} from 'primeng/picklist';
import {MessageModule} from 'primeng/message';
import {SelectButtonModule} from 'primeng/selectbutton';
import {CardModule} from 'primeng/card';

import {
  CustomUserReadDto,
  DomainWriteRequestDto,
  LanguageEnumDto,
  LanguageReadDto,
} from '../../../api/generated';

import {DomainService, DomainTranslations} from '../../../services/domain/domain';
import {UserService} from '../../../services/user/user';
import {TranslationService} from '../../../services/translation/translation';
import {LanguageService} from '../../../services/language/language';

type UserOption = { label: string; value: number };
//type DomainTr = { name?: string; description?: string };
//type DomainTranslations = Record<string, DomainTr>;
type LangCode = `${LanguageEnumDto}`;
const LANG_CODES = Object.values(LanguageEnumDto) as LangCode[];

export function isLangCode(value: string): value is LangCode {
  return (LANG_CODES as readonly string[]).includes(value);
}

@Component({
  selector: 'app-domain-create',
  standalone: true,
  imports: [
    CommonModule,
    ReactiveFormsModule,
    TabsModule,
    Editor,
    InputTextModule,
    ButtonModule,
    ToggleSwitchModule,
    SelectModule,
    SelectButtonModule,
    PickListModule,
    MessageModule,
    CardModule,
  ],
  templateUrl: './domain-create.html',
  styleUrl: './domain-create.scss',
})
export class DomainCreate implements OnInit {
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
          console.error(err);
          this.submitError.set('Erreur lors du chargement initial.');
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
    return this.translationsGroup().get(code) as FormGroup;
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
        const needDesc = this.isEmptyHtml(descCtrl.value ?? '');

        const items: Array<{ key: string; text: string; format: 'text' | 'html' }> = [];
        if (needName) items.push({key: 'name', text: sourceName, format: 'text'});
        if (needDesc) items.push({key: 'description', text: sourceDesc, format: 'html'});

        if (!items.length) continue;

        const out = await this.translator.translateBatch(sourceLang, targetLang, items);

        if (needName && out['name'] !== undefined) nameCtrl.setValue(out['name']);
        if (needDesc && out['description'] !== undefined) descCtrl.setValue(out['description']);
      }
    } catch (e) {
      console.error(e);
      this.submitError.set('Erreur lors de la traduction.');
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
          console.error(err);
          this.submitError.set('Erreur backend lors de la création.');
        },
      });
  }

  goList(): void {
    this.domainService.goList();
  }

  private translationsGroup(): FormGroup {
    return this.form.get('translations') as FormGroup;
  }

  private buildDto(): DomainWriteRequestDto {
    const codes = this.form.controls.allowed_language_codes.value ?? [];
    const idMap = this.langIdByCode();

    const allowed_languages = codes
      .map(c => idMap[String(c)])
      .filter((id): id is number => typeof id === 'number');

    const translations: DomainTranslations = {};
    const tg = this.translationsGroup();

    for (const code of Object.keys(tg.controls)) {
      const g = tg.get(code) as FormGroup;
      translations[code] = {
        name: (g.get('name') as FormControl<string>)?.value ?? '',
        description: (g.get('description') as FormControl<string>)?.value ?? '',
      };
    }
    return {
      active: this.form.controls.active.value ?? true,
      owner: this.form.controls.owner.value ?? null,
      staff: this.form.controls.staff.value ?? [],
      allowed_languages,
      translations,
    } as any;
  }

  private syncTranslationControls(codes: string[]): void {
    const tg = this.translationsGroup();

    const wanted = new Set<string>(codes);
    const existing = new Set<string>(Object.keys(tg.controls));

    for (const code of wanted) {
      if (!existing.has(code)) {
        tg.addControl(
          code,
          this.fb.group({
            name: new FormControl<string>('', {
              nonNullable: true,
              validators: [Validators.required, Validators.minLength(2)],
            }),
            description: new FormControl<string>('', {nonNullable: true}),
          }),
        );
      }
    }

    for (const code of existing) {
      if (!wanted.has(code)) tg.removeControl(code);
    }
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

  private isEmptyHtml(html: string): boolean {
    const s = (html ?? '').trim().toLowerCase();
    return !s || s === '<p><br></p>' || s === '<p></p>';
  }
}
