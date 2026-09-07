# Tech Challenge — Fase 3 · Alfabetização por aluno

**André Mohallem Ferraz · Trabalho individual · Entrega: 15/09/2026**

Estado em 06/09/2026: **Gold individual construída, EDA de 2023 e primeiro baseline executados**.
Os classificadores com atributos, a seleção de hiperparâmetros, a avaliação final e o vídeo
serão desenvolvidos nas próximas etapas. Esta versão ainda não é a entrega final.

Leitura dos resultados: [EDA e quatro figuras](reports/eda_development.md),
[baseline](reports/baseline_development.md), [auditoria da Gold](reports/gold_build.json)
e [verificação de reprodução](reports/reproducibility.json).

## 1. Contexto do problema

A Fase 2 entregou a engenharia de dados de alfabetização e indicadores municipais.
A Fase 3 amplia a Gold para uma linha por aluno e ano, com classificação supervisionada
e futura leitura dos riscos por território. A implementação reaproveita os dados locais
e as dimensões da Fase 2, preservando aquela entrega.

Os experimentos municipais da Fase 2 tinham outro alvo e outros protocolos.
Suas AUCs de 0,666 e 0,713 não são resultados deste classificador por aluno.

## 2. Objetivo analítico

Estimar a probabilidade de alfabetização de um aluno avaliado do 2º ano da rede Estadual
ou Municipal, usando rede de ensino e contexto territorial/econômico. O alvo é
`alfabetizado`, com 1 = alfabetizado e 0 = não alfabetizado. Para avaliação de risco,
`p_nao_alfabetizado = 1 - p_alfabetizado`; a classe de interesse é não alfabetizado.

O resultado terá uma linha por aluno, mas os atributos iniciais são contextuais.
Alunos com a mesma rede e o mesmo contexto recebem a mesma probabilidade.

## 3. Descrição da base de dados

| População auditada | Desenvolvimento: 2023 | Teste reservado: 2024 |
| --- | ---: | ---: |
| Silver, incluindo simulação | 1.748.957 | 2.122.042 |
| Eventos sintéticos excluídos | 1.518 | 1.482 |
| Avaliações reais elegíveis na Gold | 1.502.809 | 1.851.828 |
| Municípios elegíveis | 4.871 | 5.517 |

Total: **3.354.637 avaliações reais elegíveis**. A Gold mantém `(ano, id_aluno)` como
chave; igualdade de código entre anos não comprova identidade da criança. Excluem-se
simulação, redes fora do escopo, ausentes e avaliações sem proficiência/rótulo válidos.
Todos os dez campos de origem auditados da Silver batch foram comparados exatamente
com os registros originais, além da conferência de chaves e contagens.

O contexto usa edições publicadas até 31/12/2022, iguais nos dois ciclos. Cobertura:
100% dos municípios elegíveis, com os seis atributos completos.

| Preditor | Significado |
| --- | --- |
| `rede_nome` | Rede Estadual ou Municipal |
| `sigla_uf` | UF do município |
| `populacao_2021` | Habitantes, edição original DOU de 2021 |
| `pib_per_capita_2020` | Produção municipal por habitante em R$ de 2020 |
| `participacao_agropecuaria_2020` | Agropecuária / VAB total, em % |
| `participacao_servicos_publicos_2020` | Serviços públicos / VAB total, em % |

As participações usam **valor adicionado bruto (VAB)** como denominador. PIB per capita
não equivale a renda familiar; participação de serviços públicos não é gasto em educação.
Proficiência determina o rótulo pelo corte de 743 pontos e é removida da Gold final.
IDs, rótulo, peso e resultados contemporâneos ficam fora dos preditores.

Fontes e rastreabilidade: [manifesto IBGE](config/fontes-externas.json),
[snapshot e hashes](config/snapshot.json), [contrato](config/contrato-ml-aluno.json)
e [dicionário](config/dicionario-variaveis.csv). O contrato é a cópia congelada da definição
anterior; seu campo de estado descreve aquela etapa. O estado de execução vigente está
em `reports/gold_build.json` e nos relatórios desta versão.

## 4. Etapas de modelagem

Implementado: importação com SHA-256; reconstrução das fontes históricas; seleção dos
registros reais; junções muitos-para-um verificadas; Gold por ano; EDA; validação do
baseline em três folds por município. Um município pertence a apenas um fold.
O [mapa congelado](config/folds-municipios-2023.csv) foi balanceado por volume de alunos,
com semente 42 para desempate, sem usar rótulos.

| Fold | Municípios | Avaliações |
| --- | ---: | ---: |
| 0 | 1.622 | 500.934 |
| 1 | 1.625 | 500.942 |
| 2 | 1.624 | 500.933 |

