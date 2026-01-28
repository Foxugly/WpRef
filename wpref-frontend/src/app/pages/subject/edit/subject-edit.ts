import {Component, computed, DestroyRef, inject, OnInit, signal} from '@angular/core';
import {ActivatedRoute} from '@angular/router';
import {FormBuilder, FormControl, FormGroup, ReactiveFormsModule, Validators,} from '@angular/forms';

import {catchError, finalize} from 'rxjs/operators';
import {EMPTY} from 'rxjs';
import {takeUntilDestroyed} from '@angular/core/rxjs-interop';

import {Editor} from 'primeng/editor';
import {InputTextModule} from 'primeng/inputtext';
import {Button} from 'primeng/button';
import {TabsModule} from 'primeng/tabs';
import {PickListModule} from 'primeng/picklist';

import {DomainReadDto, LanguageReadDto, SubjectDetailDto, SubjectWriteRequestDto,} from '../../../api/generated';

import {SubjectLangGroup, SubjectService, SubjectTranslationsWrite} from '../../../services/subject/subject';
import {DomainService} from '../../../services/domain/domain';
import {UserService} from '../../../services/user/user';
import {QuestionService} from '../../../services/question/question';
import {LangCode, TranslateBatchItem, TranslationService,} from '../../../services/translation/translation';
import {TableModule} from 'primeng/table';


type QuestionListItem = { id: number; title?: string } | any;


@Component({
  standalone: true,
  selector: 'app-subject-edit',
  imports: [
    ReactiveFormsModule,
    Editor,
    InputTextModule,
    Button,
    TabsModule,
    PickListModule,
    TableModule,
  ],
  templateUrl: './subject-edit.html',
  styleUrl: './subject-edit.scss',
})
export class SubjectEdit implements OnInit {
  id!: number;

  // UI state
  loading = signal(true);
  error = signal<string | null>(null);

  translating = signal(false);
  submitError = signal<string | null>(null);
  translateOverwrite = signal(false); // optionnel: toggle UI plus tard

  // domain + languages
  domainId = signal<number>(0);
  allowedLanguages = signal<LanguageReadDto[]>([]);
  activeLang = signal<LangCode | undefined>(undefined);

  // questions
  questions = signal<QuestionListItem[]>([]);

  private fb = inject(FormBuilder);
  form = this.fb.group({
    translations: this.fb.group({}),
  });
  private route = inject(ActivatedRoute);
  private destroyRef = inject(DestroyRef);
  private subjectService = inject(SubjectService);
  private domainService = inject(DomainService);
  private userService = inject(UserService);
  // Normalisation safe de la langue UI courante -> LangCode
  currentLang = computed<LangCode>(() => {
    const v: unknown = (this.userService as any).currentLang;
    const s = typeof v === 'string' ? v : String(v ?? 'fr');
    return (['fr', 'en', 'nl', 'it', 'es'].includes(s) ? s : 'fr') as LangCode;
  });
  private translator = inject(TranslationService);
  private questionService = inject(QuestionService);

  ngOnInit(): void {
    this.id = Number(this.route.snapshot.paramMap.get('id'));
    this.load();
  }

  // ===== template helpers =====
  translationsGroup(): FormGroup {
    return this.form.get('translations') as FormGroup;
  }

  langGroup(code: string): FormGroup {
    return this.translationsGroup().get(code) as FormGroup;
  }

  tabCodes(): LangCode[] {
    return (this.allowedLanguages().map((l) => l.code) as unknown as LangCode[]);
  }

  onTabChange(value: string | number | undefined): void {
    if (value === undefined || value === null) return;
    const code = String(value) as LangCode;
    if (!this.tabCodes().includes(code)) return;
    this.activeLang.set(code);
  }

  // ===== actions =====
  save(): void {
    this.submitError.set(null);
    this.error.set(null);

    if (this.form.invalid) {
      this.form.markAllAsTouched();
      return;
    }

    const payload = this.buildPayload();
    this.loading.set(true);

    this.subjectService
      .update(this.id, payload)
      .pipe(
        takeUntilDestroyed(this.destroyRef),
        finalize(() => this.loading.set(false)),
      )
      .subscribe({
        next: () => this.goList(),
        error: (err) => {
          console.error('Erreur update subject', err);
          this.submitError.set('Erreur lors de la sauvegarde.');
        },
      });
  }

  goQuestionNew(): void {
    this.questionService.goNew();
  }

  goQuestionEdit(id: number): void {
    this.questionService.goEdit(id);
  }

  goQuestionDelete(id: number): void {
    this.questionService.goDelete(id);
  }

