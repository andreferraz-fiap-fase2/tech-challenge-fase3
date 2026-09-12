# Modelo e avaliação final · versão 1.0 · 12/09/2026

Autor: André Mohallem Ferraz. Decisão documentada antes de avaliar os resultados de 2024.

Selecionado HistGradientBoostingClassifier com seis atributos, 7 folhas e 100 iterações,
por maior AP média nos folds completos de 2023 (0,543776). Demais parâmetros e fontes
permanecem congelados. A busca de desenvolvimento não foi aninhada; o teste temporal
será a avaliação independente. Não será aplicada calibração adicional nesta versão.

O limiar foi escolhido maximizando F2 não ponderado nas previsões fora de fold de 2023,
conforme contrato v0.1. Empates de probabilidade são tratados juntos; empate exato em F2
favorece o maior limiar. Resultado: **0,15016323973380263**, F2 0,785237, recall 99,03%,
precisão 42,95% e **95,94% dos alunos sinalizados**. O limiar 0,5 também será reportado.
As métricas reunidas OOF não são a média simples das métricas dos folds anteriores.

Esse limiar cumpre o critério acadêmico previamente escolhido, mas oferece pouca
seletividade: especificidade de 6,25% no desenvolvimento. Não deve ser apresentado como
triagem pronta para aplicação com capacidade limitada. O valor proposto é principalmente
territorial e exploratório; a interpretação dessa limitação integra a entrega.

Sequência: salvar decisão e hashes; ajustar uma pipeline em todo 2023; conferir sua
persistência; registrar decisão e ajuste em Git; só então carregar a Gold reservada.
Na avaliação, parâmetros, atributos, probabilidades e limiar não serão alterados.

Avaliações previstas: conjunto de 2024 completo, municípios presentes em 2023 e novos;
baseline constante com prevalência aprendida em 2023; AP, ROC-AUC, Brier, carga de triagem,
F2, recall, precisão, especificidade e matrizes de confusão nos dois limiares. Pesos
serão suplementares, sem alegação de estimativa oficial nacional. Inspecionar calibração
e recortes regionais serve à descrição dos limites, sem retunar após observar o teste.

Interpretação: queda de AP por permutação em validação de 2023; cinco repetições e três
folds, sobre a amostra fixa de 150 mil alunos. Atributos territoriais permutados por
município, rede por aluno. Permutações podem criar contextos pouco plausíveis; importância
é dependência preditiva marginal, não impacto causal. Não usar 2024 para escolher variáveis.

Análise territorial: médias de probabilidades e resultados por município/região,
contagens e cobertura explícitas. Para a apresentação pública municipal, mínimo de 100
avaliações, critério descritivo de estabilidade; não é garantia estatística. Metas futuras
serão tratadas como cenários condicionais, sem confundir taxa esperada com probabilidade
de descumprimento. Não ligar alunos entre anos por identificador.

O comando de avaliação recusa nova execução sobre uma saída já concluída. Reproduzir em
outra raiz com o mesmo congelamento é verificação computacional, não nova seleção. Dados,
modelos e previsões individuais permanecem na cópia privada; relatórios agregados e código
serão publicados com autoria de André Mohallem Ferraz.
