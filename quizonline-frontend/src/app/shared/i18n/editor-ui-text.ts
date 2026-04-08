import {LanguageEnumDto} from '../../api/generated';

export type EditorUiText = {
  common: {
    back: string;
    cancel: string;
    clean: string;
    save: string;
    create: string;
    duplicate: string;
    loading: string;
    translateOthers: string;
    translating: string;
  };
  pages: {
    domainCreate: {title: string; subtitle: string;};
    domainEdit: {title: string; subtitle: string;};
    subjectCreate: {title: string; subtitle: string;};
    subjectEdit: {title: string; subtitle: string; questionsTitle: string; addQuestion: string; noQuestions: string; titleCol: string; actionsCol: string;};
    questionList?: {title: string; subtitle: string; searchPlaceholder: string; newQuestion: string; titleCol: string; activeCol: string; modesCol: string; domainsCol: string; subjectsCol: string; actionsCol: string; practice: string; exam: string;};
    questionCreate: {title: string; subtitle: string;};
    questionEdit: {title: string; subtitle: string;};
    quizQuick: {title: string; subtitle: string; submit: string;};
    quizCreate: {back: string; cancel: string; loading: string; createQuestionForTemplate: string; createQuestionForQuiz: string; createQuestion: string;};
  };
  domainForm: {
    translations: string;
    languagesCount: string;
    allowedLanguages: string;
    selectOneLanguage: string;
    titleLabel: string;
    description: string;
    titlePlaceholder: string;
    parameters: string;
    statusAccess: string;
    active: string;
    owner: string;
    staff: string;
    available: string;
    selected: string;
    readonly: string;
  };
  subjectForm: {
    domain: string;
    availableCount: string;
    chooseDomain: string;
    translations: string;
    languagesCount: string;
    name: string;
    description: string;
    namePlaceholder: string;
    required: string;
    emptyLanguages: string;
  };
  questionForm: {
    context: string;
    domain: string;
    domainUnavailable: string;
    chooseDomain: string;
    subjects: string;
    chooseSubjects: string;
    active: string;
    mode: string;
    practice: string;
    exam: string;
    content: string;
    title: string;
    titlePlaceholder: string;
    description: string;
    titleRequired: string;
    answers: string;
    correctAnswer: string;
    answerContent: string;
    deleteAnswer: string;
    addAnswer: string;
    explanation: string;
    media: string;
    noActiveLanguages: string;
    deleteQuestion: string;
  };
};

const FR: EditorUiText = {
  common: {
    back: 'Retour',
    cancel: 'Annuler',
    clean: 'Nettoyer',
    save: 'Enregistrer',
    create: 'Créer',
    duplicate: 'Dupliquer',
    loading: 'Chargement...',
    translateOthers: 'Traduire vers les autres langues',
    translating: 'Traduction en cours...',
  },
  pages: {
    domainCreate: {title: 'Créer le domaine', subtitle: 'Traductions, statut et accès'},
    domainEdit: {title: 'Éditer le domaine', subtitle: 'Traductions, statut et accès'},
    subjectCreate: {title: 'Créer un sujet', subtitle: 'Choix du domaine et traductions'},
    subjectEdit: {title: 'Éditer le sujet', subtitle: 'Traductions et contenu', questionsTitle: 'Questions', addQuestion: 'Ajouter', noQuestions: 'Aucune question.', titleCol: 'Titre', actionsCol: 'Actions'},
    questionCreate: {title: 'Créer une question', subtitle: 'Domaine, sujets, traductions et réponses'},
    questionEdit: {title: 'Modifier une question', subtitle: 'Contexte, traductions et réponses'},
    quizQuick: {title: 'Quiz rapide', subtitle: 'Génère une session de quiz à partir d un domaine et de sujets cibles.', submit: 'Générer le quiz'},
    quizCreate: {back: 'Retour', cancel: 'Annuler', loading: 'Chargement...', createQuestionForTemplate: 'Créer une question pour ce template', createQuestionForQuiz: 'Créer une question pour ce quiz', createQuestion: 'Créer la question'},
  },
  domainForm: {
    translations: 'Traductions',
    languagesCount: 'langue(s)',
    allowedLanguages: 'Langues autorisées',
    selectOneLanguage: 'Sélectionne au moins une langue.',
    titleLabel: 'Nom',
    description: 'Description',
    titlePlaceholder: 'Nom du domaine',
    parameters: 'Paramètres',
    statusAccess: 'active + accès',
    active: 'Actif',
    owner: 'Owner',
    staff: 'Staff',
    available: 'Disponibles',
    selected: 'Sélectionnés',
    readonly: 'readonly',
  },
  subjectForm: {
    domain: 'Domaine',
    availableCount: 'disponible(s)',
    chooseDomain: 'Choisir un domaine',
    translations: 'Traductions',
    languagesCount: 'langue(s)',
    name: 'Nom',
    description: 'Description',
    namePlaceholder: 'Nom du sujet',
    required: 'Champ requis.',
    emptyLanguages: "Ce domaine n'a pas de langues configurées.",
  },
  questionForm: {
    context: 'Contexte',
    domain: 'Domaine',
    domainUnavailable: 'Domaine non disponible',
    chooseDomain: 'Choisir un domaine',
    subjects: 'Sujets',
    chooseSubjects: 'Sélectionner un ou plusieurs sujets',
    active: 'Active',
    mode: 'Mode',
    practice: 'Pratique',
    exam: 'Examen',
    content: 'Contenu',
    title: 'Titre',
    titlePlaceholder: 'Titre...',
    description: 'Description',
    titleRequired: 'Titre requis.',
    answers: 'Réponses possibles',
    correctAnswer: 'Bonne réponse',
    answerContent: 'Contenu',
    deleteAnswer: 'Supprimer cette réponse',
    addAnswer: 'Ajouter une réponse',
    explanation: 'Explication',
    media: 'Médias',
    noActiveLanguages: 'Aucune langue active sur ce domaine.',
    deleteQuestion: 'Supprimer la question',
  },
};

