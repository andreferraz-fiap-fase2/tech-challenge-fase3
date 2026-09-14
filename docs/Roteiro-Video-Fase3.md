# Roteiro do vídeo executivo — Fase 3

**Autor: André Mohallem Ferraz · Revisão 1.3 · Duração planejada: 5 minutos**

As janelas abaixo somam 5 minutos e incluem pausas e transições. São uma estimativa para ensaio, não uma duração de gravação medida. Esta revisão atualiza o roteiro e os slides; o vídeo narrado 1.2 permanece preservado.

## 00:00–00:30 — Slide 1

Este projeto de André Mohallem Ferraz estima a probabilidade de um aluno do segundo ano ser considerado alfabetizado, dado seu contexto. O resultado observado segue o critério de setecentos e quarenta e três pontos de proficiência. O modelo produz uma probabilidade; um limiar transforma essa estimativa em classificação. A previsão contextual apoia a análise territorial, sem substituir a avaliação pedagógica individual.

## 00:30–01:10 — Slide 2

A base reúne três milhões e trezentas e cinquenta mil avaliações reais elegíveis em dois ciclos. A Gold por aluno foi reconstruída da Silver e dos originais da Fase dois, com auditoria e enriquecimento do IBGE. A nota define o alvo e fica fora dos preditores. O estudo educacional acrescenta três indicadores do Inep aos seis atributos originais. São mais informações sobre os mesmos alunos de dois mil e vinte e três, sem aumentar a amostra nem incorporar o teste à exploração.

## 01:10–01:55 — Slide 3

A exploração encontrou quarenta e um vírgula sessenta e um por cento de não alfabetização, com diferenças entre regiões. População e PIB têm distribuições assimétricas, justificando transformação logarítmica na regressão logística. Apenas cinco mil oitocentos e oitenta e um perfis originais representam um milhão e meio de avaliações. Por isso, os municípios foram mantidos inteiros nas três divisões de validação. Medianas e transformações são aprendidas somente no treino. O relatório relaciona achados, hipóteses e decisões e distingue a exploração inicial das análises complementares realizadas posteriormente.

## 01:55–02:30 — Slide 4

Comparamos uma referência constante, regressão logística e Gradient Boosting. Modelo e limiar foram congelados antes do teste temporal de dois mil e vinte e quatro. A average precision do modelo foi zero vírgula cinco um seis, acima de zero vírgula quatro zero dois do baseline. Essa métrica mede ordenação do risco, não acurácia. O desempenho caiu em municípios novos, mostrando limites de generalização para contextos pouco conhecidos.

## 02:30–03:05 — Slide 5

O limiar escolhido pela métrica F dois prioriza recuperar casos de não alfabetização. No teste, identificou mais de noventa e nove por cento desses casos, mas sinalizou quase noventa e sete por cento dos alunos. Isso oferece pouca seletividade para uma equipe com capacidade limitada. A referência de cinquenta por cento sinaliza menos alunos, mas recupera apenas um quarto dos casos. O modelo ainda não sustenta uma triagem individual autônoma.

## 03:05–03:40 — Slide 6

A exploração educacional usa uma observação por município e rede. As medianas são dezenove vírgula cinco alunos por turma, noventa e quatro vírgula quatro por cento das funções docentes com curso superior e quatro vírgula três horas diárias de aula. A cobertura supera noventa e nove vírgula noventa e oito por cento dos alunos. As associações com alfabetização são modestas, e a de horas de aula é próxima de zero. Essas correlações contextuais não medem efeitos causais.

## 03:40–04:20 — Slide 7

A hipótese complementar é que esses indicadores acrescentem informação ao contexto do IBGE. A comparação manteve os mesmos alunos, divisões municipais e parâmetros do modelo. A exploração do Inep foi registrada antes desses ajustes. O ganho de average precision foi pequeno: melhorou em duas divisões e piorou em uma. O estudo reutiliza desenvolvimento conhecido, sem novo teste independente. Por isso, a expansão com nove atributos não substitui o modelo de referência com seis.

## 04:20–05:00 — Slide 8

A demonstração recebe perfis históricos de município e rede. Para Belo Horizonte municipal, estima cinquenta e oito vírgula sessenta e seis por cento de probabilidade de alfabetização. A regra de cinquenta por cento classifica como alfabetizado; a política sensível de F dois sinaliza atenção. A probabilidade é a mesma, mas as decisões refletem objetivos diferentes. Para gestores, a recomendação é combinar contexto, volume, cobertura e evidência pedagógica local. Os dados não sustentam uma previsão individual para dois mil e vinte e seis.

## Orientação de apresentação

Apresentar como reunião executiva. Ensaiar dentro das janelas de tempo e ajustar as pausas para concluir em até 5 minutos. Explicar AP sem confundir com acurácia e correlação sem atribuir causalidade. Enfatizar a baixa seletividade e os limites de generalização. O vídeo 1.2 corresponde à revisão anterior e não foi regravado para esta atualização documental.
