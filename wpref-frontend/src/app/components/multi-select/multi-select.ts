import {
  Component,
  forwardRef,
  Input,
  signal,
} from '@angular/core';
import {
  ControlValueAccessor,
  NG_VALUE_ACCESSOR,
} from '@angular/forms';
import { CommonModule } from '@angular/common';

export interface MultiSelectOption {
  value: number | string;
  label: string;
}

@Component({
  standalone: true,
  selector: 'app-multi-select',
  templateUrl: './multi-select.html',
  styleUrls: ['./multi-select.scss'],
  imports: [CommonModule],
  providers: [
    {
      provide: NG_VALUE_ACCESSOR,
      useExisting: forwardRef(() => MultiSelectComponent),
      multi: true, // ✅ toujours true pour un ControlValueAccessor
    },
  ],
})
export class MultiSelectComponent implements ControlValueAccessor {
  /** Liste des options : [{ value, label }] */
  @Input() options: MultiSelectOption[] = [];

  /** Placeholder si aucune valeur sélectionnée */
  @Input() placeholder: string = 'Sélectionner…';

  /** Afficher les labels sélectionnés (multi) ou juste un compteur */
  @Input() showSelectedLabels: boolean = true;

  /** Mode multiple ou simple */
  @Input() multiple: boolean = true;

  /** Valeur interne sous forme de tableau, même en mode simple */
  selectedValues = signal<(number | string)[]>([]);

  isOpen = signal(false);
  disabled = false;

  // ---- ControlValueAccessor ----
  private onChange: (value: any) => void = () => {};
  private onTouched: () => void = () => {};

  writeValue(value: any): void {
    if (this.multiple) {
      // En mode multiple, on attend un tableau
      if (Array.isArray(value)) {
        this.selectedValues.set(value);
      } else if (value == null) {
        this.selectedValues.set([]);
      } else {
        // fallback : on encapsule une valeur unique dans un tableau
        this.selectedValues.set([value]);
      }
    } else {
      // Mode simple : on attend une valeur scalair (string|number|null)
      if (value == null || value === '') {
        this.selectedValues.set([]);
      } else {
        this.selectedValues.set([value]);
      }
    }
  }

  registerOnChange(fn: any): void {
    this.onChange = fn;
  }

  registerOnTouched(fn: any): void {
    this.onTouched = fn;
  }

  setDisabledState(isDisabled: boolean): void {
    this.disabled = isDisabled;
  }

  // ---- UI helpers ----

  toggleDropdown(): void {
    if (this.disabled) return;
    this.isOpen.update((v) => !v);
    this.onTouched();
  }

  closeDropdown(): void {
    this.isOpen.set(false);
  }

  isSelected(value: number | string): boolean {
    return this.selectedValues().includes(value);
  }

  onOptionToggle(value: number | string): void {
    if (this.disabled) return;

    const current = this.selectedValues();

    if (this.multiple) {
      // ---------- MODE MULTI ----------
      const exists = current.includes(value);
      const updated = exists
        ? current.filter((v) => v !== value)
        : [...current, value];

      this.selectedValues.set(updated);
      this.onChange(updated); // on renvoie un tableau
    } else {
      // ---------- MODE SINGLE ----------
      let updated: (number | string)[];

      if (current.length === 1 && current[0] === value) {
        // clic sur la valeur déjà sélectionnée → on désélectionne
        updated = [];
      } else {
        updated = [value];
      }

      this.selectedValues.set(updated);
      // En mode simple, on renvoie la valeur seule, pas un tableau
      this.onChange(updated[0] ?? null);
      // On referme le dropdown
      this.closeDropdown();
    }
  }

  getSelectedLabelSummary(): string {
    const current = this.selectedValues();

    if (current.length === 0) {
      return this.placeholder;
    }

    if (!this.multiple) {
      // Mode simple → afficher le label de la seule valeur
      const value = current[0];
      const opt = this.options.find((o) => o.value === value);
      return opt?.label ?? this.placeholder;
    }

    // Mode multiple
    if (!this.showSelectedLabels) {
      return `${current.length} sélectionné(s)`;
    }

    const labels = this.options
      .filter((opt) => current.includes(opt.value))
      .map((opt) => opt.label);

    if (labels.length <= 3) {
      return labels.join(', ');
    }
    return `${labels.slice(0, 3).join(', ')} +${labels.length - 3}`;
  }
}
