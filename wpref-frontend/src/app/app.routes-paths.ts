import {SubjectList} from './pages/subject/list/subject-list';
import {authGuard} from './guards/auth.guard';
import {SubjectCreate} from './pages/subject/create/subject-create';
import {SubjectEdit} from './pages/subject/edit/subject-edit';
import {SubjectDelete} from './pages/subject/delete/subject-delete';

export let ROUTES = {
  question: {
    add: () => ['/question/add'] as const,
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
  }
};

//goEdit(id: number) {
//  this.router.navigate(ROUTES.question.edit(id));
//}

