import { Component, OnInit, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ActivatedRoute, Router, RouterLink } from '@angular/router';
import { SubjectService, Subject } from '../../../services/subject/subject';

@Component({
  standalone: true,
  selector: 'app-subject-delete',
  imports: [CommonModule, RouterLink],
  templateUrl: './subject-delete.html',
  styleUrl: './subject-delete.scss'
})
export class SubjectDelete implements OnInit {
  private route = inject(ActivatedRoute);
  private router = inject(Router);
  private subjectService = inject(SubjectService);

  id!: number;
  subject = signal<Subject | null>(null);

  ngOnInit() {
    this.id = Number(this.route.snapshot.paramMap.get('id'));
    this.subjectService.get(this.id).subscribe(s => this.subject.set(s));
  }

  confirm() {
    this.subjectService.delete(this.id).subscribe({
      next: () => this.router.navigate(['/subject/list'])
    });
  }
}
