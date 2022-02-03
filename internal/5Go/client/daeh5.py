import queue
from contextlib import contextmanager
from dataclasses import dataclass
from threading import Condition
from typing import Any

import grpc
import synapsis
from google.protobuf.empty_pb2 import Empty

# Am I a package?..
try:
    from .proto.neuron_pb2 import (
        Request,
        AddDocumentRequest,
        GetDocumentRequest,
        ListDocumentsRequest,
        ListDocumentsResponse,
        Document,
    )
    from .proto.neuron_pb2_grpc import NeuronAPIStub
    from .proto.neurotransmitter_pb2 import AsymmetricKey, SerializedStuff
except ImportError:
    from proto.neuron_pb2 import (
        Request,
        AddDocumentRequest,
        GetDocumentRequest,
        ListDocumentsRequest,
        ListDocumentsResponse,
        Document,
    )
    from proto.neuron_pb2_grpc import NeuronAPIStub
    from proto.neurotransmitter_pb2 import AsymmetricKey, SerializedStuff


@dataclass
class Session:
    q: queue.Queue
    shared: bytes
    stream: Any
    cond: Condition

    def add_document(self, user: str, content: str, name: str):
        req = Request()
        req.add.CopyFrom(AddDocumentRequest(
            user=user,
            content=content,
            name=name,
        ))
        self.send(req)
        resp = Document()
        self.recv(resp)
        return resp

    def get_document(self, doc_id: str):
        req = Request()
        req.get.CopyFrom(GetDocumentRequest(
            id=doc_id,
        ))
        self.send(req)
        resp = Document()
        self.recv(resp)
        return resp

    def list_documents(self, user: str):
        req = Request()
        req.list.CopyFrom(ListDocumentsRequest(
            user=user,
        ))
        self.send(req)
        resp = ListDocumentsResponse()
        self.recv(resp)
        return resp.documents

    def send(self, req: Request):
        content = req.SerializeToString()
        serialized = SerializedStuff(content=content).SerializeToString()
        enc = synapsis.encrypt(self.shared, serialized)
        self.q.put(SerializedStuff(content=enc))

    def recv(self, dst):
        resp: SerializedStuff = next(self.stream)
        dec = synapsis.decrypt(self.shared, resp.content)
        stuff = SerializedStuff()
        stuff.ParseFromString(dec)
        dst.ParseFromString(stuff.content)

    def close(self):
        self.q.put(None)
        with self.cond:
            self.cond.wait(5)


class Daeh5:
    def __init__(self, url: str):
        self.url = url
        self.channel = grpc.insecure_channel(url)
        self.stub = NeuronAPIStub(channel=self.channel)

    def ping(self):
        return self.stub.Ping(Empty())

    @contextmanager
    def session(self) -> Session:
        q = queue.Queue()
        cond = Condition()
        stream = self.stub.Session(self._queue_sender(q, cond))
        shared = self.setup_handshake(q, stream)
        session = Session(
            q=q,
            stream=stream,
            shared=shared,
            cond=cond,
        )
        try:
            yield session
        finally:
            session.close()

    @staticmethod
    def setup_handshake(q, stream):
        private_key = synapsis.generate_key()
        parsed_key = AsymmetricKey()
        parsed_key.ParseFromString(private_key)

        q.put(parsed_key.public_key)
        resp: SerializedStuff = next(stream)
        server_public_key = SerializedStuff(content=resp.content).SerializeToString()
        shared_key = synapsis.generate_shared(private_key, server_public_key)
        return shared_key

    @staticmethod
    def _queue_sender(q: queue.Queue, cond: Condition):
        while True:
            value = q.get()
            if value is None:  # queue is closed
                with cond:
                    cond.notify_all()
                return
            yield value
