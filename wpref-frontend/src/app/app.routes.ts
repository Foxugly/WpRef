import { Routes } from '@angular/router';

// MENU

import { About } from './pages/about/about';

// AUTH
import { authGuard } from '../app/guards/auth.guard';
import { Login } from './pages/auth/login/login';
import { Home } from './pages/home/home';
import { Preferences } from './pages/auth/preferences/preferences';
import { ResetPassword } from './pages/auth/reset-password/reset-password';
import { ChangePassword } from './pages/auth/change-password/change-password';
import { Register } from './pages/auth/register/register';

// SUBJECT
import { SubjectList } from './pages/subject/list/subject-list';
import { SubjectCreate } from './pages/subject/create/subject-create';
import { SubjectEdit } from './pages/subject/edit/subject-edit';
import { SubjectDelete } from './pages/subject/delete/subject-delete';

// QUESTION
import { QuestionList } from './pages/question/list/question-list';
import { QuestionCreate } from './pages/question/create/question-create';
import { QuestionEdit } from './pages/question/edit/question-edit';
import { QuestionDelete } from './pages/question/delete/question-delete';
import { QuestionView } from './pages/question/view/question-view';

// QUIZ
import { QuizSubjectHome } from './pages/quiz/home-subject/home-subject';
import { QuizList } from './pages/quiz/list/quiz-list';

export const routes: Routes = [
  { path: '', redirectTo: 'subjects', pathMatch: 'full' },
  { path: 'login', component: Login },
  { path: 'home', component: Home },
  { path: 'about', component: About },
  { path: 'preferences', component: Preferences },
  { path: 'reset-password', component: ResetPassword},
  { path: 'change-password', component: ChangePassword},
  { path: 'register', component: Register },
  // SUBJECT
  { path: 'subject/list', component: SubjectList , canActivate: [authGuard] },
  { path: 'subject/add', component: SubjectCreate , canActivate: [authGuard] },
  { path: 'subject/:id/edit', component: SubjectEdit , canActivate: [authGuard] },
  { path: 'subject/:id/delete', component: SubjectDelete , canActivate: [authGuard] },
  // QUESTION
  { path: 'question/list', component: QuestionList , canActivate: [authGuard] },
  { path: 'question/add', component: QuestionCreate , canActivate: [authGuard] },
  { path: 'question/:id/edit', component: QuestionEdit , canActivate: [authGuard] },
  { path: 'question/:id/delete', component: QuestionDelete , canActivate: [authGuard] },
  { path: 'question/:id/view', component: QuestionView , canActivate: [authGuard]  },
  // QUIZ
  { path: 'quiz/subject', component: QuizSubjectHome},
  { path: 'quiz/list', component: QuizList},
];
