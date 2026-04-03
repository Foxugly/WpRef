import {LanguageEnumDto} from '../../api/generated/model/language-enum';

export type UiText = {
  topmenu: {
    quiz: string;
    domains: string;
    subjects: string;
    questions: string;
    about: string;
    alertsAria: string;
    currentDomain: string;
    ownedDomains: string;
    staffDomains: string;
    linkedDomains: string;
    noDomains: string;
    preferences: string;
  };
  userMenu: {
    preferences: string;
    changePassword: string;
    logout: string;
    login: string;
  };
  footer: {
    baseline: string;
    version: string;
  };
  home: {
    eyebrow: string;
    lead: string;
    primaryLoggedIn: string;
    primaryLoggedOut: string;
    secondaryAdmin: string;
    secondaryLoggedOut: string;
    mode: string;
    modeStaff: string;
    modeUser: string;
    modeVisitor: string;
    languages: string;
    features: string;
    featuresValue: string;
    highlights: Array<{title: string; description: string;}>;
    capabilitiesTitle: string;
    capabilities: string[];
    quickLinksTitle: string;
    quickLinks: {
      catalog: string;
      preferences: string;
      about: string;
    };
  };
  login: {
    eyebrow: string;
    title: string;
    subtitle: string;
    username: string;
    usernamePlaceholder: string;
    usernameError: string;
    password: string;
    passwordPlaceholder: string;
    passwordError: string;
    remember: string;
    forgotPassword: string;
    submit: string;
    noAccount: string;
    createAccount: string;
    invalidCredentials: string;
    confirmEmailRequired: string;
  };
  register: {
    title: string;
    subtitle: string;
    back: string;
    create: string;
    loading: string;
    identityTitle: string;
    identityBadge: string;
    securityTitle: string;
    securityBadge: string;
    username: string;
    email: string;
    firstName: string;
    lastName: string;
    language: string;
    domains: string;
    chooseDomains: string;
    domainsHint: string;
    chooseLanguage: string;
    password: string;
    confirmPassword: string;
    createAccount: string;
    cancel: string;
    usernameRequired: string;
    emailRequired: string;
    emailInvalid: string;
    firstNameRequired: string;
    lastNameRequired: string;
    languageRequired: string;
    passwordRequired: string;
    passwordMin: string;
    confirmRequired: string;
    passwordMismatch: string;
    success: string;
    loadLanguagesError: string;
    loadDomainsError: string;
    submitError: string;
  };
  registerPending: {
    title: string;
    subtitle: string;
    lead: string;
    body: string;
    login: string;
  };
  changePassword: {
    title: string;
    subtitle: string;
    oldPassword: string;
    newPassword: string;
    confirmNewPassword: string;
    oldPasswordRequired: string;
    newPasswordRequired: string;
    newPasswordMin: string;
    confirmRequired: string;
    mismatch: string;
    submit: string;
    forceMessage: string;
    success: string;
    error: string;
  };
  preferences: {
    eyebrow: string;
    title: string;
    subtitle: string;
    profileTitle: string;
    profileSubtitle: string;
    summaryTitle: string;
    summarySubtitle: string;
    loading: string;
    username: string;
    email: string;
    firstName: string;
    lastName: string;
    language: string;
    domains: string;
    chooseDomains: string;
    currentDomain: string;
    chooseLanguage: string;
    noDomain: string;
    save: string;
    changePassword: string;
    role: string;
    user: string;
    currentDomainLabel: string;
    managedDomains: string;
    ownedDomains: string;
    activeAccount: string;
    yes: string;
    no: string;
    roleSuperuser: string;
    roleStaff: string;
    roleUser: string;
    roleOwner: string;
    roleMember: string;
    domainsTitle: string;
    domainsSubtitle: string;
    linkedDomainsList: string;
    currentBadge: string;
    setCurrent: string;
    unlinkDomain: string;
    addDomain: string;
    noMoreDomains: string;
    linkSelectedDomains: string;
    cancel: string;
    ownerLabel: string;
    deleteDomain: string;
    deleteDomainSuccess: string;
    deleteDomainError: string;
    loadError: string;
    saveError: string;
    saveSuccess: string;
    userMissing: string;
  };
};

