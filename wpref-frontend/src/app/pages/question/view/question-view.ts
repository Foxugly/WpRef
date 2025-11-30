// src/app/pages/question/detail/question-detail.ts
import { Component, OnInit, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ActivatedRoute, Router, RouterLink } from '@angular/router';

import {Question, QuestionService,} from '../../../services/question/question';
import { QuizQuestionComponent } from '../../../components/quiz-question/quiz-question';
import { ButtonModule } from 'primeng/button';

@Component({
  standalone: true,
  selector: 'app-question-view',
  templateUrl: './question-view.html',
  styleUrl: './question-view.scss',
  imports: [CommonModule, QuizQuestionComponent, ButtonModule],
})
export class QuestionView implements OnInit {
  private route = inject(ActivatedRoute);
  private router = inject(Router);
  private questionService = inject(QuestionService);

  id!: number;

  loading = signal(false);
  error = signal<string | null>(null);
  question = signal<Question | null>(null);

  ngOnInit(): void {
    this.id = Number(this.route.snapshot.paramMap.get('id'));
    if (!this.id || Number.isNaN(this.id)) {
      this.error.set('Identifiant de question invalide.');
      return;
    }
    this.loadQuestion();
  }

  private loadQuestion(): void {
    this.loading.set(true);
    this.error.set(null);

    this.questionService.retrieve(this.id).subscribe({
      next: (q) => {
        this.question.set(q);
        this.loading.set(false);
      },
      error: (err) => {
        console.error('Erreur chargement question', err);
        this.error.set("Impossible de charger cette question.");
        this.loading.set(false);
      },
    });
  }

  goBack(): void {
    this.router.navigate(['/question/list']);
  }

  goEdit(id: number) {
    this.router.navigate(['/question', id, 'edit']);
  }
}
