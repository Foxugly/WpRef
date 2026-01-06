// language.ts


import {LanguageEnumDto} from '../app/api/generated';

export const SUPPORTED_LANGUAGES = [
  LanguageEnumDto.En,
  LanguageEnumDto.Fr,
  LanguageEnumDto.Nl,
  LanguageEnumDto.It,
  LanguageEnumDto.Es,
] as const;

export type SupportedLanguage = typeof SUPPORTED_LANGUAGES[number];

export function isSupportedLanguage(x: LanguageEnumDto | string): x is SupportedLanguage {
  return (SUPPORTED_LANGUAGES as readonly string[]).includes(x as string);
}
