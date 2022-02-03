import synapsis

from proto.neurotransmitter_pb2 import AsymmetricKey, SerializedStuff


def main():
    key1 = synapsis.generate_key()
    key2 = synapsis.generate_key()
    print(f'{key1=}\n{key2=}')

    parsed_key1 = AsymmetricKey()
    parsed_key1.ParseFromString(key1)
    parsed_key2 = AsymmetricKey()
    parsed_key2.ParseFromString(key2)

    print(f'{parsed_key1=}\n{parsed_key2=}')

    shared1 = synapsis.generate_shared(key1, parsed_key2.public_key.SerializeToString())
    shared2 = synapsis.generate_shared(key2, parsed_key1.public_key.SerializeToString())
    print(f'{shared1=}\n{shared2=}')
    assert shared1 == shared2

    message = b'kekekekekkekekekekek'
    message_dump = SerializedStuff(content=message).SerializeToString()
    enc = synapsis.encrypt(shared1, message_dump)
    dec = synapsis.decrypt(shared2, enc)
    print(f'{enc=}\n{dec=}')

    final = SerializedStuff()
    final.ParseFromString(dec)
    assert final.content == message


if __name__ == '__main__':
    main()
