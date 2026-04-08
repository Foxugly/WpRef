import {CommonModule} from '@angular/common';
import {Component, computed, inject, OnInit, signal} from '@angular/core';
import {firstValueFrom} from 'rxjs';

import {ButtonModule} from 'primeng/button';
import {CardModule} from 'primeng/card';
import {FileUploadModule} from 'primeng/fileupload';
import {MessageService} from 'primeng/api';

import {
  LanguageEnumDto,
  LocalizedAnswerOptionTranslationRequestDto,
  LocalizedQuestionTranslationRequestDto,
  QuestionAnswerOptionWritePayloadRequestDto,
  QuestionWritePayloadRequestDto,
} from '../../../api/generated';
import {QuestionService} from '../../../services/question/question';
import {UserService} from '../../../services/user/user';

type QuestionImportFile = {
  questions: QuestionWritePayloadRequestDto[];
};

@Component({
  standalone: true,
  selector: 'app-question-import',
  templateUrl: './question-import.html',
  styleUrl: './question-import.scss',
  imports: [
    CommonModule,
    ButtonModule,
    CardModule,
    FileUploadModule,
  ],
})
export class QuestionImport implements OnInit {
  readonly text = computed(() => this.getText());
  readonly hasValidFile = computed(() => this.validationErrors().length === 0 && this.questions().length > 0);

  importing = signal(false);
  selectedFileName = signal<string | null>(null);
  questions = signal<QuestionWritePayloadRequestDto[]>([]);
  validationErrors = signal<string[]>([]);

  private questionService = inject(QuestionService);
  private userService = inject(UserService);
  private messageService = inject(MessageService);
  private currentLang = signal<LanguageEnumDto>(LanguageEnumDto.En);

  ngOnInit(): void {
    this.currentLang.set(this.userService.currentLang ?? LanguageEnumDto.En);
  }

  goBack(): void {
    this.questionService.goList();
  }

  cancel(): void {
    this.questionService.goList();
  }

  async onFileSelected(event: { files?: File[] }): Promise<void> {
    const file = event.files?.[0];
    if (!file) {
      return;
    }

    this.selectedFileName.set(file.name);

    try {
      const content = await file.text();
      const raw = JSON.parse(content) as unknown;
      const {questions, errors} = this.parseImportFile(raw);

      this.questions.set(questions);
      this.validationErrors.set(errors);

      if (errors.length === 0) {
        this.showToast('success', this.text().formatValid, this.text().fileValidated(questions.length));
      } else {
        this.showToast('error', this.text().formatInvalid, errors[0]);
      }
    } catch {
      this.questions.set([]);
      this.validationErrors.set([this.text().invalidJson]);
      this.showToast('error', this.text().formatInvalid, this.text().invalidJson);
    }
  }

  clearSelection(): void {
    this.selectedFileName.set(null);
    this.questions.set([]);
    this.validationErrors.set([]);
  }

  downloadExample(): void {
    const blob = new Blob([JSON.stringify(this.buildExampleFile(), null, 2)], {
      type: 'application/json;charset=utf-8',
    });
    const url = URL.createObjectURL(blob);
    const anchor = document.createElement('a');
    anchor.href = url;
    anchor.download = 'question-import-example.json';
    anchor.click();
    URL.revokeObjectURL(url);
  }

  async importQuestions(): Promise<void> {
    if (!this.hasValidFile() || this.importing()) {
      return;
    }

    this.importing.set(true);
    const failures: string[] = [];
    let successCount = 0;

    try {
      for (let index = 0; index < this.questions().length; index += 1) {
        const question = this.questions()[index];
        try {
          await firstValueFrom(this.questionService.create(question));
          successCount += 1;
        } catch {
          failures.push(this.text().importFailure(index + 1));
        }
      }

      if (failures.length === 0) {
        this.showToast('success', this.text().importDone, this.text().importSuccess(successCount));
        this.questionService.goList();
        return;
      }

      this.showToast(
        successCount > 0 ? 'warn' : 'error',
        this.text().importPartialTitle,
        successCount > 0
          ? this.text().importPartialMessage(successCount, failures.length)
          : failures[0],
      );
    } finally {
      this.importing.set(false);
    }
  }

