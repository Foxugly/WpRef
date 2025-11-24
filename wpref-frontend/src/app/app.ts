import { Component, signal, computed, inject } from '@angular/core';
import { RouterOutlet } from '@angular/router';
import { TopmenuComponent } from './components/topmenu/topmenu';
import { BackendStatusService } from './services/status/status';

@Component({
  selector: 'app-root',
  imports: [RouterOutlet, TopmenuComponent],
  templateUrl: './app.html',
  //template: `
  //  <app-topmenu></app-topmenu>
  //  <main>
  //    <router-outlet></router-outlet>
  //  </main>
  //    `,
  styleUrl: './app.scss'
})
export class App {
  status = inject(BackendStatusService);
  backendDown = computed(() => this.status.backendUp() === false);
  protected readonly title = signal('wpref-frontend');
}
