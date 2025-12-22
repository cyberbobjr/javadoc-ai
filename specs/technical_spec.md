# Spécifications Techniques - Automatisation Javadoc

## 1. Architecture du Système

Le projet sera structuré comme un script Python modulaire.

### 1.1 Stack Technologique

- **Langage** : Python 3.9+
- **Gestionnaire de versions de code** : `GitPython`
- **Agent IA** : `PydanticAI` (framework robuste et typé pour les agents)
- **Configuration** : `PyYAML`
- **Appels HTTP (Teams)** : `requests` ou `httpx`
- **Email** : `smtplib` (standard library)

### 1.2 Structure du Projet

```
javadoc_ai/
├── config.yaml           # Fichier de configuration
├── main.py               # Point d'entrée
├── core/
│   ├── git_manager.py    # Gestion des opérations Git
│   ├── doc_generator.py  # Logique de l'agent IA (PydanticAI)
│   ├── file_parser.py    # Analyse des fichiers Java (optionnel, ou via IA)
│   └── notifier.py       # Gestion Email et Teams
├── utils/
│   └── config_loader.py  # Chargement de la conf
└── requirements.txt
```

## 2. Flux de Données (Data Flow)

1. **Initialisation** : Chargement de `config.yaml`.
2. **Git Pull** : `GitManager` récupère la branche `PROD`.
3. **Analyse Diff** :
   - Si `FIRST_RUN` : Liste récursive de tous les fichiers `.java` (sauf `src/test/`).
   - Sinon : `git diff --name-only HEAD@{1} HEAD` (ou logique similaire pour comparer avec la veille daily).
4. **Traitement (Boucle)** :
   - Pour chaque fichier identifié :
     - Lecture du contenu.
     - Envoi à l'Agent IA (`DocGenerator`).
     - L'Agent retourne le code avec la Javadoc ajoutée/mise à jour.
     - Réécriture du fichier.
5. **Publication** :
   - Création branche `PROD_documented_YYYY-MM-DD`.
   - `git add .`, `git commit`, `git push`.
6. **Notification** :
   - Compilation des statistiques (fichiers modifiés).
   - Envoi Email et Teams via `Notifier`.

## 3. Détails de l'Implémentation

### 3.1 Agent IA (PydanticAI)

Utilisation de `pydantic_ai.Agent` pour garantir des réponses structurées si nécessaire, ou simplement pour orchestrer le contexte.

- **Modèle** : Configurable (OpenAI GPT-4o, Claude 3.5 Sonnet recommandé pour le code).
- **Prompt** : Le prompt devra instruire l'IA de :
  - Ne pas modifier la logique du code.
  - Ajouter uniquement la Javadoc manquante ou mettre à jour l'existante.
  - Respecter le style Javadoc standard.
  - Ignorer les getters/setters si trivial (optionnel).

### 3.2 Gestion Git

Utilisation de `gitpython` pour manipuler le repo.

- Gestion des conflits : Puisqu'on crée une nouvelle branche à partir de PROD, les conflits devraient être minimes (on écrase la version documentée).

### 3.3 Configuration (config.yaml)

```yaml
git:
  repo_url: "https://gitlab.com/user/repo.git"
  token: "ENV_VAR_OR_Secret"
  base_branch: "PROD"

llm:
  provider: "openai"
  model: "gpt-4o"
  api_key: "ENV_VAR"

notifications:
  email:
    enabled: true
    smtp_host: "smtp.office365.com"
    username: "bot@company.com"
    password: "ENV_VAR"
    to: ["dev-team@company.com"]
  teams:
    enabled: true
    webhook_url: "https://outlook.office.com/webhook/..."
```

NB : Les secrets (mots de passe, tokens) devraient idéalement être passés par variables d'environnement et injectés dans la config au runtime.

## 4. Gestion des Erreurs

- Si l'IA échoue sur un fichier : logger l'erreur et passer au suivant (ne pas bloquer tout le pipeline).
- Si Git échoue : Arrêt critique et notification d'erreur.
- Logs : Utilisation du module `logging` pour tracer l'exécution.
