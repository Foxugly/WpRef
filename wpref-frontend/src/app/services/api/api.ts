// src/app/services/api.service.ts
import {Injectable} from '@angular/core';
import {HttpClient, HttpParams } from '@angular/common/http';
import {environment} from '../../../environments/environment';
import {Observable} from 'rxjs';

export interface Subject {
  id: number;
  name: string;
  slug: string;
  description?: string;
}

@Injectable({providedIn: 'root'})
export class Api {
  private base = environment.apiBaseUrl;

  constructor(private http: HttpClient) {}

  // LIST
  listSubject(params?: { search?: string }): Observable<Subject[]> {
    let p = new HttpParams();
    if (params?.search) p = p.set('search', params.search); // si tu ajoutes SearchFilter côté DRF
    return this.http.get<Subject[]>(`${this.base}/subject/`, { params: p });
  }

  // RETRIEVE
  getSubject(id: number): Observable<Subject> {
    return this.http.get<Subject>(`${this.base}/subject/${id}/`);
  }

  // CREATE
  createSubject(payload: Partial<Subject>): Observable<Subject> {
    return this.http.post<Subject>(`${this.base}/subject/add/`, payload);
  }

  // UPDATE
  updateSubject(id: number, payload: Partial<Subject>): Observable<Subject> {
    return this.http.put<Subject>(`${this.base}/subject/${id}/`, payload);
  }

  // DELETE
  deleteSubject(id: number): Observable<void> {
    return this.http.delete<void>(`${this.base}/subjects/${id}/`);
  }
}
