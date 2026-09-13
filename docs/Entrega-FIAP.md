# Entrega — FIAP Tech Challenge Fase 3

**Autor: André Mohallem Ferraz · Trabalho individual · Prazo informado: 15/09/2026**

[Repositório público](https://github.com/andreferraz-fiap-fase2/tech-challenge-fase3) ·
[Versão final com documentos e vídeo](https://github.com/andreferraz-fiap-fase2/tech-challenge-fase3/releases/tag/v1.0-entrega).

## Mapa do enunciado

| Item solicitado | Evidência na entrega |
| --- | --- |
| Evolução da Fase 2, Gold e enriquecimento | [README, seções 1–3](../README.md), [contrato](../config/contrato-ml-aluno.json), [entradas](../data/README.md) |
| EDA, distribuições, padrões e correlações | [EDA](../reports/eda_development.md), [correlações municipais](../reports/correlacoes_municipais_2023.csv), [figuras](../images/) |
| Imputação, transformação e pré-processamento integrado | [Preprocessing](../src/preprocessing/), [modelos](../src/modeling/) |
| Treino, validação, prevenção de vazamento e reprodutibilidade | [Folds municipais](../config/folds-municipios-2023.csv), [protocolo final](../reports/protocolo-final.md), [reprodução completa](../reports/reproducibilidade_completa.json) |
| Comparação e otimização | [Busca limitada](../reports/boosting_protocolo.md), [comparação](../reports/modelos_comparacao_2023.csv) |
| Avaliação, métricas e generalização | [Teste temporal](../reports/teste_temporal_2024.json), [curvas](../images/11_curvas_teste_2024.png) |
| Interpretação dos fatores | [Permutação em validação](../reports/importancia_permutacao_2023.csv), [figura](../images/10_importancia_permutacao_2023.png) |
| Municípios com maior risco | [Tabela municipal, n ≥ 100](../reports/municipios_risco_2024.csv) |
| Regiões com perfis semelhantes | [Perfis de 2023](../reports/regioes_semelhantes_2023.csv) |
| Risco de metas futuras | [Cenários condicionais](../reports/cenarios_metas_2024.csv), [limites e evolução necessária](../README.md) |
| Documentação técnica e 11 tópicos do README | [Relatório técnico](Relatorio-Tecnico-Fase3.md), [README](../README.md) |
| Vídeo executivo de até cinco minutos | MP4, apresentação editável e roteiro na versão final |
| Estrutura e versionamento Git | `data/`, `notebooks/`, `src/`, `reports/`, `images/`, `requirements.txt`, `.gitignore`, branches e pull requests |

Scripts executam os experimentos; a pasta `notebooks/` explica essa opção. A interpretação
utiliza importância por permutação. O cenário de 80% mantém o contexto de 2024 e não é
previsão validada de 2030 nem probabilidade de descumprimento de meta.

## Arquivos para submissão

- `Relatorio-Tecnico-Fase3-v1.0.pdf`: relatório técnico; Word disponível para edição.
- `Apresentacao-Executiva-Fase3-v1.0.pptx`: oito slides, com roteiro nas notas.
- `Video-Executivo-Fase3-v1.0.mp4`: apresentação executiva com narração sintética em português.
- `Roteiro-Video-Fase3-v1.0.pdf`: texto para apresentação ou regravação com a voz do autor.
- Pacote completo privado: código, entradas auditadas, Gold, modelos e entregáveis.
  Dados individuais e modelos serializados não integram o repositório público.

O repositório e a versão publicada fornecem os links de acesso aos avaliadores. A submissão
no portal da FIAP precisa ser realizada pelo autor até o prazo da turma. Os documentos de
planejamento anteriores são históricos; utilizar a pasta `Entrega-Final` para a submissão.
