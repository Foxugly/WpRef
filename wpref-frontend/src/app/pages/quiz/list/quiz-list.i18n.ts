import { LanguageEnumDto } from '../../../api/generated';

export type QuizListUiText = {
  page: {
    title: string;
    subtitle: string;
    searchPlaceholder: string;
    compose: string;
    quickCreate: string;
  };
  tabs: {
    templates: string;
    sessions: string;
  };
  templates: {
    empty: string;
    headers: {
      title: string;
      mode: string;
      questions: string;
      owner: string;
      public: string;
      active: string;
      available: string;
      availabilityWindow: string;
      actions: string;
    };
    modePractice: string;
    modeExam: string;
    permanent: string;
    yes: string;
    no: string;
    actions: {
      start: string;
      assign: string;
      results: string;
      edit: string;
      delete: string;
    };
  };
  assignDialog: {
    header: string;
    intro: string;
    noRecipients: string;
    searchPlaceholder: string;
    selectAll: string;
    clearSelection: string;
    roleAll: string;
    submit: string;
    cancel: string;
    roleOwner: string;
    roleStaff: string;
    roleMember: string;
  };
  messages: {
    assignSuccess: (count: number) => string;
    assignError: string;
    loadError: string;
    resultsError: string;
    createError: string;
  };
};

const FR: QuizListUiText = {
  page: {
    title: 'Quiz',
    subtitle: 'Recherche, templates et sessions',
    searchPlaceholder: 'Rechercher...',
    compose: 'Nouveau template',
    quickCreate: 'Rapide',
  },
  tabs: { templates: 'Templates', sessions: 'Mes quiz' },
  templates: {
    empty: 'Aucun template visible.',
    headers: {
      title: 'Titre',
      mode: 'Mode',
      questions: 'Questions',
      owner: 'Owner',
      public: 'Public',
      active: 'Actif',
      available: 'Disponible',
      availabilityWindow: 'Disponibilité',
      actions: 'Actions',
    },
    modePractice: 'Pratique',
    modeExam: 'Examen',
    permanent: 'Permanent',
    yes: 'Oui',
    no: 'Non',
    actions: {
      start: 'Commencer ce quiz',
      assign: 'Envoyer ce quiz à un utilisateur lié au domaine',
      results: 'Voir les résultats des quiz envoyés',
      edit: 'Modifier ce template',
      delete: 'Supprimer ce template',
    },
  },
  assignDialog: {
    header: 'Envoyer le quiz',
    intro: 'Sélectionne une ou plusieurs personnes liées à ce domaine pour leur envoyer',
    noRecipients: 'Aucun autre utilisateur lié à ce domaine.',
    searchPlaceholder: 'Filtrer par nom',
    selectAll: 'Tout sélectionner',
    clearSelection: 'Tout désélectionner',
    roleAll: 'Tous les rôles',
    submit: 'Envoyer',
    cancel: 'Annuler',
    roleOwner: 'Propriétaire',
    roleStaff: 'Staff',
    roleMember: 'Membre lié',
  },
  messages: {
    assignSuccess: (count) => `${count} quiz envoyé(s).`,
    assignError: 'Impossible d envoyer ce quiz.',
    loadError: 'Impossible de charger les quiz.',
    resultsError: 'Impossible de charger les résultats.',
    createError: 'Impossible de créer ce quiz.',
  },
};

