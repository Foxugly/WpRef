import {LanguageEnumDto} from '../../../api/generated';

export type QuizCreateUiText = {
  settingsTitle: string;
  createTitle: string;
  editTitle: string;
  createSubtitle: string;
  editSubtitle: string;
  createTemplate: string;
  saveTemplate: string;
  domain: string;
  mode: string;
  timer: string;
  duration: string;
  active: string;
  permanent: string;
  startedAt: string;
  endedAt: string;
  detailVisibility: string;
  detailAvailableAt: string;
  quizTitle: string;
  quizDescription: string;
  practiceMode: string;
  examMode: string;
  visibilityImmediate: string;
  visibilityScheduled: string;
  visibilityNever: string;
  dateFormat: string;
  today: string;
  clear: string;
  weekHeader: string;
  dayNames: string[];
  dayNamesShort: string[];
  dayNamesMin: string[];
  monthNames: string[];
  monthNamesShort: string[];
};

const QUIZ_CREATE_UI_TEXT: Record<LanguageEnumDto, QuizCreateUiText> = {
  [LanguageEnumDto.En]: {
    settingsTitle: 'Quiz settings',
    createTitle: 'Create a quiz template',
    editTitle: 'Edit quiz template',
    createSubtitle: 'One domain, a curated question pool, and controlled publication settings',
    editSubtitle: 'Adjust the template settings, visibility, and ordered questions',
    createTemplate: 'Create template',
    saveTemplate: 'Save template',
    domain: 'Domain',
    mode: 'Mode',
    timer: 'Timer',
    duration: 'Duration',
    active: 'Active',
    permanent: 'Permanent',
    startedAt: 'Start date',
    endedAt: 'End date',
    detailVisibility: 'Detail visibility',
    detailAvailableAt: 'Detail available at',
    quizTitle: 'Title',
    quizDescription: 'Description',
    practiceMode: 'Practice',
    examMode: 'Exam',
    visibilityImmediate: 'Immediate',
    visibilityScheduled: 'Scheduled',
    visibilityNever: 'Never',
    dateFormat: 'mm/dd/yy',
    today: 'Today',
    clear: 'Clear',
    weekHeader: 'Wk',
    dayNames: ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'],
    dayNamesShort: ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'],
    dayNamesMin: ['Su', 'Mo', 'Tu', 'We', 'Th', 'Fr', 'Sa'],
    monthNames: ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December'],
    monthNamesShort: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'],
  },
  [LanguageEnumDto.Nl]: {
    settingsTitle: 'Quizinstellingen',
    createTitle: 'Een quiztemplate maken',
    editTitle: 'Quiztemplate bewerken',
    createSubtitle: 'Een domein, een vragenpool en duidelijke publicatie-instellingen',
    editSubtitle: 'Pas template-instellingen, zichtbaarheid en volgorde van vragen aan',
    createTemplate: 'Template maken',
    saveTemplate: 'Template opslaan',
    domain: 'Domein',
    mode: 'Modus',
    timer: 'Timer',
    duration: 'Duur',
    active: 'Actief',
    permanent: 'Permanent',
    startedAt: 'Startdatum',
    endedAt: 'Einddatum',
    detailVisibility: 'Detailzichtbaarheid',
    detailAvailableAt: 'Details beschikbaar vanaf',
    quizTitle: 'Titel',
    quizDescription: 'Beschrijving',
    practiceMode: 'Oefenen',
    examMode: 'Examen',
    visibilityImmediate: 'Onmiddellijk',
    visibilityScheduled: 'Gepland',
    visibilityNever: 'Nooit',
    dateFormat: 'dd/mm/yy',
    today: 'Vandaag',
    clear: 'Wissen',
    weekHeader: 'Wk',
    dayNames: ['zondag', 'maandag', 'dinsdag', 'woensdag', 'donderdag', 'vrijdag', 'zaterdag'],
    dayNamesShort: ['zon', 'maa', 'din', 'woe', 'don', 'vri', 'zat'],
    dayNamesMin: ['zo', 'ma', 'di', 'wo', 'do', 'vr', 'za'],
    monthNames: ['januari', 'februari', 'maart', 'april', 'mei', 'juni', 'juli', 'augustus', 'september', 'oktober', 'november', 'december'],
    monthNamesShort: ['jan', 'feb', 'mrt', 'apr', 'mei', 'jun', 'jul', 'aug', 'sep', 'okt', 'nov', 'dec'],
  },
  [LanguageEnumDto.It]: {
    settingsTitle: 'Parametri del quiz',
    createTitle: 'Crea un template quiz',
    editTitle: 'Modifica il template quiz',
    createSubtitle: 'Un dominio, un set di domande e regole di pubblicazione chiare',
    editSubtitle: 'Aggiorna impostazioni, visibilita e ordine delle domande',
    createTemplate: 'Crea template',
    saveTemplate: 'Salva template',
    domain: 'Dominio',
    mode: 'Modalita',
    timer: 'Timer',
    duration: 'Durata',
    active: 'Attivo',
    permanent: 'Permanente',
    startedAt: 'Data inizio',
    endedAt: 'Data fine',
    detailVisibility: 'Visibilita dettagli',
    detailAvailableAt: 'Dettagli disponibili dal',
    quizTitle: 'Titolo',
    quizDescription: 'Descrizione',
    practiceMode: 'Pratica',
    examMode: 'Esame',
    visibilityImmediate: 'Immediata',
    visibilityScheduled: 'Pianificata',
    visibilityNever: 'Mai',
    dateFormat: 'dd/mm/yy',
    today: 'Oggi',
    clear: 'Cancella',
    weekHeader: 'Sm',
    dayNames: ['domenica', 'lunedi', 'martedi', 'mercoledi', 'giovedi', 'venerdi', 'sabato'],
    dayNamesShort: ['dom', 'lun', 'mar', 'mer', 'gio', 'ven', 'sab'],
    dayNamesMin: ['do', 'lu', 'ma', 'me', 'gi', 've', 'sa'],
    monthNames: ['gennaio', 'febbraio', 'marzo', 'aprile', 'maggio', 'giugno', 'luglio', 'agosto', 'settembre', 'ottobre', 'novembre', 'dicembre'],
    monthNamesShort: ['gen', 'feb', 'mar', 'apr', 'mag', 'giu', 'lug', 'ago', 'set', 'ott', 'nov', 'dic'],
  },
  [LanguageEnumDto.Es]: {
    settingsTitle: 'Parametros del quiz',
    createTitle: 'Crear una plantilla de quiz',
    editTitle: 'Editar plantilla de quiz',
    createSubtitle: 'Un dominio, un conjunto de preguntas y reglas claras de publicacion',
    editSubtitle: 'Actualiza configuracion, visibilidad y orden de las preguntas',
    createTemplate: 'Crear plantilla',
    saveTemplate: 'Guardar plantilla',
    domain: 'Dominio',
    mode: 'Modo',
    timer: 'Temporizador',
    duration: 'Duracion',
    active: 'Activo',
    permanent: 'Permanente',
    startedAt: 'Fecha de inicio',
    endedAt: 'Fecha de fin',
    detailVisibility: 'Visibilidad del detalle',
    detailAvailableAt: 'Detalle disponible desde',
    quizTitle: 'Titulo',
    quizDescription: 'Descripcion',
    practiceMode: 'Practica',
    examMode: 'Examen',
    visibilityImmediate: 'Inmediata',
    visibilityScheduled: 'Programada',
    visibilityNever: 'Nunca',
    dateFormat: 'dd/mm/yy',
    today: 'Hoy',
    clear: 'Borrar',
    weekHeader: 'Sm',
    dayNames: ['domingo', 'lunes', 'martes', 'miercoles', 'jueves', 'viernes', 'sabado'],
    dayNamesShort: ['dom', 'lun', 'mar', 'mie', 'jue', 'vie', 'sab'],
    dayNamesMin: ['do', 'lu', 'ma', 'mi', 'ju', 'vi', 'sa'],
    monthNames: ['enero', 'febrero', 'marzo', 'abril', 'mayo', 'junio', 'julio', 'agosto', 'septiembre', 'octubre', 'noviembre', 'diciembre'],
    monthNamesShort: ['ene', 'feb', 'mar', 'abr', 'may', 'jun', 'jul', 'ago', 'sep', 'oct', 'nov', 'dic'],
  },
  [LanguageEnumDto.Fr]: {
    settingsTitle: 'Parametres du quiz',
    createTitle: 'Creer un template de quiz',
    editTitle: 'Modifier le template de quiz',
    createSubtitle: 'Un domaine, un pool de questions et des regles de publication maitrisees',
    editSubtitle: 'Ajuste les parametres, la visibilite et l ordre des questions',
    createTemplate: 'Creer le template',
    saveTemplate: 'Enregistrer le template',
    domain: 'Domaine',
    mode: 'Mode',
    timer: 'Timer',
    duration: 'Duree',
    active: 'Active',
    permanent: 'Permanent',
    startedAt: 'Date de debut',
    endedAt: 'Date de fin',
    detailVisibility: 'Visibilite du detail',
    detailAvailableAt: 'Detail disponible a partir de',
    quizTitle: 'Titre',
    quizDescription: 'Description',
    practiceMode: 'Pratique',
    examMode: 'Examen',
    visibilityImmediate: 'Immediat',
    visibilityScheduled: 'Planifie',
    visibilityNever: 'Jamais',
    dateFormat: 'dd/mm/yy',
    today: 'Aujourd hui',
    clear: 'Effacer',
    weekHeader: 'Sem',
    dayNames: ['dimanche', 'lundi', 'mardi', 'mercredi', 'jeudi', 'vendredi', 'samedi'],
    dayNamesShort: ['dim', 'lun', 'mar', 'mer', 'jeu', 'ven', 'sam'],
    dayNamesMin: ['di', 'lu', 'ma', 'me', 'je', 've', 'sa'],
    monthNames: ['janvier', 'fevrier', 'mars', 'avril', 'mai', 'juin', 'juillet', 'aout', 'septembre', 'octobre', 'novembre', 'decembre'],
    monthNamesShort: ['jan', 'fev', 'mar', 'avr', 'mai', 'jun', 'jul', 'aou', 'sep', 'oct', 'nov', 'dec'],
  },
};

export function getQuizCreateUiText(lang: LanguageEnumDto): QuizCreateUiText {
  return QUIZ_CREATE_UI_TEXT[lang] ?? QUIZ_CREATE_UI_TEXT[LanguageEnumDto.Fr];
}
