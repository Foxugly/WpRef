import {ComponentFixture, TestBed} from '@angular/core/testing';
import {of} from 'rxjs';

import {QuizQuestionComponent} from './quiz-question';
import {UserService} from '../../services/user/user';
import {LanguageEnumDto} from '../../api/generated';

describe('QuizQuestion', () => {
  let component: QuizQuestionComponent;
  let fixture: ComponentFixture<QuizQuestionComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [QuizQuestionComponent],
      providers: [
        {
          provide: UserService,
          useValue: {
            currentLang: LanguageEnumDto.Fr,
            lang$: of(LanguageEnumDto.Fr),
          },
        },
      ],
    })
      .compileComponents();

    fixture = TestBed.createComponent(QuizQuestionComponent);
    component = fixture.componentInstance;
    component.quizNavItem = {
      index: 1,
      id: 1,
      answered: false,
      flagged: false,
      question: {
        id: 100,
        domain: {
          id: 1,
          translations: {},
          allowed_languages: [],
          active: true,
          subjects_count: 0,
          questions_count: 0,
          owner: {id: 1, username: 'owner'},
          managers: [],
          members: [],
          created_at: '',
          updated_at: '',
        },
        translations: {
          [LanguageEnumDto.Fr]: {
            title: 'Question',
            description: '',
            explanation: '',
          },
        },
        allow_multiple_correct: false,
        active: true,
        is_mode_practice: true,
        is_mode_exam: true,
        subjects: [],
        answer_options: [],
        media: [],
        created_at: '',
      },
    };
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
