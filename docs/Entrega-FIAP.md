# Entrega — FIAP Tech Challenge Fase 3

**Autor: André Mohallem Ferraz · Trabalho individual · Prazo informado: 15/09/2026**

[Repositório público](https://github.com/andreferraz-fiap-fase2/tech-challenge-fase3) ·
[Publicação oficial 1.7](https://github.com/andreferraz-fiap-fase2/tech-challenge-fase3/releases/tag/v1.7-entrega).

A organização segue o formato usado na Fase 2: documento técnico, apresentação e vídeo
executivo. O PDF e o PowerPoint compõem o pacote oficial; o roteiro da apresentação,
distribuído em dez janelas que somam cinco minutos, fica em `docs/Roteiro-Video-Fase3.md`.

## Mapa do enunciado

| Item solicitado | Evidência na entrega |
| --- | --- |
| Evolução da Fase 2, Gold e enriquecimento | [README, seções 1–3](../README.md), [contrato](../config/contrato-ml-aluno.json), [entradas](../data/README.md) |
| Pergunta probabilística, critério observado e classificação | [Pergunta e linhagem](Pergunta-e-Linhagem.md), [demonstração executável](Demonstracao-Previsao.md) |
| Enriquecimento educacional complementar | [Fontes Inep](Fontes-Educacionais.md), [protocolo exploratório](Protocolo-Estudo-Educacional.md) |
| EDA, distribuições, padrões e correlações | [Seção própria no README](../README.md#4-análise-exploratória-e-entendimento-do-problema), [síntese dos dados enriquecidos](../reports/eda_enriquecida_2023.md), [distribuições do Inep](../images/16_eda_inep_2023.png), [associações contextuais](../images/17_correlacoes_contextuais_2023.png) |
| Ligação entre EDA, hipóteses e modelagem | [Tabela de evidências, hipóteses e decisões](../README.md#44-das-evidências-às-hipóteses-e-decisões), [cronologia das análises](../README.md#41-população-unidades-de-análise-e-cronologia) |
| Imputação, transformação e pré-processamento integrado | [Preprocessing](../src/preprocessing/), [modelos](../src/modeling/) |
| Treino, validação, prevenção de vazamento e reprodutibilidade | [Folds municipais](../config/folds-municipios-2023.csv), [protocolo final](../reports/protocolo-final.md), [reprodução completa](../reports/reproducibilidade_completa.json) |
| Comparação e otimização | [Busca limitada](../reports/boosting_protocolo.md), [comparação](../reports/modelos_comparacao_2023.csv) |
| Avaliação, métricas e generalização | [Teste temporal](../reports/teste_temporal_2024.json), [curvas](../images/11_curvas_teste_2024.png) |
| Interpretação dos fatores | [Permutação em validação](../reports/importancia_permutacao_2023.csv), [figura](../images/10_importancia_permutacao_2023.png), [ablação da UF](../reports/ablacao_uf_2023.md) |
| Municípios com maior risco | [Tabela municipal, n ≥ 100](../reports/municipios_risco_2024.csv) |
| Regiões com perfis semelhantes | [Perfis de 2023](../reports/regioes_semelhantes_2023.csv) |
| Análise de metas e caminho para previsão futura | [Cenários condicionais de 2024](../reports/cenarios_metas_2024.csv), [limites e evolução necessária](../README.md); ainda sem previsão futura validada |
| Documentação técnica e 11 tópicos do README | [Relatório técnico](Relatorio-Tecnico-Fase3.md), [README](../README.md): os 11 tópicos foram preservados e a EDA ganhou uma seção adicional, totalizando 12 seções numeradas |
| Vídeo executivo de até cinco minutos | [Roteiro em dez janelas](Roteiro-Video-Fase3.md), alinhado aos dez slides da apresentação |
| Estrutura e versionamento Git | `data/`, `notebooks/`, `src/`, `reports/`, `images/`, `requirements.txt`, `.gitignore`, branches e pull requests |

Scripts executam os experimentos; a pasta `notebooks/` explica essa opção. A interpretação
utiliza importância por permutação. O cenário de 80% mantém o contexto de 2024 e não é
previsão validada de 2030 nem probabilidade de descumprimento de meta.

## Arquivos oficiais

| Arquivo | Conteúdo |
| --- | --- |
| [VisaoTecnica-TechChallengeFase3.pdf](https://github.com/andreferraz-fiap-fase2/tech-challenge-fase3/releases/download/v1.7-entrega/VisaoTecnica-TechChallengeFase3.pdf) | Relatório técnico com problema, EDA, modelagem, resultados e limitações. |
| [Apresentacao-TechChallenge-Fase3.pptx](https://github.com/andreferraz-fiap-fase2/tech-challenge-fase3/releases/download/v1.7-entrega/Apresentacao-TechChallenge-Fase3.pptx) | Apresentação executiva para exposição do trabalho pelo autor. |
| [TechChallenge-Fase3.zip](https://github.com/andreferraz-fiap-fase2/tech-challenge-fase3/releases/download/v1.7-entrega/TechChallenge-Fase3.zip) | Contém exclusivamente o PDF técnico e o PowerPoint acima. |

Esses três arquivos compõem a pasta `Entrega-Final`. O ZIP é uma alternativa para obter
os dois documentos juntos. Código e evidências analíticas continuam disponíveis no
repositório público. Fontes, Gold, modelos, roteiros, narrações, guias e verificadores
ficam no arquivo de `Preparacao`, fora da pasta e do ZIP oficiais.

O material para ensaiar a apresentação permanece disponível ao autor em `Preparacao`.
Os slides 6–8 respondem às cinco perguntas estratégicas: fatores associados, importância
no modelo, municípios de maior risco, regiões semelhantes e cenários de metas.
O repositório está identificado por links clicáveis no PDF e no PowerPoint.

A revisão 1.7 fecha duas lacunas de conteúdo. Primeira: a seção 6.2 declarava que uma
versão sem `sigla_uf` **ainda não havia sido treinada**; agora ela foi. A ablação reajusta
o modelo congelado sem esse atributo, nos mesmos folds e alunos, e mede a diferença —
remover a UF custa 0,079652 de AP, ou 62,4% de toda a vantagem sobre o baseline. Segunda:
o enriquecimento educacional do Inep, que antes só aparecia ao final da seção 3 e na 5.2,
agora é anunciado no resumo, na abertura da seção 3 e na síntese executiva do PDF, com os
dois motivos da não promoção explicitados — ganho pequeno e teste de 2024 já observado.

A revisão 1.6 havia esclarecido a seção 6 do PDF: comparação dos modelos, papel da UF e
escolha do limiar de alerta. Tudo isso é preservado, junto do experimento validado 1.0,
da EDA dos dados enriquecidos, do estudo educacional e da demonstração.
**Nenhum modelo, limiar ou resultado publicado foi alterado**: a ablação é interpretativa,
não lê a Gold de 2024 e não promove nova candidata. Na sua execução, a variante de seis
atributos reproduziu exatamente as métricas já publicadas, fold a fold.
