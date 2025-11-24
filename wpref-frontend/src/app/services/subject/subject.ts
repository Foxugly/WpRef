import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Router } from '@angular/router';
import { Observable } from 'rxjs';
import {environment, LangCode} from '../../../environments/environment';

export interface Subject {
  id: number;
  name: string;
  slug: string;
  description: string;
}


@Injectable({
  providedIn: 'root',
})
export class SubjectService {
  private base = environment.apiBaseUrl;
  private subjectPath = environment.apiSubjectPath;

  constructor(private http: HttpClient, private router: Router) {}

  listSubject(params?: { search?: string }): Observable<Subject[]> {
    return this.http.get<Subject[]>(`${this.base}${this.subjectPath}`);
  }

  getSubject(id: number): Observable<Subject> {
    return this.http.get<Subject>(`${this.base}${this.subjectPath}${id}/`);
  }

  createSubject(data: Partial<Subject>): Observable<Subject> {
    return this.http.post<Subject>(`${this.base}${this.subjectPath}`, data);
  }

  updateSubject(id: number, data: Partial<Subject>): Observable<Subject> {
  return this.http.put<Subject>(`${this.base}${this.subjectPath}${id}/`, data);
}

  deleteSubject(id: number): Observable<void> {
    return this.http.delete<void>(`${this.base}${this.subjectPath}${id}/`);
  }
}
