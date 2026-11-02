from importlib.util import find_spec


def test_pacote_src_importavel() -> None:
    spec = find_spec("src")

    assert spec is not None
    assert spec.origin is not None