const FR: UiText = {
  topmenu: {
    quiz: 'Quiz',
    domains: 'Domaines',
    subjects: 'Sujets',
    questions: 'Questions',
    about: 'À propos',
    alertsAria: 'Alertes',
    currentDomain: 'Domaine courant',
    ownedDomains: 'Mes domaines',
    staffDomains: 'Domaines où je suis staff',
    linkedDomains: 'Domaines liés',
    noDomains: 'Aucun domaine',
    preferences: 'Préférences',
  },
  userMenu: {
    preferences: 'Préférences',
    changePassword: 'Changer le mot de passe',
    logout: 'Déconnexion',
    login: 'Connexion',
  },
  footer: {
    baseline: 'Plateforme de quiz et de gestion de contenu par domaine.',
    version: 'Version',
  },
  home: {
    eyebrow: 'Quiz, templates et correction',
    lead: 'Un espace unique pour composer des quiz, les assigner, les passer et suivre les retours.',
    primaryLoggedIn: 'Voir mes quiz',
    primaryLoggedOut: 'Se connecter',
    secondaryAdmin: 'Composer un template',
    secondaryLoggedOut: 'Créer un compte',
    mode: 'Mode',
    modeStaff: 'Staff',
    modeUser: 'Utilisateur connecte',
    modeVisitor: 'Visiteur',
    languages: 'Langues',
    features: 'Fonctions',
    featuresValue: 'Quiz, alertes, affectations, correction',
    highlights: [
      {title: 'Passage fluide', description: 'Quiz pratiques ou examens avec timer, reprise et correction localisee.'},
      {title: 'Edition staff', description: 'Questions multimedia, sujets, domaines et templates dans une interface unifiee.'},
      {title: 'Suivi réel', description: 'Affectations, résultats, alertes et corrections disponibles selon les règles métier.'},
    ],
    capabilitiesTitle: 'Ce que vous pouvez faire',
    capabilities: [
      'Créer et organiser des banques de questions par domaine et sujet.',
      'Composer des quiz pratiques ou examens avec règles de visibilité.',
      'Assigner un quiz à des utilisateurs et suivre leurs résultats.',
      'Relire une session en correction avec bonnes réponses et explications.',
    ],
    quickLinksTitle: 'Acces rapides',
    quickLinks: {
      catalog: 'Catalogue des quiz',
      preferences: 'Préférences',
      about: 'À propos',
    },
  },
  login: {
    eyebrow: 'Connexion',
    title: 'Acceder a votre espace',
    subtitle: 'Identifiez-vous pour continuer.',
    username: 'Utilisateur',
    usernamePlaceholder: 'Votre identifiant',
    usernameError: 'Nom d utilisateur requis (min. 3 caracteres)',
    password: 'Mot de passe',
    passwordPlaceholder: 'Votre mot de passe',
    passwordError: 'Mot de passe requis (min. 4 caracteres)',
    remember: 'Se souvenir de moi',
    forgotPassword: 'Mot de passe oublie ?',
    submit: 'Se connecter',
    noAccount: 'Pas encore de compte ?',
    createAccount: 'Créer un compte',
    invalidCredentials: 'Identifiants invalides. Réessaie.',
    confirmEmailRequired: 'Confirme ton adresse email avant de te connecter.',
  },
  register: {
    title: 'Créer un compte',
    subtitle: 'Identite, langue et securite',
    back: 'Retour',
    create: 'Créer',
    loading: 'Chargement...',
    identityTitle: 'Identite',
    identityBadge: 'profil',
    securityTitle: 'Securite',
    securityBadge: 'mot de passe',
    username: "Nom d'utilisateur",
    email: 'Adresse e-mail',
    firstName: 'Prénom',
    lastName: 'Nom',
    language: 'Langue',
    domains: 'Domaines',
    chooseDomains: 'Choisir un ou plusieurs domaines',
    domainsHint: 'Sélectionnez les domaines auxquels vous souhaitez être rattaché.',
    chooseLanguage: 'Choisir une langue',
    password: 'Mot de passe',
    confirmPassword: 'Confirmer le mot de passe',
    createAccount: 'Créer mon compte',
    cancel: 'Annuler',
    usernameRequired: "Nom d'utilisateur obligatoire.",
    emailRequired: "L'adresse e-mail est obligatoire.",
    emailInvalid: "L'adresse e-mail n'est pas valide.",
    firstNameRequired: 'Le prénom est obligatoire.',
    lastNameRequired: 'Le nom est obligatoire.',
    languageRequired: 'La langue est obligatoire.',
    passwordRequired: 'Le mot de passe est obligatoire.',
    passwordMin: 'Minimum 8 caractères.',
    confirmRequired: 'La confirmation est obligatoire.',
    passwordMismatch: 'Les mots de passe ne correspondent pas.',
    success: 'Votre compte a été créé. Vérifiez votre boîte mail pour confirmer votre inscription.',
    loadLanguagesError: 'Impossible de charger la liste des langues.',
    loadDomainsError: 'Impossible de charger la liste des domaines.',
    submitError: "L'inscription a echoue. Verifiez les informations et reessayez.",
  },
  registerPending: {
    title: 'Inscription créée',
    subtitle: 'Confirmation de votre adresse email',
    lead: 'Votre compte a bien été créé.',
    body: 'Consultez maintenant votre boite mail et cliquez sur le lien de confirmation pour activer votre inscription.',
    login: 'Aller a la connexion',
  },
  changePassword: {
    title: 'WpRef',
    subtitle: 'Reinitialiser mon mot de passe',
    oldPassword: 'Mot de passe actuel',
    newPassword: 'Nouveau mot de passe',
    confirmNewPassword: 'Confirmer le nouveau mot de passe',
    oldPasswordRequired: 'Le mot de passe actuel est obligatoire.',
    newPasswordRequired: 'Le nouveau mot de passe est obligatoire.',
    newPasswordMin: 'Le nouveau mot de passe doit contenir au moins 8 caracteres.',
    confirmRequired: 'La confirmation est obligatoire.',
    mismatch: 'Les mots de passe ne correspondent pas.',
    submit: 'Changer le mot de passe',
    forceMessage: 'Le changement de mot de passe est requis avant de continuer.',
    success: 'Votre mot de passe a ete modifie.',
    error: 'Une erreur est survenue lors de la modification du mot de passe.',
  },
  preferences: {
    eyebrow: 'Mon compte',
    title: 'Préférences',
    subtitle: 'Gérez votre profil, votre langue d interface et votre domaine courant.',
    profileTitle: 'Profil',
    profileSubtitle: 'Informations personnelles et préférences d affichage.',
    summaryTitle: 'Résumé',
    summarySubtitle: 'Vue rapide de votre compte courant.',
    loading: 'Chargement...',
    username: "Nom d'utilisateur",
    email: 'Email',
    firstName: 'Prénom',
    lastName: 'Nom',
    language: 'Langue',
    domains: 'Domaines liés',
    chooseDomains: 'Choisir les domaines liés',
    currentDomain: 'Domaine courant',
    chooseLanguage: 'Choisir une langue',
    noDomain: 'Aucun domaine',
    save: 'Enregistrer',
    changePassword: 'Changer le mot de passe',
    role: 'Rôle',
    user: 'Utilisateur',
    currentDomainLabel: 'Domaine actuel',
    managedDomains: 'Domaines gérés',
    ownedDomains: 'Domaines possédés',
    activeAccount: 'Compte actif',
    yes: 'Oui',
    no: 'Non',
    roleSuperuser: 'Superuser',
    roleStaff: 'Staff',
    roleUser: 'Utilisateur',
    roleOwner: 'Propriétaire',
    roleMember: 'Membre lié',
    domainsTitle: 'Domaines',
    domainsSubtitle: 'Choisissez votre domaine courant et gérez vos domaines liés.',
    linkedDomainsList: 'Domaines visibles',
    currentBadge: 'Courant',
    setCurrent: 'Définir comme courant',
    unlinkDomain: 'Se délier',
    addDomain: 'Lier un domaine',
    noMoreDomains: 'Aucun autre domaine disponible.',
    linkSelectedDomains: 'Lier la sélection',
    cancel: 'Annuler',
    ownerLabel: 'Propriétaire :',
    deleteDomain: 'Supprimer',
    deleteDomainSuccess: 'Domaine supprimé.',
    deleteDomainError: 'Impossible de supprimer ce domaine.',
    loadError: 'Impossible de charger vos préférences.',
    saveError: "Impossible d'enregistrer les préférences.",
    saveSuccess: 'Préférences enregistrées.',
    userMissing: 'Utilisateur introuvable.',
  },
};

