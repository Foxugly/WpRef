import {Component, computed, inject, OnInit, signal} from '@angular/core';

import {ActivatedRoute} from '@angular/router';
import {SubjectService, SubjectTranslationDto} from '../../../services/subject/subject';
import {Button} from 'primeng/button';
import {DomainReadDto, SubjectReadDto} from '../../../api/generated';
import {selectTranslation} from '../../../shared/i18n/select-translation';
import {DomainTranslationDto} from '../../../services/domain/domain';
import {UserService} from '../../../services/user/user';

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
  private userService: UserService = inject(UserService);
  id!: number;
  subject = signal<SubjectReadDto | null>(null);
  currentLang = computed(() => this.userService.currentLang);


  getName(d: SubjectReadDto | null): string {
    if (d) {
      const t = selectTranslation<SubjectTranslationDto>(
        d.translations as unknown as Record<string, SubjectTranslationDto>,
        this.currentLang(),
      );
      return t?.name ?? '';
    }
    else {
      return "DOMAIN NAME ERROR";
    }
  }

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
