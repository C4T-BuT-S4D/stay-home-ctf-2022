import requests
from checklib import *

PORT = 1337

class CheckMachine:
    @property
    def url(self):
        return f'http://{self.c.host}:{self.port}'

    def __init__(self, checker: BaseChecker):
        self.c = checker
        self.port = PORT

    def register(self, session: requests.Session, username: str, password: str):
        pass

    def login(self, session: requests.Session, username: str, password: str, status: Status):
        pass

    def put_note(self, session: requests.Session, note_name: str, note_value: str):
        url = f'{self.url}/put_note'

        response = session.post(url, json={
            "name": note_name,
            "value": note_value,
        })

        data = self.c.get_json(response, "Invalid response on put_note")
        self.c.assert_eq(type(data), dict, "Invalid response on put_note")
        self.c.assert_in("ok", data, "Invalid response on put_note")
        self.c.assert_eq(data["ok"], True, "Can't put note")

    def get_note(self, session: requests.Session, note_name: str, status: Status) -> str:
        url = f'{self.url}/get_note'

        response = session.post(url, json={
            "name": note_name,
        })

        data = self.c.get_json(response, "Invalid response on get_note", status)
        self.c.assert_eq(type(data), dict, "Invalid response on get_note", status)
        self.c.assert_in("ok", data, "Invalid response on get_note", status)
        self.c.assert_in("note", data, "Invalid response on put_note", status)
        self.c.assert_eq(type(data["note"]), str, "Invalid response on put_note", status)
        self.c.assert_eq(data["ok"], True, "Can't get note", status)

        return data["note"]
