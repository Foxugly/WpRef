import {Component, inject, OnInit, signal} from '@angular/core';
import {ActivatedRoute} from '@angular/router';
import {QuizService, QuizSession} from '../../../services/quiz/quiz';
import {Question, QuestionService} from '../../../services/question/question';
import {UserService} from '../../../services/user/user';
import {AnswerPayload, QuizQuestionComponent} from '../../../components/quiz-question/quiz-question';
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

  /**
   * Appelé par le composant enfant quand l'utilisateur clique sur "Suivante"
   */
  onNextQuestion(payload: AnswerPayload): void {
    this.saveAnswer(payload, () => {
      this.goQuestionNext(this.index);
    });
  }

  /**
   * Appelé par le composant enfant quand l'utilisateur clique sur "Précédente"
   */
  onPreviousQuestion(payload: AnswerPayload): void {
    this.saveAnswer(payload, () => {
      this.goQuestionPrev(this.index);
    });
  }

  goQuestionNext(index: number): void {
    if (this.hasQuestionNext(index)) {
      this.changeQuestion(index + 1);
    }
  }

  goQuestionPrev(index: number): void {
    if (this.hasQuestionPrev(index)) {
      this.changeQuestion(index - 1);
    }
  }

  onQuestionSelected(index: number): void {
    this.changeQuestion(index);
  }

  markAnswered(index: number): void {
    console.log("markAnswered");
    this.quizNavItems.update(items =>
      items.map(item => {
        console.log("item before:", item);
        if (item.index === index) {
          const updated = {...item, answered: true};
          console.log("item updated:", updated);
          return updated;
        }
        return item;
      })
    );
  }

  toggleFlag(): void {
    console.log("toggleFlag");

    this.quizNavItems.update(items =>
      items.map(item => {
        console.log("checking item:", item);

        if (item.index === this.index) {
          const updated = {...item, flagged: !item.flagged};
          console.log("updated item:", updated);
          return updated;
        }

        return item;
      })
    );
  }


  protected hasQuestionNext(index: number): boolean {
    return index < (this.quizSession()?.questions.length ?? 0);
  }

  protected hasQuestionPrev(index: number): boolean {
    return index > 1;
  }

  protected changeQuestion(index: number): void {
    const item = this.quizNavItems().find(q => q.index === index);
    if (!item) {
      console.warn("QuestionNavItem introuvable pour index", index);
      return;
    }
    this.index = index;
    this.quizNavItem.set(item);
  }

  private saveAnswer(payload: AnswerPayload, afterSave?: () => void): void {
    // À adapter au nom réel de ta méthode d'API :
    // ex: this.quizService.saveAnswer(this.quiz_id, payload)
    this.quizService.saveAnswer(this.quiz_id, payload).subscribe({
      next: (response) => {
        // on marque la question comme répondue
        if (response.status != 204) {
          this.markAnswered(payload.index);
        }
        if (afterSave) {
          afterSave();
        }
      },
      error: (err) => {
        console.error('Erreur lors de la sauvegarde de la réponse', err);
        // tu peux afficher un toast ou mettre un message dans this.error
      }
    });
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
