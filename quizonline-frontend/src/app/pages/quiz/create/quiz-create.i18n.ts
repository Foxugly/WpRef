import {LanguageEnumDto} from '../../../api/generated';

export type QuizCreateUiText = {
  settingsTab: string;
  questionsTab: string;
  settingsTitle: string;
  questionPoolTitle: string;
  questionSearchPlaceholder: string;
  questionSubjectFilter: string;
  questionSubjectFilterPlaceholder: string;
  createQuestion: string;
  selectDomainToLoadQuestions: string;
  loadingQuestions: string;
  noAvailableQuestions: string;
  compositionTitle: string;
  compositionHelp: string;
  compositionEmpty: string;
  weight: string;
  weightHelp: string;
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
  public: string;
  permanent: string;
  startedAt: string;
  endedAt: string;
  detailVisibility: string;
  detailAvailableAt: string;
  quizTitle: string;
  quizDescription: string;
  translationsTitle: string;
  languagesCount: string;
  translateOthers: string;
  translating: string;
  translationHint: string;
  translationRequired: string;
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
    settingsTab: 'Settings',
    questionsTab: 'Questions',
    settingsTitle: 'Quiz settings',
    questionPoolTitle: 'Available questions',
    questionSearchPlaceholder: 'Search a question',
    questionSubjectFilter: 'Subjects',
    questionSubjectFilterPlaceholder: 'Filter by subjects',
    createQuestion: 'Create question',
    selectDomainToLoadQuestions: 'Choose a domain to load available questions.',
    loadingQuestions: 'Loading questions...',
    noAvailableQuestions: 'No active question is available for this domain.',
    compositionTitle: 'Quiz composition',
    compositionHelp: 'Adjust question order and weight before saving.',
    compositionEmpty: 'Add at least one question to compose the quiz.',
    weight: 'Weight',
    weightHelp: 'The weight changes how much this question counts in scoring.',
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
    public: 'Public',
    permanent: 'Permanent',
    startedAt: 'Start date',
    endedAt: 'End date',
    detailVisibility: 'Detail visibility',
    detailAvailableAt: 'Detail available at',
    quizTitle: 'Title',
    quizDescription: 'Description',
    translationsTitle: 'Translations',
    languagesCount: 'languages',
    translateOthers: 'Translate to other languages',
    translating: 'Translating...',
    translationHint: 'Edit the localized title and description for each active language.',
    translationRequired: 'At least one translated title is required.',
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
    settingsTab: 'Instellingen',
    questionsTab: 'Vragen',
    settingsTitle: 'Quizinstellingen',
    questionPoolTitle: 'Beschikbare vragen',
    questionSearchPlaceholder: 'Zoek een vraag',
    questionSubjectFilter: 'Onderwerpen',
    questionSubjectFilterPlaceholder: 'Filter op onderwerpen',
    createQuestion: 'Vraag maken',
    selectDomainToLoadQuestions: 'Kies een domein om beschikbare vragen te laden.',
    loadingQuestions: 'Vragen laden...',
    noAvailableQuestions: 'Geen actieve vragen beschikbaar voor dit domein.',
    compositionTitle: 'Quizopbouw',
    compositionHelp: 'Pas volgorde en gewicht van vragen aan voor het opslaan.',
    compositionEmpty: 'Voeg minstens een vraag toe om de quiz samen te stellen.',
    weight: 'Gewicht',
    weightHelp: 'Het gewicht bepaalt hoe zwaar deze vraag meetelt in de score.',
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
    public: 'Publiek',
    permanent: 'Permanent',
    startedAt: 'Startdatum',
    endedAt: 'Einddatum',
    detailVisibility: 'Detailzichtbaarheid',
    detailAvailableAt: 'Details beschikbaar vanaf',
    quizTitle: 'Titel',
    quizDescription: 'Beschrijving',
    translationsTitle: 'Vertalingen',
    languagesCount: 'talen',
    translateOthers: 'Vertalen naar andere talen',
    translating: 'Vertalen...',
    translationHint: 'Bewerk de gelokaliseerde titel en beschrijving voor elke actieve taal.',
    translationRequired: 'Minstens een vertaalde titel is verplicht.',
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
    settingsTab: 'Parametri',
    questionsTab: 'Domande',
    settingsTitle: 'Parametri del quiz',
    questionPoolTitle: 'Domande disponibili',
    questionSearchPlaceholder: 'Cerca una domanda',
    questionSubjectFilter: 'Soggetti',
    questionSubjectFilterPlaceholder: 'Filtra per soggetti',
    createQuestion: 'Crea domanda',
    selectDomainToLoadQuestions: 'Scegli un dominio per caricare le domande disponibili.',
    loadingQuestions: 'Caricamento domande...',
    noAvailableQuestions: 'Nessuna domanda attiva disponibile per questo dominio.',
    compositionTitle: 'Composizione del quiz',
    compositionHelp: 'Regola ordine e peso delle domande prima del salvataggio.',
    compositionEmpty: 'Aggiungi almeno una domanda per comporre il quiz.',
    weight: 'Peso',
    weightHelp: 'Il peso cambia quanto questa domanda conta nel punteggio.',
    createTitle: 'Crea un template quiz',
    editTitle: 'Modifica il template quiz',
    createSubtitle: 'Un dominio, un set di domande e regole di pubblicazione chiare',
    editSubtitle: 'Aggiorna impostazioni, visibilità e ordine delle domande',
    createTemplate: 'Crea template',
    saveTemplate: 'Salva template',
    domain: 'Dominio',
    mode: 'Modalità',
    timer: 'Timer',
    duration: 'Durata',
    active: 'Attivo',
    public: 'Pubblico',
    permanent: 'Permanente',
    startedAt: 'Data inizio',
    endedAt: 'Data fine',
    detailVisibility: 'Visibilità dettagli',
    detailAvailableAt: 'Dettagli disponibili dal',
    quizTitle: 'Titolo',
    quizDescription: 'Descrizione',
    translationsTitle: 'Traduzioni',
    languagesCount: 'lingue',
    translateOthers: 'Traduci nelle altre lingue',
    translating: 'Traduzione in corso...',
    translationHint: 'Modifica titolo e descrizione localizzati per ogni lingua attiva.',
    translationRequired: 'È richiesto almeno un titolo tradotto.',
    practiceMode: 'Pratica',
    examMode: 'Esame',
    visibilityImmediate: 'Immediata',
    visibilityScheduled: 'Pianificata',
    visibilityNever: 'Mai',
    dateFormat: 'dd/mm/yy',
    today: 'Oggi',
    clear: 'Cancella',
    weekHeader: 'Sm',
    dayNames: ['domenica', 'lunedì', 'martedì', 'mercoledì', 'giovedì', 'venerdì', 'sabato'],
    dayNamesShort: ['dom', 'lun', 'mar', 'mer', 'gio', 'ven', 'sab'],
    dayNamesMin: ['do', 'lu', 'ma', 'me', 'gi', 've', 'sa'],
    monthNames: ['gennaio', 'febbraio', 'marzo', 'aprile', 'maggio', 'giugno', 'luglio', 'agosto', 'settembre', 'ottobre', 'novembre', 'dicembre'],
    monthNamesShort: ['gen', 'feb', 'mar', 'apr', 'mag', 'giu', 'lug', 'ago', 'set', 'ott', 'nov', 'dic'],
  },
  [LanguageEnumDto.Es]: {
    settingsTab: 'Parámetros',
    questionsTab: 'Preguntas',
    settingsTitle: 'Parámetros del quiz',
    questionPoolTitle: 'Preguntas disponibles',
    questionSearchPlaceholder: 'Buscar una pregunta',
    questionSubjectFilter: 'Temas',
    questionSubjectFilterPlaceholder: 'Filtrar por temas',
    createQuestion: 'Crear pregunta',
    selectDomainToLoadQuestions: 'Elige un dominio para cargar las preguntas disponibles.',
    loadingQuestions: 'Cargando preguntas...',
    noAvailableQuestions: 'No hay preguntas activas disponibles para este dominio.',
    compositionTitle: 'Composición del cuestionario',
    compositionHelp: 'Ajusta el orden y el peso de cada pregunta antes de guardar.',
    compositionEmpty: 'Agrega al menos una pregunta para componer el cuestionario.',
    weight: 'Peso',
    weightHelp: 'El peso cambia cuánto cuenta esta pregunta en la puntuación.',
    createTitle: 'Crear una plantilla de quiz',
    editTitle: 'Editar plantilla de quiz',
    createSubtitle: 'Un dominio, un conjunto de preguntas y reglas claras de publicación',
    editSubtitle: 'Actualiza configuración, visibilidad y orden de las preguntas',
    createTemplate: 'Crear plantilla',
    saveTemplate: 'Guardar plantilla',
    domain: 'Dominio',
    mode: 'Modo',
    timer: 'Temporizador',
    duration: 'Duración',
    active: 'Activo',
    public: 'Publico',
    permanent: 'Permanente',
    startedAt: 'Fecha de inicio',
    endedAt: 'Fecha de fin',
    detailVisibility: 'Visibilidad del detalle',
    detailAvailableAt: 'Detalle disponible desde',
    quizTitle: 'Título',
    quizDescription: 'Descripción',
    translationsTitle: 'Traducciones',
    languagesCount: 'idiomas',
    translateOthers: 'Traducir a los otros idiomas',
    translating: 'Traducción en curso...',
    translationHint: 'Edita el título y la descripción localizados para cada idioma activo.',
    translationRequired: 'Se requiere al menos un título traducido.',
    practiceMode: 'Práctica',
    examMode: 'Examen',
    visibilityImmediate: 'Inmediata',
    visibilityScheduled: 'Programada',
    visibilityNever: 'Nunca',
    dateFormat: 'dd/mm/yy',
    today: 'Hoy',
    clear: 'Borrar',
    weekHeader: 'Sm',
    dayNames: ['domingo', 'lunes', 'martes', 'miércoles', 'jueves', 'viernes', 'sábado'],
    dayNamesShort: ['dom', 'lun', 'mar', 'mié', 'jue', 'vie', 'sab'],
    dayNamesMin: ['do', 'lu', 'ma', 'mi', 'ju', 'vi', 'sa'],
    monthNames: ['enero', 'febrero', 'marzo', 'abril', 'mayo', 'junio', 'julio', 'agosto', 'septiembre', 'octubre', 'noviembre', 'diciembre'],
    monthNamesShort: ['ene', 'feb', 'mar', 'abr', 'may', 'jun', 'jul', 'ago', 'sep', 'oct', 'nov', 'dic'],
  },
  [LanguageEnumDto.Fr]: {
    settingsTab: 'Paramètres',
    questionsTab: 'Questions',
    settingsTitle: 'Paramètres du quiz',
    questionPoolTitle: 'Questions disponibles',
    questionSearchPlaceholder: 'Rechercher une question',
    questionSubjectFilter: 'Sujets',
    questionSubjectFilterPlaceholder: 'Filtrer par sujets',
    createQuestion: 'Créer une question',
    selectDomainToLoadQuestions: 'Choisis un domaine pour charger les questions disponibles.',
    loadingQuestions: 'Chargement des questions...',
    noAvailableQuestions: 'Aucune question active disponible pour ce domaine.',
    compositionTitle: 'Composition du quiz',
    compositionHelp: 'Ajuste l\'ordre et le poids de chaque question avant enregistrement.',
    compositionEmpty: 'Ajoute au moins une question pour composer le quiz.',
    weight: 'Poids',
    weightHelp: 'Le poids change l\'importance de cette question dans le score.',
    createTitle: 'Créer un template de quiz',
    editTitle: 'Modifier le template de quiz',
    createSubtitle: 'Un domaine, un pool de questions et des règles de publication maîtrisées',
    editSubtitle: 'Ajuste les paramètres, la visibilité et l\'ordre des questions',
    createTemplate: 'Créer le template',
    saveTemplate: 'Enregistrer le template',
    domain: 'Domaine',
    mode: 'Mode',
    timer: 'Timer',
    duration: 'Durée',
    active: 'Active',
    public: 'Public',
    permanent: 'Permanent',
    startedAt: 'Date de début',
    endedAt: 'Date de fin',
    detailVisibility: 'Visibilité du détail',
    detailAvailableAt: 'Détail disponible à partir de',
    quizTitle: 'Titre',
    quizDescription: 'Description',
    translationsTitle: 'Traductions',
    languagesCount: 'langues',
    translateOthers: 'Traduire vers les autres langues',
    translating: 'Traduction en cours...',
    translationHint: 'Édite le titre et la description localisés pour chaque langue active.',
    translationRequired: 'Au moins un titre traduit est requis.',
    practiceMode: 'Pratique',
    examMode: 'Examen',
    visibilityImmediate: 'Immédiat',
    visibilityScheduled: 'Planifié',
    visibilityNever: 'Jamais',
    dateFormat: 'dd/mm/yy',
    today: 'Aujourd\'hui',
    clear: 'Effacer',
    weekHeader: 'Sem',
    dayNames: ['dimanche', 'lundi', 'mardi', 'mercredi', 'jeudi', 'vendredi', 'samedi'],
    dayNamesShort: ['dim', 'lun', 'mar', 'mer', 'jeu', 'ven', 'sam'],
    dayNamesMin: ['di', 'lu', 'ma', 'me', 'je', 've', 'sa'],
    monthNames: ['janvier', 'février', 'mars', 'avril', 'mai', 'juin', 'juillet', 'août', 'septembre', 'octobre', 'novembre', 'décembre'],
    monthNamesShort: ['jan', 'fév', 'mar', 'avr', 'mai', 'jun', 'jul', 'aoû', 'sep', 'oct', 'nov', 'déc'],
  },
};

export function getQuizCreateUiText(lang: LanguageEnumDto): QuizCreateUiText {
  return QUIZ_CREATE_UI_TEXT[lang] ?? QUIZ_CREATE_UI_TEXT[LanguageEnumDto.Fr];
}
