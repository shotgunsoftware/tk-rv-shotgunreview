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

class VersionContextMenu(QtGui.QMenu):
    """
    A QMenu that accepts VersionContextMenuAction actions. Each action
    is enabled or disabled according to its selection requirements and
    the reported number of selected items.
    """
    def __init__(self, num_selected, *args, **kwargs):
        """
        Constructs a new VersionContextMenu.

        :param num_selected:    The number of selected items to report to any
                                actions added to the menu. Each action will be
                                enabled or disabled based on their selection
                                requirements and the number given.
        """
        super(VersionContextMenu, self).__init__(*args, **kwargs)
        self._num_selected = num_selected

    def addAction(self, action):
        """
        Adds a VersionContextMenuAction to the menu.

        :param action:  The action to add to the menu.
        """
        if not isinstance(action, VersionContextMenuAction):
            raise TypeError("The given action must be of type VersionContextMenuAction.")

        single = VersionContextMenuAction.SingleSelectionRequired
        multi = VersionContextMenuAction.MultiSelectionRequired
        either = VersionContextMenuAction.SingleOrMultiSelectionRequired

        # Now we can enable or disable the action according to
        # how many items have been reported as being selected.
        if not self._num_selected:
            action.setEnabled(False)
        elif action.required_selection == single:
            action.setEnabled((self._num_selected == 1))
        elif action.required_selection == multi:
            action.setEnabled((self._num_selected > 1))
        elif action.required_selection == either:
            action.setEnabled(True)
        else:
            # This shouldn't ever happen.
            action.setEnabled(False)

        return super(VersionContextMenu, self).addAction(action)


class VersionContextMenuAction(QtGui.QAction):
    """
    A QAction with additional selection requirements. Each action requires
    one of a single item selected, multiple items selected, or one or more
    items selected.
    """

    SingleSelectionRequired = 1
    MultiSelectionRequired = 2
    SingleOrMultiSelectionRequired = 3

    def __init__(self, required_selection, *args, **kwargs):
        """
        Constructs a new VersionContextMenuAction.

        :param required_selection:  One of: VersionContextMenuAction.SingleSelectionRequired,
                                    VersionContextMenuAction.MultiSelectionRequired,
                                    VersionContextMenuAction.SingleOrMultiSelectionRequired.
        """
        super(VersionContextMenuAction, self).__init__(*args, **kwargs)
        self.required_selection = required_selection

        