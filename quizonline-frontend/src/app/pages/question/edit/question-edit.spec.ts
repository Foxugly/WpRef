import {ComponentFixture, TestBed} from '@angular/core/testing';
import {ActivatedRoute, convertToParamMap, provideRouter} from '@angular/router';
import {of} from 'rxjs';

import {QuestionEdit} from './question-edit';
import {QuestionService} from '../../../services/question/question';
import {SubjectService} from '../../../services/subject/subject';
import {UserService} from '../../../services/user/user';

describe('QuestionEdit', () => {
  let component: QuestionEdit;
  let fixture: ComponentFixture<QuestionEdit>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [QuestionEdit],
      providers: [
        provideRouter([]),
        {
          provide: ActivatedRoute,
          useValue: {
            paramMap: of(convertToParamMap({questionId: '1'})),
          },
        },
        {
          provide: QuestionService,
          useValue: {
            retrieve: () => of({
              id: 1,
              domain: {
                id: 1,
                translations: {},
                allowed_languages: [],
                active: true,
                subjects_count: 0,
                questions_count: 0,
                owner: {id: 1, username: 'owner'},
                staff: [],
                members: [],
                created_at: '',
                updated_at: '',
              },
              translations: {},
              allow_multiple_correct: false,
              active: true,
              is_mode_practice: true,
              is_mode_exam: true,
              subjects: [],
              answer_options: [],
              media: [],
              created_at: '',
            }),
            delete: () => of({}),
            update: () => of({}),
            goBack: jasmine.createSpy('goBack'),
          },
        },
        {
          provide: SubjectService,
          useValue: {
            list: () => of([]),
          },
        },
        {
          provide: UserService,
          useValue: {
            currentLang: 'fr',
          },
        },
      ],
    })
      .compileComponents();

    fixture = TestBed.createComponent(QuestionEdit);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
