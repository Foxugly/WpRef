import {Component, inject, OnInit, signal} from '@angular/core';
import {CommonModule} from '@angular/common';
import {Router, RouterLink} from '@angular/router';
import {Api, Subject} from '../../../../services/api';
import {FormControl, FormsModule} from '@angular/forms';

@Component({
  standalone: true,
  selector: 'app-subject-list',
  imports: [CommonModule, RouterLink, FormsModule],
  templateUrl: './subject-list.html',
  styleUrl: './subject-list.scss'
})
export class SubjectList implements OnInit {
  private api = inject(Api);
  private router = inject(Router);
  subjects = signal<Subject[]>([]);
  q = signal('');

  ngOnInit() {
    this.load();
  }

  load() {
    this.api.listSubject({search: this.q() || undefined}).subscribe(subs => this.subjects.set(subs));
  }

  goNew() {
    this.router.navigate(['/subject/add']);
  }

  goEdit(id: number) {
    this.router.navigate(['/subject', id, 'edit']);
  }

  goDelete(id: number) {
    this.router.navigate(['/subject', id, 'delete']);
  }
}
