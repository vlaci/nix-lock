import tomlkit

from nix_lock.schema import DerivationsSchema


def loads(content):
    dct = tomlkit.parse(content)
    return DerivationsSchema().load(dct)


def dumps(data):
    return tomlkit.dumps(data)
