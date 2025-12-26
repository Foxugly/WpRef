export const environment = {
  production: false,
  apiBaseUrl: 'http://127.0.0.1:8000/api/',
  apiTokenPath: 'token/',
  apiTokenRefreshPath: 'token/refresh/',
  apiPasswordResetPath: 'user/password/reset/',
  apiPasswordChangePath: 'user/password/change/',
  apiUserPath: 'user/',
  apiUserPreferencesPath: 'user/me/',
  apiSubjectPath: 'subject/',
  apiQuestionPath: 'question/',
  apiQuizPath: 'quiz/',

};

export type LangCode = 'en' | 'fr' | 'nl';
