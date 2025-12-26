import {Injectable} from '@angular/core';
import {Router} from '@angular/router';
import {map, Observable} from 'rxjs';

import {
  SubjectApi, SubjectCreateRequestParams, SubjectPartialUpdateRequestParams,
  SubjectUpdateRequestParams
} from '../../api/generated/api/subject.service';
import { SubjectDto } from '../../api/generated/model/subject';
import {ROUTES} from '../../app.routes-paths'

export type SubjectWritePayload = Pick<SubjectDto, 'name' | 'slug' | 'description'>;
type SubjectUpdateBody = Omit<SubjectUpdateRequestParams, 'subjectId'>;
type SubjectPartialBody = Omit<SubjectPartialUpdateRequestParams, 'subjectId'>;

@Injectable({
  providedIn: 'root',
})
export class SubjectService {

  constructor(private api: SubjectApi, private router: Router) {
  }

  list(params?: { search?: string }): Observable<SubjectDto[]> {
    return this.api.subjectList({search: params?.search,});
  }

  retrieve(subjectId: number): Observable<SubjectDto> {
    return this.api.subjectRetrieve({subjectId});
  }

  create(payload: SubjectWritePayload): Observable<SubjectDto> {
    const req: SubjectCreateRequestParams = { subjectDto: payload as any };
    return this.api.subjectCreate(req);
  }

  update(subjectId: number, payload: SubjectWritePayload): Observable<SubjectDto> {
    const body: SubjectUpdateBody = { subjectDto: payload as any };
    return this.api.subjectUpdate({ subjectId, ...body });
  }

  updatePartial(subjectId: number, payload: SubjectPartialBody): Observable<SubjectDto> {
    const body: SubjectPartialBody = payload;
    return this.api.subjectPartialUpdate({ subjectId, ...body });
  }

  delete(subjectId: number): Observable<void> {
    return this.api.subjectDestroy({ subjectId }).pipe(map(() => void 0));
  }

  goQuestionNew(): void {
    this.router.navigate(ROUTES.question.add());
  }

  goNew(): void {
    this.router.navigate(ROUTES.subject.add());
  }

  goList(): void {
    this.router.navigate(ROUTES.subject.list());
  }

  goBack(): void {
    this.router.navigate(ROUTES.subject.list());
  }

  goEdit(subjectId: number): void {
    this.router.navigate(ROUTES.question.edit(subjectId));
  }

  goDelete(subjectId: number): void {
    this.router.navigate(ROUTES.question.delete(subjectId));
  }
}
