# Geração dos documentos

**Autor: André Mohallem Ferraz**

Essas ferramentas editoriais usam ambiente separado da modelagem. As dependências estão
em `requirements-entrega.txt`. A exportação utiliza Word e PowerPoint instalados no Windows.
Por padrão, a revisão gera documentos e slides, preservando o vídeo narrado existente.

Para gerar somente o relatório, acrescentar `--report-only`. A versão 1.3 dá uma seção
própria à análise exploratória com IBGE e Inep, com gráficos, hipóteses e limites.
O roteiro distribui os oito slides em janelas que somam 5 minutos; a duração é planejada
para ensaio, sem gravação nesta revisão. O vídeo 1.2 permanece na publicação anterior.
Gerar em uma nova pasta para preservar os materiais anteriormente publicados.

```bash
uv run --no-project --python 3.13 --isolated --with python-docx==1.2.0 --with python-pptx==1.0.2 python tools/gerar_documentos.py --report-version 1.3 --output /caminho/Revisao-1.3
```

No PowerShell do Windows, executar `powershell.exe -NoProfile -ExecutionPolicy Bypass -File tools/exportar-documentos.ps1 -Version 1.3 -Output <pasta da entrega>`.
O script exporta PDFs e os oito slides em PNG. Depois, conferir a autoria dos PDFs:

```bash
uv run --no-project --python 3.13 --isolated --with pymupdf==1.28.2 --with imageio-ffmpeg==0.6.0 python tools/finalizar_midia.py --version 1.3 --output /caminho/Revisao-1.3
```

A finalização registra a autoria e as páginas em `verificacao-documentos.json`.
Os dois comandos acima não sintetizam áudio nem codificam vídeo.

Uma nova gravação exige solicitação específica: `-GenerateAudio` na exportação e
`--generate-video` na finalização. Esse caminho utiliza a voz genérica Microsoft Maria
Desktop (pt-BR), mede os áudios e recusa vídeo acima de cinco minutos. Os parâmetros
ficam desativados na revisão documental 1.3 e nos ajustes documentais posteriores.
