# NAIAD – Underwater Drone Trajectory Visualization
L’objectif de plugin : visualiser les trajectoire des drones sous-marins

Ce projet comprend :
- **NAIAD**: Un plugin QGIS pour visualiser les données GPS des drones sous-marins.
- **Pygame Animation**: Un script séparé pour simuler les mouvements des drones avec pygame.
- un fichier .csv pour tester le plugin 

## Mode d’emploi

### 1. QGIS Plugin (NAIAD)
- Copiez le dossier `NAIAD/` dans votre répertoire d’extensions QGIS.
- Ouvrez QGIS → Extensions → Gérer et installer → Activer NAIAD
        (QGIS → Plugins → Manage and Install → Enable NAIAD)
- Chargez un fichier CSV avec les colonnes : 'drone_id', 'longitude', 'latitude', 'depth', 'timestamp'

### 2. Pygame Visualization
```bash
pip install pygame pandas
python visualization/drone_animation.py


## Membres de l'équipe
- YIN Ruohan
- ROUABAH Mohamed Ali Chemseddine
- DIENG Ibrahima
- FIRSOVA Oksana
- NOTTEZ Axel


## Format des données attendu
Le plugin nécessite un fichier .csv contenant les données de trajectoire spatio-temporelles d'un ou plusieurs drones sous-marins autonomes.
Chaque ligne du fichier représente la position horodatée d'un drone spécifique.
Les colonnes sont les suivantes:
- **drone_id** - Identifiant unique du drone (par exemple, AUV1, AUV2, ...).
- **longitude** - Longitude en degrés décimaux (EPSG : 4326). L'ouest est négatif.
- **latitude** - Latitude en degrés décimaux (EPSG : 4326). Le nord est positif.
- **depth** (optionnel) - Profondeur en m (les valeurs négatives indiquent généralement une profondeur sous la surface).
- **timestamp** - Date et heure ISO 8601 (par exemple, 2024-03-13T14:00:00Z). Doit être en UTC. (ex. 2024-03-13T16:15:00Z)
