import { ComponentFixture, TestBed } from '@angular/core/testing';

import { QuestionList } from './question-list';

describe('QuestionList', () => {
  let component: QuestionList;
  let fixture: ComponentFixture<QuestionList>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [QuestionList]
    })
    .compileComponents();

    fixture = TestBed.createComponent(QuestionList);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
