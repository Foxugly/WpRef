import {CommonModule} from '@angular/common';
import {Component, computed, DestroyRef, effect, inject, OnInit, signal} from '@angular/core';
import {ActivatedRoute} from '@angular/router';
import {
  FormArray,
  FormControl,
  FormGroup,
  NonNullableFormBuilder,
  ReactiveFormsModule,
  Validators,
} from '@angular/forms';
import {finalize} from 'rxjs/operators';
import {takeUntilDestroyed} from '@angular/core/rxjs-interop';
import {firstValueFrom, forkJoin} from 'rxjs';

import {Editor} from 'primeng/editor';
import {TabsModule} from 'primeng/tabs';
import {SelectModule} from 'primeng/select';
import {MultiSelectModule} from 'primeng/multiselect';
import {CheckboxModule} from 'primeng/checkbox';
import {InputTextModule} from 'primeng/inputtext';
import {InputNumberModule} from 'primeng/inputnumber';
import {ButtonModule} from 'primeng/button';
import {PanelModule} from 'primeng/panel';
import {CardModule} from 'primeng/card';
import {TooltipModule} from 'primeng/tooltip';


import {
  DomainReadDto,
  LanguageEnumDto,
  MediaAssetDto,
  MediaAssetUploadKindEnumDto,
  QuestionCreateRequestParams,
  QuestionMediaCreateRequestParams,
  QuestionReadDto, QuestionWriteRequestDto,
  SubjectReadDto
} from '../../../api/generated';
import {DomainOption, DomainService, DomainTranslations} from '../../../services/domain/domain';
import {SubjectService} from '../../../services/subject/subject';
import {
  AnswerOptionForm,
  AnswerTrGroup,
  QuestionService,
  QuestionTrGroup,
  QuestionCreateJsonPayload
} from '../../../services/question/question';
import {LangCode, TranslateBatchItem, TranslationService} from '../../../services/translation/translation';
import {UserService} from '../../../services/user/user';
import {selectTranslation} from '../../../shared/i18n/select-translation';
import {MediaSelectorComponent, MediaSelectorValue} from '../../../components/media-selector/media-selector';
import {Divider} from 'primeng/divider';

@Component({
  standalone: true,
  selector: 'app-question-create',
  templateUrl: './question-create.html',
  styleUrl: './question-create.scss',
  imports: [
    CommonModule,
    ReactiveFormsModule,
    Editor,
    TabsModule,
    SelectModule,
    MultiSelectModule,
    CheckboxModule,
    InputTextModule,
    InputNumberModule,
    ButtonModule,
    PanelModule,
    CardModule,
    TooltipModule,

    MediaSelectorComponent,
    Divider,
  ],
})
export class QuestionCreate implements OnInit {
  // ===== Loading states =====
  loading = signal(true);      // domains + subjects
  domainLoading = signal(false);   // retrieve selected domain
  saving = signal(false);
  translating = signal(false);

  error = signal<string | null>(null);
  submitError = signal<string | null>(null);

  readonly isLocked = computed(() => this.loading() || this.domainLoading() || this.saving() || this.translating());

  // ===== Data =====
  domains = signal<DomainReadDto[]>([]);
  subjects = signal<SubjectReadDto[]>([]);

  // ===== Domain selection as signal (critical) =====
  selectedDomainId = signal<number>(0);

  // Langs du domaine sélectionné
  domainLangs = signal<LangCode[]>([]);
  activeLang = signal<LangCode | null>(null);

  // UI lang (labels domain/subject)
  currentLang = signal<LanguageEnumDto>(LanguageEnumDto.En);

  translateOverwrite = signal(false);

  domainOptions = computed<DomainOption[]>(() => {
    const lang = this.currentLang();
    return (this.domains() ?? []).map((d) => ({
      id: d.id,
      name: this.getDomainLabel(d, lang),
    }));
  });

  filteredSubjects = computed<SubjectReadDto[]>(() => {
    const domainId = this.selectedDomainId();
    if (!domainId) return [];
    return (this.subjects() ?? []).filter((s) => s.domain === domainId);
  });

  subjectOptions = computed<Array<{ name: string; code: number }>>(() => {
    const lang = this.currentLang();
    return this.filteredSubjects().map((s) => {
      const t = selectTranslation<{ name: string }>(
        s.translations as Record<string, { name: string }>,
        lang,
      );
      return {name: t?.name ?? `Subject #${s.id}`, code: s.id};
    });
  });

