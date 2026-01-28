import {Component, inject} from '@angular/core';

import {Subscription} from 'rxjs';
import {Router, RouterLink, RouterLinkActive} from '@angular/router';
import {MenubarModule} from 'primeng/menubar';
import {FormsModule} from '@angular/forms';
import {UserService} from '../../services/user/user';
import {LangSelectComponent} from '../lang-select/lang-select';
import {UserMenuComponent} from '../user-menu/user-menu';
import {SubjectService} from '../../services/subject/subject';
import {QuestionService} from '../../services/question/question';
import {QuizService} from '../../services/quiz/quiz';
import {SupportedLanguage} from '../../../environments/language';
import {DomainService} from '../../services/domain/domain';
import {environment} from '../../../environments/environment';
import {ROUTES} from '../../app.routes-paths';

declare global {
  interface Window {
    __APP__?: {
      name: string;
      version: string;
      author: string;
      year: string;
      logoSvg: string;
      logoIco: string;
      logoPng: string;
    };
  }
}

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
  ],
  templateUrl: './topmenu.html',
  styleUrl: './topmenu.scss'
})
export class TopmenuComponent {
  constructor(private router: Router) {
  }
  app = window.__APP__!;
  private subjectService = inject(SubjectService);
  private questionService = inject(QuestionService);
  private quizService = inject(QuizService);
  private userService = inject(UserService);
  private domainService = inject(DomainService);


  goQuizList(): void {
    this.quizService.goList();
  }

  goSubjectList(): void {
    this.subjectService.goList();
  }

  goDomainList(): void {
    this.domainService.goList();
  }

  goQuestionList(): void {
    this.questionService.goList();
  }

  goSubjectQuiz() {
    this.quizService.goSubject();
  }

  menuItems = [
    {
      label: environment.appName,
      command: () => this.goHome()
    },
    {
      label: 'Domains',
      icon: 'pi pi-folder',
      command: () => this.goDomainList()
    },
    {
      label: 'Subjects',
      icon: 'pi pi-folder',
      command: () => this.goSubjectList()
    },
    {
      label: 'Questions',
      icon: 'pi pi-question-circle',
      command: () => this.goQuestionList()
    },
    {
      label: 'Quiz',
      icon: 'pi pi-list-check',
      items: [
        {
          label: 'Quiz',
          icon: 'pi pi-list',
          command: () => this.goQuizList(),
        },
        {
          label: 'Quiz par sujets',
          icon: 'pi pi-pencil',
          command: () => this.goSubjectQuiz(),
        },
        {
          separator: true
        },
        {
          label: 'Blocks',
          icon: 'pi pi-server'
        },
      ]
    },
  ];
  currentLang: SupportedLanguage = this.userService.currentLang;
  private sub?: Subscription;

  onLangChange(lang: SupportedLanguage) {
    this.currentLang = lang;
    this.userService.setLang(lang);
    this.userService.updateMeLanguage(lang).subscribe(); // lang est déjà LanguageEnumDto
  }

  ngOnDestroy() {
    this.sub?.unsubscribe();
  }

  private goHome() {
    this.router.navigate(ROUTES.home());
  }
}
