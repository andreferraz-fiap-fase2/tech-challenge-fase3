# Enriquecimento educacional com o Inep

**Autor:** André Mohallem Ferraz. **Consulta das fontes:** 13/09/2026.

O estudo complementar acrescenta três indicadores do Censo da Educação Básica de
2021 ao contexto municipal do IBGE. A hipótese é que as condições da oferta de
ensino tragam informação preditiva adicional à rede, à UF e ao contexto econômico.
O estudo utiliza exclusivamente o desenvolvimento de 2023 e mantém o experimento
final 1.0 preservado, conforme o [protocolo próprio](Protocolo-Estudo-Educacional.md).

## Fontes e interpretação

| Fonte oficial — edição 2021 | Variável incorporada | Interpretação e limite |
|---|---|---|
| [Média de Alunos por Turma — ATU](https://www.gov.br/inep/pt-br/acesso-a-informacao/dados-abertos/indicadores-educacionais/media-de-alunos-por-turma/2021) | `alunos_por_turma_ai_2021` | Média de alunos por turma nos anos iniciais; caracteriza a oferta agregada da rede no município, sem identificar a turma do aluno. |
| [Percentual de Docentes com Curso Superior — DSU](https://www.gov.br/inep/pt-br/acesso-a-informacao/dados-abertos/indicadores-educacionais/percentual-de-docentes-com-curso-superior/2021) | `docentes_superior_ai_2021` | A planilha de 2021 usa o termo **funções docentes**. O indicador mede formação superior, em percentual de 0 a 100; não mede qualidade pedagógica nem comprova formação adequada à disciplina. |
| [Média de Horas-Aula Diária — HAD](https://www.gov.br/inep/pt-br/acesso-a-informacao/dados-abertos/indicadores-educacionais/media-de-horas-aula-diaria/2021) | `horas_aula_ai_2021` | Jornada média declarada nos anos iniciais. Não equivale a presença efetiva ou horas de ensino recebidas por cada aluno, especialmente no contexto da pandemia de 2021. |

Esses atributos são características educacionais agregadas e históricas. Não
permitem diferenciar dois alunos que compartilhem todos os atributos do modelo,
nem estimar o efeito causal de alterar tamanho de turma, formação ou jornada.

## Temporalidade e integridade

As três páginas específicas da edição 2021 apresentam **“Publicado em
31/01/2022 18h08”**; a página não informa fuso horário. Os servidores retornaram
`Last-Modified` em 18/01/2022, e os três arquivos XLSX internos têm data ZIP nesse
mesmo dia. Os MD5 dos XLSX coincidem com os arquivos de conferência que o próprio
Inep distribui dentro dos ZIPs. Assim, a edição é compatível com a data limite de
disponibilidade **31/12/2022**, anterior ao desenvolvimento de 2023.

Esses metadados são evidências convergentes de edição, mas não substituem um
arquivo histórico independente nem provam criptograficamente quais bytes estavam
disponíveis em 2022. Os arquivos foram consultados em 2026 e fixados por SHA-256;
o carregamento recusa bytes diferentes. Não foram utilizadas edições 2022, 2023
ou posteriores dos indicadores.

| ZIP oficial | Tamanho em bytes | SHA-256 |
|---|---:|---|
| [ATU_2021_MUNICIPIOS.zip](https://download.inep.gov.br/informacoes_estatisticas/indicadores_educacionais/2021/ATU_2021_MUNICIPIOS.zip) | 14.512.691 | `37b74acc403b8dcb932ebfd81e4732a81298e110327be58d537ff56028872296` |
| [DSU_2021_MUNICIPIOS.zip](https://download.inep.gov.br/informacoes_estatisticas/indicadores_educacionais/2021/DSU_2021_MUNICIPIOS.zip) | 9.226.118 | `393830aec52aad754b8e8e2036716ca93757363569971b255673d0a8f6b93bfa` |
| [HAD_2021_MUNICIPIOS.zip](https://download.inep.gov.br/informacoes_estatisticas/indicadores_educacionais/2021/HAD_2021_MUNICIPIOS.zip) | 10.460.519 | `23f7b0dd12ea24fc01e0591a355d726db4d5b6b9cbe8ba2891571eaa3255b2d3` |

O [manifesto versionado](../config/fontes-educacionais.json) registra também URLs,
datas, tamanhos e SHA-256 dos membros XLSX. As páginas HTML e os cabeçalhos HTTP
da consulta estão preservados privadamente em `data/input/inep/evidencias/`.

## Recorte e integração

O parser lê a aba `MUNICIPIO`, localiza os códigos oficiais de coluna e seleciona
`FUN_AI_CAT_0`, correspondente a **Anos Iniciais do Ensino Fundamental**. Mantém
somente localização `Total` e dependência `Estadual` ou `Municipal`. Não calcula
média das linhas Urbana/Rural, não substitui o indicador pelos valores do ensino
fundamental total e não mistura a rede Pública agregada com as duas redes.

O código IBGE municipal é mantido como texto com sete dígitos e conferido contra a
UF. A integração das fontes usa `(id_municipio, rede_nome)` com unicidade
obrigatória; a integração com alunos é de muitos para um. A união entre fontes é
externa, preservando ausências. Não foi feito cruzamento por código de escola,
cuja correspondência entre as bases não está demonstrada.

O marcador `--` e células vazias tornam-se `NaN`. Não são convertidos em zero nem
preenchidos com valores de outra etapa ou rede. Nulos representam informação
indisponível para o recorte, que pode incluir ausência de oferta. A mediana é
ajustada apenas nos dados de treinamento de cada fold do estudo complementar.

Além das chaves e do ano, o parser recusa categorias desconhecidas e valores fora
dos intervalos de validação: ATU maior que zero e até 200, DSU de 0 a 100 e HAD
maior que zero e até 24. Esses limites são controles de dados, sem truncamento
estatístico. Os intervalos observados na edição nacional foram, respectivamente,
1–45 alunos por turma, 0–100% de funções docentes e 3–10,3 horas-aula diárias.

## Cobertura no desenvolvimento de 2023

As fontes nacionais geram **11.131 combinações município/rede**. A Gold de
desenvolvimento contém 1.502.809 alunos, 4.871 municípios e 5.881 combinações
município/rede. O cruzamento preserva todos os alunos e apresenta a cobertura:

| Indicador | Alunos com indicador | Cobertura por aluno | Combinações sem indicador |
|---|---:|---:|---:|
| Alunos por turma | 1.502.596 | 99,9858% | 10 |
| Funções docentes com superior | 1.502.636 | 99,9885% | 9 |
| Horas-aula diária | 1.502.596 | 99,9858% | 10 |

Todos superam o requisito de 95% registrado antes da comparação. Essa cobertura
não significa que o contexto de 2021 descreva integralmente as condições de
ensino de cada aluno em 2023; existe defasagem temporal e agregação territorial.

## Reprodução

Com o ambiente de `uv sync --frozen`, obtenha os arquivos oficiais e valide o
recorte sem ler qualquer resultado individual:

```bash
uv run python -m src.infrastructure.education_sources download
uv run python -m src.infrastructure.education_sources inspect
uv run pytest tests/test_education_sources.py -q
```

O download mantém validação HTTPS, verifica tamanho e SHA-256 antes de gravar e
recusa sobrescrever uma entrada existente divergente. Na consulta, o servidor
do Inep omitia o certificado intermediário RNP ICPEdu GR46 OV TLS CA 2025. A
conexão foi validada acrescentando esse intermediário, fornecido pela autoridade
GlobalSign, à cadeia padrão do sistema; não se desativou a validação TLS. Caso
o servidor mantenha essa configuração, o comando aceita `--ca-file caminho.pem`
para acrescentar o intermediário ao conjunto de certificados confiáveis.

Os testes usam planilhas mínimas geradas em memória e exercitam seleção da etapa
correta, separação de redes, ausências, duplicatas, ano, UF, categorias, limites,
integridade dos ZIPs e bloqueio de fonte publicada após o corte temporal.
