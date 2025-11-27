import { Component, OnInit } from '@angular/core';

import { Router, RouterLink, RouterLinkActive } from '@angular/router';

import { MenuModule } from 'primeng/menu';
import { ButtonModule } from 'primeng/button';
import { MenuItem } from 'primeng/api';

import { AuthService } from '../../services/auth/auth';

@Component({
  selector: 'app-user-menu',
  standalone: true,
  imports: [
    RouterLink,
    RouterLinkActive,
    MenuModule,
    ButtonModule
],
  templateUrl: './user-menu.html',
  styleUrl: './user-menu.scss',
})
export class UserMenuComponent implements OnInit {
  items: MenuItem[] = [];

  constructor(
    public auth: AuthService,
    private router: Router,
  ) {}

  ngOnInit(): void {
    this.buildItems();
  }

  private buildItems() {
    if (!this.auth.isLoggedIn()) {
      this.items = [];
      return;
    }

    this.items = [
      {
        label: 'Préférences',
        icon: 'pi pi-cog',
        command: () => this.goPreferences(),
      },
      {
        label: 'Changer de mot de passe',
        icon: 'pi pi-key',
        command: () => this.goChangePassword(),
      },
      {
        label: 'Déconnexion',
        icon: 'pi pi-sign-out',
        command: () => this.logout(),
      },
    ];
  }

  goPreferences() {
    this.router.navigate(['/preferences']);
  }

  goChangePassword() {
    this.router.navigate(['/change-password']);
  }

  logout() {
    this.auth.logout();
    this.router.navigate(['/login']);
  }
}
