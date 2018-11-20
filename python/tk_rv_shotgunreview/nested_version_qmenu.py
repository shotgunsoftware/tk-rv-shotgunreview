
from tank.platform.qt import QtCore, QtGui


class VersionCollectionVersion(object):
    def __init__(self, version):
        self.version = version

    def __eq__(self, other):
        return self.version["id"] == other.version["id"]

    def __getitem__(self, key):
        return self.version[key]


class VersionCollectionNode(object):
    def __init__(self, name):
        self.name = name
        self.nodes = []
        self.versions = []

    def __contains__(self, item):
        return bool(self.get(item))

    def get(self, item):
        for node in self.nodes:
            if node.name == item:
                return node
        return None

    def append_node(self, node):
        self.nodes.append(node)

    def append_version(self, version):
        self.versions.append(version)

    def get_subversions(self, versions=None):
        vs = versions or []
        for node in self.nodes:
            [vs.append(v) for v in node.get_subversions(vs) if v not in vs]
            [vs.append(v) for v in node.versions if v not in vs]
        return vs


class NestedVersionQMenu(QtGui.QMenu):

    def __init__(self, rv_mode, parent_menu, name, versions,
                 nested_keys=None, compare_all=True, truncate=None):
        super(NestedVersionQMenu, self).__init__(name)

        self._rv_mode = rv_mode
        self._parent_menu = parent_menu
        self._compare_all = compare_all
        self._truncate = truncate

        # Build the VersionCollectionNode tree
        self.node = VersionCollectionNode(name)
        for version in versions:
            node = self.node
            for key in nested_keys:
                if not version.get(key):
                    break

                if version[key] not in node:
                    curr_node = VersionCollectionNode(version[key])
                    node.append_node(curr_node)
                else:
                    curr_node = node.get(version[key])

                node = curr_node

            node.append_version(VersionCollectionVersion(version))

        self._build_menu(self, self.node)

    def _build_menu(self, menu, node):
        for subnode in node.nodes:
            submenu = QtGui.QMenu(subnode.name)
            # If self._truncate is True, we clip the singleton nodes
            if (self._truncate and len(subnode.nodes) == 0 and
                        len(subnode.versions) == 1):
                self._add_action(menu, subnode.name, subnode.versions)
            else:
                self._build_menu(submenu, subnode)
                menu.addMenu(submenu)

        for version in node.versions:
            self._add_action(menu, version["code"], [version])

        subversions = node.get_subversions() + node.versions
        if len(subversions) > 1:
            self._add_action(menu, "(Compare All)", subversions)

    def _add_action(self, menu, text, versions):
        # NOTE: Continuing to use action_definition structure in case
        #   we pull this into a library at some point.
        #   -- @JoshBurnell
        action_definition = {
            "callback": self._rv_mode._compare_with_versions,
            "text": text,
            "versions": versions
        }

        action = QtGui.QAction(action_definition["text"], menu)
        action._versions = action_definition["versions"]
        self._parent_menu._actions[action] = action_definition
        menu.addAction(action)