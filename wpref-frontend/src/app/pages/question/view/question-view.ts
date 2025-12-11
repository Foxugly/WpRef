// src/app/pages/question/detail/question-detail.ts
import {Component, inject, OnInit, signal} from '@angular/core';
import {CommonModule} from '@angular/common';
import {ActivatedRoute} from '@angular/router';
import {Question, QuestionService,} from '../../../services/question/question';
import {QuizQuestionComponent} from '../../../components/quiz-question/quiz-question';
import {ButtonModule} from 'primeng/button';
import {ToggleButtonModule} from 'primeng/togglebutton';
import {FormsModule} from '@angular/forms';
import {UserService} from '../../../services/user/user';
import {QuizNavItem} from '../../../components/quiz-nav/quiz-nav';

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
  quizNavItem = signal<QuizNavItem | null>(null);
  /** Flag pour dire au composant enfant d'afficher les bonnes réponses en vert */
  showCorrect: boolean = false;
  /** À adapter à ton système d’authentification réel */

  private route = inject(ActivatedRoute);
  private questionService = inject(QuestionService);
  private userService = inject(UserService);
  isAdmin = this.userService.isAdmin();

  ngOnInit(): void {
    this.id = Number(this.route.snapshot.paramMap.get('id'));
    if (!this.id || Number.isNaN(this.id)) {
      this.error.set('Identifiant de question invalide.');
      return;
    }
    this.loadQuestion();
  }

  goBack(): void {
    this.questionService.goBack()
  }

  goEdit(id: number) {
    this.questionService.goEdit(id);
  }

  /** true si l'utilisateur PEUT voir les réponses (admin ou mode practice) */
  canRevealCorrect(): boolean {
    const q = this.quizNavItem();
    if (!q) return false;
    return this.isAdmin || q.question.is_mode_practice;
  }

  private loadQuestion(): void {
    this.loading.set(true);
    this.error.set(null);

    this.questionService.retrieve(this.id).subscribe({
      next: (q) => {
        const navItem: QuizNavItem = {
          index: 1,           // ou ce que tu veux
          id: q.id,
          answered: false,
          flagged: false,
          question: q,
        };

        this.quizNavItem.set(navItem);
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
