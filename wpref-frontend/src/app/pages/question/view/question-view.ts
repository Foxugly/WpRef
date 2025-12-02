// src/app/pages/question/detail/question-detail.ts
import {Component, inject, OnInit, signal, effect} from '@angular/core';
import {CommonModule} from '@angular/common';
import {ActivatedRoute, Router} from '@angular/router';
import {Question, QuestionService,} from '../../../services/question/question';
import {QuizQuestionComponent} from '../../../components/quiz-question/quiz-question';
import {ButtonModule} from 'primeng/button';
import {ToggleButtonModule} from 'primeng/togglebutton';
import { FormsModule } from '@angular/forms';
@Component({
  standalone: true,
  selector: 'app-question-view',
  templateUrl: './question-view.html',
  styleUrl: './question-view.scss',
  imports: [CommonModule, QuizQuestionComponent, ButtonModule, ToggleButtonModule, FormsModule],
})
export class QuestionView implements OnInit {
  id!: number;
  loading = signal(false);
  error = signal<string | null>(null);
  question = signal<Question | null>(null);
  /** Flag pour dire au composant enfant d'afficher les bonnes réponses en vert */
  showCorrect: boolean = false;
  /** À adapter à ton système d’authentification réel */
  isAdmin = false; // TODO: remplace par un vrai check de rôle (userService, token, etc.)
  private route = inject(ActivatedRoute);
  private router = inject(Router);
  private questionService = inject(QuestionService);

  ngOnInit(): void {
    this.id = Number(this.route.snapshot.paramMap.get('id'));
    if (!this.id || Number.isNaN(this.id)) {
      this.error.set('Identifiant de question invalide.');
      return;
    }
    this.loadQuestion();
  }

  goBack(): void {
    this.router.navigate(['/question/list']);
  }

  goEdit(id: number) {
    this.router.navigate(['/question', id, 'edit']);
  }

  /** true si l'utilisateur PEUT voir les réponses (admin ou mode practice) */
  canRevealCorrect(): boolean {
    const q = this.question();
    if (!q) return false;
    return this.isAdmin || q.is_mode_practice;
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

}
