import {expect, test} from '@playwright/test';

import {mockApi, seedAuthenticatedSession} from './support/mock-api';

test('cree une question avec un media YouTube normalise', async ({page}) => {
  await seedAuthenticatedSession(page);
  const api = await mockApi(page, {
    domains: [
      {
        id: 1,
        active: true,
        translations: {
          fr: {name: 'Sciences', description: '<p>Domaine sciences</p>'},
        },
        allowed_languages: [{code: 'fr', active: true}],
      },
    ],
    domainDetails: {
      '1': {
        id: 1,
        active: true,
        translations: {
          fr: {name: 'Sciences', description: '<p>Domaine sciences</p>'},
        },
        allowed_languages: [{code: 'fr', active: true}],
      },
    },
  });

  await page.goto('/question/add?domainId=1');

  await expect(page.getByPlaceholder('Titre...')).toBeVisible();
  await page.getByPlaceholder('Titre...').fill('Question E2E');

  const answers = page.locator('.answer__content .ql-editor');
  await answers.nth(0).fill('Bonne reponse');
  await answers.nth(1).fill('Mauvaise reponse');
  await page.locator('.answer__correct .p-checkbox').first().click();

  await page.getByRole('tab', {name: 'Lien YouTube'}).click();
  await page.locator('#youtube-url').fill('https://youtu.be/dQw4w9WgXcQ?t=43');
  await page.getByRole('button', {name: 'Ajouter ce lien'}).click();

  await expect(page.getByText('Video YouTube')).toBeVisible();

  await page.getByRole('button', {name: /cr.*er/i}).click();

  await expect(page).toHaveURL(/\/question\/list$/);
  expect(api.requests.mediaCreate).toEqual([
    {
      kind: 'external',
      external_url: 'https://www.youtube.com/watch?v=dQw4w9WgXcQ',
    },
  ]);
  expect(api.requests.questionCreate).toHaveLength(1);
  expect(api.requests.questionCreate[0]).toMatchObject({
    domain: 1,
    media_asset_ids: [850],
    translations: {
      fr: {
        title: 'Question E2E',
      },
    },
  });
});
