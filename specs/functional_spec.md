# Spécifications Fonctionnelles - Automatisation Javadoc

## 1. Objectif du Projet

Créer un script Python automatisé qui génère et met à jour la documentation Javadoc d'un dépôt Java en utilisant une intelligence artificielle (LLM). Le script s'exécute nightly, détecte les changements, met à jour la documentation et notifie les équipes.

## 2. Fonctionnalités Principales

### 2.1 Synchronisation Quotidienne

- Le script doit faire un `pull` de la branche `PROD` chaque nuit.
- La fréquence d'exécution est quotidienne (horaire à définir, ex: 02:00 AM).

### 2.2 Détection des Modifications

- Comparaison entre la version actuelle de `PROD` et celle de la veille (ou dernier commit traité).
- Identification précise des classes et méthodes modifiées.

### 2.3 Option d'Initialisation (First Run)

- Une option (flag ou configuration) permet de lancer une génération complète.
- Dans ce mode, toutes les classes et méthodes du projet sont documentées.
- **Exclusion** : Le répertoire `test` (et ses sous-répertoires) est exclu de la documentation.

### 2.4 Génération de Javadoc via IA

- Utilisation d'un Agent IA (PydanticAI ou LangChain) pour analyser le code et générer la Javadoc.
- Le format doit être conforme aux standards Javadoc (paramètres, retours, exceptions, description).

### 2.5 Gestion de Version et Publication

- Les modifications ne sont pas poussées directement sur `PROD`.
- Création d'une nouvelle branche : `PROD_documented_[current_date]` (ex: `PROD_documented_2025-12-22`).
- Push de cette branche sur le dépôt distant.

### 2.6 Notifications

#### 2.6.1 Email

- Envoi d'un rapport par email après chaque exécution.
- Contenu : Liste des classes et méthodes documentées.
- Configuration : Host, User, Password, TLS, Sujet, Activation (Enable/Disable).

#### 2.6.2 Microsoft Teams

- Envoi d'une notification sur un channel Teams.
- Contenu : Résumé de l'exécution et lien vers la branche (si possible).
- Configuration : Webhook URL, Token (si nécessaire), Activation.

## 3. Configuration

Toutes les options doivent être centralisées dans un fichier `config.yaml`.

### Structure attendue du fichier de configuration

- **GitLab** : URL dépôt, Token, Branche cible.
- **Email** : SMTP host, credentials, destinataires, feature toggle.
- **Teams** : Webhook, feature toggle.
- **LLM** : Clé API, Modèle (ex: GPT-4, Claude 3.5).
