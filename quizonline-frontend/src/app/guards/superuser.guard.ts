import {inject} from '@angular/core';
import {CanActivateFn, Router, UrlTree} from '@angular/router';
import {catchError, map, of} from 'rxjs';

import {AuthService} from '../services/auth/auth';
import {UserService} from '../services/user/user';

function redirectToLogin(router: Router, url: string): UrlTree {
  return router.createUrlTree(['/login'], {
    queryParams: {next: url},
  });
}

export const superuserGuard: CanActivateFn = (_route, state) => {
  const auth = inject(AuthService);
  const router = inject(Router);
  const userService = inject(UserService);

  if (!auth.isLoggedIn()) {
    return redirectToLogin(router, state.url);
  }

  const authorize = () => (
    userService.currentUser()?.is_superuser === true
      ? true
      : router.createUrlTree(['/quiz/list'])
  );

  if (userService.currentUser()) {
    return authorize();
  }

  return userService.getMe().pipe(
    map(() => authorize()),
    catchError(() => of(redirectToLogin(router, state.url))),
  );
};
