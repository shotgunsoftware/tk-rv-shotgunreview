# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'list_item_widget.ui'
#
#      by: pyside-uic 0.2.15 running on PySide 1.2.4
#
# WARNING! All changes made in this file will be lost!

from tank.platform.qt import QtCore, QtGui

class Ui_ListItemWidget(object):
    def setupUi(self, ListItemWidget):
        ListItemWidget.setObjectName("ListItemWidget")
        ListItemWidget.resize(355, 75)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Maximum)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(ListItemWidget.sizePolicy().hasHeightForWidth())
        ListItemWidget.setSizePolicy(sizePolicy)
        ListItemWidget.setMaximumSize(QtCore.QSize(16777215, 75))
        self.horizontalLayout_3 = QtGui.QHBoxLayout(ListItemWidget)
        self.horizontalLayout_3.setSpacing(1)
        self.horizontalLayout_3.setContentsMargins(0, 0, 0, 0)
        self.horizontalLayout_3.setObjectName("horizontalLayout_3")
        self.box = QtGui.QFrame(ListItemWidget)
        self.box.setFrameShape(QtGui.QFrame.NoFrame)
        self.box.setFrameShadow(QtGui.QFrame.Plain)
        self.box.setObjectName("box")
        self.horizontalLayout_2 = QtGui.QHBoxLayout(self.box)
        self.horizontalLayout_2.setSpacing(5)
        self.horizontalLayout_2.setContentsMargins(2, 2, 2, 2)
        self.horizontalLayout_2.setObjectName("horizontalLayout_2")
        self.box_layout = QtGui.QHBoxLayout()
        self.box_layout.setSpacing(10)
        self.box_layout.setContentsMargins(0, -1, -1, -1)
        self.box_layout.setObjectName("box_layout")
        self.left_layout = QtGui.QVBoxLayout()
        self.left_layout.setObjectName("left_layout")
        spacerItem = QtGui.QSpacerItem(0, 0, QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Expanding)
        self.left_layout.addItem(spacerItem)
        self.box_layout.addLayout(self.left_layout)
        self.right_layout = QtGui.QVBoxLayout()
        self.right_layout.setContentsMargins(-1, 2, -1, 2)
        self.right_layout.setObjectName("right_layout")
        spacerItem1 = QtGui.QSpacerItem(0, 0, QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Expanding)
        self.right_layout.addItem(spacerItem1)
        self.box_layout.addLayout(self.right_layout)
        self.horizontalLayout_2.addLayout(self.box_layout)
        self.horizontalLayout_3.addWidget(self.box)

        self.retranslateUi(ListItemWidget)
        QtCore.QMetaObject.connectSlotsByName(ListItemWidget)

    def retranslateUi(self, ListItemWidget):
        ListItemWidget.setWindowTitle(QtGui.QApplication.translate("ListItemWidget", "Form", None, QtGui.QApplication.UnicodeUTF8))

from . import resources_rc
