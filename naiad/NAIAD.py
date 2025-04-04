# -*- coding: utf-8 -*- 
""" 
Module principal du plugin NAIAD
"""

from qgis.core import (
    QgsVectorLayer, QgsProject, QgsField, QgsFields, QgsFeature,
    QgsGeometry, QgsPointXY, QgsPoint, QgsRendererCategory, QgsCategorizedSymbolRenderer,
    QgsMarkerSymbol, QgsLineSymbol, Qgis
)
from qgis.PyQt.QtCore import Qt, QTimer, QVariant
from qgis.PyQt.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QSlider, QAction
from qgis.PyQt.QtGui import QIcon
from datetime import datetime, timedelta
import pandas as pd
from math import hypot
import os
from .NAIAD_dialog import NAIADDialog


class CustomAnimationDialog(QDialog):
    def __init__(self, df, iface, parent=None):
        super().__init__(parent)
        self.setWindowTitle("NAIAD - Animation")
        self.iface = iface
        self.df = df
        self.setMinimumWidth(400)

        # Configuration du timer pour l'animation (toutes les 100 ms)
        self.timer = QTimer(self)
        self.timer.setInterval(100)
        self.timer.timeout.connect(self.update_frame)

        self.speed = 1.0
        self.paused = True
        self.frame = 0

        # Construction des trajectoires interpolées pour chaque drone
        self.track_paths = self.build_paths(df)
        self.total_frames = max(len(p) for p in self.track_paths.values())
        self.layer = self.create_layer()

        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        # Affichage de la frame courante et de l'heure
        self.label_info = QLabel("Frame : 0 | Heure : -")
        layout.addWidget(self.label_info)

        button_layout = QHBoxLayout()

        self.btn_play = QPushButton("▶ Play")
        self.btn_play.clicked.connect(self.toggle_play)
        button_layout.addWidget(self.btn_play)

        self.btn_reset = QPushButton("⟲ Replay")
        self.btn_reset.clicked.connect(self.reset_animation)
        button_layout.addWidget(self.btn_reset)

        layout.addLayout(button_layout)

        speed_layout = QHBoxLayout()
        self.slider_speed = QSlider(Qt.Horizontal)
        self.slider_speed.setMinimum(1)
        self.slider_speed.setMaximum(20)
        self.slider_speed.setValue(10)
        self.slider_speed.valueChanged.connect(self.update_speed)
        speed_layout.addWidget(QLabel("Vitesse :"))
        speed_layout.addWidget(self.slider_speed)
        layout.addLayout(speed_layout)

    def update_speed(self, value):
        self.speed = value / 10.0

    def toggle_play(self):
        self.paused = not self.paused
        if not self.paused:
            self.timer.start()
            self.btn_play.setText("⏸ Pause")
        else:
            self.timer.stop()
            self.btn_play.setText("▶ Play")

    def reset_animation(self):
        # Lors du Replay, on efface le contenu de la couche pour recommencer
        self.layer.dataProvider().truncate()
        self.frame = 0
        self.timer.start()
        self.paused = False
        self.btn_play.setText("⏸ Pause")

    def build_paths(self, df):
        paths = {}
        # Regroupement par drone_id pour construire les trajectoires
        for track_id, group in df.groupby('drone_id'):
            path = []
            group = group.sort_values('timestamp')
            if len(group) >= 2:
                for i in range(len(group) - 1):
                    r1, r2 = group.iloc[i], group.iloc[i + 1]
                    steps = self.calculate_steps(r1, r2)
                    for s in range(steps):
                        f = s / steps
                        lon = r1['longitude'] + f * (r2['longitude'] - r1['longitude'])
                        lat = r1['latitude'] + f * (r2['latitude'] - r1['latitude'])
                        ts = r1['timestamp'] + (r2['timestamp'] - r1['timestamp']) * f
                        path.append((lon, lat, ts))
            else:
                # Cas d'un seul point
                r = group.iloc[0]
                path.append((r['longitude'], r['latitude'], r['timestamp']))
            paths[track_id] = path
        return paths

    def calculate_steps(self, row1, row2):
        dx = row2['longitude'] - row1['longitude']
        dy = row2['latitude'] - row1['latitude']
        dist = hypot(dx, dy)
        return max(5, min(50, int(dist * 100)))

    def create_layer(self):
        fields = QgsFields()
        fields.append(QgsField("drone_id", QVariant.String))
        fields.append(QgsField("timestamp", QVariant.String))
        # Création d'une couche en mémoire de type LineString pour afficher l'animation
        layer = QgsVectorLayer("LineString?crs=EPSG:4326", "Lignes d'animation", "memory")
        pr = layer.dataProvider()
        pr.addAttributes(fields)
        layer.updateFields()

        # Attribution d'une couleur différente pour chaque drone
        categories = []
        palette = ["red", "blue", "green", "orange", "purple", "cyan", "magenta"]
        for i, drone_id in enumerate(self.track_paths.keys()):
            symbol = QgsLineSymbol.createSimple({"color": palette[i % len(palette)], "width": "1"})
            category = QgsRendererCategory(str(drone_id), symbol, str(drone_id))
            categories.append(category)
        renderer = QgsCategorizedSymbolRenderer("drone_id", categories)
        layer.setRenderer(renderer)

        QgsProject.instance().addMapLayer(layer)
        return layer

    def update_frame(self):
        # Pendant le mode Play, on conserve les trajectoires précédentes (aucun effacement)
        features = []

        # Pour chaque drone, on construit la trajectoire de l'origine jusqu'à la frame actuelle
        for track_id, path in self.track_paths.items():
            if self.frame < len(path):
                points = [QgsPointXY(pt[0], pt[1]) for pt in path[:self.frame+1]]
                if len(points) < 2:
                    continue  # Moins de deux points : pas de ligne
                feat = QgsFeature()
                feat.setGeometry(QgsGeometry.fromPolylineXY(points))
                feat.setAttributes([track_id, path[self.frame][2].isoformat()])
                features.append(feat)

        self.layer.dataProvider().addFeatures(features)
        self.layer.updateExtents()

        # Mise à jour de l'affichage de l'heure
        if features:
            current_time = features[0].attributes()[1]
        else:
            current_time = "-"
        self.label_info.setText(f"Frame : {self.frame}/{self.total_frames} | Heure : {current_time}")

        # Forcer le rafraîchissement de la couche sans modifier la vue (pas de changement de l'étendue)
        self.layer.triggerRepaint()

        self.frame += int(self.speed)
        if self.frame >= self.total_frames:
            self.frame = self.total_frames - 1
            self.timer.stop()
            self.btn_play.setText("▶ Play")
            self.paused = True


