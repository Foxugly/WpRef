import {Component} from '@angular/core';
import {CommonModule} from '@angular/common';
import {MatMenuModule} from '@angular/material/menu';
import {MatButtonModule} from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import {RouterLink, Router} from '@angular/router';
import {AuthService} from '../../services/auth';
import {MatButtonToggleModule} from '@angular/material/button-toggle';

@Component({
  selector: 'app-topmenu',
  standalone: true,
  imports: [CommonModule, RouterLink, MatButtonModule, MatMenuModule, MatButtonToggleModule, MatIconModule],
  templateUrl: './topmenu.html',
  styleUrl: './topmenu.scss'
})
export class TopmenuComponent {
  showUserMenu = false;

  constructor(public auth: AuthService, private router: Router) {}

  toggleUserMenu() {
    this.showUserMenu = !this.showUserMenu;
  }

  logout() {
    this.auth.logout();
    this.showUserMenu = false;
    this.router.navigate(['/login']);
  }

  goPreferences() {
    this.showUserMenu = false;
    this.router.navigate(['/preferences']);
  }
}
