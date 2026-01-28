import { ComponentFixture, TestBed } from '@angular/core/testing';

import { DomainCreate } from './domain-create';

describe('DomainCreate', () => {
  let component: DomainCreate;
  let fixture: ComponentFixture<DomainCreate>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [DomainCreate]
    })
    .compileComponents();

    fixture = TestBed.createComponent(DomainCreate);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
