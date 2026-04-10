import {LanguageEnumDto, QuizQuestionAnswerDto, QuizQuestionReadDto} from '../../api/generated';
import {
  applyQuizAnswers,
  buildQuizNavItems,
  findQuizNavItem,
  updateQuizNavItem,
} from './quiz-session-state';

describe('quiz session state helpers', () => {
  const domain = {
    id: 1,
    translations: {
      [LanguageEnumDto.Fr]: {
        name: 'Domaine',
        description: '',
      },
    },
    allowed_languages: [],
    active: true,
    subjects_count: 0,
    questions_count: 0,
    owner: {
      id: 1,
      username: 'owner',
    },
    managers: [],
    members: [],
    created_at: '2026-03-30T12:00:00Z',
    updated_at: '2026-03-30T12:00:00Z',
  };

  const questions: QuizQuestionReadDto[] = [
    {
      id: 10,
      sort_order: 1,
      weight: 1,
      question: {
        id: 100,
        domain,
        allow_multiple_correct: false,
        active: true,
        is_mode_practice: true,
        is_mode_exam: true,
        created_at: '2026-03-30T12:00:00Z',
        translations: {
          [LanguageEnumDto.Fr]: {
            title: 'Q1',
            description: '',
            explanation: '',
          },
        },
        subjects: [],
        answer_options: [],
        media: [],
      },
    },
    {
      id: 11,
      sort_order: 2,
      weight: 1,
      question: {
        id: 101,
        domain,
        allow_multiple_correct: false,
        active: true,
        is_mode_practice: true,
        is_mode_exam: true,
        created_at: '2026-03-30T12:00:00Z',
        translations: {
          [LanguageEnumDto.Fr]: {
            title: 'Q2',
            description: '',
            explanation: '',
          },
        },
        subjects: [],
        answer_options: [],
        media: [],
      },
    },
  ];

  it('builds nav items from ordered quiz questions', () => {
    const items = buildQuizNavItems(questions);

    expect(items.length).toBe(2);
    expect(items[0].index).toBe(1);
    expect(items[0].id).toBe(100);
    expect(items[1].index).toBe(2);
    expect(items[1].id).toBe(101);
  });

  it('applies persisted answers by question order', () => {
    const items = buildQuizNavItems(questions);
    const answers: QuizQuestionAnswerDto[] = [
      {
        id: 201,
        quiz: 700,
        quizquestion_id: 10,
        question_order: 1,
        question_id: 100,
        selected_options: [501],
        answered_at: '2026-03-30T12:05:00Z',
      },
    ];

    const hydrated = applyQuizAnswers(items, answers);

    expect(hydrated[0].answered).toBeTrue();
    expect(hydrated[0].selectedOptionIds).toEqual([501]);
    expect(hydrated[1].answered).toBeFalse();
  });

  it('falls back to question id when persisted order no longer matches', () => {
    const reorderedItems = [
      {
        ...buildQuizNavItems(questions)[0],
        index: 10,
      },
      {
        ...buildQuizNavItems(questions)[1],
        index: 20,
      },
    ];
    const answers: QuizQuestionAnswerDto[] = [
      {
        id: 202,
        quiz: 700,
        quizquestion_id: 11,
        question_order: 2,
        question_id: 101,
        selected_options: [777],
        answered_at: '2026-03-30T12:06:00Z',
      },
    ];

    const hydrated = applyQuizAnswers(reorderedItems, answers);

    expect(hydrated[1].answered).toBeTrue();
    expect(hydrated[1].selectedOptionIds).toEqual([777]);
  });

  it('updates and retrieves a single nav item', () => {
    const items = updateQuizNavItem(buildQuizNavItems(questions), 2, {
      answered: true,
      selectedOptionIds: [777],
    });

    expect(findQuizNavItem(items, 2)?.answered).toBeTrue();
    expect(findQuizNavItem(items, 2)?.selectedOptionIds).toEqual([777]);
    expect(findQuizNavItem(items, 99)).toBeNull();
  });
});
