"""Demonstra inferência contextual com o modelo 1.0, sem treinamento ou avaliação nova."""

import argparse
import json
from pathlib import Path
from typing import Protocol

import numpy as np
import pandas as pd
from sklearn.pipeline import Pipeline

from src.domain.contract import ContractError, ExperimentContract, JsonObject
from src.domain.prediction_demo import ProfileRequest, probability_decision
from src.infrastructure.profile_store import (
    CONTEXT_COLUMNS,
    DEMO_MODEL,
    FROZEN_DIGESTS,
    FrozenProfileStore,
)
from src.modeling.prediction import pipeline_risk


class ProfileStore(Protocol):
    """Interface injetável para executar e testar a inferência sem fontes externas."""

    def load_decision(self) -> JsonObject: ...

    def load_pipeline(self) -> Pipeline: ...

    def load_contexts(self, requests: list[ProfileRequest]) -> pd.DataFrame: ...


def _select_contexts(contexts: pd.DataFrame, requests: list[ProfileRequest]) -> pd.DataFrame:
    if set(contexts.columns) != set(CONTEXT_COLUMNS):
        raise ContractError(
            "Colunas de contexto incompatíveis; esperado somente atributos públicos"
        )
    selected: list[pd.DataFrame] = []
    for request in requests:
        profile = contexts.loc[
            contexts["id_municipio"].eq(request.municipality)
            & contexts["rede_nome"].eq(request.network)
        ].drop_duplicates()
        if len(profile) == 0:
            raise ContractError(
                f"Perfil {request.municipality}/{request.network} ausente da Gold 2023; "
                "a demonstração aceita somente contextos conhecidos"
            )
        if len(profile) != 1:
            raise ContractError(
                f"Contexto ambíguo em {request.municipality}/{request.network}; esperado perfil único"
            )
        selected.append(profile)
    result = pd.concat(selected, ignore_index=True)
    contract = ExperimentContract()
    if (
        result.isna().any().any()
        or not np.isfinite(result[list(contract.numeric)].to_numpy(dtype=float)).all()
    ):
        raise ContractError("Contexto incompleto; esperado perfil histórico sem nulos ou infinitos")
    return result


def predict_profiles(store: ProfileStore, requests: list[ProfileRequest]) -> JsonObject:
    """Recebe município/rede, seleciona seis preditores e retorna probabilidades e decisões."""
    if not requests or len(set(requests)) != len(requests):
        raise ContractError("Perfis inválidos; esperado ao menos um perfil e nenhum repetido")
    decision = store.load_decision()
    if decision["features"] != list(ExperimentContract().features):
        raise ContractError("Decisão incompatível; esperado contrato original com seis preditores")
    profiles = _select_contexts(store.load_contexts(requests), requests)
    pipeline = store.load_pipeline()
    risk = pipeline_risk(pipeline, profiles)
    if risk.shape != (len(profiles),):
        raise ContractError("Saída incompatível; esperado uma probabilidade por perfil")
    threshold = float(decision["risk_threshold"])
    predictions = []
    for index, row in profiles.iterrows():
        values: JsonObject = {
            name: str(row[name]) if name in ExperimentContract().categorical else float(row[name])
            for name in ExperimentContract().features
        }
        prediction: JsonObject = {
            "id_municipio": str(row["id_municipio"]),
            "nome_municipio": str(row["nome_municipio"]),
            "contexto_utilizado": values,
            **probability_decision(float(risk[index]), threshold),
        }
        predictions.append(prediction)
    return {
        "autor": "André Mohallem Ferraz",
        "modelo_versao": "1.0",
        "modelo_sha256": FROZEN_DIGESTS[DEMO_MODEL],
        "pergunta": (
            "Qual é a probabilidade estimada de alfabetização de um aluno do 2º ano, "
            "considerando a rede de ensino e o contexto territorial e socioeconômico?"
        ),
        "criterio_do_alvo_observado": "alfabetizado = 1 quando proficiência >= 743; caso contrário, 0",
        "limiar_operacional": "F2 definido exclusivamente nas previsões fora da amostra de 2023",
        "ano_do_perfil": 2023,
        "referencias_do_contexto": {"populacao": 2021, "pib_e_composicao_economica": 2020},
        "finalidade": "demonstração de inferência; não constitui nova avaliação de desempenho",
        "limitacoes": [
            "Alunos com os mesmos seis atributos recebem a mesma probabilidade contextual.",
            "A probabilidade é uma estimativa do modelo, sem calibração adicional ou garantia individual.",
            "O limiar F2 prioriza sensibilidade e sinalizou 96,84% dos alunos no teste de 2024.",
            "Os perfis demonstrados estavam no desenvolvimento de 2023; não representam teste independente.",
            "A estimativa usa o contexto histórico; não é uma previsão para 2026 ou anos futuros.",
            "Indicadores educacionais do estudo complementar não alimentam o modelo 1.0 desta demonstração.",
        ],
        "previsoes": predictions,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--root", type=Path, default=Path("."), help="Raiz do projeto e artefatos privados"
    )
    choice = parser.add_mutually_exclusive_group(required=True)
    choice.add_argument("--municipio", help="Código IBGE municipal de sete dígitos")
    choice.add_argument("--input", type=Path, help="CSV público com id_municipio,rede_nome")
    parser.add_argument("--rede", choices=["Municipal", "Estadual"], help="Rede do perfil único")
    parser.add_argument("--output", type=Path, help="JSON de saída; recusa sobrescrever arquivos")
    args = parser.parse_args()
    if bool(args.municipio) != bool(args.rede):
        parser.error("--municipio e --rede devem ser informados juntos; --input não aceita --rede")
    store = FrozenProfileStore(args.root)
    try:
        if args.output is not None and args.output.exists():
            raise FileExistsError(f"Saída já existe: {args.output}; escolha outro caminho")
        requests = (
            store.read_requests(args.input)
            if args.input
            else [ProfileRequest(args.municipio, args.rede)]
        )
        result = predict_profiles(store, requests)
        if args.output:
            store.write_result(args.output, result)
        else:
            print(json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False))
    except (ContractError, OSError, pd.errors.ParserError) as exc:
        parser.exit(2, f"Erro: {exc}\n")


if __name__ == "__main__":
    main()