const EN: QuizListUiText = {
  page: {
    title: 'Quizzes',
    subtitle: 'Search, templates and sessions',
    searchPlaceholder: 'Search...',
    compose: 'New template',
    quickCreate: 'Quick',
  },
  tabs: { templates: 'Templates', sessions: 'My quizzes' },
  templates: {
    empty: 'No visible template.',
    headers: {
      title: 'Title',
      mode: 'Mode',
      questions: 'Questions',
      owner: 'Owner',
      public: 'Public',
      active: 'Active',
      available: 'Available',
      availabilityWindow: 'Availability',
      actions: 'Actions',
    },
    modePractice: 'Practice',
    modeExam: 'Exam',
    permanent: 'Permanent',
    yes: 'Yes',
    no: 'No',
    actions: {
      start: 'Start this quiz',
      assign: 'Send this quiz to a user linked to the domain',
      results: 'View results for assigned quizzes',
      edit: 'Edit this template',
      delete: 'Delete this template',
    },
  },
  assignDialog: {
    header: 'Send quiz',
    intro: 'Select one or more people linked to this domain to send',
    noRecipients: 'No other user is linked to this domain.',
    searchPlaceholder: 'Filter by name',
    selectAll: 'Select all',
    clearSelection: 'Clear selection',
    roleAll: 'All roles',
    submit: 'Send',
    cancel: 'Cancel',
    roleOwner: 'Owner',
    roleStaff: 'Staff',
    roleMember: 'Linked member',
  },
  messages: {
    assignSuccess: (count) => `${count} quiz(es) sent.`,
    assignError: 'Unable to send this quiz.',
    loadError: 'Unable to load quizzes.',
    resultsError: 'Unable to load results.',
    createError: 'Unable to create this quiz.',
  },
};

const NL: QuizListUiText = {
  page: {
    title: 'Quizzen',
    subtitle: 'Zoeken, templates en sessies',
    searchPlaceholder: 'Zoeken...',
    compose: 'Nieuw template',
    quickCreate: 'Snel',
  },
  tabs: { templates: 'Templates', sessions: 'Mijn quizzen' },
  templates: {
    empty: 'Geen zichtbaar template.',
    headers: {
      title: 'Titel',
      mode: 'Modus',
      questions: 'Vragen',
      owner: 'Owner',
      public: 'Publiek',
      active: 'Actief',
      available: 'Beschikbaar',
      availabilityWindow: 'Beschikbaarheid',
      actions: 'Acties',
    },
    modePractice: 'Praktijk',
    modeExam: 'Examen',
    permanent: 'Permanent',
    yes: 'Ja',
    no: 'Nee',
    actions: {
      start: 'Deze quiz starten',
      assign: 'Deze quiz naar een gebruiker sturen die aan het domein gekoppeld is',
      results: 'Resultaten van verzonden quizzen bekijken',
      edit: 'Dit template bewerken',
      delete: 'Dit template verwijderen',
    },
  },
  assignDialog: {
    header: 'Quiz verzenden',
    intro: 'Selecteer een of meer personen die aan dit domein gekoppeld zijn om',
    noRecipients: 'Geen andere gebruiker gekoppeld aan dit domein.',
    searchPlaceholder: 'Filter op naam',
    selectAll: 'Alles selecteren',
    clearSelection: 'Selectie wissen',
    roleAll: 'Alle rollen',
    submit: 'Verzenden',
    cancel: 'Annuleren',
    roleOwner: 'Eigenaar',
    roleStaff: 'Staff',
    roleMember: 'Gekoppeld lid',
  },
  messages: {
    assignSuccess: (count) => `${count} quiz(zen) verzonden.`,
    assignError: 'Kan deze quiz niet verzenden.',
    loadError: 'Kan quizzen niet laden.',
    resultsError: 'Kan resultaten niet laden.',
    createError: 'Kan deze quiz niet maken.',
  },
};

