import {Component, EventEmitter, Input, OnChanges, Output, SimpleChanges, ViewChild} from '@angular/core';
import {ButtonModule} from 'primeng/button';
import {Menu} from 'primeng/menu';
import {MenuItem} from 'primeng/api';
import {LanguageEnumDto} from '../../api/generated';
import {SUPPORTED_LANGUAGES, SupportedLanguage} from '../../../environments/language';

@Component({
  selector: 'app-lang-select',
  standalone: true,
  imports: [ButtonModule, Menu],
  templateUrl: './lang-select.html',
  styleUrl: './lang-select.scss',
})
export class LangSelectComponent implements OnChanges {
  @Input() lang!: SupportedLanguage;
  @Output() langChange = new EventEmitter<SupportedLanguage>();
  @ViewChild('langMenu') private readonly langMenu?: Menu;

  internalLang: SupportedLanguage = LanguageEnumDto.En;

  readonly langOptions: Array<{label: string; value: SupportedLanguage}> = SUPPORTED_LANGUAGES.map((language) => ({
    label: this.languageLabel(language),
    value: language,
  }));

  get menuItems(): MenuItem[] {
    return this.langOptions.map((option) => ({
      label: option.label,
      command: () => this.onInternalChange(option.value),
    }));
  }

  ngOnChanges(changes: SimpleChanges): void {
    if (changes['lang']) {
      this.internalLang = this.lang ?? LanguageEnumDto.En;
    }
  }

  toggleMenu(event: Event): void {
    this.langMenu?.toggle(event);
  }

  onInternalChange(value: SupportedLanguage): void {
    this.internalLang = value;
    this.langChange.emit(value);
  }

  private languageLabel(language: SupportedLanguage): string {
    switch (language) {
      case LanguageEnumDto.Fr:
        return 'FR';
      case LanguageEnumDto.Nl:
        return 'NL';
      case LanguageEnumDto.It:
        return 'IT';
      case LanguageEnumDto.Es:
        return 'ES';
      case LanguageEnumDto.En:
      default:
        return 'EN';
    }
  }
}
