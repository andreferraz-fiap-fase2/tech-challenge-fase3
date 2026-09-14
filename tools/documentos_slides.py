"""Autor: André Mohallem Ferraz. Slides e roteiro executivo."""

import json
from pathlib import Path

from documentos_word import AUTHOR, GOLD, GRAY, NAVY, ROOT, WordDocuments
from pptx import Presentation
from pptx.dml.color import RGBColor as PColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.presentation import Presentation as PresentationType
from pptx.slide import Slide
from pptx.util import Inches as PInches
from pptx.util import Pt as PPt

NARRATIONS = [
    "Este projeto de André Mohallem Ferraz estima a probabilidade de um aluno do segundo ano ser considerado alfabetizado, dado seu contexto. O resultado observado segue o critério de setecentos e quarenta e três pontos de proficiência. O modelo produz uma probabilidade; um limiar transforma essa estimativa em classificação. A previsão contextual apoia a análise territorial, sem substituir a avaliação pedagógica individual.",
    "A base reúne três milhões e trezentas e cinquenta mil avaliações reais elegíveis em dois ciclos. A Gold por aluno foi reconstruída da Silver e dos originais da Fase dois, com auditoria e enriquecimento do IBGE. A nota define o alvo e fica fora dos preditores. O estudo educacional acrescenta três indicadores do Inep aos seis atributos originais. São mais informações sobre os mesmos alunos de dois mil e vinte e três, sem aumentar a amostra nem incorporar o teste à exploração.",
    "A exploração encontrou quarenta e um vírgula sessenta e um por cento de não alfabetização, com diferenças entre regiões. População e PIB têm distribuições assimétricas, justificando transformação logarítmica na regressão logística. Apenas cinco mil oitocentos e oitenta e um perfis originais representam um milhão e meio de avaliações. Por isso, os municípios foram mantidos inteiros nas três divisões de validação. Medianas e transformações são aprendidas somente no treino. O relatório relaciona achados, hipóteses e decisões e distingue a exploração inicial das análises complementares realizadas posteriormente.",
    "Comparamos uma referência constante, regressão logística e Gradient Boosting. Modelo e limiar foram congelados antes do teste temporal de dois mil e vinte e quatro. A average precision do modelo foi zero vírgula cinco um seis, acima de zero vírgula quatro zero dois do baseline. Essa métrica mede ordenação do risco, não acurácia. O desempenho caiu em municípios novos, mostrando limites de generalização para contextos pouco conhecidos.",
    "O limiar escolhido pela métrica F dois prioriza recuperar casos de não alfabetização. No teste, identificou mais de noventa e nove por cento desses casos, mas sinalizou quase noventa e sete por cento dos alunos. Isso oferece pouca seletividade para uma equipe com capacidade limitada. A referência de cinquenta por cento sinaliza menos alunos, mas recupera apenas um quarto dos casos. O modelo ainda não sustenta uma triagem individual autônoma.",
    "A exploração educacional usa uma observação por município e rede. As medianas são dezenove vírgula cinco alunos por turma, noventa e quatro vírgula quatro por cento das funções docentes com curso superior e quatro vírgula três horas diárias de aula. A cobertura supera noventa e nove vírgula noventa e oito por cento dos alunos. As associações com alfabetização são modestas, e a de horas de aula é próxima de zero. Essas correlações contextuais não medem efeitos causais.",
    "A hipótese complementar é que esses indicadores acrescentem informação ao contexto do IBGE. A comparação manteve os mesmos alunos, divisões municipais e parâmetros do modelo. A exploração do Inep foi registrada antes desses ajustes. O ganho de average precision foi pequeno: melhorou em duas divisões e piorou em uma. O estudo reutiliza desenvolvimento conhecido, sem novo teste independente. Por isso, a expansão com nove atributos não substitui o modelo de referência com seis.",
    "A demonstração recebe perfis históricos de município e rede. Para Belo Horizonte municipal, estima cinquenta e oito vírgula sessenta e seis por cento de probabilidade de alfabetização. A regra de cinquenta por cento classifica como alfabetizado; a política sensível de F dois sinaliza atenção. A probabilidade é a mesma, mas as decisões refletem objetivos diferentes. Para gestores, a recomendação é combinar contexto, volume, cobertura e evidência pedagógica local. Os dados não sustentam uma previsão individual para dois mil e vinte e seis.",
]

SCRIPT_WINDOWS = [
    "00:00–00:30",
    "00:30–01:10",
    "01:10–01:55",
    "01:55–02:30",
    "02:30–03:05",
    "03:05–03:40",
    "03:40–04:20",
    "04:20–05:00",
]