  private parseImportFile(raw: unknown): { questions: QuestionWritePayloadRequestDto[]; errors: string[] } {
    const errors: string[] = [];

    if (!raw || typeof raw !== 'object' || Array.isArray(raw)) {
      return {questions: [], errors: [this.text().rootObjectError]};
    }

    const payload = raw as Partial<QuestionImportFile>;
    if (!Array.isArray(payload.questions)) {
      return {questions: [], errors: [this.text().questionsArrayError]};
    }

    const normalizedQuestions = payload.questions.map((question, index) =>
      this.normalizeQuestion(question, index + 1, errors),
    );

    return {
      questions: normalizedQuestions.filter((question): question is QuestionWritePayloadRequestDto => question !== null),
      errors,
    };
  }

  private normalizeQuestion(
    question: QuestionWritePayloadRequestDto | undefined,
    itemNumber: number,
    errors: string[],
  ): QuestionWritePayloadRequestDto | null {
    if (!question || typeof question !== 'object') {
      errors.push(this.text().questionObjectError(itemNumber));
      return null;
    }

    if (!Number.isInteger(question.domain) || question.domain <= 0) {
      errors.push(this.text().questionDomainError(itemNumber));
    }

    const translations = this.normalizeQuestionTranslations(question.translations, itemNumber, errors);
    const answers = this.normalizeAnswerOptions(question.answer_options, itemNumber, errors);
    const subjectIds = this.normalizeNumberArray(question.subject_ids, this.text().questionSubjectsError(itemNumber), errors);
    const mediaAssetIds = this.normalizeNumberArray(question.media_asset_ids, this.text().questionMediaError(itemNumber), errors);

    if (!translations || !answers) {
      return null;
    }

    return {
      domain: question.domain,
      translations,
      allow_multiple_correct: !!question.allow_multiple_correct,
      active: question.active ?? true,
      is_mode_practice: !!question.is_mode_practice,
      is_mode_exam: !!question.is_mode_exam,
      subject_ids: subjectIds ?? [],
      answer_options: answers,
      media_asset_ids: mediaAssetIds ?? [],
    };
  }

  private normalizeQuestionTranslations(
    translations: { [key: string]: LocalizedQuestionTranslationRequestDto } | undefined,
    itemNumber: number,
    errors: string[],
  ): { [key: string]: LocalizedQuestionTranslationRequestDto } | null {
    if (!translations || typeof translations !== 'object' || Array.isArray(translations)) {
      errors.push(this.text().questionTranslationsError(itemNumber));
      return null;
    }

    const entries = Object.entries(translations);
    if (entries.length === 0) {
      errors.push(this.text().questionTranslationsError(itemNumber));
      return null;
    }

    const normalized: { [key: string]: LocalizedQuestionTranslationRequestDto } = {};

    for (const [lang, value] of entries) {
      if (!value || typeof value !== 'object') {
        errors.push(this.text().questionTranslationShapeError(itemNumber, lang));
        continue;
      }

      if (typeof value.title !== 'string' || typeof value.description !== 'string' || typeof value.explanation !== 'string') {
        errors.push(this.text().questionTranslationShapeError(itemNumber, lang));
        continue;
      }

      normalized[lang] = {
        title: value.title,
        description: value.description,
        explanation: value.explanation,
      };
    }

    return Object.keys(normalized).length > 0 ? normalized : null;
  }

  private normalizeAnswerOptions(
    answers: QuestionAnswerOptionWritePayloadRequestDto[] | undefined,
    itemNumber: number,
    errors: string[],
  ): QuestionAnswerOptionWritePayloadRequestDto[] | null {
    if (!Array.isArray(answers) || answers.length < 2) {
      errors.push(this.text().questionAnswersError(itemNumber));
      return null;
    }

    let correctCount = 0;
    const normalized = answers.map<QuestionAnswerOptionWritePayloadRequestDto | null>((answer, index) => {
      if (!answer || typeof answer !== 'object') {
        errors.push(this.text().answerShapeError(itemNumber, index + 1));
        return null;
      }

      const translations = this.normalizeAnswerTranslations(answer.translations, itemNumber, index + 1, errors);
      if (!translations) {
        return null;
      }

      if (answer.is_correct) {
        correctCount += 1;
      }

      return {
        is_correct: !!answer.is_correct,
        sort_order: Number.isInteger(answer.sort_order) ? answer.sort_order : index + 1,
        translations,
      };
    });

    if (correctCount === 0) {
      errors.push(this.text().questionCorrectAnswerError(itemNumber));
    }

    const validAnswers = normalized.filter((answer): answer is QuestionAnswerOptionWritePayloadRequestDto => answer !== null);
    return validAnswers.length === answers.length ? validAnswers : null;
  }

