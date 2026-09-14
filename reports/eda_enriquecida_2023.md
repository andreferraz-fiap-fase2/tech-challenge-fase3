# EDA consolidada — base enriquecida de 2023

**Autor: André Mohallem Ferraz · Consolidação descritiva posterior aos experimentos**

## População, enriquecimento e unidades

São os mesmos **1.502.809 alunos avaliados**, em **4.871 municípios** e **5.881 contextos
município × rede**. O enriquecimento amplia de seis para nove atributos: rede, UF,
quatro indicadores do IBGE e três indicadores educacionais do Inep. Ele acrescenta
informação contextual; não aumenta o número de alunos nem cria observações independentes.

O modelo final 1.0 utiliza seis atributos. Os nove pertencem ao estudo complementar
exploratório de 2023. Esta consolidação não ajusta modelos, não seleciona atributos
e não lê dados de 2024. Todos os números abaixo foram confrontados com as tabelas
existentes, preservando a Gold enriquecida e os resultados já publicados.

## Distribuições e ausências

Os histogramas usam uma observação por município × rede; cada contexto tem o mesmo
peso. Os valores ausentes são excluídos de cada estatística descritiva, sem imputação.

| Indicador Inep, anos iniciais de 2021 | Mediana | Intervalo observado | Contextos válidos | Contextos ausentes | Alunos sem indicador |
| --- | ---: | ---: | ---: | ---: | ---: |
| Alunos por turma | 19,5 | 3,6–34,8 alunos | 5.871 | 10 | 213 |
| Funções docentes com curso superior | 94,4% | 4,7–100% | 5.872 | 9 | 173 |
| Horas de aula por dia | 4,3 | 3,0–10,3 horas | 5.871 | 10 | 213 |

As distribuições mostram diferenças entre contextos. O percentual de funções docentes com
curso superior se concentra em valores elevados, com mediana de 94,4%; as horas diárias
têm mediana de 4,3 e cauda até 10,3. Valores nas caudas não são automaticamente erros
e não foram removidos por esta consolidação. Médias, quartis, desvios e extremos estão
na [tabela de distribuições](eda_enriquecida_2023_distribuicoes.csv).

A cobertura por aluno é 99,9858% em turmas/horas e 99,9885% em funções docentes. Na comparação
complementar já executada, a mediana de cada atributo foi aprendida somente no treino
do fold para tratar as ausências residuais. A [tabela de cobertura](eda_enriquecida_2023_cobertura.csv)
separa denominadores estudantis e contextuais.

![Distribuições do Inep](../images/16_eda_inep_2023.png)

## Correlações e interpretação

Os gráficos e a [tabela de associações](eda_enriquecida_2023_correlacoes.csv) usam sempre
a **taxa observada de alfabetização** como alvo. Para o IBGE, as correlações originais
de Spearman com não alfabetização têm o sinal invertido. A agregação municipal refeita
confirma essa equivalência. Para o Inep, são preservadas as correlações de Pearson
com alfabetização por município × rede; a nova agregação reproduz as tabelas existentes.

| Associação com alfabetização | Método | Unidade | Coeficiente |
| --- | --- | --- | ---: |
| População | Spearman | município | -0,182 |
| PIB per capita | Spearman | município | +0,266 |
| Agropecuária / VAB | Spearman | município | +0,196 |
| Serviços públicos / VAB | Spearman | município | -0,284 |
| Alunos por turma | Pearson | município × rede | -0,155 |
| Funções docentes com curso superior | Pearson | município × rede | +0,204 |
| Horas de aula por dia | Pearson | município × rede | -0,025 |

Coeficiente positivo indica associação com maior taxa de alfabetização; negativo,
com menor taxa, dentro da unidade observada. Métodos, anos e unidades diferentes limitam
comparações diretas entre coeficientes. Nenhum coeficiente demonstra efeito causal,
explica a trajetória individual de um aluno ou equivale à importância no modelo.

A correlação de Spearman entre PIB per capita e participação dos serviços públicos
no VAB é **-0,934930**, em 4.871 municípios. A associação forte sugere redundância
entre esses atributos contextuais e exige cautela ao interpretar contribuições isoladas.
Ela não comprova causalidade e não motivou exclusão posterior de atributos do modelo final.

![Correlações com alfabetização](../images/17_correlacoes_contextuais_2023.png)

## Cronologia e relação com a modelagem

A EDA inicial antecedeu os modelos e examinou classes, regiões, distribuições, ausências
e repetição de contextos. As correlações originais do IBGE foram calculadas posteriormente,
na interpretação. A EDA dos três indicadores do Inep, incluindo correlações, foi gravada
antes dos ajustes de sua comparação exploratória, conforme o
[registro anterior ao ajuste](estudo_educacional_eda_2023.json).

**Estes novos gráficos são uma consolidação posterior** de dados e resultados já
existentes. Não são apresentados como análises que orientaram decisões no passado.
Distribuições e ausências ajudam a entender a imputação; contextos repetidos fundamentam
a separação por município; as associações ajudam a interpretar o contexto estudado.
A comparação de seis e nove atributos apresentou ganho médio pequeno de AP (+0,000531),
com melhora em dois folds e piora em um. Significância estatística não foi demonstrada.

[Proveniência e verificações](eda_enriquecida_2023.json) ·
[Comparação complementar já executada](estudo_educacional_2023.md).
