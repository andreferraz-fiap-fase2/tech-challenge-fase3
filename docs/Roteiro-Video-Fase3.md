# Roteiro de preparação do vídeo executivo — Fase 3

**Autor: André Mohallem Ferraz · Revisão 1.7 · Duração planejada: até 5 minutos**

As janelas somam 5 minutos e incluem pausas e transições. São uma estimativa para ensaio, não uma duração de gravação medida. Material de apoio, fora do ZIP e da pasta oficial. O vídeo oficial deverá ser gravado com a voz do autor. As notas do PowerPoint permanecem vazias.

## 00:00–00:25 — Slide 1

Este projeto de André Mohallem Ferraz estima a probabilidade de alfabetização de um aluno do segundo ano, considerando seu contexto. O resultado observado segue o critério de setecentos e quarenta e três pontos de proficiência. A estimativa apoia perguntas sobre fatores associados, territórios, semelhanças regionais e metas, sem substituir a avaliação pedagógica individual.

## 00:25–00:55 — Slide 2

A base reúne avaliações reais em dois ciclos. Reconstruímos a Gold por aluno a partir da Silver e dos originais da Fase dois, com enriquecimento do IBGE. A nota define o alvo e fica fora dos preditores. Usamos três divisões por município em dois mil e vinte e três, com pré-processamento aprendido no treino, e teste separado em dois mil e vinte e quatro.

## 00:55–01:25 — Slide 3

A exploração encontrou quarenta e um vírgula sessenta e um por cento de não alfabetização e contextos repetidos, justificando validação municipal. No Inep, as medianas são dezenove vírgula cinco alunos por turma, noventa e quatro vírgula quatro por cento de funções docentes com superior e quatro vírgula três horas diárias. Cada histograma conta uma vez cada município e rede, sem multiplicar contextos pelos alunos.

## 01:25–01:55 — Slide 4

Comparamos baseline, regressão logística e Gradient Boosting. O modelo escolhido alcançou average precision de zero vírgula cinco um seis, contra zero vírgula quatro zero dois da referência. Essa métrica mede ordenação do risco. O limiar F dois recupera noventa e nove vírgula trinta por cento dos casos, mas sinaliza noventa e seis vírgula oitenta e quatro por cento dos alunos: não seleciona ninguém na prática. O valor está na ordenação. Se a capacidade permite atender dez por cento dos alunos, o grupo priorizado tem sessenta e três por cento de não alfabetizados, contra quarenta e dois por cento na população.

## 01:55–02:25 — Slide 5

Construímos e avaliamos três indicadores educacionais do Inep sobre os seis atributos originais, mantendo os mesmos alunos, divisões e parâmetros. A cobertura supera noventa e nove vírgula noventa e oito por cento. O ganho de average precision foi pequeno, positivo em duas divisões e negativo em uma. Não promovemos essa expansão por dois motivos: o ganho é pequeno e sem significância demonstrada, e o teste de dois mil e vinte e quatro já havia sido observado. Preservar a validade do teste único vale mais do que incorporar um ganho marginal.

## 02:25–03:00 — Slide 6

Sobre os fatores associados, funções docentes com superior apresentam associação positiva com alfabetização; alunos por turma, negativa; horas diárias, próxima de zero. Isso não demonstra impacto causal. A dependência do modelo responde outra pergunta, e medimos por dois caminhos. Ao permutar atributos, a maior perda ocorre com a unidade federativa: zero vírgula onze contra zero vírgula zero um de todos os outros somados. Ao retreinar sem a unidade federativa, o modelo perde sessenta e dois vírgula quatro por cento de toda a vantagem que tem sobre a referência constante. O que o modelo ordena é, em boa parte, diferença entre estados.

## 03:00–03:35 — Slide 7

Entre municípios com pelo menos cem avaliações, Aracaju e Nossa Senhora do Socorro apresentam os maiores riscos médios previstos: aproximadamente sessenta e oito e sessenta e sete por cento. Os dez primeiros estão em Sergipe, evidenciando dependência estadual. Nos perfis econômicos de dois mil e vinte e três, Centro-Oeste e Sul são os mais próximos. Isso não implica taxas de alfabetização iguais nem constitui agrupamento automático de alunos.

## 03:35–04:05 — Slide 8

Para metas, mil quinhentos e noventa e dois municípios ficam abaixo da referência de dois mil e vinte e quatro. No cenário de oitenta por cento, são dois mil setecentos e sessenta e sete. Comparamos médias ponderadas das probabilidades mantendo a composição observada. Esses cenários não preveem dois mil e trinta nem estimam a probabilidade de descumprimento. Uma previsão futura exige novos ciclos e avaliação independente.

## 04:05–04:30 — Slide 9

A demonstração para o perfil histórico de Belo Horizonte municipal estima cinquenta e oito vírgula sessenta e seis por cento de alfabetização. A referência de cinquenta por cento classifica como alfabetizado; a política F dois sinaliza atenção. A probabilidade é a mesma, com decisões diferentes. O exemplo não é uma previsão individual para dois mil e vinte e seis.

## 04:30–05:00 — Slide 10

A recomendação é investigar territórios combinando risco, volume, cobertura e evidências pedagógicas locais. Para avançar em metas futuras, precisamos ampliar ciclos, obter atributos anteriores ao período previsto e reservar avaliação independente. O repositório indicado reúne código, métodos e resultados verificáveis. A contribuição é apoiar decisões com evidências e limites claros, distinguindo associação, previsão e causalidade.

## Orientação de apresentação

Ensaiar como reunião executiva e concluir em até 5 minutos. As cinco perguntas estratégicas são respondidas nos slides 6 a 8: fatores associados, influência no modelo, municípios de maior risco, semelhanças regionais e metas futuras. Distinguir associação de causalidade, semelhança contextual de agrupamento e cenário de previsão futura. Explicar AP sem confundir com acurácia. Não afirmar que o cenário de 80% prevê 2030.

[Repositório do projeto](https://github.com/andreferraz-fiap-fase2/tech-challenge-fase3).
