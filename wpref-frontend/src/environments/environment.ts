export const environment = {
  production: false,
  apiBaseUrl: 'http://127.0.0.1:8000/api/',
  apiTokenPath : '/api/token/',
  apiPasswordResetPath : '/api/user/password/reset/',
  apiPasswordChangePath : '/api/user/password/change/',
  apiUserPath : '/api/user/',
  apiUserPreferencesPath : '/api/user/me/',
};

export type LangCode = 'en' | 'fr' | 'nl';
