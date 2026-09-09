# Tech Challenge — Fase 3 · Alfabetização por aluno

**André Mohallem Ferraz · Trabalho individual · Entrega: 15/09/2026**

Estado em 09/09/2026: **Gold, EDA, baseline, Regressão Logística e Gradient Boosting executados**.
A busca limitada avaliou seis configurações por variante em uma amostra de 2023;
os vencedores foram confirmados nos mesmos folds municipais, com a base completa.
Seleção final, limiar, avaliação temporal, relatório consolidado e vídeo permanecem pendentes.

Leitura dos resultados: [EDA e quatro figuras](reports/eda_development.md),
[baseline](reports/baseline_development.md), [auditoria da Gold](reports/gold_build.json)
e [verificação da primeira reprodução](reports/reproducibility.json).
Resultado atual: [Gradient Boosting e comparação dos cinco modelos](reports/boosting_development.md),
[protocolo da busca](reports/boosting_protocolo.md) e [reprodução](reports/boosting_reproducibility.json).
A [comparação logística e seus coeficientes](reports/logistica_development.md) foi preservada.

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

Implementado na logística: imputação categórica constante, one-hot com categoria inédita
ignorada, imputação numérica pela mediana, `log1p` para população/PIB e padronização das
numéricas. Cada fold ajusta sua própria pipeline exclusivamente nos municípios de treino.
A matriz real teve 25 atributos codificados na versão rede/UF e 29 na versão completa.

Implementado no boosting: categorias codificadas no treino e explicitamente marcadas
como nominais; inéditas viram NaN. Numéricos usam mediana do treino, sem log ou escala.
A parada automática está desativada para não criar uma divisão interna aleatória.

Pendente: escolha/congelamento de modelo e limiar, avaliação temporal e interpretação
final. O limiar desta rodada é a referência 0,5.

## 5. Escolha do algoritmo

O primeiro modelo é `DummyClassifier(strategy="prior")`: aprende a proporção das classes
nos dois folds de treino e a usa no terceiro. Ele estabelece a referência sem poder de
discriminação contextual. Não utiliza pesos no ajuste.

Foram executadas Regressões Logísticas com rede/UF e com seis atributos, usando L2,
C=1, solver `lbfgs`, tolerância 1e-6, máximo de 1.000 iterações e uma thread. Não houve
busca de parâmetros nem ponderação do ajuste. Todas as seis pipelines convergiram:
22–25 iterações para rede/UF e 59–68 para os seis atributos. Parâmetros e hashes estão
em [experimento-logistica.json](config/experimento-logistica.json).
O `HistGradientBoostingClassifier` passou por busca de 7/15/31 folhas máximas e
100/200 iterações, learning rate 0,05, mínimo de 100 alunos por folha e L2=1.
A amostra determinística contém 150.000 alunos de 4.810 municípios: 50.000 por fold,
selecionados por hash da chave, sem rótulos, mantendo o mapa municipal original.
Cada variante foi selecionada pela maior AP média na amostra e confirmada em toda
a Gold de 2023: rede/UF com 31 folhas e 100 iterações; completa com 7 folhas e 100
iterações. Foram 36 ajustes de busca e 6 de confirmação. Ainda não há modelo final.
Configuração: [experimento-boosting.json](config/experimento-boosting.json).

## 6. Métricas de avaliação

Resultados em **2023**, média simples das métricas dos três folds, para não alfabetizado:

| Modelo | Average precision | ROC-AUC | Brier ↓ | Recall a 0,5 | Precisão a 0,5 |
| --- | ---: | ---: | ---: | ---: | ---: |
| Baseline constante | 0,4161 | 0,5000 | 0,2431 | 0,00% | 0,00% |
| Logística: rede/UF | 0,5333 | 0,6361 | 0,2288 | 31,67% | 57,71% |
| Logística: seis atributos | 0,5381 | 0,6394 | 0,2284 | 36,75% | 56,14% |
| Boosting: rede/UF | 0,5336 | 0,6368 | 0,2287 | 33,69% | 57,23% |
| Boosting: seis atributos | 0,5438 | 0,6426 | 0,2275 | 34,71% | 57,80% |

