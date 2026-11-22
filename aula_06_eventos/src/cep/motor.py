from __future__ import annotations

from datetime import datetime, timedelta
from typing import Iterable

from .academia_silenciosa import avaliar as avaliar_silencio
from .academia_silenciosa import vencidos as vencidos_silencio
from .cobranca_reincidente import avaliar as avaliar_cobranca
from .experimental_sem_matricula import avaliar as avaliar_experimental
from .experimental_sem_matricula import vencidos as vencidos_experimental
from .pico_cancelamentos import avaliar as avaliar_cancelamento
from .regras import parse_utc


class MotorCEP:
    def __init__(self, estado, config, regras=None) -> None:
        self.estado = estado
        self.config = config
        self.maximo_visto = None
        self.regras = regras or (
            "cobranca_reincidente",
            "academia_silenciosa",
            "pico_de_cancelamentos",
            "experimental_sem_matricula",
        )

    @property
    def watermark(self) -> datetime | None:
        if self.maximo_visto is None:
            return None
        return self.maximo_visto - self.config.watermark_folga

    def processar(self, evento: dict) -> list[dict]:
        if not evento.get("ocorrido_em"):
            return []
        instante = parse_utc(evento["ocorrido_em"])
        atraso_antes = self.watermark
        atrasado = atraso_antes is not None and instante < atraso_antes
        if self.maximo_visto is None or instante > self.maximo_visto:
            self.maximo_visto = instante

        complexos = []
        tipo = evento["tipo"]

        if tipo == "cobranca_falhou":
            chave = evento["aluno"]
            estado = self.estado.obter("cobranca_reincidente", chave)
            novo, detectados = avaliar_cobranca(
                estado,
                evento,
                self.watermark or instante,
                self.config.reincidencia_quantidade,
                self.config.reincidencia_janela,
            )
            for detectado in detectados:
                detectado["atrasado"] = atrasado
            complexos.extend(detectados)
            self.estado.salvar_chave("cobranca_reincidente", chave, novo)

        if tipo == "heartbeat":
            chave = evento["academia"]
            estado = self.estado.obter("academia_silenciosa", chave)
            novo, _ = avaliar_silencio(
                estado,
                evento,
                self.watermark or instante,
                self.config.silencio_academia,
            )
            self.estado.salvar_chave("academia_silenciosa", chave, novo)

        if tipo == "cancelamento":
            chave = evento["academia"]
            estado = self.estado.obter("pico_de_cancelamentos", chave)
            novo, detectados = avaliar_cancelamento(
                estado,
                evento,
                self.watermark or instante,
                self.config.cancelamentos_quantidade,
                self.config.cancelamentos_janela,
            )
            for detectado in detectados:
                detectado["atrasado"] = atrasado
            complexos.extend(detectados)
            self.estado.salvar_chave("pico_de_cancelamentos", chave, novo)

        if tipo in ("aula_experimental", "matricula"):
            chave = evento["aluno"]
            estado = self.estado.obter("experimental_sem_matricula", chave)
            novo, _ = avaliar_experimental(
                estado,
                evento,
                self.watermark or instante,
                self.config.matricula_janela,
            )
            self.estado.salvar_chave("experimental_sem_matricula", chave, novo)

        complexos.extend(self._processar_temporizadores())
        self.estado.persistir()
        return complexos

    def processar_temporizadores(self) -> list[dict]:
        complexos = self._processar_temporizadores()
        if complexos:
            self.estado.persistir()
        return complexos

    def _processar_temporizadores(self) -> list[dict]:
        if self.watermark is None:
            return []
        complexos = []

        for chave, estado in list(
            self.estado.regras.get("academia_silenciosa", {}).items()
        ):
            evento = {
                "ocorrido_em": self.utc(self.watermark),
                "academia": chave,
                "regiao": "",
            }
            detectados = vencidos_silencio(
                estado,
                chave,
                evento,
                self.watermark,
                self.config.silencio_academia,
            )
            complexos.extend(detectados)
            if detectados:
                self.estado.remover("academia_silenciosa", chave)

        for chave, estado in list(
            self.estado.regras.get("experimental_sem_matricula", {}).items()
        ):
            experimental = estado.get("experimental")
            if not experimental:
                continue
            evento = {
                "ocorrido_em": experimental,
                "academia": "",
                "regiao": "",
            }
            detectados = vencidos_experimental(
                estado,
                chave,
                evento,
                self.watermark,
                self.config.matricula_janela,
            )
            complexos.extend(detectados)
            if detectados:
                self.estado.remover("experimental_sem_matricula", chave)

        self._expirar_janelas()
        return complexos

    def _expirar_janelas(self) -> None:
        if self.watermark is None:
            return
        limite_cobranca = self.watermark - self.config.reincidencia_janela
        limite_cancelamento = self.watermark - self.config.cancelamentos_janela

        for regra, limite in (
            ("cobranca_reincidente", limite_cobranca),
            ("pico_de_cancelamentos", limite_cancelamento),
        ):
            for chave, estado in list(
                self.estado.regras.get(regra, {}).items()
            ):
                datas = estado.get("datas", {})
                ids = [
                    event_id
                    for event_id in estado.get("ids", [])
                    if datas.get(event_id)
                    and parse_utc(datas[event_id]) >= limite
                ]
                if ids:
                    estado["ids"] = ids
                    estado["datas"] = {
                        event_id: datas[event_id]
                        for event_id in ids
                    }
                else:
                    self.estado.remover(regra, chave)

    @staticmethod
    def utc(instante: datetime) -> str:
        from .regras import utc_iso
        return utc_iso(instante)
