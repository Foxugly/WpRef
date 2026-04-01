import {ComponentFixture, TestBed} from '@angular/core/testing';
import {ActivatedRoute, convertToParamMap} from '@angular/router';
import {provideRouter} from '@angular/router';
import {of} from 'rxjs';

import {ResetPasswordConfirmPage} from './reset-password-confirm';
import {AuthService} from '../../../services/auth/auth';

describe('ResetPasswordConfirmPage', () => {
  let component: ResetPasswordConfirmPage;
  let fixture: ComponentFixture<ResetPasswordConfirmPage>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [ResetPasswordConfirmPage],
      providers: [
        provideRouter([]),
        {
          provide: ActivatedRoute,
          useValue: {
            paramMap: of(convertToParamMap({uid: 'abc', token: 'def'})),
          },
        },
        {
          provide: AuthService,
          useValue: {
            confirmPasswordReset: () => of({detail: 'ok'}),
          },
        },
      ],
    }).compileComponents();

    fixture = TestBed.createComponent(ResetPasswordConfirmPage);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
