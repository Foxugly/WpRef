import { Component, OnDestroy } from '@angular/core';
import { CommonModule } from '@angular/common';
import { MatMenuModule } from '@angular/material/menu';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { RouterLink, Router } from '@angular/router';
import { AuthService } from '../../services/auth';
import { MatButtonToggleChange, MatButtonToggleModule } from '@angular/material/button-toggle';
import { UserService } from '../../services/user';
import { LangCode } from '../../../environments/environment';
import { Subscription } from 'rxjs';

@Component({
  selector: 'app-topmenu',
  standalone: true,
  imports: [
    CommonModule,
    RouterLink,
    MatButtonModule,
    MatMenuModule,
    MatButtonToggleModule,
    MatIconModule
  ],
  templateUrl: './topmenu.html',
  styleUrl: './topmenu.scss'
})
export class TopmenuComponent implements OnDestroy {
  currentLang: LangCode = 'en';
  private sub?: Subscription;

  constructor(
    public auth: AuthService,
    private router: Router,
    private userService: UserService
  ) {
    // 1. S'abonner à la langue choisie dans l'application
    this.sub = this.userService.currentLang$.subscribe(lang => {
      this.currentLang = lang;
    });

     // 2. Charger /me et synchroniser (si connecté)
    this.userService.getMe().subscribe({
      // getMe() appelle déjà syncLanguageFromMe, donc currentLang sera mis à jour
      error: err => console.warn('Impossible de récupérer /me au topmenu', err),
    });
  }

  onLangChange(event: MatButtonToggleChange) {
    const lang = event.value as LangCode;

    // 1. Mettre à jour la langue frontend
    this.userService.setLocalLanguage(lang);

    // 2. Mettre à jour côté backend
    this.userService.updateMeLanguage(lang).subscribe({
      next: () => console.log('Langue mise à jour côté backend :', lang),
      error: err => console.error('Erreur maj langue', err)
    });
  }

  logout() {
    this.auth.logout();
    this.router.navigate(['/login']);
  }

  goPreferences() {
    this.router.navigate(['/preferences']);
  }

  ngOnDestroy() {
    this.sub?.unsubscribe();
  }

  goChangePassword() {
    this.router.navigate(['/change-password']);
  }
}
