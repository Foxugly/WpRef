import {expect, test} from '@playwright/test';

import {mockApi, seedAuthenticatedSession} from './support/mock-api';

test('compose un quiz depuis un domaine avec ponderation personnalisee', async ({page}) => {
  await seedAuthenticatedSession(page);
  const api = await mockApi(page, {
    questions: [
      {
        id: 200,
        active: true,
        allow_multiple_correct: false,
        is_mode_practice: true,
        is_mode_exam: false,
        domain: {
          id: 1,
          translations: {
            fr: {name: 'Sciences', description: '<p>Domaine sciences</p>'},
          },
        },
        subjects: [
          {
            id: 10,
            domain: 1,
            translations: {
              fr: {
                name: 'Physique',
                description: '<p>Sujet physique</p>',
                domain: {id: 1, name: 'Sciences'},
              },
            },
          },
        ],
        translations: {
          fr: {
            title: 'Question A',
            description: '<p>Description A</p>',
            explanation: '<p>Explication A</p>',
          },
        },
        media: [],
        answer_options: [
          {id: 501, sort_order: 1, content: '<p>Bonne reponse</p>', is_correct: true},
          {id: 502, sort_order: 2, content: '<p>Mauvaise reponse</p>', is_correct: false},
        ],
      },
      {
        id: 201,
        active: true,
        allow_multiple_correct: false,
        is_mode_practice: true,
        is_mode_exam: false,
        domain: {
          id: 1,
          translations: {
            fr: {name: 'Sciences', description: '<p>Domaine sciences</p>'},
          },
        },
        subjects: [
          {
            id: 10,
            domain: 1,
            translations: {
              fr: {
                name: 'Physique',
                description: '<p>Sujet physique</p>',
                domain: {id: 1, name: 'Sciences'},
              },
            },
          },
        ],
        translations: {
          fr: {
            title: 'Question B',
            description: '<p>Description B</p>',
            explanation: '<p>Explication B</p>',
          },
        },
        media: [],
        answer_options: [
          {id: 503, sort_order: 1, content: '<p>Bonne reponse</p>', is_correct: true},
          {id: 504, sort_order: 2, content: '<p>Mauvaise reponse</p>', is_correct: false},
        ],
      },
    ],
  });

  await page.goto('/quiz/add');

  await expect(page.getByRole('heading', {name: /template de quiz/i})).toBeVisible();
  await page.locator('input[formControlName="title"]').fill('Quiz compose E2E');
  await page.getByRole('tab', {name: 'Questions'}).click();

  const questionCards = page.locator('.question-card');
  await questionCards.filter({hasText: 'Question A'}).getByRole('button', {name: 'Ajouter'}).click();
  await questionCards.filter({hasText: 'Question B'}).getByRole('button', {name: 'Ajouter'}).click();

  const selectedCards = page.locator('.selected-card');
  await selectedCards.filter({hasText: 'Question B'}).getByRole('button').nth(1).click();
  await selectedCards
    .filter({hasText: 'Question A'})
    .locator('input[id^="weight-"]')
    .fill('3');

  await page.getByRole('tab', {name: 'Parametres'}).click();

  await page.getByRole('button', {name: /creer le template/i}).click();

  await expect(page).toHaveURL(/\/quiz\/list$/);
  expect(api.requests.quizTemplateCreate).toHaveLength(1);
  expect(api.requests.quizTemplateCreate[0]).toMatchObject({
    domain: 1,
    title: 'Quiz compose E2E',
    max_questions: 2,
    permanent: true,
    mode: 'practice',
  });
  expect(api.requests.quizTemplateQuestionCreate).toEqual([
    {
      question_id: 201,
      sort_order: 1,
      weight: 1,
    },
    {
      question_id: 200,
      sort_order: 2,
      weight: 3,
    },
  ]);
  expect(api.requests.quizCreate).toEqual([]);
});
