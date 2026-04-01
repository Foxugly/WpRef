import {Component, EventEmitter, Input, OnChanges, Output, SimpleChanges} from '@angular/core';
import {FormsModule} from '@angular/forms';
import {SelectButtonModule} from 'primeng/selectbutton';
import {SupportedLanguage} from '../../../environments/language';

@Component({
  selector: 'app-lang-select',
  standalone: true,
  imports: [FormsModule, SelectButtonModule],
  templateUrl: './lang-select.html',
})
export class LangSelectComponent implements OnChanges {
  @Input() lang!: SupportedLanguage;
  @Output() langChange = new EventEmitter<SupportedLanguage>();

  internalLang: string = 'en';

  langOptions = [
    {label: 'FR', value: 'fr'},
    {label: 'NL', value: 'nl'},
    {label: 'EN', value: 'en'},
  ];

  ngOnChanges(changes: SimpleChanges): void {
    if (changes['lang']) {
      this.internalLang = this.lang;
    }
  }

  onInternalChange(value: string) {
    const code = value as SupportedLanguage;
    this.internalLang = code;
    this.langChange.emit(code);
  }
}
