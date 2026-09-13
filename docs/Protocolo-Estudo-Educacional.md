# Estudo complementar — contexto educacional histórico

**Autor: André Mohallem Ferraz · Protocolo 1.0 exploratório · 13/09/2026**

## Pergunta e limite da comparação

Hipótese: indicadores educacionais dos anos iniciais acrescentam informação às estimativas
de alfabetização produzidas com rede, UF e contexto demográfico/econômico do IBGE.
O alvo permanece `alfabetizado`, auditado pelo critério de proficiência ≥743 pontos.
A proficiência não integra os preditores. A saída é uma probabilidade condicionada aos
atributos contextuais disponíveis, sem identificação longitudinal da criança.

O teste temporal de 2024 do experimento 1.0 já foi observado. A nova comparação é
**exploratória**, utiliza exclusivamente 2023 e não oferece um novo teste independente.
Nenhum dado de 2024 será carregado para avaliar ou selecionar a expansão. O modelo final,
seu limiar e os resultados temporais publicados permanecem como referência da entrega.
Uma eventual promoção da expansão exigirá um novo protocolo com avaliação independente.

## Fontes, junção e admissão

Serão avaliados três indicadores do Inep referentes a 2021: média de alunos por turma,
percentual de docentes com curso superior e média de horas de aula diária, nos anos
iniciais do ensino fundamental. A edição utilizada precisa ter evidência de divulgação
até 31/12/2022. Data de referência e data de publicação serão registradas separadamente.

A unidade de junção será município × rede Estadual/Municipal, com localização Total.
Não se presume equivalência entre `id_escola` e o código INEP. Cada chave contextual
precisa ser única. A união à Gold de desenvolvimento mantém todas as linhas, seus
rótulos e seus folds. A cobertura mínima previamente definida é 95% dos alunos em
cada novo atributo; abaixo disso, a execução bloqueia a comparação desta versão.
Essa regra trata disponibilidade dos dados e não depende de desempenho preditivo.
Ausências residuais são imputadas pela mediana aprendida exclusivamente no treino.

## Comparação fixada antes dos resultados

As variantes são `ibge` (seis atributos originais) e `ibge_inep` (os mesmos seis, mais
três indicadores educacionais). Ambas utilizam Gradient Boosting com sete folhas,
100 iterações, learning rate 0,05, mínimo de 100 alunos por folha, L2=1 e semente 42.
São os parâmetros do modelo de referência. Não haverá busca de hiperparâmetros,
calibração, reponderação de classes ou escolha de limiar nesta comparação.

Serão mantidos os três folds municipais já definidos em 2023. Cada rodada ajusta o
pré-processamento e o classificador em dois folds e prevê o terceiro. O boosting
recebe categorias explicitamente nominais e mediana numérica em uma pipeline única.
A EDA complementar registra cobertura, distribuição e associação descritiva das novas
variáveis antes do ajuste. A agregação da EDA por município × rede evita contar o mesmo
contexto milhares de vezes nas distribuições dos atributos.

A métrica principal será AP da classe não alfabetizado; ROC-AUC e Brier complementam
a avaliação probabilística. Serão apresentados resultados de cada fold, médias e
diferenças pareadas. Desvios entre três folds não serão tratados como intervalos de
confiança. A validação reutiliza dados de desenvolvimento conhecidos e permanece
sujeita a escolhas adaptativas do projeto; não demonstra causalidade ou significância.

## Integridade e reprodução

[Configuração executável](../config/estudo-educacional.json) define os parâmetros,
atributos, cobertura e hashes das entradas originais. A comparação escreve em uma
pasta nova fora da raiz do experimento. Fontes e artefatos próprios recebem hashes.
Os arquivos congelados são conferidos antes e depois da execução. Dados individuais,
previsões individuais e modelos persistidos ficam na cópia privada do projeto.
