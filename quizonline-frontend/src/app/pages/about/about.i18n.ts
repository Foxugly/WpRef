import {LanguageEnumDto} from '../../api/generated/model/language-enum';

export type AboutTechCard = {
  title: string;
  description: string;
  items: string[];
};

export type AboutUiText = {
  eyebrow: string;
  title: string;
  lead: string;
  viewRepository: string;
  featuresTitle: string;
  featuresIntro: string;
  features: string[];
  technicalTitle: string;
  technicalIntro: string;
  repositoryUrlLabel: string;
  cards: {
    repository: AboutTechCard;
    backend: AboutTechCard;
    frontend: AboutTechCard;
  };
};

const FR: AboutUiText = {
  eyebrow: 'À propos du projet',
  title: 'QuizOnline',
  lead: 'Plateforme de création, d\'attribution et de passage de quiz multilingues avec administration des contenus, des domaines et des sessions.',
  viewRepository: 'Voir le repository',
  featuresTitle: 'Fonctionnalités',
  featuresIntro: 'Le produit couvre à la fois l\'administration des contenus, la diffusion des quiz et le suivi des utilisateurs.',
  features: [
    'Inscription, connexion, confirmation d\'email, réinitialisation et changement de mot de passe.',
    'Choix de la langue d\'interface et synchronisation de la préférence utilisateur.',
    'Gestion des domaines avec propriétaire, staff, membres liés et domaine courant.',
    'Création, édition et suppression des sujets rattachés à un domaine.',
    'Banque de questions multilingues avec titres, descriptions, réponses et explications localisées.',
    'Questions configurées par mode pratique et mode examen avec activation par domaine.',
    'Support des médias externes via URLs YouTube normalisées et contrôlées.',
    'Composition de templates de quiz avec mode, durée, disponibilité, activation et visibilité des corrections.',
    'Création rapide de quiz et parcours complet de lecture, navigation et réponse aux questions.',
    'Attribution de templates aux utilisateurs liés à un domaine depuis l\'interface staff.',
    'Consultation des sessions, des résultats et des écrans de correction selon les règles métier.',
    'Centre d\'alertes pour suivre les actions et événements reliés aux quiz.',
  ],
  technicalTitle: 'Informations techniques',
  technicalIntro: 'Le projet est organisé comme un monorepo avec un frontend Angular, un backend Django REST et un contrat OpenAPI partagé.',
  repositoryUrlLabel: 'URL du dépôt',
  cards: {
    repository: {
      title: 'Repository',
      description: 'Code source, CI et artefacts de contrat dans le même dépôt.',
      items: [
        'Monorepo GitHub pour le frontend, le backend et les scripts de synchronisation.',
        'Génération et vérification des artefacts OpenAPI en CI.',
        'Workflows GitHub Actions pour les contrôles automatisés.',
      ],
    },
    backend: {
      title: 'Backend',
      description: 'API REST, logique métier et sécurité applicative.',
      items: [
        'Django et Django REST Framework',
        'drf-spectacular pour le contrat OpenAPI',
        'Simple JWT, django-filter et django-parler',
        'Celery, import-export et tests Python',
      ],
    },
    frontend: {
      title: 'Frontend',
      description: 'SPA d\'administration et de passage de quiz.',
      items: [
        'Angular 21, TypeScript et RxJS',
        'PrimeNG 21, PrimeFlex et PrimeIcons',
        'Client API généré depuis OpenAPI',
        'Karma, Jasmine et Playwright',
      ],
    },
  },
};

const EN: AboutUiText = {
  eyebrow: 'About the project',
  title: 'QuizOnline',
  lead: 'Platform for authoring, assigning and completing multilingual quizzes with content, domain and session administration.',
  viewRepository: 'View repository',
  featuresTitle: 'Features',
  featuresIntro: 'The product covers content administration, quiz delivery and user follow-up in the same workflow.',
  features: [
    'Sign up, sign in, email confirmation, password reset and password change flows.',
    'Interface language selection and synchronization with the user preference.',
    'Domain management with owner, staff, linked members and current domain selection.',
    'Create, edit and delete subjects linked to a domain.',
    'Multilingual question bank with localized titles, descriptions, answers and explanations.',
    'Question configuration for practice mode and exam mode with domain-level activation.',
    'External media support through normalized and validated YouTube URLs.',
    'Quiz template composition with mode, duration, availability, activation and review visibility rules.',
    'Quick quiz creation and full question answering flow with navigation and playback.',
    'Assignment of quiz templates to users linked to a domain from the staff interface.',
    'Session, result and review screens controlled by business visibility rules.',
    'Alert center for tracking quiz-related events and actions.',
  ],
  technicalTitle: 'Technical details',
  technicalIntro: 'The project is organized as a monorepo with an Angular frontend, a Django REST backend and a shared OpenAPI contract.',
  repositoryUrlLabel: 'Repository URL',
  cards: {
    repository: {
      title: 'Repository',
      description: 'Source code, CI and contract artifacts live in the same repository.',
      items: [
        'GitHub monorepo for frontend, backend and synchronization scripts.',
        'OpenAPI artifact generation and verification in CI.',
        'GitHub Actions workflows for automated checks.',
      ],
    },
    backend: {
      title: 'Backend',
      description: 'REST API, business rules and application security.',
      items: [
        'Django and Django REST Framework',
        'drf-spectacular for the OpenAPI contract',
        'Simple JWT, django-filter and django-parler',
        'Celery, import-export and Python tests',
      ],
    },
    frontend: {
      title: 'Frontend',
      description: 'Single-page app for administration and quiz delivery.',
      items: [
        'Angular 21, TypeScript and RxJS',
        'PrimeNG 21, PrimeFlex and PrimeIcons',
        'API client generated from OpenAPI',
        'Karma, Jasmine and Playwright',
      ],
    },
  },
};

