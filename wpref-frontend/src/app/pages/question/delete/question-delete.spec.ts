import {ComponentFixture, TestBed} from '@angular/core/testing';

import {QuestionDelete} from './question-delete';

describe('QuestionDelete', () => {
  let component: QuestionDelete;
  let fixture: ComponentFixture<QuestionDelete>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [QuestionDelete]
    })
      .compileComponents();

    fixture = TestBed.createComponent(QuestionDelete);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
