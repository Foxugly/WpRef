import {CommonModule} from '@angular/common';
import {Component, computed, DestroyRef, effect, inject, OnInit, signal} from '@angular/core';
import {
  FormControl,
  FormGroup,
  FormsModule,
  NonNullableFormBuilder,
  ReactiveFormsModule,
  Validators,
} from '@angular/forms';
import {catchError, finalize} from 'rxjs/operators';
import {EMPTY} from 'rxjs';
import {takeUntilDestroyed, toObservable} from '@angular/core/rxjs-interop';

import {Editor} from 'primeng/editor';
import {TabsModule} from 'primeng/tabs';
import {SelectModule} from 'primeng/select';
import {ButtonModule} from 'primeng/button';
import {InputTextModule} from 'primeng/inputtext';
import {CardModule} from 'primeng/card';

import {DomainReadDto, LanguageEnumDto, SubjectWriteRequestDto} from '../../../api/generated';
import {DomainOption, DomainService, DomainTranslations} from '../../../services/domain/domain';
import {SubjectService, SubjectLangGroup} from '../../../services/subject/subject';
import {LangCode, TranslateBatchItem, TranslationService} from '../../../services/translation/translation';
import {UserService} from '../../../services/user/user';


@Component({
  selector: 'app-subject-create',
  standalone: true,
  templateUrl: './subject-create.html',
  styleUrls: ['./subject-create.scss'],
  imports: [
    CommonModule,
    ReactiveFormsModule,
    FormsModule,
    Editor,
    TabsModule,
    SelectModule,
    ButtonModule,
    InputTextModule,
    CardModule,
  ],
})
export class SubjectCreate implements OnInit {
  // UI state
  loading = signal(false);
  error = signal<string | null>(null);

  translating = signal(false);
  submitError = signal<string | null>(null);

  readonly isLocked = computed(() => this.loading() || this.translating());

  // Domain list
  domains = signal<DomainReadDto[]>([]);
  selectedDomainId = signal<number>(0);

  // Languages (from selected domain)
  domainLangs = signal<LangCode[]>([]);
  activeLang = signal<LangCode | undefined>(undefined);

  // current UI language (for labels)
  currentLang = signal<LanguageEnumDto>(LanguageEnumDto.Fr);
  translateOverwrite = signal(false);
  domainOptions = computed<DomainOption[]>(() => {
    const lang = this.currentLang();
    return (this.domains() ?? []).map((d) => ({
      id: d.id,
      name: this.getDomainLabel(d, lang),
    }));
  });
  // Reactive form
  private fb = inject(NonNullableFormBuilder);
  form = this.fb.group({
    // domain stored here too (single source of truth for submit)
    domain: this.fb.control<number>(0, {validators: [Validators.required]}),
    translations: this.fb.group({}),
  });
  // deps
  private domainService = inject(DomainService);
  private subjectService = inject(SubjectService);
  private translator = inject(TranslationService);
  private userService = inject(UserService);
  private destroyRef = inject(DestroyRef);
  private selectedDomainId$ = toObservable(this.selectedDomainId);

  constructor() {
    // lock/unlock the form
    effect(() => {
      const locked = this.isLocked();
      if (locked) this.form.disable({emitEvent: false});
      else this.form.enable({emitEvent: false});
    });
  }

  ngOnInit(): void {
    this.currentLang.set(this.userService.currentLang ?? LanguageEnumDto.Fr);

    // load domains
    this.loading.set(true);
    this.domainService
      .list({asStaff: true} as any)
      .pipe(
        takeUntilDestroyed(this.destroyRef),
        finalize(() => this.loading.set(false)),
      )
      .subscribe({
        next: (domains) => this.domains.set(domains ?? []),
        error: (err) => {
          console.error(err);
          this.error.set('Impossible de charger les domaines.');
        },
      });

    // react: domain change => reset + load domain detail
    this.selectedDomainId$
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe((id) => {
        this.resetDomainState();

        if (!id || id <= 0) return;

        this.form.controls.domain.setValue(id);
        this.loading.set(true);

        this.domainService
          .detail(id)
          .pipe(
            finalize(() => this.loading.set(false)),
            catchError((err) => {
              console.error(err);
              this.error.set('Impossible de charger le domaine sélectionné.');
              return EMPTY;
            }),
          )
          .subscribe((domain) => {
            const codes = this.extractLangCodes(domain);
            this.domainLangs.set(codes);

            this.ensureLanguageControls(codes);
            this.activeLang.set(codes[0] ?? null);
          });
      });
  }

  // UI actions
  onDomainChange(value: number): void {
    this.selectedDomainId.set(value);
  }

  onTabChange(value: string | number | undefined): void {
    if (value === undefined || value === null) return;
    const code = String(value) as LangCode;
    if (!this.domainLangs().includes(code)) return;
    this.activeLang.set(code);
  }

  tabCodes(): LangCode[] {
    return this.domainLangs();
  }

  langGroup(code: string): FormGroup {
    return (this.form.get('translations') as FormGroup).get(code) as FormGroup;
  }

