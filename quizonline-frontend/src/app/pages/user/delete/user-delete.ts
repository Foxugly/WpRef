import {Component, inject, OnInit, signal} from '@angular/core';
import {ActivatedRoute, Router} from '@angular/router';

import {ButtonModule} from 'primeng/button';
import {CardModule} from 'primeng/card';
import {MessageModule} from 'primeng/message';

import {ROUTES} from '../../../app.routes-paths';
import {UserService} from '../../../services/user/user';
import {logApiError, userFacingApiMessage} from '../../../shared/api/api-errors';

@Component({
  selector: 'app-user-delete-page',
  standalone: true,
  imports: [ButtonModule, CardModule, MessageModule],
  templateUrl: './user-delete.html',
})
export class UserDeletePage implements OnInit {
  private readonly route = inject(ActivatedRoute);
  private readonly router = inject(Router);
  private readonly userService = inject(UserService);

  readonly userId = signal(0);
  readonly username = signal('');
  readonly submitError = signal<string | null>(null);

  ngOnInit(): void {
    const id = Number(this.route.snapshot.paramMap.get('id'));
    if (!Number.isFinite(id)) {
      this.submitError.set('Invalid user id.');
      return;
    }
    this.userId.set(id);

    this.userService.retrieveAdmin(id).subscribe({
      next: (user) => this.username.set(user.username),
      error: (err) => {
        logApiError('user.delete.load', err);
        this.submitError.set(userFacingApiMessage(err, 'Unable to load the user.'));
      },
    });
  }

  confirmDelete(): void {
    this.submitError.set(null);
    this.userService.deleteAdmin(this.userId()).subscribe({
      next: () => void this.router.navigate(ROUTES.user.list()),
      error: (err) => {
        logApiError('user.delete.submit', err);
        this.submitError.set(userFacingApiMessage(err, 'Unable to delete the user.'));
      },
    });
  }

  cancel(): void {
    void this.router.navigate(ROUTES.user.list());
  }
}