class NAIAD:
    def __init__(self, iface):
        self.iface = iface
        self.dialog = NAIADDialog()
        self.csv_path = None

        self.dialog.bouton_generer.clicked.connect(self.generer_trajectoires)
        self.dialog.bouton_animation.clicked.connect(self.lancer_animation)

    def initGui(self):
        self.action = QAction(QIcon(":/plugins/naiad/icon.png"), "NAIAD", self.iface.mainWindow())
        self.action.triggered.connect(self.run)
        self.iface.addToolBarIcon(self.action)
        self.iface.addPluginToMenu("&NAIAD", self.action)

    def unload(self):
        self.iface.removePluginMenu("&NAIAD", self.action)
        self.iface.removeToolBarIcon(self.action)

    def run(self):
        self.dialog.exec_()

    def generer_trajectoires(self):
        try:
            self.csv_path = self.dialog.get_chemin_csv()
            uri = f"file:///{self.csv_path}?type=csv&delimiter=,&xField=longitude&yField=latitude&zField=depth&crs=EPSG:4326"
            couche_points = QgsVectorLayer(uri, "Points Drone", "delimitedtext")

            if not couche_points.isValid():
                raise ValueError("Fichier CSV invalide")

            QgsProject.instance().addMapLayer(couche_points)
            couche_lignes = self.creer_lignes(couche_points)
            QgsProject.instance().addMapLayer(couche_lignes)
            self.configurer_styles(couche_points, couche_lignes)

            self.iface.messageBar().pushMessage("Succès", "Trajectoires générées", level=Qgis.Success)

        except Exception as e:
            self.iface.messageBar().pushMessage("Erreur", f"Erreur : {str(e)}", level=Qgis.Critical)

    def lancer_animation(self):
        try:
            if not self.csv_path:
                raise ValueError("Aucun fichier CSV chargé")

            df = pd.read_csv(self.csv_path)
            df = df.dropna(subset=['longitude', 'latitude', 'timestamp'])
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            if 'drone_id' not in df.columns:
                df['drone_id'] = 0

            self.dialog_animation = CustomAnimationDialog(df, self.iface)
            self.dialog_animation.show()

        except Exception as e:
            self.iface.messageBar().pushMessage("Erreur", f"Erreur : {str(e)}", level=Qgis.Critical)

    def creer_lignes(self, couche_points):
        couche = QgsVectorLayer("LineStringZ?crs=EPSG:4326", "Trajectoires", "memory")
        provider = couche.dataProvider()
        provider.addAttributes([
            QgsField("drone_id", QVariant.String),
            QgsField("start", QVariant.DateTime),
            QgsField("end", QVariant.DateTime)
        ])
        couche.updateFields()

        features = []
        drones = set(f['drone_id'] for f in couche_points.getFeatures())
        for drone_id in drones:
            points = sorted(
                [f for f in couche_points.getFeatures() if f['drone_id'] == drone_id],
                key=lambda x: x['timestamp']
            )
            if len(points) < 2:
                continue

            line = QgsFeature()
            line.setGeometry(QgsGeometry.fromPolyline([
                QgsPoint(
                    p.geometry().asPoint().x(),
                    p.geometry().asPoint().y(),
                    p['depth']
                ) for p in points
            ]))
            line.setAttributes([drone_id, points[0]['timestamp'], points[-1]['timestamp']])
            features.append(line)

        provider.addFeatures(features)
        couche.updateExtents()
        return couche

    def configurer_styles(self, points, lines):
        point_symbol = QgsMarkerSymbol.createSimple({
            'name': 'circle', 'color': '30,144,255', 'size': '3'
        })
        points.renderer().setSymbol(point_symbol)

        line_symbol = QgsLineSymbol.createSimple({
            'color': '255,50,100', 'width': '0.8'
        })
        lines.renderer().setSymbol(line_symbol)

        points.triggerRepaint()
        lines.triggerRepaint()
