# -*- coding: utf-8 -*-
from fpdf import FPDF
import datetime
import os

class PDFRecibo(FPDF):
    def __init__(self, orientation="P", unit="mm", format="A4"):
        super().__init__(orientation, unit, format)
        # Usar fonte padrão Arial
        self.set_font("Arial", size=10)
        # FPDF com fontes padrão geralmente lida melhor com Latin-1.
        # Para UTF-8 completo, seria necessário adicionar uma fonte unicode.
        self.supports_utf8 = False # Assumir fallback para codificação segura

    def _encode_str(self, text):
        if self.supports_utf8:
            return str(text)
        else:
            return str(text).encode("latin-1", "replace").decode("latin-1")

    def header(self):
        if self.supports_utf8:
            self.set_font(self.font_name, "B", 15)
        else:
            self.set_font("Arial", "B", 15)
        self.cell(0, 10, self._encode_str("Recibo de Venda"), new_x="LMARGIN", new_y="NEXT", align="C")
        self.ln(10)

    def footer(self):
        self.set_y(-15)
        if self.supports_utf8:
            self.set_font(self.font_name, "I", 8)
        else:
            self.set_font("Arial", "I", 8)
        pagina_str = f"Página {self.page_no()}/{{nb}}"
        self.cell(0, 10, self._encode_str(pagina_str), align="C")

def gerar_recibo(venda_id, dados_venda, itens_venda):
    """Gera um recibo de venda em formato PDF."""
    pdf = PDFRecibo()
    pdf.alias_nb_pages()
    pdf.add_page()

    if pdf.supports_utf8:
        pdf.set_font(pdf.font_name, "", 12)
    else:
        pdf.set_font("Arial", "", 12)

    # Informações da Venda
    pdf.cell(0, 10, pdf._encode_str(f"Venda ID: {venda_id}"), new_x="LMARGIN", new_y="NEXT")
    data_hora_str = dados_venda["data_hora"].strftime("%d/%m/%Y %H:%M:%S") if isinstance(dados_venda.get("data_hora"), datetime.datetime) else dados_venda.get("data_hora", "N/A")
    pdf.cell(0, 10, pdf._encode_str(f"Data e Hora: {data_hora_str}"), new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 10, pdf._encode_str(f"Vendedor: {dados_venda.get('usuario_nome', 'N/A')}"), new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 10, pdf._encode_str(f"Forma de Pagamento: {dados_venda.get('forma_pagamento', 'N/A')}"), new_x="LMARGIN", new_y="NEXT")
    if dados_venda.get("forma_pagamento") == "Crédito":
        pdf.cell(0, 10, pdf._encode_str(f"Parcelas: {dados_venda.get('parcelas', 1)}"), new_x="LMARGIN", new_y="NEXT")
    pdf.ln(5)

    # Itens da Venda
    if pdf.supports_utf8:
        pdf.set_font(pdf.font_name, "B", 12)
    else:
        pdf.set_font("Arial", "B", 12)

    # Larguras das colunas (ajustar conforme necessário)
    w_produto = 100
    w_qtd = 25
    w_preco = 30
    w_subtotal = 35
    line_height = 10

    pdf.cell(w_produto, line_height, pdf._encode_str("Produto"), border=1, align="C")
    pdf.cell(w_qtd, line_height, pdf._encode_str("Qtd"), border=1, align="C")
    pdf.cell(w_preco, line_height, pdf._encode_str("Preço Unit."), border=1, align="C")
    pdf.cell(w_subtotal, line_height, pdf._encode_str("Subtotal"), border=1, new_x="LMARGIN", new_y="NEXT", align="C")

    if pdf.supports_utf8:
        pdf.set_font(pdf.font_name, "", 10)
    else:
        pdf.set_font("Arial", "", 10)

    total_geral = 0
    for item in itens_venda:
        nome_produto = item.get("nome", "Produto Desconhecido")
        quantidade = item.get("quantidade", 0)
        preco_unitario = item.get("preco", 0.0)
        subtotal = quantidade * preco_unitario
        total_geral += subtotal

        # Tratar nomes longos (MultiCell pode ser melhor para quebra automática)
        # Simplesmente truncar por enquanto
        nome_produto_str = pdf._encode_str(nome_produto)
        if pdf.get_string_width(nome_produto_str) > w_produto - 2:
             while pdf.get_string_width(nome_produto_str + '...') > w_produto - 2 and len(nome_produto_str) > 0:
                 nome_produto_str = nome_produto_str[:-1]
             nome_produto_str += '...'

        pdf.cell(w_produto, line_height, nome_produto_str, border=1)
        pdf.cell(w_qtd, line_height, pdf._encode_str(str(quantidade)), border=1, align="C")
        pdf.cell(w_preco, line_height, pdf._encode_str(f"R$ {preco_unitario:.2f}"), border=1, align="R")
        pdf.cell(w_subtotal, line_height, pdf._encode_str(f"R$ {subtotal:.2f}"), border=1, new_x="LMARGIN", new_y="NEXT", align="R")

    # Total Geral
    if pdf.supports_utf8:
        pdf.set_font(pdf.font_name, "B", 12)
    else:
        pdf.set_font("Arial", "B", 12)
    pdf.cell(w_produto + w_qtd + w_preco, line_height, pdf._encode_str("Total Geral:"), border=0, align="R")
    pdf.cell(w_subtotal, line_height, pdf._encode_str(f"R$ {total_geral:.2f}"), border=1, new_x="LMARGIN", new_y="NEXT", align="R")

    # Salvar PDF
    try:
        # Garante que o diretório de recibos exista (relativo ao script main.py)
        # Idealmente, o caminho base seria passado como argumento ou obtido de forma mais robusta
        script_dir = os.path.dirname(os.path.abspath(__file__)) # Diretório do recibo.py
        diretorio_recibos = os.path.join(script_dir, "recibos") # Pasta recibos no mesmo nível
        os.makedirs(diretorio_recibos, exist_ok=True)
        caminho_completo = os.path.join(diretorio_recibos, f"recibo_venda_{venda_id}.pdf")

        pdf.output(caminho_completo, "F")
        print(f"Recibo gerado: {caminho_completo}")
        return caminho_completo
    except Exception as e:
        print(f"Erro ao gerar PDF do recibo: {e}")
        return None

