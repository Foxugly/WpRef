import { ComponentFixture, TestBed } from '@angular/core/testing';

import { SubjectList } from './subject-list';

describe('SubjectList', () => {
  let component: SubjectList;
  let fixture: ComponentFixture<SubjectList>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [SubjectList]
    })
    .compileComponents();

    fixture = TestBed.createComponent(SubjectList);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