const EN: UiText = {
  topmenu: {quiz: 'Quizzes', domains: 'Domains', subjects: 'Subjects', questions: 'Questions', about: 'About', alertsAria: 'Alerts', currentDomain: 'Current domain', ownedDomains: 'My domains', staffDomains: 'Domains where I am staff', linkedDomains: 'Linked domains', noDomains: 'No domain', preferences: 'Preferences'},
  userMenu: {preferences: 'Preferences', changePassword: 'Change password', logout: 'Logout', login: 'Login'},
  footer: {baseline: 'Quiz and domain content management platform.', version: 'Version'},
  home: {
    eyebrow: 'Quizzes, templates and review',
    lead: 'One place to build quizzes, assign them, complete them and review feedback.',
    primaryLoggedIn: 'View my quizzes',
    primaryLoggedOut: 'Sign in',
    secondaryAdmin: 'Create a template',
    secondaryLoggedOut: 'Create an account',
    mode: 'Mode',
    modeStaff: 'Staff',
    modeUser: 'Signed-in user',
    modeVisitor: 'Visitor',
    languages: 'Languages',
    features: 'Features',
    featuresValue: 'Quizzes, alerts, assignments, review',
    highlights: [
      {title: 'Smooth delivery', description: 'Practice and exam flows with timer, resume support and localized review.'},
      {title: 'Staff editing', description: 'Multimedia questions, subjects, domains and templates in one workspace.'},
      {title: 'Live follow-up', description: 'Assignments, results, alerts and review rules in the same product.'},
    ],
    capabilitiesTitle: 'What you can do',
    capabilities: [
      'Build and organize question banks by domain and subject.',
      'Create practice or exam quizzes with visibility rules.',
      'Assign a quiz to users and monitor their results.',
      'Review a session with correct answers and explanations.',
    ],
    quickLinksTitle: 'Quick links',
    quickLinks: {catalog: 'Quiz catalog', preferences: 'Preferences', about: 'About'},
  },
  login: {
    eyebrow: 'Login', title: 'Access your workspace', subtitle: 'Sign in to continue.',
    username: 'Username', usernamePlaceholder: 'Your username', usernameError: 'Username is required (min. 3 characters)',
    password: 'Password', passwordPlaceholder: 'Your password', passwordError: 'Password is required (min. 4 characters)',
    remember: 'Remember me', forgotPassword: 'Forgot password?', submit: 'Sign in', noAccount: 'No account yet?',
    createAccount: 'Create account', invalidCredentials: 'Invalid credentials. Try again.', confirmEmailRequired: 'Confirm your email address before signing in.',
  },
  register: {
    title: 'Create an account', subtitle: 'Identity, language and security', back: 'Back', create: 'Create', loading: 'Loading...',
    identityTitle: 'Identity', identityBadge: 'profile', securityTitle: 'Security', securityBadge: 'password',
    username: 'Username', email: 'Email address', firstName: 'First name', lastName: 'Last name', language: 'Language',
    domains: 'Domains', chooseDomains: 'Choose one or more domains', domainsHint: 'Select the domains you want to be linked to.',
    chooseLanguage: 'Choose a language', password: 'Password', confirmPassword: 'Confirm password', createAccount: 'Create my account',
    cancel: 'Cancel', usernameRequired: 'Username is required.', emailRequired: 'Email address is required.', emailInvalid: 'Email address is not valid.',
    firstNameRequired: 'First name is required.', lastNameRequired: 'Last name is required.', languageRequired: 'Language is required.',
    passwordRequired: 'Password is required.', passwordMin: 'Minimum 8 characters.', confirmRequired: 'Confirmation is required.',
    passwordMismatch: 'Passwords do not match.', success: 'Your account has been created. Check your mailbox to confirm your registration.',
    loadLanguagesError: 'Unable to load languages.', loadDomainsError: 'Unable to load domains.', submitError: 'Registration failed. Check the information and try again.',
  },
  registerPending: {
    title: 'Account created',
    subtitle: 'Confirm your email address',
    lead: 'Your account has been created successfully.',
    body: 'Check your mailbox now and click the confirmation link to activate your registration.',
    login: 'Go to login',
  },
  changePassword: {
    title: 'WpRef', subtitle: 'Reset my password', oldPassword: 'Current password', newPassword: 'New password',
    confirmNewPassword: 'Confirm new password', oldPasswordRequired: 'Current password is required.', newPasswordRequired: 'New password is required.',
    newPasswordMin: 'The new password must be at least 8 characters long.', confirmRequired: 'Confirmation is required.', mismatch: 'Passwords do not match.',
    submit: 'Change password', forceMessage: 'Password change is required before continuing.', success: 'Your password has been changed.',
    error: 'An error occurred while changing the password.',
  },
  preferences: {
    eyebrow: 'My account', title: 'Preferences', subtitle: 'Manage your profile, interface language and current domain.',
    profileTitle: 'Profile', profileSubtitle: 'Personal information and display preferences.', summaryTitle: 'Summary',
    summarySubtitle: 'Quick view of your current account.', loading: 'Loading...', username: 'Username', email: 'Email',
    firstName: 'First name', lastName: 'Last name', language: 'Language', domains: 'Linked domains', chooseDomains: 'Choose linked domains', currentDomain: 'Current domain', chooseLanguage: 'Choose a language',
    noDomain: 'No domain', save: 'Save', changePassword: 'Change password', role: 'Role', user: 'User', currentDomainLabel: 'Current domain',
    managedDomains: 'Managed domains', ownedDomains: 'Owned domains', activeAccount: 'Active account', yes: 'Yes', no: 'No',
    roleSuperuser: 'Superuser', roleStaff: 'Staff', roleUser: 'User', roleOwner: 'Owner', roleMember: 'Linked member', domainsTitle: 'Domains', domainsSubtitle: 'Manage your linked domains and choose the current one.', linkedDomainsList: 'Visible domains', currentBadge: 'Current', setCurrent: 'Set current', unlinkDomain: 'Unlink', addDomain: 'Link a domain', noMoreDomains: 'No additional domain available.', linkSelectedDomains: 'Link selection', cancel: 'Cancel', ownerLabel: 'Owner:', deleteDomain: 'Delete', deleteDomainSuccess: 'Domain deleted.', deleteDomainError: 'Unable to delete this domain.', loadError: 'Unable to load your preferences.',
    saveError: 'Unable to save preferences.', saveSuccess: 'Preferences saved.', userMissing: 'User not found.',
  },
};

