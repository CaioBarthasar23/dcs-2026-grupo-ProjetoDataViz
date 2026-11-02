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
        self.chamadas: list[str] = []
        self.respostas_head: list[dict[str, object] | Exception] = []
        self.resultados_put: list[Exception | None] = []

    def head_object(self, *, Bucket: str, Key: str) -> dict[str, object]:
        self.chamadas.append("head")
        if self.respostas_head:
            resposta = self.respostas_head.pop(0)
            if isinstance(resposta, Exception):
                raise resposta
            return resposta
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
        self.chamadas.append("put")
        if self.resultados_put:
            resultado = self.resultados_put.pop(0)
            if resultado is not None:
                raise resultado
        objeto = Put(Bucket, Key, Body, Metadata)
        self.puts.append(objeto)
        self.objetos[(Bucket, Key)] = objeto
