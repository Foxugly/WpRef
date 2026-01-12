import { CommonModule } from '@angular/common';
import { Component, computed, inject, OnInit, signal } from '@angular/core';
import {
  FormControl,
  FormGroup,
  FormsModule,
  NonNullableFormBuilder,
  ReactiveFormsModule,
  Validators,
} from '@angular/forms';

import { Editor } from 'primeng/editor';
import { TabsModule } from 'primeng/tabs';
import { SelectModule } from 'primeng/select';
import { ButtonModule } from 'primeng/button';
import { InputTextModule } from 'primeng/inputtext';

import { DomainReadDto, LanguageEnumDto, SubjectWriteRequestDto } from '../../../api/generated';
import { DomainService } from '../../../services/domain/domain';
import { SubjectService } from '../../../services/subject/subject';
import { TranslationService } from '../../../services/translation/translation';
import {Card} from 'primeng/card';

type LangCode = `${LanguageEnumDto}`;

type SubjectLangForm = FormGroup<{
  name: FormControl<string>;
  description: FormControl<string>;
}>;

// Adapte si tu as déjà ce type exporté ailleurs
type TranslateBatchItem = { key: 'name' | 'description'; text: string; format: 'text' | 'html' };

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
    Card,
  ],
})
export class SubjectCreate implements OnInit {
  // UI state
  loading = signal(false);
  error = signal<string | null>(null);

  translating = signal(false);
  submitError = signal<string | null>(null);

  // Domain select (staff only)
  staffDomains = signal<DomainReadDto[]>([]);
  selectedDomainId = signal<number | null>(null);

  // Tabs = languages of selected domain
  domainLangs = signal<LangCode[]>([]);
  formsByLang = signal<Partial<Record<LangCode, SubjectLangForm>>>({});
  langs = computed(() => this.domainLangs());
  activeLang = signal<LangCode | null>(null);

  // Traduction: si true => écrase même si déjà rempli
  translateOverwrite = signal(false);

  private fb = inject(NonNullableFormBuilder);
  private domainService = inject(DomainService);
  private subjectService = inject(SubjectService);
  private translator = inject(TranslationService);

  ngOnInit(): void {
    this.fetchStaffDomains();
  }

  private fetchStaffDomains(): void {
    this.loading.set(true);
    this.error.set(null);

    this.domainService.list({ asStaff: true } as any).subscribe({
      next: (domains: DomainReadDto[]) => {
        this.staffDomains.set(domains);
        this.loading.set(false);
      },
      error: (err) => {
        console.error(err);
        this.error.set('Impossible de charger les domaines.');
        this.loading.set(false);
      },
    });
  }

  onDomainChange(value: number | DomainReadDto | null): void {
    const domainId = typeof value === 'number' ? value : value?.id ?? null;

    // reset UI immediately
    this.selectedDomainId.set(domainId);
    this.error.set(null);
    this.submitError.set(null);
    this.domainLangs.set([]);
    this.formsByLang.set({});
    this.activeLang.set(null);

    if (!domainId) return;

    this.loading.set(true);

    this.domainService.retrieve(domainId).subscribe({
      next: (domain: DomainReadDto) => {
        const langs = this.extractLangCodes(domain);
        this.domainLangs.set(langs);

        const map: Partial<Record<LangCode, SubjectLangForm>> = {};
        for (const lang of langs) {
          map[lang] = this.fb.group({
            name: this.fb.control('', {
              validators: [Validators.required, Validators.maxLength(120)],
            }),
            description: this.fb.control(''),
          });
        }

        this.formsByLang.set(map);
        this.activeLang.set(langs[0] ?? null);

        this.loading.set(false);
      },
      error: (err) => {
        console.error(err);
        this.error.set('Impossible de charger le domaine sélectionné.');
        this.loading.set(false);
      },
    });
  }

  onTabChange(lang: LangCode): void {
    this.activeLang.set(lang);
  }

  tabCodes(): LangCode[] {
    return this.domainLangs();
  }

  private getLangGroup(code: LangCode): SubjectLangForm {
    const fg = this.formsByLang()[code];
    if (!fg) throw new Error(`Missing form group for language: ${code}`);
    return fg;
  }

  private isEmptyHtml(html: string): boolean {
    // Convertit un HTML "vide" (<p><br></p>) en vide
    const cleaned = (html ?? '')
      .replace(/<br\s*\/?>/gi, '')
      .replace(/&nbsp;/gi, ' ')
      .replace(/<[^>]+>/g, '')
      .trim();
    return cleaned.length === 0;
  }

  /**
   * Traduire depuis une langue source vers toutes les autres (batch par cible)
   * - Ne remplit que si vide, sauf si translateOverwrite=true
   */
  async translateFrom(sourceLang: LangCode): Promise<void> {
    const codes = this.tabCodes();
    if (!codes.includes(sourceLang)) return;

    this.translating.set(true);
    this.submitError.set(null);

    try {
      const source = this.getLangGroup(sourceLang);
      const sourceName = source.controls.name.value ?? '';
      const sourceDesc = source.controls.description.value ?? '';

      const overwrite = this.translateOverwrite();

      for (const targetLang of codes) {
        if (targetLang === sourceLang) continue;

        const target = this.getLangGroup(targetLang);
        const nameCtrl = target.controls.name;
        const descCtrl = target.controls.description;

        const needName = overwrite || !(nameCtrl.value ?? '').trim();
        const needDesc = overwrite || this.isEmptyHtml(descCtrl.value ?? '');

        const items: TranslateBatchItem[] = [];
        if (needName) items.push({ key: 'name', text: sourceName, format: 'text' });
        if (needDesc) items.push({ key: 'description', text: sourceDesc, format: 'html' });

        if (!items.length) continue;

        // ✅ ta signature exacte
        const out: Record<string, string> = await this.translator.translateBatch(
          sourceLang,
          targetLang,
          items
        );

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

  isValid(): boolean {
    const domainId = this.selectedDomainId();
    if (!domainId) return false;

    const langs = this.domainLangs();
    if (langs.length === 0) return false;

    const forms = this.formsByLang();
    return langs.every((l) => forms[l]?.valid === true);
  }

  buildPayload(): SubjectWriteRequestDto {
    const domainId = this.selectedDomainId();
    const langs = this.domainLangs();
    const forms = this.formsByLang();

    const translations: SubjectWriteRequestDto['translations'] = {};

    for (const lang of langs) {
      const fg = forms[lang];
      if (!fg) continue;

      const v = fg.getRawValue();
      translations[lang] = {
        name: v.name,
        description: v.description,
      };
    }

    return {
      domain: domainId,
      translations,
    };
  }

  submit(): void {
    this.error.set(null);
    this.submitError.set(null);

    if (!this.isValid()) {
      this.error.set('Merci de remplir au minimum le champ "name" pour chaque langue.');
      return;
    }

    const payload: SubjectWriteRequestDto = this.buildPayload();
    this.loading.set(true);

    this.subjectService.create(payload).subscribe({
      next: () => {
        this.loading.set(false);
        this.subjectService.goList();
      },
      error: (err) => {
        console.error(err);
        this.submitError.set('Erreur lors de la création du sujet.');
        this.loading.set(false);
      },
    });
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

    return [LanguageEnumDto.Fr as LangCode];
  }
}
