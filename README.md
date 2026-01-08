# Javadoc Automation AI

## Description

Ce projet automatise la génération de la documentation Javadoc pour un dépôt Java en utilisant l'intelligence artificielle. Il détecte les changements quotidiens dans le code source et utilise un agent LLM (Gemin/OpenAI via PydanticAI) pour documenter les classes et méthodes modifiées sans altérer la logique du code.

## Objectif

Maintenir une documentation technique à jour en continu en réduisant la charge de travail des développeurs. Le système fonctionne comme une tâche planifiée (cron job) qui :

1. Récupère les modifications du jour.
2. Génère la Javadoc manquante.
3. Pousse les changements sur une nouvelle branche Git.
4. Notifie l'équipe via Email et Microsoft Teams.

## Prérequis

- Python 3.10+
- Git installé et configuré
- Une clé API pour le LLM (Google Gemini ou autre compatible PydanticAI)
- Accès au dépôt Git cible

## Installation

1. Clonez ce dépôt.
2. Créez un environnement virtuel et installez les dépendances :

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Configuration

Le fichier `config.yaml` sert de modèle. Vous pouvez configurer les accès via ce fichier ou des variables d'environnement.

### Variables d'Environnement

- `GIT_TOKEN` : Token d'accès pour le dépôt Git.
- `OPENAI_API_KEY` : Clé API pour le modèle LLM.

### Logging

La verbosité des logs peut être contrôlée via l'argument `--verbose` ou le fichier de configuration.
L'ordre de priorité est : Argument CLI > Fichier Config > Défaut (INFO).

### Fichier `config.yaml`

Modifiez les sections suivantes :

```yaml
git:
  repo_url: "url_de_votre_repo"
  base_branch: "PROD"

llm:
  model_name: "gemini-1.5-pro"
  # api_key: peut être omis si défini dans l'env
  # base_url: "http://localhost:11434/v1" # Optionnel : Pour utiliser un LLM local ou interne compatible OpenAI

email:
  enabled: true
  host: "smtp.exemple.com"
  recipients: ["equipe@exemple.com"]

teams:
  enabled: true
  webhook_url: "votre_url_webhook"
### GitLab
Pour utiliser GitLab :
1. Définissez `git.provider` sur "gitlab".
2. Ajoutez `git.project_id` (obligatoire pour GitLab).

```yaml
git:
  provider: "gitlab"
  project_id: "group/project"  # Peut être un ID numérique (12345) ou un chemin encodé
```

### Exclusions

Vous pouvez exclure des fichiers via `config.yaml` :

```yaml
git:
  exclude:
    - "src/test/**"      # Exclut récursivement le dossier test
    - "**/*Info.java"    # Exclut par suffixe
```

## Utilisation

Le script `main.py` est le point d'entrée principal.

### Options de Base

```bash
# Exécution standard (diff journalier)
python main.py

# Première exécution (tous les fichiers)
python main.py --first-run

# Mode simulation (sans push)
python main.py --dry-run

# Utiliser un fichier de configuration spécifique
python main.py --config custom_config.yaml
```

### Mode Reprise (Resume)

En cas d'interruption (ex: panne réseau), vous pouvez reprendre le traitement sans tout recommencer grâce au répertoire de travail persistant.

```bash
# 1. Utiliser un répertoire de travail persistant
python main.py --work-dir ./my_cache

# 2. En cas d'erreur, reprendre :
python main.py --work-dir ./my_cache --resume
```

## Tests

Des tests unitaires sont disponibles pour valider la configuration et les composants internes.

```bash
# Lancer les tests
PYTHONPATH=. pytest tests/test_components.py
```