const NL: AboutUiText = {
  eyebrow: 'Over het project',
  title: 'QuizOnline',
  lead: 'Platform voor het opstellen, toewijzen en afleggen van meertalige quizzen met beheer van content, domeinen en sessies.',
  viewRepository: 'Repository bekijken',
  featuresTitle: 'Functies',
  featuresIntro: 'Het product dekt contentbeheer, quizafname en gebruikersopvolging binnen dezelfde workflow.',
  features: [
    'Registratie, aanmelding, e-mailbevestiging, wachtwoordreset en wachtwoordwijziging.',
    'Keuze van de interfacetaal en synchronisatie met de gebruikersvoorkeur.',
    'Domeinbeheer met eigenaar, staff, gekoppelde leden en huidig domein.',
    'Onderwerpen aanmaken, bewerken en verwijderen binnen een domein.',
    'Meertalige vragenbank met gelokaliseerde titels, beschrijvingen, antwoorden en uitleg.',
    'Vraagconfiguratie voor oefenmodus en examenmodus met activering per domein.',
    'Ondersteuning voor externe media via genormaliseerde en gevalideerde YouTube-URLs.',
    'Quiztemplates met modus, duur, beschikbaarheid, activatie en zichtbaarheid van correcties.',
    'Snelle quizcreatie en volledige beantwoording met navigatie tussen vragen.',
    'Toewijzing van quiztemplates aan gebruikers die aan een domein gekoppeld zijn.',
    'Sessies, resultaten en correctieschermen volgens de bedrijfsregels.',
    'Meldingscentrum voor quizgerelateerde acties en gebeurtenissen.',
  ],
  technicalTitle: 'Technische informatie',
  technicalIntro: 'Het project is opgezet als monorepo met een Angular-frontend, een Django REST-backend en een gedeeld OpenAPI-contract.',
  repositoryUrlLabel: 'Repository-URL',
  cards: {
    repository: {
      title: 'Repository',
      description: 'Broncode, CI en contractartefacten zitten in hetzelfde depot.',
      items: [
        'GitHub-monorepo voor frontend, backend en synchronisatiescripts.',
        'Generatie en controle van OpenAPI-artefacten in CI.',
        'GitHub Actions-workflows voor automatische controles.',
      ],
    },
    backend: {
      title: 'Backend',
      description: 'REST API, bedrijfslogica en applicatieve beveiliging.',
      items: [
        'Django en Django REST Framework',
        'drf-spectacular voor het OpenAPI-contract',
        'Simple JWT, django-filter en django-parler',
        'Celery, import-export en Python-tests',
      ],
    },
    frontend: {
      title: 'Frontend',
      description: 'Single-page app voor beheer en quizafname.',
      items: [
        'Angular 21, TypeScript en RxJS',
        'PrimeNG 21, PrimeFlex en PrimeIcons',
        'API-client gegenereerd uit OpenAPI',
        'Karma, Jasmine en Playwright',
      ],
    },
  },
};

