# Roteiro do vídeo executivo — Fase 3

**Autor: André Mohallem Ferraz · Duração alvo: até 5 minutos**

## Slide 1

Este projeto de André Mohallem Ferraz responde a uma pergunta: qual é a probabilidade estimada de um aluno do segundo ano ser considerado alfabetizado, dado seu contexto? O resultado observado segue o critério de setecentos e quarenta e três pontos de proficiência. O modelo estima uma probabilidade; uma regra de decisão produz a classificação. Essa diferença é importante: mudar o limiar de probabilidade não muda o padrão de alfabetização. A previsão é contextual, sem substituir uma avaliação pedagógica individual.

## Slide 2

A análise utiliza três milhões e trezentas e cinquenta mil avaliações reais elegíveis em dois ciclos. Eventos simulados, ausências e avaliações inválidas foram excluídos. A Gold anterior era municipal. Por isso, reconstruímos uma Gold por aluno a partir da Silver e dos originais da Fase dois, com auditoria e enriquecimento do IBGE. O modelo de referência usa seis atributos: rede, estado e quatro indicadores demográficos e econômicos. A nota da prova determina o alvo e fica fora dos preditores.

## Slide 3

A comparação respeitou uma separação por município. O treinamento e a escolha do modelo usaram somente dois mil e vinte e três, com três divisões fixas. Comparamos uma referência constante, regressão logística e Gradient Boosting. Uma busca limitada escolheu a configuração com melhor ordenação do risco. O modelo e o limiar foram congelados antes de abrir o teste de dois mil e vinte e quatro. Isso permite avaliar a generalização sem adaptar as decisões ao resultado final.

## Slide 4

No teste temporal, a average precision foi de zero vírgula cinco um seis, acima de zero vírgula quatro zero dois da referência constante. Essa métrica avalia a ordenação do risco e não deve ser confundida com acurácia. A capacidade de discriminação é moderada. Nos municípios novos, a performance caiu. Quase todos os alunos desse grupo estão no Acre, Distrito Federal e São Paulo, estados ausentes do desenvolvimento. Isso evidencia o risco de extrapolar o modelo para contextos pouco conhecidos.

## Slide 5

O critério acadêmico de escolha do limiar deu prioridade à recuperação dos casos de não alfabetização. No teste, ele identificou mais de noventa e nove por cento desses casos, mas sinalizou quase noventa e sete por cento de todos os alunos. Assim, há pouca seletividade para uma equipe com capacidade limitada. O limiar de referência, zero vírgula cinco, sinaliza menos alunos, porém recupera apenas um quarto dos casos. A conclusão é que o modelo ainda não serve como triagem individual autônoma.

## Slide 6

A importância por permutação mostra maior dependência do estado. Isso é contribuição preditiva, sem demonstrar causalidade. Os erros variam entre regiões: no Sul, o risco foi subestimado em cerca de sete pontos percentuais; no Centro-Oeste, superestimado em quase seis. As metas municipais da Gold anterior entram somente na análise posterior. O cenário de oitenta por cento mantém o contexto de dois mil e vinte e quatro e não constitui previsão validada para dois mil e trinta.

## Slide 7

Para investigar a dimensão educacional, acrescentamos três indicadores históricos do Inep: tamanho das turmas, funções docentes com curso superior e horas de aula. A cobertura supera noventa e nove vírgula noventa e oito por cento. A comparação exploratória usa os mesmos três grupos municipais de dois mil e vinte e três e passa de seis para nove atributos. O ganho de average precision foi pequeno: melhorou em dois grupos e piorou em um. Esse estudo não tem novo teste independente e não substitui o modelo de referência.

## Slide 8

A entrega também demonstra a previsão em perfis históricos de município e rede. Para Belo Horizonte, rede municipal, o modelo estima cinquenta e oito vírgula sessenta e seis por cento de probabilidade de alfabetização. A regra de cinquenta por cento classifica como alfabetizado, enquanto a política sensível de F dois sinaliza atenção. As probabilidades são iguais; as decisões refletem objetivos diferentes. Para gestores, a recomendação é combinar contexto, volume, cobertura e evidência pedagógica local. Código, fontes, testes e reprodução acompanham os materiais da entrega.

## Orientação de apresentação

Apresentar como reunião executiva. Explicar AP sem confundir com acurácia; enfatizar a baixa seletividade e os limites de generalização. A versão base usa narração sintética em português; os slides e o roteiro permitem regravar a apresentação com a voz do autor.
