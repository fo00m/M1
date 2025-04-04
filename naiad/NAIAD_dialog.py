# -*- coding: utf-8 -*-
"""
NAIADDialog - QGIS Plugin
Suivi et visualisation de sous-marins à partir d'un fichier CSV
Auteur : YIN Ruohan (2025)
"""

import os
import csv
from qgis.PyQt import uic, QtWidgets, QtCore
from qgis.PyQt.QtWidgets import QFileDialog, QMessageBox, QTableWidgetItem

FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'NAIAD_dialog_base.ui'))

class NAIADDialog(QtWidgets.QDialog, FORM_CLASS):
    def __init__(self, parent=None):
        super(NAIADDialog, self).__init__(parent)
        self.setupUi(self)

        # 绑定控件
        self.label_chemin = self.findChild(QtWidgets.QLabel, "label_chemin")
        self.bouton_csv = self.findChild(QtWidgets.QPushButton, "bouton_csv")
        self.bouton_generer = self.findChild(QtWidgets.QPushButton, "bouton_generer")
        self.bouton_tableau = self.findChild(QtWidgets.QPushButton, "bouton_tableau")
        self.tableau_donnees = self.findChild(QtWidgets.QTableWidget, "tableau_donnees")

        self._verifier_widgets()
        self._initialiser_interface()

        self.chemin_fichier = ""

    def _verifier_widgets(self):
        required = {
            self.label_chemin, self.bouton_csv,
            self.bouton_generer, self.bouton_tableau,
            self.tableau_donnees
        }
        if None in required:
            missing = [w.objectName() for w in required if w is None]
            raise AttributeError(f"Widgets manquants: {', '.join(missing)}")

    def _initialiser_interface(self):
        self.label_chemin.setText("Aucun fichier sélectionné")
        self.bouton_csv.clicked.connect(self.importer_csv)
        self.bouton_generer.clicked.connect(self.accept)
        self.bouton_tableau.clicked.connect(self.afficher_tableau)

    def importer_csv(self):
        try:
            fichier, _ = QFileDialog.getOpenFileName(
                self, "Sélectionner un fichier CSV",
                QtCore.QDir.homePath(), "CSV (*.csv);;All Files (*)"
            )
            if fichier:
                self._valider_fichier(fichier)
                self.chemin_fichier = fichier
                self.label_chemin.setText(os.path.basename(fichier))
                self.label_chemin.setToolTip(fichier)
        except Exception as e:
            self._gerer_erreur(e)

    def _valider_fichier(self, chemin):
        with open(chemin, 'r', encoding='utf-8') as f:
            lecteur = csv.DictReader(f)
            required = {'drone_id', 'longitude', 'latitude', 'depth', 'timestamp'}
            if not required.issubset(lecteur.fieldnames):
                manquants = required - set(lecteur.fieldnames)
                raise ValueError(f"Champs manquants: {', '.join(manquants)}")

    def afficher_tableau(self):
        try:
            if not self.chemin_fichier:
                raise ValueError("Aucun fichier sélectionné")

            self.tableau_donnees.clear()
            with open(self.chemin_fichier, 'r', encoding='utf-8') as f:
                lecteur = csv.reader(f)
                headers = next(lecteur)
                data = list(lecteur)
                self.tableau_donnees.setRowCount(len(data))
                self.tableau_donnees.setColumnCount(len(headers))
                self.tableau_donnees.setHorizontalHeaderLabels(headers)
                for row_idx, row in enumerate(data):
                    for col_idx, value in enumerate(row):
                        self.tableau_donnees.setItem(row_idx, col_idx, QTableWidgetItem(value))
        except Exception as e:
            self._gerer_erreur(e)

    def get_chemin_csv(self):
        return self.chemin_fichier

    def _gerer_erreur(self, erreur):
        QMessageBox.critical(self, "Erreur", str(erreur))