import { ComponentFixture, TestBed } from '@angular/core/testing';

import { Topmenu } from './topmenu';

describe('Topmenu', () => {
  let component: Topmenu;
  let fixture: ComponentFixture<Topmenu>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [Topmenu]
    })
    .compileComponents();

    fixture = TestBed.createComponent(Topmenu);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