const NL: UiText = {
  topmenu: {quiz: 'Quizzen', domains: 'Domeinen', subjects: 'Onderwerpen', questions: 'Vragen', about: 'Over', alertsAria: 'Meldingen', currentDomain: 'Huidig domein', ownedDomains: 'Mijn domeinen', staffDomains: 'Domeinen waar ik staff ben', linkedDomains: 'Gekoppelde domeinen', noDomains: 'Geen domein', preferences: 'Voorkeuren'},
  userMenu: {preferences: 'Voorkeuren', changePassword: 'Wachtwoord wijzigen', logout: 'Afmelden', login: 'Aanmelden'},
  footer: {baseline: 'Platform voor quizzen en domeingebaseerd contentbeheer.', version: 'Versie'},
  home: {
    eyebrow: 'Quizzen, templates en correctie',
    lead: 'Een plek om quizzen te bouwen, toe te wijzen, af te leggen en op te volgen.',
    primaryLoggedIn: 'Mijn quizzen bekijken',
    primaryLoggedOut: 'Aanmelden',
    secondaryAdmin: 'Template maken',
    secondaryLoggedOut: 'Account maken',
    mode: 'Modus',
    modeStaff: 'Staff',
    modeUser: 'Aangemelde gebruiker',
    modeVisitor: 'Bezoeker',
    languages: 'Talen',
    features: 'Functies',
    featuresValue: 'Quizzen, meldingen, toewijzingen, correctie',
    highlights: [
      {title: 'Vlotte afname', description: 'Oefen- en examenflows met timer, hervatten en gelokaliseerde correctie.'},
      {title: 'Staff editing', description: 'Multimediavragen, onderwerpen, domeinen en templates in een werkruimte.'},
      {title: 'Live opvolging', description: 'Toewijzingen, resultaten, meldingen en correctieregels in hetzelfde product.'},
    ],
    capabilitiesTitle: 'Wat u kunt doen',
    capabilities: [
      'Vraagbanken per domein en onderwerp opbouwen en beheren.',
      'Oefen- of examenquizzen maken met zichtbaarheidsregels.',
      'Een quiz toewijzen aan gebruikers en hun resultaten volgen.',
      'Een sessie herbekijken met juiste antwoorden en uitleg.',
    ],
    quickLinksTitle: 'Snelle links',
    quickLinks: {catalog: 'Quizcatalogus', preferences: 'Voorkeuren', about: 'Over'},
  },
  login: {
    eyebrow: 'Aanmelden', title: 'Toegang tot uw ruimte', subtitle: 'Meld u aan om verder te gaan.',
    username: 'Gebruiker', usernamePlaceholder: 'Uw gebruikersnaam', usernameError: 'Gebruikersnaam is verplicht (min. 3 tekens)',
    password: 'Wachtwoord', passwordPlaceholder: 'Uw wachtwoord', passwordError: 'Wachtwoord is verplicht (min. 4 tekens)',
    remember: 'Onthoud mij', forgotPassword: 'Wachtwoord vergeten?', submit: 'Aanmelden', noAccount: 'Nog geen account?',
    createAccount: 'Account maken', invalidCredentials: 'Ongeldige gegevens. Probeer opnieuw.', confirmEmailRequired: 'Bevestig uw e-mailadres voordat u zich aanmeldt.',
  },
  register: {
    title: 'Account maken', subtitle: 'Identiteit, taal en beveiliging', back: 'Terug', create: 'Maken', loading: 'Laden...',
    identityTitle: 'Identiteit', identityBadge: 'profiel', securityTitle: 'Beveiliging', securityBadge: 'wachtwoord',
    username: 'Gebruikersnaam', email: 'E-mailadres', firstName: 'Voornaam', lastName: 'Achternaam', language: 'Taal',
    domains: 'Domeinen', chooseDomains: 'Kies een of meer domeinen', domainsHint: 'Selecteer de domeinen waaraan u gekoppeld wilt worden.',
    chooseLanguage: 'Kies een taal', password: 'Wachtwoord', confirmPassword: 'Bevestig wachtwoord', createAccount: 'Mijn account maken',
    cancel: 'Annuleren', usernameRequired: 'Gebruikersnaam is verplicht.', emailRequired: 'E-mailadres is verplicht.', emailInvalid: 'E-mailadres is ongeldig.',
    firstNameRequired: 'Voornaam is verplicht.', lastNameRequired: 'Achternaam is verplicht.', languageRequired: 'Taal is verplicht.',
    passwordRequired: 'Wachtwoord is verplicht.', passwordMin: 'Minimaal 8 tekens.', confirmRequired: 'Bevestiging is verplicht.',
    passwordMismatch: 'Wachtwoorden komen niet overeen.', success: 'Uw account is aangemaakt. Controleer uw mailbox om uw registratie te bevestigen.',
    loadLanguagesError: 'Kan talen niet laden.', loadDomainsError: 'Kan domeinen niet laden.', submitError: 'Registratie mislukt. Controleer de gegevens en probeer opnieuw.',
  },
  registerPending: {
    title: 'Account aangemaakt',
    subtitle: 'Bevestig uw e-mailadres',
    lead: 'Uw account is succesvol aangemaakt.',
    body: 'Controleer nu uw mailbox en klik op de bevestigingslink om uw registratie te activeren.',
    login: 'Naar aanmelden',
  },
  changePassword: {
    title: 'WpRef', subtitle: 'Mijn wachtwoord resetten', oldPassword: 'Huidig wachtwoord', newPassword: 'Nieuw wachtwoord',
    confirmNewPassword: 'Nieuw wachtwoord bevestigen', oldPasswordRequired: 'Huidig wachtwoord is verplicht.', newPasswordRequired: 'Nieuw wachtwoord is verplicht.',
    newPasswordMin: 'Het nieuwe wachtwoord moet minstens 8 tekens bevatten.', confirmRequired: 'Bevestiging is verplicht.', mismatch: 'Wachtwoorden komen niet overeen.',
    submit: 'Wachtwoord wijzigen', forceMessage: 'U moet eerst uw wachtwoord wijzigen.', success: 'Uw wachtwoord is gewijzigd.',
    error: 'Er is een fout opgetreden bij het wijzigen van het wachtwoord.',
  },
  preferences: {
    eyebrow: 'Mijn account', title: 'Voorkeuren', subtitle: 'Beheer uw profiel, interfacetaal en huidig domein.', profileTitle: 'Profiel',
    profileSubtitle: 'Persoonlijke gegevens en weergavevoorkeuren.', summaryTitle: 'Overzicht', summarySubtitle: 'Snelle weergave van uw huidige account.',
    loading: 'Laden...', username: 'Gebruikersnaam', email: 'E-mail', firstName: 'Voornaam', lastName: 'Achternaam', language: 'Taal',
    domains: 'Gekoppelde domeinen', chooseDomains: 'Kies gekoppelde domeinen', currentDomain: 'Huidig domein', chooseLanguage: 'Kies een taal', noDomain: 'Geen domein', save: 'Opslaan', changePassword: 'Wachtwoord wijzigen',
    role: 'Rol', user: 'Gebruiker', currentDomainLabel: 'Huidig domein', managedDomains: 'Beheerde domeinen', ownedDomains: 'Eigen domeinen',
    activeAccount: 'Actief account', yes: 'Ja', no: 'Nee', roleSuperuser: 'Superuser', roleStaff: 'Staff', roleUser: 'Gebruiker', roleOwner: 'Eigenaar', roleMember: 'Gekoppeld lid', domainsTitle: 'Domeinen', domainsSubtitle: 'Beheer uw gekoppelde domeinen en kies het huidige domein.', linkedDomainsList: 'Zichtbare domeinen', currentBadge: 'Huidig', setCurrent: 'Instellen als huidig', unlinkDomain: 'Ontkoppelen', addDomain: 'Domein koppelen', noMoreDomains: 'Geen extra domein beschikbaar.', linkSelectedDomains: 'Selectie koppelen', cancel: 'Annuleren', ownerLabel: 'Eigenaar:', deleteDomain: 'Verwijderen', deleteDomainSuccess: 'Domein verwijderd.', deleteDomainError: 'Kan dit domein niet verwijderen.',
    loadError: 'Kan uw voorkeuren niet laden.', saveError: 'Kan voorkeuren niet opslaan.', saveSuccess: 'Voorkeuren opgeslagen.', userMissing: 'Gebruiker niet gevonden.',
  },
};

