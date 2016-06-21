from tank.platform.qt import QtCore, QtGui


class TrayDockWidget(QtGui.QDockWidget):

    def __init__(self, title, parent):
        """
        Constructor
        """
        self.orig = parent
        self.mc_widget = None
        QtGui.QDockWidget.__init__(self, title, parent) 


    def mouseMoveEvent(self, event):
        pass 
        #print "MOVE TrayDockWidget %r frame %r" % (event, self.mc_widget)
        # self.move(QtGui.QCursor.pos().x() - self.width()/2, QtGui.QCursor.pos().y())
        
        #if self.mc_widget :
        #    print "MOVING"
            # self.mc_widget.position_minicut()
