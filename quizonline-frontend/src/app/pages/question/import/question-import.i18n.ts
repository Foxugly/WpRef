import { LanguageEnumDto } from '../../../api/generated';

export type QuestionImportUiText = {
  title: string;
  subtitle: string;
  back: string;
  explanationTitle: string;
  explanation: string;
  exampleButton: string;
  uploadTitle: string;
  chooseFile: string;
  clearFile: string;
  noFile: string;
  selectedFile: string;
  validationTitle: string;
  formatValid: string;
  formatInvalid: string;
  invalidJson: string;
  rootObjectError: string;
  questionsArrayError: string;
  questionObjectError: (item: number) => string;
  questionDomainError: (item: number) => string;
  questionTranslationsError: (item: number) => string;
  questionTranslationShapeError: (item: number, lang: string) => string;
  questionSubjectsError: (item: number) => string;
  questionMediaError: (item: number) => string;
  questionAnswersError: (item: number) => string;
  questionCorrectAnswerError: (item: number) => string;
  answerShapeError: (item: number, answer: number) => string;
  answerTranslationsError: (item: number, answer: number) => string;
  answerTranslationShapeError: (item: number, answer: number, lang: string) => string;
  fileValidated: (count: number) => string;
  importLabel: string;
  cancelLabel: string;
  importDone: string;
  importSuccess: (count: number) => string;
  importPartialTitle: string;
  importPartialMessage: (success: number, failed: number) => string;
  importFailure: (item: number) => string;
};

const FR: QuestionImportUiText = {
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
  questionObjectError: (item) => `Question ${item}: format invalide.`,
  questionDomainError: (item) => `Question ${item}: "domain" doit etre un entier positif.`,
  questionTranslationsError: (item) => `Question ${item}: "translations" doit contenir au moins une langue.`,
  questionTranslationShapeError: (item, lang) => `Question ${item}: traduction "${lang}" invalide.`,
  questionSubjectsError: (item) => `Question ${item}: "subject_ids" doit etre une liste d'entiers positifs.`,
  questionMediaError: (item) => `Question ${item}: "media_asset_ids" doit etre une liste d'entiers positifs.`,
  questionAnswersError: (item) => `Question ${item}: il faut au moins 2 reponses dans "answer_options".`,
  questionCorrectAnswerError: (item) => `Question ${item}: il faut au moins une reponse correcte.`,
  answerShapeError: (item, answer) => `Question ${item}, reponse ${answer}: format invalide.`,
  answerTranslationsError: (item, answer) => `Question ${item}, reponse ${answer}: "translations" doit contenir au moins une langue.`,
  answerTranslationShapeError: (item, answer, lang) => `Question ${item}, reponse ${answer}, langue "${lang}": contenu invalide.`,
  fileValidated: (count) => `${count} question(s) prete(s) a etre importee(s).`,
  importLabel: 'Importer',
  cancelLabel: 'Annuler',
  importDone: 'Import termine',
  importSuccess: (count) => `${count} question(s) importee(s) avec succes.`,
  importPartialTitle: 'Import incomplet',
  importPartialMessage: (success, failed) => `${success} question(s) importee(s), ${failed} en erreur.`,
  importFailure: (item) => `La question ${item} n'a pas pu etre importee.`,
};

const EN: QuestionImportUiText = {
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
  questionObjectError: (item) => `Question ${item}: invalid format.`,
  questionDomainError: (item) => `Question ${item}: "domain" must be a positive integer.`,
  questionTranslationsError: (item) => `Question ${item}: "translations" must contain at least one language.`,
  questionTranslationShapeError: (item, lang) => `Question ${item}: translation "${lang}" is invalid.`,
  questionSubjectsError: (item) => `Question ${item}: "subject_ids" must be a list of positive integers.`,
  questionMediaError: (item) => `Question ${item}: "media_asset_ids" must be a list of positive integers.`,
  questionAnswersError: (item) => `Question ${item}: at least 2 answers are required in "answer_options".`,
  questionCorrectAnswerError: (item) => `Question ${item}: at least one answer must be correct.`,
  answerShapeError: (item, answer) => `Question ${item}, answer ${answer}: invalid format.`,
  answerTranslationsError: (item, answer) => `Question ${item}, answer ${answer}: "translations" must contain at least one language.`,
  answerTranslationShapeError: (item, answer, lang) => `Question ${item}, answer ${answer}, language "${lang}": invalid content.`,
  fileValidated: (count) => `${count} question(s) ready to import.`,
  importLabel: 'Import',
  cancelLabel: 'Cancel',
  importDone: 'Import complete',
  importSuccess: (count) => `${count} question(s) imported successfully.`,
  importPartialTitle: 'Import incomplete',
  importPartialMessage: (success, failed) => `${success} question(s) imported, ${failed} failed.`,
  importFailure: (item) => `Question ${item} could not be imported.`,
};

