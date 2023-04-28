from argparse import ArgumentParser
from asyncio import ensure_future, get_event_loop, run, create_task, set_event_loop

import sys

from PyQt5 import Qt, QtWidgets

from quamash import QEventLoop

from client.utils.client_proto import ChatClientProtocol, ClientAuth
from client.client_config import DB_PATH, PORT
from client.ui.windows import LoginWindow, ContactsWindow


class ConsoleClientApp:

    def __init__(self, parsed_args, db_path):
        self.args = parsed_args
        self.db_path = db_path
        self.ins = None

    def main(self):
        loop = get_event_loop()
        print(f"ох 1 - {loop}")

        # authentication process
        auth = ClientAuth(db_path=self.db_path)
        while True:
            usr = self.args["user"] or input('username: ')
            passwrd = self.args["password"] or input('password: ')
            auth.username = usr
            auth.password = passwrd
            is_auth = auth.authenticate()
            if is_auth:
                break
            else:
                print('wrong username/password')

        tasks = []
        client_ = ChatClientProtocol(db_path=self.db_path,
                                     loop=loop,
                                     username=usr,
                                     password=passwrd)
        try:
            coro = loop.create_connection(lambda: client_, self.args["addr"], self.args["port"])
            print(f"ох 2 - {coro}")
            transport, protocol = loop.run_until_complete(coro)
            print(f"ох 3 - {transport, protocol}")
        except ConnectionRefusedError:
            print('Error. wrong server')
            exit(1)
        try:
            task = loop.create_task(client_.get_from_console())
            print(f"ох 4 - {task}")
            tasks.append(task)
            loop.run_until_complete(task)

        except KeyboardInterrupt:
            pass
        except Exception as e:
            print(e)

        finally:
            loop.close()


class GuiClientApp:
    def __init__(self, parsed_args, db_path):
        self.args = parsed_args
        self.db_path = db_path
        self.ins = None

    def main(self):

        app = Qt.QApplication(sys.argv)
        loop = QEventLoop(app)
        set_event_loop(loop)
        login_wnd = LoginWindow()

        if login_wnd.exec_() == QtWidgets.QDialog.Accepted:
            pass


def parse_and_run():
    def parse_args():
        parser = ArgumentParser(description="Client settings")
        parser.add_argument("--user", default="user1", type=str)
        parser.add_argument("--password", default="123", type=str)
        parser.add_argument("--addr", default="127.0.0.1", type=str)
        parser.add_argument("--port", default=PORT, type=int)
        parser.add_argument('--nogui', action='store_true')
        return vars(parser.parse_args())

    args = parse_args()

    if args['nogui']:
        a = ConsoleClientApp(args, DB_PATH)
        a.main()
    else:
        a = GuiClientApp(args, DB_PATH)
        a.main()


if __name__ == '__main__':
    parse_and_run()
