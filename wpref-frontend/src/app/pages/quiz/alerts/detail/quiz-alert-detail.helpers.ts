import {LanguageEnumDto} from '../../../../api/generated';
import {QuizAlertThreadDetailDto} from '../../../../services/quiz-alert/quiz-alert';

export function quizAlertDateLocale(lang: LanguageEnumDto): string {
  switch (lang) {
    case LanguageEnumDto.Fr:
      return 'fr-BE';
    case LanguageEnumDto.Nl:
      return 'nl-BE';
    case LanguageEnumDto.It:
      return 'it-IT';
    case LanguageEnumDto.Es:
      return 'es-ES';
    case LanguageEnumDto.En:
    default:
      return 'en-US';
  }
}

export function formatQuizAlertMessageDate(value: string, lang: LanguageEnumDto): string {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return value;
  }

  return new Intl.DateTimeFormat(quizAlertDateLocale(lang), {
    dateStyle: 'medium',
    timeStyle: 'short',
  }).format(date);
}

export function isClosedThread(thread: QuizAlertThreadDetailDto | null): boolean {
  return thread?.status === 'closed';
}

export function canShowComposer(thread: QuizAlertThreadDetailDto | null): boolean {
  return Boolean(thread && (thread.can_reply || thread.can_manage));
}

export function canSendReply(thread: QuizAlertThreadDetailDto | null): boolean {
  return Boolean(thread && thread.status === 'open' && thread.can_reply);
}
