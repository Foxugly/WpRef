import {Component, inject, signal} from '@angular/core';
import {ReactiveFormsModule, Validators, NonNullableFormBuilder} from '@angular/forms';
import {Router} from '@angular/router';

import {LanguageEnumDto} from '../../../api/generated';
import {UserAdminFormComponent} from '../../../components/user-admin-form/user-admin-form';
import {ROUTES} from '../../../app.routes-paths';
import {UserService} from '../../../services/user/user';
import {logApiError, userFacingApiMessage} from '../../../shared/api/api-errors';

const LANGUAGE_OPTIONS = [
  {label: 'English', value: LanguageEnumDto.En},
  {label: 'Francais', value: LanguageEnumDto.Fr},
  {label: 'Nederlands', value: LanguageEnumDto.Nl},
  {label: 'Italiano', value: LanguageEnumDto.It},
  {label: 'Espanol', value: LanguageEnumDto.Es},
];

@Component({
  selector: 'app-user-create-page',
  standalone: true,
  imports: [ReactiveFormsModule, UserAdminFormComponent],
  templateUrl: './user-create.html',
})
export class UserCreatePage {
  private readonly fb = inject(NonNullableFormBuilder);
  private readonly userService = inject(UserService);
  private readonly router = inject(Router);

  readonly submitError = signal<string | null>(null);
  readonly languageOptions = LANGUAGE_OPTIONS;
  readonly form = this.fb.group({
    username: this.fb.control('', [Validators.required]),
    email: this.fb.control(''),
    first_name: this.fb.control(''),
    last_name: this.fb.control(''),
    language: this.fb.control(LanguageEnumDto.Fr),
    password: this.fb.control('', [Validators.required]),
    nb_domain_max: this.fb.control(0, [Validators.min(0)]),
    is_active: this.fb.control(true),
    password_change_required: this.fb.control(false),
  });

  save(): void {
    this.submitError.set(null);
    if (this.form.invalid) {
      this.form.markAllAsTouched();
      this.submitError.set('The form contains errors.');
      return;
    }

    const value = this.form.getRawValue();
    this.userService.createAdmin({
      username: value.username,
      email: value.email || undefined,
      first_name: value.first_name || undefined,
      last_name: value.last_name || undefined,
      language: value.language,
      password: value.password,
      nb_domain_max: value.nb_domain_max,
    }).subscribe({
      next: () => void this.router.navigate(ROUTES.user.list()),
      error: (err) => {
        logApiError('user.create.submit', err);
        this.submitError.set(userFacingApiMessage(err, 'Unable to create the user.'));
      },
    });
  }

  cancel(): void {
    void this.router.navigate(ROUTES.user.list());
  }
}
