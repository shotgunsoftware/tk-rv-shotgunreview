
import tank
shotgun_version_details = tank.platform.import_framework("tk-framework-qtwidgets", "version_details")


class VersionContextMenu(shotgun_version_details.selection_context_menu.SelectionContextMenu):

    def execute_callback(self, action):
        """
        Execute's the given action's callback method, as defined when
        it was added to the menu using addAction.

        :param action:  The QAction to use when looking up which callback
                        to execute.
        """
        if action:
            callback = self._actions[action]["callback"]
            callback(self._selected_entities, action)