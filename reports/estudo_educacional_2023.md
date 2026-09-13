# Estudo complementar — contexto educacional em 2023

**Autor: André Mohallem Ferraz · Protocolo 1.0 exploratório**

Comparação de seis atributos originais com nove atributos, acrescentando três
indicadores educacionais históricos do Inep. Foram mantidos os mesmos alunos,
três folds municipais e hiperparâmetros. Não houve busca, ajuste de calibração
nem escolha de limiar. As medianas e categorias foram aprendidas apenas no treino.

## Cobertura anterior ao ajuste

| Atributo | Cobertura de alunos | Cobertura de contextos município × rede |
| --- | ---: | ---: |
| alunos_por_turma_ai_2021 | 99.9858% | 99.8300% |
| docentes_superior_ai_2021 | 99.9885% | 99.8470% |
| horas_aula_ai_2021 | 99.9858% | 99.8300% |

A EDA registra uma observação por município × rede nas distribuições e
correlações com a taxa observada de alfabetização. A cobertura estudantil
é apresentada separadamente. Ausências residuais são imputadas no treino.

## Validação cruzada exploratória

| Variante | AP média ± desvio | ROC-AUC média ± desvio | Brier média ± desvio |
| --- | ---: | ---: | ---: |
| ibge | 0.543776 ± 0.003986 | 0.642578 ± 0.006533 | 0.227481 ± 0.002697 |
| ibge_inep | 0.544307 ± 0.004377 | 0.643154 ± 0.006188 | 0.227355 ± 0.002676 |

| Fold | Δ AP | Δ ROC-AUC | Δ Brier |
| --- | ---: | ---: | ---: |
| 0 | +0.000755 | +0.000535 | -0.000018 |
| 1 | +0.001603 | +0.001328 | -0.000249 |
| 2 | -0.000765 | -0.000136 | -0.000110 |

A diferença média da expansão foi +0.000531 em AP e -0.000126
em Brier. As diferenças são calculadas como expansão menos referência;
AP maior e Brier menor representam melhora nas respectivas métricas.
O desvio é amostral entre três folds, não um intervalo de confiança.

![Comparação por fold](../images/15_estudo_educacional_2023.png)

## Limites e preservação da entrega

**Significância estatística não foi demonstrada.** Correlações e diferenças
preditivas não demonstram causalidade. O estudo utiliza dados de desenvolvimento
já conhecidos e permanece sujeito às escolhas adaptativas do projeto.
O teste de 2024 já havia sido observado no experimento 1.0 e não foi carregado
para esta comparação. A integridade de artefatos existentes é conferida somente
por hash. Não existe um novo teste independente nesta análise.

A expansão não é promovida a modelo final. Permanecem válidos o modelo 1.0,
seu limiar e sua avaliação temporal. Uma promoção exige novo protocolo e
avaliação independente. A informação acrescentada é contextual por município
e rede; não identifica características da escola ou trajetória de cada aluno.

[Métricas por fold](estudo_educacional_folds_2023.csv) ·
[Distribuições](estudo_educacional_distribuicoes_2023.csv) ·
[Correlações descritivas](estudo_educacional_correlacoes_2023.csv) ·
[Registro completo](estudo_educacional_2023.json).
