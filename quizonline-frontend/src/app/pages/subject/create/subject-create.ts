import {CommonModule} from '@angular/common';
import {Component, computed, DestroyRef, effect, inject, OnInit, signal} from '@angular/core';
import {
  FormControl,
  FormGroup,
  NonNullableFormBuilder,
  ReactiveFormsModule,
  Validators,
} from '@angular/forms';
import {catchError, finalize} from 'rxjs/operators';
import {EMPTY} from 'rxjs';
import {takeUntilDestroyed, toObservable} from '@angular/core/rxjs-interop';

import {ButtonModule} from 'primeng/button';
import {CardModule} from 'primeng/card';
import {MessageService} from 'primeng/api';

import {DomainDetailDto, DomainReadDto, LanguageEnumDto, SubjectWriteRequestDto} from '../../../api/generated';
import {DomainOption, DomainService, DomainTranslations} from '../../../services/domain/domain';
import {SubjectService, SubjectLangGroup} from '../../../services/subject/subject';
import {isLangCode, LangCode, TranslateBatchItem, TranslationService} from '../../../services/translation/translation';
import {UserService} from '../../../services/user/user';
import {
  buildLocalizedTextRecord,
  createLocalizedTextGroup,
  getLocalizedTextGroup,
} from '../../../shared/forms/localized-text-form';
import {isEmptyRichText} from '../../../shared/html/is-empty-rich-text';
import {SubjectEditorFormComponent} from '../../../components/subject-editor-form/subject-editor-form';
import {getEditorUiText} from '../../../shared/i18n/editor-ui-text';


@Component({
  selector: 'app-subject-create',
  standalone: true,
  templateUrl: './subject-create.html',
  styleUrls: ['./subject-create.scss'],
  imports: [
    CommonModule,
    ReactiveFormsModule,
    ButtonModule,
    CardModule,
    SubjectEditorFormComponent,
  ],
})
export class SubjectCreate implements OnInit {
  readonly ui = computed(() => getEditorUiText(this.userService.currentLang));
  readonly emptyLanguagesMessage = "Ce domaine n'a pas de langues configurees.";

  // UI state
  loading = signal(false);
  error = signal<string | null>(null);

  translating = signal(false);
  submitError = signal<string | null>(null);

  readonly isLocked = computed(() => this.loading() || this.translating());

  private readonly domainMetaFallbacks: LanguageEnumDto[] = [LanguageEnumDto.Fr, LanguageEnumDto.En, LanguageEnumDto.Nl];

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
  private messageService = inject(MessageService);
  private destroyRef = inject(DestroyRef);
  private selectedDomainId$ = toObservable(this.selectedDomainId);
  private lastToastMessage: string | null = null;

  constructor() {
    // lock/unlock the form
    effect(() => {
      const locked = this.isLocked();
      if (locked) this.form.disable({emitEvent: false});
      else this.form.enable({emitEvent: false});
    });
    effect(() => {
      const detail = this.submitError() ?? this.error();
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
    this.currentLang.set(this.userService.currentLang ?? LanguageEnumDto.Fr);

    // load domains
    this.loading.set(true);
    this.domainService
      .list()
      .pipe(
        takeUntilDestroyed(this.destroyRef),
        finalize(() => this.loading.set(false)),
      )
      .subscribe({
        next: (domains) => {
          this.domains.set(domains ?? []);

          const currentDomainId = this.userService.currentUser()?.current_domain ?? 0;
          if (currentDomainId > 0 && (domains ?? []).some((domain) => domain.id === currentDomainId)) {
            this.selectedDomainId.set(currentDomainId);
          }
        },
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
            this.activeLang.set(this.resolvePreferredLang(codes));
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
    return getLocalizedTextGroup(this.translationsGroup(), code);
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
        const needDesc = overwrite || isEmptyRichText(descCtrl.value ?? '');

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
        tg.addControl(code, createLocalizedTextGroup(this.fb, {nameMaxLength: 120}));
      }
    }
  }

  private getTranslationGroup(code: LangCode): SubjectLangGroup {
    return getLocalizedTextGroup(this.translationsGroup(), code) as SubjectLangGroup;
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
    const translations = buildLocalizedTextRecord(this.translationsGroup(), langs);

    return this.subjectService.buildWritePayload(domainId, translations);
  }

  private getDomainLabel(domain: Pick<DomainReadDto, 'id' | 'translations'>, lang: LanguageEnumDto): string {
    const tr = domain.translations as DomainTranslations | undefined;

    const inCurrent = tr?.[lang]?.name?.trim();
    if (inCurrent) return inCurrent;

    for (const fb of this.domainMetaFallbacks) {
      const v = tr?.[fb]?.name?.trim();
      if (v) return v;
    }

    return `Domain #${domain.id}`;
  }

  private extractLangCodes(domain: Pick<DomainDetailDto, 'allowed_languages'>): LangCode[] {
    const codes = (domain.allowed_languages ?? [])
      .filter((language) => language.active)
      .map((language) => language.code)
      .filter(isLangCode);

    return codes.length ? codes : [LanguageEnumDto.Fr as LangCode];
  }

  private resolvePreferredLang(codes: LangCode[]): LangCode | undefined {
    const current = this.currentLang();
    return codes.includes(current as LangCode) ? current as LangCode : codes[0];
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
      case 'Impossible de charger les domaines.':
        return this.msg('Unable to load domains.', 'Impossible de charger les domaines.', 'Kan de domeinen niet laden.', 'Impossibile caricare i domini.', 'No se pueden cargar los dominios.');
      case 'Impossible de charger le domaine sÃ©lectionnÃ©.':
        return this.msg('Unable to load the selected domain.', 'Impossible de charger le domaine selectionne.', 'Kan het geselecteerde domein niet laden.', 'Impossibile caricare il dominio selezionato.', 'No se puede cargar el dominio seleccionado.');
      case 'Erreur lors de la traduction.':
        return this.msg('Translation failed.', 'Erreur lors de la traduction.', 'Fout tijdens het vertalen.', 'Errore durante la traduzione.', 'Error durante la traduccion.');
      case 'Merci de remplir au minimum le champ "name" pour chaque langue.':
        return this.msg('Fill in at least the name field for each language.', 'Merci de remplir au minimum le champ "name" pour chaque langue.', 'Vul minstens het veld naam in voor elke taal.', 'Compila almeno il campo nome per ogni lingua.', 'Completa al menos el campo nombre para cada idioma.');
      case 'Erreur lors de la crÃ©ation du sujet.':
        return this.msg('An error occurred while creating the subject.', 'Erreur lors de la creation du sujet.', 'Fout bij het aanmaken van het onderwerp.', 'Errore durante la creazione dell argomento.', 'Error al crear el tema.');
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

}
