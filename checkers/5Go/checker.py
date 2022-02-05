#!/usr/bin/env python3

import random
import re
import string
from collections import defaultdict

import google.protobuf.message
import grpc
import sys
from checklib import *

from client import Daeh5

PORT = 5005


class Checker(BaseChecker):
    vulns: int = 1
    timeout: int = 20
    uses_attack_data: bool = True

    def __init__(self, *args, **kwargs):
        super(Checker, self).__init__(*args, **kwargs)
        self.d = Daeh5(f'{self.host}:{PORT}')

    def action(self, action, *args, **kwargs):
        try:
            super(Checker, self).action(action, *args, **kwargs)
        except grpc.RpcError as e:
            if e.code() == grpc.StatusCode.UNAVAILABLE:
                self.cquit(Status.DOWN, 'Connection error', f'Got grpc error {e.code()}: {e.details()}')
            else:
                self.cquit(Status.MUMBLE, 'Unexpected grpc error', f'Got grpc error {e.code()}: {e.details()}')
        except google.protobuf.message.DecodeError as e:
            self.cquit(Status.MUMBLE, 'Protobuf parsing error', f'Got error parsing protobuf: {e}')

    def check(self):
        self.d.ping()
        with self.d.session() as session1:
            created = defaultdict(list)
            users = [rnd_username(32) for _ in range(random.randint(2, 3))]
            users += [rnd_string(i) for i in range(5, 10, 2)]
            users = random.sample(users, 5)
            for _ in range(random.randint(10, 20)):
                user = random.choice(users)
                content = rnd_string(random.randint(24, 348), alphabet=string.printable)
                name = rnd_string(random.choice((7, 8, 10, 11, 13, 14)))
                doc = session1.add_document(user, content, name)
                self.check_doc_id(doc.id, name)
                real_doc = session1.get_document(doc.id)
                self.assert_docs_equal(doc, real_doc)
                created[user].append(doc)

            with self.d.session() as session2:
                check_session = random.choice([session1, session2])
                random.shuffle(users)
                for user in users:
                    lst = check_session.list_documents(user)
                    self.assert_gte(len(lst), len(created[user]), 'Invalid number of documents for user')
                    for x, y in zip(lst, created[user]):
                        self.assert_docs_equal(x, y)

            with self.d.session() as session3:
                check_session = random.choice([session1, session3])
                random.shuffle(users)
                for user in users:
                    lst = check_session.list_documents(user)
                    self.assert_gte(len(lst), len(created[user]), 'Invalid number of documents for user')
                    for x, y in zip(lst, created[user]):
                        self.assert_docs_equal(x, y)
                random.shuffle(users)
                for user, docs in created.items():
                    random.shuffle(docs)
                    for doc in docs:
                        if random.randint(0, 2) == 0:
                            real_doc = check_session.get_document(doc.id)
                            self.assert_docs_equal(doc, real_doc)

        self.cquit(Status.OK)

    def put(self, flag_id, flag, vuln):
        user = rnd_username(32)
        part1 = rnd_string(random.randint(12, 150), alphabet=string.printable)
        part2 = rnd_string(random.randint(12, 150), alphabet=string.printable)
        content = f'{part1} {flag} {part2}'
        name = rnd_string(10)
        with self.d.session() as session:
            doc = session.add_document(user, content, name)
        self.check_doc_id(doc.id, name)
        self.cquit(Status.OK, name, f'{user}:{doc.id}')

    def get(self, flag_id, flag, vuln):
        user, doc_id = flag_id.split(':')
        with self.d.session() as session:
            doc = session.get_document(doc_id)
            self.assert_eq(doc.user, user, 'Invalid document returned', status=Status.CORRUPT)
            self.assert_eq(doc.id, doc_id, 'Invalid document returned', status=Status.CORRUPT)
            self.assert_in(flag, doc.content, 'Invalid document returned', status=Status.CORRUPT)

        with self.d.session() as session:
            docs = session.list_documents(user)
            self.assert_gte(len(docs), 1, 'Invalid document listing', status=Status.CORRUPT)

            doc = docs[0]
            self.assert_eq(doc.user, user, 'Invalid document returned', status=Status.CORRUPT)
            self.assert_eq(doc.id, doc_id, 'Invalid document returned', status=Status.CORRUPT)
            self.assert_in(flag, doc.content, 'Invalid document returned', status=Status.CORRUPT)

        self.cquit(Status.OK)

    def check_doc_id(self, doc_id, name, st=Status.MUMBLE):
        pattern = re.compile(rf"^{name}-[0-9a-f]{{8}}-[0-9a-f]{{4}}-[0-9a-f]{{4}}-[0-9a-f]{{4}}-[0-9a-f]{{12}}$")
        self.assert_neq(pattern.match(doc_id), None, 'Invalid document ID', status=st)

    def assert_docs_equal(self, doc1, doc2, st=Status.MUMBLE):
        self.assert_eq(doc1.id, doc2.id, 'Invalid document returned', status=st)
        self.assert_eq(doc1.user, doc2.user, 'Invalid document returned', status=st)
        self.assert_eq(doc1.content, doc2.content, 'Invalid document returned', status=st)
        self.assert_eq(
            doc1.created_at.ToMicroseconds(),
            doc2.created_at.ToMicroseconds(),
            'Invalid document returned',
            status=st,
        )


if __name__ == '__main__':
    c = Checker(sys.argv[2])
    try:
        c.action(sys.argv[1], *sys.argv[3:])
    except c.get_check_finished_exception():
        cquit(Status(c.status), c.public, c.private)