const EN: EditorUiText = {
  common: {
    back: 'Back',
    cancel: 'Cancel',
    clean: 'Clear',
    save: 'Save',
    create: 'Create',
    duplicate: 'Duplicate',
    loading: 'Loading...',
    translateOthers: 'Translate to other languages',
    translating: 'Translating...',
  },
  pages: {
    domainCreate: {title: 'Create domain', subtitle: 'Translations, status and access'},
    domainEdit: {title: 'Edit domain', subtitle: 'Translations, status and access'},
    subjectCreate: {title: 'Create subject', subtitle: 'Domain selection and translations'},
    subjectEdit: {title: 'Edit subject', subtitle: 'Translations and content', questionsTitle: 'Questions', addQuestion: 'Add', noQuestions: 'No question.', titleCol: 'Title', actionsCol: 'Actions'},
    questionCreate: {title: 'Create question', subtitle: 'Domain, subjects, translations and answers'},
    questionEdit: {title: 'Edit question', subtitle: 'Context, translations and answers'},
    quizQuick: {title: 'Quick quiz', subtitle: 'Generate a quiz session from a domain and target subjects.', submit: 'Generate quiz'},
    quizCreate: {back: 'Back', cancel: 'Cancel', loading: 'Loading...', createQuestionForTemplate: 'Create a question for this template', createQuestionForQuiz: 'Create a question for this quiz', createQuestion: 'Create question'},
  },
  domainForm: {
    translations: 'Translations',
    languagesCount: 'language(s)',
    allowedLanguages: 'Allowed languages',
    selectOneLanguage: 'Select at least one language.',
    titleLabel: 'Name',
    description: 'Description',
    titlePlaceholder: 'Domain name',
    parameters: 'Settings',
    statusAccess: 'active + access',
    active: 'Active',
    owner: 'Owner',
    staff: 'Staff',
    available: 'Available',
    selected: 'Selected',
    readonly: 'readonly',
  },
  subjectForm: {
    domain: 'Domain',
    availableCount: 'available',
    chooseDomain: 'Choose a domain',
    translations: 'Translations',
    languagesCount: 'language(s)',
    name: 'Name',
    description: 'Description',
    namePlaceholder: 'Subject name',
    required: 'Required field.',
    emptyLanguages: 'This domain has no configured languages.',
  },
  questionForm: {
    context: 'Context',
    domain: 'Domain',
    domainUnavailable: 'Domain unavailable',
    chooseDomain: 'Choose a domain',
    subjects: 'Subjects',
    chooseSubjects: 'Select one or more subjects',
    active: 'Active',
    mode: 'Mode',
    practice: 'Practice',
    exam: 'Exam',
    content: 'Content',
    title: 'Title',
    titlePlaceholder: 'Title...',
    description: 'Description',
    titleRequired: 'Title is required.',
    answers: 'Answer options',
    correctAnswer: 'Correct answer',
    answerContent: 'Content',
    deleteAnswer: 'Delete this answer',
    addAnswer: 'Add answer',
    explanation: 'Explanation',
    media: 'Media',
    noActiveLanguages: 'No active language on this domain.',
    deleteQuestion: 'Delete question',
  },
};

