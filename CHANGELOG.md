# Journal des versions

Chaque version publiée a sa section `## X.Y.Z` : c'est elle qui sert de notes à la release GitHub.

## 1.0.1

Compatibilité avec Home Assistant 2026.11 et son **Marketplace** (HACS intégré à Home Assistant). Rien ne change dans les entités ni dans la carte.

- Testée sur Home Assistant 2026.10.1 et 2026.11.0, y compris la migration de HACS vers le Marketplace : l'intégration reste installée et configurée, avec ses mises à jour.
- Home Assistant 2026.11 : installation par le Marketplace, **sans redémarrage** (la configuration s'ouvre aussitôt). Home Assistant 2026.10 : toujours par HACS.
- README : deux procédures (Marketplace, HACS), bouton « Open your Home Assistant » vers le Marketplace (il ouvre HACS sur 2026.10), chemins des menus mis à jour (Paramètres → Outils, Paramètres → Appareils et services → Entités). Les étapes d'installation n'apparaissent plus sur la page du Marketplace, qui a son propre bouton.
- Réparation « Ancienne carte MétéoKouran encore chargée » : elle invite à désinstaller l'ancienne carte du Marketplace (HACS avant 2026.11).

### Carte 1.3.0 (inchangée)
- Même carte que dans la 1.0.0, vérifiée sur Home Assistant 2026.11 : chargée sans ressource à déclarer, éditeur visuel complet.

## 1.0.0

Première version : l'intégration remplace le paquet YAML et la carte seule (`meteokouran-card`), en un seul téléchargement HACS.

- Ajout depuis Paramètres → Appareils et services, avec une page de configuration : adresse de l'instance préremplie (`https://meteokouran.re`), vérifiée en lisant l'API, messages distincts « injoignable », « délai dépassé », « ce n'est pas une instance MétéoKouran ». L'adresse se change ensuite par « Reconfigurer », sans supprimer l'intégration ; l'API est relue aussitôt.
- Neuf entités, rattachées à l'appareil « MétéoKouran », avec **les mêmes identifiants, états, icônes et attributs que le paquet YAML** : vos automatisations restent valables (voir « Vous utilisiez le paquet YAML ou la carte seule ? » dans le README). Indisponibles, jamais « off », quand l'API ne sait pas répondre.
- Mêmes rythmes que le paquet : `/now` et `/cyclone` toutes les 15 minutes, `/forecast` toutes les 30 minutes, une seule requête par ressource.
- Plus d'`input_text.meteokouran_url` ni d'automatisation `meteokouran_refresh` : l'adresse vit dans l'intégration.

### Carte 1.3.0 (fournie avec l'intégration)
- Chargée par l'intégration : plus de ressource de tableau de bord à déclarer, en mode normal comme en mode YAML.
- Sans `url` ni `url_entity`, la carte prend l'adresse configurée dans l'intégration, et suit son changement. `url` et `url_entity` restent acceptés.
- Éditeur visuel : toutes les options se règlent dans « Ajouter une carte », sans YAML.
- Message « Adresse de MétéoKouran inconnue » : invite à ajouter l'intégration.
- Une ressource restée de l'ancienne carte seule est signalée dans Paramètres → Réparations.
