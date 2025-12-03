import {Component, inject, OnInit} from '@angular/core';
import {MenuItem} from 'primeng/api';
import {AuthService} from '../../services/auth/auth';
import {Router} from '@angular/router';
import {Menubar} from 'primeng/menubar';
import {SubjectService} from '../../services/subject/subject';
import {QuestionService} from '../../services/question/question';
import {QuizService} from '../../services/quiz/quiz';

@Component({
  standalone: true,
  selector: 'app-quiz-menu',
  imports: [
    Menubar
  ],
  templateUrl: './quiz-menu.html',
  styleUrl: './quiz-menu.scss',
})
export class QuizMenuComponent implements OnInit {
  items: MenuItem[] = [];
  subjectService = inject(SubjectService);
  questionService = inject(QuestionService);
  quizService = inject(QuizService);
  constructor(private router: Router, public auth: AuthService,) {
  }

  ngOnInit(): void {
    this.buildItems();
  }

  goList():void{
    this.quizService.goList();
  }

  goSubjectList():void{
    this.subjectService.goList();
  }
  goQuestionList():void{
    this.questionService.goList();
  }
  goSubjectQuiz() {
    this.router.navigate(['/quiz/subject']);
  }

  private buildItems() {
    if (!this.auth.isLoggedIn()) {
      this.items = [];
      return;
    }

    this.items = [
      {
        label: 'Home',
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
            command: () => this.goList(),
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
  }
}
