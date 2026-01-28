import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { firstValueFrom } from 'rxjs';
import {environment} from '../../../environments/environment';
import {LanguageApi, LanguageEnumDto} from '../../api/generated';
import {Router} from '@angular/router';

export type LangCode = `${LanguageEnumDto}`;
export type TranslateFormat = 'text' | 'html';

export type TranslateBatchItem = {
  key: string;          // "name" | "description"
  text: string;
  format: TranslateFormat;
};

type TranslateBatchResponse = {
  translations: Record<string, string>;
};

export const LANG_CODES = Object.values(LanguageEnumDto) as LangCode[];

export function isLangCode(value: string): value is LangCode {
  return (LANG_CODES as readonly string[]).includes(value);
}

@Injectable({ providedIn: 'root' })
export class TranslationService {
  private http = inject(HttpClient);

  async translateBatch(source: string, target: string, items: TranslateBatchItem[]): Promise<Record<string, string>> {
    const url = `${environment.apiBaseUrl}/api/translate/batch/`;
    const res = await firstValueFrom(
      this.http.post<TranslateBatchResponse>(url, {  source,  target,  items,})
    );
    return res?.translations ?? {};
  }
}
