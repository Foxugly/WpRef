// src/app/components/media-selector/media-selector.ts
import {Component, forwardRef, Input, signal,} from '@angular/core';
import {ControlValueAccessor, FormsModule, NG_VALUE_ACCESSOR,} from '@angular/forms';
import {CommonModule} from '@angular/common';
import {ButtonModule} from 'primeng/button';
import {FileUploadModule} from 'primeng/fileupload';
import {TabsModule} from 'primeng/tabs';
import {InputTextModule} from 'primeng/inputtext';
import {DividerModule} from 'primeng/divider';
import {TagModule} from 'primeng/tag';
import {TooltipModule} from 'primeng/tooltip'; // pour [tooltip], optionnel


export interface MediaSelectorValue {
  id?: number;
  kind: 'image' | 'video' | 'external';
  file?: File | string | null;
  external_url?: string | null;
  sort_order: number;
}

@Component({
  standalone: true,
  selector: 'app-media-selector',
  templateUrl: './media-selector.html',
  styleUrls: ['./media-selector.scss'],
  imports: [CommonModule, ButtonModule, FileUploadModule, TabsModule, InputTextModule, FormsModule, DividerModule,
    TagModule, TooltipModule,],
  providers: [
    {
      provide: NG_VALUE_ACCESSOR,
      useExisting: forwardRef(() => MediaSelectorComponent),
      multi: true,
    },
  ],
})
export class MediaSelectorComponent implements ControlValueAccessor {
  /** URL saisie pour YouTube / externe dans l’onglet 2 */
  youtubeUrl = signal<string>('');
  @Input() multiple = true;
  @Input() placeholderYoutube = 'https://www.youtube.com/watch?v=...';
  disabled = false;

  /** Valeur interne = liste de médias */
  private _items = signal<MediaSelectorValue[]>([]);

  get items(): MediaSelectorValue[] {
    return this._items();
  }

  writeValue(value: MediaSelectorValue[] | null): void {
    const list = Array.isArray(value) ? value : [];
    // normalise le sort_order
    const normalized = list.map((m, idx) => ({
      ...m,
      sort_order: m.sort_order ?? idx + 1,
    }));
    this._items.set(normalized);
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

  isFile(value: any): boolean {
    return value instanceof File;
  }

  // ----- Helpers -----

  getMediaLabel(m: MediaSelectorValue): string {
    if (m.file instanceof File) {
      return m.file.name;
    }
    if (typeof m.file === 'string') {
      return m.file;
    }
    if (typeof m.external_url === 'string') {
      return m.external_url;
    }
    return '(sans nom)';
  }

  onFilesSelected(event: any): void {
    if (this.disabled) return;

    const files: File[] = event.files || event.target?.files || [];
    if (!files.length) return;

    const current = [...this._items()];

    for (const file of files) {
      const mime = file.type || '';
      let kind: 'image' | 'video';

      if (mime.startsWith('video/')) {
        kind = 'video';
      } else if (mime.startsWith('image/')) {
        kind = 'image';
      } else {
        // si tu veux strictement image/vidéo, on skip les autres
        continue;
      }

      current.push({
        kind,
        file,               // ⬅️ File ici ; plus tard tu testeras instanceof File
        external_url: null,
        sort_order: current.length + 1,
      });
    }

    this._items.set(current);
    this.propagate();
  }

  removeMedia(index: number): void {
    if (this.disabled) return;
    const current = [...this._items()];
    current.splice(index, 1);
    this._items.set(current);
    this.propagate();
  }

  addYoutubeLink(): void {
    if (this.disabled) return;
    const url = this.youtubeUrl().trim();
    if (!url) return;

    const current = [...this._items()];

    current.push({
      kind: 'external',
      file: null,
      external_url: url,
      sort_order: current.length + 1,
    });

    this.youtubeUrl.set('');
    this._items.set(current);
    this.propagate();
  }

  // ----- Upload de fichiers (onglet Médias) -----

  trackByIndex(_index: number, _item: MediaSelectorValue): number {
    return _index;
  }

  // ----- ControlValueAccessor -----
  private onChange: (value: MediaSelectorValue[]) => void = () => {
  };

  // ----- Lien YouTube / externe (onglet Lien) -----

  private onTouched: () => void = () => {
  };

  private propagate(): void {
    // recalcule les sort_order avant de remonter la valeur
    const normalized = this._items().map((m, idx) => ({
      ...m,
      sort_order: idx + 1,
    }));
    this._items.set(normalized);
    this.onChange(normalized);
    this.onTouched();
  }
}
