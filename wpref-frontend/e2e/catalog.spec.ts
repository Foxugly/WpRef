import {expect, test} from '@playwright/test';

import {mockApi, seedAuthenticatedSession} from './support/mock-api';

test.describe('catalog pages', () => {
  test.beforeEach(async ({page}) => {
    await seedAuthenticatedSession(page);
    await mockApi(page);
  });

  test('affiche la liste des domaines', async ({page}) => {
    await page.goto('/domain/list');

    await expect(page.getByRole('heading', {name: /domaines/i})).toBeVisible();
    await expect(page.getByRole('cell', {name: 'Sciences', exact: true})).toBeVisible();
  });

  test('affiche la liste des sujets', async ({page}) => {
    await page.goto('/subject/list');

    await expect(page.getByRole('heading', {name: /sujets/i})).toBeVisible();
    await expect(page.getByRole('cell', {name: 'Physique', exact: true})).toBeVisible();
  });

  test('affiche la liste des questions et permet d ouvrir le detail', async ({page}) => {
    await page.goto('/question/list');

    await expect(page.getByRole('heading', {name: /questions/i})).toBeVisible();
    await expect(page.getByText('Question de test')).toBeVisible();

    await page.locator('#btn_view_question').first().click();

    await expect(page.getByRole('dialog')).toBeVisible();
    await expect(page.getByText('Bonne reponse')).toBeVisible();
  });

  test('rend les medias image, video et YouTube sur le detail de question', async ({page}) => {
    await page.goto('/question/200/view');

    await expect(page.getByRole('heading', {level: 1})).toBeVisible();
    await expect(page.getByText('Bonne reponse')).toBeVisible();
    await expect(page.locator('p-image.quiz-question__media-image img')).toHaveAttribute('src', /image\.png/);
    await expect(page.locator('video.quiz-question__media-video')).toHaveAttribute('src', /video\.mp4/);
    await expect(page.locator('iframe')).toHaveAttribute('src', /youtube\.com\/embed\/dQw4w9WgXcQ/);
  });
});
