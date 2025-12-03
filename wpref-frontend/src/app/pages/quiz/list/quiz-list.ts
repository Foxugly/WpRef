import {Component, inject, OnInit, signal} from '@angular/core';
import {FormsModule} from '@angular/forms';
import {Button} from 'primeng/button';
import {InputTextModule} from 'primeng/inputtext';
import {CommonModule} from '@angular/common';
import {PaginatorModule} from 'primeng/paginator';
import {QuizSession, QuizService} from '../../../services/quiz/quiz';
import {Question} from '../../../services/question/question';

@Component({
  selector: 'app-list',
  imports: [CommonModule, FormsModule, Button, InputTextModule, PaginatorModule],
  templateUrl: './quiz-list.html',
  styleUrl: './quiz-list.scss',
})
export class QuizList implements OnInit {
  quizz = signal<QuizSession[]>([]);
  q = signal('');
  // 👉 ÉTAT DE PAGINATION
  first = 0;           // index de départ (offset)
  rows = 10;           // nb de lignes par page
  private quizService = inject(QuizService);

  ngOnInit() {
    this.load();
  }

  load() {
    this.quizService
      .listQuizSession({search: this.q() || undefined})
      .subscribe({
        next: (quizz: QuizSession[]) => {
          console.log(quizz)
          this.quizz.set(quizz);
          this.first = 0;
        },
        error: (err: unknown) => {
          console.error('Erreur lors du chargement des quizz', err);
          this.quizz.set([]);
        }
      });
  }

  goNew():void{
    this.quizService.goNew();
  }
  goView(id:number):void{
    this.quizService.goList();
  }

  get pagedQuiz(): QuizSession[] {
    const all = this.quizz() || [];
    return all.slice(this.first, this.first + this.rows);
  }

  onPageChange(event: any) {
    this.first = event.first;   // index de départ
    this.rows = event.rows;     // nb d’items par page
  }
}
