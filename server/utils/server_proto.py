from asyncio import Protocol
from hashlib import pbkdf2_hmac
from binascii import hexlify
from functools import wraps

from server.utils.server_messages import JimServerMessage
from server.utils.mixins import ConvertMixin, DbInterfaceMixin


class ChatServerProtocol(Protocol, ConvertMixin, DbInterfaceMixin):

    def __init__(self, db_path, connections, users):
        super().__init__(db_path)
        self.connections = connections
        self.users = users
        self.jim = JimServerMessage()

        self.user = None
        self.transport = None

    def connection_made(self, transport):

        self.connections[transport] = {
            'peername': transport.get_extra_info('peername'),
            'username': '',
            'transport': transport
        }
        self.transport = transport

    def eof_received(self):
        self.transport.close()

    def connection_lost(self, exc):
        """Transport Error , which means the client is disconnected."""

        if isinstance(exc, ConnectionResetError):
            print('ConnectionResetError')
            print(self.connections)
            print(self.users)

        rm_con = []
        for con in self.connections:
            if con._closing:
                rm_con.append(con)

        for i in rm_con:
            del self.connections[i]

        rm_user = []
        for k, v in self.users.items():
            for con in rm_con:
                if v['transport'] == con:
                    rm_user.append(k)

        for u in rm_user:
            del self.users[u]
            self.set_user_offline(u)
            print('{} disconnected'.format(u))

    def _login_required(func):
        """Login required decorator, which accepts only authorized clients"""

        @wraps(func)
        def wrapper(self, *args, **kwargs):
            is_auth = self.get_user_status(self.user)
            # print('is_auth status: {}'.format(is_auth))
            if is_auth:
                result = func(self, *args, **kwargs)
                return result
            else:
                resp_msg = self.jim.response(code=501, error='login required')
                self.users[self.user]['transport'].write(
                    self._dict_to_bytes(resp_msg))

        return wrapper

    def authenticate(self, username, password):
        if username and password:
            usr = self.get_client_by_username(username)
            dk = pbkdf2_hmac('sha256', password.encode('utf-8'),
                                     'salt'.encode('utf-8'), 100000)
            hashed_password = hexlify(dk)

            if usr:
                if hashed_password == usr.password:
                    self.add_client_history(username)
                    return True
                else:
                    return False
            else:
                print('new user')
                self.add_client(username, hashed_password)
                self.add_client_history(username)
                return True
        else:
            return False

    @_login_required
    def action_msg(self, data):
        try:
            if data['from']:
                print(data)

                self._cm.add_client_message(data['from'], data['to'], data['message'])

                self.users[data['from']]['transport'].write(self._dict_to_bytes(data))

            if data['to'] and data['from'] != data['to']:
                try:
                    self.users[data['to']]['transport'].write(self._dict_to_bytes(data))
                except KeyError:
                    print('{} is not connected yet'.format(data['to']))

        except Exception as e:
            resp_msg = self.jim.response(code=500, error=e)
            self.transport.write(self._dict_to_bytes(resp_msg))

    def data_received(self, data):
        """The protocol expects a json message in bytes"""

        _data = self._bytes_to_dict(data)
        print(_data)
        if _data:
            try:
                if _data['action'] == 'msg':
                    self.user = _data['from']
                    self.action_msg(_data)

                elif _data['action'] == 'list':
                    self.user = _data['user']['account_name']
                    self.action_list(_data)

                elif _data['action'] == 'presence':
                    if _data['user']['account_name']:

                        print(self.user, _data['user']['status'])
                        resp_msg = self.jim.response(code=200)
                        self.transport.write(self._dict_to_bytes(resp_msg))
                    else:
                        resp_msg = self.jim.response(code=500, error='wrong presence msg')
                        self.transport.write(self._dict_to_bytes(resp_msg))

                elif _data['action'] == 'authenticate':
                    # todo complete this
                    if self.authenticate(_data['user']['account_name'], _data['user']['password']):

                        # add new user to temp variables
                        if _data['user']['account_name'] not in self.users:
                            self.user = _data['user']['account_name']
                            self.connections[self.transport]['username'] = self.user
                            self.users[_data['user']['account_name']] = self.connections[self.transport]
                            self.set_user_online(_data['user']['account_name'])

                        resp_msg = self.jim.probe(self.user)
                        self.users[_data['user']['account_name']]['transport'].write(self._dict_to_bytes(resp_msg))
                    else:
                        resp_msg = self.jim.response(code=402, error='wrong login/password')
                        self.transport.write(self._dict_to_bytes(resp_msg))

            except Exception as e:
                resp_msg = self.jim.response(code=500, error=e)
                self.transport.write(self._dict_to_bytes(resp_msg))

        else:
            resp_msg = self.jim.response(code=500, error='You sent a message without a name or data')
            self.transport.write(self._dict_to_bytes(resp_msg))
