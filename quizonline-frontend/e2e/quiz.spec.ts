import {expect, test} from '@playwright/test';

import {mockApi, seedAuthenticatedSession} from './support/mock-api';

test.describe('quiz flows', () => {
  test.beforeEach(async ({page}) => {
    await seedAuthenticatedSession(page);
  });

  test('affiche la liste des quiz et ouvre le resume d un quiz', async ({page}) => {
    await mockApi(page);

    await page.goto('/quiz/list');
    await expect(page.getByRole('heading', {name: 'Quiz'})).toBeVisible();
    await expect(page.getByText('Template public')).toBeVisible();

    await page.getByRole('row', {name: /template public/i}).locator('button').first().click();

    await expect(page).toHaveURL(/\/quiz\/701$/);
    await expect(page.getByRole('button', {name: /demarrer|continuer|voir la correction/i})).toBeVisible();
  });

  test('envoie un template puis consulte les resultats', async ({page}) => {
    const api = await mockApi(page);

    await page.goto('/quiz/list');
    await page.getByRole('row', {name: /template admin/i}).locator('button').nth(1).click();

    await expect(page.getByText('Envoyer le quiz')).toBeVisible();
    await page.getByRole('button', {name: /tout sélectionner/i}).click();
    await page.locator('p-dialog').getByRole('button', {name: 'Envoyer'}).click({force: true});

    await expect.poll(() => api.requests.quizTemplateBulkAssign).toEqual([
      {quiz_template_id: 950, user_ids: [2]},
    ]);

    await expect(page).toHaveURL(/\/quiz\/template\/950\/results$/);
    await expect(page.getByRole('heading', {name: 'Resultats des quiz envoyes'})).toBeVisible();
    await expect(page.getByRole('cell', {name: 'apprenant'})).toBeVisible();
  });

  test('sauvegarde une reponse puis passe a la question suivante', async ({page}) => {
    const api = await mockApi(page, {
      quizzes: [
        {
          id: 700,
          title: 'Quiz de test',
          quiz_template_title: 'Quiz de test',
          user: 'admin',
          mode: 'practice',
          max_questions: 2,
          with_duration: false,
          duration: null,
          active: true,
          can_answer: true,
          created_at: '2026-03-30T12:00:00Z',
          started_at: '2026-03-30T12:01:00Z',
          ended_at: null,
          answer_correctness_state: 'unknown',
          questions: [
            {
              id: 801,
              sort_order: 1,
              question: {
                id: 200,
                active: true,
                allow_multiple_correct: false,
                is_mode_practice: true,
                is_mode_exam: false,
                translations: {
                  fr: {
                    title: 'Question de test',
                    description: '<p>Description de test</p>',
                    explanation: '<p>Explication de test</p>',
                  },
                },
                media: [],
                subjects: [],
                answer_options: [
                  {id: 501, sort_order: 1, content: '<p>Bonne reponse</p>', is_correct: null},
                  {id: 502, sort_order: 2, content: '<p>Mauvaise reponse</p>', is_correct: null},
                ],
              },
            },
            {
              id: 802,
              sort_order: 2,
              question: {
                id: 201,
                active: true,
                allow_multiple_correct: false,
                is_mode_practice: true,
                is_mode_exam: false,
                translations: {
                  fr: {
                    title: 'Deuxieme question',
                    description: '<p>Description 2</p>',
                    explanation: '<p>Explication 2</p>',
                  },
                },
                media: [],
                subjects: [],
                answer_options: [
                  {id: 503, sort_order: 1, content: '<p>Bonne reponse 2</p>', is_correct: null},
                  {id: 504, sort_order: 2, content: '<p>Mauvaise reponse 2</p>', is_correct: null},
                ],
              },
            },
          ],
        },
      ],
      quizDetails: {
        '700': {
          id: 700,
          title: 'Quiz de test',
          quiz_template_title: 'Quiz de test',
          user: 'admin',
          mode: 'practice',
          max_questions: 2,
          with_duration: false,
          duration: null,
          active: true,
          can_answer: true,
          created_at: '2026-03-30T12:00:00Z',
          started_at: '2026-03-30T12:01:00Z',
          ended_at: null,
          answer_correctness_state: 'unknown',
          questions: [
            {
              id: 801,
              sort_order: 1,
              question: {
                id: 200,
                active: true,
                allow_multiple_correct: false,
                is_mode_practice: true,
                is_mode_exam: false,
                translations: {
                  fr: {
                    title: 'Question de test',
                    description: '<p>Description de test</p>',
                    explanation: '<p>Explication de test</p>',
                  },
                },
                media: [],
                subjects: [],
                answer_options: [
                  {id: 501, sort_order: 1, content: '<p>Bonne reponse</p>', is_correct: null},
                  {id: 502, sort_order: 2, content: '<p>Mauvaise reponse</p>', is_correct: null},
                ],
              },
            },
            {
              id: 802,
              sort_order: 2,
              question: {
                id: 201,
                active: true,
                allow_multiple_correct: false,
                is_mode_practice: true,
                is_mode_exam: false,
                translations: {
                  fr: {
                    title: 'Deuxieme question',
                    description: '<p>Description 2</p>',
                    explanation: '<p>Explication 2</p>',
                  },
                },
                media: [],
                subjects: [],
                answer_options: [
                  {id: 503, sort_order: 1, content: '<p>Bonne reponse 2</p>', is_correct: null},
                  {id: 504, sort_order: 2, content: '<p>Mauvaise reponse 2</p>', is_correct: null},
                ],
              },
            },
          ],
          answers: [],
        },
      },
    });

    await page.goto('/quiz/700/questions');

    await expect(page.getByText('Bonne reponse')).toBeVisible();
    await page.locator('input[id="opt501"]').check({force: true});
    await page.getByRole('button', {name: 'Suivant'}).click();

    await expect(page.getByText('Deuxieme question')).toBeVisible();
    await expect.poll(() => api.requests.quizAnswerCreate.length).toBe(1);
    expect(api.requests.quizAnswerCreate[0]).toMatchObject({
      question_id: 200,
      question_order: 1,
      selected_options: [501],
    });
  });
});