  subjectsDisabled = computed(() => {
    return this.isLocked() || !this.selectedDomainId() || this.subjectOptions().length === 0;
  });

  // ===== deps =====
  private fb = inject(NonNullableFormBuilder);
  // ===== form =====
  form = this.fb.group({
    domain: this.fb.control<number>(0, {validators: [Validators.required]}),
    subject_ids: new FormControl<number[]>({value: [], disabled: true}, {nonNullable: true}),

    active: this.fb.control(true),
    //allow_multiple_correct: this.fb.control(false), // TODO rajouter dans le submit
    is_mode_practice: this.fb.control(true),
    is_mode_exam: this.fb.control(false),

    media: this.fb.control<MediaSelectorValue[]>([]),

    // translations[lang] contains title/desc/expl + answer_options[ {content} ... ]
    translations: this.fb.group({}),

    // root answer_options contains only meta: is_correct + sort_order
    answer_options: this.fb.array<FormGroup>([]),
  });
  private destroyRef = inject(DestroyRef);
  private route = inject(ActivatedRoute);
  private domainService = inject(DomainService);
  private subjectService = inject(SubjectService);
  private questionService = inject(QuestionService);
  private translator = inject(TranslationService);
  private userService = inject(UserService);

  constructor() {
    // enable/disable controls without destroying DOM
    effect(() => {
      const locked = this.isLocked();

      if (locked) this.form.controls.domain.disable({emitEvent: false});
      else this.form.controls.domain.enable({emitEvent: false});

      const shouldEnableSubjects = !locked && !!this.selectedDomainId() && this.subjectOptions().length > 0;
      if (shouldEnableSubjects) this.form.controls.subject_ids.enable({emitEvent: false});
      else this.form.controls.subject_ids.disable({emitEvent: false});
    });
  }

  // ===== getters =====
  get answerOptions(): FormArray {
    return this.form.controls.answer_options as unknown as FormArray;
  }

  tabCodes(): LangCode[] {
    return this.domainLangs();
  }

  translationsGroup(): FormGroup {
    return this.form.get('translations') as FormGroup;
  }

  // ===== lifecycle =====
  ngOnInit(): void {
    this.currentLang.set(this.userService.currentLang ?? LanguageEnumDto.Fr);

    // react to domain changes (single source of truth)
    this.form.controls.domain.valueChanges
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe(v => this.onDomainChange(Number(v ?? 0)));

    // load domains + subjects together (pageLoading)
    this.loading.set(true);
    forkJoin({
      domains: this.domainService.list({asStaff: true} as any),
      subjects: this.subjectService.list(),
    })
      .pipe(
        takeUntilDestroyed(this.destroyRef),
        finalize(() => this.loading.set(false)),
      )
      .subscribe({
        next: ({domains, subjects}) => {
          this.domains.set(domains ?? []);
          this.subjects.set(subjects ?? []);
        },
        error: (err) => {
          console.error(err);
          this.error.set('Impossible de charger les données initiales.');
        }
      });
    // preselect domain from query param
    const qpDomainId = Number(this.route.snapshot.queryParamMap.get('domainId') ?? 0);
    if (qpDomainId > 0) {
      this.form.controls.domain.setValue(qpDomainId);
      // handleDomainChange will be triggered by valueChanges
    }
  }

  // ===== navigation =====
  goList(): void {
    this.questionService.goList();
  }

  goBack(): void {
    this.questionService.goBack();
  }

  onTabChange(value: string | number | undefined): void {
    if (value === undefined || value === null) return;
    const code = String(value) as LangCode;
    if (!this.domainLangs().includes(code)) return;
    this.activeLang.set(code);
  }

  // ===== answers meta =====
  addOption(): void {
    const idx = this.answerOptions.length;

    // root meta
    const group = this.fb.group({
      is_correct: this.fb.control(false),
      sort_order: this.fb.control(idx + 1),
    });
    this.answerOptions.push(group as any);

    // per-lang content
    for (const lang of this.domainLangs()) {
      this.langAnswerOptions(lang).push(
        this.fb.group({
          content: this.fb.control('', {validators: [Validators.required]}),
          //is_correct: this.fb.control(false),
        }) as any,
      );
    }
  }

  removeOption(index: number): void {
    if (this.answerOptions.length <= 2) return; // backend min 2

    this.answerOptions.removeAt(index);

    for (const lang of this.domainLangs()) {
      const arr = this.langAnswerOptions(lang);
      if (arr.length > index) arr.removeAt(index);
    }

    // renumber sort_order
    this.answerOptions.controls.forEach((ctrl, i) => {
      ctrl.get('sort_order')?.setValue(i + 1);
    });
  }

