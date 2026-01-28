import {Component, computed, inject, OnInit, signal} from '@angular/core';
import {Button} from 'primeng/button';
import {ActivatedRoute} from '@angular/router';
import {DomainService, DomainTranslationDto} from '../../../services/domain/domain';
import {DomainReadDto, SubjectReadDto} from '../../../api/generated';
import {selectTranslation} from '../../../shared/i18n/select-translation';
import {UserService} from '../../../services/user/user';

@Component({
  selector: 'app-domain-delete',
  imports: [
    Button
  ],
  templateUrl: './domain-delete.html',
  styleUrl: './domain-delete.scss',
})
export class DomainDelete implements OnInit {
  private route = inject(ActivatedRoute);
  private domainService = inject(DomainService);
  private userService:UserService = inject(UserService);
  id!: number;
  domain = signal<DomainReadDto | null>(null);
  currentLang = computed(() => this.userService.currentLang);

  getName(d: DomainReadDto | null): string {
    if (d) {
      const t = selectTranslation<DomainTranslationDto>(
        d.translations as unknown as Record<string, DomainTranslationDto>,
        this.currentLang(),
      );
      return t?.name ?? '';
    }
    else {
      return "DOMAIN NAME ERROR";
    }
  }

  goBack(): void {
    this.domainService.goBack();
  }

  goList(): void {
    this.domainService.goList();
  }

  ngOnInit() {
    this.id = Number(this.route.snapshot.paramMap.get('id'));
    this.domainService.retrieve(this.id).subscribe(s => this.domain.set(s));
  }

  confirm() {
    this.domainService.delete(this.id).subscribe({
      next: () => this.goList()
    });
  }
}