const IT: AboutUiText = {
  eyebrow: 'Informazioni sul progetto',
  title: 'QuizOnline',
  lead: 'Piattaforma per creare, assegnare e completare quiz multilingue con amministrazione di contenuti, domini e sessioni.',
  viewRepository: 'Vedi repository',
  featuresTitle: 'Funzionalita',
  featuresIntro: 'Il prodotto copre amministrazione dei contenuti, distribuzione dei quiz e monitoraggio degli utenti nello stesso flusso.',
  features: [
    'Registrazione, accesso, conferma email, reset password e cambio password.',
    'Scelta della lingua dell interfaccia e sincronizzazione con la preferenza utente.',
    'Gestione dei domini con proprietario, staff, membri collegati e dominio corrente.',
    'Creazione, modifica ed eliminazione degli argomenti legati a un dominio.',
    'Banca domande multilingue con titoli, descrizioni, risposte e spiegazioni localizzate.',
    'Configurazione delle domande per modalita pratica ed esame con attivazione per dominio.',
    'Supporto ai media esterni tramite URL YouTube normalizzate e validate.',
    'Composizione di template quiz con modalita, durata, disponibilita, attivazione e visibilita della revisione.',
    'Creazione rapida dei quiz e flusso completo di risposta con navigazione tra le domande.',
    'Assegnazione dei template agli utenti collegati a un dominio dall interfaccia staff.',
    'Schermate di sessione, risultati e revisione governate dalle regole di business.',
    'Centro avvisi per tracciare eventi e azioni legati ai quiz.',
  ],
  technicalTitle: 'Informazioni tecniche',
  technicalIntro: 'Il progetto e organizzato come monorepo con frontend Angular, backend Django REST e contratto OpenAPI condiviso.',
  repositoryUrlLabel: 'URL del repository',
  cards: {
    repository: {
      title: 'Repository',
      description: 'Codice sorgente, CI e artefatti del contratto nello stesso repository.',
      items: [
        'Monorepo GitHub per frontend, backend e script di sincronizzazione.',
        'Generazione e verifica degli artefatti OpenAPI in CI.',
        'Workflow GitHub Actions per i controlli automatici.',
      ],
    },
    backend: {
      title: 'Backend',
      description: 'API REST, logica di business e sicurezza applicativa.',
      items: [
        'Django e Django REST Framework',
        'drf-spectacular per il contratto OpenAPI',
        'Simple JWT, django-filter e django-parler',
        'Celery, import-export e test Python',
      ],
    },
    frontend: {
      title: 'Frontend',
      description: 'SPA per amministrazione e fruizione dei quiz.',
      items: [
        'Angular 21, TypeScript e RxJS',
        'PrimeNG 21, PrimeFlex e PrimeIcons',
        'Client API generato da OpenAPI',
        'Karma, Jasmine e Playwright',
      ],
    },
  },
};

const ES: AboutUiText = {
  eyebrow: 'Acerca del proyecto',
  title: 'QuizOnline',
  lead: 'Plataforma para crear, asignar y completar cuestionarios multilingues con administracion de contenidos, dominios y sesiones.',
  viewRepository: 'Ver repositorio',
  featuresTitle: 'Funciones',
  featuresIntro: 'El producto cubre administracion de contenidos, entrega de cuestionarios y seguimiento de usuarios en el mismo flujo.',
  features: [
    'Registro, inicio de sesion, confirmacion de correo, restablecimiento y cambio de contrasena.',
    'Seleccion del idioma de la interfaz y sincronizacion con la preferencia del usuario.',
    'Gestion de dominios con propietario, staff, miembros vinculados y dominio actual.',
    'Creacion, edicion y eliminacion de temas vinculados a un dominio.',
    'Banco de preguntas multilingue con titulos, descripciones, respuestas y explicaciones localizadas.',
    'Configuracion de preguntas para modo practica y modo examen con activacion por dominio.',
    'Soporte de medios externos mediante URLs de YouTube normalizadas y validadas.',
    'Composicion de plantillas de cuestionario con modo, duracion, disponibilidad, activacion y visibilidad de revision.',
    'Creacion rapida de cuestionarios y flujo completo de respuesta con navegacion entre preguntas.',
    'Asignacion de plantillas a usuarios vinculados a un dominio desde la interfaz staff.',
    'Pantallas de sesion, resultados y revision controladas por reglas de negocio.',
    'Centro de alertas para seguir eventos y acciones relacionados con los cuestionarios.',
  ],
  technicalTitle: 'Informacion tecnica',
  technicalIntro: 'El proyecto esta organizado como monorepo con frontend Angular, backend Django REST y contrato OpenAPI compartido.',
  repositoryUrlLabel: 'URL del repositorio',
  cards: {
    repository: {
      title: 'Repositorio',
      description: 'Codigo fuente, CI y artefactos del contrato en el mismo repositorio.',
      items: [
        'Monorepo GitHub para frontend, backend y scripts de sincronizacion.',
        'Generacion y verificacion de artefactos OpenAPI en CI.',
        'Workflows de GitHub Actions para controles automatizados.',
      ],
    },
    backend: {
      title: 'Backend',
      description: 'API REST, reglas de negocio y seguridad de la aplicacion.',
      items: [
        'Django y Django REST Framework',
        'drf-spectacular para el contrato OpenAPI',
        'Simple JWT, django-filter y django-parler',
        'Celery, import-export y pruebas Python',
      ],
    },
    frontend: {
      title: 'Frontend',
      description: 'SPA de administracion y ejecucion de cuestionarios.',
      items: [
        'Angular 21, TypeScript y RxJS',
        'PrimeNG 21, PrimeFlex y PrimeIcons',
        'Cliente API generado desde OpenAPI',
        'Karma, Jasmine y Playwright',
      ],
    },
  },
};

const UI_TEXT: Partial<Record<LanguageEnumDto, AboutUiText>> = {
  [LanguageEnumDto.Fr]: FR,
  [LanguageEnumDto.En]: EN,
  [LanguageEnumDto.Nl]: NL,
  [LanguageEnumDto.It]: IT,
  [LanguageEnumDto.Es]: ES,
};

export function getAboutUiText(lang: LanguageEnumDto | string | null | undefined): AboutUiText {
  return UI_TEXT[lang as LanguageEnumDto] ?? EN;
}