const IT: UiText = {
  topmenu: {quiz: 'Quiz', domains: 'Domini', subjects: 'Argomenti', questions: 'Domande', about: 'Informazioni', alertsAria: 'Avvisi', currentDomain: 'Dominio corrente', ownedDomains: 'I miei domini', staffDomains: 'Domini dove sono staff', linkedDomains: 'Domini collegati', noDomains: 'Nessun dominio', preferences: 'Preferenze'},
  userMenu: {preferences: 'Preferenze', changePassword: 'Cambia password', logout: 'Disconnetti', login: 'Accedi'},
  footer: {baseline: 'Piattaforma per quiz e gestione contenuti per dominio.', version: 'Versione'},
  home: {
    eyebrow: 'Quiz, template e revisione',
    lead: 'Uno spazio unico per creare quiz, assegnarli, completarli e rivedere i risultati.',
    primaryLoggedIn: 'Vedi i miei quiz',
    primaryLoggedOut: 'Accedi',
    secondaryAdmin: 'Crea un template',
    secondaryLoggedOut: 'Crea un account',
    mode: 'Modalita',
    modeStaff: 'Staff',
    modeUser: 'Utente autenticato',
    modeVisitor: 'Visitatore',
    languages: 'Lingue',
    features: 'Funzionalita',
    featuresValue: 'Quiz, avvisi, assegnazioni, revisione',
    highlights: [
      {title: 'Esecuzione fluida', description: 'Quiz di pratica o esame con timer, ripresa e revisione localizzata.'},
      {title: 'Editing staff', description: 'Domande multimediali, argomenti, domini e template in un’unica interfaccia.'},
      {title: 'Monitoraggio live', description: 'Assegnazioni, risultati, avvisi e regole di revisione nello stesso prodotto.'},
    ],
    capabilitiesTitle: 'Cosa puoi fare',
    capabilities: [
      'Creare e organizzare banche di domande per dominio e argomento.',
      'Comporre quiz di pratica o esame con regole di visibilita.',
      'Assegnare un quiz agli utenti e seguirne i risultati.',
      'Rivedere una sessione con risposte corrette e spiegazioni.',
    ],
    quickLinksTitle: 'Accessi rapidi',
    quickLinks: {catalog: 'Catalogo quiz', preferences: 'Preferenze', about: 'Informazioni'},
  },
  login: {
    eyebrow: 'Accesso', title: 'Accedi al tuo spazio', subtitle: 'Autenticati per continuare.',
    username: 'Utente', usernamePlaceholder: 'Il tuo nome utente', usernameError: 'Nome utente obbligatorio (min. 3 caratteri)',
    password: 'Password', passwordPlaceholder: 'La tua password', passwordError: 'Password obbligatoria (min. 4 caratteri)',
    remember: 'Ricordami', forgotPassword: 'Password dimenticata?', submit: 'Accedi', noAccount: 'Nessun account?',
    createAccount: 'Crea account', invalidCredentials: 'Credenziali non valide. Riprova.', confirmEmailRequired: 'Conferma il tuo indirizzo email prima di accedere.',
  },
  register: {
    title: 'Crea un account', subtitle: 'Identita, lingua e sicurezza', back: 'Indietro', create: 'Crea', loading: 'Caricamento...',
    identityTitle: 'Identita', identityBadge: 'profilo', securityTitle: 'Sicurezza', securityBadge: 'password',
    username: 'Nome utente', email: 'Indirizzo email', firstName: 'Nome', lastName: 'Cognome', language: 'Lingua',
    domains: 'Domini', chooseDomains: 'Scegli uno o piu domini', domainsHint: 'Seleziona i domini a cui vuoi essere collegato.',
    chooseLanguage: 'Scegli una lingua', password: 'Password', confirmPassword: 'Conferma password', createAccount: 'Crea il mio account',
    cancel: 'Annulla', usernameRequired: 'Il nome utente e obbligatorio.', emailRequired: 'L’indirizzo email e obbligatorio.', emailInvalid: 'L’indirizzo email non e valido.',
    firstNameRequired: 'Il nome e obbligatorio.', lastNameRequired: 'Il cognome e obbligatorio.', languageRequired: 'La lingua e obbligatoria.',
    passwordRequired: 'La password e obbligatoria.', passwordMin: 'Minimo 8 caratteri.', confirmRequired: 'La conferma e obbligatoria.',
    passwordMismatch: 'Le password non corrispondono.', success: 'Il tuo account e stato creato. Controlla la casella email per confermare la registrazione.',
    loadLanguagesError: 'Impossibile caricare le lingue.', loadDomainsError: 'Impossibile caricare i domini.', submitError: 'Registrazione fallita. Controlla i dati e riprova.',
  },
  registerPending: {
    title: 'Account creato',
    subtitle: 'Conferma il tuo indirizzo email',
    lead: 'Il tuo account e stato creato correttamente.',
    body: 'Controlla ora la tua casella email e fai clic sul link di conferma per attivare la registrazione.',
    login: 'Vai al login',
  },
  changePassword: {
    title: 'WpRef', subtitle: 'Reimposta la mia password', oldPassword: 'Password attuale', newPassword: 'Nuova password',
    confirmNewPassword: 'Conferma nuova password', oldPasswordRequired: 'La password attuale e obbligatoria.', newPasswordRequired: 'La nuova password e obbligatoria.',
    newPasswordMin: 'La nuova password deve contenere almeno 8 caratteri.', confirmRequired: 'La conferma e obbligatoria.', mismatch: 'Le password non corrispondono.',
    submit: 'Cambia password', forceMessage: 'Devi cambiare la password prima di continuare.', success: 'La tua password e stata modificata.',
    error: 'Si e verificato un errore durante la modifica della password.',
  },
  preferences: {
    eyebrow: 'Il mio account', title: 'Preferenze', subtitle: 'Gestisci il tuo profilo, la lingua dell’interfaccia e il dominio corrente.',
    profileTitle: 'Profilo', profileSubtitle: 'Informazioni personali e preferenze di visualizzazione.', summaryTitle: 'Riepilogo',
    summarySubtitle: 'Vista rapida del tuo account corrente.', loading: 'Caricamento...', username: 'Nome utente', email: 'Email',
    firstName: 'Nome', lastName: 'Cognome', language: 'Lingua', domains: 'Domini collegati', chooseDomains: 'Scegli i domini collegati', currentDomain: 'Dominio corrente', chooseLanguage: 'Scegli una lingua',
    noDomain: 'Nessun dominio', save: 'Salva', changePassword: 'Cambia password', role: 'Ruolo', user: 'Utente', currentDomainLabel: 'Dominio attuale',
    managedDomains: 'Domini gestiti', ownedDomains: 'Domini posseduti', activeAccount: 'Account attivo', yes: 'Si', no: 'No',
    roleSuperuser: 'Superuser', roleStaff: 'Staff', roleUser: 'Utente', roleOwner: 'Proprietario', roleMember: 'Membro collegato', domainsTitle: 'Domini', domainsSubtitle: 'Gestisci i domini collegati e scegli quello corrente.', linkedDomainsList: 'Domini visibili', currentBadge: 'Corrente', setCurrent: 'Imposta corrente', unlinkDomain: 'Scollega', addDomain: 'Collega un dominio', noMoreDomains: 'Nessun altro dominio disponibile.', linkSelectedDomains: 'Collega selezione', cancel: 'Annulla', ownerLabel: 'Proprietario:', deleteDomain: 'Elimina', deleteDomainSuccess: 'Dominio eliminato.', deleteDomainError: 'Impossibile eliminare questo dominio.', loadError: 'Impossibile caricare le preferenze.',
    saveError: 'Impossibile salvare le preferenze.', saveSuccess: 'Preferenze salvate.', userMissing: 'Utente non trovato.',
  },
};

