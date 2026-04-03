import {QuizListDto, QuizTemplateDto} from '../../../api/generated';
import {QuizTemplateAssignmentSessionDto} from '../../../services/quiz/quiz';

export interface UserQuizListItem extends QuizListDto {
  earned_score: number | null;
  max_score: number | null;
  status: 'in_progress' | 'answered';
}

export type QuizTemplateListItem = QuizTemplateDto & {
  is_public?: boolean;
  created_by?: number | null;
  domain?: number | null;
  created_by_username?: string;
  ownerLabel?: string;
  canManage?: boolean;
  canAssign?: boolean;
  canEdit?: boolean;
  canDelete?: boolean;
  canViewResults?: boolean;
};

export interface AssignableRecipient {
  id: number;
  username: string;
  role: 'owner' | 'staff' | 'member';
}

export interface QuizListToolbarState {
  search: string;
  isAdmin: boolean;
}

export interface QuizTemplateAssignDialogState {
  users: AssignableRecipient[];
  sessions: QuizTemplateAssignmentSessionDto[];
}
