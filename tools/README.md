# Geração dos documentos e vídeo

**Autor: André Mohallem Ferraz**

Essas ferramentas editoriais usam ambiente separado da modelagem. As dependências estão
em `requirements-entrega.txt`. A exportação utiliza Word e PowerPoint instalados no Windows;
a narração usa a voz genérica Microsoft Maria Desktop (pt-BR), sem imitar a voz do autor.

```bash
uv run --no-project --python 3.13 --isolated --with python-docx==1.2.0 --with python-pptx==1.0.2 python tools/gerar_documentos.py --output /caminho/Entrega-Final
```

No PowerShell do Windows, executar `powershell.exe -NoProfile -ExecutionPolicy Bypass -File tools/exportar-documentos.ps1 -Output <pasta da entrega>`.
O script exporta PDFs, os oito slides em PNG e a narração em WAV. Depois:

```bash
uv run --no-project --python 3.13 --isolated --with pymupdf==1.28.2 --with imageio-ffmpeg==0.6.0 python tools/finalizar_midia.py --output /caminho/Entrega-Final
```

A finalização preenche autoria nos PDFs, mede os áudios, recusa duração acima de cinco
minutos e gera MP4 H.264/AAC. `verificacao-midia.json` registra duração e arquivos gerados.
