# Obtenção do snapshot

Os dados individuais ficam fora do Git. A cópia privada desta etapa no Drive contém
`data/input/`; nela, executar `uv run python -m src.usecase.reproduce_all` sem uma nova importação.

Para preparar um clone de código, montar uma pasta `apoio` com `fontes-fase2/` e
`fontes-externas/`. A origem da primeira é
`G:\Meu Drive\FIAP\Fase2\TechChallange - Fase2`:

| Destino dentro de apoio | Arquivo na Fase 2 |
| --- | --- |
| `fontes-fase2/alunos-original.parquet` | `data/real/alunos.parquet` |
| `fontes-fase2/alunos-silver-2023.parquet` | `data/silver/fato_aluno/ano=2023/00000000.parquet` |
| `fontes-fase2/alunos-silver-2024.parquet` | `data/silver/fato_aluno/ano=2024/00000000.parquet` |
| `fontes-fase2/diretorio_municipio.parquet` | `data/real/diretorio_municipio.parquet` |
| `fontes-fase2/diretorio_uf.parquet` | `data/real/diretorio_uf.parquet` |
| `fontes-fase2/ml_features.parquet` | `data/gold/ml_features.parquet` |

Copiar os dois arquivos de `G:\Meu Drive\FIAP\Fase3\Preparacao\fontes-externas`
para `apoio/fontes-externas/`: `pib-municipios-2010-2020.zip` e
`populacao-dou-2021.ods`. URLs e hashes estão em `config/`.

Na raiz do projeto:

```bash
uv run python -m src.pipeline prepare --source "/caminho/para/apoio"
uv run python -m src.usecase.reproduce_all
```

O importador confere os oito hashes antes de usar cada arquivo. A construção da Gold
confere novamente as entradas e bloqueia divergências. Não copiar a pasta inteira de
dados da Fase 2: ela contém arquivos alheios a este experimento. Preservar os originais.

Saídas principais: `gold/contexto_municipal.parquet`,
`gold/ml_aluno/ano=2023/alunos.parquet` e `gold/ml_aluno/ano=2024/alunos.parquet`.
O desenvolvimento utiliza somente 2023; o modelo congelado é avaliado em 2024.
A reprodução usa pastas temporárias para preservar os resultados publicados.
A Gold municipal `ml_features.parquet` é utilizada apenas na análise posterior das metas,
executada por `uv run python -m src.pipeline strategy` na cópia que contém as previsões finais.
