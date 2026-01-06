import {Component, inject, OnInit, signal} from '@angular/core';

import {ActivatedRoute} from '@angular/router';
import {SubjectService} from '../../../services/subject/subject';
import {Button} from 'primeng/button';
import {SubjectReadDto} from '../../../api/generated';

@Component({
  standalone: true,
  selector: 'app-subject-delete',
  imports: [Button],
  templateUrl: './subject-delete.html',
  styleUrl: './subject-delete.scss'
})
export class SubjectDelete implements OnInit {
  private route = inject(ActivatedRoute);
  private subjectService = inject(SubjectService);

  id!: number;
  subject = signal<SubjectReadDto | null>(null);

  goBack(): void {
    this.subjectService.goBack();
  }

  goList(): void {
    this.subjectService.goList();
  }

  ngOnInit() {
    this.id = Number(this.route.snapshot.paramMap.get('id'));
    this.subjectService.retrieve(this.id).subscribe(s => this.subject.set(s));
  }

  confirm() {
    this.subjectService.delete(this.id).subscribe({
      next: () => this.goList()
    });
  }
}
