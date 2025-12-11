import {Component, inject, OnInit, signal} from '@angular/core';
import {ActivatedRoute} from '@angular/router';
import {QuizService, QuizSession} from '../../../services/quiz/quiz';
import {Question, QuestionService} from '../../../services/question/question';
import {UserService} from '../../../services/user/user';
import {QuizQuestionComponent} from '../../../components/quiz-question/quiz-question';
import {QuizNav, QuizNavItem} from '../../../components/quiz-nav/quiz-nav';

@Component({
  selector: 'app-quiz-question-view',
  imports: [
    QuizQuestionComponent,
    QuizNav
  ],
  templateUrl: './question-view.html',
  styleUrl: './question-view.scss',
})
export class QuizQuestionView implements OnInit {
  quiz_id!: number;
  question_id!: number;
  index: number = 1;
  loading = signal(false);
  error = signal<string | null>(null);
  quizSession = signal<QuizSession | null>(null);
  quizNavItem = signal<QuizNavItem | null>(null);
  quizNavItems = signal<QuizNavItem[]>([]);
  protected showCorrect: boolean = false;
  private route = inject(ActivatedRoute);
  private quizService = inject(QuizService);
  private questionService = inject(QuestionService);
  private userService = inject(UserService);

  ngOnInit(): void {
    this.quiz_id = Number(this.route.snapshot.paramMap.get('quiz_id'));
    this.question_id = Number(this.route.snapshot.paramMap.get('question_id'));
    if (!this.quiz_id || Number.isNaN(this.quiz_id)) {
      this.error.set('Identifiant de question invalide.');
      return;
    }
    if (!this.question_id || Number.isNaN(this.question_id)) {
      this.error.set('Identifiant de question invalide.');
      return;
    }

    this.loadQuestion();
  }

  hasNext(i: number): boolean {
    return i < (this.quizSession()?.questions.length ?? 0) - 1;
  }

  goNext(i: number): void {
    if (this.hasNext(i)) {
      this.quizService.goQuestionNext(this.quiz_id, i);
    }
  }

  hasPrev(i: number): boolean {
    return i > 0;
  }

  goPrev(i: number): void {
    if (this.hasPrev(i)) {
      this.quizService.goQuestionPrev(this.quiz_id, i);
    }
  }

  onQuestionSelected(index: number): void {
    console.log("onQuestionselected", index);
    const item = this.quizNavItems().find(q => q.index === index);
    if (!item) {
      console.warn("QuestionNavItem introuvable pour index", index);
      return;
    }
    this.quizNavItem.set(item);
  }


  markAnswered(index: number): void {
    this.quizNavItems.update(items =>
      items.map(item =>
        item.index === index
          ? {...item, answered: true}
          : item
      )
    );
  }

  toggleFlag(): void {
    this.quizNavItems.update(items =>
      items.map(item =>
        item.index === this.index
          ? {...item, flagged: !item.flagged}
          : item
      )
    );
  }


  private buildQuestionNavItems(questions: Question[]): void {
    const navItems: QuizNavItem[] = questions.map((q, idx) => ({
      index: idx + 1,
      id: q.id,
      answered: false,
      flagged: false,
      question: q,
    }));

    this.quizNavItems.set(navItems);
  }

  private loadQuestion(): void {
    console.log("loadQuestion");
    this.loading.set(true);
    this.error.set(null);
    this.quizService.retrieveSession(this.quiz_id).subscribe({
      next: (session) => {
        this.quizSession.set(session);

        // Récupérer l'index de la question dans la session
        const index = this.question_id - 1;
        this.buildQuestionNavItems(session.questions);
        if (index < 0 || index >= this.quizNavItems().length) {
          console.error('Index de question invalide', index);
          this.error.set("Cette question n'existe pas dans ce quiz.");
          this.loading.set(false);
          return;
        }

        const id = this.quizNavItems()[index].id;

        this.questionService.retrieve(id).subscribe({
      next: q => {
        const items = this.quizNavItems();
        const existing = items.find(item => item.id === q.id);

        const navItem: QuizNavItem = existing
          ? {...existing, question: q} // on garde answered/flagged
          : {
            index: items.length + 1,
            id: q.id,
            answered: false,
            flagged: false,
            question: q,
          };

        this.quizNavItem.set(navItem);
      },
      error: err => {
        console.error('Erreur chargement question', err);
        this.error.set("Impossible de charger cette question.");
      }
    });
      },
      error: (err) => {
        console.error('Erreur chargement quizSession', err);
        this.error.set("Impossible de charger cette question.");
        this.loading.set(false);
      },
    });
  }
}
