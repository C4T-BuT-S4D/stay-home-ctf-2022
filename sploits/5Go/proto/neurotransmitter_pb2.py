# -*- coding: utf-8 -*-
# Generated by the protocol buffer compiler.  DO NOT EDIT!
# source: neurotransmitter.proto
"""Generated protocol buffer code."""
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from google.protobuf import reflection as _reflection
from google.protobuf import symbol_database as _symbol_database

# @@protoc_insertion_point(imports)

_sym_db = _symbol_database.Default()

DESCRIPTOR = _descriptor.FileDescriptor(
    name='neurotransmitter.proto',
    package='neuron.neurotransmitter',
    syntax='proto3',
    serialized_options=b'Z\016neuron/interop',
    create_key=_descriptor._internal_create_key,
    serialized_pb=b'\n\x16neurotransmitter.proto\x12\x17neuron.neurotransmitter\"\"\n\x0fSerializedStuff\x12\x0f\n\x07\x63ontent\x18\x01 \x01(\x0c\"\x87\x01\n\rAsymmetricKey\x12\x38\n\x06secret\x18\x01 \x01(\x0b\x32(.neuron.neurotransmitter.SerializedStuff\x12<\n\npublic_key\x18\x02 \x01(\x0b\x32(.neuron.neurotransmitter.SerializedStuffB\x10Z\x0eneuron/interopb\x06proto3'
)

_SERIALIZEDSTUFF = _descriptor.Descriptor(
    name='SerializedStuff',
    full_name='neuron.neurotransmitter.SerializedStuff',
    filename=None,
    file=DESCRIPTOR,
    containing_type=None,
    create_key=_descriptor._internal_create_key,
    fields=[
        _descriptor.FieldDescriptor(
            name='content', full_name='neuron.neurotransmitter.SerializedStuff.content', index=0,
            number=1, type=12, cpp_type=9, label=1,
            has_default_value=False, default_value=b"",
            message_type=None, enum_type=None, containing_type=None,
            is_extension=False, extension_scope=None,
            serialized_options=None, file=DESCRIPTOR, create_key=_descriptor._internal_create_key),
    ],
    extensions=[
    ],
    nested_types=[],
    enum_types=[
    ],
    serialized_options=None,
    is_extendable=False,
    syntax='proto3',
    extension_ranges=[],
    oneofs=[
    ],
    serialized_start=51,
    serialized_end=85,
)

_ASYMMETRICKEY = _descriptor.Descriptor(
    name='AsymmetricKey',
    full_name='neuron.neurotransmitter.AsymmetricKey',
    filename=None,
    file=DESCRIPTOR,
    containing_type=None,
    create_key=_descriptor._internal_create_key,
    fields=[
        _descriptor.FieldDescriptor(
            name='secret', full_name='neuron.neurotransmitter.AsymmetricKey.secret', index=0,
            number=1, type=11, cpp_type=10, label=1,
            has_default_value=False, default_value=None,
            message_type=None, enum_type=None, containing_type=None,
            is_extension=False, extension_scope=None,
            serialized_options=None, file=DESCRIPTOR, create_key=_descriptor._internal_create_key),
        _descriptor.FieldDescriptor(
            name='public_key', full_name='neuron.neurotransmitter.AsymmetricKey.public_key', index=1,
            number=2, type=11, cpp_type=10, label=1,
            has_default_value=False, default_value=None,
            message_type=None, enum_type=None, containing_type=None,
            is_extension=False, extension_scope=None,
            serialized_options=None, file=DESCRIPTOR, create_key=_descriptor._internal_create_key),
    ],
    extensions=[
    ],
    nested_types=[],
    enum_types=[
    ],
    serialized_options=None,
    is_extendable=False,
    syntax='proto3',
    extension_ranges=[],
    oneofs=[
    ],
    serialized_start=88,
    serialized_end=223,
)

_ASYMMETRICKEY.fields_by_name['secret'].message_type = _SERIALIZEDSTUFF
_ASYMMETRICKEY.fields_by_name['public_key'].message_type = _SERIALIZEDSTUFF
DESCRIPTOR.message_types_by_name['SerializedStuff'] = _SERIALIZEDSTUFF
DESCRIPTOR.message_types_by_name['AsymmetricKey'] = _ASYMMETRICKEY
_sym_db.RegisterFileDescriptor(DESCRIPTOR)

SerializedStuff = _reflection.GeneratedProtocolMessageType('SerializedStuff', (_message.Message,), {
    'DESCRIPTOR': _SERIALIZEDSTUFF,
    '__module__': 'neurotransmitter_pb2'
    # @@protoc_insertion_point(class_scope:neuron.neurotransmitter.SerializedStuff)
})
_sym_db.RegisterMessage(SerializedStuff)

AsymmetricKey = _reflection.GeneratedProtocolMessageType('AsymmetricKey', (_message.Message,), {
    'DESCRIPTOR': _ASYMMETRICKEY,
    '__module__': 'neurotransmitter_pb2'
    # @@protoc_insertion_point(class_scope:neuron.neurotransmitter.AsymmetricKey)
})
_sym_db.RegisterMessage(AsymmetricKey)

DESCRIPTOR._options = None
# @@protoc_insertion_point(module_scope)