  setOnlyCorrect(index: number): void {
    this.answerOptions.controls.forEach((ctrl, i) => {
      ctrl.get('is_correct')?.setValue(i === index);
    });
  }

  // ===== per-lang answer content access =====
  langAnswerOptions(lang: LangCode): FormArray {
    return this.langGroup(lang).get('answer_options') as unknown as FormArray;
  }

  answerContentCtrl(i: number, lang: LangCode): FormControl<string> {
    const arr = this.langAnswerOptions(lang);
    const row = arr.at(i) as AnswerTrGroup;
    return row.get('content') as FormControl<string>;
  }

  // ===== translate =====
  async translateFromActiveTab(): Promise<void> {
    const src = this.activeLang();
    if (!src) return;
    await this.translateFrom(src);
  }

  async translateFrom(sourceLang: LangCode): Promise<void> {
    const codes = this.tabCodes();
    if (!codes.includes(sourceLang)) return;

    this.translating.set(true);
    this.submitError.set(null);

    try {
      const srcQ = this.getQuestionTrGroup(sourceLang);
      const srcTitle = srcQ.controls.title.value ?? '';
      const srcDesc = srcQ.controls.description.value ?? '';
      const srcExpl = srcQ.controls.explanation.value ?? '';

      const overwrite = this.translateOverwrite();

      for (const targetLang of codes) {
        if (targetLang === sourceLang) continue;

        const tgtQ = this.getQuestionTrGroup(targetLang);

        const items: TranslateBatchItem[] = [];

        const needTitle = overwrite || !(tgtQ.controls.title.value ?? '').trim();
        if (needTitle) items.push({key: 'title', text: srcTitle, format: 'text'});

        const needDesc = overwrite || this.isEmptyHtml(tgtQ.controls.description.value ?? '');
        if (needDesc) items.push({key: 'description', text: srcDesc, format: 'html'});

        const needExpl = overwrite || this.isEmptyHtml(tgtQ.controls.explanation.value ?? '');
        if (needExpl) items.push({key: 'explanation', text: srcExpl, format: 'html'});

        for (let i = 0; i < this.answerOptions.length; i++) {
          const tgtCtrl = this.answerContentCtrl(i, targetLang);
          const needAns = overwrite || this.isEmptyHtml(tgtCtrl.value ?? '');
          if (!needAns) continue;

          const srcCtrl = this.answerContentCtrl(i, sourceLang);
          items.push({key: `ans_${i}`, text: srcCtrl.value ?? '', format: 'html'});
        }

        if (!items.length) continue;
        console.log('TRANSLATE items', items);
        const out = await this.translator.translateBatch(sourceLang, targetLang, items);
        console.log('retour TRANSLATE items', out);
        if (needTitle && out['title'] !== undefined) {
          tgtQ.controls.title.setValue(out['title']);
          tgtQ.controls.title.markAsDirty();
        }
        if (needDesc && out['description'] !== undefined) {
          tgtQ.controls.description.setValue(out['description']);
          tgtQ.controls.description.markAsDirty();
        }
        if (needExpl && out['explanation'] !== undefined) {
          tgtQ.controls.explanation.setValue(out['explanation']);
          tgtQ.controls.explanation.markAsDirty();
        }

        for (let i = 0; i < this.answerOptions.length; i++) {
          const k = `ans_${i}`;
          if (out[k] === undefined) continue;
          const tgt = this.answerContentCtrl(i, targetLang);
          tgt.setValue(out[k]);
          tgt.markAsDirty();
        }
      }
    } catch (e) {
      console.error(e);
      this.submitError.set('Erreur lors de la traduction.');
    } finally {
      this.translating.set(false);
    }
  }

  // ===== submit =====
  async save(): Promise<void> {
    this.error.set(null);
    this.submitError.set(null);

    if (!this.isValid()) {
      this.error.set('Merci de sélectionner un domaine et de compléter au minimum le titre dans chaque langue et toutes les réponses.');
      this.form.markAllAsTouched();
      return;
    }

    const correctCount = this.answerOptions.controls.filter(
      (ctrl) => !!ctrl.get('is_correct')?.value
    ).length;

    if (correctCount === 0) {
      this.submitError.set('Il faut cocher au moins une réponse correcte.');
      return;
    }
    // récupérer les medias

    this.saving.set(true);
    try {
      const mediaAssetIds = await this._createMediaAsset();
      const qwrdto:QuestionWriteRequestDto = this.buildQuestionWriteRequestDto(mediaAssetIds);

      await firstValueFrom(
        this.questionService.create(qwrdto).pipe(
          takeUntilDestroyed(this.destroyRef),
          finalize(() => this.saving.set(false)),
        )
      );

      this.goList();
    } catch (err) {
      console.error('Erreur création question', err);
      this.submitError.set("Erreur lors de l'enregistrement de la question.");
      this.saving.set(false);
    }
  }

