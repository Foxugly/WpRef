import { Injectable } from '@angular/core';
import {Observable} from 'rxjs';
import {DomainApi, DomainReadDto, LanguageApi, LanguageEnumDto, LanguageReadDto} from '../../api/generated';
import {Router} from '@angular/router';
import {LangCode} from '../translation/translation';

@Injectable({
  providedIn: 'root',
})
export class LanguageService {
  constructor(private api: LanguageApi, private router: Router) {
  }
  list(params?: { name?: string; search?: string }): Observable<LanguageReadDto[]> {
    return this.api.langList();
  }
}
