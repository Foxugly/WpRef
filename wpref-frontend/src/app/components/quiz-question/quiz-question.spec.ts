import { ComponentFixture, TestBed } from '@angular/core/testing';

import { QuizQuestion } from './quiz-question';

describe('QuizQuestion', () => {
  let component: QuizQuestion;
  let fixture: ComponentFixture<QuizQuestion>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [QuizQuestion]
    })
    .compileComponents();

    fixture = TestBed.createComponent(QuizQuestion);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
