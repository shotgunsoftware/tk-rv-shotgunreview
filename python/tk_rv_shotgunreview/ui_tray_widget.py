# -*- coding: utf-8 -*-

from tank.platform.qt import QtCore, QtGui

class Ui_TrayWidget(object):
    def setupUi(self, TrayWidget):
        TrayWidget.setObjectName("TrayWidget")
        # TrayWidget.resize(394, 93)
        
        self.horizontalLayout_3 = QtGui.QHBoxLayout(TrayWidget)
        self.horizontalLayout_3.setSpacing(1)
        self.horizontalLayout_3.setContentsMargins(1, 1, 1, 1)
        self.horizontalLayout_3.setObjectName("horizontalLayout_3")


        self.box = QtGui.QFrame(TrayWidget)
        self.box.setObjectName("tray_box")
        
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(1)
        sizePolicy.setVerticalStretch(0)
        self.box.setSizePolicy(sizePolicy)


        self.horizontalLayout_2 = QtGui.QHBoxLayout(self.box)
        self.horizontalLayout_2.setSpacing(0)
        self.horizontalLayout_2.setContentsMargins(1, 1, 1, 1)
        self.horizontalLayout_2.setObjectName("horizontalLayout_2")
        
        self.thumbnail = QtGui.QLabel(self.box)
        self.thumbnail.setText("")
        self.thumbnail.setScaledContents(True)
        self.thumbnail.setAlignment(QtCore.Qt.AlignCenter)
        self.thumbnail.setObjectName("thumbnail")
        
        self.horizontalLayout_2.addWidget(self.thumbnail)
        
        self.verticalLayout = QtGui.QVBoxLayout()
        self.verticalLayout.setObjectName("verticalLayout")
        
        self.horizontalLayout = QtGui.QHBoxLayout()
        self.horizontalLayout.setObjectName("horizontalLayout")
        
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        
        self.verticalLayout.addLayout(self.horizontalLayout)


        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)

        self.horizontalLayout_2.addLayout(self.verticalLayout)
        self.horizontalLayout_3.addWidget(self.box)

        self.retranslateUi(TrayWidget)
        QtCore.QMetaObject.connectSlotsByName(TrayWidget)

    def retranslateUi(self, TrayWidget):
        pass
        #TrayWidget.setWindowTitle(QtGui.QApplication.translate("TrayWidget", "Form", None, QtGui.QApplication.UnicodeUTF8))
        #self.header_label.setText(QtGui.QApplication.translate("TrayWidget", "Header", None, QtGui.QApplication.UnicodeUTF8))
        #self.button.setText(QtGui.QApplication.translate("TrayWidget", "Actions", None, QtGui.QApplication.UnicodeUTF8))
        #self.body_label.setText(QtGui.QApplication.translate("TrayWidget", "TextLabel\n"
        # "Foo\n"
        # "Bar", None, QtGui.QApplication.UnicodeUTF8))

#from . import resources_rc