Os JSONs do [baseline](reports/baseline_development.json), da
[logística](reports/logistica_development.json) e do [boosting](reports/boosting_development.json)
registram cada fold, desvios,
matrizes de confusão e métricas ponderadas por `peso_aluno` como visão suplementar.
Os pesos não são preditores nem pesos de balanceamento de classe.
Não calcular uma ROC-AUC única juntando probabilidades constantes diferentes dos folds:
essa medida pode refletir o efeito da partição. A comparação usa métricas por fold.

**2024 não foi avaliado por modelo.** Sua Gold foi construída e auditada apenas quanto
à integridade. Nenhum limiar foi otimizado; 0,5 é somente a referência inicial.
Os folds da confirmação participaram da busca em amostra; esta CV não é aninhada
e tem potencial otimismo por seleção. A tabela não substitui o teste temporal final.

## 7. Interpretação dos resultados

As duas variantes logísticas superaram o baseline em AP, ROC-AUC e Brier. O ganho médio de AP
dos seis atributos sobre rede/UF foi de **0,004819**, ou **0,482 ponto percentual**,
positivo nos três folds. É uma contribuição pequena dos quatro atributos numéricos
para este modelo linear. Não foi estimado intervalo de confiança para o ganho.

No limiar 0,5, a logística completa recupera 36,75% dos não alfabetizados e perde a
maioria dos casos de interesse. Seu recall supera rede/UF, acompanhado de menor
precisão. A acurácia, isoladamente, não deve orientar a seleção. Estes são resultados
de desenvolvimento em municípios separados, sem evidência ainda de desempenho em 2024.

O boosting completo atingiu AP **0,543776**, ganho de **0,005673** sobre a logística
completa e **0,010195** sobre boosting rede/UF. O ganho de AP foi positivo nos três
folds, mas ROC-AUC e Brier pioraram no fold 2 frente à logística completa.
No limiar 0,5, o recall caiu para 34,71%, enquanto a precisão subiu para 57,80%.
A maior AP não implica melhoria de todas as métricas nem um limiar operacional adequado.
As diferenças não foram submetidas a teste de significância.

## 8. Insights obtidos

Em 2023, 625.382 avaliações elegíveis (41,61%) têm resultado não alfabetizado. Entre
os recortes regionais disponíveis, essa proporção vai de 32,27% no Sul a 48,89% no Norte.
Essas são taxas descritivas sem ponderação, e não indicadores oficiais nacionais.

Há **5.881 perfis distintos dos seis atributos** entre 1.502.809 avaliações. Os gráficos
de contexto usam uma observação por município para não repetir o mesmo valor milhares
de vezes. População e PIB apresentam assimetria, representada em escala logarítmica na
EDA. Essas observações sustentam a avaliação territorial e as transformações implementadas.
O ganho preditivo do enriquecimento foi medido separadamente nos dois algoritmos.

A leitura inicial dos coeficientes numéricos indica associação condicional positiva
de população e participação dos serviços públicos com risco; PIB per capita tem
coeficiente negativo nos três folds e agropecuária muda de sinal entre folds. São
coeficientes padronizados do modelo, sem interpretação causal. A [figura de coeficientes](images/06_coeficientes_numericos_2023.png)
mostra média e desvio entre folds, que não equivalem a intervalo de confiança.

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
- Até aqui há baseline, comparação linear e boosting em 2023. A generalização temporal, a
  calibração e a utilidade operacional ainda precisam de avaliação. O experimento
  não mede evolução de crianças ou efeito de políticas públicas.

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

1. Consolidar seleção com 2023, interpretar previsões e definir/congelar o limiar.
2. Ajustar o modelo escolhido em todo 2023 e avaliar uma única vez em 2024.
3. Análises estratégicas, relatório técnico, apresentação e vídeo de até cinco minutos.
4. Conferência de acesso ao repositório e ao vídeo para a entrega acadêmica.

