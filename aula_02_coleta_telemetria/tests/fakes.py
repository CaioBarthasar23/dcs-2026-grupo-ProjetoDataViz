from dataclasses import dataclass

from botocore.exceptions import ClientError


@dataclass(frozen=True)
class Put:
    bucket: str
    chave: str
    body: bytes
    metadata: dict[str, str]


class ArmazenamentoFalso:
    def __init__(self) -> None:
        self.puts: list[Put] = []
        self.objetos: dict[tuple[str, str], Put] = {}

    def head_object(self, *, Bucket: str, Key: str) -> dict[str, object]:
        objeto = self.objetos.get((Bucket, Key))
        if objeto is None:
            raise ClientError(
                {"Error": {"Code": 404, "Message": "teste: inexistente"}},
                "HeadObject",
            )
        return {"Metadata": objeto.metadata}

    def put_object(
        self,
        *,
        Bucket: str,
        Key: str,
        Body: bytes,
        Metadata: dict[str, str],
    ) -> None:
        objeto = Put(Bucket, Key, Body, Metadata)
        self.puts.append(objeto)
        self.objetos[(Bucket, Key)] = objeto
