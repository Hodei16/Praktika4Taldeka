import requests
import urllib
import webbrowser
from socket import AF_INET, socket, SOCK_STREAM
import json
import helper

app_key = 'v74fb7fa456d1lq'
app_secret = 'f8ggfd5sb533ufu'
server_addr = "localhost"
server_port = 8070
redirect_uri = "http://" + server_addr + ":" + str(server_port)


class Dropbox:
    _access_token = ""
    _path = "/"
    _files = []
    _root = None
    _msg_listbox = None

    def __init__(self, root):
        self._root = root

    def local_server(self):
        server_socket = socket(AF_INET, SOCK_STREAM)
        server_socket.bind((server_addr, server_port))
        server_socket.listen(1)
        print("\tLocal server listening on port " + str(server_port))

        client_connection, client_address = server_socket.accept()
        peticion = client_connection.recv(1024)
        print("\tRequest from the browser received at local server:")
        print(peticion)

        primera_linea = peticion.decode('UTF8').split('\n')[0]
        aux_auth_code = primera_linea.split(' ')[1]
        auth_code = aux_auth_code[7:].split('&')[0]
        print("\tauth_code: " + auth_code)

        http_response = "HTTP/1.1 200 OK\r\n\r\n" \
                        "<html>" \
                        "<head><title>Proba</title></head>" \
                        "<body>The authentication flow has completed. Close this window.</body>" \
                        "</html>"
        client_connection.sendall(http_response)
        client_connection.close()
        server_socket.close()

        return auth_code

    def do_oauth(self):
        baimen_url = f"https://www.dropbox.com/oauth2/authorize?client_id={app_key}&response_type=code&redirect_uri={redirect_uri}"
        webbrowser.open(baimen_url)
        kodea = self.local_server()

        token_uri = "https://api.dropboxapi.com/oauth2/token"
        datuak = {
            'code': kodea,
            'grant_type': 'authorization_code',
            'client_id': app_key,
            'client_secret': app_secret,
            'redirect_uri': redirect_uri
        }
        erantzuna = requests.post(token_uri, data=datuak)
        self._access_token = erantzuna.json()['access_token']
        self._root.destroy()

    def list_folder(self, msg_listbox):
        uri = 'https://api.dropboxapi.com/2/files/list_folder'
        goiburuak = {
            'Authorization': f'Bearer {self._access_token}',
            'Content-Type': 'application/json'
        }
        bidea = "" if self._path == "/" else self._path
        datuak = {'path': bidea}
        erantzuna = requests.post(uri, headers=goiburuak, json=datuak)
        edukia_json = erantzuna.json()

        self._files = helper.update_listbox2(msg_listbox, self._path, edukia_json)

    def transfer_file(self, file_path, file_data):
        uri = 'https://content.dropboxapi.com/2/files/upload'
        goiburuak = {
            'Authorization': f'Bearer {self._access_token}',
            'Content-Type': 'application/octet-stream',
            'Dropbox-API-Arg': json.dumps({
                'path': file_path,
                'mode': 'add',
                'autorename': True,
                'mute': False,
                'strict_conflict': False
            })
        }
        requests.post(uri, headers=goiburuak, data=file_data)

    def delete_file(self, file_path):
        uri = 'https://api.dropboxapi.com/2/files/delete_v2'
        goiburuak = {
            'Authorization': f'Bearer {self._access_token}',
            'Content-Type': 'application/json'
        }
        datuak = {'path': file_path}
        requests.post(uri, headers=goiburuak, json=datuak)

    def create_folder(self, path):
        uri = 'https://api.dropboxapi.com/2/files/create_folder_v2'
        goiburuak = {
            'Authorization': f'Bearer {self._access_token}',
            'Content-Type': 'application/json'
        }
        datuak = {'path': path}
        requests.post(uri, headers=goiburuak, json=datuak)