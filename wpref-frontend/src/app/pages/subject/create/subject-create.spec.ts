import { ComponentFixture, TestBed } from '@angular/core/testing';

import { SubjectCreate } from './subject-create';

describe('SubjectCreate', () => {
  let component: SubjectCreate;
  let fixture: ComponentFixture<SubjectCreate>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [SubjectCreate]
    })
    .compileComponents();

    fixture = TestBed.createComponent(SubjectCreate);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
