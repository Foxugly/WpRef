import {ComponentFixture, TestBed} from '@angular/core/testing';

import {SubjectDelete} from './subject-delete';

describe('SubjectDelete', () => {
  let component: SubjectDelete;
  let fixture: ComponentFixture<SubjectDelete>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [SubjectDelete]
    })
      .compileComponents();

    fixture = TestBed.createComponent(SubjectDelete);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
