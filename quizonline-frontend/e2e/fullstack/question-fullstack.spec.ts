import {expect, test} from '@playwright/test';

test.beforeEach(async ({page}) => {
  await page.addInitScript(() => {
    (window as any).__WPREF_API_BASE_URL = 'http://127.0.0.1:8001';
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

function normalizeHtmlText(value: string): string {
  return value
    .replace(/&nbsp;/g, ' ')
    .replace(/<[^>]+>/g, ' ')
    .replace(/\s+/g, ' ')
    .trim();
}

test('charge une question seedee avec ses medias reels', async ({page}) => {
  await login(page);

  await page.goto('/question/list');

  await expect(page.getByRole('heading', {name: 'Questions'})).toBeVisible();
  await expect(page.getByText('Question de seed')).toBeVisible();

  await page.locator('tr', {hasText: 'Question de seed'}).locator('#btn_view_question').click();

  const previewDialog = page.locator('.p-dialog').filter({hasText: 'Question de seed'}).first();
  await expect(previewDialog).toBeVisible();
  await expect(previewDialog.getByText('Bonne reponse')).toBeVisible();
  await expect(previewDialog.locator('p-image.quiz-question__media-image img')).toHaveAttribute(
    'src',
    /fullstack-e2e-image\.png/,
  );
  await expect(previewDialog.locator('video.quiz-question__media-video')).toHaveAttribute('src', /fullstack-e2e-video\.mp4/);
  await expect(previewDialog.locator('iframe')).toHaveAttribute('src', /youtube\.com\/embed\/dQw4w9WgXcQ/);
});

test('edite une question et persiste les traductions et reponses cote backend', async ({page}) => {
  await login(page);

  await page.goto('/question/list');
  await page.locator('#btn_edit_question').first().click();

  await expect(page).toHaveURL(/\/question\/\d+\/edit$/);
  await expect(page.getByRole('heading', {name: /Modifier/i})).toBeVisible();

  await page.getByRole('tab', {name: 'FR'}).click();
  await page.locator('input[formcontrolname="title"]:visible').fill('Question modifiee FR');

  let answers = page.locator('.answer__content .ql-editor:visible');
  await answers.nth(0).fill('Bonne reponse modifiee FR');
  await answers.nth(1).fill('Mauvaise reponse modifiee FR');

  await page.getByRole('tab', {name: 'NL'}).click();
  await page.locator('input[formcontrolname="title"]:visible').fill('Vraag aangepast NL');

  answers = page.locator('.answer__content .ql-editor:visible');
  await answers.nth(0).fill('Goed antwoord aangepast NL');
  await answers.nth(1).fill('Fout antwoord aangepast NL');

  await page.getByRole('button', {name: 'Enregistrer'}).click();

  await expect(page).toHaveURL(/\/question\/\d+\/view$/);
  await expect(page.getByRole('heading', {name: /question/i})).toBeVisible();

  const questionIdMatch = page.url().match(/\/question\/(\d+)\/view$/);
  expect(questionIdMatch).toBeTruthy();
  const questionId = questionIdMatch![1];
  const accessToken = await getAccessToken(page);

  const response = await page.request.get(`http://127.0.0.1:8001/api/question/${questionId}/`, {
    headers: {
      Authorization: `Bearer ${accessToken}`,
    },
  });

  expect(response.ok()).toBeTruthy();
  const payload = await response.json();

  expect(payload.translations.fr.title).toBe('Question modifiee FR');
  expect(payload.translations.nl.title).toBe('Vraag aangepast NL');
  expect(normalizeHtmlText(payload.answer_options[0].translations.fr.content)).toBe('Bonne reponse modifiee FR');
  expect(normalizeHtmlText(payload.answer_options[0].translations.nl.content)).toBe('Goed antwoord aangepast NL');
  expect(normalizeHtmlText(payload.answer_options[1].translations.fr.content)).toBe('Mauvaise reponse modifiee FR');
  expect(normalizeHtmlText(payload.answer_options[1].translations.nl.content)).toBe('Fout antwoord aangepast NL');
});
