import { Routes } from '@angular/router';
import { Login } from './pages/login/login';
import { About } from './pages/about/about';
import { SubjectList } from './pages/subject/list/subject-list/subject-list';
import { SubjectCreate } from './pages/subject/create/subject-create/subject-create';
import { SubjectEdit } from './pages/subject/edit/subject-edit/subject-edit';
import { SubjectDelete } from './pages/subject/delete/subject-delete/subject-delete';

import { Questions } from './pages/questions/questions';

import { authGuard } from '../app/guards/auth.guard';

export const routes: Routes = [
  { path: '', redirectTo: 'subjects', pathMatch: 'full' },
  { path: 'login', component: Login },
  { path: 'about', component: About },

  { path: 'subject/list', component: SubjectList , canActivate: [authGuard] },
  { path: 'subject/add', component: SubjectCreate , canActivate: [authGuard] },
  { path: 'subject/:id/edit', component: SubjectEdit , canActivate: [authGuard] },
  { path: 'subject/:id/delete', component: SubjectDelete , canActivate: [authGuard] },

  { path: 'questions/:slug', component: Questions, canActivate: [authGuard] },
];
