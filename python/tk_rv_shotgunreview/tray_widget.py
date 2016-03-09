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
    Simple list *item* widget which hosts a square thumbnail, header text
    and body text. It has a fixed size. Multiple of these items are typically
    put together inside a QListView to form a list.
    
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
        # make sure this widget isn't shown  WHY????
        self.setVisible(True)
        
        # set up the UI
        self.ui = Ui_TrayWidget() 
        self.ui.setupUi(self)
        
    def set_actions(self, actions):
        """
        Adds a list of QActions to add to the actions menu for this widget.
        """
        # print "TRAY WIDGET set_actions"
        pass
        # if len(actions) == 0:
        #     self.ui.button.setVisible(False)
        # else:
        #     self.ui.button.setVisible(True)
        #     self._actions = actions
        #     for a in self._actions:
        #         self._menu.addAction(a)
                                    
    def set_selected(self, selected, in_mini_cut=False):
        """
        Adjust the style sheet to indicate selection or not,
        added mini - cut support however selection is not always
        the center point due to tracking timeline?
        """        
        if selected:
            self.ui.thumbnail.setStyleSheet("QLabel { border: 4px solid rgb(40,136,175); }")
        else:
            # if in_mini_cut:
            #     self.ui.thumbnail.setStyleSheet("QLabel { border: 2px solid #444444; }")
            # else:
            #     self.ui.thumbnail.setStyleSheet("QLabel { border: 1px solid #000000; }")
            self.ui.thumbnail.setStyleSheet("QLabel { border: 1px solid #000000; }")
 
                #self.ui.thumbnail.setAttribute(QtCore.Qt.WA_TranslucentBackground)
        #self.ui.thumbnail.style().unpolish(self.ui.thumbnail)
        #self.ui.thumbnail.style().polish(self.ui.thumbnail)
        #self.ui.thumbnail.update()
         

    def set_thumbnail(self, pixmap):
        """
        Set a thumbnail given the current pixmap.
        """
        # pixmap.fill(QtCore.Qt.transparent)
        self.ui.thumbnail.setPixmap(pixmap)
            
    def set_text(self, header, body):
        """
        Populate the lines of text in the widget
        """
        pass
        # self.setToolTip("%s\n%s" % (header, body))        

    def sizeHint(self):
        return QtCore.QSize(114, 64)

    @staticmethod
    def calculate_size():
        """
        Calculates and returns a suitable size for this widget.
        """        
        return QtCore.QSize(114, 64)

