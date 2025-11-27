import { ComponentFixture, TestBed } from '@angular/core/testing';

import { LangSelect } from './lang-select';

describe('LangSelect', () => {
  let component: LangSelect;
  let fixture: ComponentFixture<LangSelect>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [LangSelect]
    })
    .compileComponents();

    fixture = TestBed.createComponent(LangSelect);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
