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

## Estado após Gradient Boosting e busca limitada

- `logistic` e `boosting` comparam rede/UF e seis atributos; `run-all` inclui ambos.
- Configuração e hashes em `config/experimento-logistica.json`. Parâmetros fixos nesta rodada.
- AP: baseline 0,4161; rede/UF 0,5333; completa 0,5381. Não escolher modelo final ainda.
- Pipelines em `artifacts/logistica/` são de validação, uma por variante/fold; não há ajuste final.
- Busca boosting v0.1: 150 mil alunos por hash (50 mil/fold), seis candidatos/variante.
  Vencedores: rede/UF 31 folhas/100 iterações; completa 7/100. AP na base completa:
  0,533581 e 0,543776. CV não aninhada: resultados sujeitos a viés de seleção.
  `reports/boosting_protocolo.md` registra a decisão anterior à execução.
- `uv run python -m src.usecase.reproduce_boosting` repete busca e confirmação sem Gold 2024.
- Próxima etapa: consolidar escolha com 2023, interpretar e congelar limiar antes de
  ajustar todo 2023 e avaliar 2024 uma única vez. Ainda não há modelo final ou limiar escolhido.
- Há cópia privada em `G:\Meu Drive\FIAP\Fase3\tech-challenge-fase3`; verificar alterações
  nessa cópia antes de sobrescrever arquivos. A pasta no WSL é a raiz de trabalho.
- GitHub público: `andreferraz-fiap-fase2/tech-challenge-fase3`. A conta correspondente
  está autenticada no GitHub CLI do Windows. O WSL usa outra conta; não trocar o destino.
  Ao usar a conta da Fase 2 no Windows, restaurar a conta ativa anterior ao concluir.
