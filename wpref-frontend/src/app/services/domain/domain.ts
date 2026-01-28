import {Component, Injectable} from '@angular/core';
import {Router} from '@angular/router';
import {map, Observable} from 'rxjs';
import {ROUTES} from '../../app.routes-paths';
import {
  DomainApi,
  DomainDetailDto,
  DomainReadDto,
  DomainWriteRequestDto,
  PatchedDomainPartialRequestDto
} from '../../api/generated';

export type DomainTranslationDto = { name: string; description: string;};
export type DomainOption = { name: string; id: number };
export type DomainTranslations = Record<string, DomainTranslationDto>;

@Injectable({
  providedIn: 'root',
})
export class DomainService {
    constructor(private api: DomainApi, private router: Router) {
  }

  list(params?: { name?: string; search?: string }): Observable<DomainReadDto[]> {
    // return this.api.domainList({name:params?.name, search:params?.search}); TODO
    return this.api.domainList();
  }

  retrieve(domainId: number): Observable<DomainReadDto> {
    return this.api.domainRetrieve({ domainId: domainId });
  }

  detail(domainId: number): Observable<DomainDetailDto> {
    return this.api.domainDetailsRetrieve({ domainId: domainId });
  }

  create(payload: DomainWriteRequestDto): Observable<DomainReadDto> {
    return this.api.domainCreate({domainWriteRequestDto:payload});
  }

  update(domainId: number, payload: DomainWriteRequestDto): Observable<DomainReadDto> {
    return this.api.domainUpdate({domainId:domainId, domainWriteRequestDto:payload});
  }

  updatePartial(domainId: number, payload:PatchedDomainPartialRequestDto): Observable<DomainReadDto> {
    return this.api.domainPartialUpdate({domainId:domainId, patchedDomainPartialRequestDto:payload});
  }

  delete(domainId: number): Observable<void> {
    return this.api.domainDestroy({domainId:domainId}).pipe(map(() => void 0));
  }

  goNew(): void {
    this.router.navigate(ROUTES.domain.add());
  }

  goList(): void {
    this.router.navigate(ROUTES.domain.list());
  }

  goBack(): void {
    this.router.navigate(ROUTES.domain.list());
  }

  goEdit(domainId: number): void {
    this.router.navigate(ROUTES.domain.edit(domainId));
  }

  goDelete(domainId: number): void {
    this.router.navigate(ROUTES.domain.delete(domainId));
  }
}
