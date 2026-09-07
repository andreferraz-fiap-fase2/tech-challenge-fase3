# Primeiro baseline — desenvolvimento de 2023

DummyClassifier com a frequência das classes **dos municípios de treino de cada fold**.
Validação em três folds por município; pesos não usados no ajuste. Resultados principais
são médias das métricas de cada fold, com igual peso entre folds.

| Métrica, classe de risco = não alfabetizado | Média nos folds |
| --- | ---: |
| ROC-AUC | 0.5000 |
| Average precision | 0.4161 |
| Acurácia no limiar 0,5 | 58.39% |
| Recall de não alfabetizado no limiar 0,5 | 0.00% |

O baseline não distingue alunos: atribui a todos os casos de validação a mesma
probabilidade aprendida no respectivo treino. A average precision acompanha a
prevalência da classe de risco. A acurácia reflete a classe majoritária e, isoladamente,
não comprova utilidade para detectar não alfabetização.

O JSON contém métricas por fold, desvio entre folds, Brier, matriz de confusão e uma
visão de avaliação ponderada por peso_aluno, cuja representatividade requer discussão
da fonte. Não agregar probabilidades constantes diferentes dos folds em uma única
ROC-AUC para comparar os modelos: isso introduz um efeito da partição. Comparar as
métricas por fold sob o mesmo protocolo.

**2024 permanece reservado, sem avaliação de modelo.** Não foi escolhido um modelo
final nem ajustado um limiar operacional nesta etapa. Próxima comparação: Regressão
Logística com rede/UF e com os seis atributos, seguida de Gradient Boosting.
