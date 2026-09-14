# Entrega — FIAP Tech Challenge Fase 3

**Autor: André Mohallem Ferraz · Trabalho individual · Prazo informado: 15/09/2026**

[Repositório público](https://github.com/andreferraz-fiap-fase2/tech-challenge-fase3) ·
[Documentos atualizados 1.3](https://github.com/andreferraz-fiap-fase2/tech-challenge-fase3/releases/tag/v1.3-entrega) ·
[Vídeo existente 1.2, preservado](https://github.com/andreferraz-fiap-fase2/tech-challenge-fase3/releases/download/v1.2-entrega/Video-Executivo-Fase3-v1.2.mp4).

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
| Vídeo executivo de até cinco minutos | [MP4 1.2 existente](https://github.com/andreferraz-fiap-fase2/tech-challenge-fase3/releases/download/v1.2-entrega/Video-Executivo-Fase3-v1.2.mp4), com 4min53,10s; apresentação e roteiro atualizados na versão 1.3 |
| Estrutura e versionamento Git | `data/`, `notebooks/`, `src/`, `reports/`, `images/`, `requirements.txt`, `.gitignore`, branches e pull requests |

Scripts executam os experimentos; a pasta `notebooks/` explica essa opção. A interpretação
utiliza importância por permutação. O cenário de 80% mantém o contexto de 2024 e não é
previsão validada de 2030 nem probabilidade de descumprimento de meta.

## Arquivos para submissão

- [Relatorio-Tecnico-Fase3-v1.3.pdf](https://github.com/andreferraz-fiap-fase2/tech-challenge-fase3/releases/download/v1.3-entrega/Relatorio-Tecnico-Fase3-v1.3.pdf): relatório revisado, com seção própria de EDA; Word disponível na mesma versão.
- [Apresentacao-Executiva-Fase3-v1.3.pptx](https://github.com/andreferraz-fiap-fase2/tech-challenge-fase3/releases/download/v1.3-entrega/Apresentacao-Executiva-Fase3-v1.3.pptx): apresentação atualizada, com roteiro nas notas.
- [Video-Executivo-Fase3-v1.2.mp4](https://github.com/andreferraz-fiap-fase2/tech-challenge-fase3/releases/download/v1.2-entrega/Video-Executivo-Fase3-v1.2.mp4): vídeo existente, com narração sintética em português, preservado sem regeneração.
- [Roteiro-Video-Fase3-v1.3.pdf](https://github.com/andreferraz-fiap-fase2/tech-challenge-fase3/releases/download/v1.3-entrega/Roteiro-Video-Fase3-v1.3.pdf): roteiro atualizado para apresentação de até cinco minutos. Os novos trechos de EDA não integram o vídeo 1.2 já gravado.
- Pacote completo privado: código, entradas auditadas, Gold, modelos e entregáveis.
  Dados individuais e modelos serializados não integram o repositório público.

O repositório e a versão publicada fornecem os links de acesso aos avaliadores. A submissão
no portal da FIAP precisa ser realizada pelo autor até o prazo da turma. Os documentos de
planejamento anteriores são históricos; utilizar os documentos de `Entrega-Final/Revisao-1.3`
e o vídeo preservado de `Entrega-Final/Revisao-1.2`. A entrega 1.3 dá maior visibilidade
à EDA dos dados enriquecidos, mantendo o experimento validado 1.0, o estudo complementar
exploratório e a demonstração. Essas finalidades estão identificadas nos materiais;
nenhum modelo ou resultado temporal foi alterado por esta revisão documental.
