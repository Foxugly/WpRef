import {SubjectList} from './pages/subject/list/subject-list';
import {authGuard} from './guards/auth.guard';
import {SubjectCreate} from './pages/subject/create/subject-create';
import {SubjectEdit} from './pages/subject/edit/subject-edit';
import {SubjectDelete} from './pages/subject/delete/subject-delete';

export let ROUTES = {
  home : () =>['/home'] as const,
  auth : {
    register: () => ['/register/'] as const,
    registerPending: () => ['/register/confirmation'] as const,
    login:() => ['/login/'] as const,
    changePassword: () => ['/change-password'] as const,
    resetPasswordRequest: () => ['/reset-password'] as const,
    resetPasswordConfirm: (uid: string, token: string) => ['/user/reset-password', uid, token] as const,
    confirmEmail: (uid: string, token: string) => ['/user/confirm-email', uid, token] as const,
  },
  question: {
    add: () => ['/question/add'] as const,
    import: () => ['/question/import'] as const,
    edit: (question_id: number) => ['/question', question_id, 'edit' ] as const,
    view: (question_id: number) => ['/question', question_id, 'view' ] as const,
    delete: (question_id: number) => ['/question', question_id, 'delete'] as const,
    list: () => ['/question/list'] as const,

  },
  subject: {
    add: () => ['/subject/add'] as const,
    edit: (subject_id: number) => ['/subject', subject_id, 'edit'] as const,
    delete: (subject_id: number) => ['/subject', subject_id, 'delete'] as const,
    list: () => ['/subject/list'] as const,
  },
  domain : {
    add: () => ['/domain/add'] as const,
    edit: (domain_id: number) => ['/domain', domain_id, 'edit'] as const,
    delete: (domain_id: number) => ['/domain', domain_id, 'delete'] as const,
    list: () => ['/domain/list'] as const,
  },
  user: {
    add: () => ['/user/add'] as const,
    edit: (userId: number) => ['/user', userId, 'edit'] as const,
    delete: (userId: number) => ['/user', userId, 'delete'] as const,
    list: () => ['/user/list'] as const,
  },
  quiz: {
    add: () => ['/quiz/add'] as const,
    quick: () => ['/quiz/quick'] as const,
    list: () => ['/quiz/list'] as const,
    editTemplate: (templateId: number) => ['/quiz/template', templateId, 'edit'] as const,
    deleteTemplate: (templateId: number) => ['/quiz/template', templateId, 'delete'] as const,
    templateResults: (templateId: number) => ['/quiz/template', templateId, 'results'] as const,
    deleteSession: (quizId: number, templateId?: number | null) =>
      templateId != null ? ['/quiz', quizId, 'delete', templateId] as const : ['/quiz', quizId, 'delete'] as const,
    view: (quizId: number) => ['/quiz', quizId] as const,
    questions: (quizId: number) => ['/quiz', quizId, 'questions'] as const,
    alerts: () => ['/messages'] as const,
    alertDetail: (alertId: number) => ['/messages', alertId] as const,
  }
};

//goEdit(id: number) {
//  this.router.navigate(ROUTES.question.edit(id));
//}