  goList(): void {
    this.subjectService.goList();
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

  // ===== loading =====
  private load(): void {
    this.loading.set(true);
    this.error.set(null);
    this.submitError.set(null);

    this.subjectService
      .detail(this.id)
      .pipe(
        takeUntilDestroyed(this.destroyRef),
        catchError((err) => {
          console.error('Erreur chargement subject', err);
          this.error.set('Impossible de charger le sujet.');
          return EMPTY;
        }),
        finalize(() => this.loading.set(false)),
      )
      .subscribe((s: SubjectDetailDto) => {
        this.domainId.set(s.domain);
        console.log(s);
        this.questions.set((s as SubjectDetailDto).questions ?? []);

        const domainId = s.domain ?? null;
        if (domainId) {
          this.loadDomainLanguages(domainId, s);
        } else {
          this.fallbackFromSubjectOnly(s);
        }
      });
  }

  private loadDomainLanguages(domainId: number, subject: SubjectDetailDto): void {
    this.loading.set(true);

    this.domainService
      .retrieve(domainId)
      .pipe(
        takeUntilDestroyed(this.destroyRef),
        catchError((err) => {
          console.error('Erreur chargement domain', err);
          this.fallbackFromSubjectOnly(subject);
          return EMPTY;
        }),
        finalize(() => this.loading.set(false)),
      )
      .subscribe((d: DomainReadDto) => {
        const activeLangs = (d.allowed_languages ?? []).filter((l) => l.active);
        this.allowedLanguages.set(activeLangs);

        const codes = activeLangs.map((l) => l.code as unknown as LangCode);

        // IMPORTANT: reset avant de recréer les controls
        this.resetTranslationsControls();
        this.ensureLanguageControls(codes);

        this.patchTranslationsFromDto(subject, codes);
        this.setInitialTab(codes);
      });
  }

  // ===== form helpers =====
  private resetTranslationsControls(): void {
    const tg = this.translationsGroup();
    Object.keys(tg.controls).forEach((key) => tg.removeControl(key));
  }

  private ensureLanguageControls(codes: LangCode[]): void {
    const tg = this.translationsGroup();

    for (const code of codes) {
      if (!tg.contains(code)) {
        tg.addControl(
          code,
          this.fb.group({
            name: new FormControl<string>('', {
              nonNullable: true,
              validators: [
                Validators.required,
                Validators.minLength(2),
                Validators.maxLength(120),
              ],
            }),
            description: new FormControl<string>('', {nonNullable: true}),
          }),
        );
      }
    }
  }

  private patchTranslationsFromDto(dto: SubjectDetailDto, codes: LangCode[]): void {
    const tr = (dto.translations ?? {}) as SubjectTranslationsWrite;

    const patch: SubjectTranslationsWrite = {};
    for (const code of codes) {
      patch[code] = {
        name: tr[code]?.name ?? '',
        description: tr[code]?.description ?? '',
      };
    }

    this.translationsGroup().patchValue(patch);
  }

  private getTranslationGroup(code: LangCode): SubjectLangGroup {
    const fg = this.translationsGroup().get(code) as SubjectLangGroup | null;
    if (!fg) throw new Error(`Missing form group for language: ${code}`);
    return fg;
  }

  private setInitialTab(codes: LangCode[]): void {
    const preferred = this.currentLang();
    const pick = codes.includes(preferred) ? preferred : codes[0];
    this.activeLang.set(pick);
  }

  private fallbackFromSubjectOnly(s: SubjectDetailDto): void {
    const tr = (s.translations ?? {}) as SubjectTranslationsWrite;
    const codes = Object.keys(tr).sort() as LangCode[];

    this.allowedLanguages.set(
      codes.map((code) => ({
        id: 0 as any,
        code,
        name: code,
        active: true,
      })),
    );

    this.resetTranslationsControls();
    this.ensureLanguageControls(codes);
    this.patchTranslationsFromDto(s, codes);
    this.setInitialTab(codes);

    this.loading.set(false);
  }

  private buildPayload(): SubjectWriteRequestDto {
    const domainId = this.domainId();
    const tg = this.translationsGroup();
    const codes = this.tabCodes();

    // Ne renvoyer que les langues du domain (onglets)
    const translations: Record<string, { name: string; description: string;}> = {};
    for (const code of codes) {
    const fg = tg.get(code) as SubjectLangGroup | null;
    if (!fg) continue;

    translations[code] = {
      name: fg.controls.name.value ?? '',
      description: fg.controls.description.value ?? '',
    };
  }

  return this.subjectService.buildWritePayload(domainId, translations);
  }

  private isEmptyHtml(html: string): boolean {
    const cleaned = (html ?? '')
      .replace(/<br\s*\/?>/gi, '')
      .replace(/&nbsp;/gi, ' ')
      .replace(/<[^>]+>/g, '')
      .trim();
    return cleaned.length === 0;
  }

  protected getQuestionTitle(q: QuestionListItem):string {
    const lang = String(this.activeLang()).toLowerCase();
    return q.title?.[lang]?.title ??`Question #${q.id}`;
  }
}
