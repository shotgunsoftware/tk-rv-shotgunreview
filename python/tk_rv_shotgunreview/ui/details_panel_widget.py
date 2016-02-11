# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'details_panel_widget.ui'
#
#      by: pyside-uic 0.2.15 running on PySide 1.2.4
#
# WARNING! All changes made in this file will be lost!

from tank.platform.qt import QtCore, QtGui

class Ui_DetailsPanelWidget(object):
    def setupUi(self, DetailsPanelWidget):
        DetailsPanelWidget.setObjectName("DetailsPanelWidget")
        DetailsPanelWidget.resize(390, 737)
        self.verticalLayout_17 = QtGui.QVBoxLayout(DetailsPanelWidget)
        self.verticalLayout_17.setObjectName("verticalLayout_17")
        self.entity_tab_widget = QtGui.QTabWidget(DetailsPanelWidget)
        self.entity_tab_widget.setFocusPolicy(QtCore.Qt.NoFocus)
        self.entity_tab_widget.setObjectName("entity_tab_widget")
        self.entity_note_tab = QtGui.QWidget()
        self.entity_note_tab.setObjectName("entity_note_tab")
        self.verticalLayout_3 = QtGui.QVBoxLayout(self.entity_note_tab)
        self.verticalLayout_3.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout_3.setObjectName("verticalLayout_3")
        self.entity_details_view = QtGui.QListView(self.entity_note_tab)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Maximum)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.entity_details_view.sizePolicy().hasHeightForWidth())
        self.entity_details_view.setSizePolicy(sizePolicy)
        self.entity_details_view.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.entity_details_view.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.entity_details_view.setUniformItemSizes(True)
        self.entity_details_view.setObjectName("entity_details_view")
        self.verticalLayout_3.addWidget(self.entity_details_view)
        self.note_stream_widget = ActivityStreamWidget(self.entity_note_tab)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.note_stream_widget.sizePolicy().hasHeightForWidth())
        self.note_stream_widget.setSizePolicy(sizePolicy)
        self.note_stream_widget.setObjectName("note_stream_widget")
        self.verticalLayout_3.addWidget(self.note_stream_widget)
        self.entity_tab_widget.addTab(self.entity_note_tab, "")
        self.entity_version_tab = QtGui.QWidget()
        self.entity_version_tab.setObjectName("entity_version_tab")
        self.verticalLayout_2 = QtGui.QVBoxLayout(self.entity_version_tab)
        self.verticalLayout_2.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout_2.setObjectName("verticalLayout_2")
        self.entity_version_view = QtGui.QListView(self.entity_version_tab)
        self.entity_version_view.setVerticalScrollMode(QtGui.QAbstractItemView.ScrollPerPixel)
        self.entity_version_view.setHorizontalScrollMode(QtGui.QAbstractItemView.ScrollPerPixel)
        self.entity_version_view.setUniformItemSizes(True)
        self.entity_version_view.setObjectName("entity_version_view")
        self.verticalLayout_2.addWidget(self.entity_version_view)
        self.entity_tab_widget.addTab(self.entity_version_tab, "")
        self.verticalLayout_17.addWidget(self.entity_tab_widget)

        self.retranslateUi(DetailsPanelWidget)
        self.entity_tab_widget.setCurrentIndex(0)
        QtCore.QMetaObject.connectSlotsByName(DetailsPanelWidget)

    def retranslateUi(self, DetailsPanelWidget):
        DetailsPanelWidget.setWindowTitle(QtGui.QApplication.translate("DetailsPanelWidget", "Form", None, QtGui.QApplication.UnicodeUTF8))
        self.entity_tab_widget.setTabText(self.entity_tab_widget.indexOf(self.entity_note_tab), QtGui.QApplication.translate("DetailsPanelWidget", "NOTES", None, QtGui.QApplication.UnicodeUTF8))
        self.entity_tab_widget.setTabText(self.entity_tab_widget.indexOf(self.entity_version_tab), QtGui.QApplication.translate("DetailsPanelWidget", "VERSIONS", None, QtGui.QApplication.UnicodeUTF8))

from ..qtwidgets import ActivityStreamWidget
from . import resources_rc
from . import resources_rc
