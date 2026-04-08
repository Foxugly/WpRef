import {TestBed} from '@angular/core/testing';
import {provideRouter} from '@angular/router';
import {signal} from '@angular/core';
import {MessageService} from 'primeng/api';
import {App} from './app';
import {BackendStatusService} from './services/status/status';
import {AuthService} from './services/auth/auth';
import {UserService} from './services/user/user';

describe('App', () => {
  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [App],
      providers: [
        provideRouter([]),
        {
          provide: BackendStatusService,
          useValue: {
            backendUp: signal(true),
            lastError: signal(null),
          },
        },
        {
          provide: AuthService,
          useValue: {
            authenticated: false,
            isLoggedIn: () => false,
            logout: jasmine.createSpy('logout'),
          },
        },
        {
          provide: UserService,
          useValue: {
            currentUser: () => null,
            getMe: () => ({subscribe: () => ({})}),
            currentLang: 'fr',
            isAdmin: () => false,
            setLang: jasmine.createSpy('setLang'),
            updateMeLanguage: () => ({subscribe: () => ({})}),
          },
        },
        MessageService,
      ],
    }).compileComponents();
  });

  it('should create the app', () => {
    const fixture = TestBed.createComponent(App);
    const app = fixture.componentInstance;
    expect(app).toBeTruthy();
  });

  it('should render shell components', () => {
    const fixture = TestBed.createComponent(App);
    fixture.detectChanges();
    const compiled = fixture.nativeElement as HTMLElement;
    expect(compiled.querySelector('app-topmenu')).toBeTruthy();
    expect(compiled.querySelector('app-footer')).toBeTruthy();
  });
});