const ES: UiText = {
  topmenu: {quiz: 'Cuestionarios', domains: 'Dominios', subjects: 'Temas', questions: 'Preguntas', about: 'Acerca de', alertsAria: 'Alertas', currentDomain: 'Dominio actual', ownedDomains: 'Mis dominios', staffDomains: 'Dominios donde soy staff', linkedDomains: 'Dominios vinculados', noDomains: 'Ningun dominio', preferences: 'Preferencias'},
  userMenu: {preferences: 'Preferencias', changePassword: 'Cambiar contrasena', logout: 'Cerrar sesion', login: 'Iniciar sesion'},
  footer: {baseline: 'Plataforma de cuestionarios y gestion de contenido por dominio.', version: 'Version'},
  home: {
    eyebrow: 'Cuestionarios, plantillas y revision',
    lead: 'Un unico espacio para crear cuestionarios, asignarlos, completarlos y revisar los resultados.',
    primaryLoggedIn: 'Ver mis cuestionarios',
    primaryLoggedOut: 'Iniciar sesion',
    secondaryAdmin: 'Crear una plantilla',
    secondaryLoggedOut: 'Crear una cuenta',
    mode: 'Modo',
    modeStaff: 'Staff',
    modeUser: 'Usuario autenticado',
    modeVisitor: 'Visitante',
    languages: 'Idiomas',
    features: 'Funciones',
    featuresValue: 'Cuestionarios, alertas, asignaciones, revision',
    highlights: [
      {title: 'Uso fluido', description: 'Cuestionarios de practica o examen con temporizador, reanudacion y revision localizada.'},
      {title: 'Edicion staff', description: 'Preguntas multimedia, temas, dominios y plantillas en una sola interfaz.'},
      {title: 'Seguimiento en vivo', description: 'Asignaciones, resultados, alertas y reglas de revision en el mismo producto.'},
    ],
    capabilitiesTitle: 'Lo que puedes hacer',
    capabilities: [
      'Crear y organizar bancos de preguntas por dominio y tema.',
      'Componer cuestionarios de practica o examen con reglas de visibilidad.',
      'Asignar un cuestionario a usuarios y seguir sus resultados.',
      'Revisar una sesion con respuestas correctas y explicaciones.',
    ],
    quickLinksTitle: 'Accesos rapidos',
    quickLinks: {catalog: 'Catalogo de cuestionarios', preferences: 'Preferencias', about: 'Acerca de'},
  },
  login: {
    eyebrow: 'Acceso', title: 'Accede a tu espacio', subtitle: 'Inicia sesion para continuar.',
    username: 'Usuario', usernamePlaceholder: 'Tu nombre de usuario', usernameError: 'El nombre de usuario es obligatorio (min. 3 caracteres)',
    password: 'Contrasena', passwordPlaceholder: 'Tu contrasena', passwordError: 'La contrasena es obligatoria (min. 4 caracteres)',
    remember: 'Recordarme', forgotPassword: 'Has olvidado tu contrasena?', submit: 'Iniciar sesion', noAccount: 'Aun no tienes cuenta?',
    createAccount: 'Crear cuenta', invalidCredentials: 'Credenciales invalidas. Intentalo de nuevo.', confirmEmailRequired: 'Confirma tu direccion de correo antes de iniciar sesion.',
  },
  register: {
    title: 'Crear una cuenta', subtitle: 'Identidad, idioma y seguridad', back: 'Volver', create: 'Crear', loading: 'Cargando...',
    identityTitle: 'Identidad', identityBadge: 'perfil', securityTitle: 'Seguridad', securityBadge: 'contrasena',
    username: 'Nombre de usuario', email: 'Correo electronico', firstName: 'Nombre', lastName: 'Apellido', language: 'Idioma',
    domains: 'Dominios', chooseDomains: 'Elegir uno o varios dominios', domainsHint: 'Selecciona los dominios a los que quieres estar vinculado.',
    chooseLanguage: 'Elegir un idioma', password: 'Contrasena', confirmPassword: 'Confirmar contrasena', createAccount: 'Crear mi cuenta',
    cancel: 'Cancelar', usernameRequired: 'El nombre de usuario es obligatorio.', emailRequired: 'El correo electronico es obligatorio.', emailInvalid: 'El correo electronico no es valido.',
    firstNameRequired: 'El nombre es obligatorio.', lastNameRequired: 'El apellido es obligatorio.', languageRequired: 'El idioma es obligatorio.',
    passwordRequired: 'La contrasena es obligatoria.', passwordMin: 'Minimo 8 caracteres.', confirmRequired: 'La confirmacion es obligatoria.',
    passwordMismatch: 'Las contrasenas no coinciden.', success: 'Tu cuenta ha sido creada. Revisa tu correo para confirmar el registro.',
    loadLanguagesError: 'No se pueden cargar los idiomas.', loadDomainsError: 'No se pueden cargar los dominios.', submitError: 'El registro ha fallado. Revisa los datos e intentalo de nuevo.',
  },
  registerPending: {
    title: 'Cuenta creada',
    subtitle: 'Confirma tu direccion de correo',
    lead: 'Tu cuenta se ha creado correctamente.',
    body: 'Revisa ahora tu correo electronico y haz clic en el enlace de confirmacion para activar tu registro.',
    login: 'Ir al inicio de sesion',
  },
  changePassword: {
    title: 'WpRef', subtitle: 'Restablecer mi contrasena', oldPassword: 'Contrasena actual', newPassword: 'Nueva contrasena',
    confirmNewPassword: 'Confirmar nueva contrasena', oldPasswordRequired: 'La contrasena actual es obligatoria.', newPasswordRequired: 'La nueva contrasena es obligatoria.',
    newPasswordMin: 'La nueva contrasena debe tener al menos 8 caracteres.', confirmRequired: 'La confirmacion es obligatoria.', mismatch: 'Las contrasenas no coinciden.',
    submit: 'Cambiar contrasena', forceMessage: 'Debes cambiar tu contrasena antes de continuar.', success: 'Tu contrasena ha sido modificada.',
    error: 'Se produjo un error al cambiar la contrasena.',
  },
  preferences: {
    eyebrow: 'Mi cuenta', title: 'Preferencias', subtitle: 'Gestiona tu perfil, el idioma de la interfaz y el dominio actual.',
    profileTitle: 'Perfil', profileSubtitle: 'Informacion personal y preferencias de visualizacion.', summaryTitle: 'Resumen',
    summarySubtitle: 'Vista rapida de tu cuenta actual.', loading: 'Cargando...', username: 'Nombre de usuario', email: 'Correo electronico',
    firstName: 'Nombre', lastName: 'Apellido', language: 'Idioma', domains: 'Dominios vinculados', chooseDomains: 'Elegir dominios vinculados', currentDomain: 'Dominio actual', chooseLanguage: 'Elegir un idioma',
    noDomain: 'Ningun dominio', save: 'Guardar', changePassword: 'Cambiar contrasena', role: 'Rol', user: 'Usuario', currentDomainLabel: 'Dominio actual',
    managedDomains: 'Dominios gestionados', ownedDomains: 'Dominios propios', activeAccount: 'Cuenta activa', yes: 'Si', no: 'No',
    roleSuperuser: 'Superuser', roleStaff: 'Staff', roleUser: 'Usuario', roleOwner: 'Propietario', roleMember: 'Miembro vinculado', domainsTitle: 'Dominios', domainsSubtitle: 'Gestiona tus dominios vinculados y elige el dominio actual.', linkedDomainsList: 'Dominios visibles', currentBadge: 'Actual', setCurrent: 'Definir actual', unlinkDomain: 'Desvincular', addDomain: 'Vincular un dominio', noMoreDomains: 'No hay más dominios disponibles.', linkSelectedDomains: 'Vincular selección', cancel: 'Cancelar', ownerLabel: 'Propietario:', deleteDomain: 'Eliminar', deleteDomainSuccess: 'Dominio eliminado.', deleteDomainError: 'No se puede eliminar este dominio.', loadError: 'No se pueden cargar tus preferencias.',
    saveError: 'No se pueden guardar las preferencias.', saveSuccess: 'Preferencias guardadas.', userMissing: 'Usuario no encontrado.',
  },
};

const UI_TEXT: Partial<Record<LanguageEnumDto, UiText>> = {
  [LanguageEnumDto.Fr]: FR,
  [LanguageEnumDto.En]: EN,
  [LanguageEnumDto.Nl]: NL,
  [LanguageEnumDto.It]: IT,
  [LanguageEnumDto.Es]: ES,
};

export function getUiText(lang: LanguageEnumDto | string | null | undefined): UiText {
  return UI_TEXT[(lang as LanguageEnumDto)] ?? EN;
}
