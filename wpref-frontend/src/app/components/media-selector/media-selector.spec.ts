import {ComponentFixture, TestBed} from '@angular/core/testing';

import {MediaSelector} from './media-selector';

describe('MediaSelector', () => {
  let component: MediaSelector;
  let fixture: ComponentFixture<MediaSelector>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [MediaSelector]
    })
      .compileComponents();

    fixture = TestBed.createComponent(MediaSelector);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
