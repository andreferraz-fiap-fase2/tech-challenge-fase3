# Protocolo da busca de Gradient Boosting · 09/09/2026

Definido antes da execução. Complementa o contrato analítico v0.1 sem mudar
população, alvo, seis atributos, datas das fontes ou mapa de folds.

- HistGradientBoostingClassifier do scikit-learn 1.7.2; perda log_loss.
- Duas variantes: rede/UF e completa. Busca separada com o mesmo orçamento.
- Amostra de até 50.000 alunos por fold fixo de 2023: menores SHA-256 de
  `42|ano|id_aluno`, em UTF-8; empate por id. Sem usar rótulos ou pesos na seleção.
  Amostragem por aluno, sem balanceamento de classes ou de municípios. Não é uma
  seleção de 50.000 municípios. Municípios pequenos podem não aparecer na amostra.
- Treino em dois folds e validação no terceiro, repetidos três vezes por candidato.
  Municípios exclusivos continuam exclusivos. Pré-processamento aprende só no treino.
- Seis candidatos: produto de 7/15/31 folhas máximas e 100/200 iterações.
  Learning rate 0,05; mínimo de 100 observações por folha; regularização L2 = 1.
- Parada automática desativada: não há divisão aleatória interna para early stopping.
  Semente 42, uma thread, sem pesos ou class_weight no ajuste.
- Categorias imputadas com constante e codificadas no treino, explicitamente marcadas
  como nominais no estimador. Categoria inédita vira NaN. Numéricos: mediana do treino,
  sem log ou escala. Na logística, log e escala permanecem conforme protocolo anterior.
- Seleção pela maior AP de risco média nos três folds; empate exato favorece menos
  folhas, depois menos iterações, depois nome. ROC, Brier e tempos apenas relatados.
- Vencedor de cada variante confirmado nos mesmos folds, agora com todos os
  1.502.809 alunos de 2023. Isso requer 36 ajustes na busca e 6 na confirmação.
- AP é average precision, classe positiva = não alfabetizado; não é a precisão
  de uma decisão binária. Métricas binárias usam limiar descritivo de 0,5.
- Pesos entram somente na avaliação suplementar da confirmação. Na busca, a seleção
  usa a métrica não ponderada. Não há alegação de representatividade populacional.

A confirmação usa os mesmos folds que participaram da busca em amostra; a validação
não é aninhada. Portanto, as métricas de desenvolvimento têm viés de seleção potencial
e não constituem estimativa final independente. Só 2024 poderá medir o desempenho
temporal depois de escolher e congelar modelo e limiar com 2023. Este comando não lê
a Gold de 2024, não escolhe limiar e não ajusta um modelo final em todo 2023.

Configuração executável: [experimento-boosting.json](../config/experimento-boosting.json).
Referência técnica para categorias, probabilidades e parada automática:
[HistGradientBoostingClassifier, documentação 1.7.2](https://scikit-learn.org/1.7/modules/generated/sklearn.ensemble.HistGradientBoostingClassifier.html).
