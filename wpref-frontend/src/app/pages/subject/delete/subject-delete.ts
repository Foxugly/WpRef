import { Component, OnInit, inject, signal } from '@angular/core';

import { ActivatedRoute} from '@angular/router';
import { SubjectService, Subject } from '../../../services/subject/subject';
import {Button} from 'primeng/button';

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
  subject = signal<Subject | null>(null);

  goBack():void{
    this.subjectService.goBack();
  }

  goList():void{
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
