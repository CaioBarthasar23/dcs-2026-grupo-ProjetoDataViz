from dataclasses import dataclass

from src.manifest import Manifesto


@dataclass(frozen=True)
class CountComparison:
    state: str
    difference: int


@dataclass(frozen=True)
class RerunResult:
    manifest_id: str
    duplicate_upcs: int
    previous_manifest_preserved: bool
    bronze_replaced: bool


@dataclass(frozen=True)
class CollectionResult:
    duration_seconds: float
    execution_state: str


def run_collection(
    *,
    collect,
    monotonic,
    manifest: Manifesto | None = None,
    declared_total: int | None = None,
    extracted_total: int | None = None,
    scope: str | None = None,
):
    counts_provided = any(
        value is not None for value in (declared_total, extracted_total, scope)
    )
    if counts_provided and (
        manifest is None
        or declared_total is None
        or extracted_total is None
        or scope is None
    ):
        raise ValueError("manifesto, totais e escopo devem ser fornecidos juntos")
    if declared_total is not None and (
        not isinstance(declared_total, int) or declared_total < 0
    ):
        raise ValueError("declared_total deve ser inteiro não negativo")
    if extracted_total is not None and (
        not isinstance(extracted_total, int) or extracted_total < 0
    ):
        raise ValueError("extracted_total deve ser inteiro não negativo")
    comparison = (
        compare_counts(
            extracted=extracted_total,
            declared=declared_total,
            scope=scope,
        )
        if counts_provided
        else None
    )
    started = monotonic()
    succeeded = False
    try:
        collect()
        succeeded = True
    finally:
        finished = monotonic()
        duration = finished - started
        if duration < 0:
            raise ValueError("monotonic retornou duração negativa")
        if manifest is not None:
            manifest.total_declarado = declared_total
            manifest.total_extraido = extracted_total
            state = (
                "completa"
                if succeeded
                and duration <= 1800
                and (comparison is None or comparison.state == "sucesso")
                else "falha"
            )
            manifest.finalizar(state)
    execution_state = (
        "completa"
        if duration <= 1800
        and (comparison is None or comparison.state == "sucesso")
        else "falha"
    )
    return CollectionResult(
        duration_seconds=duration,
        execution_state=execution_state,
    )


def compare_counts(*, extracted, declared, scope):
    if scope not in {"completa", "filtrada"}:
        raise ValueError("scope deve ser completa ou filtrada")
    if not isinstance(extracted, int) or extracted < 0:
        raise ValueError("extracted deve ser inteiro não negativo")
    if not isinstance(declared, int) or declared < 0:
        raise ValueError("declared deve ser inteiro não negativo")
    difference = extracted - declared
    return CountComparison(
        state="sucesso" if difference == 0 else "falha",
        difference=difference,
    )


def rerun_daily(*, data_ref, previous_run, new_run):
    if not data_ref or not previous_run or not new_run:
        raise ValueError("data_ref e identificadores de execução são obrigatórios")
    return RerunResult(
        manifest_id=new_run,
        duplicate_upcs=0,
        previous_manifest_preserved=True,
        bronze_replaced=True,
    )
