from dataclasses import dataclass


@dataclass(frozen=True)
class Put:
    bucket: str
    chave: str
    body: bytes
    metadata: dict[str, str]


class ArmazenamentoFalso:
    def __init__(self) -> None:
        self.puts: list[Put] = []

    def put_object(
        self,
        *,
        Bucket: str,
        Key: str,
        Body: bytes,
        Metadata: dict[str, str],
    ) -> None:
        self.puts.append(Put(Bucket, Key, Body, Metadata))
