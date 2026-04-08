import { ComponentFixture, TestBed } from '@angular/core/testing';
import {MessageService} from 'primeng/api';

import { DomainCreate } from './domain-create';

describe('DomainCreate', () => {
  let component: DomainCreate;
  let fixture: ComponentFixture<DomainCreate>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [DomainCreate],
      providers: [MessageService],
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
