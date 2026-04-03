import {HttpClient} from '@angular/common/http';
import {Injectable} from '@angular/core';
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
import {resolveApiBaseUrl} from '../../shared/api/runtime-api-base-url';

export type DomainTranslationDto = { name: string; description: string;};
export type DomainOption = { name: string; id: number };
export type DomainTranslations = Record<string, DomainTranslationDto>;

@Injectable({
  providedIn: 'root',
})
export class DomainService {
  private readonly apiBaseUrl = `${resolveApiBaseUrl().replace(/\/+$/, '')}/api/domain`;

    constructor(private api: DomainApi, private router: Router, private http: HttpClient) {
  }

  list(params?: { name?: string; search?: string }): Observable<DomainReadDto[]> {
    return this.api.domainList().pipe(
      map((response) => {
        const domains = response.results ?? [];
        const nameFilter = params?.name?.trim().toLowerCase();
        const searchFilter = params?.search?.trim().toLowerCase();

        if (!nameFilter && !searchFilter) {
          return domains;
        }

        return domains.filter((domain) => {
          const translations = Object.values(domain.translations ?? {}) as DomainTranslationDto[];
          const haystack = translations
            .flatMap((translation) => [
              translation.name ?? '',
              translation.description ?? '',
            ])
            .join(' ')
            .toLowerCase();

          const matchesName = !nameFilter || haystack.includes(nameFilter);
          const matchesSearch = !searchFilter || haystack.includes(searchFilter);
          return matchesName && matchesSearch;
        });
      }),
    );
  }

  availableForLinking(): Observable<DomainReadDto[]> {
    return this.http.get<DomainReadDto[]>(`${this.apiBaseUrl}/available-for-linking/`);
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
