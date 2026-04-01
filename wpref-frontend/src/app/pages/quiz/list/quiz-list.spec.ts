import {ComponentFixture, TestBed} from '@angular/core/testing';

import {QuizListPage} from './quiz-list';

describe('QuizListPage', () => {
  let component: QuizListPage;
  let fixture: ComponentFixture<QuizListPage>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [QuizListPage]
    })
      .compileComponents();

    fixture = TestBed.createComponent(QuizListPage);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
