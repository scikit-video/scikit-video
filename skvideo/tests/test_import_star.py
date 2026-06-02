"""Guard against a malformed top-level ``__all__``.

``skvideo.__all__`` previously listed the function *objects* rather than
their names, so ``from skvideo import *`` raised
``TypeError: Item in skvideo.__all__ must be str, not function``.
"""
import skvideo


def test_all_entries_are_strings():
    assert all(isinstance(name, str) for name in skvideo.__all__)


def test_import_star_does_not_raise():
    namespace = {}
    exec("from skvideo import *", namespace)
    # Every advertised name should resolve to a real attribute.
    for name in skvideo.__all__:
        assert name in namespace, "%s not exported by import *" % name
