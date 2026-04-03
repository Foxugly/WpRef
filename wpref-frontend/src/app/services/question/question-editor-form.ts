import {firstValueFrom, Observable} from 'rxjs';
import {
  FormArray,
  FormControl,
  FormGroup,
  NonNullableFormBuilder,
  Validators,
} from '@angular/forms';

import {
  LanguageEnumDto,
  MediaAssetDto,
  MediaAssetUploadKindEnumDto,
  PatchedQuestionPartialWritePayloadRequestDto,
  QuestionMediaCreateRequestParams,
  QuestionReadDto,
  QuestionWritePayloadRequestDto,
} from '../../api/generated';
import {MediaSelectorValue} from '../../components/media-selector/media-selector';
import {LangCode} from '../translation/translation';
import {
  AnswerOptionForm,
  AnswerTrGroup,
  QuestionDuplicateDraft,
  QuestionTrGroup,
  QuestionTranslationForm,
} from './question';

export type QuestionEditorForm = FormGroup<{
  domain: FormControl<number>;
  subject_ids: FormControl<number[]>;
  active: FormControl<boolean>;
  is_mode_practice: FormControl<boolean>;
  is_mode_exam: FormControl<boolean>;
  media: FormControl<MediaSelectorValue[]>;
  translations: FormGroup;
  answer_options: FormArray<FormGroup>;
}>;

type QuestionMediaUploader = (params: QuestionMediaCreateRequestParams) => Observable<MediaAssetDto>;

export function createQuestionEditorForm(
  fb: NonNullableFormBuilder,
  options?: { domainDisabled?: boolean; subjectIdsDisabled?: boolean },
): QuestionEditorForm {
  const form: QuestionEditorForm = fb.group({
    domain: fb.control<number>(0, {validators: [Validators.required]}),
    subject_ids: new FormControl<number[]>(
      {
        value: [],
        disabled: !!options?.subjectIdsDisabled,
      },
      {nonNullable: true},
    ),
    active: fb.control(true),
    is_mode_practice: fb.control(true),
    is_mode_exam: fb.control(false),
    media: fb.control<MediaSelectorValue[]>([]),
    translations: fb.group({}),
    answer_options: fb.array<FormGroup>([]),
  });

  if (options?.domainDisabled) {
    form.controls.domain.disable({emitEvent: false});
  }

  return form;
}

export function getAnswerOptions(form: QuestionEditorForm): FormArray<FormGroup> {
  return form.controls.answer_options;
}

export function getTranslationsGroup(form: QuestionEditorForm): FormGroup {
  return form.controls.translations;
}

export function getLangGroup(form: QuestionEditorForm, lang: LangCode): FormGroup {
  return getTranslationsGroup(form).get(lang) as FormGroup;
}

export function getQuestionTrGroup(form: QuestionEditorForm, lang: LangCode): QuestionTrGroup {
  const group = getTranslationsGroup(form).get(lang) as QuestionTrGroup | null;
  if (!group) {
    throw new Error(`Missing question translation group for: ${lang}`);
  }
  return group;
}

export function getLangAnswerOptions(form: QuestionEditorForm, lang: LangCode): FormArray<AnswerTrGroup> {
  return getLangGroup(form, lang).get('answer_options') as FormArray<AnswerTrGroup>;
}

export function getAnswerContentControl(
  form: QuestionEditorForm,
  index: number,
  lang: LangCode,
): FormControl<string> {
  const row = getLangAnswerOptions(form, lang).at(index) as AnswerTrGroup;
  return row.controls.content;
}

export function getAnswerMetaGroup(form: QuestionEditorForm, index: number): FormGroup {
  return getAnswerOptions(form).at(index) as FormGroup;
}

export function getAnswerCorrectControl(
  form: QuestionEditorForm,
  index: number,
): FormControl<boolean> {
  return getAnswerMetaGroup(form, index).get('is_correct') as FormControl<boolean>;
}