Pendente: integrar imputação, encoding e transformações ao estimador; comparar atributos;
ajustar poucos hiperparâmetros; escolher e congelar modelo/limiar; avaliar 2024 uma vez.
Para o modelo linear, estão previstos `log1p` para população/PIB e padronização.
Todas as transformações serão ajustadas exclusivamente nos folds de treino.

## 5. Escolha do algoritmo

O primeiro modelo é `DummyClassifier(strategy="prior")`: aprende a proporção das classes
nos dois folds de treino e a usa no terceiro. Ele estabelece a referência sem poder de
discriminação contextual. Não utiliza pesos no ajuste.

Próximos candidatos definidos no protocolo: Regressão Logística e
`HistGradientBoostingClassifier`. Comparar a versão rede/UF com a versão de seis
atributos permitirá medir a contribuição do enriquecimento. Ainda não há modelo final.

## 6. Métricas de avaliação

Resultados do baseline em **2023**, média simples das métricas dos três folds:

| Métrica da classe não alfabetizado | Resultado |
| --- | ---: |
| ROC-AUC | 0,5000 |
| Average precision (critério principal) | 0,4161 |
| Brier score | 0,2431 |
| Acurácia no limiar 0,5 | 58,39% |
| Recall no limiar 0,5 | 0,00% |
| Balanced accuracy | 0,5000 |

O [JSON de avaliação](reports/baseline_development.json) registra cada fold, desvios
entre folds, matrizes de confusão e métricas ponderadas por `peso_aluno` como visão
suplementar. Os pesos não são preditores nem pesos de balanceamento de classe.
Não calcular uma ROC-AUC única juntando probabilidades constantes diferentes dos folds:
essa medida pode refletir o efeito da partição. A comparação usa métricas por fold.

**2024 não foi avaliado por modelo.** Sua Gold foi construída e auditada apenas quanto
à integridade. Nenhum limiar foi otimizado; 0,5 é somente a referência inicial.

## 7. Interpretação dos resultados

ROC-AUC de 0,50 significa que este baseline não ordena os casos por risco. A average
precision acompanha a prevalência da classe de interesse. No limiar 0,5, o baseline
classifica todos como alfabetizados: a acurácia de 58,39% vem da classe majoritária,
com recall zero dos não alfabetizados. Essa é a referência que os próximos modelos
precisam superar sob o mesmo protocolo.

## 8. Insights obtidos

Em 2023, 625.382 avaliações elegíveis (41,61%) têm resultado não alfabetizado. Entre
os recortes regionais disponíveis, essa proporção vai de 32,27% no Sul a 48,89% no Norte.
Essas são taxas descritivas sem ponderação, e não indicadores oficiais nacionais.

Há **5.881 perfis distintos dos seis atributos** entre 1.502.809 avaliações. Os gráficos
de contexto usam uma observação por município para não repetir o mesmo valor milhares
de vezes. População e PIB apresentam assimetria, representada em escala logarítmica na
EDA. Essas observações sustentam a avaliação territorial e as transformações previstas;
não demonstram causalidade nem ganho preditivo do enriquecimento.

## 9. Limitações

- Informação essencialmente contextual, sem histórico pedagógico ou características
  familiares individuais. Milhões de linhas não equivalem a milhões de contextos independentes.
- Contexto fixo de 2020/2021, incluindo a economia de um ano de pandemia.
- Ausentes não têm resultado observado e estão fora do universo modelado.
- Rede e município são tratados como cadastros disponíveis na matrícula; o snapshot
  não comprova uma fotografia cadastral individual anterior à prova.
- Não há chave escolar externa validada nem identidade longitudinal de aluno comprovada.
- Cobertura muda entre anos. A existência de pesos não demonstra representatividade
  nacional; a documentação da fonte precisa orientar sua interpretação.
- Até aqui há somente um baseline constante: não há evidência de capacidade de antecipar
  risco individual, evolução de crianças ou efeito de políticas públicas.

## 10. Aplicação em políticas públicas

A aplicação proposta é apoiar uma futura leitura territorial de risco, com volume,
cobertura e incerteza explícitos. Ainda dependem dos próximos experimentos: fatores
associados, municípios com maior risco, perfis regionais semelhantes, leitura de metas
futuras e importância de variáveis. Não produzir ranking preditivo com o baseline constante.

Uma futura média ponderada das probabilidades de alfabetização poderá estimar uma taxa
municipal no recorte avaliado. Ela não será a probabilidade de descumprir uma meta.
Qualquer cenário futuro exigirá população/atributos do ciclo correspondente e metas
com disponibilidade histórica verificada.

## 11. Evoluções futuras

