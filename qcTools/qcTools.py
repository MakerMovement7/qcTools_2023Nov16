import sys
import os
import fnmatch
import math
import PIL.Image
import PIL.ExifTags
import win32clipboard as cb
import random
import csv
import pandas as pd
from datetime import datetime
from qgis.gui import QgsMapToolEmitPoint, QgsMapTool, QgsMessageBar
from PyQt5.QtWidgets import QComboBox, QLineEdit, QAction, QShortcut, QMessageBox,QFileDialog,QProgressBar,QInputDialog
from qgis.utils import iface
from PyQt5.QtGui import *
from PyQt5.QtCore import *
#For QIcon, etc
from qgis.core import *
from qgis.gui import *
import qcTools.resources
import psycopg2
import re
import numpy as np
from pathlib import Path
from win32com.client import Dispatch


class QC_Tools():
	def __init__(self,iface):
		self.iface=iface
		#self.settings = QSettings('Geodigital', 'db_params_settings')

	def initGui(self):
		#check which user is using plugin
		self.settings = QSettings('Geodigital', 'db_params_settings')
		currentConnectionName = str(self.settings.value('current_connection'))
		try:
			username = str(self.settings.value('connections')[currentConnectionName]['user_name'])
		except:
			username= str('postgres')

		### wuFinder ###
		#set toolbar
		self.toolbar = self.iface.pluginToolBar()
		## wuFinder drop-down menu ##
		# Create & add drop-down menu
		self.dropDownMenu = QComboBox(self.iface.mainWindow())
		# Set width
		self.dropDownMenu.setFixedWidth(173)
		# add items
		self.dropDownMenu.addItem("Road Unit Id:")
		self.dropDownMenu.addItem("WU ID:")
		self.dropDownMenu.addItem("Path Id:")
		self.dropDownMenu.addItem("Boundary Id:")
		self.dropDownMenu.addItem("Crossing Id:")
		self.dropDownMenu.addItem("Delineator Id:")
		self.dropDownMenu.addItem("Road Object Id:")
		self.dropDownMenu.addItem("Path Type Chg Id:")
		self.dropDownMenu.addItem("Siloc Id:")
		self.dropDownMenu.addItem("Trail Name:")
		self.dropDownMenu.addItem("WU Connection Id:")
		self.dropDownMenu.addItem("Intersection Id:")
		self.dropDownMenu.addItem("OSM Intersection Node:")
		self.dropDownMenu.addItem("WU Assigned Lidar:")
		self.dropDownMenu.addItem("Count Features for WU(s):")
		#self.dropDownMenu.addItem("Old->New Ru:")
		#self.dropDownMenu.addItem("Image On Click:")
		if 'ushr_' in username.lower() and 'bps' not in username.lower() and 'gsi' not in username.lower():
			#self.dropDownMenu.addItem("Ru Geoms in State:")
			self.dropDownMenu.addItem("Random RUs from WU List:")
			#self.dropDownMenu.addItem("SQL Runner:")
			#self.dropDownMenu.addItem("Lidar SHPs for WU:")
			self.dropDownMenu.addItem("USHR Ground Images:")
		if 'jgreener' in username.lower() or 'todonnell' in username.lower() or 'mmicallef' in username.lower():
			self.dropDownMenu.addItem("Import WU List (to open Training DB):")
		#if 'scs_' in username.lower():
		#	self.dropDownMenu.addItem("Ru Geoms in State:")
		self.dropDownMenu.addItem("Coords (ME):")
		self.dropDownMenu.addItem("Coords (USA CAN JPN EU):")

		# Add drop-down menu
		self.dropDownAction = self.toolbar.addWidget(self.dropDownMenu)
		## wuFinder Text box ##
		# Create & add a textbox
		self.textbox = QLineEdit(self.iface.mainWindow())
		# Set width
		self.textbox.setFixedWidth(200)
		# Add textbox to toolbar
		self.txtAction = self.toolbar.addWidget(self.textbox)

		## wuFinder icon ##
		wuFinder_Icon = QIcon(":/plugins/qcTools/wuFinder_Icon.png")
		self.action5 = QAction(wuFinder_Icon, "Search For This Feature ID", self.iface.mainWindow())
		self.action5.triggered.connect(self.onRunWorkUnitFinder)
		self.iface.addPluginToMenu("QC Tools",self.action5)
		self.iface.addToolBarIcon(self.action5)

		### FilterFeature ###
		filterFeature_Icon = QIcon(":/plugins/qcTools/FilterFeature_Icon.png")
		self.action2 = QAction(filterFeature_Icon,"Click Over A Road Unit to HIDE that RU, Click Where No RU Exists to SHOW", self.iface.mainWindow())
		self.action2.triggered.connect(self.onRunFilterFeature)
		self.iface.addPluginToMenu("QC Tools",self.action2)
		self.iface.addToolBarIcon(self.action2)

		### Hide Nearby Features ###

		### ShowRastersOnly ###
		showRastersOnly_Icon = QIcon(":/plugins/qcTools/ShowRastersOnly_Icon.png")
		self.action3 = QAction(showRastersOnly_Icon,"Toggle Imagery-Only On/Off", self.iface.mainWindow())
		self.action3.triggered.connect(self.onRunShowRastersOnly)
		self.iface.addPluginToMenu("QC Tools",self.action3)
		self.iface.addToolBarIcon(self.action3)
		# shortcut doesn't overwrite existing F2, if assigned
		self.iface.registerMainWindowAction(self.action3,'F2')

		'''
		### WU_Seg_Sync_CSAV3_Info ###
		filterFeature_Icon = QIcon(":/plugins/qcTools/WU_Seg_Sync_CSAV3_Info_Icon.png")
		self.action7 = QAction(filterFeature_Icon,"Use for WU_Seg_Sync: Open s2s_segment database for a STATE first. Then click this button to load CSAV3_Info Layer for same STATE.", self.iface.mainWindow())
		self.action7.triggered.connect(self.WU_Seg_Sync_CSAV3_Info)
		self.iface.addPluginToMenu("QC Tools",self.action7)
		self.iface.addToolBarIcon(self.action7)
		'''

		### onRunRemoveSelection ###
		RemoveSelection_Icon = QIcon(":/plugins/qcTools/RemoveSelection_Icon.png")
		self.action8 = QAction(RemoveSelection_Icon,"Remove Selection", self.iface.mainWindow())
		self.action8.triggered.connect(self.onRunRemoveSelection)
		self.iface.addPluginToMenu("QC Tools",self.action8)
		self.iface.addToolBarIcon(self.action8)

		### ApplyStyles ###
		applyStyles_Icon = QIcon(":/plugins/qcTools/ApplyStyles_Icon.png")
		self.action10 = QAction(applyStyles_Icon,"Loads styles on layers in layer panel, if layer name matches name in \\Documents\\QGIS\\Style Files\\", self.iface.mainWindow())
		self.action10.triggered.connect(self.onRunApplyStylesWithMatchingNames)
		self.iface.addPluginToMenu("QC Tools",self.action10)
		self.iface.addToolBarIcon(self.action10)

		### Administrative Boundaries SHP###
		AdminBoundaries_Icon = QIcon(":/plugins/qcTools/AdminBoundaries_Icon.png")
		self.action11 = QAction(AdminBoundaries_Icon,"Loads Administrative Boundaries", self.iface.mainWindow())
		self.action11.triggered.connect(self.onRun_Load_AdministrativeBoundaries_Shapefile)
		self.iface.addPluginToMenu("QC Tools",self.action11)
		self.iface.addToolBarIcon(self.action11)

		###Overlap Tool###
		overlapTool_Icon = QIcon(":/plugins/qcTools/overlapTool_Icon.png")
		self.action12 = QAction(overlapTool_Icon,"Overlap Tool: Loads Overlap Style to Road Unit Segment layer. Visually check this layer for overlapping hatch-marks.", self.iface.mainWindow())
		self.action12.triggered.connect(self.onRunOverlapTool)
		self.iface.addPluginToMenu("QC Tools",self.action12)
		self.iface.addToolBarIcon(self.action12)

		## PrevNext icon ##
		PrevNext_Icon = QIcon(":/plugins/qcTools/PrevNext_Icon.png")
		self.action15 = QAction(PrevNext_Icon, "Move Forward and Back Through Layer", self.iface.mainWindow())
		self.action15.triggered.connect(self.onRunPrevNext)
		self.iface.addPluginToMenu("QC Tools",self.action15)
		self.iface.addToolBarIcon(self.action15)

		###3D Lidar Viewer###
		if 'jgreener' in username.lower():
			threeDLidarViewer_Icon = QIcon(":/plugins/qcTools/threeDLidarViewer_Icon.png")
			self.action13 = QAction(threeDLidarViewer_Icon,"3D Lidar Viewer: select lidar layer then click on point in map to view that 3D lidar there", self.iface.mainWindow())
			self.action13.triggered.connect(self.onRunThreeDLidarViewer)
			self.iface.addPluginToMenu("QC Tools",self.action13)
			self.iface.addToolBarIcon(self.action13)

		### change Wu 4 Rus ###
		if 'jgreener' in username.lower() or 'jpepper' in username.lower() or 'keri' in username.lower():
			changeWu4Rus_Icon = QIcon(":/plugins/qcTools/changeWu4Rus_Icon.png")
			self.action14 = QAction(changeWu4Rus_Icon,"Change WU_ID for Selected RUs", self.iface.mainWindow())
			self.action14.triggered.connect(self.onRunchangeWu4Rus)
			self.iface.addPluginToMenu("QC Tools",self.action14)
			self.iface.addToolBarIcon(self.action14)

	def unload(self):
		self.settings = QSettings('Geodigital', 'db_params_settings')
		currentConnectionName = str(self.settings.value('current_connection'))
		try:
			username = str(self.settings.value('connections')[currentConnectionName]['user_name'])
		except:
			username = str('postgres')
		#### wuFinder ###
		self.iface.removePluginMenu("QC Tools",self.action5)
		self.iface.removeToolBarIcon(self.action5)
		## wuFinder Text box ##
		self.textbox.setFixedWidth(0)
		## wuFinder Drop Down box ##
		self.dropDownMenu.setFixedWidth(0)

		### FilterFeature ###
		self.iface.removePluginMenu("QC Tools",self.action2)
		self.iface.removeToolBarIcon(self.action2)

		#### ShowRastersOnly ###
		self.iface.removePluginMenu("QC Tools",self.action3)
		self.iface.removeToolBarIcon(self.action3)

		'''
		### WU_Seg_Sync_CSAV3_Info ###
		self.iface.removePluginMenu("QC Tools",self.action7)
		self.iface.removeToolBarIcon(self.action7)
		'''

		### onRunRemoveSelection ###
		self.iface.removePluginMenu("QC Tools",self.action8)
		self.iface.removeToolBarIcon(self.action8)

		### ApplyStyles ###
		self.iface.removePluginMenu("QC Tools",self.action10)
		self.iface.removeToolBarIcon(self.action10)

		### Administrative Boundaries SHP###
		self.iface.removePluginMenu("QC Tools",self.action11)
		self.iface.removeToolBarIcon(self.action11)

		###Overlap Tool###
		self.iface.removePluginMenu("QC Tools",self.action12)
		self.iface.removeToolBarIcon(self.action12)

		###PrevNext Tool###
		self.iface.removePluginMenu("QC Tools",self.action15)
		self.iface.removeToolBarIcon(self.action15)

		###3D Lidar Viewer###
		if 'jgreener' in username.lower():
			self.iface.removePluginMenu("QC Tools",self.action13)
			self.iface.removeToolBarIcon(self.action13)

		### change Wu 4 Rus ###
		if 'jgreener' in username.lower() or 'jpepper' in username.lower() or 'keri' in username.lower():
			self.iface.removePluginMenu("QC Tools",self.action14)
			self.iface.removeToolBarIcon(self.action14)

	def onRunPrevNext(self):
		print("START PROCESS: PrevNext")
		#TODO: when loaded layer gets deleted and the dialog still exists, python error..
				#maybe close dialog when loaded layer gets deleted or clear out its values
		from PyQt5 import QtWidgets, uic
		from qgis.PyQt.QtWidgets import QWidget, QDialog, QLineEdit
		from qgis.core import QgsProject
		from PyQt5.QtWidgets import QShortcut
		from PyQt5.QtGui import QKeySequence
		from PyQt5.QtCore import QEventLoop
		from itertools import islice

		class PrevNextDialog(QDialog):
			def __init__(self):
				super().__init__(iface.mainWindow())  # Set the parent as iface.mainWindow()
				#self.setWindowFlags(self.windowFlags() & ~Qt.WindowModal)
				uic.loadUi(os.path.join(os.path.dirname(__file__), 'PrevNextD.ui'), self)
				self.setWindowTitle("Dialog - Previous / Next Feature")
				print('loaded UI')
				self.selected_layer = None
				self.selected_id = None
				self.selected_Notesfield = None
				self.LoadedLayerExtension=None
				self.feature_index = 0
				self.ButtonsAllowed=True
				self.EditingAllowed=True
				self.IndexEdit.setAlignment(Qt.AlignRight)

				self.NextButton.setEnabled(True)
				self.PreviousButton.setEnabled(True)
				self.NextButton.clicked.connect(self.go_forward)
				self.NextButton.setAutoDefault(False)
				self.PreviousButton.clicked.connect(self.go_backward)
				self.PreviousButton.setAutoDefault(False)
				self.IndexEdit.returnPressed.connect(self.zoom_to_feature_by_input)
				self.ExportButton.clicked.connect(self.create_working_copy)
				self.ExportButton.setAutoDefault(False)
				self.LoadLayerButton.clicked.connect(self.load_selected_layer)
				self.LoadLayerButton.setAutoDefault(False)
				self.AddNotesButton.clicked.connect(self.add_notes_column)
				self.AddNotesButton.setAutoDefault(False)
				self.LoadOptionsButton.clicked.connect(self.load_options_from_file)
				self.LoadOptionsButton.setAutoDefault(False)
				#self.FieldsComboBox.currentIndexChanged.connect(self.update_id_text)
				self.FieldsComboBox.currentIndexChanged.connect(self.update_id_selection)
				self.NotesComboBox.currentIndexChanged.connect(self.update_selected_Notesfield)
				# Connect the SaveButton's clicked signal to the save_notes_to_feature slot
				self.SaveButton.clicked.connect(self.save_notes_to_feature)
				self.SaveButton.setAutoDefault(False)
				#self.CancelButton.clicked.connect(self.reject)
				#QgsProject.instance().layersRemoved.connect(self.handle_layers_removed)
				print("Button signals connected")

				# New values to set
				new_values = ["Pass", "Fail", ""]
				self.DropDownMenu.clear()  # Clear the current items
				self.DropDownMenu.addItems(new_values)  # Add the new items

				# shortcuts
				self.next_shortcut = QShortcut(QKeySequence(Qt.Key_Right), self)
				self.prev_shortcut = QShortcut(QKeySequence(Qt.Key_Left), self)
				self.next_shortcut.activated.connect(self.go_forward)
				self.prev_shortcut.activated.connect(self.go_backward)
				#shortcuts

				self.load_selected_layer()
				self.update_total_count()

			def apply_style(self, layer):
				print('Try apply style')
				from qgis.PyQt.QtGui import QColor
				from qgis.core import QgsSingleSymbolRenderer, QgsSymbol, QgsSimpleLineSymbolLayer, QgsSimpleMarkerSymbolLayer, QgsSimpleFillSymbolLayer
				active_layer = layer

				if active_layer:
					# Get the geometry type of the active layer
					geometry_type = active_layer.geometryType()

					# Create a default symbol for each geometry type
					symbol = None
					color=QColor(255, 3, 242)
					if geometry_type == QgsWkbTypes.PointGeometry:
						symbol = QgsMarkerSymbol.defaultSymbol(geometry_type)
						symbol_layer = QgsSimpleMarkerSymbolLayer.create({'name': 'diamond', 'width': '3','color': color})
						symbol.changeSymbolLayer(0, symbol_layer)
					elif geometry_type == QgsWkbTypes.LineGeometry:
						symbol = QgsLineSymbol.defaultSymbol(geometry_type)
						symbol_layer = QgsSimpleLineSymbolLayer.create({'width': '3', 'color': color})
						symbol.changeSymbolLayer(0, symbol_layer)
					elif geometry_type == QgsWkbTypes.PolygonGeometry:
						symbol = QgsFillSymbol.createSimple({'color': QColor('transparent'),'outline_color': color, 'outline_style': 'solid', 'outline_width': '1'})

					if symbol:
						renderer = QgsSingleSymbolRenderer(symbol)
						active_layer.setRenderer(renderer)
						active_layer.triggerRepaint()   # Refresh the layer to apply the new style
				else:
					print('Error: Apply style failed')

			def on_layer_deleted(self):
				print('Layer About to be Deleted, Run on_layer_deleted')
				#self.disable_buttons_and_clear_text("Load Layer to Begin.")
				self.project = QgsProject.instance()
				self.project.layerWillBeRemoved.disconnect(self.on_layer_deleted)


			def update_id_selection(self, index):
				self.selected_id = self.FieldsComboBox.itemText(index)
				self.update_id_text()

			def save_notes_to_feature(self):
				if self.ButtonsAllowed==True and self.EditingAllowed==True:
					print('starting save notes function')
					value_to_save = self.DropDownMenu.currentText()
					layer =self.selected_layer
					if layer:
						try:
							with edit(layer):
								# Get the index of the PrevNext field
								prev_next_field_index = layer.fields().indexFromName("PrevNext")

								# Edit the first feature's PrevNext attribute value
								feature = self.selected_layer.getFeature(self.feature_index)
								layer.changeAttributeValue(feature.id(), prev_next_field_index, value_to_save)
								self.update_Notesfield_value_text()
								self.update_id_text()
						except:
							print('Layer cannot be edited. Please create Working Copy, then work from that.')
							#error text
							iface.messageBar().clearWidgets()
							errorText='Layer cannot be edited. Please create Working Copy, then work from that.'
							widget = iface.messageBar().createMessage(errorText)
							iface.messageBar().pushWidget(widget, Qgis.Info,duration=5)
				elif self.EditingAllowed==False:
					iface.messageBar().clearWidgets()
					errorText="Layer Not Editable in QGIS. Please 'Create Working Copy' first."
					widget = iface.messageBar().createMessage(errorText)
					iface.messageBar().pushWidget(widget, Qgis.Info,duration=5)

			def update_selected_Notesfield(self, index):
				self.selected_Notesfield = self.NotesComboBox.itemText(index)
				self.update_Notesfield_value_text()

			def update_Notesfield_value_text(self):
				if self.LoadedLayerExtension!='else':
					print('update id text: not else')
					if self.selected_layer and self.selected_Notesfield is not None:
						fields = self.selected_layer.fields()
						if self.selected_Notesfield in [field.name() for field in fields]:
							try:
								feature = self.selected_layer.getFeature(self.feature_index)
								if feature:
									attribute_value = feature.attribute(self.selected_Notesfield)
									self.NotesText.setText(str(attribute_value))
							except:
								print('Error updating Notes text')
						else:
							self.NotesText.clear()  # Clear the text if the field doesn't exist
					else:
						self.NotesText.clear()  # Clear the text if no layer or field is selected
				else:
					print('ELSE update id text')
					if self.selected_layer and self.selected_Notesfield is not None:
						fields = self.selected_layer.fields()
						if self.selected_Notesfield in [field.name() for field in fields]:
							if True:
								layer = self.selected_layer  # Get the active selected layer
								target_row_index = self.feature_index  # 8th row (0-based index)
								if layer is not None and layer.featureCount() > target_row_index:
									features = layer.getFeatures()
									target_feature = next(islice(features, target_row_index, target_row_index + 1), None)

									if target_feature:
										attributes = target_feature.attributes()
										field_names = [field.name() for field in layer.fields()]
										for field_name, value in zip(field_names, attributes):
											if field_name == self.selected_id:
												self.NotesText.setText(str(value))
							#except:
							#	print('Error updating Notes text')
						else:
							self.NotesText.clear()  # Clear the text if the field doesn't exist
					else:
						self.NotesText.clear()
			def update_id_text(self):
				if self.LoadedLayerExtension!='else':
					print('update id text: not else')
					if self.selected_layer and self.selected_id is not None:
						fields = self.selected_layer.fields()
						if self.selected_id in [field.name() for field in fields]:
							try:
								feature = self.selected_layer.getFeature(self.feature_index)
								if feature:
									attribute_value = feature.attribute(self.selected_id)
									self.FieldValueText.setText(str(attribute_value))
							except:
								print('Error updating id text')
						else:
							self.FieldValueText.clear()  # Clear the text if the field doesn't exist
					else:
						self.FieldValueText.clear()  # Clear the text if no layer or field is selected
				else:
					print('ELSE update id text')
					if self.selected_layer and self.selected_id is not None:
						fields = self.selected_layer.fields()
						if self.selected_id in [field.name() for field in fields]:
							if True:
								layer = self.selected_layer  # Get the active selected layer
								target_row_index = self.feature_index  # 8th row (0-based index)
								if layer is not None and layer.featureCount() > target_row_index:
									features = layer.getFeatures()
									target_feature = next(islice(features, target_row_index, target_row_index + 1), None)

									if target_feature:
										attributes = target_feature.attributes()
										field_names = [field.name() for field in layer.fields()]
										for field_name, value in zip(field_names, attributes):
											if field_name == self.selected_id:
												self.FieldValueText.setText(str(value))

									else:
										print(f"No feature in the layer at row index {target_row_index}.")
								else:
									print("No active selected layer.")

							#except:
							#	print('Error updating id text')
						else:
							self.FieldValueText.clear()  # Clear the text if the field doesn't exist
					else:
						self.FieldValueText.clear()
			def populate_fields_combobox(self):
				if self.selected_layer:
					fields = self.selected_layer.fields()
					field_names = [field.name() for field in fields]
					self.FieldsComboBox.clear()
					self.FieldsComboBox.addItems(field_names)
					self.update_id_selection(0)
					self.NotesComboBox.clear()
					self.NotesComboBox.addItems(field_names)
					self.update_selected_Notesfield(0)
				else:
					print('Error: Layer Not Found')

			def run_dialog(self):
				# Check if a PrevNextDialog instance is already open
				existing_dialogs = [widget for widget in QApplication.instance().topLevelWidgets() if isinstance(widget, PrevNextDialog)]
				if not existing_dialogs:
					#error text
					iface.messageBar().clearWidgets()
					errorText='Prev Next Dialog already open.'
					widget = iface.messageBar().createMessage(errorText)
					iface.messageBar().pushWidget(widget, Qgis.Info,duration=5)
				else:
					selected_layer = iface.activeLayer()  # Get the currently selected layer
					if selected_layer and selected_layer.type() == QgsMapLayer.VectorLayer:
						iface.messageBar().clearWidgets()
						self.show()  # Display the dialog non-modally
						self.exec_dialog_loop()

			def closeEvent(self, event):
				super().closeEvent(event)

			def exec_dialog_loop(self):
				loop = QEventLoop()
				loop.exec_()

			def create_working_copy(self):
				if self.ButtonsAllowed==True:
					import processing
					print('name of loaded layer: '+str(self.selected_layer.name()))
					print('feature count of loaded layer: '+ str(self.selected_layer.featureCount()))
					if self.selected_layer:
						layer=self.selected_layer
						#setting suggested filename/path
						try:
							downloads_folder = os.path.expanduser("~") + "/Downloads"
							suggested_filename = os.path.splitext(layer.name())[0] + "_workingCopy.shp"
							suggested=os.path.join(downloads_folder, suggested_filename)
						except:
							suggested=""

						#running dialog and saving export path
						file_dialog = QFileDialog()
						export_path, _ = file_dialog.getSaveFileName(None, "Save Selected Features", suggested, "Shapefile (*.shp)")
						if export_path:
							exported_filename = os.path.basename(export_path)
							# Create a memory copy of the selected layer
							layer.selectAll()
							working_copy = processing.run("native:saveselectedfeatures", {'INPUT': layer, 'OUTPUT': export_path})['OUTPUT']
							layer.removeSelection()
							print("Success")
							iface.messageBar().clearWidgets()
							errorText="Success! Working Copy Created"
							widget = iface.messageBar().createMessage(errorText)
							iface.messageBar().pushWidget(widget, Qgis.Success,duration=5)

							# Load the exported layer into QGIS
							saved_working_copy_layer = QgsVectorLayer(export_path, exported_filename, "ogr")
							if not saved_working_copy_layer.isValid():
								print("Error loading exported layer into QGIS.")
							else:
								QgsProject.instance().addMapLayer(saved_working_copy_layer, True)
								print("Exported layer loaded into QGIS.")
								print('Setting default load layer to newly loaded Working Copy')
								iface.setActiveLayer(saved_working_copy_layer)
								self.load_selected_layer()
								self.add_notes_column()
								self.apply_style(saved_working_copy_layer)
						else:
							#iface.messageBar().clearWidgets()
							errorText="Successfully Cancelled Creation of Working Copy"
							print(errorText)
							#widget = iface.messageBar().createMessage(errorText)
							#iface.messageBar().pushWidget(widget, Qgis.Info,duration=5)
							self.reject
							#self.disable_buttons_and_clear_text('Please save working copy first')
					else:
						print("No layer is loaded.")

			def add_notes_column(self):
				if self.ButtonsAllowed==True and self.EditingAllowed==True:
					if self.selected_layer:
						layer_fields = self.selected_layer.fields()
						prev_next_field_name = "PrevNext"

						if not layer_fields.indexFromName(prev_next_field_name) >= 0:
							# Column not found, add it
							print('About to add Notes column to the layer.')
							if self.LoadedLayerExtension == '.csv':
								print('.csv')
							else:
								print('not csv')
								new_field = QgsField(prev_next_field_name, QVariant.String)
								self.selected_layer.dataProvider().addAttributes([new_field])
								self.selected_layer.updateFields()
							print(f"Added Notes column to the layer.")

							self.populate_fields_combobox()
							fields = self.selected_layer.fields()
							field_names = [field.name() for field in fields]
							pn_index = field_names.index(prev_next_field_name)
							self.NotesComboBox.setCurrentIndex(pn_index)
							self.update_selected_Notesfield(pn_index)
							#success message
							errorText='Success! Notes column added.'
							widget = iface.messageBar().createMessage(errorText)
							iface.messageBar().pushWidget(widget, Qgis.Success,duration=1)
						else:
							print(f"'{prev_next_field_name}' column already exists.")
							#warning message
							iface.messageBar().clearWidgets()
							errorText=f"'{prev_next_field_name}' Notes column already exists."
							widget = iface.messageBar().createMessage(errorText)
							iface.messageBar().pushWidget(widget, Qgis.Info,duration=5)

					else:
						print("No layer is loaded.")
				elif self.EditingAllowed==False:
					iface.messageBar().clearWidgets()
					errorText="Layer Not Editable in QGIS. Please 'Create Working Copy' first."
					widget = iface.messageBar().createMessage(errorText)
					iface.messageBar().pushWidget(widget, Qgis.Info,duration=5)

			def zoom_to_feature_by_input(self):
				print('zooming to feature by input')
				if self.selected_layer:
					total_features = self.selected_layer.featureCount()
					input_text = self.IndexEdit.text()
					try:
						requested_index = int(input_text)
						if 1 <= requested_index <= total_features:
							print('valid feature index')
							self.feature_index = requested_index-1 # Adjust for 0-based index
							self.update_feature_and_pan()
							self.update_total_count()  # Call the method to update the Counter QLabel
							self.update_id_text()
							self.update_Notesfield_value_text()
						else:
							print("Invalid feature index. Enter a value between 1 and", total_features)
							self.IndexEdit.clear()
							if self.LoadedLayerExtension=='.shp':
								displayIndex=self.feature_index+1
							elif self.LoadedLayerExtension=='.gpkg':
								displayIndex=self.feature_index
							elif self.LoadedLayerExtension=='.csv':
								displayIndex=self.feature_index-1
							elif self.LoadedLayerExtension=='else':
								displayIndex=self.feature_index+1
							self.IndexEdit.setText(str(displayIndex))
					except ValueError:
						print("Invalid input. Enter a valid integer.")
				else:
					print('Error: Layer Not Found')

			def update_total_count(self):
				if self.selected_layer:
					#current_index = self.feature_index
					total_features = self.selected_layer.featureCount()
					self.Counter.setText(f"/ {total_features}")
				else:
					print('Error: Layer Not Found')

			def load_options_from_file(self):
				options_file, _ = QFileDialog.getOpenFileName(self, "Open Options File", "", "Excel Files (*.xlsx);;CSV Files (*.csv)")
				if options_file:
					if options_file.lower().endswith('.csv'):
						self.load_options_from_csv(options_file)
					elif options_file.lower().endswith('.xlsx'):
						self.load_options_from_excel(options_file)
					self.DropDownMenu.addItem("")

			def load_options_from_excel(self, file_path):
				self.DropDownMenu.clear()
				try:
					data_frame = pd.read_excel(file_path, engine='openpyxl', header=None)
					for index, row in data_frame.iterrows():
						value = row.iloc[0]
						self.DropDownMenu.addItem(str(value))
				except Exception as e:
					print("Error loading Excel:", e)

			def load_options_from_csv(self, file_path):
				self.DropDownMenu.clear()
				with open(file_path, 'r') as file:
					reader = csv.reader(file, delimiter='\t')  # Use tab as the delimiter
					for row in reader:
						try:
							if row:
								self.DropDownMenu.addItem(row[0])
						except (_csv.Error, UnicodeDecodeError):
							# Stop processing on error
							break

			def load_selected_layer(self):
				selected_layer = iface.activeLayer()  # Get the currently selected layer
				if selected_layer and selected_layer.type() == QgsMapLayer.VectorLayer:
					if selected_layer.featureCount()>0:
						self.project = QgsProject.instance()
						self.project.layerWillBeRemoved.connect(self.on_layer_deleted)
						# Extract the file name from the data source URI
						source_uri = selected_layer.source()
						file_name = source_uri.split('/')[-1].split('?')[0].lower().split('|')[0]  # Extracts the file name from the URI
						self.ButtonsAllowed=True
						self.EditingAllowed==True
						self.LoadedLayerExtension=None
						layer_name = selected_layer.name()  # Get the name of the selected layer
						print("Selected layer name:", layer_name)
						self.layerNameLabel.setText(str(layer_name))
						self.selected_layer = QgsProject.instance().mapLayersByName(layer_name)[0]

						if file_name.endswith('.shp'):
							print('.shp')
							self.LoadedLayerExtension='.shp'
							self.feature_index = 0
							self.enableEditing()
						elif file_name.endswith('.gpkg'):
							print('.gpkg')
							self.LoadedLayerExtension='.gpkg'
							self.feature_index = 1
							self.enableEditing()
						elif file_name.endswith('.csv'):
							print('.csv')
							self.LoadedLayerExtension='.csv'
							self.feature_index = 2
							self.disableEditing()
						else:
							print("Active layer isn't a shapefile or geopackage or csv.")
							self.LoadedLayerExtension='else'
							self.feature_index = 0
							print(str(file_name))
							self.disableEditing()
							# Get the layer registry
							turnOffLayer=selected_layer
							try:
								self.add_notes_column()
							except:
								print('Could not create PrevNext column')
							#QgsProject.instance().layerTreeRoot().findLayer(turnOffLayer.id()).setItemVisibilityChecked(0)
						self.populate_fields_combobox()
						self.update_total_count()
						self.update_feature_and_pan()
						try:
							prev_next_field_name = 'PrevNext'
							fields = self.selected_layer.fields()
							field_names = [field.name() for field in fields]
							pn_index = field_names.index(prev_next_field_name)
							self.NotesComboBox.setCurrentIndex(pn_index)
						except:
							print('No existing PrevNext column to change to.')
					else:
						#error text
						iface.messageBar().clearWidgets()
						errorText='Layer has 0 Features (layer may still be loading?)'
						widget = iface.messageBar().createMessage(errorText)
						iface.messageBar().pushWidget(widget, Qgis.Info,duration=5)

						#self.layerNameLabel.setText("No vector layer is currently selected.")
						self.disable_buttons_and_clear_text("Layer had 0 Features.")
				else:
					#error text
					iface.messageBar().clearWidgets()
					errorText='Please select a vector layer'
					widget = iface.messageBar().createMessage(errorText)
					iface.messageBar().pushWidget(widget, Qgis.Info,duration=5)

					#self.layerNameLabel.setText("No vector layer is currently selected.")
					self.disable_buttons_and_clear_text("No vector layer is currently selected.")
			def disableEditing(self):
				self.EditingAllowed=False
				#self.AddNotesButton.setStyleSheet("color: black")
				#self.SaveButton.setStyleSheet("color: black")
			def enableEditing(self):
				self.EditingAllowed=True
				#self.AddNotesButton.setStyleSheet("color: lightgrey")
				#self.SaveButton.setStyleSheet("color: lightgrey")
			def disable_buttons_and_clear_text(self, text):
				self.layerNameLabel.setText(text)
				self.selected_layer = None
				self.feature_index = 0
				self.IndexEdit.clear()
				self.FieldsComboBox.clear()
				self.FieldValueText.clear()
				self.NotesComboBox.clear()
				self.NotesText.clear()
				self.Counter.clear()
				self.ButtonsAllowed=False
			def go_forward(self):
				print('going forward from ' + str(self.feature_index))
				if self.ButtonsAllowed==True:
					if self.selected_layer:
						total_features = self.selected_layer.featureCount()
						if self.LoadedLayerExtension=='.shp':
							if self.feature_index == total_features-1:
								self.feature_index = 0  # Loop around to the first feature index
							else:
								self.feature_index += 1
						elif self.LoadedLayerExtension=='.gpkg':
							if self.feature_index == total_features:
								self.feature_index = 1  # Loop around to the first feature index
							else:
								self.feature_index += 1
						elif self.LoadedLayerExtension=='.csv':
							if self.feature_index == total_features+1:
								self.feature_index = 2  # Loop around to the first feature index
							else:
								self.feature_index += 1
						elif self.LoadedLayerExtension=='else':
							if self.feature_index == total_features-1:
								self.feature_index = 0  # Loop around to the first feature index
							else:
								self.feature_index += 1
						print('gone forward to ' + str(self.feature_index))
						# Select the newly moved-to feature
						feature = self.selected_layer.getFeature(self.feature_index)
						if feature:
							self.selected_layer.selectByIds([feature.id()])

						self.update_feature_and_pan()
						self.update_total_count()
						self.update_id_text()
						self.update_Notesfield_value_text()
					else:
						print('Error: Layer Not Found')

			def go_backward(self):
				print('going back from ' + str(self.feature_index))
				if self.ButtonsAllowed==True:
					if self.selected_layer:
						total_features = self.selected_layer.featureCount()
						if self.LoadedLayerExtension=='.shp':
							if self.feature_index == 0:
								self.feature_index = total_features-1  # Loop around to the last feature index
							else:
								self.feature_index -= 1
						elif self.LoadedLayerExtension=='.gpkg':
							if self.feature_index == 1:
								self.feature_index = total_features  # Loop around to the last feature index
							else:
								self.feature_index -= 1
						elif self.LoadedLayerExtension=='.csv':
							if self.feature_index == 2:
								self.feature_index = total_features+1  # Loop around to the last feature index
							else:
								self.feature_index -= 1
						elif self.LoadedLayerExtension=='else':
							if self.feature_index == 0:
								self.feature_index = total_features-1  # Loop around to the last feature index
							else:
								self.feature_index -= 1
						print('gone back to ' + str(self.feature_index))
						# Select the newly moved-to feature
						feature = self.selected_layer.getFeature(self.feature_index)
						if feature:
							self.selected_layer.selectByIds([feature.id()])

						self.update_feature_and_pan()
						self.update_total_count()
						self.update_id_text()
						self.update_Notesfield_value_text()
					else:
						print('Error: Layer Not Found')

			def update_feature_and_pan(self):
				print("Panning to Location for current feature index: "+ str(self.feature_index))
				if self.selected_layer:
					if self.selected_layer.featureCount()>0:
						if self.LoadedLayerExtension!='else':
							feature = self.selected_layer.getFeature(self.feature_index)
							geometry = feature.geometry()
						else:
							layer = self.selected_layer  # Get the active selected layer
							target_row_index = self.feature_index  # 8th row (0-based index)
							if layer is not None and layer.featureCount() > target_row_index:
								features = layer.getFeatures()
								target_feature = next(islice(features, target_row_index, target_row_index + 1), None)
								feature=target_feature
								geometry = feature.geometry()

						if geometry:
							print('geometry found')
							centroid = geometry.centroid().asPoint()
							self.pan_to_location(centroid)
						else:
							print('Error: no geometry found')
						# Select the newly moved-to feature
						if feature:
							print('feature found')
							self.selected_layer.selectByIds([feature.id()])
						else:
							print('no feature found')
					else:
						errorText='Layer has 0 Features (may still be loading?). Try again once it has features.'
						print(errorText)
						widget = iface.messageBar().createMessage(errorText)
						iface.messageBar().pushWidget(widget, Qgis.Info,duration=5)
				else:
					print('Error: Layer Not Found')

			def pan_to_location(self, point):
				print('panning to location')
				if point:
					print('point found')
					canvas = iface.mapCanvas()  # Access the QGIS map canvas
					canvas.zoomScale(1000)  # Zoom to the specified scale
					canvas.setCenter(point)  # Center the map view on the specified point
					if self.LoadedLayerExtension=='.shp':
						displayIndex=self.feature_index+1
					elif self.LoadedLayerExtension=='.gpkg':
						displayIndex=self.feature_index
					elif self.LoadedLayerExtension=='.csv':
						displayIndex=self.feature_index-1
					elif self.LoadedLayerExtension=='else':
						displayIndex=self.feature_index+1
					self.IndexEdit.setText(str(displayIndex))
					canvas.refresh()  # Refresh the canvas to update the view
				else:
					print('point NOT found')

		# Create an instance of your custom dialog
		dialog = PrevNextDialog()
		dialog.run_dialog()


	def onRunchangeWu4Rus(self):
		print("START PROCESS: Change Wu 4 Rus")
		#check if road unit layer exists
		for lyr in QgsProject.instance().layerTreeRoot().findLayers():
			if lyr.name()=="Road Unit Segment":
				ruLayerFound = True
		#if road unit layer exists
		if ruLayerFound == True:
			print("RU layer found")

			#variables
			expression=None
			fieldName = "segment_id"
			layerRU = None
			layerWu = None
			message=None
			messageType=None
			layerRU_NearbyFtrs=None

			#connection settings
			settings = QSettings('Geodigital', 'db_params_settings')
			currentConnectionName = str(settings.value('current_connection'))
			currentConnection = {}
			currentConnection = settings.value('connections')[currentConnectionName]
			username = str(settings.value('connections')[currentConnectionName]['user_name'])
			password = str(settings.value('connections')[currentConnectionName]['password'])
			databaseName = str(settings.value('connections')[currentConnectionName]['database_name'])
			hostName = str(settings.value('connections')[currentConnectionName]['server_ip'])
			port = str(settings.value('connections')[currentConnectionName]['port'])

			#store needed layers, from QGIS layers panel
			for lyr in QgsProject.instance().layerTreeRoot().findLayers():
				current_layer=QgsProject.instance().layerTreeRoot().findLayer(lyr.layerId())
				if current_layer!=None:
					if current_layer.parent()!=None:
						if current_layer.parent().parent()!=None:
							#not from Nearby Features parent group
							if current_layer.parent().parent().name()!="Nearby Features":
								if lyr.name()=="Road Unit Segment":
									layerRU = lyr.layer()
							#from Nearby Features parent group
							elif current_layer.parent().parent().name()=="Nearby Features":
								if lyr.name()=="Road Unit Segment":
									layerRU_NearbyFtrs = lyr.layer()
						elif lyr.name()=="Work Units":
							layerWu = lyr.layer()
			# Get the selected features from the layer
			selected_features = layerRU.selectedFeatures()

			# Loop through the selected features and save the features
			selected_Rus = []
			for feature in selected_features:
			    selected_Rus.append(feature)

			#show drop-down of WU_IDs to move those RUs into (taken from Work Units layer intersecting canvas)
			if len(selected_Rus)>0:
				#get wu_ids from Work Units layer whose geom intersects current viewing panel
				feats = [ feat for feat in layerWu.getFeatures() ]
				wu_ids_intersecting_view=set()
				for feat in feats:
					if feat.geometry().intersects(iface.mapCanvas().extent()):
						if str(feat['work_unit_id']) !='NULL' or feat['work_unit_id']!=None:
							wu_ids_intersecting_view.add(feat['work_unit_id'])

				#saves visibility settings
				nameOfTheme="ChangeWu4RuTool_SavedVisibilitySettings"
				theme=None
				root = QgsProject.instance().layerTreeRoot()
				OFF=0
				ON=1
				theme=QgsProject.instance().mapThemeCollection().createThemeFromCurrentState(root, QgsLayerTreeModel(root))
				QgsProject.instance().mapThemeCollection().insert(nameOfTheme,theme)

				#turns off visibility on all layers
				for lyr2 in root.findLayers():
					type=-1
					try:
						type=lyr2.layer().type()
					except:
						continue
					if type!=-1:
						if type==0:
							QgsProject.instance().layerTreeRoot().findLayer(lyr2.layerId()).setItemVisibilityChecked(OFF)

				#turns on visibility of Work Unit layer
				ltl=QgsProject.instance().layerTreeRoot().findLayer(layerWu.id())
				#turns on visibility of all sub-category rules of Work Units layer
				ltl.setItemVisibilityChecked(ON)
				ltm = iface.layerTreeView().layerTreeModel()
				legendNodes = ltm.layerLegendNodes( ltl )
				for node in legendNodes:
					node.setData( Qt.Checked, Qt.CheckStateRole)

				#set cleanup enabled for associations/disassociations. If associations is disabled, then disassociations automatically will also not disassociate
				cleanup_Enabled=True
				cleanupDisassociations_Enabled=True
				#make temporary layer, using geometry
				try:
					iface.setActiveLayer(QgsProject.instance().layerTreeRoot().children()[0].layer())
				except:
					print("Top layer is a group, not a layer. Could not load layer to top of Layers Panel")
				selectedRuTempLayerName='_RoadUnit_forWuChange'
				iface.mainWindow().blockSignals(True)
				crs_authid = iface.mapCanvas().mapSettings().destinationCrs().authid()
				my_layer = QgsVectorLayer('Polygon', selectedRuTempLayerName, 'memory')
				my_layer.setCrs(QgsCoordinateReferenceSystem(crs_authid))
				pr = my_layer.dataProvider()
				pr.addAttributes([QgsField("seg_id", QVariant.String)])
				my_layer.updateFields()

				#loop through road units
				for selected_Ru in selected_Rus:
					feature = QgsFeature(my_layer.fields())
					geom = QgsGeometry().fromWkt('GEOMETRYCOLLECTION()')
					geom = selected_Ru.geometry()
					feature.setGeometry(geom)
					feature.setAttribute("seg_id", str(selected_Ru['segment_id']))
					pr.addFeatures([feature])
				#style
				alphaOpaque=',255'
				alphaSeeThrough=',100'
				color='255,255,0'
				symbol = QgsFillSymbol.createSimple({'color': color+alphaSeeThrough,'outline_color': color+alphaOpaque, 'outline_style': 'solid', 'outline_width': '1'})
				renderer = QgsSingleSymbolRenderer(symbol)
				my_layer.triggerRepaint()
				my_layer.setRenderer(renderer)
				iface.mapCanvas().setDestinationCrs(QgsCoordinateReferenceSystem(crs_authid))
				QgsProject.instance().addMapLayer(my_layer, True)
				iface.mainWindow().blockSignals(False)

				#QInputDialog for wu_id
				qid = QInputDialog()
				title = 'Change WU_ID for RU(s)'
				label = "Select wu_id: "
				editable=False
				#sort combo box options
				items=[]
				for wus in wu_ids_intersecting_view:
					items.append(wus)
				items.sort()
				items=[str(i) for i in items]

				#for user-selected combo box dialogue
				userInputWuId, ok = QInputDialog.getItem( qid, title, label, items, editable=editable)
				print(str(userInputWuId))

				#if 'ok' button clicked in QInputDialog
				if ok:
					summary_message=''
					# loop through road unit segments
					for selected_Ru in selected_Rus:
						#run user Input CHECK against wu List
						if userInputWuId in items:
							#get info
							conn = psycopg2.connect(host=hostName, port=port, dbname=databaseName, user=username, password=password)
							cur = conn.cursor()
							sql = (f"SELECT sb.segment_id, sb.start_boundary_id, sb.end_boundary_id, sb.wu_id, sb.replaced_by_wuid, cp.crossing_id, rop.road_object_id \
								FROM road_unit.segment_boundaries sb \
								INNER JOIN road_unit.segment_paths sp on sb.segment_id = sp.segment_id \
								FULL OUTER JOIN crossing.crossings_paths cp on cp.path_id = sp.id \
								FULL OUTER JOIN road_object.road_objects_paths rop on rop.path_id = sp.id \
								where sb.segment_id={str(selected_Ru['segment_id'])} \
								group by sb.segment_id,cp.crossing_id, rop.road_object_id; ")
							cur.execute(sql)
							result = cur.fetchall()
							print(result)

							#put results into sets (efficiency, remove  duplicates)
							result_boundary_ids=set()
							result_crossing_ids=set()
							result_roadObject_ids=set()
							result_wu_ids=set()
							for row in result:
								if row[1]!=None:
									result_boundary_ids.add(row[1])
								if row[2]!=None:
									result_boundary_ids.add(row[2])
								if row[3]!=None:
									result_wu_ids.add(str(row[3]))
								if row[5]!=None:
									result_crossing_ids.add(row[5])
								if row[6]!=None:
									result_roadObject_ids.add(row[6])
							if str(userInputWuId) not in result_wu_ids:
								boundariesMoved=False
								crossingsMoved=False
								roadObjectsMoved=False
								boundariesMovedOut=False
								crossingsMovedOut=False
								roadObjectsMovedOut=False
								countAssociated_boundaries=0
								countAssociated_crossings=0
								countAssociated_roadObjects=0
								countDisassociated_boundaries=0
								countDisassociated_crossings=0
								countDisassociated_roadObjects=0
								cleanUpFailed=''

								###### Clean-up (Associations and Disassociations)######
								if cleanup_Enabled==True:
									#Progress Bar (set up)#
									#clear the message bar
									iface.messageBar().clearWidgets()
									#set a new message bar
									progressMessageBar = iface.messageBar()
									progress = QProgressBar()
									#Maximum is set to 100, making it easy to work with percentage of completion
									progress.setMaximum(100)
									#pass the progress bar to the message Bar
									progressMessageBar.pushWidget(progress)
									#Set initial percent
									progress.setValue(1)
									#make changes to database, if able
									if len(result_boundary_ids)!=0:
										print('boundaring: make changes to database, if able')
										max_count=len(result_boundary_ids)
										count=0
										progress.setValue(1)
										for boundary_id in result_boundary_ids:
											#Update the progress bar
											count+=1
											percent = (count/float(max_count)) * 100
											progress.setValue(percent)
											try:
												sql = (f"SELECT wu_id, boundary_id FROM work_units.associated_boundaries where wu_id={str(userInputWuId)} and boundary_id={str(boundary_id)} ; ")
												cur.execute(sql)
												#check_featureExists=cur.fetchall()
												count_result=0
												count_result=cur.rowcount
												#if boundary/WU combo is not already assigned, then assign it
												if count_result	==0:
													sql = (f"INSERT INTO work_units.associated_boundaries(wu_id, boundary_id) VALUES ({str(userInputWuId)}, {str(boundary_id)} ) ; ")
													cur.execute(sql)
													conn.commit()
													boundariesMoved=True
													countAssociated_boundaries+=1
													print('Success for boundary id: '+str(boundary_id))
												else:
													print('Boundary / WU combo already exists for: '+str(boundary_id))
											except Exception as e:
												cleanUpFailed+=' Boundary(ies)'
												print(e)
										try:
											#update wuid for selected RU seg
											sql = (f"Update road_unit.segment_boundaries SET wu_id ={str(userInputWuId)} WHERE segment_id={selected_Ru['segment_id']} ; ")
											cur.execute(sql)
											conn.commit()
											print('New wu_id update for road unit passed')
										except Exception as e:
											print(e)
											print('New wu_id update for road unit failed')
									if len(result_crossing_ids)!=0:
										max_count=len(result_crossing_ids)
										count=0
										progress.setValue(0)
										for crossing_id in result_crossing_ids:
											#Update the progress bar
											count+=1
											percent = (count/float(max_count)) * 100
											progress.setValue(percent)
											try:
												#check if crossing is already associated to user-defined WU
												sql = (f"SELECT wu_id, crossing_id FROM work_units.associated_crossings where wu_id={str(userInputWuId)} and crossing_id={str(crossing_id)} ; ")
												cur.execute(sql)
												count_result=0
												count_result=cur.rowcount
												#if crossing is not already associated to user-defined WU, then associate it
												if count_result	==0:
													sql = (f"INSERT INTO work_units.associated_crossings(wu_id, crossing_id) VALUES ({str(userInputWuId)}, {str(crossing_id)} ) ; ")
													cur.execute(sql)
													conn.commit()
													crossingsMoved=True
													countAssociated_crossings+=1
													print('Success for crossing id: '+str(crossing_id))
												else:
													print('Crossing / WU combo already exists for: '+str(crossing_id))

												#crossings
												if cleanupDisassociations_Enabled==True:
													#disassociate crossing from WU in associated_crossings table, if it is assigned to no other RU, other than {str(selected_Ru['segment_id'])}
													#for crossings associated to selected RU, check if that crossing is assigned to another WU but not any of that WUs segments, and disassociate that crossing from that WU
													sql = (f"SELECT ac0.wu_id FROM work_units.associated_crossings ac0 \
														where ac0.crossing_id={str(crossing_id)} \
														and ac0.wu_id not in (SELECT sb.wu_id	FROM crossing.crossings_paths cp \
														INNER JOIN road_unit.segment_paths sp on sp.id = cp.path_id \
														INNER JOIN road_unit.segment_boundaries sb on sb.segment_id=sp.segment_id \
														WHERE sb.wu_id IS NOT NULL and cp.crossing_id={str(crossing_id)}  \
														GROUP BY sb.wu_id) ; ")
													cur.execute(sql)
													count_result=0
													count_result=cur.rowcount
													print("Crossing count_result: "+str(count_result))
													if count_result	>0:
														#build set of WUs to disassociate crossing from
														result_Disassociate_WUs_ForCrossing=cur.fetchall()
														print('result_Disassociate_WUs_ForCrossing:')
														print(result_Disassociate_WUs_ForCrossing)
														SetOfWusToDisassociateFrom_Crossings=set()
														for row in result_Disassociate_WUs_ForCrossing:
															if row[0]!=None and str(row[0])!='NULL' and str(row[0])!=str(userInputWuId):
																SetOfWusToDisassociateFrom_Crossings.add(row[0])
														print('SetOfWusToDisassociateFrom_Crossings:')
														print(SetOfWusToDisassociateFrom_Crossings)
														#execute disassociation(s) from set of WUs
														for wu in SetOfWusToDisassociateFrom_Crossings:
															sql=(f"DELETE FROM work_units.associated_crossings \
															WHERE crossing_id={str(crossing_id)} and wu_id={str(wu)} ;")
															cur.execute(sql)
															conn.commit()
															crossingsMovedOut=True
															countDisassociated_crossings+=1
															print("Disassociated crossing "+str(crossing_id)+" from WU: "+str(wu))
													else:
														print("No disassociations needed/allowed for crossing: "+str(crossing_id))
											except Exception as e:
												cleanUpFailed+=' Crossing(s)'
												print(e)
									#road objects
									if len(result_roadObject_ids)!=0:
										max_count=len(result_roadObject_ids)
										count=0
										progress.setValue(0)
										for roadObject_id in result_roadObject_ids:
											#Update the progress bar
											count+=1
											percent = (count/float(max_count)) * 100
											progress.setValue(percent)
											try:
												#check if road object is already associated to user-defined WU
												sql = (f"SELECT wu_id, road_object_id FROM work_units.associated_road_objects where wu_id={str(userInputWuId)} and road_object_id={str(roadObject_id)} ; ")
												cur.execute(sql)
												#check_featureExists=cur.fetchall()
												count_result=0
												count_result=cur.rowcount
												#if road object is not already associated to user-defined WU, then associate it
												if count_result	==0:
													sql = (f"INSERT INTO work_units.associated_road_objects(wu_id, road_object_id) VALUES ({str(userInputWuId)}, {str(roadObject_id)} ) ; ")
													cur.execute(sql)
													conn.commit()
													roadObjectsMoved=True
													countAssociated_roadObjects+=1
													print('Success for road object id: '+str(roadObject_id))
												else:
													print('Road Object / WU combo already exists for: '+str(roadObject_id))
												if cleanupDisassociations_Enabled==True:
													#disassociate road object from WU in associated_road_objects table, if it is assigned to no other RU, other than {str(selected_Ru['segment_id'])}
													#for road objects associated to selected RU, check if that road object is assigned to another WU but not any of that WUs segments, and disassociate that road object from that WU
													sql = (f"SELECT aro0.wu_id FROM work_units.associated_road_objects aro0 \
														where aro0.road_object_id={str(roadObject_id)} \
														and aro0.wu_id not in (SELECT sb.wu_id	FROM road_object.road_objects_paths rop \
														INNER JOIN road_unit.segment_paths sp on sp.id = rop.path_id \
														INNER JOIN road_unit.segment_boundaries sb on sb.segment_id=sp.segment_id \
														WHERE sb.wu_id IS NOT NULL and rop.road_object_id={str(roadObject_id)}  \
														GROUP BY sb.wu_id) ; ")
													cur.execute(sql)
													count_result=0
													count_result=cur.rowcount
													print("Road Object count_result: "+str(count_result))
													if count_result	>0:
														#build set of WUs to disassociate road object from
														result_Disassociate_WUs_ForRoadObject=cur.fetchall()
														print("result_Disassociate_WUs_ForRoadObject:")
														print(result_Disassociate_WUs_ForRoadObject)
														SetOfWusToDisassociateFrom_RoadObjects=set()
														for row in result_Disassociate_WUs_ForRoadObject:
															if row[0]!=None and str(row[0])!='NULL' and str(row[0])!=str(userInputWuId):
																SetOfWusToDisassociateFrom_RoadObjects.add(row[0])
														print("SetOfWusToDisassociateFrom_RoadObjects:")
														print(SetOfWusToDisassociateFrom_RoadObjects)
														#execute disassociation(s) from set of WUs
														for wu in SetOfWusToDisassociateFrom_RoadObjects:
															sql=(f"DELETE FROM work_units.associated_road_objects \
															WHERE road_object_id={str(roadObject_id)} and wu_id={str(wu)} ;")
															cur.execute(sql)
															conn.commit()
															roadObjectsMovedOut=True
															countDisassociated_roadObjects+=1
															print("Disassociated road object "+str(roadObject_id)+" from WU: "+str(wu))
													else:
														print("No disassociations needed/allowed for road object: "+str(roadObject_id))
											except Exception as e:
												cleanUpFailed+=' Road_Object(s)'
												print(e)
									#closing connection and cursor
									cur.close()
									conn.close()

									#completion message
									layerRU.select(selected_Ru.id())
									message='COMMITTED CHANGES! Segment ' + str(selected_Ru['segment_id']) + ' now belongs to WU: ' + str(userInputWuId)
									if boundariesMoved==True or crossingsMoved==True or roadObjectsMoved==True or boundariesMovedOut==True or crossingsMovedOut==True or roadObjectsMovedOut==True:
										message+='. Cleaned Up'
										if boundariesMoved==True or crossingsMoved==True or roadObjectsMoved==True:
											message+=' - Associated:'
											if boundariesMoved==True:
												message+=' Boundaries ('+str(countAssociated_boundaries)+')'
											if crossingsMoved==True:
												message+=' Crossings ('+str(countAssociated_crossings)+')'
											if roadObjectsMoved==True:
												message+=' Road_Objects ('+str(countAssociated_roadObjects)+')'
										if boundariesMovedOut==True or crossingsMovedOut==True or roadObjectsMovedOut==True:
											message+='. Disassociated:'
											if boundariesMovedOut==True:
												message+=' Boundaries ('+str(countDisassociated_boundaries)+')'
											if crossingsMovedOut==True:
												message+=' Crossings ('+str(countDisassociated_crossings)+')'
											if roadObjectsMovedOut==True:
												message+=' Road_Objects ('+str(countDisassociated_roadObjects)+')'
									else:
										message+=". Clean-up NOT NEEDED (boundaries, crossings, and road objects found to be OK)."
									messageType= Qgis.Success
									if cleanUpFailed!='':
										messageType= Qgis.Warning
										message='WARNING: Clean-up Failed: '+cleanUpFailed + '. Perform Manually (In chosen WU, associate: boundaries, crossing(s), road objects as needed).'
								#Changes not enabled
								else:
									message='WARNING: Changes not enabled on backend'
									messageType= Qgis.Warning
							else:
								message='ALREADY DONE: RU '+str(selected_Ru['segment_id'])+ ' already in WU ' + str(selected_Ru['wu_id'])
								messageType= Qgis.Success
						else:
							message='WARNING: NOT WITHIN VIEW. Ensure WU entered is within view. Wus currently within view: '
							messageType= Qgis.Warning
							for wus in wu_ids_intersecting_view:
								message+=str(wus)+' '

						#display message, for selected RUs
						summary_message+= (str(message) + '\n' + '\n')
						print(message)

					#clear progress bar
					iface.messageBar().clearWidgets()
					#try message dialogue
					from PyQt5.QtWidgets import QMessageBox

					# Create a message box
					msg_box = QMessageBox()

					# Set the title of the message box
					msg_box.setWindowTitle("Summary: Change wu_id for selected RU(s)")

					# Set the text of the message box
					msg_box.setText(summary_message)

					# Set the standard OK button and run the message box
					msg_box.setStandardButtons(QMessageBox.Ok)
					msg_box.exec_()

				#deletes temporary layer that used geometry of selected_Ru
				for lyr in QgsProject.instance().mapLayers().values():
					if "_RoadUnit_" in lyr.name():
						QgsProject.instance().removeMapLayer(lyr)

				#restores visibility settings that were previously saved, an deletes theme used
				QgsProject.instance().mapThemeCollection().applyTheme(nameOfTheme,root, QgsLayerTreeModel(root))
				QgsProject.instance().mapThemeCollection().removeMapTheme(nameOfTheme)

			else:
				errorText='Error: No Road Units selected in Road Unit Layer'
				widget = iface.messageBar().createMessage(errorText)
				iface.messageBar().pushWidget(widget, Qgis.Warning,duration=5)

		#Error: RU layer not found
		else:
			errorText='Error: No Road Unit Layer found. May need to load RFDB plugin'
			widget = iface.messageBar().createMessage(errorText)
			iface.messageBar().pushWidget(widget, Qgis.Warning,duration=5)

	def onRunThreeDLidarViewer(self):
		print("START PROCESS: 3D Lidar Viewer")
		#define map tool for drawing line in qgis
		from qgis.gui import QgsMapTool
		from qgis.core import QgsPoint, QgsGeometry, QgsMessageLog

		#draws red line
		class DrawLineMapTool(QgsMapTool):
			def __init__(self, canvas):
				super(DrawLineMapTool, self).__init__(canvas)
				self.canvas = canvas
				self.rubber_band = QgsRubberBand(self.canvas, QgsWkbTypes.LineGeometry)
				self.rubber_band.setColor(Qt.red)
				self.rubber_band.setWidth(2)
				self.start_point = None

			def canvasPressEvent(self, event):
				self.start_point = self.toMapCoordinates(event.pos())


			def canvasMoveEvent(self, event):
				if self.start_point:
					self.rubber_band.reset(QgsWkbTypes.LineGeometry)
					self.rubber_band.addPoint(self.start_point)
					self.rubber_band.addPoint(self.toMapCoordinates(event.pos()))

			def canvasReleaseEvent(self, event):
				self.rubber_band.reset(QgsWkbTypes.LineGeometry)
				end_point = self.toMapCoordinates(event.pos())
				line = QgsGeometry.fromPolylineXY([self.start_point, end_point])
				self.start_point = None
				# remove the rubber band from the canvas
				self.rubber_band.reset()
				# change the map tool back to the default pan tool
				iface.mapCanvas().setMapTool(QgsMapToolPan(iface.mapCanvas()))
				# Open the lidar viewer
				OpenLidarViewer(line)

		#define code for displaying the lidar
		def OpenLidarViewer(line):
			"""
			Function to open the Lidar Viewer and display the line as a red arrow
			"""
			# Code to open the Lidar Viewer
			import laspy
			import csv
			import pyvista as pv
			import numpy as np
			# Input coordinates
			# 138.90302514, 35.22801117
			x = line.asPolyline()[0].x()
			y = line.asPolyline()[0].y()

			#BIX FILTER
			import os
			from qgis.core import QgsProject, QgsVectorLayer
			from qgis.utils import iface

			# check the scale of the canvas
			canvas = iface.mapCanvas()
			scale = canvas.scale()
			if scale <= 3000:
				# Get the current canvas extent
				extent = iface.mapCanvas().extent()

				#BY WORK UNITS in canvas extent, get trail names
				# Get the layer by name
				layer = QgsProject.instance().mapLayersByName("Work Units")[0]

				# Select the WUs that are within the current canvas extent
				layer.selectByRect(extent)

				# Get the selected features
				selected_features = layer.selectedFeatures()

				# Iterate over the selected features and get the work_unit_id
				work_unit_ids = [str(f["work_unit_id"]) for f in selected_features]

				# connect to the road features database
				##### connection settings to live RFDB #####
				self.settings = QSettings('Geodigital', 'db_params_settings')
				currentConnectionName = str(self.settings.value('current_connection'))
				currentConnection = {}
				currentConnection = self.settings.value('connections')[currentConnectionName]
				username = str(self.settings.value('connections')[currentConnectionName]['user_name'])
				password = str(self.settings.value('connections')[currentConnectionName]['password'])
				databaseName = str(self.settings.value('connections')[currentConnectionName]['database_name'])
				hostName = str(self.settings.value('connections')[currentConnectionName]['server_ip'])
				port = str(self.settings.value('connections')[currentConnectionName]['port'])
				##### END connection settings to live RFDB #####

				print("Connecting to database")
				conn = psycopg2.connect(host=hostName, port=port, dbname=databaseName, user=username, password=password)
				cur = conn.cursor()

				sql = ("SELECT w.subcountry \
				, pc.pc_id \
				FROM work_units.work_unit w \
				INNER JOIN work_units.wu_point_cloud pc ON pc.wu_id=w.id \
				WHERE w.id in ({} \
				) \
				GROUP BY w.subcountry, pc.pc_id \
				ORDER BY w.subcountry ASC ; ").format(str(', '.join(work_unit_ids)))

				print("Executing Query")
				cur.execute(sql)
				result = cur.fetchall()
				#closing connection and cursor
				cur.close()
				conn.close()
				result_list_FoundCoord=[]
				count=-1

				# save new results result_list_FoundCoord with also trail names and subcountries for the WUs
				for row in result:
					count+=1
					subcountry  = row[0]
					trail_name = row[1]
					# create the file path
					path_dir = "P:/CSAV3/acquisition_data/point_clouds/" + subcountry + "/" + trail_name
					previous_rows = []
					next_rows = []
					if os.path.isfile(path_dir+ ".bix")==True:
						# check if the coordinate is present in the .bix files
						with open(path_dir+".bix", newline='') as f:
							reader = csv.reader(f, delimiter=' ')
							for row in reader:
								if previous_rows:
									# Extract the bounding box coordinates, for previous row
									xmin, xmax, ymin, ymax = float(previous_rows[-1][2]), float(previous_rows[-1][3]), float(previous_rows[-1][4]), float(previous_rows[-1][5])
									# Check if the input coordinates are within the bounding box
									if xmin <= x <= xmax and ymin <= y <= ymax:
										# Extract the first and last point number in the subset
										first, last = int(previous_rows[-1][0]), int(previous_rows[-1][1])
										first_next, last_next = int(row[0]), int(row[1])
										result_list_FoundCoord.append([subcountry,trail_name,first, last,first_next, last_next,path_dir,str(str(trail_name).split('_')[1])+str(str(trail_name).split('_')[2]) ])
								previous_rows.append(row)


				#order result_list_FoundCoord by newest trail name's datetime
				print("Unsorted")
				indexOfYearDateTime=7
				print(result_list_FoundCoord)
				result_list_FoundCoord=sorted(result_list_FoundCoord, key=lambda x: x[indexOfYearDateTime], reverse=True)
				print("Sorted")
				print(result_list_FoundCoord)

				#set variables
				subcountry=result_list_FoundCoord[0][0]
				trail_name=result_list_FoundCoord[0][1]
				first=result_list_FoundCoord[0][2]
				last=result_list_FoundCoord[0][3]
				first_next=result_list_FoundCoord[0][4]
				last_next=result_list_FoundCoord[0][5]
				path_dir=result_list_FoundCoord[0][6]
				#overrides
				#path_dir="C:/Users/jgreener/Downloads/JE_220911_003630_S0"
				#path_dir="P:/CSAV3/acquisition_data/point_clouds/JPN_Chubu/JG_220609_063645_S0"
				print('\n variables'+str(subcountry)+' / '+ str(trail_name)+' / '+ str(first) +' / '+str(last)+' / ' +str(first_next) +' / '+str(last_next) +' / '+str(path_dir)+' / '+str(result_list_FoundCoord[0][7]))

				#path to your laz file
				print('about to save lax file')
				#file = laspy.read(path_dir+".laz")
				#TODO: try chunking due to memory Errors
				#Alternatively, you can try splitting the point cloud into smaller subsets manually and processing them one by one using the laspy library, as we discussed earlier.
				# Extract coordinates and intensity of each point
				file = laspy.read(path_dir+".laz")
				x_coords = file['X']
				y_coords = file['Y']
				z_coords = file['Z']
				print('got x,y,z coords from lax file')

				# Extract the selected points using the first and last point numbers, from prev row with coordinates
				selected_points = [[x_coords[i], y_coords[i], z_coords[i]] for i in range(first, last+1)]
				# Extract the selected points using the first and last point numbers, from next row
				selected_points += [[x_coords[i], y_coords[i], z_coords[i]] for i in range(first_next, last_next+1)]
				print(len(selected_points))

				# Scale factor
				scale_factor = 100000

				# Separate the x, y and z coordinates
				x_coords, y_coords, z_coords = np.array(selected_points).T

				# Scale up the x and y coordinates
				scaled_x = x_coords * scale_factor
				scaled_y = y_coords * scale_factor

				# Combine the scaled x and y coordinates with the z coordinates
				scaled_points = np.column_stack((scaled_x, scaled_y, z_coords))

				# Create a PyVista dataset
				pointcloud = pv.PolyData(scaled_points)

				# Extract the intensity values of the selected points
				intensity = file.intensity[first:last+1]
				if first_next is not None and last_next is not None:
					intensity_next = file.intensity[first_next:last_next+1]
					# Concatenate the intensity values from the next subset with the current subset
					intensity_combined = np.concatenate((intensity, intensity_next))
				# Add the intensity values as a scalar field to the point cloud dataset
				pointcloud['Intensity'] = intensity_combined

				# Create a 3D viewer and add the point cloud with the intensity scalars
				p = pv.Plotter()
				p.add_points(pointcloud, scalars='Intensity', cmap='gray', render_points_as_spheres=True)
				p.show()
				'''# Code to display the line as a red arrow
				# convert the QGIS line geometry to a numpy array
				line_array =line.asPolyline()
				#add z values to line arrays
				z_value=306 #TODO: get from bix file
				line_array = np.column_stack((line_array,np.array([z_value]*len(line_array))))
				# create a new pyvista line
				arrow = pv.PolyData(line_array)
				# set the color of the arrow to red
				arrow.plot(color='red')'''

				#END 3D Viewer
				print('Finished with loading 3D Viewer')

			#scale >3000
			else:
				# do nothing
				pass

		# Call the above-defined Map Tool function
		canvas = iface.mapCanvas()
		tool = DrawLineMapTool(canvas)
		canvas.setMapTool(tool)

		'''OLD**************************
		#get selected layers
		selectedLayers=iface.layerTreeView().selectedLayers()
		countSelectedLayers=len(selectedLayers)
		#remove any layers with '3D_Viewer_' in name
		for lyr in QgsProject.instance().layerTreeRoot().findLayers():
			if '3D_Viewer_' in lyr.name():
				QgsProject.instance().removeMapLayer(lyr.layer())
				iface.mapCanvas().refreshAllLayers()

		#must be exactly 1 layer selected
		if countSelectedLayers==1:
			nameSelectedLayer=str(selectedLayers[0].name())
			print("Selected Layer Name: "+nameSelectedLayer)
			#attempt to filter out layers selected that are not lidar layers
			if nameSelectedLayer.count('_')>=2:
				##find directory to LAZ file from variable nameSelectedLayer
				rootDir='P:/CSAV3/acquisition_data/point_clouds/'   ####assumes root directory is this P: drive location
				lazDir=None
				shpDir=None
				list_subfolders_with_paths = [f.path for f in os.scandir(rootDir) if f.is_dir()]
				for subfolderPath in list_subfolders_with_paths:
					#print(subfolderPath)
					potentialLazPath=str(subfolderPath) +"/" + nameSelectedLayer +".laz"
					potentialShpPath=str(subfolderPath) +"/" + nameSelectedLayer +".shp"
					if os.path.isfile(potentialLazPath):
						lazDir=potentialLazPath
						if os.path.isfile(potentialShpPath):
							shpDir=potentialShpPath
						print("LAZ Directory: " + str(lazDir))
						break
				#lidar LAZ and SHP directories must exist for lidar name from selected lidar layer
				if shpDir!=None and lazDir!=None:
					#make temp layer using SHP directory variable shpDir
					try:
						iface.setActiveLayer(QgsProject.instance().layerTreeRoot().children()[0].layer())
					except:
						print("Top layer is a group, not a layer. Could not load layer to top of Layers Panel")
					lidar_shp_layer = QgsVectorLayer(shpDir, "3D_Viewer_"+nameSelectedLayer, "ogr")
					pr = lidar_shp_layer.dataProvider()
					QgsProject.instance().addMapLayer(lidar_shp_layer)
					#turn on clickTool
					self.clickTool2 = QgsMapToolEmitPoint(self.iface.mapCanvas())
					self.clickTool2.canvasClicked.connect(self.view3dLidar)
					self.iface.mapCanvas().setMapTool(self.clickTool2)
				else:
					errorText='Error: No Shapefile or LAZ found for this lidar file name'
					widget = iface.messageBar().createMessage(errorText)
					iface.messageBar().pushWidget(widget, Qgis.Warning,duration=5)
			else:
				errorText=str("Error: Not exactly 1 Lidar Layer selected")
				widget = iface.messageBar().createMessage(errorText)
				iface.messageBar().pushWidget(widget, Qgis.Warning,duration=5)

		else:
			errorText=str("Error: Not exactly 1 Lidar Layer selected")
			widget = iface.messageBar().createMessage(errorText)
			iface.messageBar().pushWidget(widget, Qgis.Warning,duration=5)
		#OLD'''

	def onRunOverlapTool(self):
		print("START PROCESS: Overlap Tool")
		#find road unit segments layer, not 'nearby feature'
		layerCsav3_RuGeomsFound=False
		layerRUFound=False
		layerRU=None
		layerBoundaryPlanes=None
		layerDelins=None
		layerBoundaryPoints=None
		for lyr in QgsProject.instance().layerTreeRoot().findLayers():
			root = QgsProject.instance().layerTreeRoot()
			layer1=root.findLayer(lyr.layerId())
			#collapse groups
			layer1.setExpanded(False)
			if 'CSAV3_Ru_Geoms_' in lyr.name():
				layerCsav3_RuGeomsFound = True
				layerCsav3_RuGeoms = lyr.layer()
			elif layer1!=None:
				if layer1.parent()!=None:
					layer1.parent().setExpanded(False)
					if layer1.parent().parent()!=None:
						layer1.parent().parent().setExpanded(False)
						if layer1.parent().parent().name()!="Nearby Features":
							if lyr.name()=="Road Unit Segment":
								layerRUFound=True
								layerRU = lyr.layer()
							elif lyr.name()=="Boundary Planes":
								layerBoundaryPlanes = lyr.layer()
							elif lyr.name()=="Delineators":
								layerDelins = lyr.layer()
							elif lyr.name()=="Boundary Points":
								layerBoundaryPoints = lyr.layer()

		if layerCsav3_RuGeomsFound==False and layerRUFound==True:
			#get all 'start_boundary_point_id's from Delineators layer
			#get all 'end_boundary_point_id's from Delineators layer
			startBoundaryPointIdList=set()
			endBoundaryPointIdList=set()
			feats = [ feat for feat in layerDelins.getFeatures() ]
			for feat in feats:
				startBoundaryPointIdList.add(feat['start_boundary_point_id'])
				endBoundaryPointIdList.add(feat['end_boundary_point_id'])

			#find boundary point ids that are in 'start_boundary_point_id's but not in 'end_boundary_point_id', put in set1
			set1=set()
			for startId in startBoundaryPointIdList:
				if startId not in endBoundaryPointIdList:
					set1.add(startId)
			#find boundary point ids that are in 'end_boundary_point_id's but not in 'start_boundary_point_id', add to set1
			for endId in endBoundaryPointIdList:
				if endId not in startBoundaryPointIdList:
					set1.add(endId)
			#for each boundary point in list1, go into Boundary Points layer, and get its corresponding boundary_id, add those boundary_ids to set2
			set2=set()
			feats = [ feat for feat in layerBoundaryPoints.getFeatures() ]
			for feat in feats:
				if feat['boundary_point_id'] in set1:
					set2.add(feat['boundary_id'])
			#for all boundaries in list2, add a filter to Boundary Planes layer to only see those boundary ids
			layerBoundaryPlanes.setSubsetString('')
			if len(set2)>0:
				layerExpression = '\"boundary_id\" in ('
				for boundary in set2:
					#expressionBoundaryPlanes = layerPath.subsetString()
					layerExpression = layerExpression + str(boundary) +','
				layerExpression = layerExpression[0:-1] + ')'
				layerBoundaryPlanes.setSubsetString(layerExpression)
				print(layerExpression)
			#count number of rule categories in starting style, Road Unit Segments layer
			start_numberOfCategoriesForRuLayerStyle=0
			ltl=QgsProject.instance().layerTreeRoot().findLayer(layerRU.id())
			ltm = iface.layerTreeView().layerTreeModel()
			legendNodes = ltm.layerLegendNodes( ltl ) #QGIS 3.22 Error: 'QSortFilterProxyModel' object has no attribute 'layerLegendNodes'
			for node in legendNodes:
				start_numberOfCategoriesForRuLayerStyle+=1

			#if # sub-categories of style is not =6 (suspected of not being the overlap style, then save that style) ***COULD CAUSE ISSUES IF they use their style has exact same # of sub-categories, or if you change # of sub-categories of Overlap RU Style***
			if start_numberOfCategoriesForRuLayerStyle!=6:
				#save original styles
				pathToDEFAULTStyleFile=str(QgsApplication.qgisSettingsDirPath()+'python/plugins/qcTools/Style_Files/RoadUnitSegment_NORMAL.qml')
				layerRU.saveNamedStyle(pathToDEFAULTStyleFile)
				pathToDEFAULTStyleFile=str(QgsApplication.qgisSettingsDirPath()+'python/plugins/qcTools/Style_Files/BoundaryPlanes_NORMAL.qml')
				layerBoundaryPlanes.saveNamedStyle(pathToDEFAULTStyleFile)

			#apply style to road unit segments layer
			pathToStyleFile=str(QgsApplication.qgisSettingsDirPath()+'python/plugins/qcTools/Style_Files/RoadUnitSegment_OVERLAP.qml')
			layerRU.loadNamedStyle(pathToStyleFile)

			#apply style to boundary planes layer
			pathToStyleFile=str(QgsApplication.qgisSettingsDirPath()+'python/plugins/qcTools/Style_Files/BoundaryPlanes_DISCONNECT.qml')
			layerBoundaryPlanes.loadNamedStyle(pathToStyleFile)

			#count number of rule categories in applied style, Road Unit Segments layer
			end_numberOfCategoriesForRuLayerStyle=0
			ltl=QgsProject.instance().layerTreeRoot().findLayer(layerRU.id())
			ltm = iface.layerTreeView().layerTreeModel()
			legendNodes = ltm.layerLegendNodes( ltl )
			for node in legendNodes:
				end_numberOfCategoriesForRuLayerStyle+=1
			iface.mapCanvas().refreshAllLayers()

			#turn off visibility of certain feature groups not called 'Road Unit'
			for child1 in QgsProject.instance().layerTreeRoot().children():
				if child1.name() in ['Work Units','Work Unit Connections','2D LiDAR','OSM','Nearby Features','Work Status Errors','Mapillary Features','Pointcloud Acquisition Trail', 'Camera Images']:
					child1.setItemVisibilityChecked(False)
				elif child1.name() in ['Work Unit Features']:
					for children in child1.children():
						if children.name() in ['Crossings','Delineators','Paths','Road Objects']:
							children.setItemVisibilityChecked(False)
						elif children.name() in ['Boundaries']:
							for child in children.children():
								if child.name() in ['Boundary Planes']:
									child.setItemVisibilityChecked(True)
								elif child.name() in ['Boundary Points']:
									child.setItemVisibilityChecked(False)
						elif children.name() in ['Road Unit']:
							children.setItemVisibilityChecked(True)
							for child in children.children():
								if child.name() in ['Road Unit Segment']:
									child.setItemVisibilityChecked(True)
		elif layerCsav3_RuGeomsFound==True and layerRUFound==False:
			message = "Enabling ACQ_TRACK MODE! (For normal mode, please delete 'CSAV3_Ru_Geoms_' Layer)"
			widget5 = iface.messageBar().createMessage(message)
			iface.messageBar().pushWidget(widget5, Qgis.Success, duration=2)
		elif layerCsav3_RuGeomsFound==True and layerRUFound==True:
			message = "MODE UNCLEAR. For normal mode, please delete 'CSAV3_Ru_Geoms_' Layer. For Acq_Track Mode, turn off RFDB plugin."
			widget5 = iface.messageBar().createMessage(message)
			iface.messageBar().pushWidget(widget5, Qgis.Warning, duration=7)
		elif layerCsav3_RuGeomsFound==False and layerRUFound==False:
			message = "ERROR: LAYER NOT FOUND. No 'Road Unit Segment' layer (rfdb plugin) or 'CSAV3_Ru_Geoms_' layer (acq_track plugin) found."
			widget5 = iface.messageBar().createMessage(message)
			iface.messageBar().pushWidget(widget5, Qgis.Warning, duration=7)

		##### Activate Cross-Hairs, per Mode, for certain users ####
		#get username
		self.settings = QSettings('Geodigital', 'db_params_settings')
		currentConnectionName = str(self.settings.value('current_connection'))
		username = str(self.settings.value('connections')[currentConnectionName]['user_name'])
		#Normal Mode
		if layerRUFound==True and layerCsav3_RuGeomsFound==False:
			#turn ON overlap click tool, for certain users
			if 'ushr_' in username.lower():
				#turn on clickTool
				self.clickTool = QgsMapToolEmitPoint(self.iface.mapCanvas())
				self.clickTool.canvasClicked.connect(self.setReplacedByWuid)
				self.iface.mapCanvas().setMapTool(self.clickTool)
				'''self.clickTool = QgsMapToolEmitPoint(self.iface.mapCanvas())
				QObject.connect(self.clickTool,SIGNAL("canvasClicked(const QgsPoint &, Qt::MouseButton)"),self.setReplacedByWuid)'''
		#Acq_Track Mode
		if layerCsav3_RuGeomsFound==True and layerRUFound==False:
			#turn ON overlap click tool, for certain users
			if 'ushr_' in username.lower():
				#turn on clickTool
				self.clickTool = QgsMapToolEmitPoint(self.iface.mapCanvas())
				self.clickTool.canvasClicked.connect(self.setReplacedByWuid)
				self.iface.mapCanvas().setMapTool(self.clickTool)

		##### Visibility #####
		#for NORMAL MODE only: reset style and visibility, if tool is found to be on already
		if layerRUFound==True and layerCsav3_RuGeomsFound==False:
			if start_numberOfCategoriesForRuLayerStyle==end_numberOfCategoriesForRuLayerStyle:
				#reset boundary filter
				layerBoundaryPlanes.setSubsetString('')
				#reset style to road unit segments layer
				pathToStyleFile=str(QgsApplication.qgisSettingsDirPath()+'python/plugins/qcTools/Style_Files/RoadUnitSegment_NORMAL.qml')
				layerRU.loadNamedStyle(pathToStyleFile)
				#reset style to boundary planes layer
				pathToStyleFile=str(QgsApplication.qgisSettingsDirPath()+'python/plugins/qcTools/Style_Files/BoundaryPlanes_NORMAL.qml')
				layerBoundaryPlanes.loadNamedStyle(pathToStyleFile)
				iface.mapCanvas().refreshAllLayers()
				for child1 in QgsProject.instance().layerTreeRoot().children():
					if child1.name() in ['Work Unit Features']:
						for children in child1.children():
							if children.name() in ['Boundaries','Delineators','Paths','Road Objects','Road Unit', 'Crossings']:
								children.setItemVisibilityChecked(True)
							if children.name() in ['Boundaries']:
								for child in children.children():
									child.setItemVisibilityChecked(True)

	def onRun_Load_AdministrativeBoundaries_Shapefile(self):
		exists_Administrative_Boundaries_Layer=False
		#check if Administrative_Boundaries layer exists
		for lyr in QgsProject.instance().mapLayers().values():
			if "Administrative_Boundaries" in lyr.name():
				exists_Administrative_Boundaries_Layer=True
		if exists_Administrative_Boundaries_Layer==False:
			#try to set active layer to top
			try:
				iface.setActiveLayer(QgsProject.instance().layerTreeRoot().children()[0].layer())
			except:
				print("Top layer is a group, not a layer. Could not load layer to top of Layers Panel")
			#load layer
			layer3 = QgsVectorLayer(QgsApplication.qgisSettingsDirPath()+"python/plugins/qcTools/Administrative_Boundaries/Administrative_Boundaries.shp", "Administrative_Boundaries", "ogr")
			pr3 = layer3.dataProvider()
			QgsProject.instance().addMapLayer(layer3)
		elif exists_Administrative_Boundaries_Layer==True:
			#delete layer
			for lyr in QgsProject.instance().mapLayers().values():
				if "Administrative_Boundaries" in lyr.name():
					QgsProject.instance().removeMapLayer(lyr)
		iface.mapCanvas().refreshAllLayers()

	def onRunApplyStylesWithMatchingNames(self):
		#from qgis.utils import iface
		#from qgis.core import (QgsProject)
		import getpass
		from os import listdir
		from os.path import isfile, join
		userProfile=getpass.getuser()
		pathStyleFiles='C:/Users/'+userProfile+'/Documents/QGIS/Style Files/'
		extensionStyleFile='.qml'
		onlyfiles = [f for f in listdir(pathStyleFiles) if isfile(join(pathStyleFiles, f))]
		root=QgsProject.instance().layerTreeRoot()
		for lyr in root.findLayers():
			filename=''
			if lyr.layer()!=None:
				####special CSAV2 cases
				if 'ATD' in  lyr.layer().name():
					lyr.layer().loadNamedStyle(pathStyleFiles + 'ATD Traj.qml')
					#apply styles if name of a styleFile in dir has is contained within QGIS layer name
					#i.e. 'lane_split_or_merge.qml' would load for 'USA_Mississippi_2406-2338_lane_split_or_merge' layer because styleFile name is in layer name
				for file in onlyfiles:
					#only look for .qmls, or whatever the file extension is
					if file.split(".")[-1] == extensionStyleFile.split(".")[-1]:
						filename=file.split(".")[0]
						if filename in lyr.layer().name():
							lyr.layer().loadNamedStyle(pathStyleFiles + filename + extensionStyleFile)

				####special CSAV3 cases
				lyr.layer().loadNamedStyle(pathStyleFiles + 'RFDB_' + lyr.layer().name() + extensionStyleFile)

				####layer panel name = name in StyleFile directory
				lyr.layer().loadNamedStyle(pathStyleFiles + lyr.layer().name() + extensionStyleFile)

		#refresh
		iface.mapCanvas().refreshAllLayers()

	def onRunRemoveSelection(self):
		root=QgsProject.instance().layerTreeRoot()
		for lyr in root.findLayers():
			try:
				lyr.layer().removeSelection()
			except:
				continue


	def WU_Seg_Sync_CSAV3_Info(self):

		####Uses state of sea2sea_segments layer. If that doesn't exist, then script defaults to string below in Line 5####
		state='USA_NewYork'     ####e.g. 'USA_NewYork'

		### DO NOT CHANGE BELOW ####
		existingLayer=None
		s2s_segments_layer=None
		s2s_segments_layer_State=None

		#try to find state from s2s segments, if it is open in qgis
		try:
			s2s_segments_layer = QgsProject.instance().mapLayersByName('sea2sea_segments')[0]
			s2s_segments_layer_Source = s2s_segments_layer.dataProvider().dataSourceUri()
			s2s_segments_layer_State = s2s_segments_layer_Source.split(' ')[0].split('/')[-1][0:-4]
			#print(s2s_segments_layer_State)
		except:
			print("No 'sea2sea_segments' layer found. Loading state from Line 5 of code: " + state)

		#if state found from s2s segments layer, then set it as state. Otherwise, continue to use state from Line 5
		if s2s_segments_layer_State!=None:
			state=s2s_segments_layer_State
		print(state)

		#set layer name
		layerName='CSAV3_Info_'+state
		'''
		##### connection settings to local host #####
		currentConnection = '127.0.0.1'
		username = 'postgres'
		password = 'Passw0rd!'
		databaseName = 'road_features'
		hostName = 'localhost'
		port = '5432'
		##### END connection settings to local host #####

		'''
		##### connection settings to live RFDB #####
		self.settings = QSettings('Geodigital', 'db_params_settings')
		currentConnectionName = str(self.settings.value('current_connection'))
		currentConnection = {}
		currentConnection = self.settings.value('connections')[currentConnectionName]
		username = str(self.settings.value('connections')[currentConnectionName]['user_name'])
		password = str(self.settings.value('connections')[currentConnectionName]['password'])
		databaseName = str(self.settings.value('connections')[currentConnectionName]['database_name'])
		hostName = str(self.settings.value('connections')[currentConnectionName]['server_ip'])
		port = str(self.settings.value('connections')[currentConnectionName]['port'])
		##### END connection settings to live RFDB #####


		print("Connecting to database")
		conn = psycopg2.connect(host=hostName, port=port, dbname=databaseName, user=username, password=password)
		cur = conn.cursor()

		sql = ("SELECT w.subcountry \
		, w.id  \
		, sp.segment_id  \
		, p.id  \
		, st_astext(p.envelope) \
		, rtn.road_type_name \
		FROM path.paths p \
		INNER JOIN road_unit.segment_paths sp ON sp.id = p.id \
		INNER JOIN road_unit.segments s ON s.id = sp.segment_id \
		INNER JOIN road_unit.road_type_names rtn ON rtn.id = s.road_type_id \
		INNER JOIN delineator.delineators d ON p.left_delineator_id = d.id \
		INNER JOIN boundary.boundary_points bp ON d.start_boundary_point_id = bp.id \
		FULL OUTER JOIN work_units.associated_boundaries ab ON bp.boundary_id = ab.boundary_id  \
		FULL OUTER JOIN work_units.work_unit w ON ab.wu_id = w.id \
		INNER JOIN boundary.boundary_points bp2 ON d.end_boundary_point_id = bp2.id \
		FULL OUTER JOIN work_units.associated_boundaries ab2 ON bp2.boundary_id = ab2.boundary_id  \
		FULL OUTER JOIN work_units.work_unit w2 ON ab2.wu_id = w2.id \
		WHERE w.subcountry = '{}'  \
		AND w.id = w2.id \
		AND ST_isValid(ST_GeomFromText(ST_AsText(p.envelope)))  --avoids paths that self-intersect \
		GROUP BY \
		w.subcountry \
		, w.id \
		, sp.segment_id\
		, p.id \
		, rtn.road_type_name ; ").format(str(state))

		print("Executing Query")
		cur.execute(sql)
		result = cur.fetchall()
		#closing connection and cursor
		cur.close()
		conn.close()

		print("Creating Layer")
		# create layer
		vl = QgsVectorLayer("Polygon", layerName, "memory")
		pr = vl.dataProvider()

		# Enter editing mode
		vl.startEditing()

		# add fields
		pr.addAttributes( [ QgsField("Subcountry", QVariant.String),
						QgsField("wu_id",  QVariant.Int),
						QgsField("RU_id", QVariant.Int),
						QgsField("Path_ID", QVariant.Int)
						, QgsField("Road_Type", QVariant.String)
						, QgsField("Notes", QVariant.String, len=100)
						] )

		for rowFromResult in result:
			# add a feature
			fet = QgsFeature()
			fet.setAttributes([rowFromResult[0], rowFromResult[1], rowFromResult[2], rowFromResult[3], rowFromResult[5]])
			coordinates=None
			coordinates=str(rowFromResult[4])[9:-2].split(',')
			coordinates = [c.split(' ') for c in coordinates]
			coordinates2=[]
			for coordLists in coordinates:
				coordinates2.append( QgsPointXY(   float(coordLists[0])   ,float(coordLists[1])   )   )
			coordinates3=[]
			coordinates3.append(coordinates2)
			fet.setGeometry( QgsGeometry.fromPolygonXY(coordinates3 ))
			pr.addFeatures( [ fet ] )

		# Commit changes
		vl.commitChanges()
		QgsProject.instance().addMapLayer(vl)

		#layer settings
		layer_settings  = QgsPalLayerSettings()
		text_format = QgsTextFormat()
		text_format.setFont(QFont("Arial", 10))
		text_format.setSize(10)
		text_format.setColor(QColor("white"))
		background_color = QgsTextBackgroundSettings()
		background_color.setFillColor(QColor('black'))
		background_color.setEnabled(True)
		text_format.setBackground(background_color)
		layer_settings.setFormat(text_format)
		layer_settings.fieldName = "wu_id"
		layer_settings.placement = 2
		layer_settings.enabled = True
		layer_settings = QgsVectorLayerSimpleLabeling(layer_settings)
		#vl.setScaleBasedVisibility(True)
		#vl.setMinimumScale(5000)
		#vl.setMaximumScale(0)
		vl.setLabelsEnabled(False)
		vl.setLabeling(layer_settings)
		vl.triggerRepaint()
		print('COMPLETE')


	def onRunWorkUnitFinder(self):
		'''Finds feature then goes there and makes necessary selections'''
		dropDown_ftr_type = str(self.dropDownMenu.currentText())
		if dropDown_ftr_type == "Ru Geoms in State:":
			print("START PROCESS: Ru Geoms in State")

			####Uses state of sea2sea_segments layer. If that doesn't exist, then script defaults to string below in Line 5####
			state=self.textbox.text().lstrip().rstrip()     ####e.g. 'USA_NewYork'
			if '_' not in str(state):
				#error
				errorMessage = 'No underscore found. Please use correct format (i.e. USA_NewYork)'
				widget5 = iface.messageBar().createMessage(errorMessage)
				iface.messageBar().pushWidget(widget5, Qgis.Warning, duration=7)
			else:
				### DO NOT CHANGE BELOW ####
				print(state)
				existingLayer=None

				#####Progress Bar (set up)#####
				#clear the message bar
				iface.messageBar().clearWidgets()
				#set a new message bar
				progressMessageBar = iface.messageBar()
				progress = QProgressBar()
				#Maximum is set to 100, making it easy to work with percentage of completion
				progress.setMaximum(100)
				#pass the progress bar to the message Bar
				progressMessageBar.pushWidget(progress)
				#Set initial percent
				progress.setValue(1)

				#set layer name
				layerName='CSAV3_Ru_Geoms_'+state
				'''
				##### connection settings to local host #####
				currentConnection = '127.0.0.1'
				username = 'postgres'
				password = 'Passw0rd!'
				databaseName = 'road_features'
				hostName = 'localhost'
				port = '5432'
				##### END connection settings to local host #####

				'''
				##### connection settings to live RFDB #####
				self.settings = QSettings('Geodigital', 'db_params_settings')
				currentConnectionName = str(self.settings.value('current_connection'))
				currentConnection = {}
				currentConnection = self.settings.value('connections')[currentConnectionName]
				username = str(self.settings.value('connections')[currentConnectionName]['user_name'])
				password = str(self.settings.value('connections')[currentConnectionName]['password'])
				databaseName = str(self.settings.value('connections')[currentConnectionName]['database_name'])
				hostName = str(self.settings.value('connections')[currentConnectionName]['server_ip'])
				port = str(self.settings.value('connections')[currentConnectionName]['port'])
				##### END connection settings to live RFDB #####

				print("Connecting to database")
				conn = psycopg2.connect(host=hostName, port=port, dbname=databaseName, user=username, password=password)
				cur = conn.cursor()

				sql = ("SELECT w.subcountry, sb.wu_id, sb.segment_id, sb.start_boundary_id, sb.end_boundary_id,  sb.replaced_by_wuid, st_astext(st_union(st_astext(p.envelope))), rtn.road_type_name \
					FROM road_unit.segment_boundaries sb \
					INNER JOIN road_unit.segment_paths sp ON sp.segment_id = sb.segment_id \
					INNER JOIN path.paths p on p.id = sp.id \
					INNER JOIN work_units.work_unit w on w.id = sb.wu_id \
					FULL OUTER JOIN road_unit.segments s on s.id=sb.segment_id \
					FULL OUTER JOIN road_unit.road_type_names rtn on rtn.id=s.road_type_id \
					WHERE w.subcountry in ('{}') \
					AND ST_isValid(ST_GeomFromText(ST_AsText(p.envelope))) \
					AND sb.replaced_by_wuid IS NULL\
					GROUP BY w.subcountry,sb.wu_id, sb.segment_id, rtn.road_type_name ; ").format(str(state))

				print("Executing Query")
				cur.execute(sql)
				result = cur.fetchall()
				count_result=0
				count_result=cur.rowcount
				#closing connection and cursor
				cur.close()
				conn.close()
				#progress.setValue(2)
				if count_result==0:
					#clear progress bar
					iface.messageBar().clearWidgets()
					#error
					errorMessage = 'No rows found. Please ensure correct name (i.e. USA_NewYork). XTRAs not supported at this time.'
					widget5 = iface.messageBar().createMessage(errorMessage)
					iface.messageBar().pushWidget(widget5, Qgis.Warning, duration=7)
				else:

					print("Creating Layer")
					# create layer
					vl = QgsVectorLayer("Polygon", layerName, "memory")
					pr = vl.dataProvider()

					# Enter editing mode
					vl.startEditing()

					# add fields
					pr.addAttributes( [ QgsField("subcountry", QVariant.String),
									QgsField("wuid",  QVariant.Int),
									QgsField("segment_id", QVariant.Int),
									QgsField("start_boundary", QVariant.Int)
									, QgsField("end_boundary", QVariant.Int)
									, QgsField("replaced_by_wuid", QVariant.Int)
									, QgsField("road_type", QVariant.String)
									, QgsField("Notes", QVariant.String, len=100)
									] )
					count=0
					for rowFromResult in result:
						count+=1
						#Update the progress bar
						if count==1 or count==count_result or count % 10000 == 0:
							percent = (count/float(count_result)) * 100
							progress.setValue(percent)
						# add a feature
						fet = QgsFeature()
						fet.setAttributes([rowFromResult[0], rowFromResult[1], rowFromResult[2], rowFromResult[3], rowFromResult[4],rowFromResult[5],rowFromResult[7]])
						fet.setGeometry( QgsGeometry.fromWkt(rowFromResult[6] ))
						pr.addFeatures( [ fet ] )

					# Commit changes
					vl.commitChanges()
					QgsProject.instance().addMapLayer(vl)

					#apply style to road unit segments layer
					pathToStyleFile=str(QgsApplication.qgisSettingsDirPath()+'python/plugins/qcTools/Style_Files/CSAV3_Ru_Geoms.qml')
					vl.loadNamedStyle(pathToStyleFile)
					vl.triggerRepaint()

			print('COMPLETE')

		elif dropDown_ftr_type == "Random RUs from WU List:":
			print('starting Random RUs from WU csv')
			wuListFilePath=""
			downloads_path = str(Path.home() / "Downloads")
			wuListFilePath = str(QFileDialog.getOpenFileName(iface.mainWindow(), "Choose CSV WU List to Run", downloads_path ,filter = "Excel (*.csv *.xlsx)")[0])
			wuHeaderFound=False
			csvFound=False
			ExcelFound=False
			if wuListFilePath!="":
				with open(wuListFilePath, 'r') as file:
					#go through WU List csv and get list of WUs and save list
					wu_list=[]
					str_wu_list=''
					try:
						df = pd.ExcelFile(wuListFilePath) #you could add index_col=0 if there's an index
						ExcelFound=True
						print('Excel Found')
					except:
						try:
							df = pd.read_csv(wuListFilePath)
							csvFound=True
							print('CSV Found')
						except:
							print('Error: No CSV or Excel Found')
					#get sheet names and get first sheet name that is not called 'summary'. Sheet name not needed for CSVs
					if csvFound==False and ExcelFound==True:
						sheetNames=df.sheet_names
						sheetName=''
						for s in sheetNames:
							if 'summary' not in str(s).lower():
								sheetName=str(s)
								break
						df = pd.ExcelFile(wuListFilePath).parse(sheetName) #you could add index_col=0 if there's an index
					#get column header for WU_Ids, from csv or excel sheet
					if csvFound==True or ExcelFound==True:
						columnName=''
						headers=list(df.columns.values)
						for h in headers:
							if 'work unit' in str(h).lower() or 'wu' in str(h).lower() or 'work_unit' in str(h).lower():
								columnName=str(h)
								wuHeaderFound=True
								break
						if wuHeaderFound==False:
							errorMessage4 = "No column header found with WU, Work Unit, or Work_Unit in name. Make sure headers are in 1st row, and spelling is ok"
							widget5 = iface.messageBar().createMessage(errorMessage4)
							iface.messageBar().pushWidget(widget5, Qgis.Warning, duration=0)
						else:
							wu_list.append(df[columnName].tolist())
							for wu in wu_list[0]:
								try:
									str_wu_list=str_wu_list+str(int(wu))+','
								except:
									print('cannot convert this row to WU int: ' + str(wu))
							str_wu_list=str_wu_list[0:-1]
							print('string wu list:')
							print(str_wu_list)
					else:
						errorMessage4 = "No CSV or Excel file found."
						widget5 = iface.messageBar().createMessage(errorMessage4)
						iface.messageBar().pushWidget(widget5, Qgis.Warning, duration=0)
				if (csvFound==True or ExcelFound==True) and wuHeaderFound==True:
					#run query
					##### connection settings to live RFDB #####
					iface.settings = QSettings('Geodigital', 'db_params_settings')
					currentConnectionName = str(iface.settings.value('current_connection'))
					currentConnection = {}
					currentConnection = iface.settings.value('connections')[currentConnectionName]
					username = str(iface.settings.value('connections')[currentConnectionName]['user_name'])
					password = str(iface.settings.value('connections')[currentConnectionName]['password'])
					databaseName = str(iface.settings.value('connections')[currentConnectionName]['database_name'])
					hostName = str(iface.settings.value('connections')[currentConnectionName]['server_ip'])
					port = str(iface.settings.value('connections')[currentConnectionName]['port'])
					##### END connection settings to live RFDB #####
					message=''

					conn = psycopg2.connect(host=hostName, port=port, dbname=databaseName, user=username, password=password)
					cur = conn.cursor()
					#counts: query that gets the total number of RUs from list of WUs
					ruCountColumn=0
					sql = ("""
					SELECT count(sb.segment_id) \
					FROM road_unit.segment_boundaries sb \
					INNER JOIN road_unit.segments segs ON sb.segment_id = segs.id \
					INNER JOIN road_unit.road_type_names ruType ON segs.road_type_id = ruType.id \
					LEFT JOIN road_unit.segment_envelopes se ON se.segment_id =  sb.segment_id\
					WHERE sb.replaced_by_wuid IS NULL \
						AND se.envelope IS NOT NULL \
						AND sb.start_boundary_id IS NOT NULL \
						AND sb.end_boundary_id IS NOT NULL \
						AND sb.wu_id IS NOT NULL \
					AND sb.wu_id in ({})
					;""").format(str_wu_list)

					cur.execute(sql)
					result = cur.fetchall()
					cur.close()
					conn.close()
					countRus_In_WuList=0
					sampleCount_randomRuCount=0
					for results in result:
						countRus_In_WuList = results[ruCountColumn]
					if countRus_In_WuList>0:
						#use countRus_In_WuList variable to look up in ansi table how many random segments are needed
						#ANSI TABLE lookup
						p=countRus_In_WuList
						s=1
						if p >= 2 and p <= 8 :
							s = 2
						elif p >=9  and p <=  15:
							s =3
						elif p >=16  and p <= 25 :
							s =5
						elif p >=26  and p <= 50 :
							s =8
						elif p >=51  and p <=  90:
							s =13
						elif p >=91  and p <= 150 :
							s =20
						elif p >=151  and p <= 280 :
							s =32
						elif p >=281  and p <= 500 :
							s =50
						elif p >=501  and p <= 1200 :
							s =80
						elif p >=1201  and p <= 3200 :
							s =125
						elif p >=3200  and p <= 10000 :
							s =200
						elif p >=10001  and p <= 35000 :
							s =315
						elif p >=35000  and p <= 150000 :
							s =500
						elif p >=150001  and p <= 500000 :
							s =800
						elif p >=500001:
							s =1250
						sampleCount_randomRuCount=s
						errorMessage4 = "WUs Found in Excel Sheet: "+str(len(wu_list[0]))+" | ANSI Sample Size: " +str(sampleCount_randomRuCount) + " RUs | Total # RUs in WU List: " + str(countRus_In_WuList)
						widget5 = iface.messageBar().createMessage(errorMessage4)
						iface.messageBar().pushWidget(widget5, Qgis.Success, duration=0)

						#run query to get list of specific Road Units, random, from WU_list, count = sampleCount_randomRuCount
						conn = psycopg2.connect(host=hostName, port=port, dbname=databaseName, user=username, password=password)
						cur = conn.cursor()
						#query column header numbers
						subcountry=0
						wu_id=1
						segment_id=2
						geom=59
						#query
						sql = ("""
						SELECT w.subcountry, sb.wu_id,sb.segment_id,'' as "Technician",'' as "Notes",  \
						'' as "Boundary Plane MISSING",\
						'' as "Boundary Plane PRESENCE",\
						'' as "Boundary Plane ACCURACY",\
						'' as "Boundary Plane CONNECTIONS",\
						'' as "Boundary Plane WUC CONNECTIONS",\
						'' as "Boundary Point MISSING",\
						'' as "Boundary Point PRESENCE",\
						'' as "Boundary Point ACCURACY",\
						'' as "Road Unit TYPE",\
						'' as "Road Unit NAME",\
						'' as "Road Unit PROJECT CODE",\
						'' as "Road Unit SUSPECT GEOMETRY",\
						'' as "Delineator MISSING",\
						'' as "Delineator PRESENCE",\
						'' as "Delineator ACCURACY",\
						'' as "Delineator HEADING",\
						'' as "Delineator CONNECTION",\
						'' as "Delineator MAIN TYPE: Road Edge or Lane Line",\
						'' as "Delineator TYPE Start Type at Boundary",\
						'' as "Delineator TYPE CHANGE POINTS",\
						'' as "Delineator ATTRIBUTES (color, width, SOP, ect.",\
						'' as "Path MISSING ",\
						'' as "Path PRESENCE ",\
						'' as "Path ACCURACY",\
						'' as "Path SPLIT ",\
						'' as "Path MERGE",\
						'' as "Path TYPE (drivable/ non-drivable)",\
						'' as "Path ATTRIBUTE Start Type at Boundary",\
						'' as "Path TYPE CHANGE POINTS",\
						'' as "Speed Limit TYPE ",\
						'' as "Speed Limit VALUE",\
						'' as "Speed Limit TYPE CHANGES",\
						'' as "Path Crossing MISSING",\
						'' as "Path Crossing PRESENCE",\
						'' as "Path Crossing TYPE",\
						'' as "Path Crossing ACCURACY",\
						'' as "Path Crossing ASSOCIATION",\
						'' as "Pavement Marking MISSING",\
						'' as "Pavement Marking PRESENCE",\
						'' as "Pavement Marking TYPE ",\
						'' as "Pavement Marking ACCURACY",\
						'' as "Pavement Marking ASSOCIATION",\
						'' as "Regulatory Traffic Device MISSING",\
						'' as "Regulatory Traffic Device PRESENCE",\
						'' as "Regulatory Traffic Device TYPE",\
						'' as "Regulatory Traffic Device ACCURACY",\
						'' as "Regulatory Traffic Device ASSOCIATION",\
						'' as "Regulatory Traffic Device APPLY POSITION",\
						'' as "SILOC feature MISSING",\
						'' as "SILOC feature PRESENCE",\
						'' as "SILOC feature TYPE",\
						'' as "SILOC feature ACCURACY",\
						'' as "SILOC feature ASSOCIATION",\
						'' as "SILOC feature APPLY POSITION",\
						 st_astext(se.envelope) as "RU_geom" \
						FROM road_unit.segment_boundaries sb \
						INNER JOIN road_unit.segments segs ON sb.segment_id = segs.id \
						INNER JOIN road_unit.road_type_names ruType ON segs.road_type_id = ruType.id \
						LEFT JOIN road_unit.segment_envelopes se ON se.segment_id =  sb.segment_id\
						LEFT JOIN work_units.work_unit w ON w.id = sb.wu_id
						WHERE sb.replaced_by_wuid IS NULL \
							AND se.envelope IS NOT NULL \
							AND sb.start_boundary_id IS NOT NULL \
							AND sb.end_boundary_id IS NOT NULL \
							AND sb.wu_id IS NOT NULL \
						AND sb.wu_id in ({})
						ORDER BY RANDOM()
						LIMIT {}
						;""").format(str_wu_list, str(sampleCount_randomRuCount))
						cur.execute(sql)
						result = cur.fetchall()
						#sort result by subcountry and wu_id
						mul_sort = sorted(result, key=lambda t: (t[subcountry], t[wu_id]))
						#print("Multiple elements sorted",mul_sort)
						result=mul_sort
						rows=len(result)
						headers=[]
						for items in cur.description:
							headers.append(str(items.name))
						cur.close()
						conn.close()
						ansiRuList=[]
						for results in result:
							ansiRuList.append(results[segment_id])

						#output ansiRuList to csv, save csv to downloads_path
						#filename
						resultsSavePath_Base=str(QgsApplication.qgisSettingsDirPath())
						dateTimeObj = datetime.now()
						timestampStr = dateTimeObj.strftime("%Y%m%d-%H%M%S")
						cutPos=resultsSavePath_Base.find('Roaming')

						#create folder here: resultsSavePath_Base[0:cutPos]+'Local/Ushr/reports/'#+timestampStr+'/'
						resultsSavePath_Base=resultsSavePath_Base[0:cutPos]+'Local/Ushr/reports/RandomRus_FromWuList_'+timestampStr+'/'
						#create new folder, if not exists
						# Check whether the specified path exists or not
						isExist = os.path.exists(resultsSavePath_Base)
						if not isExist:
							# Create a new directory because it does not exist
							os.makedirs(resultsSavePath_Base)
							print("The new directory is created!")

						######MASTER csv, write results to CSV########
						#save Path
						sqlScriptName=wuListFilePath.split('/')[-1].split('.')[0]
						filename='MASTER_'+sqlScriptName+'_'+timestampStr+'_count'+str(rows)
						resultsSavePath=resultsSavePath_Base+filename+'.csv'
						try:
							with open(resultsSavePath, 'w', newline='') as csvfile:
								spamwriter = csv.writer(csvfile, delimiter=',',quotechar='\"', quoting=csv.QUOTE_MINIMAL)
								spamwriter.writerow(headers)
								spamwriter.writerows(result)
							message+= ' / Saved Results to: ' + resultsSavePath
							#delete row with polygon geoms at geom=59 (maybe + or - 1 row lol from 59)
							df=pd.read_csv(resultsSavePath)
							df.drop('RU_geom', axis = 1, inplace = True)
							df.to_csv(resultsSavePath, index = False)
							#transpose Master csv (swap rows and columns)
							pd.read_csv(resultsSavePath, header=None).T.to_csv(resultsSavePath, header=False, index=False)
							#convert Master csv to Excel
							read_file = pd.read_csv(resultsSavePath)
							read_file.to_excel (resultsSavePath_Base+filename+'.xlsx', index = None, header=True)
							#formatting Master Excel file
							#format column widths to fit data
							excel = Dispatch('Excel.Application')
							wb = excel.Workbooks.Open(resultsSavePath_Base+filename+'.xlsx')
							excel.Worksheets(1).Activate()
							excel.ActiveSheet.Columns.AutoFit()
							excel.Cells.Range("B4").Select() #freeze rows/column above/left of a cell
							excel.ActiveWorkbook.Windows(1).FreezePanes = True
							wb.Save()
							wb.Close()

							## If csv exists (which it should) delete it ##
							if os.path.isfile(resultsSavePath):
								os.remove(resultsSavePath)
							else:    ## Show an error ##
								print("Error: %s file not found" % resultsSavePath)
							#refresh save folder
							try:
								path = os.path.realpath(resultsSavePath_Base)
								os.startfile(path)
							except:
								message+= ' / Failed to Open Save Folder'
						except:
							message+= ' / Failed to Save Results'

						######make Master Shapefile#######
						#load layer template
						layer4 = QgsVectorLayer(QgsApplication.qgisSettingsDirPath()+"python/plugins/qcTools/Templates/Template_RandomRU_polygon.shp", "Template_RandomRU_polygon", "ogr")
						pr4 = layer4.dataProvider()
						QgsProject.instance().addMapLayer(layer4)
						#export template layer to shapefile at location
						_writer = QgsVectorFileWriter.writeAsVectorFormat(layer4,resultsSavePath_Base+'MASTER_SHP_'+timestampStr+'_count'+str(rows)+'.shp',"utf-8",driverName="ESRI Shapefile")
						#export template style file to same location
						layer4.saveNamedStyle(resultsSavePath_Base+'MASTER_SHP_'+timestampStr+'_count'+str(rows)+'.qml')
						#remove template
						QgsProject.instance().removeMapLayers( [layer4.id()] )
						#load newly created shapefile (non-template)
						layer3 = QgsVectorLayer(resultsSavePath_Base+'MASTER_SHP_'+timestampStr+'_count'+str(rows)+'.shp', 'MASTER_SHP_'+timestampStr+'_count'+str(rows), "ogr")
						pr3 = layer3.dataProvider()
						QgsProject.instance().addMapLayer(layer3)
						fields = layer3.fields()
						for results in result:
							# add a feature
							fet = QgsFeature()
							fet.setFields(fields)
							fet.setGeometry(QgsGeometry.fromWkt(str(results[geom])))
							fet['subcountry']=results[subcountry]
							fet['wu_id']=results[wu_id]
							fet['ru_id']=results[segment_id]
							pr3.addFeatures([fet])
							layer3.commitChanges()
						#remove master shapefile layer from qgis
						QgsProject.instance().removeMapLayers( [layer3.id()] )

						#######CSVs for each QC Tech, for work management, if a number between 2-9 is inputted into text field
						#get text from textbox
						saveName='Group'
						csvCount = self.textbox.text().strip()
						#check if string is digit
						if csvCount.isdigit() == True and int(csvCount) in [2,3,4,5,6,7,8,9]:
							print('Will create number of CSVs: ' + str(csvCount))
							#for each csvCount, create a csv
							counter=1
							for i in range(0,int(csvCount)):
								#break apart results into group, per csvCount and counter
								rusPerSHP=len(result)/int(csvCount)
								max=counter*rusPerSHP-1
								min=(counter*rusPerSHP)-rusPerSHP
								print('rusPerSHP: ' + str(rusPerSHP))
								print('min: ' + str(min))
								print('max: ' + str(max))
								#add rows/features to shapefile using results from query
								#for results in result[int(min):int(max)+1]: #if csvCount=4, then rusPerSHP=50 when len(result)=200. For counter=1, the range should be 0-49. For counter=2, the range would be 51-100
								#add rows to each csv
								#save Path
								filename=saveName+str(counter)+'_Rus_'+timestampStr
								resultsSavePath=resultsSavePath_Base+filename+'.csv'
								try:
									with open(resultsSavePath, 'w', newline='') as csvfile: #str(QgsApplication.qgisSettingsDirPath()) find AppData and
										spamwriter = csv.writer(csvfile, delimiter=',',quotechar='\"', quoting=csv.QUOTE_MINIMAL)
										spamwriter.writerow(headers)
										spamwriter.writerows(result[int(min):int(max)+1])
									message+= ' / Saved Results to: ' + resultsSavePath
									#delete row with polygon geoms at geom=59 (maybe + or - 1 row lol from 59)
									df=pd.read_csv(resultsSavePath)
									df.drop('RU_geom', axis = 1, inplace = True)
									df.to_csv(resultsSavePath, index = False)
									#transpose csv (swap rows and columns)
									pd.read_csv(resultsSavePath, header=None).T.to_csv(resultsSavePath, header=False, index=False)
									#convert csv to Excel
									read_file = pd.read_csv (resultsSavePath)
									read_file.to_excel (resultsSavePath_Base+filename+'.xlsx', index = None, header=True)
									#TODO: formatting Excel file (pretty much copy from Master Excel file formatting)
									#format column widths to fit data
									excel = Dispatch('Excel.Application')
									wb = excel.Workbooks.Open(resultsSavePath_Base+filename+'.xlsx')
									excel.Worksheets(1).Activate()
									excel.ActiveSheet.Columns.AutoFit()
									excel.Cells.Range("B4").Select() #freeze rows/column above/left of a cell
									excel.ActiveWorkbook.Windows(1).FreezePanes = True
									wb.Save()
									wb.Close()

									## If csv exists (which it should) delete it ##
									if os.path.isfile(resultsSavePath):
										os.remove(resultsSavePath)
									else:    ## Show an error ##
										print("Error: %s file not found" % resultsSavePath)
									#refresh save folder
									try:
										path = os.path.realpath(resultsSavePath_Base)
										os.startfile(path)
									except:
										message+= ' / Failed to Open Save Folder'
								except:
									message+= ' / Failed to Save Results'
								counter+=1
						else:
							print('Only 1 csv created, the master csv')
						#resresh output directory to ensure all files in there are displayed
						os.listdir(resultsSavePath_Base)
						#display Results message
						errorMessage4 = message
						widget5 = iface.messageBar().createMessage(errorMessage4)
						iface.messageBar().pushWidget(widget5, Qgis.Success, duration=1)
					else:
						errorMessage4 = "No Rus Found for that WU List"
						widget5 = iface.messageBar().createMessage(errorMessage4)
						iface.messageBar().pushWidget(widget5, Qgis.Warning, duration=7)

		elif dropDown_ftr_type == "Import WU List (to open Training DB):":
			print('starting Copy WU List to Training DB from WU csv')
			##### connection settings to live RFDB #####
			iface.settings = QSettings('Geodigital', 'db_params_settings')
			currentConnectionName = str(iface.settings.value('current_connection'))
			currentConnection = {}
			currentConnection = iface.settings.value('connections')[currentConnectionName]
			username = str(iface.settings.value('connections')[currentConnectionName]['user_name'])
			password = str(iface.settings.value('connections')[currentConnectionName]['password'])
			databaseName = str(iface.settings.value('connections')[currentConnectionName]['database_name'])
			hostName = str(iface.settings.value('connections')[currentConnectionName]['server_ip'])
			port = str(iface.settings.value('connections')[currentConnectionName]['port'])
			print(hostName)
			print(databaseName)

			##### END connection settings to live RFDB #####

			#check if connected to training DB cluster
			if str(hostName) == 'rfdb-training.cluster-ro-cyyozlmkfkuq.ap-south-1.rds.amazonaws.com':
				#processing CSV or EXCEL, which is WU LIST
				wuListFilePath=""
				downloads_path = str(Path.home() / "Downloads")
				wuListFilePath = str(QFileDialog.getOpenFileName(iface.mainWindow(), "Choose CSV WU List to Run", downloads_path ,filter = "Excel (*.csv *.xlsx)")[0])
				wuHeaderFound=False
				csvFound=False
				ExcelFound=False
				if wuListFilePath!="":
					with open(wuListFilePath, 'r') as file:
						#go through WU List csv and get list of WUs and save list
						wu_list=[]
						str_wu_list=''
						try:
							df = pd.ExcelFile(wuListFilePath) #you could add index_col=0 if there's an index
							ExcelFound=True
							print('Excel Found')
						except:
							try:
								df = pd.read_csv(wuListFilePath)
								csvFound=True
								print('CSV Found')
							except:
								print('Error: No CSV or Excel Found')
						#get sheet names and get first sheet name that is not called 'summary'. Sheet name not needed for CSVs
						if csvFound==False and ExcelFound==True:
							sheetNames=df.sheet_names
							sheetName=''
							for s in sheetNames:
								if 'summary' not in str(s).lower():
									sheetName=str(s)
									break
							df = pd.ExcelFile(wuListFilePath).parse(sheetName) #you could add index_col=0 if there's an index
						#get column header for WU_Ids, from csv or excel sheet
						if csvFound==True or ExcelFound==True:
							columnName=''
							headers=list(df.columns.values)
							for h in headers:
								if 'work unit' in str(h).lower() or 'wu' in str(h).lower() or 'work_unit' in str(h).lower():
									columnName=str(h)
									wuHeaderFound=True
									break
							if wuHeaderFound==False:
								errorMessage4 = "No column header found with WU, Work Unit, or Work_Unit in name. Make sure headers are in 1st row, and spelling is ok"
								widget5 = iface.messageBar().createMessage(errorMessage4)
								iface.messageBar().pushWidget(widget5, Qgis.Warning, duration=0)
							else:
								wu_list.append(df[columnName].tolist())
								for wu in wu_list[0]:
									try:
										str_wu_list=str_wu_list+str(int(wu))+','
									except:
										print('cannot convert this row to WU int: ' + str(wu))
								str_wu_list=str_wu_list[0:-1]
								print('string wu list:')
								print(str_wu_list)
						else:
							errorMessage4 = "No CSV or Excel file found."
							widget5 = iface.messageBar().createMessage(errorMessage4)
							iface.messageBar().pushWidget(widget5, Qgis.Warning, duration=0)
					#running query, if WU LIST import successful
					if (csvFound==True or ExcelFound==True) and wuHeaderFound==True:
						#TODO: add dialog question, are you sure you want to 'Import len(wu_list) from Prod DB to this Training DB?''
						#blueprint for 'Are you sure?' dialog
						class CustomDialog(QDialog):
							def __init__(self):
								super(CustomDialog, self).__init__()

								# Set the window title
								self.setWindowTitle("Confirm import into " + str(databaseName))

								# Create a layout for the dialog
								layout = QVBoxLayout()

								# Add a label with your message
								message_label = QLabel("Are you sure you want to import?\n" + str(len(wu_list[0])) + " WUs \nfrom Prod DB \nto " + str(databaseName) + "\n("+str(hostName)+")?")
								layout.addWidget(message_label)

								# Add OK and Cancel buttons
								ok_button = QPushButton("OK")
								cancel_button = QPushButton("Cancel")

								layout.addWidget(ok_button)
								layout.addWidget(cancel_button)

								# Connect the buttons to their respective functions
								ok_button.clicked.connect(self.accept)
								cancel_button.clicked.connect(self.reject)

								self.setLayout(layout)
						# Create and show the custom dialog
						dialog = CustomDialog()
						result = dialog.exec_()

						#Yes, selected
						if result == QDialog.Accepted:
							# OK button was pressed
							print("OK button pressed. Running your code here.")

							#run query
							message=''

							conn = psycopg2.connect(host=hostName, port=port, dbname=databaseName, user=username, password=password)
							cur = conn.cursor()
							print(str_wu_list)
							str_wu_list_withQuotes = "'" + str(str_wu_list.replace(",","','")) + "'"
							print(str_wu_list_withQuotes)
							sql = ("""
							SELECT dblink_connect('CONN',
									'host=rfdb-production-mumbai.cyyozlmkfkuq.ap-south-1.rds.amazonaws.com
								  	port=5432 dbname=road_features
									user=ushr_vithakurdwarkar password=ushr_vithakurdwarkar_2018');

							INSERT INTO work_units.work_unit (id, subcountry, created, created_user, geom, manual_geom) \
							SELECT * FROM dblink('CONN', \
							'SELECT DISTINCT on (id) id, subcountry, created, created_user, geom, manual_geom \
							FROM work_units.work_unit \
							where id IN ({normal})') \
							AS t(id bigint, subcountry character varying, created timestamp without time zone, \
								created_user text, geom postgis.geometry, manual_geom boolean) \
							WHERE not exists (SELECT id FROM work_units.work_unit w where w.id = t.id) \
							ON CONFLICT (id) DO UPDATE SET subcountry = EXCLUDED.subcountry, created = EXCLUDED.created, \
								created_user = EXCLUDED.created_user, geom = EXCLUDED.geom, manual_geom = EXCLUDED.manual_geom; \

							INSERT INTO activity.osm_work_unit (id, id_seg, id_acquisition, wu_id, operation, by_user, modified_time) \
							SELECT * FROM dblink('CONN', \
							$$  \
							SELECT id, id_seg, id_acquisition, wu_id, operation, by_user, modified_time \
							FROM activity.osm_work_unit \
							WHERE wu_id IN ({special}) \
							$$) \
							AS t(id bigint, id_seg bigint, id_acquisition integer, wu_id text,  operation text, by_user text, modified_time timestamp without time zone) \
							ON CONFLICT (id) DO UPDATE SET id_seg = EXCLUDED.id_seg, id_acquisition = EXCLUDED.id_acquisition, wu_id = EXCLUDED.wu_id, \
							operation = EXCLUDED.operation, by_user = EXCLUDED.by_user, modified_time = EXCLUDED.modified_time \
							WHERE (osm_work_unit.id_seg, osm_work_unit.id_acquisition, osm_work_unit.wu_id, osm_work_unit.operation, osm_work_unit.by_user, osm_work_unit.modified_time) is distinct from \
							(EXCLUDED.id_seg, EXCLUDED.id_acquisition, EXCLUDED.wu_id, EXCLUDED.operation, EXCLUDED.by_user, EXCLUDED.modified_time); \

							INSERT INTO externaL_data_metadata.pointcloud_acquisitions (pointcloud_id, acquisition_system_name, \
							start_date, trail, bidirectional_coverage) \
							SELECT * FROM dblink('CONN', \
							'SELECT distinct pointcloud_id, acquisition_system_name, start_date, trail, bidirectional_coverage \
							FROM external_data_metadata.pointcloud_acquisitions pcacq \
							JOIN work_units.wu_point_cloud wpc ON wpc.pc_id = pcacq.pointcloud_id \
							WHERE wu_id in ({normal})') \
							AS t(pointcloud_id text, acquisition_system_name text, start_date date, trail postgis.geography, \
								 bidirectional_coverage boolean) \
							ON CONFLICT (pointcloud_id) DO UPDATE SET acquisition_system_name = EXCLUDED.acquisition_system_name, \
							start_date = EXCLUDED.start_date, trail = EXCLUDED.trail, \
							bidirectional_coverage = EXCLUDED.bidirectional_coverage \
							WHERE (pointcloud_acquisitions.acquisition_system_name, pointcloud_acquisitions.start_date, \
								pointcloud_acquisitions.trail, pointcloud_acquisitions.bidirectional_coverage) is distinct from \
								(EXCLUDED.acquisition_system_name, EXCLUDED.start_date, EXCLUDED.trail, EXCLUDED.bidirectional_coverage); \

							INSERT INTO work_units.wu_point_cloud (id, wu_id, pc_id, modified_time) \
							SELECT * FROM dblink('CONN', \
							'SELECT id, wu_id, pc_id, modified_time \
							FROM work_units.wu_point_cloud \
							WHERE wu_id IN ({normal})') \
							AS t(id bigint, wu_id bigint, pc_id text, modified_time timestamp without time zone) \
							ON CONFLICT (id) DO UPDATE SET wu_id = EXCLUDED.wu_id, pc_id = EXCLUDED.pc_id, \
							modified_time = EXCLUDED.modified_time \
							WHERE (wu_point_cloud.wu_id, wu_point_cloud.pc_id, wu_point_cloud.modified_time) is distinct from \
							(EXCLUDED.wu_id, EXCLUDED.pc_id, EXCLUDED.modified_time); \

							INSERT INTO work_units.projects (id, wu_id, project) \
							SELECT * FROM dblink('CONN', \
							'SELECT id, wu_id, project FROM work_units.projects \
							WHERE wu_id IN ({normal})') \
							AS t(id integer, wu_id bigint, project text) \
							ON CONFLICT (id) DO UPDATE SET wu_id = EXCLUDED.wu_id, project = EXCLUDED.project \
							WHERE (projects.wu_id, projects.project) is distinct from (EXCLUDED.wu_id, EXCLUDED.project); \

							INSERT INTO work_units.completion_tracking (wu_id, publishable_state, segment_length_sum, geom_length) \
							SELECT * FROM dblink('CONN', \
							'SELECT wu_id, publishable_state, segment_length_sum, geom_length \
							FROM work_units.completion_tracking \
							WHERE wu_id IN ({normal})') \
							AS t(wu_id bigint, publishable_state boolean, segment_length_sum double precision, \
								geom_length double precision) \
							ON CONFLICT (wu_id) DO UPDATE SET publishable_state = EXCLUDED.publishable_state, \
								segment_length_sum = EXCLUDED.segment_length_sum, geom_length = EXCLUDED.geom_length \
							WHERE (completion_tracking.publishable_state, completion_tracking.segment_length_sum, \
								completion_tracking.geom_length) is distinct from (EXCLUDED.publishable_state, \
								EXCLUDED.segment_length_sum, EXCLUDED.geom_length); \

							INSERT INTO work_units.activity (id, wu_id, start_time, stop_time, active_user, wu_state, description) \
							SELECT * FROM dblink('CONN', \
							$$ \
							SELECT id, wu_id, start_time, stop_time, active_user, wu_state, description \
							FROM work_units.activity \
							WHERE wu_id IN ({normal}) and wu_state='Created' \
							ORDER BY wu_id ASC, start_time ASC \
							$$) \
							AS t(id integer, wu_id bigint, start_time timestamp without time zone, stop_time timestamp without \
							 time zone, active_user text, wu_state work_unit_state, description text) \
							ON CONFLICT (id) DO UPDATE SET wu_id = EXCLUDED.wu_id, start_time = EXCLUDED.start_time, \
							stop_time = EXCLUDED.stop_time, active_user = EXCLUDED.active_user, wu_state = EXCLUDED.wu_state, \
							description = EXCLUDED.description \
							WHERE (activity.wu_id, activity.start_time, activity.stop_time, activity.active_user, activity.wu_state, \
							activity.description) is distinct from (EXCLUDED.wu_id, EXCLUDED.start_time, EXCLUDED.stop_time, \
							EXCLUDED.active_user, EXCLUDED.wu_state, EXCLUDED.description)  \
							;""").format(normal=str_wu_list, special=str_wu_list_withQuotes)

							#over-write above sql to test
							'''sql = ("""
							SELECT * FROM work_units.activity \
							where wu_id in ({normal}) and wu_state ='Created' \
							;""").format(normal=str_wu_list)'''

							cur.execute(sql)
							if 'delete from' in sql.lower() or 'insert into' in sql.lower():
								additionalText = 'COMMITTED CHANGES! '
								conn.commit()
							else:
								additionalText = 'EXECUTED! '
							cur.close()
							conn.close()

							#success message
							errorMessage4 = "Open ATDB plugin on same Training DB and deploy imported, newly-Created WUs."
							widget5 = iface.messageBar().createMessage(additionalText + errorMessage4)
							iface.messageBar().pushWidget(widget5, Qgis.Success, duration=12)
						else:
							# Cancel button was pressed or the dialog was closed
							print("Cancel button pressed or dialog closed. No code executed.")

					#error, either no csv/Excel found, or no WU Header Found
					else:
						errorMessage4 = "Either no csv/Excel found, or no WU Header Found."
						widget5 = iface.messageBar().createMessage(errorMessage4)
						iface.messageBar().pushWidget(widget5, Qgis.Warning, duration=7)
			#error, if not connected to training DB cluster
			else:
				errorMessage4 = "Please re-connect to a Training DB. You can only import WUs from Prod DB to a Training DB."
				widget5 = iface.messageBar().createMessage(errorMessage4)
				iface.messageBar().pushWidget(widget5, Qgis.Warning, duration=7)

		elif dropDown_ftr_type == "SQL Runner:":
			sqlFilePath=""
			sqlFilePath = str(QFileDialog.getOpenFileName(iface.mainWindow(), "Choose SQL File to Run", "G:/CSAV3/_Production_Query_Library",filter = "SQL (*.sql *.txt)")[0])
			if sqlFilePath!="":
				##### connection settings to live RFDB #####
				iface.settings = QSettings('Geodigital', 'db_params_settings')
				currentConnectionName = str(iface.settings.value('current_connection'))
				currentConnection = {}
				currentConnection = iface.settings.value('connections')[currentConnectionName]
				username = str(iface.settings.value('connections')[currentConnectionName]['user_name'])
				password = str(iface.settings.value('connections')[currentConnectionName]['password'])
				databaseName = str(iface.settings.value('connections')[currentConnectionName]['database_name'])
				hostName = str(iface.settings.value('connections')[currentConnectionName]['server_ip'])
				port = str(iface.settings.value('connections')[currentConnectionName]['port'])
				##### END connection settings to live RFDB #####
				message=''


				conn = psycopg2.connect(host=hostName, port=port, dbname=databaseName, user=username, password=password)
				cur = conn.cursor()
				sql = ("""
				SELECT wu_id, segment_id, replaced_by_wuid
				FROM road_unit.segment_boundaries WHERE segment_id=1362271


				;""")
				result=None
				resultsFound=False
				headers=[]
				with open(sqlFilePath, 'r') as file:
					sql = file.read().replace('\n', ' ')
					sql+=';'
				print(sql)
				#.format(str(state))
				cur.execute(sql)
				message+="Executed Query"
				for items in cur.description:
					headers.append(str(items.name))
				try:
					result = cur.fetchall()
					if str(result) =='[]' or result==None:
						resultsFound=False
					else:
						resultsFound=True
					rows=len(result)
					message+=' / Rows: '+str(rows)
				except:
					if 'update' in sql.lower() or 'insert into' in sql.lower():
						conn.commit()
						message+=' / Committed Changes! '
				#closing connection and cursor
				cur.close()
				conn.close()
				if resultsFound==True:
					#filename
					resultsSavePath_Base=str(QgsApplication.qgisSettingsDirPath())
					cutPos=resultsSavePath_Base.find('Roaming')
					resultsSavePath_Base=resultsSavePath_Base[0:cutPos]+'Local/Ushr/reports/'
					dateTimeObj = datetime.now()
					timestampStr = dateTimeObj.strftime("%Y%m%d-%H%M%S")
					sqlScriptName=sqlFilePath.split('/')[-1].split('.')[0]
					filename=sqlScriptName+'_'+timestampStr+'_count'+str(rows)
					#save Path
					resultsSavePath=resultsSavePath_Base+filename+'.csv'

					# open csv, write results to CSV
					try:
						with open(resultsSavePath, 'w', newline='') as csvfile: #str(QgsApplication.qgisSettingsDirPath()) find AppData and
							spamwriter = csv.writer(csvfile, delimiter=';',quotechar='|', quoting=csv.QUOTE_MINIMAL)
							spamwriter.writerow(headers)
							spamwriter.writerows(result)
						message+= ' / Saved Results to: ' + resultsSavePath
						try:
							path = os.path.realpath(resultsSavePath_Base)
							os.startfile(path)
						except:
							message+= ' / Failed to Open Save Folder'
					except:
						message+= ' / Failed to Save Results'
				#display Results message
				errorMessage4 = message
				widget5 = iface.messageBar().createMessage(errorMessage4)
				iface.messageBar().pushWidget(widget5, Qgis.Success, duration=0)

		elif dropDown_ftr_type == "USHR Ground Images:":
			print("START PROCESS: USHR Ground Images")
			error=""
			#open user-input file browser, only showing folders
			groundImagesPath = str(QFileDialog.getExistingDirectory(iface.mainWindow(),"Choose Path to USHR Ground Images for Loading","G:/TestTracks/Rivian/Toyota_Arizona_Proving_Ground/VMQ4_20049_jpgs/images",QFileDialog.ShowDirsOnly))
			if groundImagesPath!="":
				imageDir=str(groundImagesPath)+"/"
				#stripChar=['a','b','c','d','e','f','g','h','i','j','k','l','m','n','o','p','q','r','s','t','u','v','w','x','y','z','!','\"','#','$','%','&','\'','(',')','*','+','/',':',';','<','=','>','?','@','[','\\',']','^','`','{','|','}','~',',','\t','\n','°','_']
				#julienDay = self.textbox.text().lstrip().rstrip()
				#for char in stripChar:
				#	julienDay = julienDay.lower().replace(char, '')
				#julienDay.lstrip().rstrip()
				#julienDay=julienDay[0:6]
				#print(julienDay)
				#searchCriteria='*'+julienDay+'*'
				filter=self.textbox.text()
				searchCriteria='*'+filter+'*'
				ext='.jpg'

				#####progress bar#####
				#clear the message bar
				iface.messageBar().clearWidgets()
				#set a new message bar
				progressMessageBar = iface.messageBar()
				progress = QProgressBar()
				#Maximum is set to 100, making it easy to work with percentage of completion
				progress.setMaximum(100)
				#pass the progress bar to the message Bar
				progressMessageBar.pushWidget(progress)
				#count total matches
				totalMatchesCount=0
				for file in os.listdir(imageDir):
					if fnmatch.fnmatch(file, searchCriteria) and fnmatch.fnmatch(file, '*'+ext+'*'):
						totalMatchesCount+=1
				if totalMatchesCount==0:
					error="No Images Found using filter: " + str(filter)
				#ground images found
				else:
					#create memory layer with layerName and certain style
					if searchCriteria=='**':
						layerName='USHR_GroundImages_NoFilterUsed'
					else:
						layerName='USHR_GroundImages_UsingFilter_'+str(filter)
					print("Creating Layer")
					# create layer
					vl = QgsVectorLayer("Point", layerName, "memory")
					pr = vl.dataProvider()

					# Enter editing mode
					vl.startEditing()

					# add fields
					pr.addAttributes( [ QgsField("filename", QVariant.String),
									QgsField("imagePath", QVariant.String),
									QgsField("coordsX",  QVariant.Double),
									QgsField("coordsY", QVariant.Double),
									QgsField("Heading", QVariant.Double)
								] )

					#get GPS info from certain images and add features to memory layer using those coordinates below
					count=0
					for file in os.listdir(imageDir):
						if fnmatch.fnmatch(file, searchCriteria) and fnmatch.fnmatch(file, '*'+ext+'*'):
							if count>-1:
								count+=1
								## DEBUG
								print("file: ")
								print(str(file))
								print("imageDir: ")
								print(str(imageDir))
								#Update the progress bar
								percent = (count/float(totalMatchesCount)) * 100
								progress.setValue(percent)

								filename=file[0:-4]
								#matchingImagesList[filename]={} 	#WARNING: overwrites image files with same filename.extsn, so duplicates within a folder directory not supported
								imgPath=imageDir+file
								#matchingImagesList[filename]["imagePath"]=imgPath

								#gets info from image at this image path
								#ERROR when using G:\Subaru\20210426_sampledata\Route50-407\HD_1110_202103260944_S04_01\Camera01
								#ERROR CONT.:  PIL.Image.open(imageDir+file)._getexif() becomes NoneType
								img = PIL.Image.open(imgPath)
								#DEBUG
								print(img._getexif())
								exif_GPSInfo = {
									PIL.ExifTags.TAGS[k]: v
									for k, v in img._getexif().items()
									if k in PIL.ExifTags.TAGS
									}['GPSInfo']
								img.close()
								gpsinfo = {}
								for key in exif_GPSInfo.keys():
									decode = PIL.ExifTags.GPSTAGS.get(key,key)
									gpsinfo[decode] = exif_GPSInfo[key]

								#coordinates. Copied mostly from: https://gist.github.com/snakeye/fdc372dbf11370fe29eb
								def _get_if_exist(data, key):
									if key in data:
										return data[key]
									return None
								def _convert_to_degress(value):
									d = float(value[0][0]) / float(value[0][1])
									m = float(value[1][0]) / float(value[1][1])
									s = float(value[2][0]) / float(value[2][1])
									return d + (m / 60.0) + (s / 3600.0)

								lat = None
								lon = None

								gps_latitude = _get_if_exist(gpsinfo, 'GPSLatitude')
								gps_latitude_ref = _get_if_exist(gpsinfo, 'GPSLatitudeRef')
								gps_longitude = _get_if_exist(gpsinfo, 'GPSLongitude')
								gps_longitude_ref = _get_if_exist(gpsinfo, 'GPSLongitudeRef')

								if gps_latitude and gps_latitude_ref and gps_longitude and gps_longitude_ref:
									lat = _convert_to_degress(gps_latitude)
									if gps_latitude_ref != 'N':
										lat = 0 - lat

									lon = _convert_to_degress(gps_longitude)
									if gps_longitude_ref != 'E':
										lon = 0 - lon

								#heading
								gps_direction=_get_if_exist(gpsinfo, 'GPSImgDirection')
								gps_heading=gps_direction[0]/gps_direction[1]
								#matchingImagesList[filename]["Heading"]=gps_heading

								# add a feature
								fet = QgsFeature()
								fet.setAttributes([filename, 'file:///'+imgPath, lon, lat, gps_heading])
								fet.setGeometry(QgsGeometry.fromPointXY(QgsPointXY(float(lon),float(lat))))
								pr.addFeatures( [ fet ] )

					# Commit changes to new layer
					vl.commitChanges()
					QgsProject.instance().addMapLayer(vl)

					#add action
					acManager = vl.actions()
					acActor = QgsAction(5, 'Open Photo', '[%imagePath%]', False)
					acActor.setActionScopes({'Feature','Canvas'})
					acManager.addAction(acActor)

					#set symbol
					# create a new single symbol renderer
					symbol = QgsSymbol.defaultSymbol(vl.geometryType())
					renderer = QgsSingleSymbolRenderer(symbol)

					# create a new simple marker symbol layer, a green circle with a black border
					properties={'name': 'arrow', 'color':'255,0,255,255', 'outline_color': 'black', 'size': '5.0','outline_style': 'solid', 'outline_width': '0.25', 'rotation_expression': '"Heading"'}
					symbol_layer = QgsSimpleMarkerSymbolLayer.create(properties)

					# assign the symbol layer to the symbol
					renderer.symbols(QgsRenderContext())[0].changeSymbolLayer(0, symbol_layer)

					# assign the renderer to the layer
					vl.setRenderer(renderer)

					vl.triggerRepaint()
				iface.messageBar().clearWidgets()
			if error!='':
				widget05 = iface.messageBar().createMessage(error)
				iface.messageBar().pushWidget(widget05, Qgis.Warning, duration=5)
			print("END PROCESS: USHR Ground Images\n")

		#disabled, for now
		elif dropDown_ftr_type == "Image On Click:":
			#searches a folder and looks through JPG GPS details to find image that is close to coordinate. A bit slow if you're going to be using it a lot, and you'd have to know where the points are, unless you used more code to find nearest point, possibly with correct heading
			print("START PROCESS: Image On Click")
			tol=0.00001
			clickedCoordinates=(-112.79528169, 33.76020825)
			clickedCoordinatesX=clickedCoordinates[0]
			#xDeg=math.floor(abs(clickedCoordinatesX))
			clickedCoordinatesY=clickedCoordinates[1]
			#yDeg=math.floor(abs(clickedCoordinatesY))
			print('clickedCoordinates: '+str(clickedCoordinatesX) +', '+ str(clickedCoordinatesY))
			#clickedCoordinatesX=-112.76665651
			#clickedCoordinatesY=33.74425033
			imageDir='G:/TestTracks/Toyota_Arizona_Proving_Ground/VMQ4_20049_jpgs/images/'

			#get coordinates and  add features to memory layer using those coordinates below
			#matchingImagesList={}
			count=0
			for file in os.listdir(imageDir):
				if fnmatch.fnmatch(file, '*.jpg*'):
					if count>-1:
						count+=1
						filename=file[0:-4]
						#matchingImagesList[filename]={} 	#WARNING: overwrites image files with same filename.extsn, so duplicates within a folder directory not supported
						imgPath=imageDir+file
						img = PIL.Image.open(imgPath)
						exif_GPSInfo = {
							PIL.ExifTags.TAGS[k]: v
							for k, v in img._getexif().items()
							if k in PIL.ExifTags.TAGS
							}['GPSInfo']
						#print(exif_GPSInfo)
						img.close()
						gpsinfo = {}
						for key in exif_GPSInfo.keys():
							decode = PIL.ExifTags.GPSTAGS.get(key,key)
							gpsinfo[decode] = exif_GPSInfo[key]

						#get coordinates:  convert exif GPSInfo lat/long to degrees/corrdinates and maybe add coordinates to dictionary. Copied mostly from: https://gist.github.com/snakeye/fdc372dbf11370fe29eb
						def _get_if_exist(data, key):
							if key in data:
								return data[key]
							return None
						def _convert_to_degress(value):
							d = float(value[0][0]) / float(value[0][1])
							m = float(value[1][0]) / float(value[1][1])
							s = float(value[2][0]) / float(value[2][1])
							return d + (m / 60.0) + (s / 3600.0)

						lat = None
						lon = None

						gps_latitude = _get_if_exist(gpsinfo, 'GPSLatitude')
						gps_latitude_ref = _get_if_exist(gpsinfo, 'GPSLatitudeRef')
						gps_longitude = _get_if_exist(gpsinfo, 'GPSLongitude')
						gps_longitude_ref = _get_if_exist(gpsinfo, 'GPSLongitudeRef')

						if gps_latitude and gps_latitude_ref and gps_longitude and gps_longitude_ref:
							lat = _convert_to_degress(gps_latitude)
							if gps_latitude_ref != 'N':
								lat = 0 - lat

							lon = _convert_to_degress(gps_longitude)
							if gps_longitude_ref != 'E':
								lon = 0 - lon

						if abs(lon-clickedCoordinatesX)<=tol:
							if abs(lat-clickedCoordinatesY)<=tol:
								print(filename)
								print('photo coordinates: '+str(lon)+', ' + str(lat))

			print("END PROCESS: Image On Click")

		elif dropDown_ftr_type == 'Coords (USA CAN JPN EU):':
			try:
				#remove existing coord layer, if any
				for lyr in QgsProject.instance().mapLayers().values():
					if "_qcToolsCoord_" in lyr.name():
						QgsProject.instance().removeMapLayer(lyr)
				#pan to Coordinates
				stripChar=['a','b','c','d','e','f','g','h','i','j','k','l','m','n','o','p','q','r','s','t','u','v','w','x','y','z','!','\"','#','$','%','&','\'','(',')','*','+','/',':',';','<','=','>','?','@','[','\\',']','^','_','`','{','|','}','~']
				coordsWithPoint = self.textbox.text().lstrip().rstrip()
				for char in stripChar:
					coordsWithPoint = coordsWithPoint.lower().replace(char, '')
				coordsWithPoint.lstrip().rstrip()
				coordsWithPoint = coordsWithPoint.replace(',' ,' ').replace('\t', ' ').replace('\n', ' ').replace('_', ' ').replace('°', ' ')
				coordsWithPoint = ' '.join(coordsWithPoint.split())
				coordsX = float(coordsWithPoint.split(' ')[0])
				coordsY = float(coordsWithPoint.split(' ')[1])
				#USA CAN JPN (where all of our work is done currently for USA, CAN, and JPN). This is so that regardless of using QGIS or Google 'lat lon' or 'lon lat', the coords should work
				if coordsY<=0 or coordsY>=90 or (coordsY>0 and coordsX>0 and coordsY<=34.55 and coordsX<=90):
					print('swap: out of bounds, aka inversion territory')
					coords2Point = QgsPointXY(coordsY, coordsX)
					print(str(coordsY) +','+str(coordsX))
				else:
					print('keep same: in bounds, aka non-inversion territory')
					coords2Point = QgsPointXY(coordsX, coordsY)
					print(str(coordsX) +','+str(coordsY))
				iface.mapCanvas().setCenter(coords2Point)
				iface.mapCanvas().refresh()
				#zoom to scale
				iface.mapCanvas().zoomScale(1000.0)

				#add symbol to canvas
				iface.mainWindow().blockSignals(True)
				try:
					iface.setActiveLayer(QgsProject.instance().layerTreeRoot().children()[0].layer())
				except:
					print("Top layer is a group, not a layer. Could not load layer to top of Layers Panel")
				crs_authid = iface.mapCanvas().mapSettings().destinationCrs().authid()
				my_layer = QgsVectorLayer('Point', '_qcToolsCoord_' + str(crs_authid) + '_' + coordsWithPoint, 'memory')
				my_layer.setCrs(QgsCoordinateReferenceSystem(crs_authid))
				pr = my_layer.dataProvider()
				feature = QgsFeature()
				feature.setGeometry(QgsGeometry.fromPointXY(coords2Point))
				pr.addFeatures([feature])
				symbol = QgsMarkerSymbol.createSimple({'name': 'cross', 'outline_color': '255,0,0,255', 'size': '5.0','outline_style': 'solid', 'outline_width': '0.7'})
				renderer = QgsSingleSymbolRenderer(symbol)
				my_layer.setRenderer(renderer)
				iface.mapCanvas().setDestinationCrs(QgsCoordinateReferenceSystem(crs_authid))
				QgsProject.instance().addMapLayer(my_layer, True)
				iface.mainWindow().blockSignals(False)
			except:
				errorMessage3a = "Error"
		elif dropDown_ftr_type == 'Coords (ME):':
			try:
				#remove existing coord layer, if any
				for lyr in QgsProject.instance().mapLayers().values():
					if "_qcToolsCoord_" in lyr.name():
						QgsProject.instance().removeMapLayer(lyr)
				#pan to Coordinates
				stripChar=['a','b','c','d','e','f','g','h','i','j','k','l','m','n','o','p','q','r','s','t','u','v','w','x','y','z','!','\"','#','$','%','&','\'','(',')','*','+','/',':',';','<','=','>','?','@','[','\\',']','^','_','`','{','|','}','~']
				coordsWithPoint = self.textbox.text().lstrip().rstrip()
				for char in stripChar:
					coordsWithPoint = coordsWithPoint.lower().replace(char, '')
				coordsWithPoint.lstrip().rstrip()
				coordsWithPoint = coordsWithPoint.replace(',' ,' ').replace('\t', ' ').replace('\n', ' ').replace('_', ' ').replace('°', ' ')
				coordsWithPoint = ' '.join(coordsWithPoint.split())
				coordsX = float(coordsWithPoint.split(' ')[0])
				coordsY = float(coordsWithPoint.split(' ')[1])
				#ME. This is so that regardless of using QGIS or Google 'lat lon' or 'lon lat', the coords should work
				if coordsY>=34 or coordsX<34: #out of bounds: swap if above 34 lat, or below 34 longitude
					print('swap (out of bounds)')
					coords2Point = QgsPointXY(coordsY, coordsX)
					print(str(coordsY) +','+str(coordsX))
				else:						#in bounds: keep same if below 34 lat, or above 34 longitude
					print('keep same (in bounds)')
					coords2Point = QgsPointXY(coordsX, coordsY)
					print(str(coordsX) +','+str(coordsY))
				iface.mapCanvas().setCenter(coords2Point)
				iface.mapCanvas().refresh()
				#zoom to scale
				iface.mapCanvas().zoomScale(1000.0)

				#add symbol to canvas
				iface.mainWindow().blockSignals(True)
				try:
					iface.setActiveLayer(QgsProject.instance().layerTreeRoot().children()[0].layer())
				except:
					print("Top layer is a group, not a layer. Could not load layer to top of Layers Panel")
				crs_authid = iface.mapCanvas().mapSettings().destinationCrs().authid()
				my_layer = QgsVectorLayer('Point', '_qcToolsCoord_' + str(crs_authid) + '_' + coordsWithPoint, 'memory')
				my_layer.setCrs(QgsCoordinateReferenceSystem(crs_authid))
				pr = my_layer.dataProvider()
				feature = QgsFeature()
				feature.setGeometry(QgsGeometry.fromPointXY(coords2Point))
				pr.addFeatures([feature])
				symbol = QgsMarkerSymbol.createSimple({'name': 'cross', 'outline_color': '255,0,0,255', 'size': '5.0','outline_style': 'solid', 'outline_width': '0.7'})
				renderer = QgsSingleSymbolRenderer(symbol)
				my_layer.setRenderer(renderer)
				iface.mapCanvas().setDestinationCrs(QgsCoordinateReferenceSystem(crs_authid))
				QgsProject.instance().addMapLayer(my_layer, True)
				iface.mainWindow().blockSignals(False)
			except:
				errorMessage3a = "Error"
		elif dropDown_ftr_type == "Old->New Ru:":
			self.settings = QSettings('Geodigital', 'db_params_settings')
			currentConnectionName = str(self.settings.value('current_connection'))
			currentConnection = {}
			currentConnection = self.settings.value('connections')[currentConnectionName]
			username = str(self.settings.value('connections')[currentConnectionName]['user_name'])
			password = str(self.settings.value('connections')[currentConnectionName]['password'])
			databaseName = str(self.settings.value('connections')[currentConnectionName]['database_name'])
			hostName = str(self.settings.value('connections')[currentConnectionName]['server_ip'])
			port = str(self.settings.value('connections')[currentConnectionName]['port'])
			##### END connection settings to RFDB #####

			errorMessage4 = None
			#get text from textbox
			searchingForThis_Feature_ID = self.textbox.text().strip()
			#check if string is digit
			if searchingForThis_Feature_ID.isdigit() == True:
				conn = psycopg2.connect(host=hostName, port=port, dbname=databaseName, user=username, password=password)
				cur = conn.cursor()
				#build and execute SQL query
				sql =   ("SELECT sh.id, sh.old_segment, sh.new_segment, sh.modified_time, sh.modified_user, sp.segment_id \
						FROM road_unit.segment_history sh \
						INNER JOIN road_unit.segment_paths sp on sp.segment_id = sh.new_segment \
						where old_segment={} \
						group by sh.id, sh.old_segment, sh.new_segment, sh.modified_time, sh.modified_user, sp.segment_id;").format(searchingForThis_Feature_ID)
				cur.execute(sql)
				result = cur.fetchall()
				#closing connection and cursor
				cur.close()
				conn.close()
				#print(result)
				ruList=[]
				for results in result:
					ruList.append(results[2])
				if ruList != []:
					errorMessage4 = "OLD RU " +searchingForThis_Feature_ID +" REPLACED BY NEW RUs (That Still Exist): "+ str(ruList)
					widget5 = iface.messageBar().createMessage(errorMessage4)
					iface.messageBar().pushWidget(widget5, Qgis.Success, duration=0)
				else:
					errorMessage4 = "RU LIKELY STILL EXISTS. Change qcTools Drop-Down Menu option to 'Road Unit Id:'. Then, try running again..."
					widget5 = iface.messageBar().createMessage(errorMessage4)
					iface.messageBar().pushWidget(widget5, Qgis.Warning, duration=7)
			else:
				errorMessage4 = "Please enter digits only!" #ok
				#display warning
				widget5 = iface.messageBar().createMessage(errorMessage4)
				iface.messageBar().pushWidget(widget5, Qgis.Warning,duration=3)

		elif dropDown_ftr_type =="Count Features for WU(s):":
			csvFound=False
			ExcelFound=False
			wuHeaderFound=False
			WuTextBoxFound=False
			searchingForThis_Feature_ID = self.textbox.text().strip()
			##### connection settings to RFDB #####
			self.settings = QSettings('Geodigital', 'db_params_settings')
			currentConnectionName = str(self.settings.value('current_connection'))
			currentConnection = {}
			currentConnection = self.settings.value('connections')[currentConnectionName]
			username = str(self.settings.value('connections')[currentConnectionName]['user_name'])
			password = str(self.settings.value('connections')[currentConnectionName]['password'])
			databaseName = str(self.settings.value('connections')[currentConnectionName]['database_name'])
			hostName = str(self.settings.value('connections')[currentConnectionName]['server_ip'])
			port = str(self.settings.value('connections')[currentConnectionName]['port'])
			##### END connection settings to RFDB #####

			#WU from text box
			#get text from textbox
			if searchingForThis_Feature_ID != '':
				print('using text box')

				#clean input text
				digits = re.findall(r'\d+', str(searchingForThis_Feature_ID))
				digit_set = set(digits)
				countNumWus=len(digit_set)
				searchingForThis_Feature_ID_clean= ', '.join(str(d) for d in digit_set)
				str_wu_list=str(searchingForThis_Feature_ID_clean)
				print('str_wu_list: ' + str_wu_list)
				WuTextBoxFound=True
			else:
				#processing CSV or EXCEL, which is WU LIST
				wuListFilePath=""
				downloads_path = str(Path.home() / "Downloads")
				wuListFilePath = str(QFileDialog.getOpenFileName(iface.mainWindow(), "Choose CSV WU List to Run", downloads_path ,filter = "Excel (*.csv *.xlsx)")[0])
				wuHeaderFound=False
				csvFound=False
				ExcelFound=False
				if wuListFilePath!="":
					with open(wuListFilePath, 'r') as file:
						#go through WU List csv and get list of WUs and save list
						wu_list=[]
						str_wu_list=''
						try:
							df = pd.ExcelFile(wuListFilePath) #you could add index_col=0 if there's an index
							ExcelFound=True
							print('Excel Found')
						except:
							try:
								df = pd.read_csv(wuListFilePath)
								csvFound=True
								print('CSV Found')
							except:
								print('Error: No CSV or Excel Found')
						#get sheet names and get first sheet name that is not called 'summary'. Sheet name not needed for CSVs
						if csvFound==False and ExcelFound==True:
							sheetNames=df.sheet_names
							sheetName=''
							for s in sheetNames:
								if 'summary' not in str(s).lower():
									sheetName=str(s)
									break
							df = pd.ExcelFile(wuListFilePath).parse(sheetName) #you could add index_col=0 if there's an index
						#get column header for WU_Ids, from csv or excel sheet
						if csvFound==True or ExcelFound==True:
							columnName=''
							headers=list(df.columns.values)
							for h in headers:
								if 'work unit' in str(h).lower() or 'wu' in str(h).lower() or 'work_unit' in str(h).lower() or 'workunit' in str(h).lower():
									columnName=str(h)
									wuHeaderFound=True
									break
							if wuHeaderFound==False:
								errorMessage4 = "No column header found with WU, Work Unit, or Work_Unit in name. Make sure headers are in 1st row, and spelling is ok"
								widget5 = iface.messageBar().createMessage(errorMessage4)
								iface.messageBar().pushWidget(widget5, Qgis.Warning, duration=0)
							else:
								wu_list.append(df[columnName].tolist())
								for wu in wu_list[0]:
									try:
										str_wu_list=str_wu_list+str(int(wu))+','
									except:
										print('cannot convert this row to WU int: ' + str(wu))
								str_wu_list=str_wu_list[0:-1]
								print('string wu list:')
								print(str_wu_list)
						else:
							errorMessage4 = "No CSV or Excel file found."
							widget5 = iface.messageBar().createMessage(errorMessage4)
							iface.messageBar().pushWidget(widget5, Qgis.Warning, duration=0)
			#running query, if WU LIST import successful
			if ((csvFound==True or ExcelFound==True) and wuHeaderFound==True) or (WuTextBoxFound==True):
				print('about to run query')
				#variables
				errorMessage = None
				countNumWus=len(str_wu_list.split(","))
				count_road_units=0
				count_boundaries=0
				count_boundary_points=0
				count_delins=0
				count_paths=0
				count_crossings=0
				count_RO_PM=0
				count_RO_RTD=0
				count_RO_SILOC=0

				#build SQL queries
				sql =   	("with road_units as(SELECT sb.segment_id, sb.start_boundary_id, sb.end_boundary_id, sb.wu_id, sb.replaced_by_wuid, ruType.road_type_name\
					FROM road_unit.segment_boundaries sb\
					INNER JOIN road_unit.segments segs ON sb.segment_id = segs.id\
					INNER JOIN road_unit.road_type_names ruType ON segs.road_type_id = ruType.id\
					WHERE sb.replaced_by_wuid IS NULL\
						AND sb.start_boundary_id IS NOT NULL	\
						AND sb.end_boundary_id IS NOT NULL	\
						AND sb.wu_id IS NOT NULL\
					AND sb.wu_id in ({})),		\
					boundaries as (select ru.start_boundary_id from road_units ru\
								inner join boundary.boundary_points bp\
								on bp.boundary_id = ru.start_boundary_id\
								union\
								select end_boundary_id from road_units ru\
								inner join boundary.boundary_points bp\
								on bp.boundary_id = ru.end_boundary_id\
								),\
					boundary_pts as (select bp.id as boundary_point_id from boundary.boundary_points bp\
									inner join boundaries bds\
									on bds.start_boundary_id = bp.boundary_id \
									union\
									select bp.id from boundary.boundary_points bp\
									inner join boundaries bds\
									on bds.start_boundary_id = bp.boundary_id \
									),\
					distinct_deln as (select d.id as deln_id from delineator.delineators d\
									inner join boundary_pts bp\
									on bp.boundary_point_id = d.start_boundary_point_id\
									union \
									select d.id from delineator.delineators d\
									inner join boundary_pts bp\
									on bp.boundary_point_id = d.end_boundary_point_id\
									),\
					deln_change as (select id as deln_type_chng_id from delineator.delineator_type_changes dtc\
								join distinct_deln dd on dd.deln_id = dtc.delineator_id),\
					distinct_path as (select distinct sp.id as path_id from road_units ru\
									inner join road_unit.segment_paths sp on sp.segment_id = ru.segment_id),\
					path_change as (select id as path_type_chng_id from road_unit.segment_path_type_set_changes sptsc\
								join distinct_path dp on dp.path_id = sptsc.segment_path_id),\
					crossing as (select distinct ac.crossing_id from work_units.associated_crossings ac\
								join road_units ru on ru.wu_id = ac.wu_id),\
					road_object as (select distinct aro.road_object_id, ro.type_name\
									from work_units.associated_road_objects aro\
									join road_object.road_objects ro on ro.id = aro.road_object_id\
									join road_units ru on ru.wu_id = aro.wu_id),\
					intersection_s as (select distinct intseg.intersection_id from road_unit.intersection_segments intseg\
								join road_units ru on ru.segment_id = intseg.segment_id)\
					select count(*) as road_unit_count,\
					(select count(*) from boundaries) as boundary_plane_count, \
					(select count(*) from boundary_pts) as boundary_pt_count,\
					(select count(*) from distinct_deln) as deln_count,\
					(select count(*) from distinct_path) as path_count,\
					(select count(crossing_id) from crossing) as crossing_count,\
					(select count(road_object_id) from road_object where type_name like 'RO_LI%' or type_name like 'RO_RSR%') as rtd_count,\
					(select count(road_object_id) from road_object where type_name like 'RO_OTHER_SILOC') as sign_count,\
					(select count(road_object_id) from road_object where type_name like 'RO_PM%') as pm_count,\
					(select count(intersection_id) from intersection_s) as intersection_count\
					from road_units; ").format(str_wu_list) #good test WU 398194 for Road objects

				####execute sqls and save results###
				conn = psycopg2.connect(host=hostName, port=port, dbname=databaseName, user=username, password=password)
				cur = conn.cursor()

				#execute
				cur.execute(sql)
				results=cur.fetchall()
				print(results)
				if len(results[0])==0:
					message='NO results found '
					print(message)
					resultsFound=False
				else:
					message='FOUND results '
					print(message)
					resultsFound=True
				headers=[]
				for items in cur.description:
					headers.append(str(items.name))

				cur.close()
				conn.close()
				if resultsFound==True:
					#filename
					dateTimeObj = datetime.now()
					timestampStr = dateTimeObj.strftime("%Y%m%d-%H%M%S")
					name='FeatureCount'
					filename=name+'_'+timestampStr+'_WUcount'+str(countNumWus)
					#save Path
					resultsSavePath_Base=str(QgsApplication.qgisSettingsDirPath())
					print(str(resultsSavePath_Base))
					cutPos=resultsSavePath_Base.find('Roaming')
					resultsSavePath_Base=resultsSavePath_Base[0:cutPos]+'Local/Ushr/reports/'
					print(str(resultsSavePath_Base))
					resultsSavePath=resultsSavePath_Base+filename+'.csv'
					print(str(resultsSavePath))

					# open csv, write results to CSV
					try:
						with open(resultsSavePath, 'w', newline='') as csvfile: #str(QgsApplication.qgisSettingsDirPath()) find AppData and
							spamwriter = csv.writer(csvfile, delimiter=',',quotechar='|', quoting=csv.QUOTE_MINIMAL)
							spamwriter.writerow(headers)
							spamwriter.writerows(results)
						message+= ' / Saved Results to: ' + resultsSavePath
						try:
							path = os.path.realpath(resultsSavePath_Base)
							os.startfile(path)
						except:
							message+= ' / Failed to Open Save Folder'
					except:
						message+= ' / Failed to Save Results'

					#display results in QGIS
					count_road_units=results[0][0]
					count_boundaries=results[0][1]
					count_boundary_points=results[0][2]
					count_delins=results[0][3]
					count_paths=results[0][4]
					count_crossings=results[0][5]
					count_RO_RTD=results[0][6]
					count_RO_SILOC=results[0][7]
					count_RO_PM=results[0][8]
					count_intersections=results[0][9]

					#organize results
					summary_message='Summary for WU Count: '+ str(countNumWus) + '\n' + '\n'
					summary_message+='Road Units: '+ str(count_road_units)+ '\n'
					summary_message+='Boundaries: '+ str(count_boundaries)+ '\n'
					summary_message+='Boundary Points: '+ str(count_boundary_points)+ '\n'
					summary_message+='Delineators: '+ str(count_delins)+ '\n'
					summary_message+='Paths: '+ str(count_paths)+ '\n'
					summary_message+='Crossings: '+ str(count_crossings)+ '\n'
					summary_message+='RO RTDs: '+ str(count_RO_RTD)+ '\n'
					summary_message+='RO Siloc: '+ str(count_RO_SILOC)+ '\n'
					summary_message+='RO Pavement Markings: '+ str(count_RO_PM)+ '\n'
					summary_message+='Intersections: '+ str(count_intersections)+ '\n'

					#print results on QMessageBox
					#clear progress bar
					iface.messageBar().clearWidgets()
					#try message dialogue
					from PyQt5.QtWidgets import QMessageBox

					# Create a message box
					msg_box = QMessageBox()

					# Set the title of the message box
					msg_box.setWindowTitle("Summary: WU Feature Counts")

					# Set the text of the message box
					msg_box.setText(summary_message)

					#display Results message
					errorMessage4 = message
					widget5 = iface.messageBar().createMessage(errorMessage4)
					iface.messageBar().pushWidget(widget5, Qgis.Success, duration=10)

					# Set the standard OK button and run the message box
					msg_box.setStandardButtons(QMessageBox.Ok)
					msg_box.exec_()
				else:
					#display Results message
					errorMessage4 = message
					widget5 = iface.messageBar().createMessage(errorMessage4)
					iface.messageBar().pushWidget(widget5, Qgis.Success, duration=10)




		#RFDB feature finder
		elif dropDown_ftr_type == "Road Unit Id:" or dropDown_ftr_type == "WU ID:" or dropDown_ftr_type == "Path Id:"  or dropDown_ftr_type == "Boundary Id:" or dropDown_ftr_type == 'Crossing Id:' or dropDown_ftr_type == 'Delineator Id:' or dropDown_ftr_type == 'Road Object Id:' or dropDown_ftr_type == 'Siloc Id:' or dropDown_ftr_type == 'WU Connection Id:' or dropDown_ftr_type == 'Trail Name:' or dropDown_ftr_type == 'Intersection Id:' or dropDown_ftr_type == 'OSM Intersection Node:' or dropDown_ftr_type == 'Path Type Chg Id:':

			##### connection settings to RFDB #####
			#line below taken from C:\Program Files\QGIS 2.18\apps\qgis-ltr\python\plugins\RoadFeatures\db_interface\db_params_settings.py
			#db_params_settings: This class provides access to persistent database parameters using pyqt QSettings to store the information
			self.settings = QSettings('Geodigital', 'db_params_settings')
			currentConnectionName = str(self.settings.value('current_connection'))
			currentConnection = {}
			currentConnection = self.settings.value('connections')[currentConnectionName]
			username = str(self.settings.value('connections')[currentConnectionName]['user_name'])
			password = str(self.settings.value('connections')[currentConnectionName]['password'])
			databaseName = str(self.settings.value('connections')[currentConnectionName]['database_name'])
			hostName = str(self.settings.value('connections')[currentConnectionName]['server_ip'])
			port = str(self.settings.value('connections')[currentConnectionName]['port'])
			##### END connection settings to RFDB #####

			errorMessage2 = None
			intersectionRemoved=False
			#get text from textbox
			searchingForThis_Feature_ID = self.textbox.text().strip()
			#check if string is digit
			if (searchingForThis_Feature_ID.isdigit() == True) or dropDown_ftr_type == 'Trail Name:':

				#select feature if feature in a layer in layer's panel (i.e. inside a Work Unit)
				foundFeatureToSelect=False
				if dropDown_ftr_type == 'Road Unit Id:':
					queryPrefix = '"segment_id" = '
					groupName="Road Unit Segment"
				elif dropDown_ftr_type == 'Path Id:':
					queryPrefix = '"path_id" = '
					groupName="Path"
				elif dropDown_ftr_type == 'Boundary Id:':
					queryPrefix = '"boundary_id" = '
					groupName="Boundary Planes"
				elif dropDown_ftr_type == 'Crossing Id:':
					queryPrefix = '"crossing_id" = '
					groupName="Path Crossing Regions"
				elif dropDown_ftr_type == 'Delineator Id:':
					queryPrefix = '"delineator_id" = '
					groupName= "Delineators"
				elif dropDown_ftr_type == 'Road Object Id:':
					queryPrefix = '"road_object_id" = '
					groupName= "Road Objects"
				elif dropDown_ftr_type == 'Siloc Id:':
					queryPrefix = '"siloc_sign_id" = '
					groupName= "Road Objects"
				elif dropDown_ftr_type == 'WU Connection Id:':
					queryPrefix = '"id" = '
					groupName= "Work Unit Connections"
				elif dropDown_ftr_type == 'Trail Name:':
					queryPrefix = '"pointcloud_id" = '
					groupName= "Pointcloud Acquisition Trail"
					print('set query and group name for Trail Name')
				elif dropDown_ftr_type == "WU ID:":
					queryPrefix = '"work_unit_id" = '
					groupName="Work Units"
				elif dropDown_ftr_type == 'Intersection Id:':
					queryPrefix = '"intersection_id" = '
					groupName= "Road Unit Intersection"
				elif dropDown_ftr_type == 'OSM Intersection Node:':
					queryPrefix = '"node_id" = '
					groupName= "OSM"
				elif dropDown_ftr_type =='Path Type Chg Id:':
					queryPrefix = '"type_change_id" = '
					groupName= "Path Types"
				root = QgsProject.instance().layerTreeRoot()
				for lyr in root.findLayers():
					try:
						if dropDown_ftr_type != 'Trail Name:' and dropDown_ftr_type != 'WU Connection Id:' and dropDown_ftr_type != 'OSM Intersection Node:' and dropDown_ftr_type != "WU ID:":	#exclude non-grouped layers that have search drop-down menu
							print('looking in layer groups')
							my_layer = lyr.layer()
							tree_layer = root.findLayer(my_layer.id())
							if tree_layer:
								layer_parent = tree_layer.parent()
								if layer_parent:
									group_parent = layer_parent.parent()
							print("Checking. If parent's name is not Nearby Features")
							if group_parent.name()!="Nearby Features":
								if groupName == lyr.name():
									query4 = queryPrefix + str(searchingForThis_Feature_ID)
									selection4 = lyr.layer().getFeatures(QgsFeatureRequest().setFilterExpression(query4))
									iteratorList=list(selection4)
									print(len(iteratorList))
									if len(iteratorList)!=0:
										print("FEATURE FOUND in a non-'Nearby Features' attribute table")
										foundFeatureToSelect=True
										for lyr2 in QgsProject.instance().layerTreeRoot().findLayers():
											try:
												lyr2.layer().removeSelection()
											except:
												continue
										lyr.layer().selectByIds([k.id() for k in iteratorList])
										iface.mapCanvas().zoomToSelected(lyr.layer())
										iface.mapCanvas().zoomScale(250.0) #ok
										break
						else:														#for non-grouped layers that have search drop-down menu
							if str(lyr.name()) == str(groupName):
								print('looking at layer with root parent called: ' + str(lyr.name()))
								query4 = queryPrefix + str(searchingForThis_Feature_ID)
								if dropDown_ftr_type == 'Trail Name:': #for strings, not integer values
									query4 = queryPrefix + str("'"+searchingForThis_Feature_ID+"'")
								selection4 = lyr.layer().getFeatures(QgsFeatureRequest().setFilterExpression(query4))
								iteratorList=list(selection4)
								print(len(iteratorList))
								if len(iteratorList)!=0:
									print("FEATURE FOUND in a non-'Nearby Features' attribute table")
									foundFeatureToSelect=True
									for lyr2 in QgsProject.instance().layerTreeRoot().findLayers():
										try:
											lyr2.layer().removeSelection()
										except:
											continue
									lyr.layer().selectByIds([k.id() for k in iteratorList])
									iface.mapCanvas().zoomToSelected(lyr.layer())
									if dropDown_ftr_type != "WU ID:" and dropDown_ftr_type != "Trail Name:":
										iface.mapCanvas().zoomScale(250.0)
									else: #if dropDown_ftr_type == WU ID:
										#zoom to show full extent of WU geom
										print('zoom to show full extent of WU geom')
										canvas = iface.mapCanvas()
										layer = iface.activeLayer()
										if layer.selectedFeatureCount() > 0:
											extent = layer.selectedFeaturesBoundingBox()
											canvas.setExtent(extent)
											canvas.refresh()
									break
					except:
						continue
				#if feature NOT in a layer in layer's panel (i.e. outside a Work Unit)
				if foundFeatureToSelect==False:
					print("NO FEATURE FOUND in non-'Nearby Features' attribute tables")
					conn = psycopg2.connect(host=hostName, port=port, dbname=databaseName, user=username, password=password)
					cur = conn.cursor()
					print('CONNECTION DETAILS')
					print('host ' + str(hostName) + ' dbname: '+str(databaseName))
					tableString = None
					# get the current drop-down menu selection as a text string
					if dropDown_ftr_type =='Boundary Id:':
						tableString = "b.boundary_id"
					elif dropDown_ftr_type =='Delineator Id:':
						tableString = "d.id"
					#build and execute SQL query
					sql =   ("SELECT DISTINCT w.id, w.subcountry, REPLACE(TRIM('POINT(,)' FROM ST_ASTEXT(ST_CENTROID(ST_ASTEXT(p.envelope)))),' ', ',')  as onePaths_centroid, REPLACE(TRIM('POINT(,)' FROM ST_ASTEXT(ST_CENTROID(ST_ASTEXT(bo.nominal_location)))),' ', ',') as bndry_centroid, sb0.replaced_by_wuid \
					FROM work_units.work_unit w \
					FULL OUTER JOIN work_units.associated_boundaries ab ON ab.wu_id = w.id \
					FULL OUTER JOIN work_units.associated_boundaries ab2 ON ab2.wu_id = w.id \
					FULL OUTER JOIN boundary.boundary_points b ON ab.boundary_id = b.boundary_id \
					FULL OUTER JOIN boundary.boundaries bo ON bo.id = b.boundary_id \
					FULL OUTER JOIN boundary.boundary_points b2 ON ab2.boundary_id = b2.boundary_id \
					FULL OUTER JOIN delineator.delineators d ON d.start_boundary_point_id = b.id and d.end_boundary_point_id = b2.id \
					FULL OUTER JOIN path.paths p ON p.left_delineator_id = d.id \
					FULL OUTER JOIN road_unit.segment_paths sp ON sp.id = p.id \
					FULL OUTER JOIN road_unit.segment_boundaries sb0 on sb0.segment_id = sp.segment_id \
					WHERE {} = {} ; ").format(tableString, searchingForThis_Feature_ID)
					#replace sql for certain drop-down menu options
					if dropDown_ftr_type == 'Road Unit Id:':
						sql =   ("SELECT DISTINCT sp.segment_id, sb0.start_boundary_id, sb0.end_boundary_id, sb0.replaced_by_wuid, REPLACE(TRIM('POINT(,)' FROM st_astext(st_centroid(st_astext(p.envelope)))),' ', ','), sb0.wu_id, w0.subcountry, ab.wu_id, w.subcountry \
						, (SELECT array_agg(distinct sh.new_segment) FROM road_unit.segment_history sh INNER JOIN road_unit.segment_paths sp on sp.segment_id = sh.new_segment  \
						where old_segment={})  \
						, REPLACE(TRIM('POINT(,)' FROM st_astext(st_centroid(st_astext(b.nominal_location)))),' ', ',') \
						FROM road_unit.segments s \
						FULL OUTER JOIN road_unit.segment_paths sp on sp.segment_id = s.id \
						FULL OUTER JOIN path.paths p on sp.id = p.id \
						FULL OUTER JOIN road_unit.segment_boundaries sb0 on sb0.segment_id = s.id  \
						FULL OUTER JOIN work_units.work_unit w0 on w0.id = sb0.wu_id  \
						FULL OUTER JOIN delineator.delineators d on d.id = p.left_delineator_id  \
						FULL OUTER JOIN boundary.boundary_points bp on bp.id = d.start_boundary_point_id  \
						FULL OUTER JOIN work_units.associated_boundaries ab on ab.boundary_id = bp.boundary_id  \
						FULL OUTER JOIN work_units.work_unit w on w.id = ab.wu_id  \
						FULL OUTER JOIN boundary.boundary_points bp2 on bp2.id = d.end_boundary_point_id  \
						FULL OUTER JOIN work_units.associated_boundaries ab2 on ab2.boundary_id = bp2.boundary_id  \
						FULL OUTER JOIN work_units.work_unit w2 on w2.id = ab2.wu_id \
						FULL OUTER JOIN boundary.boundaries b on sb0.start_boundary_id=b.id \
						WHERE s.id={} ; ").format(searchingForThis_Feature_ID, searchingForThis_Feature_ID)
					elif dropDown_ftr_type == 'Path Id:':
						sql =   ("SELECT p.id, p.left_delineator_id, p.right_delineator_id, REPLACE(TRIM('POINT(,)' FROM st_astext(st_centroid(st_astext(p.envelope)))),' ', ','), sp.segment_id, sb0.wu_id, w0.subcountry, ab.wu_id, w.subcountry,ab2.wu_id,sb0.replaced_by_wuid \
						FROM path.paths p \
						FULL OUTER JOIN road_unit.segment_paths sp on sp.id = p.id \
						FULL OUTER JOIN road_unit.segment_boundaries sb0 on sb0.segment_id = sp.segment_id \
						FULL OUTER JOIN work_units.work_unit w0 on w0.id = sb0.wu_id \
						FULL OUTER JOIN delineator.delineators d on d.id = p.left_delineator_id \
						FULL OUTER JOIN boundary.boundary_points bp on bp.id = d.start_boundary_point_id \
						FULL OUTER JOIN work_units.associated_boundaries ab on ab.boundary_id = bp.boundary_id \
						FULL OUTER JOIN work_units.work_unit w on w.id = ab.wu_id \
						FULL OUTER JOIN boundary.boundary_points bp2 on bp2.id = d.end_boundary_point_id \
						FULL OUTER JOIN work_units.associated_boundaries ab2 on ab2.boundary_id = bp2.boundary_id \
						FULL OUTER JOIN work_units.work_unit w2 on w2.id = ab2.wu_id \
						WHERE p.id={} ; ").format(searchingForThis_Feature_ID)
					elif dropDown_ftr_type == 'Crossing Id:':
						sql =   ("SELECT ac.wu_id, c.id, REPLACE(TRIM('POINT(,)' FROM ST_ASTEXT(ST_CENTROID(ST_ASTEXT(c.start_line)))),' ', ','), w.subcountry \
						FROM crossing.crossings c \
						FULL OUTER JOIN work_units.associated_crossings ac on c.id=ac.crossing_id\
						FULL OUTER JOIN work_units.work_unit w on w.id = ac.wu_id \
						WHERE c.id={} ;").format(searchingForThis_Feature_ID)
					elif dropDown_ftr_type == 'Road Object Id:':
						sql =   ("SELECT aro.wu_id, ro.id, REPLACE(TRIM('POINT(,)' FROM ST_ASTEXT(ST_CENTROID(ST_ASTEXT(ro.location)))),' ', ','), w.subcountry  \
						FROM road_object.road_objects ro \
						FULL OUTER JOIN work_units.associated_road_objects aro on ro.id=aro.road_object_id \
						FULL OUTER JOIN work_units.work_unit w on w.id = aro.wu_id  \
						WHERE ro.id={} ;").format(searchingForThis_Feature_ID)
					elif dropDown_ftr_type == 'Siloc Id:':
						sql =   ("SELECT aro.wu_id, ro.id, REPLACE(TRIM('POINT(,)' FROM ST_ASTEXT(ST_CENTROID(ST_ASTEXT(ro.location)))),' ', ','), w.subcountry,ros.sign_id \
						FROM road_object.road_objects ro \
						INNER JOIN road_object.road_object_signs ros on ros.road_object_id = ro.id \
						FULL OUTER JOIN work_units.associated_road_objects aro on ro.id=aro.road_object_id \
						FULL OUTER JOIN work_units.work_unit w on w.id = aro.wu_id   \
						WHERE ros.sign_id={} ;").format(searchingForThis_Feature_ID)
					elif dropDown_ftr_type ==  'WU Connection Id:':
						sql =   ("SELECT id, from_wuid, to_wuid, REPLACE(TRIM('POINT(,)' FROM ST_ASTEXT(ST_CENTROID(ST_ASTEXT(geom)))),' ', ','), from_subcountry, to_subcountry, description, bypass, boundary_id, connection_type \
						FROM work_units.wu_connections where id={} ;").format(searchingForThis_Feature_ID)
					elif dropDown_ftr_type ==  'Trail Name:':
						sql =   ("SELECT id, name, REPLACE(TRIM('POINT(,)' FROM ST_ASTEXT(ST_StartPoint(ST_GeometryN(wkb_geometry::geometry, 1)))), ' ', ',') \
						FROM acquisition_trail.trails \
						where name ilike '%{}%';").format(searchingForThis_Feature_ID)
					elif dropDown_ftr_type == "WU ID:":
						sql =   ("SELECT id, subcountry, REPLACE(TRIM('POINT(,)' FROM ST_ASTEXT(ST_StartPoint(ST_GeometryN(geom, 1)))), ' ', ',') \
						FROM work_units.work_unit where id={} ;").format(searchingForThis_Feature_ID)
					elif dropDown_ftr_type ==  'OSM Intersection Node:':
						sql =   ("SELECT oi.node_id, REPLACE(TRIM('POINT(,)' FROM ST_ASTEXT(ST_CENTROID(ST_ASTEXT(nodes.geom)))),' ', ','), oi.connection_type \
						FROM osm_views.osm_intersections oi \
						INNER JOIN osm_views.nodes ON oi.node_id = nodes.id and oi.node_id = {} ;").format(searchingForThis_Feature_ID)
					elif dropDown_ftr_type == 'Intersection Id:':
						sql =   ("SELECT w.id, i.id, REPLACE(TRIM('POINT(,)' FROM ST_ASTEXT(ST_CENTROID(ST_ASTEXT(i.envelope)))),' ', ','), w.subcountry, count(distinct sp.id), count(distinct sb.segment_id), array_agg(REPLACE(TRIM('POINT(,)' FROM ST_ASTEXT(ST_CENTROID(ST_ASTEXT(b.nominal_location)))),' ', ','))\
						FROM road_unit.intersections i\
						INNER JOIN road_unit.intersection_segments iseg on iseg.intersection_id =  i.id\
						INNER JOIN road_unit.segment_boundaries sb on sb.segment_id = iseg.segment_id\
						INNER JOIN work_units.work_unit w on w.id = sb.wu_id \
						full outer join road_unit.segment_paths sp on sp.segment_id = sb.segment_id \
						full outer join boundary.boundaries b on sb.start_boundary_id = b.id \
						WHERE i.id ={} \
						GROUP BY w.id, i.id  \
						ORDER BY w.id asc;").format(searchingForThis_Feature_ID)
					elif dropDown_ftr_type == 'Path Type Chg Id:':
						sql =   ("SELECT w.id, sptsc.id, REPLACE(TRIM('POINT(,)' FROM ST_ASTEXT(ST_CENTROID(ST_ASTEXT(sptsc.location)))),' ', ','), w.subcountry  \
						FROM path.paths p  \
						INNER JOIN road_unit.segment_paths sp ON sp.id = p.id  \
						INNER JOIN segment_path_type.segment_path_type_sets_members sptsm ON sp.start_type_set_id = sptsm.segment_path_type_set_id  \
						INNER JOIN segment_path_type.segment_path_types spt ON sptsm.segment_path_type_id = spt.id  \
						INNER JOIN road_unit.segment_boundaries sb ON sp.segment_id = sb.segment_id  \
						FULL OUTER JOIN road_unit.segment_path_type_set_changes sptsc on sptsc.segment_path_id = p.id  \
						FULL OUTER JOIN segment_path_type.segment_path_type_sets_members sptsm2 ON sptsc.path_type_set_id = sptsm2.segment_path_type_set_id  \
						FULL OUTER JOIN segment_path_type.segment_path_types spt2 ON sptsm2.segment_path_type_id = spt2.id  \
						FULL OUTER JOIN road_unit.segments s ON s.id = sp.segment_id  \
						FULL OUTER JOIN work_units.work_unit w ON sb.wu_id = w.id  \
						WHERE sptsc.id={} ;").format(searchingForThis_Feature_ID)
					cur.execute(sql)
					#save results, depending on drop-down menu selection
					if dropDown_ftr_type != 'Intersection Id:':
						result = cur.fetchone()
						print('Results=' + str(result))
					else:
						print('intersection check')
						i_results=cur.fetchall()
						if len(i_results) !=0:
							intersectionRemoved=False
							countPaths=0
							countRus=0
							row_withMostRus=0
							prevCountRus=0
							#otherWUs_HavingIntersection=''
							for i,row in enumerate(i_results):
								countPaths = countPaths+row[4]
								#set countRus
								if countPaths==0:
									countRus=0
								else:
									countRus=row[5]
								if countRus>=prevCountRus:
									row_withMostRus = i
								prevCountRus=countRus
								'''if i>0:
									otherWUs_HavingIntersection+= (str(row[0]) + ' ')'''
							if countPaths==0:
								intersectionRemoved=True
							result=i_results[row_withMostRus]
						else:
							print('no rows. Intersection not found')
							result=None
						print('end Intersction check')

					#closing connection and cursor
					cur.close()
					conn.close()
					#result found
					if result is not None:
						print('result is NOT null')
						cnt=len(result)
						print('num cells in row returned from query (if 0 then no row returned): '+str(cnt))
						#check if raster layer exists to pan
						rasterLayerFoundText = None
						count=0
						wu=None
						ru_HasExistingSegId_ButNoPaths=False
						useBoundaryGeom=False
						ru_HasHadBoundaryInserted_AndOneOfItsNewRus_StillExists=False
						hasReplacedByWuid=False
						#for layers in QGIS registry
						for lyr in QgsProject.instance().mapLayers().values():
							#if layers are not Raster
							if lyr.type() == QgsMapLayer.RasterLayer:
								count=count+1
						if count == 0:
							print('-1')
							rasterLayerFoundText = ' No Raster Layer Found for Panning to RU.'
						print('0')
						#pan to Coordinates
						if dropDown_ftr_type == 'Road Unit Id:':
							print('1')
							if result[0] is not None:
								coords= str(result[4])
								print('2')
							else:
								ru_HasExistingSegId_ButNoPaths=True
								useBoundaryGeom=True
								coords= str(result[10])
								print('3')
							if result[5] is not None:
								wu=str(result[5])
								sbcntry=str(result[6])
								print('4')
							else:
								wu='000_wuFieldIsNull_000'
								sbcntry=''
								print('5')
							if result[9] is not None:
								ru_HasHadBoundaryInserted_AndOneOfItsNewRus_StillExists=True
								print('6')
							if result[3] is not None:
								replacedByWuid=str(result[3])
								hasReplacedByWuid=True
								print('7')
							else:
								replacedByWuid='null'
								print('8')
						elif dropDown_ftr_type == 'Path Id:':
							coords= str(result[3])
							if result[5] is not None:
								wu=str(result[5])
								sbcntry=str(result[6])
							else:
								wu='000_wuFieldIsNull_000'
								sbcntry=''
							if result[10] is not None:
								replacedByWuid=str(result[10])
								hasReplacedByWuid=True
							else:
								replacedByWuid='null'
						elif dropDown_ftr_type == 'Boundary Id:':
							coords= str(result[3])
							wu=str(result[0])
							sbcntry=str(result[1])
						elif dropDown_ftr_type == 'Crossing Id:':
							coords= str(result[2])
							wu=str(result[0])
							sbcntry=str(result[3])
						elif dropDown_ftr_type == 'Delineator Id:':
							if result[0] is not None:
								coords= str(result[3])
								wu=str(result[0])
								sbcntry=str(result[1])
							else:
								coords= str(result[2])
								wu='000_wuFieldIsNull_000'
								sbcntry=''
							if result[4] is not None:
								replacedByWuid=str(result[4])
								hasReplacedByWuid=True
							else:
								replacedByWuid='null'
						elif dropDown_ftr_type == 'Road Object Id:':
							coords= str(result[2])
							wu=str(result[0])
							sbcntry=str(result[3])
						elif dropDown_ftr_type == 'Siloc Id:':
							coords= str(result[2])
							wu=str(result[0])
							sbcntry=str(result[3])
						elif dropDown_ftr_type == 'Trail Name:':
							coords= str(result[2])
							wu='Null'
							sbcntry='Null'
						elif dropDown_ftr_type == 'WU Connection Id:':
							coords= str(result[3])
							wu=str(result[1])
							sbcntry=str(result[4])
						elif dropDown_ftr_type == "WU ID:":
							coords= str(result[2])
							wu=str(result[0])
							sbcntry=str(result[1])
						elif dropDown_ftr_type == 'OSM Intersection Node:':
							coords= str(result[1])
							connection_type=''
							if result[2]==0:
								connection_type='in-out'
							elif result[2]==1:
								connection_type='in-in'
							else:
								connection_type='not found'
							wu=str("")
							sbcntry=str("")
						elif dropDown_ftr_type == 'Intersection Id:':
							if result[2] is not None:
								coords= str(result[2])
							else:
								print('No Intersection Geom. Going to first start_boundary geom found from list of former RUs in intersection.')
								coords= str(result[6][0])
							wu=str(result[0])
							sbcntry=str(result[3])
						elif dropDown_ftr_type == 'Path Type Chg Id:':
							coords= str(result[2])
							wu=str(result[0])
							sbcntry=str(result[3])
						#pan/zoom if ru has paths or boundary usable
						if (ru_HasExistingSegId_ButNoPaths==False or useBoundaryGeom==True) and ru_HasHadBoundaryInserted_AndOneOfItsNewRus_StillExists ==False:
							coordsX = float(coords.split(',')[0])
							coordsY = float(coords.split(',')[1])
							coords2Point = QgsPointXY(coordsX, coordsY)
							iface.mapCanvas().setCenter(coords2Point)
							iface.mapCanvas().refresh()
							rasterLayerFoundText = ' Panned to location'
							#zoom to scale
							if dropDown_ftr_type != "WU ID:" and dropDown_ftr_type != "Trail Name:":
								iface.mapCanvas().zoomScale(250.0)
							else:
								iface.mapCanvas().zoomScale(4000.0)
						#select WU or RU, if possible
						queryWu=wu
						#if hasReplacedByWuid==True:
						#	queryWu=replacedByWuid
						for lyr in QgsProject.instance().mapLayers().values():
							if "Work Units" in lyr.name():
								query3 = '"work_unit_id" = ' + queryWu
								selection3 = lyr.getFeatures(QgsFeatureRequest().setFilterExpression(query3))
								lyr.selectByIds([k.id() for k in selection3])
						print(wu)
						#display message
						if ru_HasExistingSegId_ButNoPaths==False or useBoundaryGeom==True:
							#if not zombie
							if wu!='000_wuFieldIsNull_000' or (wu=='000_wuFieldIsNull_000' and ru_HasHadBoundaryInserted_AndOneOfItsNewRus_StillExists==True):
								errorType=Qgis.Success
								duration=5
								if useBoundaryGeom==True:
									errorMessage2='RU found to be REMOVED. Formerly:  ' + sbcntry + ' Work Unit: ' + wu+'. Panned to former start_boundary= '+str(result[1])
									errorType=Qgis.Warning
									duration=7
									if ru_HasHadBoundaryInserted_AndOneOfItsNewRus_StillExists==True:
										duration=0
										errorMessage2="RU no longer exists. Likely had a BOUNDARY INSERTED or DELIN STITCHING. Replaced By RUs (That Still Exist): "+ str(result[9])+'. Panned, if able.'
								elif hasReplacedByWuid==True:
									errorType=Qgis.Warning
									errorMessage2 = 'REPLACED_BY_WUID=' + replacedByWuid + '.  Formerly: '+sbcntry + ' Work Unit: ' + wu
									duration=7
									print('9')
								elif intersectionRemoved==True:
									errorMessage2='Intersection found to be REMOVED. Formerly:  ' + sbcntry + ' Work Unit: ' + wu+'. Panned to former location if possible.'
									errorType=Qgis.Warning
									duration=7
								elif dropDown_ftr_type == 'OSM Intersection Node:':
									errorMessage2 = 'FOUND ' +str(connection_type) + ' Intersection Node ID (OSM): ' + str(searchingForThis_Feature_ID)
								elif dropDown_ftr_type == 'Trail Name:':
									errorMessage2 = 'FOUND Trail Name: ' + str(searchingForThis_Feature_ID) + '. Zooming to Start Point.'
								else:
									errorMessage2 = sbcntry + ' Work Unit: ' + wu
									'''if dropDown_ftr_type == 'Intersection Id:':
										if otherWUs_HavingIntersection != '':
											errorMessage2+= '. Also, in WUs: ' + otherWUs_HavingIntersection'''
								widget5 = iface.messageBar().createMessage(errorMessage2)
								iface.messageBar().pushWidget(widget5, errorType, duration=duration)
							#zombie
							else:
								if hasReplacedByWuid==False:
									errorMessage2 = "ZOMBIE: ID found, but NO associated WU id found." + str(rasterLayerFoundText)
									duration=5
								else:
									errorMessage2 = 'REPLACED_BY_WUID=' + replacedByWuid + ". "+str(rasterLayerFoundText)+". And a ZOMBIE (likely ok because it has a replaced_by_wuid)."
									duration=7
								widget5 = iface.messageBar().createMessage(errorMessage2)
								iface.messageBar().pushWidget(widget5, Qgis.Warning, duration=duration)


						else:
							errorMessage2 = "Could not find: " + searchingForThis_Feature_ID
							#display message
							widget5 = iface.messageBar().createMessage(errorMessage2)
							iface.messageBar().pushWidget(widget5, Qgis.Warning, duration=3)
					#no results found
					else:
						print('result returned null')
						errorMessage2 = "Could not find: " + searchingForThis_Feature_ID
						#display message
						widget5 = iface.messageBar().createMessage(errorMessage2)
						iface.messageBar().pushWidget(widget5, Qgis.Warning, duration=3)
			#not digits only
			else:
				errorMessage2 = "Please enter digits only!"  #ok
				#display warning
				widget5 = iface.messageBar().createMessage(errorMessage2)
				iface.messageBar().pushWidget(widget5, Qgis.Warning,duration=3)
			print("Finished looking for feature")
			if dropDown_ftr_type == 'WU ID:':
				print('show all WU style rules')
				layer = iface.activeLayer()
				rules = layer.renderer().rootRule().children()
				for rule in rules:
					rule.setActive(True)
				iface.layerTreeView().refreshLayerSymbology(layer.id())
				layer.triggerRepaint()

		elif dropDown_ftr_type =='Lidar SHPs for WU:':
			'''Gets work unit lidar extents, and loads as shapefile layers in QGIS 3'''
			searchingForThis_Feature_ID=self.textbox.text().strip()
			#check if string is digit
			if searchingForThis_Feature_ID.isdigit() == True:
				### START RFDB connection lsettings ###
				self.settings = QSettings('Geodigital', 'db_params_settings')
				currentConnectionName = str(self.settings.value('current_connection'))
				currentConnection = {}
				currentConnection = self.settings.value('connections')[currentConnectionName]
				username = str(self.settings.value('connections')[currentConnectionName]['user_name'])
				password = str(self.settings.value('connections')[currentConnectionName]['password'])
				databaseName = str(self.settings.value('connections')[currentConnectionName]['database_name'])
				hostName = str(self.settings.value('connections')[currentConnectionName]['server_ip'])
				port = str(self.settings.value('connections')[currentConnectionName]['port'])
				### END RFDB connection settings ###

				print("Connecting to Host")
				conn = psycopg2.connect(host=hostName, port=port, dbname=databaseName, user=username, password=password)
				cur = conn.cursor()
				sql = (f"SELECT * FROM work_units.wu_point_cloud \
					WHERE wu_id = {searchingForThis_Feature_ID};")

				print("Executing Query")
				cur.execute(sql)
				result = cur.fetchall()
				#closing connection and cursor
				cur.close()
				conn.close()
				print(result)

				#creating layers
				print("Creating Layer(s)")
				#set active layer to top layer so that loaded layers get loaded on top
				try:
					iface.setActiveLayer(QgsProject.instance().layerTreeRoot().children()[0].layer())
				except:
					print("Top layer is a group, not a layer. Could not load layer to top of Layers Panel")
				SHP_basePath="P:/sea2sea/acquisition_001/point_cloud/"
				SHP_basePath_CM="P:/sea2sea/acquisition_001/point_cloud_CM/"
				SHP_Path=None
				SHP_Path_CM=None
				for pointCloudName in result:
					SHP_Path_CM = SHP_basePath_CM+str(pointCloudName[2])+".shp"
					SHP_Path = SHP_basePath+str(pointCloudName[2])+".shp"
					if os.path.isfile(SHP_Path_CM):
						layer2 = QgsVectorLayer(SHP_Path_CM, str(pointCloudName[2]), "ogr")
					elif os.path.isfile(SHP_Path):
						layer2 = QgsVectorLayer(SHP_Path_CM, str(pointCloudName[2]), "ogr")

					features = layer2.getFeatures()
					geoms = QgsGeometry().fromWkt('GEOMETRYCOLLECTION()')
					for feature in features:
						geoms = geoms.combine(feature.geometry())
						#layer2.deleteFeature(feature.id())
					#layer2.addAttribute(QgsField("TrailName", QVariant.String))
					iface.mainWindow().blockSignals(True)
					crs_authid = iface.mapCanvas().mapSettings().destinationCrs().authid()
					my_layer = QgsVectorLayer('Polygon', str(pointCloudName[2]), 'memory')
					my_layer.setCrs(QgsCoordinateReferenceSystem(crs_authid))
					pr = my_layer.dataProvider()
					pr.addAttributes([QgsField("TrailName", QVariant.String)])
					my_layer.updateFields()
					feature = QgsFeature(my_layer.fields())
					feature.setGeometry(geoms)
					feature.setAttribute("TrailName", str(pointCloudName[2]))
					pr.addFeatures([feature])
					#style
					alphaOpaque=',255'
					alphaSeeThrough=',100'
					randomColor=str(random.randint(0, 255))+','+str(random.randint(0, 255))+','+str(random.randint(0, 255))
					symbol = QgsFillSymbol.createSimple({'color': randomColor+alphaSeeThrough,'outline_color': randomColor+alphaOpaque, 'outline_style': 'solid', 'outline_width': '1'}) #str(random.randint(0, 255))
					renderer = QgsSingleSymbolRenderer(symbol)
					#lables
					layer_settings  = QgsPalLayerSettings()
					text_format = QgsTextFormat()
					text_format.setFont(QFont("Arial", 12))
					text_format.setSize(12)
					buffer_settings = QgsTextBufferSettings()
					buffer_settings.setEnabled(True)
					buffer_settings.setSize(1)
					buffer_settings.setColor(QColor("white"))
					text_format.setBuffer(buffer_settings)
					layer_settings.setFormat(text_format)
					layer_settings.fieldName = "TrailName"
					layer_settings.enabled = True
					layer_settings = QgsVectorLayerSimpleLabeling(layer_settings)
					my_layer.setLabelsEnabled(True)
					my_layer.setLabeling(layer_settings)
					my_layer.triggerRepaint()

					my_layer.setRenderer(renderer)
					iface.mapCanvas().setDestinationCrs(QgsCoordinateReferenceSystem(crs_authid))
					QgsProject.instance().addMapLayer(my_layer, True)
					iface.mainWindow().blockSignals(False)
			else:
				errorMessage2 = "Please enter digits only!"  #ok
				#display warning
				widget5 = iface.messageBar().createMessage(errorMessage2)
				iface.messageBar().pushWidget(widget5, Qgis.Warning,duration=3)

		elif dropDown_ftr_type =='WU Assigned Lidar:':
			searchingForThis_Feature_ID=self.textbox.text().strip()
			#check if string is digit
			if searchingForThis_Feature_ID.isdigit() == True:
				'''
				#connect to local host
				##### connection settings to local host #####
				currentConnection = '127.0.0.1'
				username = 'postgres'
				password = 'Passw0rd!'
				databaseName = 'road_features'
				hostName = 'localhost'
				port = '5432'
				##### END connection settings to local host #####
				'''
				### START RFDB connection lsettings ###
				self.settings = QSettings('Geodigital', 'db_params_settings')
				currentConnectionName = str(self.settings.value('current_connection'))
				currentConnection = {}
				currentConnection = self.settings.value('connections')[currentConnectionName]
				username = str(self.settings.value('connections')[currentConnectionName]['user_name'])
				password = str(self.settings.value('connections')[currentConnectionName]['password'])
				databaseName = str(self.settings.value('connections')[currentConnectionName]['database_name'])
				hostName = str(self.settings.value('connections')[currentConnectionName]['server_ip'])
				port = str(self.settings.value('connections')[currentConnectionName]['port'])
				### END RFDB connection settings ###

				print("Connecting to Host")
				conn = psycopg2.connect(host=hostName, port=port, dbname=databaseName, user=username, password=password)
				cur = conn.cursor()
				sql = (f"SELECT pc_id \
					, (SELECT count(*) \
					FROM external_data_metadata.pointcloud_acquisitions \
					WHERE pointcloud_id = pc_id) as rows_preprocessed \
					FROM work_units.wu_point_cloud  \
					WHERE wu_id = {searchingForThis_Feature_ID};")

				print("Executing Query")
				cur.execute(sql)
				result = cur.fetchall()
				#closing connection and cursor
				cur.close()
				conn.close()
				print(result)
				transformedResult = "Assigned Lidar for WU "+ str(searchingForThis_Feature_ID) + ' ['+str(len(result))+']: '
				count=0
				for results in result:
					count+=1
					transformedResult+=str(count)+'.) '
					transformedResult+= str(results[0])
					if results[1]>0:
						transformedResult+=', '
					else:
						transformedResult+='0 Rows], '
				transformedResult=transformedResult[:-2]
				errorMessage2 = transformedResult
				#display warning
				widget5 = iface.messageBar().createMessage(errorMessage2)
				widget5.layout
				iface.messageBar().pushWidget(widget5, Qgis.Info,duration=0)
				#display dialog # WARNING
				msg=QMessageBox()
				msg.setText("Test")
				msg.show()
			else:
				errorMessage2 = "Please enter digits only!"  #ok
				#display warning
				widget5 = iface.messageBar().createMessage(errorMessage2)
				iface.messageBar().pushWidget(widget5, Qgis.Warning,duration=3)

	def onRunShowRastersOnly(self):
		####QGIS 3 IN Work: NEW LOGIC###
		#variable(s)
		onRunShowRastersOnlyThemeExists=False
		nameOfTheme="Show_Rasters_Only_On"
		theme=None
		root = QgsProject.instance().layerTreeRoot()
		OFF=0
		ON=1
		#save list of existing themes
		existingThemes=QgsProject.instance().mapThemeCollection().mapThemes()
		#debug
		#print("Existing Themes from QgsProject.instance().mapThemeCollection().mapThemes(): ")
		#print (existingThemes)

		#detect if certain theme name exists in existing themes
		for themes in existingThemes:
			if themes == nameOfTheme:
				onRunShowRastersOnlyThemeExists=True
		#if certain theme DOESN'T exists:
		if onRunShowRastersOnlyThemeExists==False:
			#print("Theme called '"+nameOfTheme+"' does NOT exist")
			print("Saving current visibility in theme called: " + nameOfTheme)
			theme=QgsProject.instance().mapThemeCollection().createThemeFromCurrentState(root, QgsLayerTreeModel(root))
			QgsProject.instance().mapThemeCollection().insert(nameOfTheme,theme)

			print("Turning off visibility of non-raster layers")
			for lyr2 in root.findLayers():
				#print ( lyr2.children())
				type=-1
				#print(lyr2.name())
				#print(lyr2.layerId())
				try:
					type=lyr2.layer().type()
					#print(lyr2.layer().type())
				except:
					#print("Not a QgsLayerTreeLayer\n")
					continue
				if type!=-1:
					if type==0:
						QgsProject.instance().layerTreeRoot().findLayer(lyr2.layerId()).setItemVisibilityChecked(OFF)
		#else, if theme DOES exist:
		else:
			#debug
			#print("Theme called '"+nameOfTheme+"' exists")
			print("Restoring Non-Raster Visibility")
			QgsProject.instance().mapThemeCollection().applyTheme(nameOfTheme,root, QgsLayerTreeModel(root))
			#print("Deleting theme")
			QgsProject.instance().mapThemeCollection().removeMapTheme(nameOfTheme)

	def onRunFilterFeature(self):
		'''Filter out a single road unit and its associated features when clicked on that road unit. To get it back, click somewhere else where no other RU is. '''
		#below 3 lines got crosshair mapTool to show up in QGIS after clicking on ruFilter plugin button (and loading Google Sat into QGIS)!
		self.clickTool = QgsMapToolEmitPoint(self.iface.mapCanvas())
		self.clickTool.canvasClicked.connect(self.filterRuByMouseClick)
		self.iface.mapCanvas().setMapTool(self.clickTool)

	def view3dLidar(self, point, mouse_button):
		#import pptk
		print("..Running def view3DLidar(self, point, mouse_button)")
		from liblas import file
		#get lidar SHP layer previously loaded, to find lidar blocks containing click point location
		for lyr in QgsProject.instance().layerTreeRoot().findLayers():
			if '3D_Viewer_' in lyr.name():
				lidar_shp_layer=lyr.layer()
				lidar_name=lyr.name().replace('3D_Viewer_','')
		print("3D_Viewer_ Layer, found after click: "+str(lidar_shp_layer.name()))
		#getLazDir
		rootDir='P:/CSAV3/acquisition_data/point_clouds/'   ####assumes root directory is this P: drive location
		lazDir=None
		list_subfolders_with_paths = [f.path for f in os.scandir(rootDir) if f.is_dir()]
		for subfolderPath in list_subfolders_with_paths:
			potentialLazPath=str(subfolderPath) +"/" + lidar_name +".laz"
			if os.path.isfile(potentialLazPath):
				lazDir=potentialLazPath
				break
		print("LAZ directory ("+str(lidar_name)+"), file found: "+str(lazDir))
		#get/save coordinates of mouse click
		self.iface.mapCanvas().setMapTool(self.clickTool2)
		mouse_x=point.x()
		mouse_y=point.y()
		print("x: "+str(mouse_x))
		print("y: "+str(mouse_y))
		geo_pt = QgsGeometry.fromPointXY(QgsPointXY(point.x(), point.y()))
		#for each feature in that layer, find which features/blockIds contain the point geo_pt
		blockIds=[]
		feats = [ feat for feat in lidar_shp_layer.getFeatures() ]
		for feat in feats:
			if geo_pt.within(feat.geometry()):
				blockIds.append(feat['block'])
		if len(blockIds)>0:
			print(str(blockIds))
			#remove lidar_shp_layer
			QgsProject.instance().removeMapLayer(lidar_shp_layer)
			iface.mapCanvas().refreshAllLayers()
			#reset mapTool to cursor with no functionality
			iface.mapCanvas().setMapTool(QgsMapToolPan(iface.mapCanvas()))

			##open lidar Viewer
			print("Open 3D Lidar Viewer")
			#### Variables  ##################################################

			#  scale =1 (identity)
			scale = 111111.111111
			#only load points that are within below Range of given coordinates
			#0.00001 degrees Lat ~1m
			#0.0005 degrees Lat ~50m
			loadRange=0.00025
			qgisLat=mouse_y
			qgisLong=mouse_x
			qgisAlt=0
			pointCapCounter=0
			pointCap=1000000
			ps=0.00000001
			num_cols=3

			#min/max points to load into viewer
			#descaled
			#qgisLatMin=(qgisLat - loadRange) #47.570305 - 0.00025 = 47.570055
			#qgisLatMax=(qgisLat + loadRange) #47.570305 + 0.00025 = 47.570555
			#qgisLongMin=(qgisLong - loadRange) #-122.338109 - 0.00025 = -122.338359
			#qgisLongMax=(qgisLong + loadRange) #-122.338109 + 0.00025 = -122.337859

			#set initial lookat location
			initialLookAtX=qgisLong*scale
			initialLookAtY=qgisLat*scale
			initialLookAtZ=qgisAlt
			las_file=None
			PointsXYZ=None

			#### Methods / Functions ##################################################
			#INSERT code to get the LAS file that matches the name of the selected lidar in the QGIS registry
			#las_file = r"C:\Users\jgreener\Documents\Projects\LidarViewer\Lidar\150728_175300_S1.las"
			las_file = lazDir

			#'''Read LAS file and create a Numpy array to hold X, Y, Z values'''
			# Get file
			# Read file
			file = file.File(las_file, mode='r')
			# Get number of points from header
			num_points = int(file.__len__())
			#override pointcap, if desired
			num_points = pointCap
			print('Create empty numpy array')
			PointsXYZ = np.empty(shape=(num_points, num_cols))
			# Load all LAS points into numpy array
			#counter = 0
			#save initial camera position, or 'pose' in format:
			# (x, y, z, phit, theta, r)
			#'phi' is float32 Camera azimuthal angle (radians),
			#'theta' is float32 Camera elevation angle (radians),
			#'r' is float32 Camera distance to look-at point)
			#poses.append([firstRowX, firstRowY, firstRowZ, 0 * np.pi/2, np.pi/4, 5])
			print("Iterate through Numpy Array: seems slow")
			for ptCloudPt in file:
				if pointCapCounter<pointCap:
					x = ptCloudPt.x*scale
					y = ptCloudPt.y*scale
					z = ptCloudPt.z
					#override initial lookat location to look at first x,y,z in laz file
					if pointCapCounter ==1:
						initialLookAtX=x
						initialLookAtY=y
						initialLookAtZ=z
					newrow = [x, y, z]
					PointsXYZ[pointCapCounter] = newrow
					#counts number of points to be loaded
					pointCapCounter += 1
				else:
					break
			print("Count lidar points in x,y,z array: "+str(np.count_nonzero(PointsXYZ)/num_cols))
			print("Start Viewer using Numpy Array")
			v=pptk.viewer(PointsXYZ)

			print("Execute viewer's setters")
			v.set(bg_color=[0,0,0,1])
			v.set(floor_color=[0,0,0,1])
			v.set(show_grid=False)
			v.set(show_info=True)
			v.set(show_axis=False)
			v.set(point_size=ps)
			v.set(lookat = [initialLookAtX,initialLookAtY,initialLookAtZ])
			v.set(r = 100) #r=camera distance to look-at point


			#debug with getters
			#print("Camera Position:")
			#print(v.get(eye))
			#print("Camera look-at Position:")
			#print(v.get(lookat))
			#print("Number of points loaded:")
			#print(v.get(num_points))
			#print("Camera azimuthal angle in radians called phi:")
			#print(v.get(phi))
			#print("Camera Distance to look-at point:")
			#print(v.get(r))
			#print("Camera Right Vector:")
			#print(v.get(right))
			#print("Camera elevation angle in radians called theta:")
			#print(v.get(theta))
			#print("Camera up Vector:")
			#print(v.get(up))
			#print("Camera view Vector:")
			#print(v.get(view))
			#v.capture('PointCloudscreenshot.png')
			#v.close()
			#set initial camera position
			#play(poses, ts=[], tlim=[-inf, inf], repeat=False, interp='cubic_natural')
			#v.play(poses, tlim=[-inf, inf], repeat=False, interp='linear')

			####  Calls  ##################################################



			#get LAS file from selected 2D tile Lidar layer in QGIS layers Panel
			#las_file=getLAS_file()

			#use that las file to create a numpy array
			#PointsXYZ=LAS2Numpy(las_file)

			#use numpy array to start Viewer
			#startViewer(PointsXYZ)
			print("3D Lidar Viewer Finished")
						##TODO: display first block in blockIds from LAZ file from lazDir directory in Lidar Viewer

						##TODO: go to coordinates in lidar Viewer, possibly from coordinates from variables mouse_x and mouse_y


		else:
			errorText='Error: Clicked Point Does Not Intersect Lidar Shapefile'
			widget = iface.messageBar().createMessage(errorText)
			iface.messageBar().pushWidget(widget, Qgis.Warning,duration=5)


	def setReplacedByWuid(self, point, mouse_button):
		self.iface.mapCanvas().setMapTool(self.clickTool)

		###USERS ALLOWED TO MAKE EDITS, BY MODE###
		USERS_ALLOWED_toMakeEdits_NORMAL_MODE=['ushr_jgreener', 'ushr_jpepper', 'ushr_rwaldon', 'ushr_todonnell', 'ushr_kryan', 'ushr_egarnica', 'ushr_jcuevas', 'ushr_jklath', 'ushr_dlossing', 'ushr_syang', 'ushr_aestrada', 'ushr_hahmed']
		USERS_ALLOWED_toMakeEdits_ACQTRACK_MODE=['ushr_jgreener', 'ushr_egarnica']

		print('Mouse Button: ')
		print(mouse_button)
		overlapToolenabled=True
		ruLayerFound = False
		CSAV3_Ru_Geoms_Layer_Found = False

		for lyr in QgsProject.instance().layerTreeRoot().findLayers():
			if lyr.name()=="Road Unit Segment":
				ruLayerFound = True
			elif "CSAV3_Ru_Geoms_" in lyr.name():
				CSAV3_Ru_Geoms_Layer_Found = True
		#### NORMAL MODE #####
		if ruLayerFound == True and CSAV3_Ru_Geoms_Layer_Found == False:
			print("RU layer found")
			currentLayer=None
			layerList=[]
			selectedRuFeatures = []
			expression=None
			layerIDs=[]
			currentID=None
			fieldName = "segment_id"
			currentPathID = None
			currentLeftDelinID = None
			currentRightDelinID = None
			layerDelineators = None
			layerPath = None
			layerDelineatorTypes = None
			layerRU = None
			layerWu = None
			layerNearbyFeaturesRu=None
			layerPathTypes = None
			#layerPathSurfaceTypes = None
			layerPathSpeedLimits = None
			geo_pt = QgsGeometry.fromPointXY(QgsPointXY(point.x(), point.y()))
			message=None
			messageType=None

			####NEW connection settings
			settings = QSettings('Geodigital', 'db_params_settings')
			currentConnectionName = str(settings.value('current_connection'))
			currentConnection = {}
			currentConnection = settings.value('connections')[currentConnectionName]
			username = str(settings.value('connections')[currentConnectionName]['user_name'])
			password = str(settings.value('connections')[currentConnectionName]['password'])
			databaseName = str(settings.value('connections')[currentConnectionName]['database_name'])
			hostName = str(settings.value('connections')[currentConnectionName]['server_ip'])
			port = str(settings.value('connections')[currentConnectionName]['port'])
			####NEW connection settings
			for lyr in QgsProject.instance().layerTreeRoot().findLayers():
				layer1=QgsProject.instance().layerTreeRoot().findLayer(lyr.layerId())
				if layer1!=None:
					if layer1.parent()!=None:
						if layer1.parent().parent()!=None:
							if layer1.parent().parent().name()!="Nearby Features":
								if lyr.name()=="Path":
									layerPath = lyr.layer()
								elif lyr.name()=="Road Unit Segment":
									layerRU = lyr.layer()
								elif lyr.name()=="Path Types":
									layerPathTypes = lyr.layer()
							#elif layer1.parent().parent().name()=="Nearby Features":
								#if lyr.name()=="Replaced Segments":
								elif lyr.name()=="Replaced Segments":
									layerNearbyFeaturesRu= lyr.layer()
						elif lyr.name()=="Work Units":
							layerWu = lyr.layer()

			####  LEFT MOUSE BUTTON PRESSED #####
			if mouse_button==1:
				#get road unit features at click that are overlapping
				print("Left Mouse Button Pressed")
				feats = [ feat for feat in layerRU.getFeatures() ]
				roadUnit = set()
				zombieRus = set()
				zombieFound=False
				wu_ids_listed_in_current_RoadUnitSegments_Layer=set()
				for feat in feats:
					if feat['wu_id']>0:
						wu_ids_listed_in_current_RoadUnitSegments_Layer.add(str(feat['wu_id']))
					if geo_pt.within(feat.geometry()):
						#if str(feat['under_construction']) =='False':
						if str(feat['replaced_by_wuid']) =='NULL':
							if str(feat['wu_id']) !='NULL':
								roadUnit.add(feat)
							else:
								zombieFound=True
								zombieRus.add(feat)
				#ZOMBIES, under click
				if len(zombieRus)>0:
					if 'ushr_' in username.lower():
						#get wu_ids from Work Units layer whose geom intersects current viewing panel
						feats = [ feat for feat in layerWu.getFeatures() ]
						wu_ids_intersecting_view=set()
						for feat in feats:
							if feat.geometry().intersects(iface.mapCanvas().extent()):
								if str(feat['work_unit_id']) !='NULL' or feat['work_unit_id']!=None:
									wu_ids_intersecting_view.add(feat['work_unit_id'])

						#saves visibility settings
						nameOfTheme="ZombieTool_SavedVisibilitySettings"
						theme=None
						root = QgsProject.instance().layerTreeRoot()
						OFF=0
						ON=1
						theme=QgsProject.instance().mapThemeCollection().createThemeFromCurrentState(root, QgsLayerTreeModel(root))
						QgsProject.instance().mapThemeCollection().insert(nameOfTheme,theme)

						#turns off visibility on all layers
						for lyr2 in root.findLayers():
							type=-1
							try:
								type=lyr2.layer().type()
							except:
								continue
							if type!=-1:
								if type==0:
									QgsProject.instance().layerTreeRoot().findLayer(lyr2.layerId()).setItemVisibilityChecked(OFF)

						#turns on visibility of Work Unit layer
						ltl=QgsProject.instance().layerTreeRoot().findLayer(layerWu.id())
						#turns on visibility of all sub-category rules of Work Units layer
						ltl.setItemVisibilityChecked(ON)
						ltm = iface.layerTreeView().layerTreeModel()
						legendNodes = ltm.layerLegendNodes( ltl )
						for node in legendNodes:
							node.setData( Qt.Checked, Qt.CheckStateRole)

						for zombieRu in zombieRus:
							#set zombie cleanup enabled for associations/disassociations. If associations is disabled, then disassociations automatically will also not disassociate
							cleanupZombies_Enabled=False
							cleanupZombiesDisassociations_Enabled=False
							#make temporary layer using geometry of zombieRu called "zombie_"+ str(zombieSeg_id)
							try:
								iface.setActiveLayer(QgsProject.instance().layerTreeRoot().children()[0].layer())
							except:
								print("Top layer is a group, not a layer. Could not load layer to top of Layers Panel")
							zombieTempLayerName='_zombie_' + str(zombieRu['segment_id'])
							geom = QgsGeometry().fromWkt('GEOMETRYCOLLECTION()')
							geom = zombieRu.geometry()
							iface.mainWindow().blockSignals(True)
							crs_authid = iface.mapCanvas().mapSettings().destinationCrs().authid()
							my_layer = QgsVectorLayer('Polygon', zombieTempLayerName, 'memory')
							my_layer.setCrs(QgsCoordinateReferenceSystem(crs_authid))
							pr = my_layer.dataProvider()
							pr.addAttributes([QgsField("seg_id", QVariant.String)])
							my_layer.updateFields()
							feature = QgsFeature(my_layer.fields())
							feature.setGeometry(geom)
							feature.setAttribute("seg_id", str(zombieRu['segment_id']))
							pr.addFeatures([feature])
							#style
							alphaOpaque=',255'
							alphaSeeThrough=',100'
							color='255,255,0'
							symbol = QgsFillSymbol.createSimple({'color': color+alphaSeeThrough,'outline_color': color+alphaOpaque, 'outline_style': 'solid', 'outline_width': '1'})
							renderer = QgsSingleSymbolRenderer(symbol)
							my_layer.triggerRepaint()
							my_layer.setRenderer(renderer)
							iface.mapCanvas().setDestinationCrs(QgsCoordinateReferenceSystem(crs_authid))
							QgsProject.instance().addMapLayer(my_layer, True)
							iface.mainWindow().blockSignals(False)

							#Zombie QInputDialog for wu_id
							qid = QInputDialog()
							title = 'Zombie RU ' + str(zombieRu['segment_id'])
							label = "Select wu_id: "
							editable=False
							#sort combo box options
							items=[]
							for wus in wu_ids_intersecting_view:
								items.append(wus)
							items.sort()
							items=[str(i) for i in items]

							#for user-input text dialogue
							#mode = QLineEdit.Normal
							#defaultInputText = "Enter wu_id for Zombie"
							#userInputWuId, ok = QInputDialog.getText( qid, title, label, mode, defaultInputText)

							#for user-selected combo box dialogue
							userInputWuId, ok = QInputDialog.getItem( qid, title, label, items, editable=editable)
							print(str(userInputWuId))

							#if 'ok' button clicked in QInputDialog
							if ok:
								#run user Input CHECK against wu List
								#OLD: if str(userInputWuId) in wu_ids_listed_in_current_RoadUnitSegments_Layer:
								if userInputWuId in items:
									conn = psycopg2.connect(host=hostName, port=port, dbname=databaseName, user=username, password=password)
									cur = conn.cursor()
									#update wuid for zombie seg
									sql = (f"Update road_unit.segment_boundaries SET wu_id ={str(userInputWuId)} WHERE segment_id={zombieRu['segment_id']} ; ")
									cur.execute(sql)
									conn.commit()
									#get info
									sql = (f"SELECT sb.segment_id, sb.start_boundary_id, sb.end_boundary_id, sb.wu_id, sb.replaced_by_wuid, cp.crossing_id, rop.road_object_id \
										FROM road_unit.segment_boundaries sb \
										INNER JOIN road_unit.segment_paths sp on sb.segment_id = sp.segment_id \
										FULL OUTER JOIN crossing.crossings_paths cp on cp.path_id = sp.id \
										FULL OUTER JOIN road_object.road_objects_paths rop on rop.path_id = sp.id \
										where sb.segment_id={str(zombieRu['segment_id'])} \
										group by sb.segment_id,cp.crossing_id, rop.road_object_id; ")
									cur.execute(sql)
									result = cur.fetchall()
									print(result)
									boundariesMoved=False
									crossingsMoved=False
									roadObjectsMoved=False
									boundariesMovedOut=False
									crossingsMovedOut=False
									roadObjectsMovedOut=False
									countAssociated_boundaries=0
									countAssociated_crossings=0
									countAssociated_roadObjects=0
									countDisassociated_boundaries=0
									countDisassociated_crossings=0
									countDisassociated_roadObjects=0

									#put results into sets
									result_boundary_ids=set()
									result_crossing_ids=set()
									result_roadObject_ids=set()
									for row in result:
										if row[1]!=None:
											result_boundary_ids.add(row[1])
										if row[2]!=None:
											result_boundary_ids.add(row[2])
										if row[5]!=None:
											result_crossing_ids.add(row[5])
										if row[6]!=None:
											result_roadObject_ids.add(row[6])
									print('result_boundary_ids:')
									print(result_boundary_ids)
									print('result_crossing_ids:')
									print(result_crossing_ids)
									print('result_roadObject_ids:')
									print(result_roadObject_ids)
									cleanUpFailed=''

									######Zombie Clean-up (Associations and Disassociations)######
									if cleanupZombies_Enabled==True:
										#Progress Bar (set up)#
										#clear the message bar
										iface.messageBar().clearWidgets()
										#set a new message bar
										progressMessageBar = iface.messageBar()
										progress = QProgressBar()
										#Maximum is set to 100, making it easy to work with percentage of completion
										progress.setMaximum(100)
										#pass the progress bar to the message Bar
										progressMessageBar.pushWidget(progress)
										#Set initial percent
										progress.setValue(1)
										#make changes to database, if able
										if len(result_boundary_ids)!=0:
											max_count=len(result_boundary_ids)
											count=0
											progress.setValue(1)
											for boundary_id in result_boundary_ids:
												#Update the progress bar
												count+=1
												percent = (count/float(max_count)) * 100
												progress.setValue(percent)
												try:
													sql = (f"SELECT wu_id, boundary_id FROM work_units.associated_boundaries where wu_id={str(userInputWuId)} and boundary_id={str(boundary_id)} ; ")
													cur.execute(sql)
													#check_featureExists=cur.fetchall()
													count_result=0
													count_result=cur.rowcount
													#if boundary/WU combo is not already assigned, then assign it
													if count_result	==0:
														sql = (f"INSERT INTO work_units.associated_boundaries(wu_id, boundary_id) VALUES ({str(userInputWuId)}, {str(boundary_id)} ) ; ")
														cur.execute(sql)
														conn.commit()
														boundariesMoved=True
														countAssociated_boundaries+=1
														print('Success for boundary id: '+str(boundary_id))
													else:
														print('Boundary / WU combo already exists for: '+str(boundary_id))
												except Exception as e:
													cleanUpFailed+=' Boundary(ies)'
													print(e)
												#except:
												#	print('Boundary Error: '+str(boundary_id))
										if len(result_crossing_ids)!=0:
											max_count=len(result_crossing_ids)
											count=0
											progress.setValue(0)
											for crossing_id in result_crossing_ids:
												#Update the progress bar
												count+=1
												percent = (count/float(max_count)) * 100
												progress.setValue(percent)
												try:
													#check if crossing is already associated to user-defined WU
													sql = (f"SELECT wu_id, crossing_id FROM work_units.associated_crossings where wu_id={str(userInputWuId)} and crossing_id={str(crossing_id)} ; ")
													cur.execute(sql)
													count_result=0
													count_result=cur.rowcount
													#if crossing is not already associated to user-defined WU, then associate it
													if count_result	==0:
														sql = (f"INSERT INTO work_units.associated_crossings(wu_id, crossing_id) VALUES ({str(userInputWuId)}, {str(crossing_id)} ) ; ")
														cur.execute(sql)
														conn.commit()
														crossingsMoved=True
														countAssociated_crossings+=1
														print('Success for crossing id: '+str(crossing_id))
													else:
														print('Crossing / WU combo already exists for: '+str(crossing_id))
													if cleanupZombiesDisassociations_Enabled==True:
														#disassociate crossing from WU in associated_crossings table, if it is assigned to no other RU, other than {str(zombieRu['segment_id'])}
														#for crossings associated to zombie, check if that crossing is assigned to another WU but not any of that WUs segments, and disassociate that crossing from that WU
														sql = (f"SELECT ac0.wu_id FROM work_units.associated_crossings ac0 \
															where ac0.crossing_id={str(crossing_id)} \
															and ac0.wu_id not in (SELECT sb.wu_id	FROM crossing.crossings_paths cp \
															INNER JOIN road_unit.segment_paths sp on sp.id = cp.path_id \
															INNER JOIN road_unit.segment_boundaries sb on sb.segment_id=sp.segment_id \
															WHERE sb.wu_id IS NOT NULL and cp.crossing_id={str(crossing_id)}  \
															GROUP BY sb.wu_id) ; ")
														cur.execute(sql)
														count_result=0
														count_result=cur.rowcount
														print("Crossing count_result: "+str(count_result))
														if count_result	>0:
															#build set of WUs to disassociate crossing from
															result_Disassociate_WUs_ForCrossing=cur.fetchall()
															print('result_Disassociate_WUs_ForCrossing:')
															print(result_Disassociate_WUs_ForCrossing)
															SetOfWusToDisassociateFrom_Crossings=set()
															for row in result_Disassociate_WUs_ForCrossing:
																if row[0]!=None and str(row[0])!='NULL' and str(row[0])!=str(userInputWuId):
																	SetOfWusToDisassociateFrom_Crossings.add(row[0])
															print('SetOfWusToDisassociateFrom_Crossings:')
															print(SetOfWusToDisassociateFrom_Crossings)
															#execute disassociation(s) from set of WUs
															for wu in SetOfWusToDisassociateFrom_Crossings:
																sql=(f"DELETE FROM work_units.associated_crossings \
																WHERE crossing_id={str(crossing_id)} and wu_id={str(wu)} ;")
																cur.execute(sql)
																conn.commit()
																crossingsMovedOut=True
																countDisassociated_crossings+=1
																print("Disassociated crossing "+str(crossing_id)+" from WU: "+str(wu))
														else:
															print("No disassociations needed/allowed for crossing: "+str(crossing_id))
												except Exception as e:
													cleanUpFailed+=' Crossing(s)'
													print(e)
												#except:
												#	print('Crossing Error: '+str(crossing_id))
										if len(result_roadObject_ids)!=0:
											max_count=len(result_roadObject_ids)
											count=0
											progress.setValue(0)
											for roadObject_id in result_roadObject_ids:
												#Update the progress bar
												count+=1
												percent = (count/float(max_count)) * 100
												progress.setValue(percent)
												try:
													#check if road object is already associated to user-defined WU
													sql = (f"SELECT wu_id, road_object_id FROM work_units.associated_road_objects where wu_id={str(userInputWuId)} and road_object_id={str(roadObject_id)} ; ")
													cur.execute(sql)
													#check_featureExists=cur.fetchall()
													count_result=0
													count_result=cur.rowcount
													#if road object is not already associated to user-defined WU, then associate it
													if count_result	==0:
														sql = (f"INSERT INTO work_units.associated_road_objects(wu_id, road_object_id) VALUES ({str(userInputWuId)}, {str(roadObject_id)} ) ; ")
														cur.execute(sql)
														conn.commit()
														roadObjectsMoved=True
														countAssociated_roadObjects+=1
														print('Success for road object id: '+str(roadObject_id))
													else:
														print('Road Object / WU combo already exists for: '+str(roadObject_id))
													if cleanupZombiesDisassociations_Enabled==True:
														#disassociate road object from WU in associated_road_objects table, if it is assigned to no other RU, other than {str(zombieRu['segment_id'])}
														#for road objects associated to zombie, check if that road object is assigned to another WU but not any of that WUs segments, and disassociate that road object from that WU
														sql = (f"SELECT aro0.wu_id FROM work_units.associated_road_objects aro0 \
															where aro0.road_object_id={str(roadObject_id)} \
															and aro0.wu_id not in (SELECT sb.wu_id	FROM road_object.road_objects_paths rop \
															INNER JOIN road_unit.segment_paths sp on sp.id = rop.path_id \
															INNER JOIN road_unit.segment_boundaries sb on sb.segment_id=sp.segment_id \
															WHERE sb.wu_id IS NOT NULL and rop.road_object_id={str(roadObject_id)}  \
															GROUP BY sb.wu_id) ; ")
														cur.execute(sql)
														count_result=0
														count_result=cur.rowcount
														print("Road Object count_result: "+str(count_result))
														if count_result	>0:
															#build set of WUs to disassociate road object from
															result_Disassociate_WUs_ForRoadObject=cur.fetchall()
															print("result_Disassociate_WUs_ForRoadObject:")
															print(result_Disassociate_WUs_ForRoadObject)
															SetOfWusToDisassociateFrom_RoadObjects=set()
															for row in result_Disassociate_WUs_ForRoadObject:
																if row[0]!=None and str(row[0])!='NULL' and str(row[0])!=str(userInputWuId):
																	SetOfWusToDisassociateFrom_RoadObjects.add(row[0])
															print("SetOfWusToDisassociateFrom_RoadObjects:")
															print(SetOfWusToDisassociateFrom_RoadObjects)
															#execute disassociation(s) from set of WUs
															for wu in SetOfWusToDisassociateFrom_RoadObjects:
																sql=(f"DELETE FROM work_units.associated_road_objects \
																WHERE road_object_id={str(roadObject_id)} and wu_id={str(wu)} ;")
																cur.execute(sql)
																conn.commit()
																roadObjectsMovedOut=True
																countDisassociated_roadObjects+=1
																print("Disassociated road object "+str(roadObject_id)+" from WU: "+str(wu))
														else:
															print("No disassociations needed/allowed for road object: "+str(roadObject_id))
												except Exception as e:
													cleanUpFailed+=' Road_Object(s)'
													print(e)
												#except:
												#	print('Road Object Error: '+str(roadObject_id))
									#closing connection and cursor
									cur.close()
									conn.close()
									layerRU.select(zombieRu.id())
									message='COMMITTED CHANGES! Segment ' + str(zombieRu['segment_id']) + ' now belongs to WU: ' + str(userInputWuId)
									if boundariesMoved==True or crossingsMoved==True or roadObjectsMoved==True or boundariesMovedOut==True or crossingsMovedOut==True or roadObjectsMovedOut==True:
										message+='. Cleaned Up'
										if boundariesMoved==True or crossingsMoved==True or roadObjectsMoved==True:
											message+=' - Associated:'
											if boundariesMoved==True:
												message+=' Boundaries ('+str(countAssociated_boundaries)+')'
											if crossingsMoved==True:
												message+=' Crossings ('+str(countAssociated_crossings)+')'
											if roadObjectsMoved==True:
												message+=' Road_Objects ('+str(countAssociated_roadObjects)+')'
										if boundariesMovedOut==True or crossingsMovedOut==True or roadObjectsMovedOut==True:
											message+='. In other WUs, dissociated:'
											if boundariesMovedOut==True:
												message+=' Boundaries ('+str(countDisassociated_boundaries)+')'
											if crossingsMovedOut==True:
												message+=' Crossings ('+str(countDisassociated_crossings)+')'
											if roadObjectsMovedOut==True:
												message+=' Road_Objects ('+str(countDisassociated_roadObjects)+')'
									else:
										message+=". Clean-up NOT NEEDED (boundaries, crossings, and road objects found to be OK)."
									messageType= Qgis.Success
									if cleanUpFailed!='':
										messageType= Qgis.Warning
										message='WARNING: Clean-up Failed: '+cleanUpFailed + '. Perform Manually (In chosen WU, associate: boundaries, crossing(s), road objects as needed).'
								else:
									message='WARNING: NOT WITHIN VIEW. Ensure WU entered is within view. Wus currently within view: '
									messageType= Qgis.Warning
									for wus in wu_ids_intersecting_view:
										message+=str(wus)+' '
								#display message, for Zombie RUs
								iface.messageBar().clearWidgets()
								widget = iface.messageBar().createMessage(message)
								iface.messageBar().pushWidget(widget, messageType,duration=20)
							#deletes temporary layer that used geometry of zombieRu called "_zombie_"+ str(zombieSeg_id)
							for lyr in QgsProject.instance().mapLayers().values():
								if "_zombie_" in lyr.name():
									QgsProject.instance().removeMapLayer(lyr)
						#restores visibility settings that were previously saved, an deletes theme used
						QgsProject.instance().mapThemeCollection().applyTheme(nameOfTheme,root, QgsLayerTreeModel(root))
						QgsProject.instance().mapThemeCollection().removeMapTheme(nameOfTheme)

				#if exactly 2 road units found under mouse click
				elif len(roadUnit)==2:
					#check clicked point is not at point where 2+ SHOULDER path types are
					pathTypeFeats = [ feat for feat in layerPathTypes.getFeatures() ]
					withinPathTypeShoulderGeomCount = 0
					withinPathTypeBidirectionalGeomCount = 0
					for feat in pathTypeFeats:
						if geo_pt.within(feat.geometry()):
							if 'shoulder' in str(feat['type_name']).lower():
								withinPathTypeShoulderGeomCount+=1
							if 'bidirectional' in str(feat['type_name']).lower():
								withinPathTypeBidirectionalGeomCount+=1
					#if not at overlapping SHOULDER path types
					if withinPathTypeShoulderGeomCount<2:
						if withinPathTypeBidirectionalGeomCount<1:
							newestWU=-1
							oldestRuFeature=None
							newestRuFeature=None
							oldestRU=-1
							newestRU=-1
							oldestWU=-1
							equalWu=False
							wuid1=None
							for RU in roadUnit:
								if wuid1==None:
									wuid1=RU['wu_id']
								else:
									if RU['wu_id']==wuid1:
										equalWu=True
							if equalWu==False:
								#find newest WU
								for RU in roadUnit:
									if RU['wu_id']>newestWU:
										newestWU=RU['wu_id']
										newestRU=RU['segment_id']
										newestRuFeature=RU
								#find oldest RU
								for RU in roadUnit:
									if RU['wu_id']<newestWU:
										oldestRU=RU['segment_id']
										oldestRuFeature=RU
										oldestWU=RU['wu_id']
							elif equalWu==True:
								for RU in roadUnit:
									if RU['segment_id']>newestRU:
										newestWU=RU['wu_id']
										newestRU=RU['segment_id']
										newestRuFeature=RU
								for RU in roadUnit:
									if RU['segment_id']<newestRU:
										oldestRU=RU['segment_id']
										oldestRuFeature=RU
										oldestWU=RU['wu_id']

							print("Oldest RU (to have its replaced_by_wuid=Null be updated): "+str(oldestRU))
							print("Newest WU (to use as replaced_by_wuid): "+str(newestWU))
							print("Oldest WU: " + str(oldestWU))
							print("Newest RU: " + str(newestRU))
							if newestWU!=oldestWU:
								#copy to clipboard
								messageToClipboard="(RU " + str(oldestRU)+ ", WU " + str(newestWU)+" )"
								cb.OpenClipboard()
								cb.EmptyClipboard()
								cb.SetClipboardText(str(messageToClipboard))
								cb.CloseClipboard()
								#select old RU, to show user where they have already collected data from
								layerRU.select(oldestRuFeature.id())
								strNewestWU=str(newestWU)
								strOldestRU=str(oldestRU)
								print(strNewestWU)
								print(strOldestRU)
								additionalText=''

								####  UPDATE RFDB with a replaced_by_wuid - if enabled and if meets certain criteria   ####
								if username.lower() in USERS_ALLOWED_toMakeEdits_NORMAL_MODE:
									if overlapToolenabled==True:
										conn = psycopg2.connect(host=hostName, port=port, dbname=databaseName, user=username, password=password)
										cur = conn.cursor()
										sql = (f"Update road_unit.segment_boundaries SET replaced_by_wuid ={strNewestWU} WHERE segment_id={strOldestRU} ; ")
										print(sql)
										cur.execute(sql)
										try:
											result = cur.fetchall()
										except:
											if 'update' in sql.lower() or 'insert into' in sql.lower():
												additionalText = 'COMMITTED CHANGES!   Also, '
												conn.commit()
										#closing connection and cursor
										cur.close()
										conn.close()

								#SUCCESS message
								message = additionalText+"Copied to your Clipboard relevant text, if valid error: " + "(Replace RU " + str(oldestRU)+ " by WU " + str(newestWU)+" )"
								messageType=Qgis.Success
							elif len(zombieRus)==0:
								message='WARNING: SAME wu_ids. Cannot add replaced_by_wuid.'
								messageType=Qgis.Warning
						elif len(zombieRus)==0:
							message='WARNING: BI-DIRECTIONAL lane present here. Please perform manually, if valid error.'
							messageType=Qgis.Warning
					elif len(zombieRus)==0:
						message='WARNING: Please re-click at NON-SHOULDER overlapping geoms.'
						messageType=Qgis.Warning
				elif len(roadUnit)==1:
					#only allow acq_tracking 'replaced_by' functionality (using CSAV3_Ru_Geoms_ layer) for certain, trained users
					if username.lower() in USERS_ALLOWED_toMakeEdits_NORMAL_MODE:
						#get road unit features at click that are overlapping
						feats = [ feat for feat in layerRU.getFeatures() ]
						roadUnit = set()
						for feat in feats:
							if geo_pt.within(feat.geometry()):
								#if str(feat['under_construction']) =='False':
								if str(feat['Replaced_by_Wuid']) =='NULL':
									if str(feat['wu_id']) !='NULL':
										roadUnit.add(feat)
						print("RU found under mouse click from 'Road Unit Segments' layer: ")
						#get wu_ids from Work Units layer whose geom intersects current viewing panel
						feats = [ feat for feat in layerWu.getFeatures() ]
						wu_ids_intersecting_view=set()
						for feat in feats:
							if feat.geometry().intersects(iface.mapCanvas().extent()):
								if str(feat['work_unit_id']) !='NULL' or feat['work_unit_id']!=None:
									if 'Created' not in str(feat['work_unit_state']):
										wu_ids_intersecting_view.add(feat['work_unit_id'])

						#saves visibility settings
						nameOfTheme="SingleReplaceBy_SavedVisibilitySettings"
						theme=None
						root = QgsProject.instance().layerTreeRoot()
						OFF=0
						ON=1
						theme=QgsProject.instance().mapThemeCollection().createThemeFromCurrentState(root, QgsLayerTreeModel(root))
						QgsProject.instance().mapThemeCollection().insert(nameOfTheme,theme)

						#turns off visibility on all layers
						for lyr2 in root.findLayers():
							type=-1
							try:
								type=lyr2.layer().type()
							except:
								continue
							if type!=-1:
								if type==0:
									QgsProject.instance().layerTreeRoot().findLayer(lyr2.layerId()).setItemVisibilityChecked(OFF)

						#turns on visibility of Work Unit layer
						ltl=QgsProject.instance().layerTreeRoot().findLayer(layerWu.id())
						#turns on visibility of all sub-category rules of Work Units layer
						ltl.setItemVisibilityChecked(ON)
						ltm = iface.layerTreeView().layerTreeModel()
						legendNodes = ltm.layerLegendNodes( ltl )
						for node in legendNodes:
							node.setData( Qt.Checked, Qt.CheckStateRole)

						for ru in roadUnit:
							seg_id=ru['segment_id']
							seg_id_str=str(seg_id)
							print(seg_id_str)

							#open dialogue box that allows the user to select from a drop-down list of 'Ready_Collecting' wu_ids whose geom(s) intersect the viewing panel. Potentially, sample code for zombieRus above
							#make temporary layer using geometry of ru called "_segToReplace_"+ str(ru['segment_id'])
							try:
								iface.setActiveLayer(QgsProject.instance().layerTreeRoot().children()[0].layer())
							except:
								print("Top layer is a group, not a layer. Could not load layer to top of Layers Panel")
							segToReplace_TempLayerName='_segToReplace_' + str(ru['segment_id'])
							geom = QgsGeometry().fromWkt('GEOMETRYCOLLECTION()')
							geom = ru.geometry()
							iface.mainWindow().blockSignals(True)
							crs_authid = iface.mapCanvas().mapSettings().destinationCrs().authid()
							my_layer = QgsVectorLayer('Polygon', segToReplace_TempLayerName, 'memory')
							my_layer.setCrs(QgsCoordinateReferenceSystem(crs_authid))
							pr = my_layer.dataProvider()
							pr.addAttributes([QgsField("seg_id", QVariant.String)])
							my_layer.updateFields()
							feature = QgsFeature(my_layer.fields())
							feature.setGeometry(geom)
							feature.setAttribute("seg_id", str(ru['segment_id']))
							pr.addFeatures([feature])
							#style
							alphaOpaque=',255'
							alphaSeeThrough=',100'
							color='255,255,0'
							symbol = QgsFillSymbol.createSimple({'color': color+alphaSeeThrough,'outline_color': color+alphaOpaque, 'outline_style': 'solid', 'outline_width': '1'})
							renderer = QgsSingleSymbolRenderer(symbol)
							my_layer.triggerRepaint()
							my_layer.setRenderer(renderer)
							iface.mapCanvas().setDestinationCrs(QgsCoordinateReferenceSystem(crs_authid))
							QgsProject.instance().addMapLayer(my_layer, True)
							iface.mainWindow().blockSignals(False)

							#QInputDialog for wu_id
							qid = QInputDialog()
							title = 'RU ' + str(ru['segment_id'])+' (Not Zombie! Not Overlapping!)'
							label = "Choose replace_by_wuid (Not Zombie! Not Overlapping!): "
							editable=False
							#sort combo box options
							items=[]
							for wus in wu_ids_intersecting_view:
								items.append(wus)
							items.sort()
							items=[str(i) for i in items]

							#for user-selected combo box dialogue
							userInputWuId, ok = QInputDialog.getItem( qid, title, label, items, editable=editable)
							print(str(userInputWuId))

							#if 'ok' button clicked in QInputDialog
							if ok:
								#run user Input CHECK against wu List
								#OLD: if str(userInputWuId) in wu_ids_listed_in_current_RoadUnitSegments_Layer:
								if str(userInputWuId) != str(ru['wu_id']):
									conn = psycopg2.connect(host=hostName, port=port, dbname=databaseName, user=username, password=password)
									cur = conn.cursor()
									sql = (f"Update road_unit.segment_boundaries SET replaced_by_wuid ={str(userInputWuId)} WHERE segment_id={ru['segment_id']} ; ")
									cur.execute(sql)
									try:
										result = cur.fetchall()
									except:
										if 'update' in sql.lower() or 'insert into' in sql.lower():
											conn.commit()
									#closing connection and cursor
									cur.close()
									conn.close()
									layerRU.select(ru.id())
									message='COMMITTED CHANGES! Segment ' + str(ru['segment_id']) + ' now replaced by WU: ' + str(userInputWuId)
									messageType= Qgis.Success
								else:
									message="ERROR: REPLACED_BY_WUID = RU WU_ID. Did not commit changes. Ensure WU selected is not the Wu the RU belongs to, WU: "
									messageType= Qgis.Warning
									for wus in wu_ids_intersecting_view:
										message+=str(wus)+' '
							#deletes temporary layer that used geometry of zombieRu called "_segToReplace_"+ str(zombieSeg_id)
							for lyr in QgsProject.instance().mapLayers().values():
								if "_segToReplace_" in lyr.name():
									QgsProject.instance().removeMapLayer(lyr)

						#restores visibility settings that were previously saved, an deletes theme used
						QgsProject.instance().mapThemeCollection().applyTheme(nameOfTheme,root, QgsLayerTreeModel(root))
						QgsProject.instance().mapThemeCollection().removeMapTheme(nameOfTheme)

				#if road unit not found under mouse click or more than 2 RUs
				elif len(zombieRus)==0:
					#add warning
					message = "WARNING: Not Exactly 1 or 2 RUs found under mouse click. Number of RUs found: " + str(len(roadUnit))
					messageType=Qgis.Warning
				#display message, for overlapping Rus
				if len(zombieRus)==0:
					if message!=None and messageType!=None:
						widget = iface.messageBar().createMessage(message)
						iface.messageBar().pushWidget(widget, messageType,duration=3)


			####  RIGHT MOUSE BUTTON PRESSED #####
			elif mouse_button==2:
				if username.lower() in USERS_ALLOWED_toMakeEdits_NORMAL_MODE:
					#get all Nearby Feature's road unit features with a replaced_by_wuid at click
					print("Right Mouse Button Pressed")
					roadUnit_NF = set()

					#Nearby Features Replaced Segments layer found
					if layerNearbyFeaturesRu!=None:
						feats = [ feat for feat in layerNearbyFeaturesRu.getFeatures() ]
						for feat in feats:
							if geo_pt.within(feat.geometry()):
								#if str(feat['under_construction']) =='False':
								if str(feat['replaced_by_wuid']) !='NULL':
									if str(feat['wu_id']) !='NULL':
										roadUnit_NF.add(feat)
						if len(roadUnit_NF)==0:
							message = "WARNING: Count=0 replaced_by RUs found under mouse click. Cannot Undo replaced_by_wuid here."
							messageType=Qgis.Warning
							widget = iface.messageBar().createMessage(message)
							iface.messageBar().pushWidget(widget, messageType,duration=5)
						elif len(roadUnit_NF)>0:
							#saves visibility settings
							nameOfTheme="SingleReplaceBy_SavedVisibilitySettings"
							theme=None
							root = QgsProject.instance().layerTreeRoot()
							OFF=0
							ON=1
							theme=QgsProject.instance().mapThemeCollection().createThemeFromCurrentState(root, QgsLayerTreeModel(root))
							QgsProject.instance().mapThemeCollection().insert(nameOfTheme,theme)

							#turns off visibility on all layers
							for lyr2 in root.findLayers():
								type=-1
								try:
									type=lyr2.layer().type()
								except:
									continue
								if type!=-1:
									if type==0:
										QgsProject.instance().layerTreeRoot().findLayer(lyr2.layerId()).setItemVisibilityChecked(OFF)

							#turns on visibility of Work Unit layer
							ltl=QgsProject.instance().layerTreeRoot().findLayer(layerWu.id())
							#turns on visibility of all sub-category rules of Work Units layer
							ltl.setItemVisibilityChecked(ON)
							ltm = iface.layerTreeView().layerTreeModel()
							legendNodes = ltm.layerLegendNodes( ltl )
							for node in legendNodes:
								node.setData( Qt.Checked, Qt.CheckStateRole)
							total_nf=len(roadUnit_NF)
							count_nf=0
							for ru_nf in roadUnit_NF:
								count_nf+=1
								seg_id_nf=ru_nf['segment_id']
								wu_id_nf=ru_nf['replaced_by_wuid']
								dropdownSTR="(RU " + str(seg_id_nf)+ ", WU " + str(wu_id_nf)+" )                        "
								print(dropdownSTR)
								#open dialogue box that allows the user to select from a drop-down list of 'Ready_Collecting' wu_ids whose geom(s) intersect the viewing panel. Potentially, sample code for zombieRus above
								#make temporary layer using geometry of ru called "_segToReplace_"+ str(ru['segment_id'])
								try:
									iface.setActiveLayer(QgsProject.instance().layerTreeRoot().children()[0].layer())
								except:
									print("Top layer is a group, not a layer. Could not load layer to top of Layers Panel")
								segToReplace_TempLayerName='_segToUndo_ReplacedBy_' + str(ru_nf['segment_id'])
								geom = QgsGeometry().fromWkt('GEOMETRYCOLLECTION()')
								geom = ru_nf.geometry()
								iface.mainWindow().blockSignals(True)
								crs_authid = iface.mapCanvas().mapSettings().destinationCrs().authid()
								my_layer = QgsVectorLayer('Polygon', segToReplace_TempLayerName, 'memory')
								my_layer.setCrs(QgsCoordinateReferenceSystem(crs_authid))
								pr = my_layer.dataProvider()
								pr.addAttributes([QgsField("seg_id", QVariant.String)])
								my_layer.updateFields()
								feature = QgsFeature(my_layer.fields())
								feature.setGeometry(geom)
								feature.setAttribute("seg_id", str(ru_nf['segment_id']))
								pr.addFeatures([feature])
								#style
								alphaOpaque=',255'
								alphaSeeThrough=',100'
								color='255,255,0'
								symbol = QgsFillSymbol.createSimple({'color': color+alphaSeeThrough,'outline_color': color+alphaOpaque, 'outline_style': 'solid', 'outline_width': '1'})
								renderer = QgsSingleSymbolRenderer(symbol)
								my_layer.triggerRepaint()
								my_layer.setRenderer(renderer)
								iface.mapCanvas().setDestinationCrs(QgsCoordinateReferenceSystem(crs_authid))
								QgsProject.instance().addMapLayer(my_layer, True)
								iface.mainWindow().blockSignals(False)

								#QInputDialog for wu_id
								qid = QInputDialog()
								title = str(count_nf) +'/'+str(total_nf) + ': RU ' + str(ru_nf['segment_id'])+' (Right-Click Detected)'
								label = "REMOVE replace_by_wuid?"
								editable=False
								#add and sort combo box options
								items=[]
								items.append(dropdownSTR)

								#for user-selected combo box dialogue
								userInputWuId, ok = QInputDialog.getItem( qid, title, label, items, editable=editable)
								print(str(userInputWuId))

								#if 'ok' button clicked in QInputDialog
								if ok:
									#run user Input CHECK against wu List
									#OLD: if str(userInputWuId) in wu_ids_listed_in_current_RoadUnitSegments_Layer:

									conn = psycopg2.connect(host=hostName, port=port, dbname=databaseName, user=username, password=password)
									cur = conn.cursor()
									sql = (f"Update road_unit.segment_boundaries SET replaced_by_wuid =NULL WHERE segment_id={ru_nf['segment_id']} ; ")
									cur.execute(sql)
									try:
										result = cur.fetchall()
									except:
										if 'update' in sql.lower() or 'insert into' in sql.lower():
											conn.commit()
									#closing connection and cursor
									cur.close()
									conn.close()
									layerNearbyFeaturesRu.select(ru_nf.id())
									message='COMMITTED CHANGES! Segment ' + str(ru_nf['segment_id']) + ' now has NO replaced_by_wuid'
									messageType= Qgis.Success
								#deletes temporary layer that used geometry of zombieRu called "_segToReplace_"+ str(zombieSeg_id)
								for lyr in QgsProject.instance().mapLayers().values():
									if "_segToUndo_ReplacedBy_" in lyr.name():
										QgsProject.instance().removeMapLayer(lyr)

							#restores visibility settings that were previously saved, an deletes theme used
							QgsProject.instance().mapThemeCollection().applyTheme(nameOfTheme,root, QgsLayerTreeModel(root))
							QgsProject.instance().mapThemeCollection().removeMapTheme(nameOfTheme)

					#No Nearby Features Road Unit layer found, error message
					else:
						message = "ERROR: LAYER NOT FOUND. Right mouse button pressed. No Nearby Features 'Road Unit Segment' layer found."
						messageType=Qgis.Warning
						widget = iface.messageBar().createMessage(message)
						iface.messageBar().pushWidget(widget, messageType,duration=5)



		#Acq_Track
		#### ACQ_TRACK MODE #####
		elif CSAV3_Ru_Geoms_Layer_Found == True and ruLayerFound == False:
			####NEW connection settings
			settings = QSettings('Geodigital', 'db_params_settings')
			currentConnectionName = str(settings.value('current_connection'))
			currentConnection = {}
			currentConnection = settings.value('connections')[currentConnectionName]
			username = str(settings.value('connections')[currentConnectionName]['user_name'])
			password = str(settings.value('connections')[currentConnectionName]['password'])
			databaseName = str(settings.value('connections')[currentConnectionName]['database_name'])
			hostName = str(settings.value('connections')[currentConnectionName]['server_ip'])
			port = str(settings.value('connections')[currentConnectionName]['port'])
			####NEW connection settings

			#only allow acq_tracking 'replaced_by' functionality (using CSAV3_Ru_Geoms_ layer) for certain, trained users
			if username.lower() in USERS_ALLOWED_toMakeEdits_ACQTRACK_MODE:
				layerCsav3_RuGeoms=None
				layerWu=None
				geo_pt = QgsGeometry.fromPointXY(QgsPointXY(point.x(), point.y()))
				for lyr in QgsProject.instance().layerTreeRoot().findLayers():
					if 'CSAV3_Ru_Geoms_' in lyr.name():
						layerCsav3_RuGeoms = lyr.layer()
					elif "Work Units" in lyr.name():
						layerWu = lyr.layer()
				#get road unit features at click that are overlapping
				feats = [ feat for feat in layerCsav3_RuGeoms.getFeatures() ]
				roadUnit = set()
				for feat in feats:
					if geo_pt.within(feat.geometry()):
						#if str(feat['under_construction']) =='False':
						if str(feat['Replaced_by_Wuid']) =='NULL':
							if str(feat['wu_id']) !='NULL':
								roadUnit.add(feat)
				if len(roadUnit)!=1:
					message='Not Exactly 1 Road Unit Found Under Mouse Click. Counted: ' + str(len(roadUnit))
					widget = iface.messageBar().createMessage(message)
					iface.messageBar().pushWidget(widget, Qgis.Warning,duration=5)
				else:
					print("RU found under mouse click from 'CSAV3_Ru_Geoms_' layer: ")
					#get wu_ids from Work Units layer whose geom intersects current viewing panel
					feats = [ feat for feat in layerWu.getFeatures() ]
					wu_ids_intersecting_view=set()
					for feat in feats:
						if feat.geometry().intersects(iface.mapCanvas().extent()):
							if str(feat['work_unit_id']) !='NULL' or feat['work_unit_id']!=None:
								if 'Created' not in str(feat['work_unit_state']):
									wu_ids_intersecting_view.add(feat['work_unit_id'])

					#saves visibility settings
					nameOfTheme="AcqTrackReplaceBy_SavedVisibilitySettings"
					theme=None
					root = QgsProject.instance().layerTreeRoot()
					OFF=0
					ON=1
					theme=QgsProject.instance().mapThemeCollection().createThemeFromCurrentState(root, QgsLayerTreeModel(root))
					QgsProject.instance().mapThemeCollection().insert(nameOfTheme,theme)

					#turns off visibility on all layers
					for lyr2 in root.findLayers():
						type=-1
						try:
							type=lyr2.layer().type()
						except:
							continue
						if type!=-1:
							if type==0:
								QgsProject.instance().layerTreeRoot().findLayer(lyr2.layerId()).setItemVisibilityChecked(OFF)

					#turns on visibility of Work Unit layer
					ltl=QgsProject.instance().layerTreeRoot().findLayer(layerWu.id())
					#turns on visibility of all sub-category rules of Work Units layer
					ltl.setItemVisibilityChecked(ON)
					ltm = iface.layerTreeView().layerTreeModel()
					legendNodes = ltm.layerLegendNodes( ltl )
					for node in legendNodes:
						node.setData( Qt.Checked, Qt.CheckStateRole)

					for ru in roadUnit:
						seg_id=ru['segment_id']
						seg_id_str=str(seg_id)
						print(seg_id_str)

						#open dialogue box that allows the user to select from a drop-down list of 'Ready_Collecting' wu_ids whose geom(s) intersect the viewing panel. Potentially
						#make temporary layer using geometry of ru called "_segToReplace_"+ str(ru['segment_id'])
						try:
							iface.setActiveLayer(QgsProject.instance().layerTreeRoot().children()[0].layer())
						except:
							print("Top layer is a group, not a layer. Could not load layer to top of Layers Panel")
						segToReplace_TempLayerName='_segToReplace_' + str(ru['segment_id'])
						geom = QgsGeometry().fromWkt('GEOMETRYCOLLECTION()')
						geom = ru.geometry()
						iface.mainWindow().blockSignals(True)
						crs_authid = iface.mapCanvas().mapSettings().destinationCrs().authid()
						my_layer = QgsVectorLayer('Polygon', segToReplace_TempLayerName, 'memory')
						my_layer.setCrs(QgsCoordinateReferenceSystem(crs_authid))
						pr = my_layer.dataProvider()
						pr.addAttributes([QgsField("seg_id", QVariant.String)])
						my_layer.updateFields()
						feature = QgsFeature(my_layer.fields())
						feature.setGeometry(geom)
						feature.setAttribute("seg_id", str(ru['segment_id']))
						pr.addFeatures([feature])
						#style
						alphaOpaque=',255'
						alphaSeeThrough=',100'
						color='255,255,0'
						symbol = QgsFillSymbol.createSimple({'color': color+alphaSeeThrough,'outline_color': color+alphaOpaque, 'outline_style': 'solid', 'outline_width': '1'})
						renderer = QgsSingleSymbolRenderer(symbol)
						my_layer.triggerRepaint()
						my_layer.setRenderer(renderer)
						iface.mapCanvas().setDestinationCrs(QgsCoordinateReferenceSystem(crs_authid))
						QgsProject.instance().addMapLayer(my_layer, True)
						iface.mainWindow().blockSignals(False)

						#QInputDialog for wu_id
						qid = QInputDialog()
						title = 'RU ' + str(ru['segment_id'])+ ": Set 'replaced_by_wuid'"
						label = "Choose wu_id (Deployed only):                                 "
						editable=False
						#sort combo box options
						items=[]
						for wus in wu_ids_intersecting_view:
							items.append(wus)
						items.sort()
						items=[str(i) for i in items]

						#for user-selected combo box dialogue
						userInputWuId, ok = QInputDialog.getItem( qid, title, label, items, editable=editable)
						print(str(userInputWuId))

						#if 'ok' button clicked in QInputDialog
						if ok:
							#run user Input CHECK against wu List
							#OLD: if str(userInputWuId) in wu_ids_listed_in_current_RoadUnitSegments_Layer:
							if userInputWuId in items:
								conn = psycopg2.connect(host=hostName, port=port, dbname=databaseName, user=username, password=password)
								cur = conn.cursor()
								sql = (f"Update road_unit.segment_boundaries SET replaced_by_wuid ={str(userInputWuId)} WHERE segment_id={ru['segment_id']} ; ")
								cur.execute(sql)
								try:
									result = cur.fetchall()
								except:
									if 'update' in sql.lower() or 'insert into' in sql.lower():
										conn.commit()
								#closing connection and cursor
								cur.close()
								conn.close()
								layerCsav3_RuGeoms.select(ru.id())
								message='COMMITTED CHANGES! Segment ' + str(ru['segment_id']) + ' now replaced by WU: ' + str(userInputWuId)
								messageType= Qgis.Success
							else:
								message='WARNING: NOT WITHIN VIEW. Ensure WU entered is within view. Wus currently within view: '
								messageType= Qgis.Warning
								for wus in wu_ids_intersecting_view:
									message+=str(wus)+' '
							#display message, for Zombie RUs
							widget = iface.messageBar().createMessage(message)
							iface.messageBar().pushWidget(widget, messageType,duration=5)
						#deletes temporary layer that used geometry of zombieRu called "_segToReplace_"+ str(zombieSeg_id)
						for lyr in QgsProject.instance().mapLayers().values():
							if "_segToReplace_" in lyr.name():
								QgsProject.instance().removeMapLayer(lyr)

					#restores visibility settings that were previously saved, an deletes theme used
					QgsProject.instance().mapThemeCollection().applyTheme(nameOfTheme,root, QgsLayerTreeModel(root))
					QgsProject.instance().mapThemeCollection().removeMapTheme(nameOfTheme)
		elif CSAV3_Ru_Geoms_Layer_Found == True and ruLayerFound == True:
			message="MODE UNCLEAR. For normal mode, please delete 'CSAV3_Ru_Geoms_' Layer. For Acq_Track Mode, turn off RFDB plugin."
			widget = iface.messageBar().createMessage(message)
			iface.messageBar().pushWidget(widget, Qgis.Warning,duration=7)

	def filterRuByMouseClick(self, point, mouse_button):
		self.iface.mapCanvas().setMapTool(self.clickTool)
		ruLayerFound = False
		for lyr in QgsProject.instance().layerTreeRoot().findLayers():    ########
			if lyr.name()=="Road Unit Segment":
				ruLayerFound = True
		if ruLayerFound == True:
			print("RU layer found")
			currentLayer=None
			layerList=[]
			selectedRuFeatures = []
			expression=None
			layerIDs=[]
			currentID=None
			fieldName = "segment_id"
			currentPathID = None
			currentLeftDelinID = None
			currentRightDelinID = None
			layerDelineators = None
			layerPath = None
			layerDelineatorTypes = None
			layerRU = None
			layerPathTypes = None
			#layerPathSurfaceTypes = None
			layerPathSpeedLimits = None
			countRuFiltered=0
			numFiltersAllowed=9

			####NEW connection settings
			#line below taken from C:\Program Files\QGIS 2.18\apps\qgis-ltr\python\plugins\RoadFeatures\db_interface\db_params_settings.py
			#same line as RFDB plugin uses, so as long as it works for RFDB plugin, SHOULD work for this
			settings = QSettings('Geodigital', 'db_params_settings')
			currentConnectionName = str(settings.value('current_connection'))
			currentConnection = {}
			currentConnection = settings.value('connections')[currentConnectionName]
			username = str(settings.value('connections')[currentConnectionName]['user_name'])
			password = str(settings.value('connections')[currentConnectionName]['password'])
			databaseName = str(settings.value('connections')[currentConnectionName]['database_name'])
			hostName = str(settings.value('connections')[currentConnectionName]['server_ip'])
			port = str(settings.value('connections')[currentConnectionName]['port'])
			#fix off-by-1 bug
			numFiltersAllowed=numFiltersAllowed-1

			for lyr in QgsProject.instance().layerTreeRoot().findLayers():
				layer1=QgsProject.instance().layerTreeRoot().findLayer(lyr.layerId())
				if layer1!=None:
					if layer1.parent()!=None:
						if layer1.parent().parent()!=None:
							if layer1.parent().parent().name()!="Nearby Features":
								if lyr.name()=="Delineators":
									layerDelineators = lyr.layer()
								elif lyr.name()=="Delineator Types":
									layerDelineatorTypes = lyr.layer()
								elif lyr.name()=="Path":
									layerPath = lyr.layer()
								elif lyr.name()=="Road Unit Segment":
									layerRU = lyr.layer()
								elif lyr.name()=="Path Types":
									layerPathTypes = lyr.layer()
								#elif lyr.name()=="Path Surface Types":
								#	layerPathSurfaceTypes = lyr.layer()
								elif lyr.name()=="Path Speed Limits":
									layerPathSpeedLimits = lyr.layer()
								elif lyr.name()=="Crossings Paths Association":
									layerAssocXing = lyr.layer()
								elif lyr.name()=="Road Objects Paths Association":
									layerAssocRo = lyr.layer()
			expressionRUFound=False
			expressionPathFound=False
			expressionDelineatorFound=False
			expressionRU = layerRU.subsetString()
			expressionPath = layerPath.subsetString()
			expressionDelineator = layerDelineators.subsetString()
			#TODO: change "expressionRU != '' " and all filter expressions in RuFilter to start with "segment_id" != -2 and ... to be more robust if user has filter already
			if expressionRU != '':
				expressionRUFound=True
				countRuFiltered = expressionRU.count(',')
				countRuFiltered = countRuFiltered + 1
			else:
				countRuFiltered=0
			if expressionPath != '':
				expressionPathFound=True
			if expressionDelineator != '':
				expressionDelineatorFound=True


			print('expressionRU',expressionRU)
			print('countRuFiltered',countRuFiltered)
			feats = [ feat for feat in layerRU.getFeatures() ]

			geo_pt = QgsGeometry.fromPointXY(QgsPointXY(point.x(), point.y()))

			id = -1
			roadUnit = None

			for feat in feats:
				if geo_pt.within(feat.geometry()):
					id = feat.id()
					roadUnit = feat
					break

			#if road unit found under mouse click
			if id != -1:
				if countRuFiltered<=numFiltersAllowed:
					roadUnitFeaturesUnderMouseClick=[]
					#right now, only works with 1 RU geometry under mouse click
					roadUnitFeaturesUnderMouseClick.append(roadUnit)
					if len(roadUnitFeaturesUnderMouseClick)!=0:
						print("Road Unit Was Found Under Mouse Click")
						if 'segment_id' in layerRU.subsetString():
							#save subset string from Delineators, Paths, and Road Unit
							expressionRU_valuesList = re.findall("'(.+?)'", expressionRU)
							expressionPath_valuesList = re.findall("'(.+?)'", expressionPath)
							expressionDelineator_valuesList = re.findall("'(.+?)'", expressionDelineator)

							RU_delete_ftrs_list = []
							Path_delete_ftrs_list = []
							Delin_delete_ftrs_list = []
							Delin_delete_ftrs_list_filtered = []

						#Road Units
							#iterate through expressionRU_valuesList, and remove 1 of the duplicate road units (the one with Null)
							for values in expressionRU_valuesList:
								count = 0
								for features in layerRU.getFeatures():
									if str(features["segment_id"]) == str(values) and count == 0:
										count = count + 1
									elif str(features["segment_id"]) == str(values) and count >= 1:
										RU_delete_ftrs_list.append(features.id())
										count = count + 1
							expressionRU_valuesList_string = "\',\'".join(expressionRU_valuesList)
							#remove features
							layerRU.dataProvider().deleteFeatures(RU_delete_ftrs_list)

						#Paths
							for values in expressionPath_valuesList:
								count = 0
								for features in layerPath.getFeatures():
									if str(features["path_id"]) == str(values) and count == 0:
										count = count + 1
									elif str(features["path_id"]) == str(values) and count >= 1:
										Path_delete_ftrs_list.append(features.id())
										count = count + 1
							expressionPath_valuesList_string= "\',\'".join(expressionPath_valuesList)
							#remove features
							layerPath.dataProvider().deleteFeatures(Path_delete_ftrs_list)

						#Delineators
							delinFeatsWithSameDelinIdAsInExpression = []
							#convert list to set (unordered, only unique values)
							expressionDelineator_valuesSet = set(expressionDelineator_valuesList)

							#for values in the set
							for values in expressionDelineator_valuesSet:
								#for all of the delineators in the Delineators layer attribute table
								for features in layerDelineators.getFeatures():
								#if a delineator feature shares the same delineator_id as a value
									if str(features["delineator_id"]) == str(values):
										delinFeatsWithSameDelinIdAsInExpression.append(features)
							expressionDelineator_valuesSet_string= "\',\'".join(expressionDelineator_valuesSet)
							print("expressionRU_valuesList_string",expressionRU_valuesList_string)
							print("expressionPath_valuesList_string",expressionPath_valuesList_string)
							print("expressionDelineator_valuesSet_string",expressionDelineator_valuesSet_string)
							temp2 = set()
							duplicateIdFoundHere = []
							for feats in delinFeatsWithSameDelinIdAsInExpression:
								count=0
								for feats2 in delinFeatsWithSameDelinIdAsInExpression:
									if feats != feats2:
										#if this id has not been marked as a duplicateAlreadyFound
										if feats.id() not in duplicateIdFoundHere:
											if str(feats["delineator_id"]) == str(feats2["delineator_id"]):
												if str(feats["ordinal"]) == str(feats2["ordinal"]):
													#found duplicate
													duplicateIdFoundHere.append(feats2.id())
													temp2.add(feats.id())
							#cast set to list
							temp3 = list(temp2)
						#remove features
							######activate below to DELETE#############
							layerDelineators.dataProvider().deleteFeatures(temp3)

							iface.messageBar().clearWidgets()
							#refresh map canvas
							for layer in iface.mapCanvas().layers():
								layer.triggerRepaint()
							iface.mapCanvas().refresh()
							iface.mapCanvas().refreshAllLayers()

						current_RuCount_underMouseClick=0
						#Set Expressions, for each selected RU
						for roadUnit in roadUnitFeaturesUnderMouseClick:
							print("roadUnit",str(roadUnit[fieldName]))
							#replace query below for finding segment_paths for given segment_id in roadUnit[fieldName] with searching the e paths layer for the same thing.
							#get info associated to road unit id

							#get path-segment infomation from paths layer since it's available now, rather than querying the DB above (to improve time)
							pathDelin_IDsList_ForRU=[]
							for features in layerPath.getFeatures():
								if str(features["segment_id"]) == str(roadUnit[fieldName]):
									pathDelin_IDsList_ForRU.append([features["path_id"],features["left_delineator_id"],features["right_delineator_id"]])
							print(pathDelin_IDsList_ForRU)

							###remove duplicate delins ids###
								#get right delin ids
							rightDelinIdList_ForRU=[]
							for row1 in pathDelin_IDsList_ForRU:
								rightDelinIdList_ForRU.append(row1[2])

							#replace duplicate left ids with '-3'
							for row2 in pathDelin_IDsList_ForRU:
								for right_id in rightDelinIdList_ForRU:
									if right_id !='-3':
										if right_id==row2[1]:
											row2[1]='-3'

							current_pathCount_inRU=0
							#per path (aka for each [path,left, right]) in pathDelin_IDsList_ForRU
							for row in pathDelin_IDsList_ForRU:

								#Path layer -expression builder
								currentPathID = row[0]
								pathID_str=str(currentPathID)
								if current_RuCount_underMouseClick==0 and current_pathCount_inRU==0:
									#replace existing path expression
									path_expression = '\"path_id\" not in (\'' + pathID_str + '\')'
								elif current_RuCount_underMouseClick>0 or current_pathCount_inRU>0:
									#add to existing path expression
									path_expression = path_expression.replace(')','') + ',\'' + pathID_str + '\')'
								layerPath.setSubsetString(path_expression)
								layerPathTypes.setSubsetString(path_expression)
								#layerPathSurfaceTypes.setSubsetString(path_expression)
								layerPathSpeedLimits.setSubsetString(path_expression)
								layerAssocRo.setSubsetString(path_expression)
								layerAssocXing.setSubsetString(path_expression)

								#Delineator/DelineatorTypes layers - expression builder
								currentLeftDelinID = row[1]
								currentRightDelinID = row[2]
								leftDelinID_str = str(currentLeftDelinID)
								rightDelinID_str = str(currentRightDelinID)
								if current_RuCount_underMouseClick==0 and current_pathCount_inRU==0:
									delin_expression = '\"delineator_id\" not in (\'' + leftDelinID_str + '\',\'' + rightDelinID_str + '\')'
								else:
									delin_expression = delin_expression.replace(')','') + ',\'' + leftDelinID_str + '\',\'' + rightDelinID_str + '\')'
								#remove duplicate placeholders '-3'
								delin_expression=delin_expression.replace("'-3',","")
								delin_expression=delin_expression.replace(",'-3'","")
								#set expression - Delineator/DelineatorTypes layers
								layerDelineators.setSubsetString(delin_expression)
								layerDelineatorTypes.setSubsetString(delin_expression)
								current_pathCount_inRU = current_pathCount_inRU+1

							#path: if it existed, add the previous path expression ids from expressionPath_valuesList_string
							if expressionPathFound==True:
							#	print(expressionPath_valuesList_string, str(expressionPath_valuesList_string))
								path_expression = path_expression.replace(')','') + ',\'' + str(expressionPath_valuesList_string) + '\')'
								#update where needed
								layerPath.setSubsetString(path_expression)
								layerPathTypes.setSubsetString(path_expression)
								#layerPathSurfaceTypes.setSubsetString(path_expression)
								layerPathSpeedLimits.setSubsetString(path_expression)
								layerAssocRo.setSubsetString(path_expression)
								layerAssocXing.setSubsetString(path_expression)
							#delin: if it existed, add the previous delin expression ids
							if expressionDelineatorFound==True:
								delin_expression = delin_expression.replace(')','') + ',\'' + str(expressionDelineator_valuesSet_string) + '\')'
								#update where needed
								layerDelineators.setSubsetString(delin_expression)
								layerDelineatorTypes.setSubsetString(delin_expression)

							#expression builder - Road Unit Segment layer
							if current_RuCount_underMouseClick==0:
								RU_expression = '\"segment_id\" not in (\'' + str(roadUnit[fieldName]) + '\')'
							elif current_RuCount_underMouseClick>0:
								RU_expression = RU_expression.replace(')','') + ',\'' + str(roadUnit[fieldName]) + '\')'

							#set expression - Road Unit Segment layer
							#TAG1
							if expressionRUFound==True:
								RU_expression = RU_expression.replace(')','') + ',\'' + str(expressionRU_valuesList_string) + '\')'
							layerRU.setSubsetString(RU_expression)
							current_RuCount_underMouseClick=current_RuCount_underMouseClick+1
						#add warning that filter is ON
						filtersRemaining = numFiltersAllowed - countRuFiltered
						if filtersRemaining>0:
							warningMessage = 'RU Filters Remaining: ' + str(filtersRemaining)
						elif filtersRemaining == 0:
							warningMessage = 'RU Filters Remaining: ' + str(filtersRemaining) + ' (NEXT CLICK RESETS)'
						'''warningMessage = "Road Unit Last Filtered From View: "
						count = 1
						for roadUnits in roadUnitFeaturesUnderMouseClick:
							warningMessage = warningMessage + str(roadUnits["segment_id"])
							if count != len(roadUnitFeaturesUnderMouseClick):
								warningMessage = warningMessage + ', '
							count += 1'''
						widget3 = iface.messageBar().createMessage(warningMessage)
						iface.messageBar().pushWidget(widget3, Qgis.Warning,duration=0)
						#refresh map canvas
						for layer in iface.mapCanvas().layers():
							layer.triggerRepaint()
						iface.mapCanvas().refresh()
						iface.mapCanvas().refreshAllLayers()
				#reset expressions once too many RUs have been filtered
				else:
					'''#add warning
					warningMessage = "Too many RUs filtered"
					widget3 = iface.messageBar().createMessage(warningMessage)
					iface.messageBar().pushWidget(widget3, Qgis.Warning,duration=3)'''
					expression=''
					layerRU.setSubsetString(expression)
					layerDelineators.setSubsetString(expression)
					layerDelineatorTypes.setSubsetString(expression)
					layerPath.setSubsetString(expression)
					layerPathTypes.setSubsetString(expression)
					#layerPathSurfaceTypes.setSubsetString(expression)
					layerPathSpeedLimits.setSubsetString(expression)
					layerAssocRo.setSubsetString(expression)
					layerAssocXing.setSubsetString(expression)

					iface.messageBar().clearWidgets()

					#refresh map canvas
					for layer in iface.mapCanvas().layers():
						layer.triggerRepaint()
					iface.mapCanvas().refresh()
					iface.mapCanvas().refreshAllLayers()
			#if road unit not found under mouse click
			else:
				print("No RU found under mouse click")
				#set expression to nothing
				expression=''
				layerRU.setSubsetString(expression)
				layerDelineators.setSubsetString(expression)
				layerDelineatorTypes.setSubsetString(expression)
				layerPath.setSubsetString(expression)
				layerPathTypes.setSubsetString(expression)
				#layerPathSurfaceTypes.setSubsetString(expression)
				layerPathSpeedLimits.setSubsetString(expression)
				layerAssocRo.setSubsetString(expression)
				layerAssocXing.setSubsetString(expression)

				iface.messageBar().clearWidgets()

				#refresh map canvas
				for layer in iface.mapCanvas().layers():
					layer.triggerRepaint()
				iface.mapCanvas().refresh()
				iface.mapCanvas().refreshAllLayers()
		#if RU layer not found
		else:
			#add warning
			warningMessage = "Please load RFDB plugin before using this tool"
			widget3 = iface.messageBar().createMessage(warningMessage)
			iface.messageBar().pushWidget(widget3, Qgis.Warning,duration=3)

class qcToolsClickTool(QgsMapTool):
	def __init__(self, canvas):
		QgsMapTool.__init__(self, canvas)
		self.canvas = canvas

	def canvasReleaseEvent(self, event):
		print("Test Break")