export function ensureQuestionTranslationControls(
  fb: NonNullableFormBuilder,
  form: QuestionEditorForm,
  codes: LangCode[],
): void {
  const translationsGroup = getTranslationsGroup(form);

  Object.keys(translationsGroup.controls).forEach((key) => {
    if (!codes.includes(key as LangCode)) {
      translationsGroup.removeControl(key);
    }
  });

  for (const code of codes) {
    if (!translationsGroup.contains(code)) {
      translationsGroup.addControl(
        code,
        fb.group({
          title: fb.control('', {
            validators: [Validators.required, Validators.minLength(2), Validators.maxLength(200)],
          }),
          description: fb.control(''),
          explanation: fb.control(''),
          answer_options: fb.array<AnswerTrGroup>([]),
        }),
      );
    }
  }
}

export function resetQuestionTranslationsOnly(form: QuestionEditorForm): void {
  const translationsGroup = getTranslationsGroup(form);
  Object.keys(translationsGroup.controls).forEach((key) => translationsGroup.removeControl(key));
}

export function clearQuestionLangAnswerArrays(form: QuestionEditorForm, codes: LangCode[]): void {
  for (const code of codes) {
    const answers = getLangAnswerOptions(form, code);
    while (answers.length > 0) {
      answers.removeAt(answers.length - 1);
    }
  }
}

export function syncLangAnswerArraysWithRoot(
  fb: NonNullableFormBuilder,
  form: QuestionEditorForm,
  langs: LangCode[],
): void {
  const needed = getAnswerOptions(form).length;

  for (const lang of langs) {
    const answers = getLangAnswerOptions(form, lang);
    while (answers.length < needed) {
      answers.push(
        fb.group({
          content: fb.control('', {validators: [Validators.required]}),
        }) as AnswerTrGroup,
      );
    }
    while (answers.length > needed) {
      answers.removeAt(answers.length - 1);
    }
  }
}

export function addQuestionAnswerOption(
  fb: NonNullableFormBuilder,
  form: QuestionEditorForm,
  langs: LangCode[],
): void {
  const nextIndex = getAnswerOptions(form).length;
  getAnswerOptions(form).push(
    fb.group({
      id: fb.control<number | null>(null),
      is_correct: fb.control(false),
      sort_order: fb.control(nextIndex + 1),
    }),
  );

  for (const lang of langs) {
    getLangAnswerOptions(form, lang).push(
      fb.group({
        content: fb.control('', {validators: [Validators.required]}),
      }) as AnswerTrGroup,
    );
  }
}

export function removeQuestionAnswerOption(
  form: QuestionEditorForm,
  langs: LangCode[],
  index: number,
  minCount = 2,
): void {
  if (getAnswerOptions(form).length <= minCount) {
    return;
  }

  getAnswerOptions(form).removeAt(index);

  for (const lang of langs) {
    getLangAnswerOptions(form, lang).removeAt(index);
  }

  getAnswerOptions(form).controls.forEach((control, i) => {
    control.get('sort_order')?.setValue(i + 1);
  });
}

export function resolveQuestionDomainLanguages(question: QuestionReadDto): LangCode[] {
  const allowed = (question.domain.allowed_languages ?? [])
    .filter((language) => !!language.active)
    .map((language) => language.code)
    .filter((code): code is LangCode => !!code);

  if (allowed.length) {
    return allowed;
  }

  const translationCodes = Object.keys(question.translations ?? {}) as LangCode[];
  if (translationCodes.length) {
    return translationCodes;
  }

  return [LanguageEnumDto.Fr as LangCode];
}

export function populateQuestionEditorForm(
  fb: NonNullableFormBuilder,
  form: QuestionEditorForm,
  question: QuestionReadDto,
): LangCode[] {
  const langs = resolveQuestionDomainLanguages(question);

  ensureQuestionTranslationControls(fb, form, langs);
  getAnswerOptions(form).clear();
  clearQuestionLangAnswerArrays(form, langs);

  form.patchValue({
    domain: question.domain.id,
    subject_ids: question.subjects.map((subject) => subject.id),
    active: question.active,
    is_mode_practice: question.is_mode_practice,
    is_mode_exam: question.is_mode_exam,
    media: (question.media ?? []).map((media, index) => ({
      id: media.asset.id,
      kind: media.asset.kind,
      sort_order: media.sort_order ?? index + 1,
      file: media.asset.file ?? null,
      external_url: media.asset.external_url ?? null,
    })),
  });

  const translations = (question.translations ?? {}) as Record<string, QuestionTranslationForm>;
  for (const lang of langs) {
    getQuestionTrGroup(form, lang).patchValue({
      title: translations[lang]?.title ?? '',
      description: translations[lang]?.description ?? '',
      explanation: translations[lang]?.explanation ?? '',
    });
  }

  const answers = [...(question.answer_options ?? [])].sort(
    (left, right) => (left.sort_order ?? left.id) - (right.sort_order ?? right.id),
  );

  for (const [index, answer] of answers.entries()) {
    getAnswerOptions(form).push(
      fb.group({
        id: fb.control<number | null>(answer.id ?? null),
        is_correct: fb.control(!!answer.is_correct),
        sort_order: fb.control(answer.sort_order ?? index + 1),
      }),
    );

    const answerTranslations = (answer.translations ?? {}) as Record<string, { content?: string }>;
    for (const lang of langs) {
      getLangAnswerOptions(form, lang).push(
        fb.group({
          content: fb.control(
            answerTranslations[lang]?.content ?? '',
            {validators: [Validators.required]},
          ),
        }) as AnswerTrGroup,
      );
    }
  }

  return langs;
}