  private normalizeAnswerTranslations(
    translations: { [key: string]: LocalizedAnswerOptionTranslationRequestDto } | undefined,
    itemNumber: number,
    answerNumber: number,
    errors: string[],
  ): { [key: string]: LocalizedAnswerOptionTranslationRequestDto } | null {
    if (!translations || typeof translations !== 'object' || Array.isArray(translations)) {
      errors.push(this.text().answerTranslationsError(itemNumber, answerNumber));
      return null;
    }

    const entries = Object.entries(translations);
    if (entries.length === 0) {
      errors.push(this.text().answerTranslationsError(itemNumber, answerNumber));
      return null;
    }

    const normalized: { [key: string]: LocalizedAnswerOptionTranslationRequestDto } = {};
    for (const [lang, value] of entries) {
      if (!value || typeof value !== 'object' || typeof value.content !== 'string') {
        errors.push(this.text().answerTranslationShapeError(itemNumber, answerNumber, lang));
        continue;
      }

      normalized[lang] = {content: value.content};
    }

    return Object.keys(normalized).length > 0 ? normalized : null;
  }

  private normalizeNumberArray(
    value: number[] | undefined,
    errorMessage: string,
    errors: string[],
  ): number[] | null {
    if (value === undefined) {
      return [];
    }

    if (!Array.isArray(value) || value.some((item) => !Number.isInteger(item) || item <= 0)) {
      errors.push(errorMessage);
      return null;
    }

    return value;
  }

  private buildExampleFile(): QuestionImportFile {
    return {
      questions: [
        {
          domain: 1,
          subject_ids: [2],
          allow_multiple_correct: false,
          active: true,
          is_mode_practice: true,
          is_mode_exam: false,
          translations: {
            fr: {
              title: 'Capitale de la Belgique',
              description: '<p>Choisis la bonne reponse.</p>',
              explanation: '<p>Bruxelles est la capitale de la Belgique.</p>',
            },
            en: {
              title: 'Capital of Belgium',
              description: '<p>Choose the correct answer.</p>',
              explanation: '<p>Brussels is the capital of Belgium.</p>',
            },
          },
          answer_options: [
            {
              is_correct: true,
              sort_order: 1,
              translations: {
                fr: {content: '<p>Bruxelles</p>'},
                en: {content: '<p>Brussels</p>'},
              },
            },
            {
              is_correct: false,
              sort_order: 2,
              translations: {
                fr: {content: '<p>Anvers</p>'},
                en: {content: '<p>Antwerp</p>'},
              },
            },
          ],
          media_asset_ids: [],
        },
      ],
    };
  }

  private showToast(severity: 'success' | 'error' | 'warn', summary: string, detail: string): void {
    this.messageService.add({
      severity,
      summary,
      detail,
    });
  }

