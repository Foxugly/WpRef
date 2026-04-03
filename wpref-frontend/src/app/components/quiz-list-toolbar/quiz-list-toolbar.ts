import {Component, input, output} from '@angular/core';
import {FormsModule} from '@angular/forms';
import {InputTextModule} from 'primeng/inputtext';
import {ButtonModule} from 'primeng/button';

@Component({
  selector: 'app-quiz-list-toolbar',
  imports: [FormsModule, InputTextModule, ButtonModule],
  templateUrl: './quiz-list-toolbar.html',
  styleUrl: './quiz-list-toolbar.scss',
})
export class QuizListToolbarComponent {
  readonly search = input('');
  readonly canCompose = input(false);
  readonly canQuickCreate = input(false);

  readonly searchChange = output<string>();
  readonly compose = output<void>();
  readonly quickCreate = output<void>();
}
