# Copyright (c) 2016 Shotgun Software Inc.
# 
# CONFIDENTIAL AND PROPRIETARY
# 
# This work is provided "AS IS" and subject to the Shotgun Pipeline Toolkit 
# Source Code License included in this distribution package. See LICENSE.
# By accessing, using, copying or modifying this work you indicate your 
# agreement to the Shotgun Pipeline Toolkit Source Code License. All rights 
# not expressly granted therein are reserved by Shotgun Software Inc.

from .ui_tray_widget import Ui_TrayWidget

import tank

from tank.platform.qt import QtCore, QtGui

class TrayWidget(QtGui.QWidget):
    """    
    This class is typically used in conjunction with a QT View and the 
    ShotgunDelegate class. 

    This has been hacked up at the moment to be just a thumbnail scroller.
    """
    clicked = QtCore.Signal(int)

    def __init__(self, parent):
        """
        Constructor
        """
        QtGui.QWidget.__init__(self, parent)
       
        # set up the UI
        self.ui = Ui_TrayWidget() 
        self.ui.setupUi(self)
        # make sure this widget isn't shown  WHY????
        self.setVisible(False)
        self.hintSize = None
        self.parent = parent

        
    def set_actions(self, actions):
        """
        Adds a list of QActions to add to the actions menu for this widget.
        """
        # print "TRAY WIDGET set_actions"
        pass
                                    
    def set_selected(self, selected, in_mini_cut=False):
        """
        Adjust the style sheet to indicate selection or not,
        """        
        if selected:
            self.ui.thumbnail.setStyleSheet("QLabel { border: 2px solid rgb(40,136,175); }")
        else:
            self.ui.thumbnail.setStyleSheet("QLabel { border: 0px solid rgb(37,38,41); }")
          

    def set_thumbnail(self, pixmap):
        """
        Set a thumbnail given the current pixmap.
        """
        self.ui.thumbnail.setPixmap(pixmap)
        self.resize(pixmap.size())
        if pixmap.height() < 74:
            self.parent.resize(self.parent.width(), 74)
        else:
            self.parent.resize(self.parent.width(), pixmap.height())
            
    def set_text(self, header, body):
        """
        Populate the lines of text in the widget
        """
        pass

    def sizeHint(self):
        #  = QtCore.QSize(self.ui.thumbnail.width() * 2, self.ui.thumbnail.height()*2)
        # return s
        # return QtCore.QSize(96, 54)
        #self.parent.resize(self.parent.width(), 74)
        return self.ui.thumbnail.size()

    # @staticmethod
    # def calculate_size():
    #     """
    #     Calculates and returns a suitable size for this widget.
    #     """ 
    #     #return self.ui.thumbnail.size()       
    #     return QtCore.QSize(114, 64)

