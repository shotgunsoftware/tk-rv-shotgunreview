# -*- coding: utf-8 -*-

from tank.platform.qt import QtCore, QtGui

class Ui_TrayWidget(object):

    def setupUi(self, TrayWidget):
        TrayWidget.setObjectName("TrayWidget")
        #TrayWidget.resize(114, 34)
        
        self.horizontalLayout_3 = QtGui.QHBoxLayout(TrayWidget)
        self.horizontalLayout_3.setSpacing(1)
        self.horizontalLayout_3.setContentsMargins(0, 0, 0, 0)
        self.horizontalLayout_3.setObjectName("horizontalLayout_3")

        self.box = QtGui.QFrame(TrayWidget)
        self.box.setObjectName("tray_box")
        
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)        
        sizePolicy.setHorizontalStretch(1)
        sizePolicy.setVerticalStretch(0)
        
        # self.box.setSizePolicy(sizePolicy)

        self.horizontalLayout_2 = QtGui.QHBoxLayout(self.box)
        self.horizontalLayout_2.setSpacing(1)
        self.horizontalLayout_2.setContentsMargins(2, 0, 2, 0)
        self.horizontalLayout_2.setObjectName("horizontalLayout_2")
        
        self.thumbnail = QtGui.QLabel(self.box)
        self.thumbnail.setText("")
        self.thumbnail.setScaledContents(True)
        self.thumbnail.setAlignment(QtCore.Qt.AlignCenter)
        self.thumbnail.setObjectName("thumbnail")
        
        self.horizontalLayout_2.addWidget(self.thumbnail)
        
        self.horizontalLayout = QtGui.QHBoxLayout()
        self.horizontalLayout.setObjectName("horizontalLayout")
        
        self.horizontalLayout_2.addLayout(self.horizontalLayout)
        self.horizontalLayout_3.addWidget(self.box)

        QtCore.QMetaObject.connectSlotsByName(TrayWidget)

 
