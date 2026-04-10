import {expect, test} from '@playwright/test';

test.beforeEach(async ({page}) => {
  await page.addInitScript(() => {
    (window as Window & {__WPREF_API_BASE_URL?: string}).__WPREF_API_BASE_URL = 'http://127.0.0.1:8001';
  });
});

async function login(page: import('@playwright/test').Page): Promise<void> {
  await page.goto('/login');
  await page.locator('#username').fill('admin');
  await page.locator('input[type="password"]').fill('secret123');
  await page.locator('button[type="submit"]').click();
  await expect(page).toHaveURL(/\/home$/);
}

async function getAccessToken(page: import('@playwright/test').Page): Promise<string> {
  const token = await page.evaluate(() =>
    sessionStorage.getItem('access_token') ?? localStorage.getItem('access_token'),
  );
  expect(token).toBeTruthy();
  return token!;
}

test('parcourt un quiz reel et persiste une reponse cote backend', async ({page}) => {
  await login(page);

  await page.goto('/quiz/list');
  await expect(page.getByRole('heading', {name: 'Quiz'})).toBeVisible();
  const templatesPanel = page.locator('p-tabpanel').filter({has: page.locator('app-quiz-template-table')}).first();
  await expect(templatesPanel.getByRole('cell', {name: 'Quiz full-stack', exact: true})).toBeVisible();

  await templatesPanel.locator(`[aria-label*="Commencer"][aria-label*="Quiz full-stack"]`).first().click();

  await expect(page).toHaveURL(/\/quiz\/\d+$/);
  await expect(page.getByRole('heading', {name: 'Quiz full-stack'})).toBeVisible();

  const quizIdMatch = page.url().match(/\/quiz\/(\d+)$/);
  expect(quizIdMatch).toBeTruthy();
  const quizId = quizIdMatch![1];

  await page.getByRole('button', {name: /Demarrer le quiz/i}).click();

  await expect(page).toHaveURL(new RegExp(`/quiz/${quizId}/questions$`));
  await expect(page.getByText('Bonne reponse')).toBeVisible();

  await page.getByRole('radio').first().check();
  await page.getByRole('button', {name: 'Suivant'}).click();

  await expect(page.getByRole('button', {name: 'Terminer'})).toBeVisible();
  await page.locator('input[type="checkbox"], input[type="radio"]').first().check();
  await page.getByRole('button', {name: 'Terminer'}).click();

  await expect(page).toHaveURL(new RegExp(`/quiz/${quizId}$`));
  await expect(page.getByText('2 / 2')).toBeVisible();

  const accessToken = await getAccessToken(page);
  const answersResponse = await page.request.get(`http://127.0.0.1:8001/api/quiz/${quizId}/answer/`, {
    headers: {
      Authorization: `Bearer ${accessToken}`,
    },
  });
  expect(answersResponse.ok()).toBeTruthy();
  const answersJson = await answersResponse.json();
  const answersPayload = answersJson.results ?? answersJson;

  expect(answersPayload).toHaveLength(2);
  expect(answersPayload[0].question_order).toBe(1);
  expect(answersPayload[0].selected_options).toHaveLength(1);
  expect(answersPayload[1].question_order).toBe(2);
  expect(answersPayload[1].selected_options).toHaveLength(1);

  const quizResponse = await page.request.get(`http://127.0.0.1:8001/api/quiz/${quizId}/`, {
    headers: {
      Authorization: `Bearer ${accessToken}`,
    },
  });
  expect(quizResponse.ok()).toBeTruthy();
  const quizPayload = await quizResponse.json();

  expect(quizPayload.started_at).toBeTruthy();
  expect(quizPayload.active).toBe(false);
  expect(quizPayload.correct_answers).toBe(2);
  expect(quizPayload.earned_score).toBe(2);
  expect(quizPayload.max_score).toBe(2);
});
