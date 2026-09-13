"""Autor: André Mohallem Ferraz. Documentos Word da entrega."""

import re
from datetime import datetime, timezone
from pathlib import Path

from docx import Document
from docx.opc.constants import RELATIONSHIP_TYPE
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Inches, Pt, RGBColor
from docx.text.paragraph import Paragraph

AUTHOR = "André Mohallem Ferraz"
ROOT = Path(__file__).resolve().parents[1]
NAVY, GOLD, GRAY, WHITE = "183650", "B78C31", "596573", "FFFFFF"


class WordDocuments:
    def __init__(self, output: Path, version: str = "1.0") -> None:
        self.output = output
        if not re.fullmatch(r"\d+\.\d+", version):
            raise ValueError(f"Versão {version!r}; esperado formato numérico N.N")
        self.version = version
        output.mkdir(parents=True, exist_ok=True)

    def inline(self, paragraph: Paragraph, text: str) -> None:
        pattern = r"(\*\*.*?\*\*|`[^`]+`|\[[^\]]+\]\([^)]+\))"
        for part in re.split(pattern, text):
            link = re.fullmatch(r"\[([^\]]+)\]\(([^)]+)\)", part)
            if link:
                url = link[2]
                if not url.startswith("http"):
                    url = (
                        "https://github.com/andreferraz-fiap-fase2/tech-challenge-fase3/blob/main/"
                        + url
                    )
                node = OxmlElement("w:hyperlink")
                node.set(
                    qn("r:id"),
                    paragraph.part.relate_to(url, RELATIONSHIP_TYPE.HYPERLINK, is_external=True),
                )
                run = OxmlElement("w:r")
                properties = OxmlElement("w:rPr")
                color = OxmlElement("w:color")
                color.set(qn("w:val"), NAVY)
                properties.append(color)
                run.append(properties)
                t = OxmlElement("w:t")
                t.text = link[1]
                run.append(t)
                node.append(run)
                paragraph._p.append(node)
            else:
                run = paragraph.add_run(
                    part[2:-2]
                    if part.startswith("**")
                    else part[1:-1]
                    if part.startswith("`")
                    else part
                )
                run.bold = part.startswith("**")
                if part.startswith("`"):
                    run.font.name = "Consolas"
                    run.font.size = Pt(9)

    def word(self, markdown: str, filename: str) -> None:
        document = Document()
        section = document.sections[0]
        section.top_margin = Inches(0.7)
        section.bottom_margin = Inches(0.65)
        section.left_margin = Inches(0.7)
        section.right_margin = Inches(0.7)
        normal = document.styles["Normal"]
        normal.font.name = "Calibri"
        normal.font.size = Pt(10.5)
        normal.paragraph_format.space_after = Pt(4)
        normal.paragraph_format.line_spacing = 1.04
        for name in ("Title", "Heading 1", "Heading 2"):
            document.styles[name].font.color.rgb = RGBColor.from_string(NAVY)
        document.styles["Title"].font.size = Pt(25)
        document.styles["Heading 1"].font.size = Pt(15)
        header = section.header.paragraphs[0]
        header.text = "FIAP  /  TECH CHALLENGE FASE 3"
        header.runs[0].font.size = Pt(8)
        header.runs[0].font.color.rgb = RGBColor.from_string(GOLD)
        footer = section.footer.paragraphs[0]
        footer.alignment = 2
        footer.add_run(AUTHOR + f" · v{self.version} · 13/09/2026  |  ").font.size = Pt(8)
        field = OxmlElement("w:fldSimple")
        field.set(qn("w:instr"), "PAGE")
        footer._p.append(field)
        lines = markdown.splitlines()
        i = 0
        pending_page_break = False
        while i < len(lines):
            line = lines[i].strip()
            i += 1
            if not line:
                continue
            if line == "<!-- pagebreak -->":
                pending_page_break = True
                continue
            image = re.fullmatch(r"!\[.*?\]\((.*?)\)", line)
            if image:
                document.add_picture(str(ROOT / image[1]), width=Inches(6.65))
                continue
            if line.startswith("|"):
                rows = [line]
                while i < len(lines) and lines[i].strip().startswith("|"):
                    rows.append(lines[i].strip())
                    i += 1
                parsed = [[c.strip() for c in row.strip("|").split("|")] for row in rows]
                parsed = [row for row in parsed if not all(re.fullmatch(r":?-+:?", c) for c in row)]
                table = document.add_table(rows=0, cols=len(parsed[0]))
                table.style = "Table Grid"
                for index, row in enumerate(parsed):
                    cells = table.add_row().cells
                    for cell, text in zip(cells, row):
                        self.inline(cell.paragraphs[0], text)
                        for run in cell.paragraphs[0].runs:
                            run.font.size = Pt(9)
                        if index == 0:
                            for run in cell.paragraphs[0].runs:
                                run.bold = True
                                run.font.color.rgb = RGBColor.from_string(WHITE)
                            shade = OxmlElement("w:shd")
                            shade.set(qn("w:fill"), NAVY)
                            cell._tc.get_or_add_tcPr().append(shade)
                    table.rows[index]._tr.get_or_add_trPr().append(OxmlElement("w:cantSplit"))
                continue
            if line.startswith("### "):
                paragraph = document.add_paragraph(style="Heading 2")
                text = line[4:]
            elif line.startswith("# "):
                paragraph = document.add_paragraph(style="Title")
                text = line[2:]
            elif line.startswith("## "):
                paragraph = document.add_paragraph(style="Heading 1")
                text = line[3:]
            elif line.startswith("- "):
                paragraph = document.add_paragraph(style="List Bullet")
                text = line[2:]
            else:
                paragraph = document.add_paragraph()
                text = line
            if pending_page_break:
                paragraph.paragraph_format.page_break_before = True
                pending_page_break = False
            self.inline(paragraph, text)
        document.core_properties.author = AUTHOR
        document.core_properties.last_modified_by = AUTHOR
        document.core_properties.title = markdown.splitlines()[0].lstrip("# ")
        document.core_properties.created = datetime(2026, 9, 13, tzinfo=timezone.utc)
        document.core_properties.modified = datetime(2026, 9, 13, tzinfo=timezone.utc)
        document.save(self.output / filename)

    def report(self) -> None:
        readme = (ROOT / "README.md").read_text()
        pieces = re.split(r"(?=^## )", readme, flags=re.M)
        sections = {piece.splitlines()[0]: piece for piece in pieces[1:]}
        title = (
            "# Relatório técnico — alfabetização no Brasil\n\n**Autor: "
            + AUTHOR
            + f"**\n\n**FIAP · Tech Challenge Fase 3 · Trabalho individual · Revisão documental {self.version} · 13/09/2026**\n\n"
        )
        abstract = "**Síntese executiva.** O Gradient Boosting supera o baseline no teste temporal, com AP 0,5162 e ROC-AUC 0,6224. Seu limiar acadêmico de F2 sinaliza 96,84% dos alunos. A entrega evidencia potencial para leitura territorial e limites importantes de generalização e seletividade, sem recomendar decisões individuais autônomas.\n\n"
        groups = [
            ["## 1. Contexto do problema", "## 2. Objetivo analítico"],
            ["## 3. Base utilizada"],
            ["## 4. Etapas de modelagem"],
            ["## 5. Escolha do algoritmo"],
            ["## 6. Métricas de avaliação"],
            ["## 7. Interpretação dos resultados"],
            ["## 8. Insights encontrados"],
            ["## 9. Limitações", "## 10. Aplicação prática para políticas públicas"],
            ["## 11. Possíveis evoluções futuras", "## Como reproduzir"],
            ["## Referências"],
        ]
        pages = []
        extras = {
            3: "\n![Escolha do limiar](images/09_limiar_f2_2023.png)\n",
            6: "\n![Erros por região](images/12_regioes_teste_2024.png)\n",
            9: "\n## Apêndice — perfis regionais\n\n![Perfis regionais](images/14_perfis_regionais_2023.png)\n",
        }
        for index, group in enumerate(groups):
            page = "\n".join(sections[name] for name in group)
            if index == 2:
                page = page.replace("### 4.2.", "<!-- pagebreak -->\n\n### 4.2.")
            if index == 8:
                page = re.sub(r"```.*?```", "", page, flags=re.S)
            pages.append(page + extras.get(index, ""))
        pages.append(
            "## Apêndice — distribuições do contexto\n\nUma observação por município no desenvolvimento de 2023. A escala log10 desta figura é apenas visual; o modelo logístico utiliza log1p.\n\n![Distribuições do contexto](images/03_contexto_municipal_2023.png)\n"
        )
        markdown = title + abstract + "\n<!-- pagebreak -->\n".join(pages)
        (ROOT / "docs/Relatorio-Tecnico-Fase3.md").write_text(
            re.sub(r"\]\((?!https?://)([^)]+)\)", lambda match: "](../" + match[1] + ")", markdown)
        )
        filename = f"Relatorio-Tecnico-Fase3-v{self.version}"
        self.word(markdown, filename + ".docx")
        (self.output / (filename + ".md")).write_text(markdown)