  async translateFrom(sourceLang: LangCode): Promise<void> {
    const codes = this.tabCodes();
    if (!codes.includes(sourceLang)) return;

    this.translating.set(true);
    this.submitError.set(null);

    try {
      const source = this.getTranslationGroup(sourceLang);
      const sourceName = source.controls.name.value ?? '';
      const sourceDesc = source.controls.description.value ?? '';

      const overwrite = this.translateOverwrite();

      for (const targetLang of codes) {
        if (targetLang === sourceLang) continue;

        const target = this.getTranslationGroup(targetLang);
        const nameCtrl = target.controls.name;
        const descCtrl = target.controls.description;

        const needName = overwrite || !(nameCtrl.value ?? '').trim();
        const needDesc = overwrite || this.isEmptyHtml(descCtrl.value ?? '');

        const items: TranslateBatchItem[] = [];
        if (needName) items.push({key: 'name', text: sourceName, format: 'text'});
        if (needDesc) items.push({key: 'description', text: sourceDesc, format: 'html'});

        if (!items.length) continue;

        const out = await this.translator.translateBatch(sourceLang, targetLang, items);

        if (needName && out['name'] !== undefined) {
          nameCtrl.setValue(out['name']);
          nameCtrl.markAsDirty();
        }
        if (needDesc && out['description'] !== undefined) {
          descCtrl.setValue(out['description']);
          descCtrl.markAsDirty();
        }
      }
    } catch (e) {
      console.error(e);
      this.submitError.set('Erreur lors de la traduction.');
    } finally {
      this.translating.set(false);
    }
  }

  async translateFromActiveTab(): Promise<void> {
    const src = this.activeLang();
    if (!src) return;
    await this.translateFrom(src);
  }

  submit(): void {
    this.error.set(null);
    this.submitError.set(null);

    if (!this.isValid()) {
      this.error.set('Merci de remplir au minimum le champ "name" pour chaque langue.');
      return;
    }

    const payload = this.buildPayload();
    this.loading.set(true);

    this.subjectService
      .create(payload)
      .pipe(
        takeUntilDestroyed(this.destroyRef),
        finalize(() => this.loading.set(false)),
      )
      .subscribe({
        next: () => this.subjectService.goList(),
        error: (err) => {
          console.error(err);
          this.submitError.set('Erreur lors de la création du sujet.');
        },
      });
  }

  protected goList(): void {
    this.subjectService.goList();
  }

  // ====== helpers ======

  private resetDomainState(): void {
    this.error.set(null);
    this.submitError.set(null);
    this.domainLangs.set([]);
    this.activeLang.set(undefined);

    // reset translations form group
    const tg = this.translationsGroup();
    Object.keys(tg.controls).forEach((key) => tg.removeControl(key));
  }

  private translationsGroup(): FormGroup {
    return this.form.get('translations') as FormGroup;
  }

  private ensureLanguageControls(codes: LangCode[]): void {
    const tg = this.translationsGroup();

    for (const code of codes) {
      if (!tg.contains(code)) {
        tg.addControl(
          code,
          this.fb.group({
            name: this.fb.control('', {validators: [Validators.required, Validators.minLength(2), Validators.maxLength(120)]}),
            description: this.fb.control(''),
          }),
        );
      }
    }
  }

  private getTranslationGroup(code: LangCode): SubjectLangGroup {
    const tg = this.translationsGroup();
    const fg = tg.get(code) as SubjectLangGroup | null;
    if (!fg) throw new Error(`Missing form group for language: ${code}`);
    return fg;
  }

  private isValid(): boolean {
    const domainId = this.form.controls.domain.value;
    if (!domainId || domainId <= 0) return false;

    const langs = this.domainLangs();
    if (langs.length === 0) return false;

    const tg = this.translationsGroup();
    return langs.every((l) => (tg.get(l) as SubjectLangGroup | null)?.valid === true);
  }

  private buildPayload(): SubjectWriteRequestDto {
    const domainId = this.form.controls.domain.value;
    const langs = this.domainLangs();
    const tg = this.translationsGroup();

    const translations: Record<string, { name: string; description: string }> = {};
    for (const lang of langs) {
      const fg = tg.get(lang) as SubjectLangGroup | null;
      if (!fg) continue;
      const v = fg.getRawValue();
      translations[lang] = {name: v.name, description: v.description};
    }

    return this.subjectService.buildWritePayload(domainId, translations);
  }

  private getDomainLabel(domain: DomainReadDto, lang: LanguageEnumDto): string {
    const tr = domain.translations as DomainTranslations | undefined;

    const inCurrent = tr?.[lang]?.name?.trim();
    if (inCurrent) return inCurrent;

    const fallbacks: LanguageEnumDto[] = [LanguageEnumDto.Fr, LanguageEnumDto.En, LanguageEnumDto.Nl];
    for (const fb of fallbacks) {
      const v = tr?.[fb]?.name?.trim();
      if (v) return v;
    }

    return `Domain #${domain.id}`;
  }

  private extractLangCodes(domain: DomainReadDto): LangCode[] {
    const d: any = domain;

    if (Array.isArray(d.allowed_language_codes)) {
      return d.allowed_language_codes as LangCode[];
    }

    if (Array.isArray(d.allowed_languages)) {
      return (d.allowed_languages as any[])
        .map((x) => x?.code)
        .filter(Boolean) as LangCode[];
    }

    return [LanguageEnumDto.Fr as unknown as LangCode];
  }

  private isEmptyHtml(html: string): boolean {
    const cleaned = (html ?? '')
      .replace(/<br\s*\/?>/gi, '')
      .replace(/&nbsp;/gi, ' ')
      .replace(/<[^>]+>/g, '')
      .trim();
    return cleaned.length === 0;
  }
}
