import {Component, inject, OnInit, signal} from '@angular/core';

import {FormControl, FormsModule} from '@angular/forms';
import {Router, RouterLink} from '@angular/router';
import { QuestionService, Question } from '../../../services/question/question';
import {InputTextModule} from 'primeng/inputtext';

@Component({
  standalone: true,
  selector: 'app-question-list',
  imports: [RouterLink, FormsModule, InputTextModule],
  templateUrl: './question-list.html',
  styleUrl: './question-list.scss'
})
export class QuestionList implements OnInit {
private questionService = inject(QuestionService);
  private router = inject(Router);

  questions = signal<Question[]>([]);
  q = signal('');

  ngOnInit() {
    this.load();
  }

  load() {
    this.questionService
      .list({ search: this.q() || undefined })
      .subscribe({
        next: (subs: Question[]) => this.questions.set(subs),
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

  goNew() {
    this.router.navigate(['/question']);
  }

  goEdit(id: number) {
    this.router.navigate(['/question', id, 'edit']);
  }

  goDelete(id: number) {
    this.router.navigate(['/question', id, 'delete']);
  }
}
