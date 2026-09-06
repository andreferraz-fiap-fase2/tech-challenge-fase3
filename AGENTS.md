# Fase 3 — alfabetização por aluno

Projeto individual de André Mohallem Ferraz, entrega em 15/09/2026. Python 3.12,
Pandas/PyArrow, Scikit-learn e Matplotlib. Repositório independente da Fase 2.

## Comandos

- Ambiente: `uv sync --frozen`
- Testes: `uv run pytest -q`
- Formatação/lint: `uv run ruff format .` e `uv run ruff check .`
- Execução: `uv run python -m src.pipeline --help`

## Estrutura

`src/domain` guarda o contrato sem bibliotecas externas; `infrastructure` concentra
I/O; `preprocessing`, `modeling`, `evaluation`, `visualization` correspondem ao
enunciado; `usecase` orquestra e `pipeline.py` expõe a CLI.

## Regras do experimento

- Alvo: alfabetizado; risco = 1 - P(alfabetizado). Uma linha por `(ano, id_aluno)`.
- Somente registros batch reais, redes Estadual/Municipal, 2º ano e avaliação válida.
- Desenvolvimento/CV exclusivamente 2023; 2024 reservado para o teste final.
- Manter os três folds por município definidos em `config/folds-municipios-2023.csv`.
- Somente os seis preditores do contrato. Proficiência, peso, IDs e resultado municipal
  contemporâneo ficam fora de X. Não ligar alunos entre anos por código.
- Preservar as fontes da Fase 2. Dados individuais, modelos e credenciais não vão ao Git.
- Alterações no contrato/protocolo precisam de decisão documentada e nova versão.
- Documentação e arquivos de entrega em português; manter resultados de desenvolvimento
  explicitamente separados de avaliação temporal final, ainda não realizada.