  // ===== domain selection =====
  protected onDomainChange(domainId: number): void {
    this.error.set(null);
    this.submitError.set(null);
    this.selectedDomainId.set(domainId);
    // reset when domain changes
    this.form.controls.subject_ids.setValue([]);
    this.resetTranslationsOnly();
    this.domainLangs.set([]);
    this.activeLang.set(null);

    if (!domainId || domainId <= 0) return;

    this.domainLoading.set(true);
    this.domainService
      .retrieve(domainId)
      .pipe(
        takeUntilDestroyed(this.destroyRef),
        finalize(() => this.domainLoading.set(false)),
      )
      .subscribe({
        next: (d: DomainReadDto) => {
          const codes = (d.allowed_languages ?? [])
            .filter((l) => !!l.active)
            .map((x) => x?.code)
            .filter((x): x is LangCode => !!x);

          const langs = codes.length ? codes : [LanguageEnumDto.Fr as unknown as LangCode];

          this.domainLangs.set(langs);

          // create translations[lang] groups (including per-lang answer_options array)
          this.ensureQuestionTranslationControls(langs);
          if (this.answerOptions.length === 0) {
            this.addOption();
            this.addOption();
          }
          // make sure per-lang answer_options arrays have same length as root answerOptions
          this.syncLangAnswerArraysWithRoot(langs);

          this.activeLang.set(langs[0] ?? null);
        },
        error: (err) => {
          console.error(err);
          this.error.set('Impossible de charger le domaine sélectionné.');
        },
      });
  }

  protected answerMetaGroup(i: number): FormGroup {
    return this.answerOptions.at(i) as FormGroup;
  }

