import { Component, OnInit, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormBuilder, Validators, ReactiveFormsModule } from '@angular/forms';
import { ActivatedRoute, Router, RouterLink } from '@angular/router';
import { SubjectService, Subject } from '../../../services/subject/subject';

@Component({
  standalone: true,
  selector: 'app-subject-edit',
  imports: [CommonModule, RouterLink, ReactiveFormsModule],
  templateUrl: './subject-edit.html',
  styleUrl: './subject-edit.scss'
})
export class SubjectEdit implements OnInit {
  private fb = inject(FormBuilder);
  private route = inject(ActivatedRoute);
  private router = inject(Router);
  private subjectService = inject(SubjectService);

  id!: number;
  form = this.fb.nonNullable.group({
    name: ['', [Validators.required, Validators.minLength(2)]],
    description: ['']
  });

  ngOnInit() {
    this.id = Number(this.route.snapshot.paramMap.get('id'));
    this.subjectService.get(this.id).subscribe((s: Subject) => {
      this.form.patchValue({ name: s.name, description: s.description || '' });
    });
  }

  save() {
    if (this.form.invalid) { this.form.markAllAsTouched(); return; }
    this.subjectService.update(this.id, this.form.value).subscribe({
      next: () => this.router.navigate(['/subject/list'])
    });
  }
}
