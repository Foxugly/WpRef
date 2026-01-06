import {Component, inject, OnInit, signal} from '@angular/core';
import {ActivatedRoute} from '@angular/router';
import {QuizService} from '../../../services/quiz/quiz';
import {QuestionService} from '../../../services/question/question';
import {UserService} from '../../../services/user/user';
import {AnswerPayload, QuizQuestionComponent} from '../../../components/quiz-question/quiz-question';
import {QuizNav, QuizNavItem} from '../../../components/quiz-nav/quiz-nav';
import {
  QuestionReadDto,
  QuizDto,
  QuizQuestionAnswerDto,
  QuizQuestionAnswerWriteRequestDto,
  QuizQuestionReadDto
} from '../../../api/generated';
import {HttpResponse} from '@angular/common/http';

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
  quizSession = signal<QuizDto | null>(null);
  quizNavItem = signal<QuizNavItem | null>(null);
  quizNavItems = signal<QuizNavItem[]>([]);
  protected showCorrect: boolean = false;
  private route = inject(ActivatedRoute);
  private quizService = inject(QuizService);
  private questionService = inject(QuestionService);
  private userService = inject(UserService);

  ngOnInit(): void {
    this.quiz_id = Number(this.route.snapshot.paramMap.get('quiz_id'));
    this.question_id = 1;
    if (!this.quiz_id || Number.isNaN(this.quiz_id)) {
      this.error.set('Identifiant de question invalide.');
      return;
    }
    this.loadQuestion();
  }

  /**
   * Appelé par le composant enfant quand l'utilisateur clique sur "Suivante"
   */
  onNextQuestion(payload: AnswerPayload): void {
    const qqawr: QuizQuestionAnswerWriteRequestDto = {
      question_id: payload.questionId,
      question_order: payload.index,
      selected_options: payload.selectedOptionIds,
    };
    this.saveAnswer(qqawr, () => {
      this.goQuestionNext(this.index);
    });
  }

  /**
   * Appelé par le composant enfant quand l'utilisateur clique sur "Précédente"
   */
  onPreviousQuestion(payload: AnswerPayload): void {
    const qqawr: QuizQuestionAnswerWriteRequestDto = {
      question_id: payload.questionId,
      question_order: payload.index,
      selected_options: payload.selectedOptionIds,
    };
    this.saveAnswer(qqawr, () => {
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
    this.quizNavItems.update(items =>
      items.map(item => {
        if (item.index === index) {
          const updated = {...item, answered: true};
          return updated;
        }
        return item;
      })
    );
  }

  toggleFlag(): void {
    this.quizNavItems.update(items =>
      items.map(item => {
        if (item.index === this.index) {
          const updated = {...item, flagged: !item.flagged};
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
    console.log("ChangeQuestion", index);
    console.log(this.quizNavItems());
    const item = this.quizNavItems().find(q => q.index === index);
    if (!item) {
      console.warn("QuestionNavItem introuvable pour index", index);
      return;
    }
    this.index = index;
    this.quizNavItem.set(item);
  }

  private saveAnswer(payload: QuizQuestionAnswerWriteRequestDto, afterSave?: () => void): void {
    // À adapter au nom réel de ta méthode d'API :
    // ex: this.quizService.saveAnswer(this.quiz_id, payload)
    // @ts-ignore
    this.quizService.saveAnswer(this.quiz_id, payload).subscribe({
      next: (resp: HttpResponse<QuizQuestionAnswerDto>): void => {
        // on marque la question comme répondue
        if (resp.status === 200 || resp.status === 201) {
          if (payload.question_order == null) {
            return;
          }
          this.markAnswered(payload.question_order);
          // 2) stocker les réponses de l'utilisateur dans QuizNavItems
          this.quizNavItems.update(items =>
            items.map(item => {
              if (item.index === payload.question_order) {
                return {
                  ...item,
                  answered: true,
                  selectedOptionIds: payload.selected_options ?? [],
                };
              }
              return item;
            })
          );

          // 3) garder quizNavItem courant en phase
          this.quizNavItem.update(current => {
            if (!current || current.index !== payload.question_order) {
              return current;
            }
            return {
              ...current,
              answered: true,
              selectedOptionIds: payload.selected_options ?? [],
            };
          });
        }
        if (afterSave) {
          afterSave();
        }
      },
      error: (err: any): void => {
        console.error('Erreur lors de la sauvegarde de la réponse', err);
      }
    });
  }

  /**
   * Interroge le backend pour chaque question (par question_order = index)
   * et met à jour quizNavItems avec les réponses déjà sauvegardées.
   */
  private hydrateNavItemsFromBackend(): void {
    const quizId = this.quiz_id;
    const items = this.quizNavItems();

    items.forEach(item => {
      this.quizService.getAnswer(quizId, item.index).subscribe({
        next: (answer: QuizQuestionAnswerDto) => {
          console.log("answer");
          console.log(answer);
          const selectedIds = answer.selected_options;

          if (selectedIds.length === 0) {
            // rien de coché pour cette question → on ne touche pas
            return;
          }

          // Met à jour la liste complète
          this.quizNavItems.update(current =>
            current.map(navItem =>
              navItem.index === item.index
                ? {
                  ...navItem,
                  answered: true,
                  selectedOptionIds: selectedIds,
                }
                : navItem
            )
          );

          // Si la question actuelle est celle-ci, on aligne aussi quizNavItem
          this.quizNavItem.update(current => {
            if (!current || current.index !== item.index) {
              return current;
            }
            return {
              ...current,
              answered: true,
              selectedOptionIds: selectedIds,
            };
          });
        },
        error: (err) => {
          console.error(
            `Erreur lors de la récupération de la réponse pour la question ${item.index}`,
            err
          );
        }
      });
    });
  }


  private buildQuestionNavItems(questions: QuizQuestionReadDto[]): void {
    console.log("buildQuestionNavItems");
    // @ts-ignore
    const navItems: QuizNavItem[] = questions.map((qq: QuizQuestionRead, idx: number) => ({
      index: qq.sort_order,
      id: qq.id,
      answered: false,
      flagged: false,
      question: qq.question,
      selectedOptionIds: [],
    }));

    this.quizNavItems.set(navItems);
  }

  private loadQuestion(): void {
    this.loading.set(true);
    this.error.set(null);
    this.quizService.retrieveQuiz(this.quiz_id).subscribe({
      next: (session: QuizDto): void => {
        this.quizSession.set(session);

        // Récupérer l'index de la question dans la session
        const index: number = this.question_id - 1;
        this.buildQuestionNavItems(session.questions); // TODO envoyer les questions
        this.hydrateNavItemsFromBackend();
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
