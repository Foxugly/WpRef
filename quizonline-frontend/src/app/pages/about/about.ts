import {Component, computed, inject} from '@angular/core';

import {UserService} from '../../services/user/user';
import {getAboutUiText} from './about.i18n';

@Component({
  selector: 'app-about',
  imports: [],
  templateUrl: './about.html',
  styleUrl: './about.css',
})
export class About {
  private readonly userService = inject(UserService);

  protected readonly repositoryUrl = 'https://github.com/Foxugly/QuizOnline';
  protected readonly ui = computed(() => getAboutUiText(this.userService.currentLang));
  protected readonly technicalCardKeys = ['repository', 'backend', 'frontend'] as const;
}