  private getText() {
    switch (this.currentLang()) {
      case LanguageEnumDto.Fr:
        return {
          title: 'Import de questions',
          subtitle: "Importez un fichier JSON contenant une ou plusieurs questions multilingues.",
          back: 'Retour',
          explanationTitle: 'Format attendu',
          explanation: 'Le fichier doit etre un JSON avec une cle "questions" contenant une liste de payloads de creation.',
          exampleButton: "Telecharger l'exemple",
          uploadTitle: 'Fichier JSON',
          chooseFile: 'Choisir un fichier',
          clearFile: 'Effacer',
          noFile: 'Aucun fichier selectionne.',
          selectedFile: 'Fichier selectionne',
          validationTitle: 'Verification du format',
          formatValid: 'Format valide',
          formatInvalid: 'Format invalide',
          invalidJson: "Le fichier n'est pas un JSON valide.",
          rootObjectError: 'Le fichier doit contenir un objet JSON.',
          questionsArrayError: 'Le fichier doit contenir une cle "questions" avec une liste.',
          questionObjectError: (item: number) => `Question ${item}: format invalide.`,
          questionDomainError: (item: number) => `Question ${item}: "domain" doit etre un entier positif.`,
          questionTranslationsError: (item: number) => `Question ${item}: "translations" doit contenir au moins une langue.`,
          questionTranslationShapeError: (item: number, lang: string) => `Question ${item}: traduction "${lang}" invalide.`,
          questionSubjectsError: (item: number) => `Question ${item}: "subject_ids" doit etre une liste d'entiers positifs.`,
          questionMediaError: (item: number) => `Question ${item}: "media_asset_ids" doit etre une liste d'entiers positifs.`,
          questionAnswersError: (item: number) => `Question ${item}: il faut au moins 2 reponses dans "answer_options".`,
          questionCorrectAnswerError: (item: number) => `Question ${item}: il faut au moins une reponse correcte.`,
          answerShapeError: (item: number, answer: number) => `Question ${item}, reponse ${answer}: format invalide.`,
          answerTranslationsError: (item: number, answer: number) => `Question ${item}, reponse ${answer}: "translations" doit contenir au moins une langue.`,
          answerTranslationShapeError: (item: number, answer: number, lang: string) => `Question ${item}, reponse ${answer}, langue "${lang}": contenu invalide.`,
          fileValidated: (count: number) => `${count} question(s) prete(s) a etre importee(s).`,
          importLabel: 'Importer',
          cancelLabel: 'Annuler',
          importDone: 'Import termine',
          importSuccess: (count: number) => `${count} question(s) importee(s) avec succes.`,
          importPartialTitle: 'Import incomplet',
          importPartialMessage: (success: number, failed: number) => `${success} question(s) importee(s), ${failed} en erreur.`,
          importFailure: (item: number) => `La question ${item} n'a pas pu etre importee.`,
        };
      case LanguageEnumDto.Nl:
        return {
          title: 'Vragen importeren',
          subtitle: 'Importeer een JSON-bestand met een of meerdere meertalige vragen.',
          back: 'Terug',
          explanationTitle: 'Verwacht formaat',
          explanation: 'Het bestand moet een JSON-object zijn met een sleutel "questions" die een lijst met aanmaakpayloads bevat.',
          exampleButton: 'Voorbeeld downloaden',
          uploadTitle: 'JSON-bestand',
          chooseFile: 'Bestand kiezen',
          clearFile: 'Wissen',
          noFile: 'Geen bestand geselecteerd.',
          selectedFile: 'Geselecteerd bestand',
          validationTitle: 'Formaatcontrole',
          formatValid: 'Geldig formaat',
          formatInvalid: 'Ongeldig formaat',
          invalidJson: 'Het bestand is geen geldige JSON.',
          rootObjectError: 'Het bestand moet een JSON-object bevatten.',
          questionsArrayError: 'Het bestand moet een sleutel "questions" met een lijst bevatten.',
          questionObjectError: (item: number) => `Vraag ${item}: ongeldig formaat.`,
          questionDomainError: (item: number) => `Vraag ${item}: "domain" moet een positief geheel getal zijn.`,
          questionTranslationsError: (item: number) => `Vraag ${item}: "translations" moet minstens een taal bevatten.`,
          questionTranslationShapeError: (item: number, lang: string) => `Vraag ${item}: vertaling "${lang}" is ongeldig.`,
          questionSubjectsError: (item: number) => `Vraag ${item}: "subject_ids" moet een lijst met positieve gehele getallen zijn.`,
          questionMediaError: (item: number) => `Vraag ${item}: "media_asset_ids" moet een lijst met positieve gehele getallen zijn.`,
          questionAnswersError: (item: number) => `Vraag ${item}: er moeten minstens 2 antwoorden in "answer_options" staan.`,
          questionCorrectAnswerError: (item: number) => `Vraag ${item}: er moet minstens een correct antwoord zijn.`,
          answerShapeError: (item: number, answer: number) => `Vraag ${item}, antwoord ${answer}: ongeldig formaat.`,
          answerTranslationsError: (item: number, answer: number) => `Vraag ${item}, antwoord ${answer}: "translations" moet minstens een taal bevatten.`,
          answerTranslationShapeError: (item: number, answer: number, lang: string) => `Vraag ${item}, antwoord ${answer}, taal "${lang}": ongeldige inhoud.`,
          fileValidated: (count: number) => `${count} vraag(en) klaar om te importeren.`,
          importLabel: 'Importeren',
          cancelLabel: 'Annuleren',
          importDone: 'Import voltooid',
          importSuccess: (count: number) => `${count} vraag(en) succesvol geimporteerd.`,
          importPartialTitle: 'Import onvolledig',
          importPartialMessage: (success: number, failed: number) => `${success} vraag(en) geimporteerd, ${failed} met fouten.`,
          importFailure: (item: number) => `Vraag ${item} kon niet worden geimporteerd.`,
        };
      case LanguageEnumDto.It:
        return {
          title: 'Importazione domande',
          subtitle: 'Importa un file JSON con una o piu domande multilingue.',
          back: 'Indietro',
          explanationTitle: 'Formato atteso',
          explanation: 'Il file deve essere un oggetto JSON con una chiave "questions" che contiene un elenco di payload di creazione.',
          exampleButton: 'Scarica esempio',
          uploadTitle: 'File JSON',
          chooseFile: 'Scegli file',
          clearFile: 'Cancella',
          noFile: 'Nessun file selezionato.',
          selectedFile: 'File selezionato',
          validationTitle: 'Verifica del formato',
          formatValid: 'Formato valido',
          formatInvalid: 'Formato non valido',
          invalidJson: 'Il file non contiene un JSON valido.',
          rootObjectError: 'Il file deve contenere un oggetto JSON.',
          questionsArrayError: 'Il file deve contenere una chiave "questions" con una lista.',
          questionObjectError: (item: number) => `Domanda ${item}: formato non valido.`,
          questionDomainError: (item: number) => `Domanda ${item}: "domain" deve essere un intero positivo.`,
          questionTranslationsError: (item: number) => `Domanda ${item}: "translations" deve contenere almeno una lingua.`,
          questionTranslationShapeError: (item: number, lang: string) => `Domanda ${item}: traduzione "${lang}" non valida.`,
          questionSubjectsError: (item: number) => `Domanda ${item}: "subject_ids" deve essere una lista di interi positivi.`,
          questionMediaError: (item: number) => `Domanda ${item}: "media_asset_ids" deve essere una lista di interi positivi.`,
          questionAnswersError: (item: number) => `Domanda ${item}: servono almeno 2 risposte in "answer_options".`,
          questionCorrectAnswerError: (item: number) => `Domanda ${item}: serve almeno una risposta corretta.`,
          answerShapeError: (item: number, answer: number) => `Domanda ${item}, risposta ${answer}: formato non valido.`,
          answerTranslationsError: (item: number, answer: number) => `Domanda ${item}, risposta ${answer}: "translations" deve contenere almeno una lingua.`,
          answerTranslationShapeError: (item: number, answer: number, lang: string) => `Domanda ${item}, risposta ${answer}, lingua "${lang}": contenuto non valido.`,
          fileValidated: (count: number) => `${count} domanda/e pronta/e per l'importazione.`,
          importLabel: 'Importa',
          cancelLabel: 'Annulla',
          importDone: 'Importazione completata',
          importSuccess: (count: number) => `${count} domanda/e importata/e con successo.`,
          importPartialTitle: 'Importazione parziale',
          importPartialMessage: (success: number, failed: number) => `${success} domanda/e importata/e, ${failed} con errore.`,
          importFailure: (item: number) => `La domanda ${item} non e stata importata.`,
        };
      case LanguageEnumDto.Es:
        return {
          title: 'Importar preguntas',
          subtitle: 'Importa un archivo JSON con una o varias preguntas multilingues.',
          back: 'Volver',
          explanationTitle: 'Formato esperado',
          explanation: 'El archivo debe ser un objeto JSON con una clave "questions" que contenga una lista de cargas de creacion.',
          exampleButton: 'Descargar ejemplo',
          uploadTitle: 'Archivo JSON',
          chooseFile: 'Elegir archivo',
          clearFile: 'Borrar',
          noFile: 'Ningun archivo seleccionado.',
          selectedFile: 'Archivo seleccionado',
          validationTitle: 'Verificacion del formato',
          formatValid: 'Formato valido',
          formatInvalid: 'Formato invalido',
          invalidJson: 'El archivo no contiene un JSON valido.',
          rootObjectError: 'El archivo debe contener un objeto JSON.',
          questionsArrayError: 'El archivo debe contener una clave "questions" con una lista.',
          questionObjectError: (item: number) => `Pregunta ${item}: formato invalido.`,
          questionDomainError: (item: number) => `Pregunta ${item}: "domain" debe ser un entero positivo.`,
          questionTranslationsError: (item: number) => `Pregunta ${item}: "translations" debe contener al menos un idioma.`,
          questionTranslationShapeError: (item: number, lang: string) => `Pregunta ${item}: traduccion "${lang}" invalida.`,
          questionSubjectsError: (item: number) => `Pregunta ${item}: "subject_ids" debe ser una lista de enteros positivos.`,
          questionMediaError: (item: number) => `Pregunta ${item}: "media_asset_ids" debe ser una lista de enteros positivos.`,
          questionAnswersError: (item: number) => `Pregunta ${item}: se necesitan al menos 2 respuestas en "answer_options".`,
          questionCorrectAnswerError: (item: number) => `Pregunta ${item}: debe haber al menos una respuesta correcta.`,
          answerShapeError: (item: number, answer: number) => `Pregunta ${item}, respuesta ${answer}: formato invalido.`,
          answerTranslationsError: (item: number, answer: number) => `Pregunta ${item}, respuesta ${answer}: "translations" debe contener al menos un idioma.`,
          answerTranslationShapeError: (item: number, answer: number, lang: string) => `Pregunta ${item}, respuesta ${answer}, idioma "${lang}": contenido invalido.`,
          fileValidated: (count: number) => `${count} pregunta(s) lista(s) para importar.`,
          importLabel: 'Importar',
          cancelLabel: 'Cancelar',
          importDone: 'Importacion completada',
          importSuccess: (count: number) => `${count} pregunta(s) importada(s) correctamente.`,
          importPartialTitle: 'Importacion parcial',
          importPartialMessage: (success: number, failed: number) => `${success} pregunta(s) importada(s), ${failed} con error.`,
          importFailure: (item: number) => `La pregunta ${item} no pudo importarse.`,
        };
      case LanguageEnumDto.En:
      default:
        return {
          title: 'Question Import',
          subtitle: 'Import a JSON file containing one or more multilingual questions.',
          back: 'Back',
          explanationTitle: 'Expected format',
          explanation: 'The file must be a JSON object with a "questions" key containing a list of create payloads.',
          exampleButton: 'Download example',
          uploadTitle: 'JSON file',
          chooseFile: 'Choose file',
          clearFile: 'Clear',
          noFile: 'No file selected.',
          selectedFile: 'Selected file',
          validationTitle: 'Format validation',
          formatValid: 'Valid format',
          formatInvalid: 'Invalid format',
          invalidJson: 'The file does not contain valid JSON.',
          rootObjectError: 'The file must contain a JSON object.',
          questionsArrayError: 'The file must contain a "questions" key with a list.',
          questionObjectError: (item: number) => `Question ${item}: invalid format.`,
          questionDomainError: (item: number) => `Question ${item}: "domain" must be a positive integer.`,
          questionTranslationsError: (item: number) => `Question ${item}: "translations" must contain at least one language.`,
          questionTranslationShapeError: (item: number, lang: string) => `Question ${item}: translation "${lang}" is invalid.`,
          questionSubjectsError: (item: number) => `Question ${item}: "subject_ids" must be a list of positive integers.`,
          questionMediaError: (item: number) => `Question ${item}: "media_asset_ids" must be a list of positive integers.`,
          questionAnswersError: (item: number) => `Question ${item}: at least 2 answers are required in "answer_options".`,
          questionCorrectAnswerError: (item: number) => `Question ${item}: at least one answer must be correct.`,
          answerShapeError: (item: number, answer: number) => `Question ${item}, answer ${answer}: invalid format.`,
          answerTranslationsError: (item: number, answer: number) => `Question ${item}, answer ${answer}: "translations" must contain at least one language.`,
          answerTranslationShapeError: (item: number, answer: number, lang: string) => `Question ${item}, answer ${answer}, language "${lang}": invalid content.`,
          fileValidated: (count: number) => `${count} question(s) ready to import.`,
          importLabel: 'Import',
          cancelLabel: 'Cancel',
          importDone: 'Import complete',
          importSuccess: (count: number) => `${count} question(s) imported successfully.`,
          importPartialTitle: 'Import incomplete',
          importPartialMessage: (success: number, failed: number) => `${success} question(s) imported, ${failed} failed.`,
          importFailure: (item: number) => `Question ${item} could not be imported.`,
        };
    }
  }
}
