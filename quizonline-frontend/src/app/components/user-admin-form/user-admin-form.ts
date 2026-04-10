import {CommonModule} from '@angular/common';
import {Component, input, output} from '@angular/core';
import {FormGroup, ReactiveFormsModule} from '@angular/forms';

import {ButtonModule} from 'primeng/button';
import {InputNumberModule} from 'primeng/inputnumber';
import {InputTextModule} from 'primeng/inputtext';
import {MessageModule} from 'primeng/message';
import {PasswordModule} from 'primeng/password';
import {SelectModule} from 'primeng/select';
import {ToggleSwitchModule} from 'primeng/toggleswitch';

type Option<T> = { label: string; value: T };

@Component({
  selector: 'app-user-admin-form',
  standalone: true,
  imports: [
    CommonModule,
    ReactiveFormsModule,
    ButtonModule,
    InputNumberModule,
    InputTextModule,
    MessageModule,
    PasswordModule,
    SelectModule,
    ToggleSwitchModule,
  ],
  templateUrl: './user-admin-form.html',
  styleUrl: './user-admin-form.scss',
})
export class UserAdminFormComponent {
  readonly form = input.required<FormGroup>();
  readonly languageOptions = input.required<Array<Option<string>>>();
  readonly title = input('User');
  readonly submitLabel = input('Save');
  readonly submitError = input<string | null>(null);
  readonly showPassword = input(true);
  readonly showFlags = input(true);

  readonly submitForm = output<void>();
  readonly cancel = output<void>();

  submit(): void {
    this.submitForm.emit();
  }

  onCancel(): void {
    this.cancel.emit();
  }
}
