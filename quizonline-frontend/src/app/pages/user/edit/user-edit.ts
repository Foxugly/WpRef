import {Component, inject, OnInit, signal} from '@angular/core';
import {ActivatedRoute, Router} from '@angular/router';
import {ReactiveFormsModule, Validators, NonNullableFormBuilder} from '@angular/forms';

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
  selector: 'app-user-edit-page',
  standalone: true,
  imports: [ReactiveFormsModule, UserAdminFormComponent],
  templateUrl: './user-edit.html',
})
export class UserEditPage implements OnInit {
  private readonly fb = inject(NonNullableFormBuilder);
  private readonly route = inject(ActivatedRoute);
  private readonly router = inject(Router);
  private readonly userService = inject(UserService);

  private userId = 0;
  readonly submitError = signal<string | null>(null);
  readonly languageOptions = LANGUAGE_OPTIONS;
  readonly form = this.fb.group({
    username: this.fb.control({value: '', disabled: true}, [Validators.required]),
    email: this.fb.control(''),
    first_name: this.fb.control(''),
    last_name: this.fb.control(''),
    language: this.fb.control(LanguageEnumDto.Fr),
    password: this.fb.control(''),
    nb_domain_max: this.fb.control(0, [Validators.min(0)]),
    is_active: this.fb.control(true),
    password_change_required: this.fb.control(false),
  });

  ngOnInit(): void {
    const id = Number(this.route.snapshot.paramMap.get('id'));
    if (!Number.isFinite(id)) {
      this.submitError.set('Invalid user id.');
      return;
    }
    this.userId = id;

    this.userService.retrieveAdmin(id).subscribe({
      next: (user) => {
        this.form.patchValue({
          username: user.username,
          email: user.email ?? '',
          first_name: user.first_name ?? '',
          last_name: user.last_name ?? '',
          language: user.language ?? LanguageEnumDto.Fr,
          nb_domain_max: user.nb_domain_max ?? 0,
          is_active: user.is_active,
          password_change_required: user.password_change_required,
        });
      },
      error: (err) => {
        logApiError('user.edit.load', err);
        this.submitError.set(userFacingApiMessage(err, 'Unable to load the user.'));
      },
    });
  }

  save(): void {
    this.submitError.set(null);
    if (this.form.invalid) {
      this.form.markAllAsTouched();
      this.submitError.set('The form contains errors.');
      return;
    }

    const value = this.form.getRawValue();
    this.userService.updateAdmin(this.userId, {
      email: value.email || undefined,
      first_name: value.first_name || undefined,
      last_name: value.last_name || undefined,
      language: value.language,
      password: value.password || undefined,
      is_active: value.is_active,
      password_change_required: value.password_change_required,
      nb_domain_max: value.nb_domain_max,
    }).subscribe({
      next: () => void this.router.navigate(ROUTES.user.list()),
      error: (err) => {
        logApiError('user.edit.submit', err);
        this.submitError.set(userFacingApiMessage(err, 'Unable to update the user.'));
      },
    });
  }

  cancel(): void {
    void this.router.navigate(ROUTES.user.list());
  }
}
