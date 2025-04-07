# -*- coding: utf-8 -*-
"""
/***************************************************************************
 MNT
                                 A QGIS plugin
 This plugin adds MNT on map
 Generated by Plugin Builder: http://g-sherman.github.io/Qgis-Plugin-Builder/
                              -------------------
        begin                : 2025-04-04
        git sha              : $Format:%H$
        copyright            : (C) 2025 by Truong Anh Huy LE
        email                : huymop.lee@gmail.com
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""
from qgis.PyQt.QtCore import *
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import QAction, QFileDialog, QMessageBox

from qgis.core import *
from qgis.gui import *
from qgis.utils import iface
from qgis import processing
from osgeo import gdal

import os
import re
import random
import tempfile

# Initialize Qt resources from file resources.py
from .resources import *
# Import the code for the dialog
from .MNT_dialog import MNTDialog
import os.path


class MNT:
    """QGIS Plugin Implementation."""

    def __init__(self, iface):
        """Constructor.

        :param iface: An interface instance that will be passed to this class
            which provides the hook by which you can manipulate the QGIS
            application at run time.
        :type iface: QgsInterface
        """
        # Save reference to the QGIS interface
        self.iface = iface
        # initialize plugin directory
        self.plugin_dir = os.path.dirname(__file__)
        # initialize locale
        locale = QSettings().value('locale/userLocale')[0:2]
        locale_path = os.path.join(
            self.plugin_dir,
            'i18n',
            'MNT_{}.qm'.format(locale))

        if os.path.exists(locale_path):
            self.translator = QTranslator()
            self.translator.load(locale_path)
            QCoreApplication.installTranslator(self.translator)

        # Declare instance attributes
        self.actions = []
        self.menu = self.tr(u'&MNT')

        # Check if plugin was started the first time in current QGIS session
        # Must be set in initGui() to survive plugin reloads
        self.first_start = None

    # noinspection PyMethodMayBeStatic
    def tr(self, message):
        """Get the translation for a string using Qt translation API.

        We implement this ourselves since we do not inherit QObject.

        :param message: String for translation.
        :type message: str, QString

        :returns: Translated version of message.
        :rtype: QString
        """
        # noinspection PyTypeChecker,PyArgumentList,PyCallByClass
        return QCoreApplication.translate('MNT', message)


    def add_action(
        self,
        icon_path,
        text,
        callback,
        enabled_flag=True,
        add_to_menu=True,
        add_to_toolbar=True,
        status_tip=None,
        whats_this=None,
        parent=None):
        """Add a toolbar icon to the toolbar.

        :param icon_path: Path to the icon for this action. Can be a resource
            path (e.g. ':/plugins/foo/bar.png') or a normal file system path.
        :type icon_path: str

        :param text: Text that should be shown in menu items for this action.
        :type text: str

        :param callback: Function to be called when the action is triggered.
        :type callback: function

        :param enabled_flag: A flag indicating if the action should be enabled
            by default. Defaults to True.
        :type enabled_flag: bool

        :param add_to_menu: Flag indicating whether the action should also
            be added to the menu. Defaults to True.
        :type add_to_menu: bool

        :param add_to_toolbar: Flag indicating whether the action should also
            be added to the toolbar. Defaults to True.
        :type add_to_toolbar: bool

        :param status_tip: Optional text to show in a popup when mouse pointer
            hovers over the action.
        :type status_tip: str

        :param parent: Parent widget for the new action. Defaults None.
        :type parent: QWidget

        :param whats_this: Optional text to show in the status bar when the
            mouse pointer hovers over the action.

        :returns: The action that was created. Note that the action is also
            added to self.actions list.
        :rtype: QAction
        """

        icon = QIcon(icon_path)
        action = QAction(icon, text, parent)
        action.triggered.connect(callback)
        action.setEnabled(enabled_flag)

        if status_tip is not None:
            action.setStatusTip(status_tip)

        if whats_this is not None:
            action.setWhatsThis(whats_this)

        if add_to_toolbar:
            # Adds plugin icon to Plugins toolbar
            self.iface.addToolBarIcon(action)

        if add_to_menu:
            self.iface.addPluginToVectorMenu(
                self.menu,
                action)

        self.actions.append(action)

        return action

    def initGui(self):
        """Create the menu entries and toolbar icons inside the QGIS GUI."""

        icon_path = os.path.join(self.plugin_dir, 'icon.png')
        self.add_action(
            icon_path,
            text=self.tr(u'MNT'),
            callback=self.run,
            parent=self.iface.mainWindow())

        # will be set False in run()
        self.first_start = True


    def unload(self):
        """Removes the plugin menu item and icon from QGIS GUI."""
        for action in self.actions:
            self.iface.removePluginVectorMenu(
                self.tr(u'&MNT'),
                action)
            self.iface.removeToolBarIcon(action)

    def select_alti_folder(self):
        folder = QFileDialog.getExistingDirectory(self.dlg, "Select Alti folder")
        if folder:
            self.dlg.lineEdit.setText(folder)

    def select_output_file(self):
        filename, _filter = QFileDialog.getSaveFileName(
            self.dlg, "Select output file ", "", '*.shp')
        self.dlg.lineEdit_2.setText(filename)


    def run(self):
        """Run method that performs all the real work"""

        # Create the dialog with elements (after translation) and keep reference
        # Only create GUI ONCE in callback, so that it will only load when the plugin is started
        if self.first_start == True:
            self.first_start = False
            self.dlg = MNTDialog()
            self.dlg.pushButton.clicked.connect(self.select_alti_folder)
            self.dlg.pushButton_2.clicked.connect(self.select_output_file)
        layers = QgsProject.instance().layerTreeRoot().children()
        self.dlg.comboBox.clear()
        self.dlg.comboBox.addItems([layer.name() for layer in layers])

        # show the dialog
        self.dlg.show()
        # Run the dialog event loop
        result = self.dlg.exec_()
        # See if OK was pressed
        if result:
            # Do something useful here - delete the line containing pass and
            # substitute with your code.

            # Read alti folder
            alti_folder = self.dlg.lineEdit.text()

            # Read Zone layer
            selectedLayerIndex = self.dlg.comboBox.currentIndex()
            Zone = layers[selectedLayerIndex].layer()
            Zone_path = Zone.dataProvider().dataSourceUri()

            # Read Output layer
            terrain = self.dlg.lineEdit_2.text()

            # Define projection system Lambert 93 (EPSG:2154)
            crs_lambert93 = QgsCoordinateReferenceSystem("EPSG:2154")

            # Get the extent of selected layer
            emprise = Zone.extent()
            xmin_emprise, ymin_emprise, xmax_emprise, ymax_emprise = emprise.xMinimum(), emprise.yMinimum(), emprise.xMaximum(), emprise.yMaximum()

            # Create temporary rectangle zone shapefile
            # temp_shapefile = os.path.join(tempfile.gettempdir(), "temp_rectangle.shp")
            # fields = QgsFields()
            # fields.append(QgsField("id", QVariant.Int))
            # writer = QgsVectorFileWriter(temp_shapefile, "UTF-8", fields, QgsWkbTypes.Polygon, crs_lambert93, "ESRI Shapefile")
            # feature = QgsFeature()
            # feature.setGeometry(QgsGeometry.fromRect(QgsRectangle(xmin_emprise, ymin_emprise, xmax_emprise, ymax_emprise)))
            # feature.setAttributes([1])
            # writer.addFeature(feature)
            # del writer

            # Read raster file
            files = [f for f in os.listdir(alti_folder) if f.endswith(".asc")]
            file_example = random.choice(files)
            path_file_exemple = os.path.join(alti_folder, file_example)
            path_file_exemple = os.path.normpath(path_file_exemple)
            path_file_exemple = path_file_exemple.replace("\\", "/")

            # Read metadata
            with open(path_file_exemple, "r") as f:
                meta = [next(f) for _ in range(6)]

            ncols = int(meta[0].split()[1])  
            nrows = int(meta[1].split()[1])  
            cellsize = float(meta[4].split()[1])  

            # Calculate extent
            xmin_limit = xmin_emprise - (ncols * cellsize)
            xmax_limit = xmax_emprise
            ymin_limit = ymin_emprise
            ymax_limit = ymax_emprise + (nrows * cellsize)

            # Filter files corresponding to extent
            pattern = re.compile(r".*_FXX_(\d{4})_(\d{4})_.*\.asc")
            file_to_fusion = []

            for file in files:
                match = pattern.match(file)
                if match:
                    x_raster = int(match.group(1)) * 1000  
                    y_raster = int(match.group(2)) * 1000  

                    if xmin_limit <= x_raster <= xmax_limit and ymin_limit <= y_raster <= ymax_limit:
                        file_to_fusion.append(os.path.join(alti_folder, file))

            # Verify if there are raster files to fusion
            if len(file_to_fusion) > 0:
                # Fusion raster files
                temp_dir = tempfile.gettempdir()
                raster_fusion_tiff = os.path.join(temp_dir, "raster_fusion_temp.tif")
                if os.path.exists(raster_fusion_tiff):
                    os.remove(raster_fusion_tiff)

                params_fusion = {
                    'INPUT': file_to_fusion,
                    'PCT': False,
                    'SEPARATE': False,
                    'NODATA_INPUT': None,
                    'NODATA_OUTPUT': -9999,
                    'OPTIONS': '',
                    'DATA_TYPE': 5,  # Float32
                    'OUTPUT': raster_fusion_tiff
                }
                processing.run("gdal:merge", params_fusion)

                processing.run("gdal:assignprojection", {
                    'INPUT': raster_fusion_tiff,
                    'CRS': crs_lambert93.authid()
                    })

                ds = gdal.Open(raster_fusion_tiff, gdal.GA_Update)
                if ds:
                    band = ds.GetRasterBand(1)
                    band.ComputeStatistics(False)
                    ds = None


                # Add fusioned file to map
                # raster_fusion_layer = QgsRasterLayer(raster_fusion_tiff, "Raster Fusionné Temporaire", "gdal")
                # QgsProject.instance().addMapLayer(raster_fusion_layer)

                # Create level line
                contour_asc = os.path.join(temp_dir, "contour.shp")
                if os.path.exists(contour_asc):
                    os.remove(contour_asc)

                params_contour = {
                    'INPUT': raster_fusion_tiff,
                    'BAND': 1,
                    'INTERVAL': 1.0,
                    'FIELD_NAME' : 'ELEV',
                    'CREATE_3D': False,
                    'IGNORE_NODATA': True,
                    'NODATA': -9999,
                    'OFFSET': 0,
                    'OUTPUT': contour_asc
                }

                processing.run("gdal:contour", params_contour)

                # Clip file
                params_clip = {
                    'INPUT': contour_asc,
                    'OVERLAY': Zone,
                    'OUTPUT': terrain
                }

                processing.run("native:clip", params_clip)

                # raster_decoupe_layer = QgsRasterLayer(raster_decoupe_asc, "Raster Découpé Temporaire", "gdal")
                # QgsProject.instance().addMapLayer(raster_decoupe_layer)

                terrain_layer = QgsVectorLayer(terrain, "Courbes de niveau", "ogr")
                QgsProject.instance().addMapLayer(terrain_layer)

                # elevations = [feature['ELEV'] for feature in contour_layer.getFeatures()]
                # max_alti = max(elevations)
                # min_alti = min(elevations)

                QMessageBox.information(
                    self.iface.mainWindow(),
                    "Fusion terminée",
                    f"Nombre de raster fusionnés : {len(file_to_fusion)}\n"
                    # f"Max Alti: {max_alti} m\n"
                    # f"Min Alti: {min_alti} m"
                )

            else:
                print("❌ Aucun raster MNT trouvé pour la fusion.")