const NL: EditorUiText = {
  ...EN,
  common: {...EN.common, back: 'Terug', cancel: 'Annuleren', clean: 'Wissen', save: 'Opslaan', create: 'Maken', duplicate: 'Dupliceren', loading: 'Laden...'},
  pages: {
    ...EN.pages,
    domainCreate: {title: 'Domein maken', subtitle: 'Vertalingen, status en toegang'},
    domainEdit: {title: 'Domein bewerken', subtitle: 'Vertalingen, status en toegang'},
    subjectCreate: {title: 'Onderwerp maken', subtitle: 'Domeinkeuze en vertalingen'},
    subjectEdit: {title: 'Onderwerp bewerken', subtitle: 'Vertalingen en inhoud', questionsTitle: 'Vragen', addQuestion: 'Toevoegen', noQuestions: 'Geen vraag.', titleCol: 'Titel', actionsCol: 'Acties'},
    questionCreate: {title: 'Vraag maken', subtitle: 'Domein, onderwerpen, vertalingen en antwoorden'},
    questionEdit: {title: 'Vraag bewerken', subtitle: 'Context, vertalingen en antwoorden'},
    quizQuick: {title: 'Snelle quiz', subtitle: 'Genereer een quizsessie vanuit een domein en doelonderwerpen.', submit: 'Quiz genereren'},
    quizCreate: {back: 'Terug', cancel: 'Annuleren', loading: 'Laden...', createQuestionForTemplate: 'Een vraag maken voor dit template', createQuestionForQuiz: 'Een vraag maken voor deze quiz', createQuestion: 'Vraag maken'},
  },
};

const IT: EditorUiText = {
  ...EN,
  common: {...EN.common, back: 'Indietro', cancel: 'Annulla', clean: 'Pulisci', save: 'Salva', create: 'Crea', duplicate: 'Duplica', loading: 'Caricamento...'},
  pages: {
    ...EN.pages,
    domainCreate: {title: 'Crea dominio', subtitle: 'Traduzioni, stato e accesso'},
    domainEdit: {title: 'Modifica dominio', subtitle: 'Traduzioni, stato e accesso'},
    subjectCreate: {title: 'Crea argomento', subtitle: 'Scelta del dominio e traduzioni'},
    subjectEdit: {title: 'Modifica argomento', subtitle: 'Traduzioni e contenuto', questionsTitle: 'Domande', addQuestion: 'Aggiungi', noQuestions: 'Nessuna domanda.', titleCol: 'Titolo', actionsCol: 'Azioni'},
    questionCreate: {title: 'Crea domanda', subtitle: 'Dominio, argomenti, traduzioni e risposte'},
    questionEdit: {title: 'Modifica domanda', subtitle: 'Contesto, traduzioni e risposte'},
    quizQuick: {title: 'Quiz rapido', subtitle: 'Genera una sessione quiz da un dominio e da argomenti mirati.', submit: 'Genera quiz'},
    quizCreate: {back: 'Indietro', cancel: 'Annulla', loading: 'Caricamento...', createQuestionForTemplate: 'Crea una domanda per questo template', createQuestionForQuiz: 'Crea una domanda per questo quiz', createQuestion: 'Crea domanda'},
  },
};

const ES: EditorUiText = {
  ...EN,
  common: {...EN.common, back: 'Volver', cancel: 'Cancelar', clean: 'Limpiar', save: 'Guardar', create: 'Crear', duplicate: 'Duplicar', loading: 'Cargando...'},
  pages: {
    ...EN.pages,
    domainCreate: {title: 'Crear dominio', subtitle: 'Traducciones, estado y acceso'},
    domainEdit: {title: 'Editar dominio', subtitle: 'Traducciones, estado y acceso'},
    subjectCreate: {title: 'Crear tema', subtitle: 'Eleccion del dominio y traducciones'},
    subjectEdit: {title: 'Editar tema', subtitle: 'Traducciones y contenido', questionsTitle: 'Preguntas', addQuestion: 'Anadir', noQuestions: 'Ninguna pregunta.', titleCol: 'Titulo', actionsCol: 'Acciones'},
    questionCreate: {title: 'Crear pregunta', subtitle: 'Dominio, temas, traducciones y respuestas'},
    questionEdit: {title: 'Editar pregunta', subtitle: 'Contexto, traducciones y respuestas'},
    quizQuick: {title: 'Quiz rapido', subtitle: 'Genera una sesion de quiz a partir de un dominio y temas objetivo.', submit: 'Generar quiz'},
    quizCreate: {back: 'Volver', cancel: 'Cancelar', loading: 'Cargando...', createQuestionForTemplate: 'Crear una pregunta para esta plantilla', createQuestionForQuiz: 'Crear una pregunta para este quiz', createQuestion: 'Crear pregunta'},
  },
};

const TEXTS: Partial<Record<LanguageEnumDto, EditorUiText>> = {
  [LanguageEnumDto.Fr]: FR,
  [LanguageEnumDto.En]: EN,
  [LanguageEnumDto.Nl]: NL,
  [LanguageEnumDto.It]: IT,
  [LanguageEnumDto.Es]: ES,
};

export function getEditorUiText(lang: LanguageEnumDto | string | null | undefined): EditorUiText {
  return TEXTS[lang as LanguageEnumDto] ?? EN;
}
