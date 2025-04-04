# NAIAD – Underwater Drone Trajectory Visualization
L’objectif de plugin : visualiser les trajectoire des drones sous-marins

Ce projet comprend :
- **NAIAD**: Un plugin QGIS pour visualiser les données GPS des drones sous-marins.
- **PYGAME_animation.py**: Un script séparé pour simuler les mouvements des drones avec pygame.
- **testfile.csv**: un fichier .csv pour tester le plugin NAIAD et PYGAME
- **QGIS_fond-carte_2025-04-02_Sentinel-2_L2A.tiff**: un geotiff fond-de-carte, à charger dans QGIS avant le lancement de plugin NAIAD
- ocean-waves.gif: fichier-fond pour PYGAME


## Mode d’emploi

### 1. QGIS Plugin (NAIAD)
- Copiez le dossier `NAIAD/` dans votre répertoire d’extensions QGIS.
- Ouvrez QGIS → Extensions → Gérer et installer → Activer NAIAD
        (QGIS → Plugins → Manage and Install → Enable NAIAD
- **Remarque : veuillez charger le fichier GeoTIFF "QGIS_fond-carte" avant de lancer le plugin, afin d'assurer un centrage optimal de la carte.**
- Chargez un fichier CSV avec les colonnes : 'drone_id', 'longitude', 'latitude', 'depth', 'timestamp'
Pour plus d'explication, voir :
- [Pas à pas rapide avec images] (doc_NAIAD_v.rapide.pdf)
- [Documentation de plugin complete] (doc_NAIAD_v.complete.pdf)


### 2. Pygame Visualization
Ouvrir le code de Pygame (PYGAME_animation.py) en VSCode  → Ouvrir le terminal  → Charger les packages necessaires (voir en bas)  → Lancer le code en VSCode
```bash
pip install pygame pandas pyproj Pillow
python visualization/drone_animation.py
```
Quand vous lancer le Pygame,
- Ouvrez le fichier .csv
- Suivez les instructions dans le pop-up
- Ouvrez le .tif
- Si l'animation est trop vite, ajustez la vitesse
- [Documentation de PYGAME avec images] (doc_NAIAD_PYGAME_TUTORIAL.pdf)


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
  
