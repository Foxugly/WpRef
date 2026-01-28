import {Component, computed, DestroyRef, inject, OnInit, signal} from '@angular/core';
import {ActivatedRoute} from '@angular/router';
import {FormBuilder, FormControl, FormGroup, ReactiveFormsModule, Validators} from '@angular/forms';
import {takeUntilDestroyed} from '@angular/core/rxjs-interop';

import {forkJoin, of} from 'rxjs';
import {catchError, finalize} from 'rxjs/operators';

import {TabsModule} from 'primeng/tabs';
import {Editor} from 'primeng/editor';
import {InputTextModule} from 'primeng/inputtext';
import {Button} from 'primeng/button';

import {ToggleSwitchModule} from 'primeng/toggleswitch';
import {SelectModule} from 'primeng/select';
import {PickListModule} from 'primeng/picklist';
import {BadgeModule} from 'primeng/badge';
import {SelectButtonModule} from 'primeng/selectbutton';

import {DomainService, DomainTranslations} from '../../../services/domain/domain';
import {UserService} from '../../../services/user/user';
import {LanguageService} from '../../../services/language/language';
import {LangCode, TranslationService} from '../../../services/translation/translation';

import {
  CustomUserReadDto,
  DomainDetailDto,
  DomainWriteRequestDto,
  LanguageEnumDto,
  LanguageReadDto,
} from '../../../api/generated';
import {isLangCode} from '../create/domain-create';

type UserOption = { label: string; value: number };


function asNumber(x: unknown): number | null {
  return typeof x === 'number' && Number.isFinite(x) ? x : null;
}

function getUserId(u: unknown): number | null {
  if (!u || typeof u !== 'object') return null;
  return asNumber((u as any).id);
}

@Component({
  standalone: true,
  selector: 'app-domain-edit',
  imports: [
    ReactiveFormsModule,
    TabsModule,
    Editor,
    InputTextModule,
    Button,
    ToggleSwitchModule,
    SelectModule,
    PickListModule,
    BadgeModule,
    SelectButtonModule,
  ],
  templateUrl: './domain-edit.html',
  styleUrl: './domain-edit.scss',
})
export class DomainEdit implements OnInit {
  id!: number;

  loading = signal(true);
  submitError = signal<string | null>(null);
  translating = signal(false);

  domain = signal<DomainDetailDto | null>(null);

  // global languages (for selectButton options + code->id mapping)
  languages = signal<LanguageReadDto[]>([]);

  // users for owner/staff
  ownerOptions = signal<UserOption[]>([]);
  staffOptions = signal<UserOption[]>([]);
  availableStaff = signal<UserOption[]>([]);
  selectedStaff = signal<UserOption[]>([]);

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
    staff: new FormControl<number[]>([], {nonNullable: true}),

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
          console.error('Erreur chargement domain', err);
          return of(null as DomainDetailDto | null);
        }),
      ),
      users: this.userService.list().pipe(
        catchError((err) => {
          console.error('Erreur chargement users', err);
          return of([] as CustomUserReadDto[]);
        }),
      ),
      languages: this.languageService.list().pipe(
        catchError((err) => {
          console.error('Erreur chargement languages', err);
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

        // 2) Set global active languages
        const activeLangs = (languages ?? []).filter(l => l.active);
        this.languages.set(activeLangs);

        // 3) Build user options
        const opts: UserOption[] = (users ?? [])
          .filter(u => typeof u.id === 'number')
          .map(u => ({label: u.username, value: u.id}));

        this.ownerOptions.set(opts);
        this.staffOptions.set(opts);

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
          console.error('Erreur update domain', err);
          this.submitError.set("Erreur lors de l'enregistrement.");
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

  // --- helpers ---
  private translationsGroup(): FormGroup {
    return this.form.get('translations') as FormGroup;
  }

  private patchMetaFromDto(dto: DomainDetailDto): void {
    const ownerId = getUserId(dto.owner);

    const staffIds = (dto.staff ?? [])
      .map((u: any) => getUserId(u))
      .filter((id: any): id is number => typeof id === 'number');

    this.form.patchValue({
      active: dto.active ?? true,
      owner: ownerId,
      staff: staffIds,
    });
  }

  private syncTranslationControls(codes: string[]): void {
    const tg = this.translationsGroup();

    const wanted = new Set<string>(codes);
    const existing = new Set<string>(Object.keys(tg.controls));

    // add missing
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

    // remove obsolete
    for (const code of existing) {
      if (!wanted.has(code)) tg.removeControl(code);
    }

    // patch values from DTO for all wanted codes (stable, no emit)
    const dto = this.domain();
    if (dto) {
      const tr = (dto.translations ?? {}) as DomainTranslations;
      const patch: Record<string, { name: string; description: string }> = {};

      for (const code of wanted) {
        patch[code] = {
          name: tr[code]?.name ?? '',
          description: tr[code]?.description ?? '',
        };
      }

      tg.patchValue(patch, {emitEvent: false});
    }
  }

  private buildPayload(): DomainWriteRequestDto {
    const codes = this.form.controls.allowed_language_codes.value ?? [];
    const idMap = this.langIdByCode();

    const allowed_languages = codes
      .map(c => idMap[String(c)])
      .filter((id): id is number => typeof id === 'number');

    return {
      active: this.form.controls.active.value,
      owner: this.form.controls.owner.value,
      staff: this.form.controls.staff.value,
      allowed_languages,
      translations: this.translationsGroup().getRawValue(),
    } as any;
  }

  private ensureMeInStaff(emitEvent: boolean): number | null {
    const meId = this.userService.currentUser()?.id;
    if (typeof meId !== 'number') return null;

    const current = this.form.controls.staff.value ?? [];
    if (!current.includes(meId)) {
      this.form.controls.staff.setValue([...current, meId], {emitEvent});
    }
    return meId;
  }

  private recomputePickList(): void {
    this.ensureMeInStaff(false);

    const all = this.staffOptions();
    const selectedIds = new Set(this.form.controls.staff.value ?? []);

    this.selectedStaff.set(all.filter(o => selectedIds.has(o.value)));
    this.availableStaff.set(all.filter(o => !selectedIds.has(o.value)));
  }

  private isEmptyHtml(html: string): boolean {
    const s = (html ?? '').trim().toLowerCase();
    return !s || s === '<p><br></p>' || s === '<p></p>';
  }
}
