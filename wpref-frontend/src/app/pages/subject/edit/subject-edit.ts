import {Component, computed, inject, OnInit, signal} from '@angular/core';
import {ActivatedRoute} from '@angular/router';
import {FormBuilder, FormControl, FormGroup, ReactiveFormsModule, Validators,} from '@angular/forms';

import {Editor} from 'primeng/editor';
import {InputTextModule} from 'primeng/inputtext';
import {Button} from 'primeng/button';
import {TabsModule} from 'primeng/tabs';
import { PickListModule } from 'primeng/picklist';
import {DomainReadDto, LanguageReadDto, SubjectDetailDto, SubjectWriteRequestDto,} from '../../../api/generated';

import {SubjectService} from '../../../services/subject/subject';
import {DomainService} from '../../../services/domain/domain';
import {UserService} from '../../../services/user/user';
import {QuestionService} from '../../../services/question/question';

type SubjectTr = { name?: string; description?: string };
type SubjectTranslations = Record<string, SubjectTr>;

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
  ],
  templateUrl: './subject-edit.html',
  styleUrl: './subject-edit.scss',
})
export class SubjectEdit implements OnInit {
  id!: number;
  // UI state
  loading = signal<boolean>(true);
  activeTabIndex = signal<number>(0);
  allowedLanguages = signal<LanguageReadDto[]>([]);
  langCodes = computed(() => this.allowedLanguages().map(l => l.code));
  protected questions: [] | undefined;
  private fb: FormBuilder = inject(FormBuilder);
  form = this.fb.group({
    translations: this.fb.group({}),
  });
  private route: ActivatedRoute = inject(ActivatedRoute);
  private subjectService: SubjectService = inject(SubjectService);
  private domainService: DomainService = inject(DomainService);
  private userService: UserService = inject(UserService);
  currentLang = computed(() => this.userService.currentLang);
  private questionService: QuestionService = inject(QuestionService);

  ngOnInit(): void {
    this.id = Number(this.route.snapshot.paramMap.get('id'));

    this.subjectService.detail(this.id).subscribe({
      next: (s: SubjectDetailDto) => {
        const domainId = s.domain ?? null;
        const questions = s.questions;

        // 1) Charger les langues autorisées du domain
        if (domainId) {
          this.domainService.retrieve(domainId).subscribe({
            next: (d: DomainReadDto) => {
              const activeLangs = (d.allowed_languages ?? []).filter(l => l.active);
              this.allowedLanguages.set(activeLangs);

              // 2) Construire les controls selon allowed_languages
              this.ensureLanguageControls(activeLangs.map(l => l.code));

              // 3) Remplir depuis s.translations
              this.patchTranslationsFromDto(s);

              // 4) Sélection onglet sur langue courante si possible
              this.setInitialTab();

              this.loading.set(false);
            },
            error: (err) => {
              console.error('Erreur chargement domain', err);
              // fallback : on utilise les langues présentes dans le Subject
              this.fallbackFromSubjectOnly(s);
            },
          });
        } else {
          // Pas de domain -> fallback sur les langues présentes dans le Subject
          this.fallbackFromSubjectOnly(s);
        }
      },
      error: (err) => {
        console.error('Erreur chargement subject', err);
        this.loading.set(false);
      },
    });
  }

  // Helper template

  langGroup(code: string): FormGroup {
    return this.translationsGroup().get(code) as FormGroup;
  }

  save(): void {
    if (this.form.invalid) {
      this.form.markAllAsTouched();
      return;
    }

    const payload: SubjectWriteRequestDto = {translations: this.translationsGroup().getRawValue(),} as any;
   // TODO Bug ici
    this.subjectService.update(this.id, payload).subscribe({
      next: () => this.goList(),
      error: (err) => console.error('Erreur update subject', err),
    });
  }

  goQuestionNew(): void {
    this.questionService.goNew();
  }

  goQuestionEdit(id: number) {
    this.questionService.goEdit(id);
  }

  goQuestionDelete(id: number) {
    this.questionService.goDelete(id);
  }

  goBack(): void {
    this.subjectService.goBack();
  }

  goList(): void {
    this.subjectService.goList();
  }

  private translationsGroup(): FormGroup {
    return this.form.get('translations') as FormGroup;
  }

  private ensureLanguageControls(codes: string[]): void {
    const tg = this.translationsGroup();

    for (const code of codes) {
      if (!tg.contains(code)) {
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
  }

  private patchTranslationsFromDto(dto: SubjectDetailDto): void {
    const tr = (dto.translations ?? {}) as SubjectTranslations;

    // on patch seulement les langues présentes dans le form (allowed_languages)
    const codes = Object.keys(this.translationsGroup().controls);

    const patch: Record<string, { name: string; description: string }> = {};
    for (const code of codes) {
      patch[code] = {
        name: tr[code]?.name ?? '',
        description: tr[code]?.description ?? '',
      };
    }
    this.translationsGroup().patchValue(patch);
  }

  private setInitialTab(): void {
    const codes = this.langCodes();
    const idx = codes.indexOf(this.currentLang());
    this.activeTabIndex.set(idx >= 0 ? idx : 0);
  }

  private fallbackFromSubjectOnly(s: SubjectDetailDto): void {
    const tr = (s.translations ?? {}) as SubjectTranslations;
    const codes = Object.keys(tr).sort();

    this.allowedLanguages.set(
      codes.map((code) => ({
        id: 0 as any, // on n’a pas l’ID, c’est un fallback UI
        code,
        name: code,
        active: true,
      })),
    );

    this.ensureLanguageControls(codes);
    this.patchTranslationsFromDto(s);
    this.setInitialTab();

    this.loading.set(false);
  }
}
