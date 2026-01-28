import { ComponentFixture, TestBed } from '@angular/core/testing';

import { DomainEdit } from './domain-edit';

describe('DomainEdit', () => {
  let component: DomainEdit;
  let fixture: ComponentFixture<DomainEdit>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [DomainEdit]
    })
    .compileComponents();

    fixture = TestBed.createComponent(DomainEdit);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
