import {Component, inject, OnInit, signal} from '@angular/core';
import {FormsModule} from '@angular/forms';
import { SubjectService, Subject } from '../../../services/subject/subject';
import {Button} from 'primeng/button';
import {InputTextModule} from 'primeng/inputtext';
import { PaginatorModule } from 'primeng/paginator';
import {TableModule} from 'primeng/table';

@Component({
  standalone: true,
  selector: 'app-subject-list',
  imports: [FormsModule, Button, InputTextModule, PaginatorModule, TableModule],
  templateUrl: './subject-list.html',
  styleUrl: './subject-list.scss'
})
export class SubjectList implements OnInit {
  private subjectService = inject(SubjectService);

  subjects = signal<Subject[]>([]);
  q = signal('');

  // 📌 Pagination
  first = 0;  // index de départ
  rows = 10;  // nombre de lignes par page

  ngOnInit() {
    this.load();
  }

  load() {
    this.subjectService
      .list({ search: this.q() || undefined })
      .subscribe({
        next: (subs: Subject[]) => {
          this.subjects.set(subs);
          this.first = 0;  // retour à la première page à chaque recherche
        },
        error: (err: unknown) => {
          console.error('Erreur lors du chargement des sujets', err);
          this.subjects.set([]);
        }
      });
  }

  onSearchChange(term: string) {
    this.q.set(term);
    this.load();
  }

  // Liste paginée pour la page courante
  get pagedSubjects(): Subject[] {
    const all = this.subjects() || [];
    return all.slice(this.first, this.first + this.rows);
  }

  // Handler appelé par p-paginator
  onPageChange(event: any) {
    this.first = event.first;
    this.rows = event.rows;
  }

  goNew() {
    this.subjectService.goNew();
  }

  goEdit(id: number) {
    this.subjectService.goEdit(id);
  }

  goDelete(id: number) {
    this.subjectService.goDelete(id);
  }
}
