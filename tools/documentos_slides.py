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
    "Este projeto de André Mohallem Ferraz responde a uma pergunta: qual é a probabilidade estimada de um aluno do segundo ano ser considerado alfabetizado, dado seu contexto? O resultado observado segue o critério de setecentos e quarenta e três pontos de proficiência. O modelo estima uma probabilidade; uma regra de decisão produz a classificação. Essa diferença é importante: mudar o limiar de probabilidade não muda o padrão de alfabetização. A previsão é contextual, sem substituir uma avaliação pedagógica individual.",
    "A análise utiliza três milhões e trezentas e cinquenta mil avaliações reais elegíveis em dois ciclos. Eventos simulados, ausências e avaliações inválidas foram excluídos. A Gold anterior era municipal. Por isso, reconstruímos uma Gold por aluno a partir da Silver e dos originais da Fase dois, com auditoria e enriquecimento do IBGE. O modelo de referência usa seis atributos: rede, estado e quatro indicadores demográficos e econômicos. A nota da prova determina o alvo e fica fora dos preditores.",
    "A comparação respeitou uma separação por município. O treinamento e a escolha do modelo usaram somente dois mil e vinte e três, com três divisões fixas. Comparamos uma referência constante, regressão logística e Gradient Boosting. Uma busca limitada escolheu a configuração com melhor ordenação do risco. O modelo e o limiar foram congelados antes de abrir o teste de dois mil e vinte e quatro. Isso permite avaliar a generalização sem adaptar as decisões ao resultado final.",
    "No teste temporal, a average precision foi de zero vírgula cinco um seis, acima de zero vírgula quatro zero dois da referência constante. Essa métrica avalia a ordenação do risco e não deve ser confundida com acurácia. A capacidade de discriminação é moderada. Nos municípios novos, a performance caiu. Quase todos os alunos desse grupo estão no Acre, Distrito Federal e São Paulo, estados ausentes do desenvolvimento. Isso evidencia o risco de extrapolar o modelo para contextos pouco conhecidos.",
    "O critério acadêmico de escolha do limiar deu prioridade à recuperação dos casos de não alfabetização. No teste, ele identificou mais de noventa e nove por cento desses casos, mas sinalizou quase noventa e sete por cento de todos os alunos. Assim, há pouca seletividade para uma equipe com capacidade limitada. O limiar de referência, zero vírgula cinco, sinaliza menos alunos, porém recupera apenas um quarto dos casos. A conclusão é que o modelo ainda não serve como triagem individual autônoma.",
    "A importância por permutação mostra maior dependência do estado. Isso é contribuição preditiva, sem demonstrar causalidade. Os erros variam entre regiões: no Sul, o risco foi subestimado em cerca de sete pontos percentuais; no Centro-Oeste, superestimado em quase seis. As metas municipais da Gold anterior entram somente na análise posterior. O cenário de oitenta por cento mantém o contexto de dois mil e vinte e quatro e não constitui previsão validada para dois mil e trinta.",
    "Para investigar a dimensão educacional, acrescentamos três indicadores históricos do Inep: tamanho das turmas, funções docentes com curso superior e horas de aula. A cobertura supera noventa e nove vírgula noventa e oito por cento. A comparação exploratória usa os mesmos três grupos municipais de dois mil e vinte e três e passa de seis para nove atributos. O ganho de average precision foi pequeno: melhorou em dois grupos e piorou em um. Esse estudo não tem novo teste independente e não substitui o modelo de referência.",
    "A entrega também demonstra a previsão em perfis históricos de município e rede. Para Belo Horizonte, rede municipal, o modelo estima cinquenta e oito vírgula sessenta e seis por cento de probabilidade de alfabetização. A regra de cinquenta por cento classifica como alfabetizado, enquanto a política sensível de F dois sinaliza atenção. As probabilidades são iguais; as decisões refletem objetivos diferentes. Para gestores, a recomendação é combinar contexto, volume, cobertura e evidência pedagógica local. Código, fontes, testes e reprodução acompanham os materiais da entrega.",
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
        s = self.slide_base(p, "Escolher antes de observar o futuro", 3)
        self.cards(
            s,
            [
                ("Comparar", "Baseline, logística e Gradient Boosting"),
                ("Congelar", "Municípios separados; modelo e limiar definidos em 2023"),
                ("Avaliar", "2024 reservado para o teste temporal"),
            ],
        )
        self.textbox(
            s,
            "Proficiência, resultados contemporâneos e identificadores ficam fora dos preditores.",
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
        s = self.slide_base(p, "O limiar acadêmico tem pouca seletividade", 5)
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
        s = self.slide_base(p, "UF concentra a influência preditiva", 6)
        importance = s.shapes.add_picture(
            str(ROOT / "images/10_importancia_permutacao_2023.png"),
            PInches(1.1),
            PInches(2),
            height=PInches(4.75),
        )
        importance.left = int((p.slide_width - importance.width) / 2)
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
            "# Roteiro do vídeo executivo — Fase 3\n\n**Autor: "
            + AUTHOR
            + " · Duração alvo: até 5 minutos**\n\n"
        )
        for i, narration in enumerate(NARRATIONS, 1):
            script += f"## Slide {i}\n\n{narration}\n\n"
        script += "## Orientação de apresentação\n\nApresentar como reunião executiva. Explicar AP sem confundir com acurácia; enfatizar a baixa seletividade e os limites de generalização. A versão base usa narração sintética em português; os slides e o roteiro permitem regravar a apresentação com a voz do autor.\n"
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
