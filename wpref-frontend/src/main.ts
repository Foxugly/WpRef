import {provideZoneChangeDetection} from "@angular/core";
// src/main.ts
import {bootstrapApplication} from '@angular/platform-browser';
import {App} from './app/app';
import {appConfig} from './app/app.config';
import {environment} from './environments/environment';

(window as any).__APP__ = {
  name: environment.appName,
  author: environment.author,
  year: environment.year,
  logoSvg : environment.logoSvg,
  logoIco : environment.logoIco,
  logoPng : environment.logoPng,
};

bootstrapApplication(App, {...appConfig, providers: [provideZoneChangeDetection(), ...appConfig.providers]})
  .catch(err => console.error(err));
