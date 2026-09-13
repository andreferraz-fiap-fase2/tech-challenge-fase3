# Roteiro do vídeo executivo — Fase 3

**Autor: André Mohallem Ferraz · Duração alvo: até 5 minutos**

## Slide 1

A alfabetização é um desafio educacional e de planejamento. Este projeto de André Mohallem Ferraz transforma a engenharia de dados construída na Fase dois em uma análise de risco contextual. O objetivo é estimar a probabilidade de um aluno avaliado ser alfabetizado e apoiar a leitura dos territórios. O resultado é um instrumento exploratório: ele não substitui o diagnóstico pedagógico nem demonstra as causas das dificuldades de aprendizagem.

## Slide 2

A análise utiliza três milhões e trezentas e cinquenta mil avaliações reais elegíveis, distribuídas entre dois mil e vinte e três e dois mil e vinte e quatro. Foram retirados eventos simulados, ausências e avaliações inválidas. As fontes da fase anterior foram auditadas e enriquecidas com população e economia municipais do IBGE. São seis atributos: rede, estado, população, PIB por habitante e duas participações econômicas. A nota da própria prova ficou fora dos preditores, pois ela determina o resultado que queremos prever.

## Slide 3

A comparação respeitou uma separação por município. O treinamento e a escolha do modelo usaram somente dois mil e vinte e três, com três divisões fixas. Comparamos uma referência constante, regressão logística e Gradient Boosting. Uma busca limitada escolheu a configuração com melhor ordenação do risco. O modelo e o limiar foram congelados antes de abrir o teste de dois mil e vinte e quatro. Isso permite avaliar a generalização sem adaptar as decisões ao resultado final.

## Slide 4

No teste temporal, a average precision foi de zero vírgula cinco um seis, acima de zero vírgula quatro zero dois da referência constante. Essa métrica avalia a ordenação do risco e não deve ser confundida com acurácia. A capacidade de discriminação é moderada. Nos municípios novos, a performance caiu. Quase todos os alunos desse grupo estão no Acre, Distrito Federal e São Paulo, estados ausentes do desenvolvimento. Isso evidencia o risco de extrapolar o modelo para contextos pouco conhecidos.

## Slide 5

O critério acadêmico de escolha do limiar deu prioridade à recuperação dos casos de não alfabetização. No teste, ele identificou mais de noventa e nove por cento desses casos, mas sinalizou quase noventa e sete por cento de todos os alunos. Assim, há pouca seletividade para uma equipe com capacidade limitada. O limiar de referência, zero vírgula cinco, sinaliza menos alunos, porém recupera apenas um quarto dos casos. A conclusão é que o modelo ainda não serve como triagem individual autônoma.

## Slide 6

A análise de importância mostrou que o estado é a variável de maior influência preditiva. Os indicadores econômicos municipais agregam informação, mas com contribuição menor. Essa dependência explica por que os primeiros municípios no ranking previsto se concentram em Sergipe. Aracaju e Nossa Senhora do Socorro aparecem no topo do recorte analisado. Isso deve orientar perguntas e verificações locais, e não ser apresentado como ranking oficial ou como evidência de que o território causa o desfecho de uma criança.

## Slide 7

Os erros também mudam entre regiões. No Sul, o risco médio foi subestimado em aproximadamente sete pontos percentuais; no Centro-Oeste, foi superestimado em quase seis. Na comparação dos perfis de contexto, Centro-Oeste e Sul ficaram mais próximos, mas isso não significa resultados educacionais iguais. A análise de metas usa taxas previstas e referências municipais da fase anterior. Um cenário de oitenta por cento é apenas uma simulação com a composição de dois mil e vinte e quatro, e não uma previsão para dois mil e trinta.

## Slide 8

Para gestores, a recomendação é combinar risco contextual, quantidade de alunos, cobertura dos dados e evidências pedagógicas locais. O projeto oferece uma base auditável para planejar investigações e discutir apoio territorial. Antes de orientar atendimento ou orçamento, é necessário ampliar dados escolares, validar a cobertura e definir custos e capacidade reais. A entrega inclui código versionado, testes, documentação e reprodução do experimento. O valor está em apresentar evidências e limites com clareza para apoiar decisões responsáveis.

## Orientação de apresentação

Apresentar como reunião executiva. Explicar AP sem confundir com acurácia; enfatizar a baixa seletividade e os limites de generalização. A versão base usa narração sintética em português; os slides e o roteiro permitem regravar a apresentação com a voz do autor.
