import {Component, inject, OnInit, signal} from '@angular/core';
import {FormsModule} from '@angular/forms';
import {Router} from '@angular/router';
import {Question, QuestionService} from '../../../services/question/question';
import {Button} from 'primeng/button';
import {InputTextModule} from 'primeng/inputtext';
import {CommonModule} from '@angular/common';
import {PaginatorModule} from 'primeng/paginator';

@Component({
  standalone: true,
  selector: 'app-question-list',
  imports: [CommonModule, FormsModule, Button, InputTextModule, PaginatorModule],
  templateUrl: './question-list.html',
  styleUrl: './question-list.scss'
})
export class QuestionList implements OnInit {
  questions = signal<Question[]>([]);
  q = signal('');
  // 👉 ÉTAT DE PAGINATION
  first = 0;           // index de départ (offset)
  rows = 10;           // nb de lignes par page
  private questionService = inject(QuestionService);
  private router = inject(Router);

  ngOnInit() {
    this.load();
  }

  load() {
    this.questionService
      .list({search: this.q() || undefined})
      .subscribe({
        next: (subs: Question[]) => {
          this.questions.set(subs);
          this.first = 0;           // 👈 on revient à la première page à chaque recherche
        },
        error: (err: unknown) => {
          console.error('Erreur lors du chargement des questions', err);
          this.questions.set([]);
        }
      });
  }

  onSearchChange(term: string) {
    this.q.set(term);
    this.load();
  }

   // 👉 QUESTIONS POUR LA PAGE COURANTE
  get pagedQuestions(): Question[] {
    const all = this.questions() || [];
    return all.slice(this.first, this.first + this.rows);
  }

  // 👉 GESTION DU CHANGEMENT DE PAGE DU PAGINATOR
  onPageChange(event: any) {
    this.first = event.first;   // index de départ
    this.rows = event.rows;     // nb d’items par page
  }

  goNew() {
    this.router.navigate(['/question/add']);
  }

  goView(id: number) {
    this.router.navigate(['/question', id, 'view']);
  }

  goEdit(id: number) {
    this.router.navigate(['/question', id, 'edit']);
  }

  goDelete(id: number) {
    this.router.navigate(['/question', id, 'delete']);
  }

  goSubject(id: number) {
    this.router.navigate(['/subject', id, 'edit']);
  }
}
