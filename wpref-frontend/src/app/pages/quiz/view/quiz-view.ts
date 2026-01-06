import {Component, inject, OnInit, signal} from '@angular/core';
import {ActivatedRoute} from '@angular/router';
import {UserService} from '../../../services/user/user';
import {QuizService} from '../../../services/quiz/quiz';
import {Button} from 'primeng/button';
import {CardModule} from 'primeng/card';
import {DatePipe} from '@angular/common';
import {CreateQuizInputRequestDto, QuizDto} from '../../../api/generated';

@Component({
  selector: 'app-view',
  imports: [
    Button,
    CardModule,
    DatePipe,
  ],
  templateUrl: './quiz-view.html',
  styleUrl: './quiz-view.scss',
})
export class QuizView implements OnInit {
  id!: number;
  loading = signal(false);
  error = signal<string | null>(null);
  quizSession = signal<QuizDto | null>(null);
  private route = inject(ActivatedRoute);
  private quizService = inject(QuizService);
  private userService = inject(UserService);
  isAdmin = this.userService.isAdmin();

  ngOnInit(): void {
    this.id = Number(this.route.snapshot.paramMap.get('id'));
    if (!this.id || Number.isNaN(this.id)) {
      this.error.set('Identifiant de question invalide.');
      return;
    }
    this.loadQuizSession();
  }

  goBack(): void {
    this.quizService.goList()
  }

  goStart(): void {
    const payload: CreateQuizInputRequestDto = {quiz_template_id : this.id};
    this.quizService.goStart(this.id, payload);
  }

  goQuestion(): void {
    this.quizService.goQuestion(this.id);
  }

  private loadQuizSession(): void {
    this.loading.set(true);
    this.error.set(null);

    this.quizService.retrieveQuiz(this.id).subscribe({
      next: (q) => {
        this.quizSession.set(q);
        this.loading.set(false);
      },
      error: (err) => {
        console.error('Erreur chargement quizSession', err);
        this.error.set("Impossible de charger cette question.");
        this.loading.set(false);
      },
    });
  }
}
