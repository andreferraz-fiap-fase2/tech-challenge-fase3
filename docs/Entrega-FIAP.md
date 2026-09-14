# Entrega — FIAP Tech Challenge Fase 3

**Autor: André Mohallem Ferraz · Trabalho individual · Prazo informado: 15/09/2026**

[Repositório público](https://github.com/andreferraz-fiap-fase2/tech-challenge-fase3) ·
[Publicação oficial 1.4](https://github.com/andreferraz-fiap-fase2/tech-challenge-fase3/releases/tag/v1.4-entrega).

A organização segue o formato usado na Fase 2: documento técnico, apresentação e vídeo
do autor. **O PDF e o PowerPoint estão preparados; a gravação do vídeo com a voz de
André Mohallem Ferraz, de até cinco minutos, permanece pendente.** O ZIP atual contém
somente os dois documentos disponíveis.

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
| Interpretação dos fatores | [Permutação em validação](../reports/importancia_permutacao_2023.csv), [figura](../images/10_importancia_permutacao_2023.png) |
| Municípios com maior risco | [Tabela municipal, n ≥ 100](../reports/municipios_risco_2024.csv) |
| Regiões com perfis semelhantes | [Perfis de 2023](../reports/regioes_semelhantes_2023.csv) |
| Risco de metas futuras | [Cenários condicionais](../reports/cenarios_metas_2024.csv), [limites e evolução necessária](../README.md) |
| Documentação técnica e 11 tópicos do README | [Relatório técnico](Relatorio-Tecnico-Fase3.md), [README](../README.md): os 11 tópicos foram preservados e a EDA ganhou uma seção adicional, totalizando 12 seções numeradas |
| Vídeo executivo de até cinco minutos | Pendente: gravação da apresentação com a voz de André Mohallem Ferraz |
| Estrutura e versionamento Git | `data/`, `notebooks/`, `src/`, `reports/`, `images/`, `requirements.txt`, `.gitignore`, branches e pull requests |

Scripts executam os experimentos; a pasta `notebooks/` explica essa opção. A interpretação
utiliza importância por permutação. O cenário de 80% mantém o contexto de 2024 e não é
previsão validada de 2030 nem probabilidade de descumprimento de meta.

## Arquivos oficiais

| Arquivo | Conteúdo |
| --- | --- |
| [VisaoTecnica-TechChallengeFase3.pdf](https://github.com/andreferraz-fiap-fase2/tech-challenge-fase3/releases/download/v1.4-entrega/VisaoTecnica-TechChallengeFase3.pdf) | Relatório técnico com problema, EDA, modelagem, resultados e limitações. |
| [Apresentacao-TechChallenge-Fase3.pptx](https://github.com/andreferraz-fiap-fase2/tech-challenge-fase3/releases/download/v1.4-entrega/Apresentacao-TechChallenge-Fase3.pptx) | Apresentação executiva para exposição do trabalho pelo autor. |
| [TechChallenge-Fase3.zip](https://github.com/andreferraz-fiap-fase2/tech-challenge-fase3/releases/download/v1.4-entrega/TechChallenge-Fase3.zip) | Contém exclusivamente o PDF técnico e o PowerPoint acima. |

Esses três arquivos compõem a pasta `Entrega-Final`. O ZIP é uma alternativa para obter
os dois documentos juntos. Código e evidências analíticas continuam disponíveis no
repositório público. Fontes, Gold, modelos, roteiros, narrações, guias e verificadores
ficam no arquivo de `Preparacao`, fora da pasta e do ZIP oficiais.

O material para ensaiar a apresentação permanece disponível ao autor em `Preparacao`.
Após gravar o vídeo com sua voz, será necessário conferir duração de até cinco minutos
e completar a submissão no portal da FIAP até o prazo da turma. O pacote atual não é
apresentado como atendimento concluído ao requisito de vídeo.

A organização 1.4 preserva o experimento validado 1.0, a EDA dos dados enriquecidos,
o estudo educacional exploratório e a demonstração. Nenhum modelo, limiar ou resultado
temporal foi alterado para organizar os arquivos oficiais.
