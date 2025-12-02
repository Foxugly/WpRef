import {Injectable} from '@angular/core';
import {HttpClient} from '@angular/common/http';
import {Router} from '@angular/router';
import {Observable} from 'rxjs';
import {environment} from '../../../environments/environment';
import {Question} from '../question/question'

export interface Subject {
  id: number;
  name: string;
  slug: string;
  description: string;
  questions?: Question[];
}


@Injectable({
  providedIn: 'root',
})
export class SubjectService {
  private base = environment.apiBaseUrl;
  private subjectPath = environment.apiSubjectPath;

  constructor(private http: HttpClient, private router: Router) {
  }

  list(params?: { search?: string }): Observable<Subject[]> {
    return this.http.get<Subject[]>(
      `${this.base}${this.subjectPath}`,
      {
        params: params?.search ? {search: params.search} : {}
      }
    );
  }

  retrieve(id: number): Observable<Subject> {
    return this.http.get<Subject>(`${this.base}${this.subjectPath}${id}/`);
  }

  create(data: Partial<Subject>): Observable<Subject> {
    return this.http.post<Subject>(`${this.base}${this.subjectPath}`, data);
  }

  update(id: number, data: Partial<Subject>): Observable<Subject> {
    return this.http.put<Subject>(`${this.base}${this.subjectPath}${id}/`, data);
  }

  delete(id: number): Observable<void> {
    return this.http.delete<void>(`${this.base}${this.subjectPath}${id}/`);
  }

  goQuestionNew(): void {
    this.router.navigate(['/question/add']);
  }

  goNew(): void {
    this.router.navigate(['/subject/add']);
  }

  goList(): void {
    this.router.navigate(['/subject/list']);
  }

  goBack(): void {
    this.router.navigate(['/subject/list']);
  }

  goEdit(id: number): void {
    this.router.navigate(['/subject', id, 'edit']);
  }

  goDelete(id: number): void {
    this.router.navigate(['/subject', id, 'delete']);
  }
}