# Exemplo de uso (para teste, executando recibo.py diretamente)
if __name__ == '__main__':
    # Mock data
    venda_id_teste = 999 # ID diferente para teste
    dados_venda_teste = {
        "data_hora": datetime.datetime.now(),
        "usuario_nome": "Admin Teste",
        "forma_pagamento": "Crédito",
        "parcelas": 3,
        "total": 150.00 # Este total no exemplo não bate com os itens, é só para estrutura
    }
    itens_venda_teste = [
        {"nome": "Produto A", "quantidade": 2, "preco": 25.00},
        {"nome": "Produto B Com Nome Muito Longo Para Caber Na Célula", "quantidade": 1, "preco": 50.00},
        {"nome": "Produto C", "quantidade": 5, "preco": 10.00}
    ]

    # Salvar na pasta 'recibos_teste' no mesmo diretório do script
    script_dir = os.path.dirname(os.path.abspath(__file__))
    diretorio_teste = os.path.join(script_dir, "recibos_teste")
    os.makedirs(diretorio_teste, exist_ok=True)
    caminho_teste = os.path.join(diretorio_teste, f"recibo_teste_{venda_id_teste}.pdf")

    print(f"Tentando salvar recibo de teste em: {caminho_teste}")

    # Gerar o PDF de teste
    pdf_teste = PDFRecibo()
    pdf_teste.alias_nb_pages()
    pdf_teste.add_page()
    if pdf_teste.supports_utf8:
        pdf_teste.set_font(pdf_teste.font_name, "", 12)
    else:
        pdf_teste.set_font("Arial", "", 12)
    pdf_teste.cell(0, 10, pdf_teste._encode_str(f"Recibo de TESTE - Venda ID: {venda_id_teste}"), new_x="LMARGIN", new_y="NEXT")
    # Adicionar mais detalhes se necessário para o teste...
    pdf_teste.cell(0, 10, pdf_teste._encode_str("Este é um arquivo de teste gerado executando recibo.py diretamente."), new_x="LMARGIN", new_y="NEXT")

    try:
        pdf_teste.output(caminho_teste, "F")
        print(f"Recibo de teste gerado com sucesso em: {caminho_teste}")
    except Exception as e:
        print(f"Falha ao gerar recibo de teste: {e}")

