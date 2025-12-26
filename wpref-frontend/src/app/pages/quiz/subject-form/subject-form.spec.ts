import {ComponentFixture, TestBed} from '@angular/core/testing';

import {QuizSubjectForm} from './subject-form';

describe('QuizSubjectForm', () => {
  let component: QuizSubjectForm;
  let fixture: ComponentFixture<QuizSubjectForm>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [QuizSubjectForm]
    })
      .compileComponents();

    fixture = TestBed.createComponent(QuizSubjectForm);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
