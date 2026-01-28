import { Component, computed, DestroyRef, inject, OnInit, signal } from '@angular/core';
import { ActivatedRoute } from '@angular/router';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { finalize } from 'rxjs/operators';

import { Button } from 'primeng/button';
import { QuestionReadDto } from '../../../api/generated';
import { QuestionService, QuestionTranslationForm } from '../../../services/question/question';
import { selectTranslation } from '../../../shared/i18n/select-translation';
import { UserService } from '../../../services/user/user';
import {LangCode} from '../../../services/translation/translation';

@Component({
  standalone: true,
  selector: 'question-delete',
  imports: [Button],
  templateUrl: './question-delete.html',
  styleUrl: './question-delete.scss',
})
export class QuestionDelete implements OnInit {
  id!: number;

  loading = signal(false);
  submitError = signal<string | null>(null);

  question = signal<QuestionReadDto | null>(null);

  private route = inject(ActivatedRoute);
  private questionService = inject(QuestionService);
  private userService = inject(UserService);
  private destroyRef = inject(DestroyRef);

  currentLang = computed(() => {
    const v: any = this.userService.currentLang;
    return typeof v === 'string' ? v : String(v ?? 'fr');
  });

  ngOnInit(): void {
    this.id = Number(this.route.snapshot.paramMap.get('id'));
    this.loading.set(true);

    this.questionService
      .retrieve(this.id)
      .pipe(
        takeUntilDestroyed(this.destroyRef),
        finalize(() => this.loading.set(false)),
      )
      .subscribe({
        next: (q) => this.question.set(q),
        error: (err) => {
          console.error(err);
          this.submitError.set('Impossible de charger la question.');
        },
      });
  }

  getTitle(d: QuestionReadDto | null): string {
    if (!d) return '';
    const t = selectTranslation<QuestionTranslationForm>(
      d.translations as Record<string, QuestionTranslationForm>,
      this.currentLang() as LangCode,
    );
    return t?.title ?? '';
  }

  goBack(): void {
    this.questionService.goBack();
  }

  confirm(): void {
    this.submitError.set(null);
    this.loading.set(true);

    this.questionService
      .delete(this.id)
      .pipe(
        takeUntilDestroyed(this.destroyRef),
        finalize(() => this.loading.set(false)),
      )
      .subscribe({
        next: () => this.questionService.goList(),
        error: (err) => {
          console.error(err);
          this.submitError.set('Erreur lors de la suppression.');
        },
      });
  }
}
