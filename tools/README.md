# Preparação dos documentos

**Autor: André Mohallem Ferraz**

Essas ferramentas editoriais usam ambiente separado da modelagem. As dependências estão
em `requirements-entrega.txt`. A exportação utiliza Word e PowerPoint instalados no Windows.
Estas ferramentas geram editáveis, roteiros, renderizações e recibos em `Preparacao`.
A saída em `Entrega-Final` é bloqueada para impedir a mistura com materiais oficiais.
O ZIP oficial contém somente a visão técnica em PDF e a apresentação em PowerPoint,
sem notas de narração. O vídeo oficial de até cinco minutos depende de gravação pelo autor.

Para gerar somente o relatório, acrescentar `--report-only`. A visão técnica inclui uma seção
própria à análise exploratória com IBGE e Inep, com gráficos, hipóteses e limites.
O roteiro distribui os dez slides em janelas que somam 5 minutos; a duração é planejada
para ensaio, sem gravação nesta revisão. Roteiros, áudios, vídeos de ensaio e versões
anteriores permanecem na preparação privada, fora do ZIP e da pasta oficial.
Gerar em uma nova pasta de preparação para preservar os materiais anteriores.
Os slides 6–8 explicitam as cinco perguntas estratégicas do enunciado, distinguindo
associações, importância preditiva e cenários de metas. O PDF identifica o repositório
na primeira página; o PowerPoint contém links clicáveis no rodapé e no encerramento.

```bash
uv run --no-project --python 3.13 --isolated --with python-docx==1.2.0 --with python-pptx==1.0.2 python tools/gerar_documentos.py --report-version 1.5 --output /caminho/Preparacao/documentos-1.5
```

No PowerShell do Windows, executar `powershell.exe -NoProfile -ExecutionPolicy Bypass -File tools/exportar-documentos.ps1 -Version 1.5 -Output <pasta de preparacao>`.
O script exporta PDFs e os dez slides em PNG. Depois, conferir a autoria dos PDFs:

```bash
uv run --no-project --python 3.13 --isolated --with pymupdf==1.28.2 --with imageio-ffmpeg==0.6.0 python tools/finalizar_midia.py --version 1.5 --output /caminho/Preparacao/documentos-1.5
```

A finalização registra a autoria e as páginas em `verificacao-documentos.json`.
Os dois comandos acima não sintetizam áudio nem codificam vídeo.

Uma nova gravação exige solicitação específica: `-GenerateAudio` na exportação e
`--generate-video` na finalização. Esse caminho utiliza a voz genérica Microsoft Maria
Desktop (pt-BR), mede os áudios e recusa vídeo acima de cinco minutos. Os parâmetros
ficam desativados. Eventual mídia sintética serve somente a ensaio privado; não substitui
o vídeo oficial com a voz do autor nem deve ser publicada como entregável.
