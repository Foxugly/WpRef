export const environment = {
  production: false,
  apiBaseUrl: 'http://127.0.0.1:8000/api/',
  apiTokenPath : 'token/',
  apiPasswordResetPath : 'user/password/reset/',
  apiPasswordChangePath : 'user/password/change/',
  apiUserPath : 'user/',
  apiUserPreferencesPath : 'user/me/',
  apiSubjectPath : 'subject/',
  apiQuestionPath : 'question/',

};

export type LangCode = 'en' | 'fr' | 'nl';
