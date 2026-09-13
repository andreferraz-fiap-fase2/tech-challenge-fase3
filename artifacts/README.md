Artefatos por aluno e modelos ficam fora do Git. Métricas e figuras agregadas ficam
em `reports/` e `images/`. A cópia privada contém:

- `logistica/` e `boosting/`: seis pipelines por família, duas variantes × três folds.
- `modelo_final.joblib`: boosting completo ajustado em todo 2023, com pré-processamento integrado.
- `logistica_oof_2023.parquet` e `boosting_oof_2023.parquet`: previsões de validação.
- `boosting_amostra_2023.parquet`: chaves da amostra fixa para busca e interpretação.
- `previsoes_teste_2024.parquet`: probabilidades e decisões do teste temporal reservado.

Os hashes do modelo final e das previsões estão em `reports/ajuste_final.json`,
`reports/teste_temporal_2024.json` e `reports/reproducibilidade_final.json`.
Usar `uv run python -m src.usecase.reproduce_final` para conferir a reprodução sem
sobrescrever o experimento. Carregar somente os arquivos da própria entrega verificada.
