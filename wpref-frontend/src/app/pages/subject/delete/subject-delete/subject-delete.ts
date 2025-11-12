import { Component, OnInit, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ActivatedRoute, Router, RouterLink } from '@angular/router';
import { Api, Subject } from '../../../../services/api';

@Component({
  standalone: true,
  selector: 'app-subject-delete',
  imports: [CommonModule, RouterLink],
  templateUrl: './subject-delete.html',
  styleUrl: './subject-delete.scss'
})
export class SubjectDelete implements OnInit {
  private api = inject(Api);
  private route = inject(ActivatedRoute);
  private router = inject(Router);

  id!: number;
  subject = signal<Subject | null>(null);

  ngOnInit() {
    this.id = Number(this.route.snapshot.paramMap.get('id'));
    this.api.getSubject(this.id).subscribe(s => this.subject.set(s));
  }

  confirm() {
    this.api.deleteSubject(this.id).subscribe({
      next: () => this.router.navigate(['/subject'])
    });
  }
}
