import {Component, inject} from '@angular/core';

import {Subscription} from 'rxjs';
import {Router, RouterLink, RouterLinkActive} from '@angular/router';
import {MenubarModule} from 'primeng/menubar';
import {FormsModule} from '@angular/forms'; // <-- IMPORTANT pour [(ngModel)]
import {AuthService} from '../../services/auth/auth';
import {UserService} from '../../services/user/user';
import {LangCode} from '../../../environments/environment';
import {LangSelectComponent} from '../lang-select/lang-select';
import {UserMenuComponent} from '../user-menu/user-menu';
import {SubjectService} from '../../services/subject/subject';
import {QuestionService} from '../../services/question/question';
import {QuizService} from '../../services/quiz/quiz';

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

  subjectService = inject(SubjectService);
  questionService = inject(QuestionService);
  quizService = inject(QuizService);

  goQuizList(): void {
    this.quizService.goList();
  }

  goSubjectList(): void {
    this.subjectService.goList();
  }

  goQuestionList(): void {
    this.questionService.goList();
  }

  goSubjectQuiz() {
    this.router.navigate(['/quiz/subject']);
  }

  menuItems = [
    {
      label: 'WpRef',
      icon: 'pi pi-home'
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
  currentLang: LangCode = 'en';
  private sub?: Subscription;

  constructor(
    public auth: AuthService,
    private router: Router,
    private userService: UserService
  ) {
  }

  onLangChange(lang: LangCode) {
    this.currentLang = lang;
    this.userService.setLocalLanguage(lang);
    this.userService.updateMeLanguage(lang).subscribe();
  }

  ngOnDestroy() {
    this.sub?.unsubscribe();
  }
}