export function populateQuestionEditorFormFromDraft(
  fb: NonNullableFormBuilder,
  form: QuestionEditorForm,
  draft: QuestionDuplicateDraft,
  langs: LangCode[],
): void {
  ensureQuestionTranslationControls(fb, form, langs);
  getAnswerOptions(form).clear();
  clearQuestionLangAnswerArrays(form, langs);

  form.patchValue({
    domain: draft.domainId,
    subject_ids: draft.subjectIds,
    active: draft.active,
    is_mode_practice: draft.isModePractice,
    is_mode_exam: draft.isModeExam,
    media: draft.media,
  });

  for (const lang of langs) {
    getQuestionTrGroup(form, lang).patchValue({
      title: draft.translations[lang]?.title ?? '',
      description: draft.translations[lang]?.description ?? '',
      explanation: draft.translations[lang]?.explanation ?? '',
    });
  }

  for (const [index, answer] of draft.answerOptions.entries()) {
    getAnswerOptions(form).push(
      fb.group({
        id: fb.control<number | null>(null),
        is_correct: fb.control(!!answer.is_correct),
        sort_order: fb.control(answer.sort_order ?? index + 1),
      }),
    );

    for (const lang of langs) {
      getLangAnswerOptions(form, lang).push(
        fb.group({
          content: fb.control(
            answer.translations[lang]?.content ?? '',
            {validators: [Validators.required]},
          ),
        }) as AnswerTrGroup,
      );
    }
  }
}

export function clearQuestionTranslationTab(
  form: QuestionEditorForm,
  lang: LangCode,
): void {
  const group = getQuestionTrGroup(form, lang);
  group.controls.title.setValue('');
  group.controls.description.setValue('');
  group.controls.explanation.setValue('');
  group.controls.title.markAsDirty();
  group.controls.description.markAsDirty();
  group.controls.explanation.markAsDirty();

  const answers = getLangAnswerOptions(form, lang);
  for (let i = 0; i < answers.length; i += 1) {
    const control = getAnswerContentControl(form, i, lang);
    control.setValue('');
    control.markAsDirty();
  }
}

export function isQuestionEditorFormValid(
  form: QuestionEditorForm,
  langs: LangCode[],
  options?: { requireDomain?: boolean },
): boolean {
  if (options?.requireDomain && !form.controls.domain.value) {
    return false;
  }

  if (!langs.length) {
    return false;
  }

  if (getAnswerOptions(form).length < 2) {
    return false;
  }

  const titlesValid = langs.every((lang) => getQuestionTrGroup(form, lang).controls.title.valid);
  if (!titlesValid) {
    return false;
  }

  for (const lang of langs) {
    const answers = getLangAnswerOptions(form, lang);
    if (answers.length !== getAnswerOptions(form).length) {
      return false;
    }

    for (let i = 0; i < answers.length; i += 1) {
      if (getAnswerContentControl(form, i, lang).invalid) {
        return false;
      }
    }
  }

  return true;
}

export function getQuestionCorrectCount(form: QuestionEditorForm): number {
  return getAnswerOptions(form).controls.filter((control) => !!control.get('is_correct')?.value).length;
}

