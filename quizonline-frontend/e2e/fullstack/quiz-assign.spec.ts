import {expect, test} from '@playwright/test';

const API = 'http://127.0.0.1:8001';

test.beforeEach(async ({page}) => {
  await page.addInitScript(() => {
    (window as Window & {__WPREF_API_BASE_URL?: string}).__WPREF_API_BASE_URL = 'http://127.0.0.1:8001';
  });
});

async function login(
  page: import('@playwright/test').Page,
  username = 'admin',
  password = 'secret123',
): Promise<void> {
  await page.goto('/login');
  await page.locator('#username').fill(username);
  await page.locator('input[type="password"]').fill(password);
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

test('admin assigne un QuizTemplate a testuser, testuser voit le quiz dans sa liste', async ({page}) => {
  await login(page);
  const adminToken = await getAccessToken(page);

  const usersResp = await page.request.get(`${API}/api/user/?search=testuser`, {
    headers: {Authorization: `Bearer ${adminToken}`},
  });
  expect(usersResp.ok()).toBeTruthy();
  const usersPayload = await usersResp.json();
  const testuser = (usersPayload.results ?? usersPayload).find(
    (u: {username: string}) => u.username === 'testuser',
  );
  expect(testuser).toBeTruthy();
  const testuserId: number = testuser.id;

  const templatesResp = await page.request.get(`${API}/api/quiz/template/`, {
    headers: {Authorization: `Bearer ${adminToken}`},
  });
  expect(templatesResp.ok()).toBeTruthy();
  const templatesPayload = await templatesResp.json();
  const templates = templatesPayload.results ?? templatesPayload;
  const template = templates.find((t: {title: string}) => t.title === 'Quiz full-stack');
  expect(template).toBeTruthy();
  const templateId: number = template.id;

  await page.goto('/quiz/list');
  await expect(page.getByRole('heading', {name: 'Quiz'})).toBeVisible();
  const templatesPanel = page.locator('p-tabpanel').filter({has: page.locator('app-quiz-template-table')}).first();
  await expect(templatesPanel.getByRole('cell', {name: 'Quiz full-stack', exact: true})).toBeVisible();

  await templatesPanel.locator(`[aria-label*="Envoyer"][aria-label*="Quiz full-stack"]`).first().click();

  const assignDialog = page.getByRole('dialog', {name: 'Envoyer le quiz'});
  await expect(assignDialog).toBeVisible();
  await expect(assignDialog.getByText('testuser', {exact: false})).toBeVisible();
  await assignDialog.getByText('testuser', {exact: false}).click();
  await assignDialog.getByRole('button', {name: 'Envoyer'}).click();

  const quizzesResp = await page.request.get(`${API}/api/quiz/?user=${testuserId}`, {
    headers: {Authorization: `Bearer ${adminToken}`},
  });
  expect(quizzesResp.ok()).toBeTruthy();
  const quizzesPayload = await quizzesResp.json();
  const quizzes = quizzesPayload.results ?? quizzesPayload;
  const assignedQuiz = quizzes.find(
    (q: {quiz_template: number; user: number}) =>
      q.quiz_template === templateId && q.user === testuserId,
  );
  expect(assignedQuiz).toBeTruthy();
  const assignedQuizId: number = assignedQuiz.id;

  await login(page, 'testuser', 'secret123');
  await page.goto('/quiz/list');
  await expect(page.getByRole('heading', {name: 'Quiz'})).toBeVisible();

  const sessionsTab = page.getByRole('tab', {name: /Mes quiz/i});
  if (await sessionsTab.isVisible()) {
    await sessionsTab.click();
  }
  const sessionsPanel = page.locator('p-tabpanel').filter({has: page.locator('app-quiz-session-table')}).first();
  await expect(sessionsPanel.getByRole('cell', {name: 'Quiz full-stack', exact: true}).first()).toBeVisible();

  const testuserToken = await getAccessToken(page);
  const quizResp = await page.request.get(`${API}/api/quiz/${assignedQuizId}/`, {
    headers: {Authorization: `Bearer ${testuserToken}`},
  });
  expect(quizResp.ok()).toBeTruthy();
  const quizPayload = await quizResp.json();
  expect(quizPayload.quiz_template).toBe(templateId);
  expect(quizPayload.user).toBe(testuserId);
  expect(quizPayload.started_at).toBeNull();
});