const NL: QuestionImportUiText = {
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
  questionObjectError: (item) => `Vraag ${item}: ongeldig formaat.`,
  questionDomainError: (item) => `Vraag ${item}: "domain" moet een positief geheel getal zijn.`,
  questionTranslationsError: (item) => `Vraag ${item}: "translations" moet minstens een taal bevatten.`,
  questionTranslationShapeError: (item, lang) => `Vraag ${item}: vertaling "${lang}" is ongeldig.`,
  questionSubjectsError: (item) => `Vraag ${item}: "subject_ids" moet een lijst met positieve gehele getallen zijn.`,
  questionMediaError: (item) => `Vraag ${item}: "media_asset_ids" moet een lijst met positieve gehele getallen zijn.`,
  questionAnswersError: (item) => `Vraag ${item}: er moeten minstens 2 antwoorden in "answer_options" staan.`,
  questionCorrectAnswerError: (item) => `Vraag ${item}: er moet minstens een correct antwoord zijn.`,
  answerShapeError: (item, answer) => `Vraag ${item}, antwoord ${answer}: ongeldig formaat.`,
  answerTranslationsError: (item, answer) => `Vraag ${item}, antwoord ${answer}: "translations" moet minstens een taal bevatten.`,
  answerTranslationShapeError: (item, answer, lang) => `Vraag ${item}, antwoord ${answer}, taal "${lang}": ongeldige inhoud.`,
  fileValidated: (count) => `${count} vraag(en) klaar om te importeren.`,
  importLabel: 'Importeren',
  cancelLabel: 'Annuleren',
  importDone: 'Import voltooid',
  importSuccess: (count) => `${count} vraag(en) succesvol geimporteerd.`,
  importPartialTitle: 'Import onvolledig',
  importPartialMessage: (success, failed) => `${success} vraag(en) geimporteerd, ${failed} met fouten.`,
  importFailure: (item) => `Vraag ${item} kon niet worden geimporteerd.`,
};

const IT: QuestionImportUiText = {
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
  questionObjectError: (item) => `Domanda ${item}: formato non valido.`,
  questionDomainError: (item) => `Domanda ${item}: "domain" deve essere un intero positivo.`,
  questionTranslationsError: (item) => `Domanda ${item}: "translations" deve contenere almeno una lingua.`,
  questionTranslationShapeError: (item, lang) => `Domanda ${item}: traduzione "${lang}" non valida.`,
  questionSubjectsError: (item) => `Domanda ${item}: "subject_ids" deve essere una lista di interi positivi.`,
  questionMediaError: (item) => `Domanda ${item}: "media_asset_ids" deve essere una lista di interi positivi.`,
  questionAnswersError: (item) => `Domanda ${item}: servono almeno 2 risposte in "answer_options".`,
  questionCorrectAnswerError: (item) => `Domanda ${item}: serve almeno una risposta corretta.`,
  answerShapeError: (item, answer) => `Domanda ${item}, risposta ${answer}: formato non valido.`,
  answerTranslationsError: (item, answer) => `Domanda ${item}, risposta ${answer}: "translations" deve contenere almeno una lingua.`,
  answerTranslationShapeError: (item, answer, lang) => `Domanda ${item}, risposta ${answer}, lingua "${lang}": contenuto non valido.`,
  fileValidated: (count) => `${count} domanda/e pronta/e per l'importazione.`,
  importLabel: 'Importa',
  cancelLabel: 'Annulla',
  importDone: 'Importazione completata',
  importSuccess: (count) => `${count} domanda/e importata/e con successo.`,
  importPartialTitle: 'Importazione parziale',
  importPartialMessage: (success, failed) => `${success} domanda/e importata/e, ${failed} con errore.`,
  importFailure: (item) => `La domanda ${item} non e stata importata.`,
};

const ES: QuestionImportUiText = {
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
  questionObjectError: (item) => `Pregunta ${item}: formato invalido.`,
  questionDomainError: (item) => `Pregunta ${item}: "domain" debe ser un entero positivo.`,
  questionTranslationsError: (item) => `Pregunta ${item}: "translations" debe contener al menos un idioma.`,
  questionTranslationShapeError: (item, lang) => `Pregunta ${item}: traduccion "${lang}" invalida.`,
  questionSubjectsError: (item) => `Pregunta ${item}: "subject_ids" debe ser una lista de enteros positivos.`,
  questionMediaError: (item) => `Pregunta ${item}: "media_asset_ids" debe ser una lista de enteros positivos.`,
  questionAnswersError: (item) => `Pregunta ${item}: se necesitan al menos 2 respuestas en "answer_options".`,
  questionCorrectAnswerError: (item) => `Pregunta ${item}: debe haber al menos una respuesta correcta.`,
  answerShapeError: (item, answer) => `Pregunta ${item}, respuesta ${answer}: formato invalido.`,
  answerTranslationsError: (item, answer) => `Pregunta ${item}, respuesta ${answer}: "translations" debe contener al menos un idioma.`,
  answerTranslationShapeError: (item, answer, lang) => `Pregunta ${item}, respuesta ${answer}, idioma "${lang}": contenido invalido.`,
  fileValidated: (count) => `${count} pregunta(s) lista(s) para importar.`,
  importLabel: 'Importar',
  cancelLabel: 'Cancelar',
  importDone: 'Importacion completada',
  importSuccess: (count) => `${count} pregunta(s) importada(s) correctamente.`,
  importPartialTitle: 'Importacion parcial',
  importPartialMessage: (success, failed) => `${success} pregunta(s) importada(s), ${failed} con error.`,
  importFailure: (item) => `La pregunta ${item} no pudo importarse.`,
};

const UI_TEXT: Partial<Record<LanguageEnumDto, QuestionImportUiText>> = {
  [LanguageEnumDto.Fr]: FR,
  [LanguageEnumDto.En]: EN,
  [LanguageEnumDto.Nl]: NL,
  [LanguageEnumDto.It]: IT,
  [LanguageEnumDto.Es]: ES,
};

export function getQuestionImportUiText(lang: LanguageEnumDto | string | null | undefined): QuestionImportUiText {
  return UI_TEXT[lang as LanguageEnumDto] ?? EN;
}
