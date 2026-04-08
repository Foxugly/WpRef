import {Component, computed, effect, inject, OnInit} from '@angular/core';
import {Router, RouterOutlet} from '@angular/router';
import {TopMenuComponent} from './components/topmenu/topmenu';
import {BackendStatusService} from './services/status/status';
import {FooterComponent} from './components/footer/footer';
import {AuthService} from './services/auth/auth';
import {UserService} from './services/user/user';
import {logApiError} from './shared/api/api-errors';
import {requiredSessionRedirect} from './shared/auth/session-access-policy';
import {ROUTES} from './app.routes-paths';
import {ToastModule} from 'primeng/toast';

@Component({
  selector: 'app-root',
  imports: [RouterOutlet, TopMenuComponent, FooterComponent, ToastModule],
  templateUrl: './app.html',
  //template: `
  //  <app-topmenu></app-topmenu>
  //  <main>
  //    <router-outlet></router-outlet>
  //  </main>
  //    `,
  styleUrl: './app.scss'
})
export class App implements OnInit {
  status = inject(BackendStatusService);
  backendDown = computed(() => this.status.backendUp() === false);
  private readonly authService = inject(AuthService);
  private readonly userService = inject(UserService);
  private readonly router = inject(Router);
  //protected readonly title = signal('quizonline-frontend');

  constructor() {
    effect(() => {
      const redirect = requiredSessionRedirect(
        this.userService.currentUser(),
        this.router.url,
        {
          authenticated: this.authService.authenticated,
          requiresEmailConfirmation: (user) => this.userService.shouldConfirmEmail(user),
          requiresPasswordChange: (user) => this.userService.shouldForcePasswordChange(user),
        },
      );
      if (!redirect || redirect.kind !== 'login') {
        return;
      }

      this.authService.logout();
      void this.router.navigate(ROUTES.auth.login(), {
        queryParams: redirect.queryParams,
      });
    });

    effect(() => {
      const redirect = requiredSessionRedirect(
        this.userService.currentUser(),
        this.router.url,
        {
          authenticated: this.authService.authenticated,
          requiresEmailConfirmation: (user) => this.userService.shouldConfirmEmail(user),
          requiresPasswordChange: (user) => this.userService.shouldForcePasswordChange(user),
        },
      );
      if (!redirect || redirect.kind !== 'change-password') {
        return;
      }

      void this.router.navigate(ROUTES.auth.changePassword(), {
        queryParams: redirect.queryParams,
      });
    });
  }

  ngOnInit(): void {
    if (!this.authService.authenticated || this.userService.currentUser()) {
      return;
    }

    this.userService.getMe().subscribe({
      error: (error) => {
        logApiError('app.session-rehydrate', error);
        this.authService.logout();
      },
    });
  }
}
