import { Component, OnInit, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormBuilder, Validators, ReactiveFormsModule } from '@angular/forms';
import { ActivatedRoute, Router } from '@angular/router';
import { Api, Subject } from '../../../../services/api';

@Component({
  standalone: true,
  selector: 'app-subject-edit',
  imports: [CommonModule, ReactiveFormsModule],
  templateUrl: './subject-edit.html',
  styleUrl: './subject-edit.scss'
})
export class SubjectEdit implements OnInit {
  private fb = inject(FormBuilder);
  private api = inject(Api);
  private route = inject(ActivatedRoute);
  private router = inject(Router);

  id!: number;
  form = this.fb.nonNullable.group({
    name: ['', [Validators.required, Validators.minLength(2)]],
    description: ['']
  });

  ngOnInit() {
    this.id = Number(this.route.snapshot.paramMap.get('id'));
    this.api.getSubject(this.id).subscribe((s: Subject) => {
      this.form.patchValue({ name: s.name, description: s.description || '' });
    });
  }

  save() {
    if (this.form.invalid) { this.form.markAllAsTouched(); return; }
    this.api.updateSubject(this.id, this.form.value).subscribe({
      next: () => this.router.navigate(['/subject'])
    });
  }
}
