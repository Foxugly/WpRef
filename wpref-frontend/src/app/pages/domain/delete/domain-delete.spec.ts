import { ComponentFixture, TestBed } from '@angular/core/testing';

import { DomainDelete } from './domain-delete';

describe('DomainDelete', () => {
  let component: DomainDelete;
  let fixture: ComponentFixture<DomainDelete>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [DomainDelete]
    })
    .compileComponents();

    fixture = TestBed.createComponent(DomainDelete);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