function buildQuestionTranslations(
  form: QuestionEditorForm,
  langs: LangCode[],
): Record<LangCode, QuestionTranslationForm> {
  const translations = {} as Record<LangCode, QuestionTranslationForm>;

  for (const lang of langs) {
    const group = getQuestionTrGroup(form, lang);
    translations[lang] = {
      title: group.controls.title.value ?? '',
      description: group.controls.description.value ?? '',
      explanation: group.controls.explanation.value ?? '',
    };
  }

  return translations;
}

function buildAnswerOptionsPayload(form: QuestionEditorForm, langs: LangCode[]): AnswerOptionForm[] {
  const answerOptions: AnswerOptionForm[] = [];

  for (let i = 0; i < getAnswerOptions(form).length; i += 1) {
    const meta = getAnswerMetaGroup(form, i);
    const perLang = {} as AnswerOptionForm['translations'];

    for (const lang of langs) {
      perLang[lang] = {
        content: getAnswerContentControl(form, i, lang).value ?? '',
      };
    }

    answerOptions.push({
      id: Number(meta.get('id')?.value) || undefined,
      is_correct: !!meta.get('is_correct')?.value,
      sort_order: Number(meta.get('sort_order')?.value ?? i + 1),
      translations: perLang,
    });
  }

  return answerOptions;
}

export function buildQuestionCreatePayload(
  form: QuestionEditorForm,
  langs: LangCode[],
  mediaAssetIds: number[],
): QuestionWritePayloadRequestDto {
  const correctCount = getQuestionCorrectCount(form);

  return {
    domain: Number(form.controls.domain.value),
    subject_ids: form.controls.subject_ids.value ?? [],
    allow_multiple_correct: correctCount > 1,
    active: !!form.controls.active.value,
    is_mode_practice: !!form.controls.is_mode_practice.value,
    is_mode_exam: !!form.controls.is_mode_exam.value,
    translations: buildQuestionTranslations(form, langs),
    answer_options: buildAnswerOptionsPayload(form, langs),
    media_asset_ids: mediaAssetIds,
  };
}

export function buildQuestionPatchPayload(
  form: QuestionEditorForm,
  langs: LangCode[],
  mediaAssetIds: number[],
): PatchedQuestionPartialWritePayloadRequestDto {
  const correctCount = getQuestionCorrectCount(form);

  return {
    translations: buildQuestionTranslations(form, langs),
    allow_multiple_correct: correctCount > 1,
    active: !!form.controls.active.value,
    is_mode_practice: !!form.controls.is_mode_practice.value,
    is_mode_exam: !!form.controls.is_mode_exam.value,
    subject_ids: form.controls.subject_ids.value ?? [],
    answer_options: buildAnswerOptionsPayload(form, langs),
    media_asset_ids: mediaAssetIds,
  };
}

export async function uploadQuestionEditorMediaAssets(
  media: MediaSelectorValue[],
  uploadMedia: QuestionMediaUploader,
): Promise<number[]> {
  if (!media.length) {
    return [];
  }

  const ids: number[] = [];

  for (const item of media) {
    if (item.id) {
      ids.push(item.id);
      continue;
    }

    if (item.kind === MediaAssetUploadKindEnumDto.External && item.external_url) {
      const asset = await firstValueFrom(
        uploadMedia({
          kind: MediaAssetUploadKindEnumDto.External,
          externalUrl: item.external_url,
        }),
      );
      ids.push(asset.id);
      continue;
    }

    if (
      (item.kind === MediaAssetUploadKindEnumDto.Image || item.kind === MediaAssetUploadKindEnumDto.Video) &&
      item.file instanceof File
    ) {
      const uploadKind =
        item.kind === MediaAssetUploadKindEnumDto.Image
          ? MediaAssetUploadKindEnumDto.Image
          : MediaAssetUploadKindEnumDto.Video;

      const asset = await firstValueFrom(
        uploadMedia({
          file: item.file,
          kind: uploadKind,
        }),
      );
      ids.push(asset.id);
      continue;
    }

    throw new Error(`Media invalide: ${JSON.stringify(item)}`);
  }

  return [...new Set(ids)];
}

export function isEmptyQuestionHtml(html: string): boolean {
  const cleaned = (html ?? '')
    .replace(/<br\s*\/?>/gi, '')
    .replace(/&nbsp;/gi, ' ')
    .replace(/<[^>]+>/g, '')
    .trim();
  return cleaned.length === 0;
}
