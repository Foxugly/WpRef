import {Component, computed, inject, OnInit, signal} from '@angular/core';
import {FormsModule} from '@angular/forms';
import {Router} from '@angular/router';

import {ButtonModule} from 'primeng/button';
import {InputTextModule} from 'primeng/inputtext';
import {PaginatorModule} from 'primeng/paginator';
import {TableModule} from 'primeng/table';

import {ROUTES} from '../../../app.routes-paths';
import {AdminUserDto, UserService} from '../../../services/user/user';
import {logApiError} from '../../../shared/api/api-errors';

type UserListRow = AdminUserDto & {
  fullName: string;
};

@Component({
  selector: 'app-user-list-page',
  standalone: true,
  imports: [FormsModule, ButtonModule, InputTextModule, PaginatorModule, TableModule],
  templateUrl: './user-list.html',
  styleUrl: './user-list.scss',
})
export class UserListPage implements OnInit {
  private readonly userService = inject(UserService);
  private readonly router = inject(Router);

  readonly users = signal<AdminUserDto[]>([]);
  readonly q = signal('');
  readonly rows = 10;
  readonly rowsData = computed<UserListRow[]>(() => {
    const needle = this.q().trim().toLowerCase();
    return this.users()
      .filter((user) => {
        if (!needle) {
          return true;
        }
        const haystack = [
          user.username ?? '',
          user.email ?? '',
          user.first_name ?? '',
          user.last_name ?? '',
        ].join(' ').toLowerCase();
        return haystack.includes(needle);
      })
      .map((user) => ({
        ...user,
        fullName: `${user.first_name ?? ''} ${user.last_name ?? ''}`.trim(),
      }));
  });

  ngOnInit(): void {
    this.load();
  }

  load(): void {
    this.userService.listAdmin().subscribe({
      next: (users) => this.users.set(users),
      error: (err) => {
        logApiError('user.list.load', err);
        this.users.set([]);
      },
    });
  }

  goNew(): void {
    void this.router.navigate(ROUTES.user.add());
  }

  goEdit(userId: number): void {
    void this.router.navigate(ROUTES.user.edit(userId));
  }

  goDelete(userId: number): void {
    void this.router.navigate(ROUTES.user.delete(userId));
  }
}