class SlideDocuments:
    def __init__(self, output: Path, version: str = "1.0") -> None:
        self.output = output
        self.version = WordDocuments(output, version).version
        output.mkdir(parents=True, exist_ok=True)

    def textbox(
        self,
        slide: Slide,
        text: str,
        x: float,
        y: float,
        w: float,
        h: float,
        size: int = 24,
        color: str = NAVY,
        bold: bool = False,
    ) -> None:
        shape = slide.shapes.add_textbox(PInches(x), PInches(y), PInches(w), PInches(h))
        tf = shape.text_frame
        tf.word_wrap = True
        for index, line in enumerate(text.split("\n")):
            p = tf.paragraphs[0] if index == 0 else tf.add_paragraph()
            p.text = line
            p.font.name = "Aptos"
            p.font.size = PPt(size)
            p.font.bold = bold
            p.font.color.rgb = PColor.from_string(color)
            p.space_after = PPt(8)

    def slide_base(self, presentation: PresentationType, title: str, number: int) -> Slide:
        slide = presentation.slides.add_slide(presentation.slide_layouts[6])
        bar = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, PInches(13.333), PInches(0.16))
        bar.fill.solid()
        bar.fill.fore_color.rgb = PColor.from_string(GOLD)
        bar.line.fill.background()
        self.textbox(
            slide,
            "FIAP  /  INTELIGÊNCIA ANALÍTICA PARA ALFABETIZAÇÃO",
            0.55,
            0.3,
            12,
            0.3,
            11,
            GOLD,
            True,
        )
        self.textbox(slide, title, 0.55, 0.9, 12.2, 1.15, 31, NAVY, True)
        self.textbox(
            slide, AUTHOR + "  ·  Fase 3  ·  Setembro de 2026", 0.55, 7.05, 11, 0.3, 10, GRAY
        )
        self.textbox(slide, f"{number:02d}", 12.1, 7.03, 0.6, 0.3, 11, GOLD, True)
        slide.notes_slide.notes_text_frame.text = NARRATIONS[number - 1]
        return slide

    def cards(self, slide: Slide, items: list[tuple[str, str]], y: float = 2.35) -> None:
        width = 11.8 / len(items)
        for index, (headline, body) in enumerate(items):
            x = 0.6 + index * width
            box = slide.shapes.add_shape(
                MSO_SHAPE.ROUNDED_RECTANGLE,
                PInches(x),
                PInches(y),
                PInches(width - 0.15),
                PInches(2.6),
            )
            box.fill.solid()
            box.fill.fore_color.rgb = PColor.from_string("F1F4F6")
            box.line.fill.background()
            self.textbox(slide, headline, x + 0.22, y + 0.3, width - 0.6, 0.85, 32, NAVY, True)
            self.textbox(slide, body, x + 0.22, y + 1.2, width - 0.6, 1.15, 20, GRAY)

    def presentation(self) -> None:
        p = Presentation()
        p.slide_width = PInches(13.333)
        p.slide_height = PInches(7.5)
        s = self.slide_base(p, "Qual é a probabilidade de alfabetização?", 1)
        self.textbox(
            s,
            "Critério observado: proficiência ≥743 pontos\nEstimativa condicionada ao contexto do aluno",
            0.65,
            2.5,
            11.8,
            1.8,
            34,
            NAVY,
        )
        self.textbox(
            s, "Uma evolução da engenharia de dados da Fase 2", 0.65, 5.3, 11.8, 0.7, 22, GOLD
        )
        s = self.slide_base(p, "Uma base auditada, com teste temporal separado", 2)
        self.cards(
            s,
            [
                ("3,35 milhões", "avaliações reais elegíveis nos dois ciclos"),
                ("2023", "1,50 milhão para desenvolvimento"),
                ("2024", "1,85 milhão para teste final"),
            ],
        )
        self.textbox(
            s,
            "Gold por aluno reconstruída das fontes da Fase 2 + IBGE · seis atributos\nGold municipal original utilizada na análise posterior de metas",
            0.65,
            5.5,
            12,
            1,
            21,
            GRAY,
        )
        s = self.slide_base(p, "A exploração orienta o tratamento e a validação", 3)
        self.cards(
            s,
            [
                ("41,61%", "Não alfabetizados; classe de risco com volume expressivo"),
                ("5.881 perfis", "Contextos repetidos: separar municípios inteiros"),
                ("População/PIB", "Assimetria: log1p na regressão logística"),
            ],
        )
        self.textbox(
            s,
            "EDA de 2023 · imputação e transformações aprendidas no treino\nModelo e limiar congelados antes de avaliar 2024.",
            0.65,
            5.6,
            12,
            0.9,
            21,
            GRAY,
        )
        s = self.slide_base(p, "Há ganho preditivo, com generalização moderada", 4)
        self.cards(
            s,
            [
                ("0,516", "AP do modelo no teste de 2024"),
                ("0,402", "AP da referência constante"),
                ("0,456", "AP em municípios novos"),
            ],
        )
        self.textbox(
            s,
            "AP mede ordenação do risco; não é acurácia.\nNovas UFs concentram quase todos os alunos de municípios novos.",
            0.65,
            5.5,
            12,
            1,
            21,
            GRAY,
        )
        s = self.slide_base(p, "O limiar F2 tem pouca seletividade", 5)
        self.cards(
            s,
            [
                ("99,30%", "dos casos de não alfabetização recuperados"),
                ("96,84%", "de todos os alunos sinalizados"),
                ("41,24%", "de precisão entre os sinalizados"),
            ],
        )
        self.textbox(
            s,
            "Conclusão: não usar como triagem individual autônoma\ncom capacidade de atendimento limitada.",
            0.65,
            5.5,
            12,
            1,
            23,
            NAVY,
            True,
        )
        s = self.slide_base(p, "Como se distribui o contexto educacional?", 6)
        distribution = s.shapes.add_picture(
            str(ROOT / "images/16_eda_inep_2023.png"),
            PInches(0.65),
            PInches(2.15),
            width=PInches(12.0),
        )
        distribution.left = int((p.slide_width - distribution.width) / 2)
        s = self.slide_base(p, "Inep: mais contexto educacional, ganho pequeno", 7)
        self.cards(
            s,
            [
                ("3 indicadores", "Turmas, funções docentes com nível superior e horas de aula"),
                (">99,98%", "Cobertura dos alunos no desenvolvimento de 2023"),
                ("+0,000531", "Ganho médio de AP; melhora em dois dos três folds"),
            ],
        )
        self.textbox(
            s,
            "Estudo exploratório: seis versus nove atributos nos mesmos folds de 2023.\nSem novo teste independente; o modelo de referência permanece 1.0.",
            0.65,
            5.5,
            12,
            1,
            21,
            GRAY,
        )
        s = self.slide_base(p, "Demonstrar a probabilidade e interpretar a decisão", 8)
        self.cards(
            s,
            [
                ("58,66%", "P(alfabetizado) no perfil histórico Belo Horizonte / Municipal"),
                ("Probabilidade", "Mesma estimativa; classificação depende do limiar adotado"),
                ("Aplicação", "Combinar contexto, volume e evidência pedagógica local"),
            ],
        )
        self.textbox(
            s,
            "Demonstração contextual do modelo 1.0; não é previsão para 2026.\nAutoria: " + AUTHOR,
            0.65,
            5.45,
            12,
            1,
            20,
            NAVY,
        )
        p.core_properties.author = AUTHOR
        p.core_properties.last_modified_by = AUTHOR
        p.core_properties.title = "Alfabetização: inteligência analítica para decisões territoriais"
        p.save(self.output / f"Apresentacao-Executiva-Fase3-v{self.version}.pptx")
        script = (
            "# Roteiro de preparação do vídeo executivo — Fase 3\n\n**Autor: "
            + AUTHOR
            + f" · Revisão {self.version} · Duração planejada: 5 minutos**\n\n"
            + "As janelas abaixo somam 5 minutos e incluem pausas e transições. "
            + "São uma estimativa para ensaio, não uma duração de gravação medida. "
            + "Material de apoio, fora do ZIP e da pasta oficial de entrega. "
            + "O vídeo oficial deverá ser gravado com a voz do autor.\n\n"
        )
        for i, narration in enumerate(NARRATIONS, 1):
            script += f"## {SCRIPT_WINDOWS[i - 1]} — Slide {i}\n\n{narration}\n\n"
        script += "## Orientação de apresentação\n\nApresentar como reunião executiva. Ensaiar dentro das janelas de tempo e ajustar as pausas para concluir em até 5 minutos. Explicar AP sem confundir com acurácia e correlação sem atribuir causalidade. Enfatizar a baixa seletividade e os limites de generalização. Gravar com a voz do autor. Narração sintética e versões de ensaio são materiais privados de preparação e não integram a entrega oficial.\n"
        (ROOT / "docs/Roteiro-Video-Fase3.md").write_text(script)
        (self.output / f"Roteiro-Video-Fase3-v{self.version}.md").write_text(script)
        WordDocuments(self.output, self.version).word(
            script, f"Roteiro-Video-Fase3-v{self.version}.docx"
        )
        (self.output / "narracao.json").write_text(
            json.dumps(
                [{"slide": i, "text": t} for i, t in enumerate(NARRATIONS, 1)],
                ensure_ascii=False,
                indent=2,
            )
        )
