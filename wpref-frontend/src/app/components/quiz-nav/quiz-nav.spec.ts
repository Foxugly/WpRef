import { ComponentFixture, TestBed } from '@angular/core/testing';

import { QuizNav } from './quiz-nav';

describe('QuizNav', () => {
  let component: QuizNav;
  let fixture: ComponentFixture<QuizNav>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [QuizNav]
    })
    .compileComponents();

    fixture = TestBed.createComponent(QuizNav);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