Repositório público: [andreferraz-fiap-fase2/tech-challenge-fase3](https://github.com/andreferraz-fiap-fase2/tech-challenge-fase3).
A branch `main` reúne a implementação integrada. `feature/gold-eda-baseline` preserva
a primeira execução e `feature/logistica-comparacao` registra a rodada logística.
`feature/gradient-boosting` registra a busca e sua confirmação.
A integração fica registrada nos [pull requests](https://github.com/andreferraz-fiap-fase2/tech-challenge-fase3/pulls?q=is%3Apr).
O trabalho é individual; as verificações são documentadas sem simular revisão por terceiros.
O repositório pode ser consultado sem autenticação.

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
uv run python -m src.pipeline logistic
uv run python -m src.pipeline boosting
uv run ruff check .
uv run ruff format --check .
```

`gold` reconstrói as duas partições; `eda`, `baseline`, `logistic` e `boosting` leem
exclusivamente o caminho de 2023. `run-all` inclui ambas as comparações. A CLI permite
`--root /outro/diretorio` antes do subcomando; nesse caso, copiar
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
src/modeling/           Baseline, Regressão Logística e Gradient Boosting
src/evaluation/         Métricas e resumos de desenvolvimento
src/visualization/      Figuras em PNG e SVG
src/usecase/            Orquestração das etapas
src/pipeline.py         CLI
reports/                Métricas, auditorias e análise em Markdown/CSV/JSON
images/                 Oito figuras, cada uma em PNG e SVG
artifacts/              Probabilidades, amostra e 12 pipelines de validação (fora do Git)
tests/                  Testes de integridade, vazamento e orientação do alvo
```

Verificações atuais: **56 testes aprovados**, lint/formatação aprovados. Há 14 avisos
de depreciação de Matplotlib/Pyparsing na suíte; nenhum aviso de convergência do modelo.
A reprodução da logística usa saídas vazias e somente a Gold de 2023. Compara métricas,
iterações, previsões, coeficientes, pipelines e figuras; tempos de execução são excluídos
da comparação de igualdade. A releitura de seis pipelines reproduz 100 previsões de
validação por modelo com tolerância absoluta 1e-12. Consulte os relatórios de reprodução
das etapas 04 e 05. A reprodução do boosting repete também a amostragem e a busca;
13 arquivos são idênticos por SHA-256, incluindo seis pipelines reabertas, amostra,
OOF e figuras. A Gold de 2024 está ausente no diretório de reprodução. Executar:

```bash
uv run python -m src.usecase.reproduce_boosting
```

Os modelos salvos são dos folds, não um ajuste final em todo 2023.
Dados individuais, ambientes virtuais, credenciais e artefatos por aluno não vão ao Git.

### Referências técnicas

- [IBGE: arquivo histórico do PIB dos Municípios, edição 2020](https://ftp.ibge.gov.br/Pib_Municipios/2020/base/base_de_dados_2010_2020_txt.zip).
- [IBGE: estimativas originais DOU de 2021](https://ftp.ibge.gov.br/Estimativas_de_Populacao/Estimativas_2021/estimativa_dou_2021.ods).
- [Scikit-learn: DummyClassifier](https://scikit-learn.org/stable/modules/generated/sklearn.dummy.DummyClassifier.html).
- [Scikit-learn: average precision](https://scikit-learn.org/stable/modules/generated/sklearn.metrics.average_precision_score.html).
- [Scikit-learn: prevenção de vazamento](https://scikit-learn.org/stable/common_pitfalls.html).
- [Scikit-learn 1.7: Regressão Logística](https://scikit-learn.org/1.7/modules/generated/sklearn.linear_model.LogisticRegression.html).
- [Scikit-learn 1.7: OneHotEncoder](https://scikit-learn.org/1.7/modules/generated/sklearn.preprocessing.OneHotEncoder.html).

Documentos de referência: enunciado `[IAST] - Tech Challenge - Fase 3.pdf`, entrega
da Fase 2 e documentos 01–04 em `FIAP/Fase3/Planejamento`. Relatório consolidado desta
etapa: `05-Regressao-Logistica-Fase3-v0.1`, na mesma pasta. Vídeo final: pendente.
