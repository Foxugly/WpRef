import {Component, EventEmitter, Input, OnChanges, Output, SimpleChanges} from '@angular/core';

import {FormsModule} from '@angular/forms';
import {SelectButtonModule} from 'primeng/selectbutton';
import {SupportedLanguage} from '../../../environments/language'; // adapte le chemin si besoin

@Component({
  selector: 'app-lang-select',
  standalone: true,
  imports: [FormsModule, SelectButtonModule],
  templateUrl: './lang-select.html',
  styleUrl: './lang-select.scss',
})
export class LangSelectComponent implements OnChanges {
  /** Langue actuelle ( venant du parent ) */
  @Input() lang!: SupportedLanguage;

  /** Événement vers le parent quand la langue change */
  @Output() langChange = new EventEmitter<SupportedLanguage>();

  /** Valeur liée au p-selectbutton (string) */
  internalLang: string = 'en';

  /** Options du p-selectbutton */
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

