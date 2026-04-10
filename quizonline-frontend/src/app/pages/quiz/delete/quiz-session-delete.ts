import {Component, inject, OnInit, signal} from '@angular/core';
import {ActivatedRoute, Router} from '@angular/router';
import {ButtonModule} from 'primeng/button';
import {QuizDto} from '../../../api/generated';
import {ROUTES} from '../../../app.routes-paths';
import {QuizService} from '../../../services/quiz/quiz';

@Component({
  standalone: true,
  selector: 'app-quiz-session-delete',
  imports: [ButtonModule],
  templateUrl: './quiz-session-delete.html',
  styleUrl: './quiz-session-delete.scss',
})
export class QuizSessionDeletePage implements OnInit {
  private readonly route = inject(ActivatedRoute);
  private readonly router = inject(Router);
  private readonly quizService = inject(QuizService);

  readonly quiz = signal<QuizDto | null>(null);
  readonly error = signal<string | null>(null);
  readonly loading = signal(false);

  private quizId = 0;
  private templateId: number | null = null;

  ngOnInit(): void {
    const rawQuizId = this.route.snapshot.paramMap.get('quizId');
    const rawTemplateId = this.route.snapshot.paramMap.get('templateId');
    const quizId = Number(rawQuizId);
    const templateId = rawTemplateId ? Number(rawTemplateId) : null;

    if (!Number.isFinite(quizId)) {
      this.error.set('Identifiant de quiz invalide.');
      return;
    }

    this.quizId = quizId;
    this.templateId = Number.isFinite(templateId) ? templateId : null;

    this.quizService.retrieveQuiz(quizId).subscribe({
      next: (quiz) => this.quiz.set(quiz),
      error: (error) => {
        console.error(error);
        this.error.set('Impossible de charger le quiz.');
      },
    });
  }

  goBack(): void {
    if (this.templateId != null) {
      void this.router.navigate(ROUTES.quiz.templateResults(this.templateId));
      return;
    }
    void this.router.navigate(ROUTES.quiz.list());
  }

  confirm(): void {
    this.error.set(null);
    this.loading.set(true);

    this.quizService.deleteQuiz(this.quizId).subscribe({
      next: () => this.goBack(),
      error: (error) => {
        console.error(error);
        this.loading.set(false);
        this.error.set('Suppression impossible.');
      },
    });
  }
}
