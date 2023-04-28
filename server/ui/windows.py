from PyQt5.QtWidgets import QMainWindow
from server.ui.server_monitor_ui import Ui_ServerWindow as server_ui_class


class ServerMonitorWindow(QMainWindow):

    def __init__(self, parent=None):
        super().__init__(parent)

        self.ui = server_ui_class()
        self.ui.setupUi(self)

    def closeEvent(self, event):

        self.server_instance._cm.dal.session.close()

    def after_start(self):


        self.update_clients()

    def update_clients(self):

        contacts = self.server_instance.get_all_clients()
        self.ui.clients_list.clear()
        self.ui.clients_list.addItems(
            [contact.username for contact in contacts])

    def update_history_messages(self, username):

        self.ui.msg_history_list.clear()
        msgs = self.server_instance.get_client_history(username)
        _resp = [m.time.strftime(
            "%Y-%m-%d %H:%M:%S") + '_' + m.ip_addr + '_' + m.client.username
                 for m in msgs]
        self.ui.msg_history_list.addItems(_resp)

    def on_clients_list_itemDoubleClicked(self):

        selected_client = self.ui.clients_list.currentItem().text()
        self.update_history_messages(selected_client)
        self.ui.tabWidgetClients.setCurrentIndex(1)  # set history tab active

    def refresh_action(self):


        print('refresh')
        self.update_clients()
