import {CustomUserReadDto, QuizListDto, QuizTemplateDto} from '../../../api/generated';
import {QuizTemplateAssignmentSessionDto} from '../../../services/quiz/quiz';

export interface UserQuizListItem extends QuizListDto {
  earned_score: number | null;
  max_score: number | null;
  status: 'in_progress' | 'answered';
}

export type QuizTemplateListItem = QuizTemplateDto & {
  is_public?: boolean;
  created_by?: number | null;
};

export interface QuizListToolbarState {
  search: string;
  isAdmin: boolean;
}

export interface QuizTemplateAssignDialogState {
  users: CustomUserReadDto[];
  sessions: QuizTemplateAssignmentSessionDto[];
}