  // ===== helpers =====
  private langGroup(lang: LangCode): FormGroup {
    return this.translationsGroup().get(lang) as FormGroup;
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

  private syncLangAnswerArraysWithRoot(langs: LangCode[]): void {
    const needed = this.answerOptions.length;

    for (const lang of langs) {
      const arr = this.langAnswerOptions(lang);

      while (arr.length < needed) {
        arr.push(
          this.fb.group({
            content: this.fb.control('', {validators: [Validators.required]}),
            //is_correct: this.fb.control(false),
          }) as any,
        );
      }
      while (arr.length > needed) {
        arr.removeAt(arr.length - 1);
      }
    }
  }

  private ensureQuestionTranslationControls(codes: LangCode[]): void {
    const tg = this.translationsGroup();

    // remove old controls not in codes
    Object.keys(tg.controls).forEach((k) => {
      if (!codes.includes(k as LangCode)) tg.removeControl(k);
    });

    // add missing
    for (const code of codes) {
      if (!tg.contains(code)) {
        tg.addControl(
          code,
          this.fb.group({
            title: this.fb.control('', {
              validators: [Validators.required, Validators.minLength(2), Validators.maxLength(200)],
            }),
            description: this.fb.control(''),
            explanation: this.fb.control(''),
            answer_options: this.fb.array<AnswerTrGroup>([]),
          }),
        );
      }
    }
  }

  private resetTranslationsOnly(): void {
    const qtg = this.translationsGroup();
    Object.keys(qtg.controls).forEach((k) => qtg.removeControl(k));
  }

  private getQuestionTrGroup(code: LangCode): QuestionTrGroup {
    const fg = this.translationsGroup().get(code) as QuestionTrGroup | null;
    if (!fg) throw new Error(`Missing question translation group for: ${code}`);
    return fg;
  }

  private isValid(): boolean {
    const domainId = this.selectedDomainId();
    if (!domainId) return false;

    const langs = this.domainLangs();
    if (!langs.length) return false;

    // title required per lang
    const okTitles = langs.every((l) => this.getQuestionTrGroup(l).controls.title.valid === true);
    if (!okTitles) return false;

    // answers: min 2
    if (this.answerOptions.length < 2) return false;

    // per-lang answer content required
    for (const l of langs) {
      const arr = this.langAnswerOptions(l);
      if (arr.length !== this.answerOptions.length) return false;

      for (let i = 0; i < arr.length; i++) {
        const g = arr.at(i) as AnswerTrGroup;
        if (!g || g.controls.content.invalid) return false;
      }
    }
    return true;
  }

  private buildQuestionWriteRequestDto(media_ids: number[]): QuestionWriteRequestDto {
    const langs = this.domainLangs();
    const tg = this.translationsGroup();

    const translations: QuestionCreateJsonPayload['translations'] = {} as any;
    for (const l of langs) {
      const g = tg.get(l) as QuestionTrGroup;
      translations[l] = {
        title: g.controls.title.value ?? '',
        description: g.controls.description.value ?? '',
        explanation: g.controls.explanation.value ?? '',
      };
    }

    const answer_options: AnswerOptionForm[] = [];
    let correctCount = 0;
    for (let i = 0; i < this.answerOptions.length; i++) {
      const opt = this.answerOptions.at(i) as FormGroup;

      const isCorrect = !!opt.get('is_correct')?.value;
      if (isCorrect) correctCount++;

      const perLang: AnswerOptionForm['translations'] = {} as any;
      for (const l of langs) {
        const contentCtrl = this.answerContentCtrl(i, l);
        perLang[l] = {content: contentCtrl.value ?? ''};
      }

      answer_options.push({
        is_correct: isCorrect,
        sort_order: Number(opt.get('sort_order')?.value ?? (i + 1)),
        translations: perLang,
      });
    }

    return {
      domain: Number(this.form.controls.domain.value),
      subject_ids: this.form.controls.subject_ids.value ?? [],
      allow_multiple_correct: correctCount > 1,
      active: !!this.form.controls.active.value,
      is_mode_practice: !!this.form.controls.is_mode_practice.value,
      is_mode_exam: !!this.form.controls.is_mode_exam.value,
      translations: translations,
      answer_options: answer_options,
      media_asset_ids: media_ids ?? [],
    };
  }

  private getTitle(question: QuestionReadDto): string {
    return this.questionService.getQuestionTranslationForm(question, this.currentLang()).title ?? ' ';
  }

  private getDescription(question: QuestionReadDto): string {
    return this.questionService.getQuestionTranslationForm(question, this.currentLang()).description ?? ' ';
  }

  private getExplanation(question: QuestionReadDto): string {
    return this.questionService.getQuestionTranslationForm(question, this.currentLang()).explanation ?? ' ';
  }


  private isEmptyHtml(html: string): boolean {
    const cleaned = (html ?? '')
      .replace(/<br\s*\/?>/gi, '')
      .replace(/&nbsp;/gi, ' ')
      .replace(/<[^>]+>/g, '')
      .trim();
    return cleaned.length === 0;
  }

  private async _createMediaAsset(): Promise<number[]> {
    const media: MediaSelectorValue[] = this.form.get('media')?.value ?? [];
    if (!media.length) return [];

    const ids: number[] = [];

    for (const m of media) {
      // --------------------------------------------------
      // 1) Media déjà existant
      // --------------------------------------------------
      if (m.id) {
        ids.push(m.id);
        continue;
      }

      // --------------------------------------------------
      // 2) Media externe
      // --------------------------------------------------
      if (m.kind === MediaAssetUploadKindEnumDto.External && m.external_url) {
        const params: QuestionMediaCreateRequestParams = {
          kind: m.kind as MediaAssetUploadKindEnumDto,
          externalUrl: m.external_url,
        };

        const res: MediaAssetDto = await firstValueFrom(
          this.questionService.questionMediaCreate(params)
        );

        ids.push(res.id);
        continue;
      }

      // --------------------------------------------------
      // 3) Upload fichier (image / video)
      // --------------------------------------------------
      if (
        (m.kind === MediaAssetUploadKindEnumDto.Image || m.kind === MediaAssetUploadKindEnumDto.Video) &&
        m.file instanceof File
      ) {
        const fd = new FormData();
        fd.append('file', m.file);
        fd.append('kind', m.kind); // string enum OK

        const res = await firstValueFrom(
          this.questionService.questionMediaCreate(fd as any)
        );

        ids.push(res.id);
        continue;
      }

      // --------------------------------------------------
      // 4) Sécurité
      // --------------------------------------------------
      throw new Error(`Media invalide: ${JSON.stringify(m)}`);
    }

    // --------------------------------------------------
    // 5) Dédup en conservant l'ordre
    // --------------------------------------------------
    return [...new Set(ids)];
  }

}
