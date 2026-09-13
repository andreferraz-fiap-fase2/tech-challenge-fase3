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
    "A alfabetização é um desafio educacional e de planejamento. Este projeto de André Mohallem Ferraz transforma a engenharia de dados construída na Fase dois em uma análise de risco contextual. O objetivo é estimar a probabilidade de um aluno avaliado ser alfabetizado e apoiar a leitura dos territórios. O resultado é um instrumento exploratório: ele não substitui o diagnóstico pedagógico nem demonstra as causas das dificuldades de aprendizagem.",
    "A análise utiliza três milhões e trezentas e cinquenta mil avaliações reais elegíveis, distribuídas entre dois mil e vinte e três e dois mil e vinte e quatro. Foram retirados eventos simulados, ausências e avaliações inválidas. As fontes da fase anterior foram auditadas e enriquecidas com população e economia municipais do IBGE. São seis atributos: rede, estado, população, PIB por habitante e duas participações econômicas. A nota da própria prova ficou fora dos preditores, pois ela determina o resultado que queremos prever.",
    "A comparação respeitou uma separação por município. O treinamento e a escolha do modelo usaram somente dois mil e vinte e três, com três divisões fixas. Comparamos uma referência constante, regressão logística e Gradient Boosting. Uma busca limitada escolheu a configuração com melhor ordenação do risco. O modelo e o limiar foram congelados antes de abrir o teste de dois mil e vinte e quatro. Isso permite avaliar a generalização sem adaptar as decisões ao resultado final.",
    "No teste temporal, a average precision foi de zero vírgula cinco um seis, acima de zero vírgula quatro zero dois da referência constante. Essa métrica avalia a ordenação do risco e não deve ser confundida com acurácia. A capacidade de discriminação é moderada. Nos municípios novos, a performance caiu. Quase todos os alunos desse grupo estão no Acre, Distrito Federal e São Paulo, estados ausentes do desenvolvimento. Isso evidencia o risco de extrapolar o modelo para contextos pouco conhecidos.",
    "O critério acadêmico de escolha do limiar deu prioridade à recuperação dos casos de não alfabetização. No teste, ele identificou mais de noventa e nove por cento desses casos, mas sinalizou quase noventa e sete por cento de todos os alunos. Assim, há pouca seletividade para uma equipe com capacidade limitada. O limiar de referência, zero vírgula cinco, sinaliza menos alunos, porém recupera apenas um quarto dos casos. A conclusão é que o modelo ainda não serve como triagem individual autônoma.",
    "A análise de importância mostrou que o estado é a variável de maior influência preditiva. Os indicadores econômicos municipais agregam informação, mas com contribuição menor. Essa dependência explica por que os primeiros municípios no ranking previsto se concentram em Sergipe. Aracaju e Nossa Senhora do Socorro aparecem no topo do recorte analisado. Isso deve orientar perguntas e verificações locais, e não ser apresentado como ranking oficial ou como evidência de que o território causa o desfecho de uma criança.",
    "Os erros também mudam entre regiões. No Sul, o risco médio foi subestimado em aproximadamente sete pontos percentuais; no Centro-Oeste, foi superestimado em quase seis. Na comparação dos perfis de contexto, Centro-Oeste e Sul ficaram mais próximos, mas isso não significa resultados educacionais iguais. A análise de metas usa taxas previstas e referências municipais da fase anterior. Um cenário de oitenta por cento é apenas uma simulação com a composição de dois mil e vinte e quatro, e não uma previsão para dois mil e trinta.",
    "Para gestores, a recomendação é combinar risco contextual, quantidade de alunos, cobertura dos dados e evidências pedagógicas locais. O projeto oferece uma base auditável para planejar investigações e discutir apoio territorial. Antes de orientar atendimento ou orçamento, é necessário ampliar dados escolares, validar a cobertura e definir custos e capacidade reais. A entrega inclui código versionado, testes, documentação e reprodução do experimento. O valor está em apresentar evidências e limites com clareza para apoiar decisões responsáveis.",
]


class SlideDocuments:
    def __init__(self, output: Path) -> None:
        self.output = output
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
        s = self.slide_base(p, "Onde antecipar apoio à alfabetização?", 1)
        self.textbox(
            s,
            "Risco contextual, evidências territoriais\ne limites para a tomada de decisão",
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
            "Gold da Fase 2 + contexto histórico do IBGE · seis atributos\nEventos simulados e avaliações inválidas excluídos",
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
        s = self.slide_base(p, "A média nacional esconde erros territoriais", 7)
        self.cards(
            s,
            [
                ("Sul", "Risco subestimado em 6,98 pontos percentuais"),
                ("Centro-Oeste", "Risco superestimado em 5,81 pontos percentuais"),
                ("Metas", "Cenários condicionais; sem previsão validada de 2030"),
            ],
        )
        self.textbox(
            s,
            "Validar localmente antes de definir prioridades.\nO ranking previsto é contextual e não substitui indicadores oficiais.",
            0.65,
            5.5,
            12,
            1,
            21,
            GRAY,
        )
        s = self.slide_base(p, "Transformar a análise em perguntas e ações verificáveis", 8)
        self.cards(
            s,
            [
                ("Planejar", "Combinar risco, volume, cobertura e evidência local"),
                ("Validar", "Conferir capacidade, custos e qualidade pedagógica"),
                ("Evoluir", "Ampliar ciclos, dados escolares e monitoramento"),
            ],
        )
        self.textbox(
            s,
            "Código, documentação e reprodução disponíveis no repositório público.\nAutoria: "
            + AUTHOR,
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
        p.save(self.output / "Apresentacao-Executiva-Fase3-v1.0.pptx")
        script = (
            "# Roteiro do vídeo executivo — Fase 3\n\n**Autor: "
            + AUTHOR
            + " · Duração alvo: até 5 minutos**\n\n"
        )
        for i, narration in enumerate(NARRATIONS, 1):
            script += f"## Slide {i}\n\n{narration}\n\n"
        script += "## Orientação de apresentação\n\nApresentar como reunião executiva. Explicar AP sem confundir com acurácia; enfatizar a baixa seletividade e os limites de generalização. A versão base usa narração sintética em português; os slides e o roteiro permitem regravar a apresentação com a voz do autor.\n"
        (ROOT / "docs/Roteiro-Video-Fase3.md").write_text(script)
        (self.output / "Roteiro-Video-Fase3-v1.0.md").write_text(script)
        WordDocuments(self.output).word(script, "Roteiro-Video-Fase3-v1.0.docx")
        (self.output / "narracao.json").write_text(
            json.dumps(
                [{"slide": i, "text": t} for i, t in enumerate(NARRATIONS, 1)],
                ensure_ascii=False,
                indent=2,
            )
        )
