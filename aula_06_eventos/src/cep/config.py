from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta
import os


@dataclass(frozen=True)
class ConfiguracaoCEP:
    """Valores de negocio. Os limites sao hipotese, validacao pendente."""

    reincidencia_quantidade: int = 2
    reincidencia_janela: timedelta = timedelta(days=7)
    silencio_academia: timedelta = timedelta(minutes=5)
    cancelamentos_quantidade: int = 3
    cancelamentos_janela: timedelta = timedelta(hours=24)
    matricula_janela: timedelta = timedelta(days=7)
    watermark_folga: timedelta = timedelta(minutes=2)

    @classmethod
    def ambiente(cls) -> "ConfiguracaoCEP":
        def minutos(nome: str, padrao: int) -> timedelta:
            return timedelta(minutes=int(os.environ.get(nome, str(padrao))))

        def dias(nome: str, padrao: int) -> timedelta:
            return timedelta(days=int(os.environ.get(nome, str(padrao))))

        return cls(
            reincidencia_quantidade=int(
                os.environ.get("CEP_REINCIDENCIA_QUANTIDADE", "2")
            ),
            reincidencia_janela=dias("CEP_REINCIDENCIA_DIAS", 7),
            silencio_academia=minutos("CEP_SILENCIO_ACADEMIA_MINUTOS", 5),
            cancelamentos_quantidade=int(
                os.environ.get("CEP_CANCELAMENTOS_QUANTIDADE", "3")
            ),
            cancelamentos_janela=minutos(
                "CEP_CANCELAMENTOS_HORAS",
                24 * 60,
            ),
            matricula_janela=dias("CEP_MATRICULA_DIAS", 7),
            watermark_folga=minutos("CEP_WATERMARK_FOLGA_MINUTOS", 2),
        )
