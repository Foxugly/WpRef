import {Component, inject, OnInit, signal} from '@angular/core';
import {CommonModule} from '@angular/common';
import {Router, RouterLink} from '@angular/router';
import { SubjectService, Subject } from '../../../services/subject/subject';
import {FormControl, FormsModule} from '@angular/forms';

@Component({
  standalone: true,
  selector: 'app-subject-list',
  imports: [CommonModule, RouterLink, FormsModule],
  templateUrl: './subject-list.html',
  styleUrl: './subject-list.scss'
})
export class SubjectList implements OnInit {
  private subjectService = inject(SubjectService);
  private router = inject(Router);

  subjects = signal<Subject[]>([]);
  q = signal('');

  ngOnInit() {
    this.load();
  }

  load() {
    this.subjectService
      .listSubject({ search: this.q() || undefined })
      .subscribe({
        next: (subs) => this.subjects.set(subs),
        error: (err) => {
          console.error('Erreur lors du chargement des sujets', err);
          this.subjects.set([]);
        }
      });
  }

  onSearchChange(term: string) {
    this.q.set(term);
    this.load();
  }

  goNew() {
    this.router.navigate(['/subject']);
  }

  goEdit(id: number) {
    this.router.navigate(['/subject', id, 'edit']);
  }

  goDelete(id: number) {
    this.router.navigate(['/subject', id, 'delete']);
  }
}
