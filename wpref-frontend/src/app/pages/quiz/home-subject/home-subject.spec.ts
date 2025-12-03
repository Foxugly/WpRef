import { ComponentFixture, TestBed } from '@angular/core/testing';

import {QuizSubjectHome} from './home-subject';

describe('HomeSubject', () => {
  let component: QuizSubjectHome;
  let fixture: ComponentFixture<QuizSubjectHome>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [QuizSubjectHome]
    })
    .compileComponents();

    fixture = TestBed.createComponent(QuizSubjectHome);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