const IT: QuizListUiText = {
  page: {
    title: 'Quiz',
    subtitle: 'Ricerca, template e sessioni',
    searchPlaceholder: 'Cerca...',
    compose: 'Nuovo template',
    quickCreate: 'Rapido',
  },
  tabs: { templates: 'Template', sessions: 'I miei quiz' },
  templates: {
    empty: 'Nessun template visibile.',
    headers: {
      title: 'Titolo',
      mode: 'Modalita',
      questions: 'Domande',
      owner: 'Owner',
      public: 'Pubblico',
      active: 'Attivo',
      available: 'Disponibile',
      availabilityWindow: 'Disponibilita',
      actions: 'Azioni',
    },
    modePractice: 'Pratica',
    modeExam: 'Esame',
    permanent: 'Permanente',
    yes: 'Si',
    no: 'No',
    actions: {
      start: 'Avvia questo quiz',
      assign: 'Invia questo quiz a un utente collegato al dominio',
      results: 'Vedi i risultati dei quiz inviati',
      edit: 'Modifica questo template',
      delete: 'Elimina questo template',
    },
  },
  assignDialog: {
    header: 'Invia quiz',
    intro: 'Seleziona una o piu persone collegate a questo dominio per inviare',
    noRecipients: 'Nessun altro utente collegato a questo dominio.',
    searchPlaceholder: 'Filtra per nome',
    selectAll: 'Seleziona tutto',
    clearSelection: 'Deseleziona tutto',
    roleAll: 'Tutti i ruoli',
    submit: 'Invia',
    cancel: 'Annulla',
    roleOwner: 'Proprietario',
    roleStaff: 'Staff',
    roleMember: 'Membro collegato',
  },
  messages: {
    assignSuccess: (count) => `${count} quiz inviato/i.`,
    assignError: 'Impossibile inviare questo quiz.',
    loadError: 'Impossibile caricare i quiz.',
    resultsError: 'Impossibile caricare i risultati.',
    createError: 'Impossibile creare questo quiz.',
  },
};

const ES: QuizListUiText = {
  page: {
    title: 'Cuestionarios',
    subtitle: 'Busqueda, plantillas y sesiones',
    searchPlaceholder: 'Buscar...',
    compose: 'Nueva plantilla',
    quickCreate: 'Rapido',
  },
  tabs: { templates: 'Plantillas', sessions: 'Mis cuestionarios' },
  templates: {
    empty: 'No hay plantillas visibles.',
    headers: {
      title: 'Titulo',
      mode: 'Modo',
      questions: 'Preguntas',
      owner: 'Owner',
      public: 'Publico',
      active: 'Activo',
      available: 'Disponible',
      availabilityWindow: 'Disponibilidad',
      actions: 'Acciones',
    },
    modePractice: 'Practica',
    modeExam: 'Examen',
    permanent: 'Permanente',
    yes: 'Si',
    no: 'No',
    actions: {
      start: 'Iniciar este cuestionario',
      assign: 'Enviar este cuestionario a un usuario vinculado al dominio',
      results: 'Ver resultados de los cuestionarios enviados',
      edit: 'Editar esta plantilla',
      delete: 'Eliminar esta plantilla',
    },
  },
  assignDialog: {
    header: 'Enviar cuestionario',
    intro: 'Selecciona una o varias personas vinculadas a este dominio para enviar',
    noRecipients: 'No hay ningun otro usuario vinculado a este dominio.',
    searchPlaceholder: 'Filtrar por nombre',
    selectAll: 'Seleccionar todo',
    clearSelection: 'Deseleccionar todo',
    roleAll: 'Todos los roles',
    submit: 'Enviar',
    cancel: 'Cancelar',
    roleOwner: 'Propietario',
    roleStaff: 'Staff',
    roleMember: 'Miembro vinculado',
  },
  messages: {
    assignSuccess: (count) => `${count} cuestionario(s) enviado(s).`,
    assignError: 'No se puede enviar este cuestionario.',
    loadError: 'No se pueden cargar los cuestionarios.',
    resultsError: 'No se pueden cargar los resultados.',
    createError: 'No se puede crear este cuestionario.',
  },
};

const UI_TEXT: Partial<Record<LanguageEnumDto, QuizListUiText>> = {
  [LanguageEnumDto.Fr]: FR,
  [LanguageEnumDto.En]: EN,
  [LanguageEnumDto.Nl]: NL,
  [LanguageEnumDto.It]: IT,
  [LanguageEnumDto.Es]: ES,
};

export function getQuizListUiText(lang: LanguageEnumDto | string | null | undefined): QuizListUiText {
  return UI_TEXT[lang as LanguageEnumDto] ?? EN;
}
