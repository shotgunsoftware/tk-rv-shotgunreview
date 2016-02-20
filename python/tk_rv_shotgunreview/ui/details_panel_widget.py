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
        self.verticalLayout_17.setSpacing(2)
        self.verticalLayout_17.setContentsMargins(5, 0, 5, 0)
        self.verticalLayout_17.setObjectName("verticalLayout_17")
        self.entity_tab_widget = QtGui.QTabWidget(DetailsPanelWidget)
        self.entity_tab_widget.setFocusPolicy(QtCore.Qt.NoFocus)
        self.entity_tab_widget.setObjectName("entity_tab_widget")
        self.entity_note_tab = QtGui.QWidget()
        self.entity_note_tab.setObjectName("entity_note_tab")
        self.verticalLayout_3 = QtGui.QVBoxLayout(self.entity_note_tab)
        self.verticalLayout_3.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout_3.setObjectName("verticalLayout_3")
        self.horizontalLayout_3 = QtGui.QHBoxLayout()
        self.horizontalLayout_3.setSpacing(0)
        self.horizontalLayout_3.setContentsMargins(0, 0, -1, 10)
        self.horizontalLayout_3.setObjectName("horizontalLayout_3")
        spacerItem = QtGui.QSpacerItem(40, 20, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
        self.horizontalLayout_3.addItem(spacerItem)
        self.widget = QtGui.QWidget(self.entity_note_tab)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.widget.sizePolicy().hasHeightForWidth())
        self.widget.setSizePolicy(sizePolicy)
        self.widget.setObjectName("widget")
        self.horizontalLayout_2 = QtGui.QHBoxLayout(self.widget)
        self.horizontalLayout_2.setSpacing(0)
        self.horizontalLayout_2.setContentsMargins(15, 0, 0, 0)
        self.horizontalLayout_2.setObjectName("horizontalLayout_2")
        self.shot_info_widget = ListItemWidget(self.widget)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.Maximum)
        sizePolicy.setHorizontalStretch(3)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.shot_info_widget.sizePolicy().hasHeightForWidth())
        self.shot_info_widget.setSizePolicy(sizePolicy)
        self.shot_info_widget.setMaximumSize(QtCore.QSize(350, 25))
        self.shot_info_widget.setObjectName("shot_info_widget")
        self.horizontalLayout_2.addWidget(self.shot_info_widget)
        self.horizontalLayout = QtGui.QHBoxLayout()
        self.horizontalLayout.setSpacing(0)
        self.horizontalLayout.setContentsMargins(-1, 0, -1, -1)
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.shotgun_nav_button = QtGui.QToolButton(self.widget)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Maximum, QtGui.QSizePolicy.Maximum)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.shotgun_nav_button.sizePolicy().hasHeightForWidth())
        self.shotgun_nav_button.setSizePolicy(sizePolicy)
        self.shotgun_nav_button.setMaximumSize(QtCore.QSize(20, 20))
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap(":/tk-rv-shotgunreview/navigate_out_hover.png"), QtGui.QIcon.Active, QtGui.QIcon.On)
        icon.addPixmap(QtGui.QPixmap(":/tk-rv-shotgunreview/navigate_out.png"), QtGui.QIcon.Normal, QtGui.QIcon.On)
        icon.addPixmap(QtGui.QPixmap(":/tk-rv-shotgunreview/navigate_out_hover.png"), QtGui.QIcon.Selected, QtGui.QIcon.On)
        self.shotgun_nav_button.setIcon(icon)
        self.shotgun_nav_button.setAutoRaise(True)
        self.shotgun_nav_button.setObjectName("shotgun_nav_button")
        self.horizontalLayout.addWidget(self.shotgun_nav_button)
        self.pin_button = QtGui.QToolButton(self.widget)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Maximum, QtGui.QSizePolicy.Maximum)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.pin_button.sizePolicy().hasHeightForWidth())
        self.pin_button.setSizePolicy(sizePolicy)
        self.pin_button.setMaximumSize(QtCore.QSize(20, 20))
        self.pin_button.setText("")
        icon1 = QtGui.QIcon()
        icon1.addPixmap(QtGui.QPixmap(":/tk-rv-shotgunreview/tack_hover.png"), QtGui.QIcon.Active, QtGui.QIcon.On)
        icon1.addPixmap(QtGui.QPixmap(":/tk-rv-shotgunreview/tack_up.png"), QtGui.QIcon.Normal, QtGui.QIcon.On)
        icon1.addPixmap(QtGui.QPixmap(":/tk-rv-shotgunreview/tack_hover.png"), QtGui.QIcon.Selected, QtGui.QIcon.On)
        self.pin_button.setIcon(icon1)
        self.pin_button.setCheckable(True)
        self.pin_button.setAutoRaise(True)
        self.pin_button.setObjectName("pin_button")
        self.horizontalLayout.addWidget(self.pin_button)
        self.horizontalLayout_2.addLayout(self.horizontalLayout)
        self.horizontalLayout_3.addWidget(self.widget)
        spacerItem1 = QtGui.QSpacerItem(40, 20, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
        self.horizontalLayout_3.addItem(spacerItem1)
        self.verticalLayout_3.addLayout(self.horizontalLayout_3)
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
        self.entity_version_view.setObjectName("entity_version_view")
        self.verticalLayout_2.addWidget(self.entity_version_view)
        self.entity_tab_widget.addTab(self.entity_version_tab, "")
        self.verticalLayout_17.addWidget(self.entity_tab_widget)

        self.retranslateUi(DetailsPanelWidget)
        self.entity_tab_widget.setCurrentIndex(0)
        QtCore.QMetaObject.connectSlotsByName(DetailsPanelWidget)

    def retranslateUi(self, DetailsPanelWidget):
        DetailsPanelWidget.setWindowTitle(QtGui.QApplication.translate("DetailsPanelWidget", "Form", None, QtGui.QApplication.UnicodeUTF8))
        self.shotgun_nav_button.setText(QtGui.QApplication.translate("DetailsPanelWidget", "...", None, QtGui.QApplication.UnicodeUTF8))
        self.entity_tab_widget.setTabText(self.entity_tab_widget.indexOf(self.entity_note_tab), QtGui.QApplication.translate("DetailsPanelWidget", "NOTES", None, QtGui.QApplication.UnicodeUTF8))
        self.entity_tab_widget.setTabText(self.entity_tab_widget.indexOf(self.entity_version_tab), QtGui.QApplication.translate("DetailsPanelWidget", "VERSIONS", None, QtGui.QApplication.UnicodeUTF8))

from ..qtwidgets import ActivityStreamWidget
from ..list_item_widget import ListItemWidget
from . import resources_rc
from . import resources_rc
from . import resources_rc
