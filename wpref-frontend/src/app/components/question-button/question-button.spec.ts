import {ComponentFixture, TestBed} from '@angular/core/testing';

import {QuestionButton} from './question-button';

describe('QuestionButton', () => {
  let component: QuestionButton;
  let fixture: ComponentFixture<QuestionButton>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [QuestionButton]
    })
      .compileComponents();

    fixture = TestBed.createComponent(QuestionButton);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
