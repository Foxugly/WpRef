import {Injectable} from '@angular/core';
import {Router} from '@angular/router';
import {map, Observable} from 'rxjs';

import {ROUTES} from '../../app.routes-paths'
import {
  PatchedSubjectWriteRequestDto, SubjectCreateRequestParams, SubjectDetailDto, SubjectReadDto,
  SubjectWriteRequestDto
} from '../../api/generated';
import{SubjectApi} from '../../api/generated';

@Injectable({
  providedIn: 'root',
})
export class SubjectService {

  constructor(private api: SubjectApi, private router: Router) {
  }

  list(params?: { name?: string; search?: string }): Observable<SubjectReadDto[]> {
    return this.api.subjectList({name:params?.name, search:params?.search});
  }

  retrieve(subjectId: number): Observable<SubjectReadDto> {
    return this.api.subjectRetrieve({ subjectId: subjectId });
  }

  detail(subjectId: number): Observable<SubjectDetailDto> {
    return this.api.subjectDetailsRetrieve({ subjectId: subjectId });
  }

  create(payload: SubjectWriteRequestDto): Observable<SubjectReadDto> {
    return this.api.subjectCreate({subjectWriteRequestDto:payload});
  }

  update(subjectId: number, payload: SubjectWriteRequestDto): Observable<SubjectReadDto> {
    return this.api.subjectUpdate({subjectId:subjectId, subjectWriteRequestDto:payload});
  }

  updatePartial(subjectId: number, payload: PatchedSubjectWriteRequestDto): Observable<SubjectReadDto> {
    return this.api.subjectPartialUpdate({subjectId:subjectId, patchedSubjectWriteRequestDto:payload});
  }

  delete(subjectId: number): Observable<void> {
    return this.api.subjectDestroy({subjectId:subjectId}).pipe(map(() => void 0));
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
    this.router.navigate(ROUTES.subject.edit(subjectId));
  }

  goDelete(subjectId: number): void {
    this.router.navigate(ROUTES.subject.delete(subjectId));
  }
}