1. Regressão Logística: rede/UF e seis atributos, mesmos folds de 2023.
2. Gradient Boosting e busca limitada de parâmetros, usando somente desenvolvimento.
3. Seleção, calibração/limiar, interpretação e avaliação temporal congelada.
4. Análises estratégicas, relatório técnico, apresentação e vídeo de até cinco minutos.
5. Publicação do repositório, PRs reais e revisão individual documentada.

O repositório Git desta etapa é local: `main` contém o scaffold, e
`feature/gold-eda-baseline` contém a implementação. Ainda não há repositório remoto
ou pull request da Fase 3 publicado.

## Como reproduzir

Ambiente usado: Python 3.12.13, dependências fixadas em `pyproject.toml`, transitivas
congeladas em `uv.lock`. A execução inicial foi realizada em Linux/WSL; Windows nativo
ainda não foi validado. Com `uv` instalado, executar na raiz do projeto:

```bash
uv sync --frozen
uv run pytest -q
uv run python -m src.pipeline run-all
```

A cópia privada entregue no Drive inclui `data/input` e permite executar `run-all`
diretamente. Em um clone apenas de código, preparar primeiro o snapshot conforme
[instruções e mapeamento dos arquivos](data/README.md):

```bash
uv run python -m src.pipeline prepare --source "/caminho/para/apoio"
uv run python -m src.pipeline run-all
```

No ambiente local de trabalho, `--source` é
`/home/sortiesimi/entregas/fiap-fase3/apoio`. O comando copia somente os sete arquivos
explicitamente listados no manifesto e recusa SHA-256 diferente do esperado.

Para executar etapas separadas:

```bash
uv run python -m src.pipeline gold
uv run python -m src.pipeline eda
uv run python -m src.pipeline baseline
uv run ruff check .
uv run ruff format --check .
```

`gold` reconstrói as duas partições; `eda` e `baseline` leem exclusivamente o caminho
de 2023. A CLI permite `--root /outro/diretorio` antes do subcomando; nesse caso, copiar
primeiro a pasta `config/` para essa raiz e executar `prepare`.

Alternativa sem `uv`, com Python 3.12: criar um ambiente virtual e instalar
`python -m pip install --require-hashes -r requirements.txt`, depois usar
`python -m src.pipeline ...`. Esse arquivo contém apenas dependências de execução;
a instalação por `uv` inclui as ferramentas de desenvolvimento/teste.

### Estrutura e saídas

```text
config/                 Contrato, dicionário, fontes, hashes e folds
data/input/             Sete arquivos de entrada verificados (fora do Git)
data/gold/              Contexto e Gold individual por ano (fora do Git)
notebooks/              Orientação; nesta etapa a EDA usa scripts
src/domain/             Contrato do experimento
src/infrastructure/     Leitura, escrita e verificação de arquivos
src/preprocessing/      Contexto, população elegível, junções e Gold
src/modeling/           Baseline
src/evaluation/         Métricas e resumos de desenvolvimento
src/visualization/      Figuras em PNG e SVG
src/usecase/            Orquestração das etapas
src/pipeline.py         CLI
reports/                Métricas, auditorias e análise em Markdown/CSV/JSON
images/                 Quatro figuras, cada uma em PNG e SVG
artifacts/              Probabilidades fora de fold de 2023 (fora do Git)
tests/                  Testes de integridade, vazamento e orientação do alvo
```

Verificações: 30 testes aprovados, lint/formatação aprovados e reprodução em diretório
de saídas vazio. Nesse ensaio, o arquivo Gold de 2024 ficou indisponível durante EDA e
baseline; ambos concluíram. Hashes, ambiente e tempos estão no relatório de reprodução.
Dados individuais, ambientes virtuais, credenciais e artefatos por aluno não vão ao Git.

### Referências técnicas

- [IBGE: arquivo histórico do PIB dos Municípios, edição 2020](https://ftp.ibge.gov.br/Pib_Municipios/2020/base/base_de_dados_2010_2020_txt.zip).
- [IBGE: estimativas originais DOU de 2021](https://ftp.ibge.gov.br/Estimativas_de_Populacao/Estimativas_2021/estimativa_dou_2021.ods).
- [Scikit-learn: DummyClassifier](https://scikit-learn.org/stable/modules/generated/sklearn.dummy.DummyClassifier.html).
- [Scikit-learn: average precision](https://scikit-learn.org/stable/modules/generated/sklearn.metrics.average_precision_score.html).
- [Scikit-learn: prevenção de vazamento](https://scikit-learn.org/stable/common_pitfalls.html).

Documentos de referência: enunciado `[IAST] - Tech Challenge - Fase 3.pdf`, entrega
da Fase 2 e documentos 01–03 em `FIAP/Fase3/Planejamento`. Relatório consolidado desta
etapa: `04-Primeira-Execucao-Fase3-v0.1`, na mesma pasta. Vídeo final: pendente.
