import { Component, OnDestroy } from '@angular/core';

import { Subscription } from 'rxjs';
import { Router, RouterLink, RouterLinkActive } from '@angular/router';
import { MenubarModule } from 'primeng/menubar';
import { FormsModule } from '@angular/forms'; // <-- IMPORTANT pour [(ngModel)]

import { AuthService } from '../../services/auth/auth';
import { UserService } from '../../services/user/user';
import { LangCode } from '../../../environments/environment';
import { LangSelectComponent } from '../lang-select/lang-select';
import { UserMenuComponent } from '../user-menu/user-menu';
import {QuizMenuComponent} from '../quiz-menu/quiz-menu';

@Component({
  selector: 'app-topmenu',
  standalone: true,
  imports: [
    FormsModule,
    RouterLink,
    RouterLinkActive,
    MenubarModule,
    LangSelectComponent,
    UserMenuComponent,
    QuizMenuComponent,
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
  ) {}

  onLangChange(lang: LangCode) {
    this.currentLang = lang;
    this.userService.setLocalLanguage(lang);
    this.userService.updateMeLanguage(lang).subscribe();
  }

  ngOnDestroy() {
    this.sub?.unsubscribe();
  }
}
