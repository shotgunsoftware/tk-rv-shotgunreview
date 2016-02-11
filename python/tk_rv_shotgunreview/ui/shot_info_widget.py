# Copyright (c) 2016 Shotgun Software Inc.
# 
# CONFIDENTIAL AND PROPRIETARY
# 
# This work is provided "AS IS" and subject to the Shotgun Pipeline Toolkit 
# Source Code License included in this distribution package. See LICENSE.
# By accessing, using, copying or modifying this work you indicate your 
# agreement to the Shotgun Pipeline Toolkit Source Code License. All rights 
# not expressly granted therein are reserved by Shotgun Software Inc.

from tank.platform.qt import QtCore, QtGui

class Ui_ShotInfoWidget(object):
    def setupUi(self, ShotInfoWidget):
        # self.font = QtGui.QFontDatabase.addApplicationFont('/Users/stewartb/git/tk-rv/python/tk_rv/fonts/ProximaNova-Reg.otf')
        # ShotInfoWidget.setFont(QtGui.QFont('Proxima Nova Regular', 30))
        ShotInfoWidget.setObjectName("ShotInfoWidget")
        ShotInfoWidget.resize(500, 100)
        
        self.horizontalLayout_3 = QtGui.QHBoxLayout(ShotInfoWidget)
        self.horizontalLayout_3.setSpacing(1)
        self.horizontalLayout_3.setContentsMargins(1, 1, 1, 1)
        self.horizontalLayout_3.setObjectName("horizontalLayout_3")
        
        self.box = QtGui.QFrame(ShotInfoWidget)
        # self.box.setFrameShape(QtGui.QFrame.StyledPanel)
        # self.box.setFrameShadow(QtGui.QFrame.Raised)
        self.box.setObjectName("box")
        
        self.horizontalLayout_2 = QtGui.QHBoxLayout(self.box)
        self.horizontalLayout_2.setSpacing(4)
        self.horizontalLayout_2.setContentsMargins(1, 2, 1, 2)
        self.horizontalLayout_2.setObjectName("horizontalLayout_2")
        
        self.thumbnail = QtGui.QLabel(self.box)
        self.thumbnail.setMinimumSize(QtCore.QSize(175, 75))
        self.thumbnail.setMaximumSize(QtCore.QSize(175, 75))
        self.thumbnail.setText("")
        self.thumbnail.setScaledContents(True)
        self.thumbnail.setAlignment(QtCore.Qt.AlignCenter)
        self.thumbnail.setObjectName("thumbnail")
        
        self.horizontalLayout_2.addWidget(self.thumbnail)
        
        self.verticalLayout = QtGui.QVBoxLayout()
        self.verticalLayout.setObjectName("verticalLayout")
        
        self.horizontalLayout = QtGui.QHBoxLayout()
        self.horizontalLayout.setObjectName("horizontalLayout")
        
        self.header_label = QtGui.QLabel(self.box)
        
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.header_label.sizePolicy().hasHeightForWidth())
        
        self.header_label.setSizePolicy(sizePolicy)
        self.header_label.setObjectName("header_label")
        # self.header_label.setStyleSheet("QLabel { font-family: Proxima Nova; }")
        
        self.horizontalLayout.addWidget(self.header_label)
        
        self.button = QtGui.QToolButton(self.box)
        self.button.setPopupMode(QtGui.QToolButton.InstantPopup)
        self.button.setToolButtonStyle(QtCore.Qt.ToolButtonTextOnly)
        self.button.setObjectName("button")
        
        self.horizontalLayout.addWidget(self.button)
        
        self.verticalLayout.addLayout(self.horizontalLayout)
        
        self.body_label = QtGui.QLabel(self.box)
        
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.body_label.sizePolicy().hasHeightForWidth())
        
        self.body_label.setSizePolicy(sizePolicy)
        self.body_label.setAlignment(QtCore.Qt.AlignLeading|QtCore.Qt.AlignLeft|QtCore.Qt.AlignTop)
        self.body_label.setWordWrap(True)
        self.body_label.setObjectName("body_label")
        # self.body_label.setStyleSheet("QLabel { font-family: Proxima Nova; font-size: 21pt; }")
        
        self.verticalLayout.addWidget(self.body_label)
        self.horizontalLayout_2.addLayout(self.verticalLayout)
        self.horizontalLayout_3.addWidget(self.box)

        self.retranslateUi(ShotInfoWidget)
        QtCore.QMetaObject.connectSlotsByName(ShotInfoWidget)

    def retranslateUi(self, ShotInfoWidget):
        ShotInfoWidget.setWindowTitle(QtGui.QApplication.translate("ShotInfoWidget", "Form", None, QtGui.QApplication.UnicodeUTF8))
        self.header_label.setText(QtGui.QApplication.translate("ShotInfoWidget", "Header", None, QtGui.QApplication.UnicodeUTF8))
        self.button.setText(QtGui.QApplication.translate("ShotInfoWidget", "Actions", None, QtGui.QApplication.UnicodeUTF8))
        self.body_label.setText(QtGui.QApplication.translate("ShotInfoWidget", "TextLabel\n"
"Foo\n"
"Bar", None, QtGui.QApplication.UnicodeUTF8))

#from . import resources_rc
