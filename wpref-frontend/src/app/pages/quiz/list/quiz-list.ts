import {Component, inject, OnInit, signal} from '@angular/core';
import {FormsModule} from '@angular/forms';
import {ButtonModule} from 'primeng/button';
import {InputTextModule} from 'primeng/inputtext';
import {CommonModule} from '@angular/common';
import {PaginatorModule} from 'primeng/paginator';
import {QuizService, QuizSession} from '../../../services/quiz/quiz';
import {DialogModule} from 'primeng/dialog';
import {QuizSubjectForm} from '../subject-form/subject-form'
import {TableModule} from 'primeng/table';

@Component({
  selector: 'app-quiz-list',
  imports: [CommonModule, DialogModule, FormsModule, ButtonModule, InputTextModule, TableModule, PaginatorModule, QuizSubjectForm],
  templateUrl: './quiz-list.html',
  styleUrl: './quiz-list.scss',
})
export class QuizList implements OnInit {
  quizz = signal<QuizSession[]>([]);
  q = signal('');

  first = 0;           // index de départ (offset)
  rows = 10;           // nb de lignes par page
  // état dialog
  visible = false;

  saving = signal(false);
  success = signal<string | null>(null);
  maxQuestions = signal<number | null>(null);

  private quizService = inject(QuizService);

  get pagedQuiz(): QuizSession[] {
    const all = this.quizz() || [];
    return all.slice(this.first, this.first + this.rows);
  }

  ngOnInit(): void {
    this.load();
  }

  load(): void {
    this.quizService
      .listQuizSession({search: this.q() || undefined})
      .subscribe({
        next: (quizz: QuizSession[]) => {
          this.quizz.set(quizz);
          this.first = 0;
        },
        error: (err: unknown) => {
          console.error('Erreur lors du chargement des quizz', err);
          this.quizz.set([]);
        }
      });
  }

  closeDialog(): void {
    this.visible = false;
  }

  onGenerate(payload: any): void {
    this.saving.set(true);
    this.success.set(null);

    this.quizService.generateQuizSession(payload).subscribe({
      next: (): void => {
        this.saving.set(false);
        this.success.set('Quiz généré avec succès.');
        this.closeDialog();
        this.load();
      },
      error: (err) => {
        console.error('Erreur génération quiz', err);
        this.saving.set(false);
      },
    });
  }

  onSubjectsChange(ids: number[]): void {
    this.quizService.getQuestionCountBySubjects(ids).subscribe({
      next: (data): void => {
        this.maxQuestions.set(data.count);
      },
      error: (err): void => console.error('Erreur getQuestionCountBySubjects', err),
    });
  }

  goNew(): void {
    this.success.set(null);
    this.visible = true;
  }

  goList(): void {
    this.quizService.goList();
  }

  goView(id: number): void {
    this.quizService.goView(id);
  }


  onPageChange(event: any): void {
    this.first = event.first;   // index de départ
    this.rows = event.rows;     // nb d’items par page
  }
}
