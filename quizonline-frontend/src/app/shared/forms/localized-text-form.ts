import {FormBuilder, FormControl, FormGroup, Validators} from '@angular/forms';

export type LocalizedTextValue = {
  name: string;
  description: string;
};

export type LocalizedTextRecord = Record<string, LocalizedTextValue>;

export type LocalizedTextGroup = FormGroup<{
  name: FormControl<string>;
  description: FormControl<string>;
}>;

type FormBuilderLike = Pick<FormBuilder, 'group' | 'control'>;

export function createLocalizedTextGroup(
  fb: FormBuilderLike,
  options?: { nameMaxLength?: number },
): LocalizedTextGroup {
  const nameValidators = [Validators.required, Validators.minLength(2)];
  if (options?.nameMaxLength) {
    nameValidators.push(Validators.maxLength(options.nameMaxLength));
  }

  return fb.group({
    name: fb.control('', nameValidators),
    description: fb.control(''),
  }) as LocalizedTextGroup;
}

export function syncLocalizedTextControls(
  fb: FormBuilderLike,
  translationsGroup: FormGroup,
  codes: readonly string[],
  options?: { nameMaxLength?: number },
): void {
  const wanted = new Set<string>(codes);
  const existing = new Set<string>(Object.keys(translationsGroup.controls));

  for (const code of wanted) {
    if (!existing.has(code)) {
      translationsGroup.addControl(code, createLocalizedTextGroup(fb, options));
    }
  }

  for (const code of existing) {
    if (!wanted.has(code)) {
      translationsGroup.removeControl(code);
    }
  }
}

export function getLocalizedTextGroup(translationsGroup: FormGroup, code: string): LocalizedTextGroup {
  const group = translationsGroup.get(code) as LocalizedTextGroup | null;
  if (!group) {
    throw new Error(`Missing localized text group for language: ${code}`);
  }
  return group;
}

export function buildLocalizedTextRecord(
  translationsGroup: FormGroup,
  codes?: readonly string[],
): LocalizedTextRecord {
  const translations: LocalizedTextRecord = {};
  const keys = codes ? [...codes] : Object.keys(translationsGroup.controls);

  for (const code of keys) {
    const group = getLocalizedTextGroup(translationsGroup, code);
    translations[code] = {
      name: group.controls.name.value ?? '',
      description: group.controls.description.value ?? '',
    };
  }

  return translations;
}

export function patchLocalizedTextRecord(
  translationsGroup: FormGroup,
  codes: readonly string[],
  translations: Record<string, Partial<LocalizedTextValue>>,
): void {
  const patch: LocalizedTextRecord = {};

  for (const code of codes) {
    patch[code] = {
      name: translations[code]?.name ?? '',
      description: translations[code]?.description ?? '',
    };
  }

  translationsGroup.patchValue(patch, {emitEvent: false});
}
