# -*- coding: utf-8 -*-
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog, filedialog
import database as db
import recibo
import relatorio
import datetime
import os

# --- Variáveis Globais ---
itens_venda_atual = []
usuario_logado = None # Armazenará {"id": id, "nome": nome, "tipo": tipo}
produto_selecionado_id = None
produto_selecionado_venda_id = None

# --- Funções Auxiliares ---
def formatar_data(data_str):
    """Tenta formatar a data para YYYY-MM-DD."""
    for fmt in ("%d/%m/%Y", "%Y-%m-%d"):
        try:
            return datetime.datetime.strptime(data_str, fmt).strftime("%Y-%m-%d")
        except ValueError:
            pass
    raise ValueError("Formato de data inválido. Use DD/MM/AAAA ou YYYY-MM-DD.")

def validar_float(valor_str):
    """Valida e converte string para float."""
    try:
        return float(valor_str.replace(",", "."))
    except ValueError:
        raise ValueError("Valor inválido. Use números e ponto/vírgula decimal.")

def validar_int(valor_str):
    """Valida e converte string para int."""
    try:
        return int(valor_str)
    except ValueError:
        raise ValueError("Valor inválido. Use apenas números inteiros.")

# --- Tela de Login ---
def fazer_login():
    global usuario_logado
    usuario = entry_usuario.get()
    senha = entry_senha.get()

    if not usuario or not senha:
        messagebox.showwarning("Campos Vazios", "Por favor, preencha usuário e senha.")
        return

    user_data = db.autenticar_usuario(usuario, senha)

    if user_data:
        usuario_logado = user_data
        # Precisamos buscar o ID também
        conn = db.conectar_bd()
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM usuarios WHERE usuario = ?", (usuario,))
        user_id_result = cursor.fetchone()
        conn.close()
        if user_id_result:
            usuario_logado["id"] = user_id_result["id"]
        else:
             messagebox.showerror("Erro", "Não foi possível obter o ID do usuário.")
             usuario_logado = None # Resetar se não achar ID
             return

        janela_login.destroy()
        iniciar_sistema()
    else:
        messagebox.showerror("Erro de Login", "Usuário ou senha incorretos!")

# --- Sistema Principal ---
def iniciar_sistema():
    global tree_produtos_cadastro, entry_cod_barras_cad, entry_nome_cad, entry_custo_cad, entry_venda_cad, entry_estoque_cad, entry_fornecedor_cad, entry_minimo_cad
    global tree_venda_busca, tree_venda_carrinho, lbl_total_venda, var_pagamento, entry_parcelas, combo_pagamento
    global tree_estoque, entry_produto_id_est, entry_qtd_entrada, entry_motivo_entrada
    global combo_relatorio, entry_data_ini, entry_data_fim, tree_relatorio
    global abas, frame_botoes_cad # Tornar abas e frame_botoes_cad globais

    janela = tk.Tk()
    janela.title("Sistema Loja Simplificado")
    janela.geometry("900x700") # Aumentar tamanho

    # Informação do Usuário Logado
    if usuario_logado:
        info_usuario = f"Usuário: {usuario_logado['nome']} ({usuario_logado['tipo']})"
    else:
        info_usuario = "Erro: Usuário não identificado"
        messagebox.showerror("Erro Crítico", "Não foi possível identificar o usuário logado.")
        janela.destroy()
        return

    lbl_usuario = tk.Label(janela, text=info_usuario, anchor="e")
    lbl_usuario.pack(fill="x", padx=10, pady=5)

    abas = ttk.Notebook(janela)

    # --- Aba Cadastro --- #
    aba_cadastro = ttk.Frame(abas)
    abas.add(aba_cadastro, text="Cadastro de Produto")

    # Frame para os campos de entrada
    frame_campos_cad = ttk.LabelFrame(aba_cadastro, text="Dados do Produto")
    frame_campos_cad.pack(padx=10, pady=10, fill="x")

    ttk.Label(frame_campos_cad, text="Cód. Barras:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
    entry_cod_barras_cad = ttk.Entry(frame_campos_cad, width=20)
    entry_cod_barras_cad.grid(row=0, column=1, padx=5, pady=5, sticky="ew")

    ttk.Label(frame_campos_cad, text="Nome:").grid(row=1, column=0, padx=5, pady=5, sticky="w")
    entry_nome_cad = ttk.Entry(frame_campos_cad, width=40)
    entry_nome_cad.grid(row=1, column=1, columnspan=3, padx=5, pady=5, sticky="ew")

    ttk.Label(frame_campos_cad, text="Preço Custo:").grid(row=2, column=0, padx=5, pady=5, sticky="w")
    entry_custo_cad = ttk.Entry(frame_campos_cad, width=10)
    entry_custo_cad.grid(row=2, column=1, padx=5, pady=5, sticky="ew")

    ttk.Label(frame_campos_cad, text="Preço Venda:").grid(row=2, column=2, padx=5, pady=5, sticky="w")
    entry_venda_cad = ttk.Entry(frame_campos_cad, width=10)
    entry_venda_cad.grid(row=2, column=3, padx=5, pady=5, sticky="ew")

    ttk.Label(frame_campos_cad, text="Estoque Inicial:").grid(row=3, column=0, padx=5, pady=5, sticky="w")
    entry_estoque_cad = ttk.Entry(frame_campos_cad, width=10)
    entry_estoque_cad.grid(row=3, column=1, padx=5, pady=5, sticky="ew")

    ttk.Label(frame_campos_cad, text="Estoque Mínimo:").grid(row=3, column=2, padx=5, pady=5, sticky="w")
    entry_minimo_cad = ttk.Entry(frame_campos_cad, width=10)
    entry_minimo_cad.grid(row=3, column=3, padx=5, pady=5, sticky="ew")

    ttk.Label(frame_campos_cad, text="Fornecedor:").grid(row=4, column=0, padx=5, pady=5, sticky="w")
    entry_fornecedor_cad = ttk.Entry(frame_campos_cad, width=40)
    entry_fornecedor_cad.grid(row=4, column=1, columnspan=3, padx=5, pady=5, sticky="ew")

    # Frame para os botões de ação
    frame_botoes_cad = ttk.Frame(aba_cadastro)
    frame_botoes_cad.pack(pady=5, fill="x", padx=10)

    btn_adicionar_cad = ttk.Button(frame_botoes_cad, text="Adicionar", command=adicionar_produto_interface)
    btn_adicionar_cad.pack(side=tk.LEFT, padx=5)
    btn_editar_cad = ttk.Button(frame_botoes_cad, text="Salvar Edição", command=editar_produto_interface, state=tk.DISABLED)
    btn_editar_cad.pack(side=tk.LEFT, padx=5)
    btn_excluir_cad = ttk.Button(frame_botoes_cad, text="Excluir", command=excluir_produto_interface, state=tk.DISABLED)
    btn_excluir_cad.pack(side=tk.LEFT, padx=5)
    btn_limpar_cad = ttk.Button(frame_botoes_cad, text="Limpar Campos", command=lambda: limpar_campos_cadastro(True))
    btn_limpar_cad.pack(side=tk.LEFT, padx=5)

    # Frame para pesquisa e listagem
    frame_lista_cad = ttk.LabelFrame(aba_cadastro, text="Produtos Cadastrados")
    frame_lista_cad.pack(padx=10, pady=10, fill="both", expand=True)

    ttk.Label(frame_lista_cad, text="Pesquisar (Nome/Cód.):").pack(side=tk.LEFT, padx=5, pady=5)
    entry_pesquisa_cad = ttk.Entry(frame_lista_cad, width=30)
    entry_pesquisa_cad.pack(side=tk.LEFT, padx=5, pady=5)
    btn_pesquisar_cad = ttk.Button(frame_lista_cad, text="Pesquisar", command=lambda: pesquisar_produto_interface(entry_pesquisa_cad.get()))
    btn_pesquisar_cad.pack(side=tk.LEFT, padx=5, pady=5)
    btn_listar_todos_cad = ttk.Button(frame_lista_cad, text="Listar Todos", command=lambda: pesquisar_produto_interface(""))
    btn_listar_todos_cad.pack(side=tk.LEFT, padx=5, pady=5)

    # Treeview para listar produtos
    cols_cadastro = ("ID", "Cód. Barras", "Nome", "P. Venda", "Estoque", "Est. Mín.")
    tree_produtos_cadastro = ttk.Treeview(frame_lista_cad, columns=cols_cadastro, show="headings", height=10)
    for col in cols_cadastro:
        tree_produtos_cadastro.heading(col, text=col)
        tree_produtos_cadastro.column(col, width=100, anchor=tk.CENTER)
    tree_produtos_cadastro.column("Nome", width=250, anchor=tk.W)
    tree_produtos_cadastro.pack(fill="both", expand=True, padx=5, pady=5)
    tree_produtos_cadastro.bind("<<TreeviewSelect>>", lambda event: selecionar_produto_cadastro(event, btn_editar_cad, btn_excluir_cad))

    # --- Aba Venda --- #
    aba_venda = ttk.Frame(abas)
    abas.add(aba_venda, text="Venda / Pagamento")

    # Layout com PanedWindow para dividir busca/carrinho e pagamento
    paned_venda = ttk.PanedWindow(aba_venda, orient=tk.HORIZONTAL)
    paned_venda.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

    # Frame Esquerdo: Busca e Carrinho
    frame_esquerda_venda = ttk.Frame(paned_venda)
    paned_venda.add(frame_esquerda_venda, weight=2)

    # Busca de Produto
    frame_busca_venda = ttk.LabelFrame(frame_esquerda_venda, text="Buscar Produto")
    frame_busca_venda.pack(padx=5, pady=5, fill="x")
    ttk.Label(frame_busca_venda, text="Nome/Cód.:").pack(side=tk.LEFT, padx=5)
    entry_busca_prod_venda = ttk.Entry(frame_busca_venda, width=20)
    entry_busca_prod_venda.pack(side=tk.LEFT, padx=5)
    btn_buscar_prod_venda = ttk.Button(frame_busca_venda, text="Buscar", command=lambda: buscar_produto_venda(entry_busca_prod_venda.get()))
    btn_buscar_prod_venda.pack(side=tk.LEFT, padx=5)

    # Lista de Produtos Encontrados (para adicionar)
    cols_busca_venda = ("ID", "Nome", "Preço", "Estoque")
    tree_venda_busca = ttk.Treeview(frame_esquerda_venda, columns=cols_busca_venda, show="headings", height=5)
    for col in cols_busca_venda:
        tree_venda_busca.heading(col, text=col)
        tree_venda_busca.column(col, width=80, anchor=tk.CENTER)
    tree_venda_busca.column("Nome", width=150, anchor=tk.W)
    tree_venda_busca.pack(padx=5, pady=5, fill="x")
    tree_venda_busca.bind("<<TreeviewSelect>>", selecionar_produto_venda)

    # Botão Adicionar ao Carrinho
    frame_add_item = ttk.Frame(frame_esquerda_venda)
    frame_add_item.pack(pady=5)
    ttk.Label(frame_add_item, text="Qtd:").pack(side=tk.LEFT)
    entry_qtd_item_venda = ttk.Entry(frame_add_item, width=5)
    entry_qtd_item_venda.pack(side=tk.LEFT, padx=5)
    entry_qtd_item_venda.insert(0, "1") # Default 1
    btn_add_item_venda = ttk.Button(frame_add_item, text="Adicionar Item", command=lambda: adicionar_item_venda(entry_qtd_item_venda.get()))
    btn_add_item_venda.pack(side=tk.LEFT, padx=5)

    # Carrinho de Compras
    frame_carrinho_venda = ttk.LabelFrame(frame_esquerda_venda, text="Carrinho")
    frame_carrinho_venda.pack(padx=5, pady=5, fill="both", expand=True)
    cols_carrinho = ("ID", "Nome", "Qtd", "Preço Unit.", "Subtotal")
    tree_venda_carrinho = ttk.Treeview(frame_carrinho_venda, columns=cols_carrinho, show="headings", height=8)
    for col in cols_carrinho:
        tree_venda_carrinho.heading(col, text=col)
        tree_venda_carrinho.column(col, width=80, anchor=tk.CENTER)
    tree_venda_carrinho.column("Nome", width=150, anchor=tk.W)
    tree_venda_carrinho.pack(fill="both", expand=True, padx=5, pady=5)

    btn_remover_item_venda = ttk.Button(frame_carrinho_venda, text="Remover Item Selecionado", command=remover_item_venda)
    btn_remover_item_venda.pack(pady=5)

    # Frame Direito: Pagamento e Finalização
    frame_direita_venda = ttk.Frame(paned_venda)
    paned_venda.add(frame_direita_venda, weight=1)

    frame_pagamento = ttk.LabelFrame(frame_direita_venda, text="Pagamento")
    frame_pagamento.pack(padx=5, pady=10, fill="x")

    ttk.Label(frame_pagamento, text="Forma de Pagamento:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
    var_pagamento = tk.StringVar()
    combo_pagamento = ttk.Combobox(frame_pagamento, textvariable=var_pagamento, values=["Dinheiro", "Débito", "Crédito"], state="readonly")
    combo_pagamento.grid(row=0, column=1, padx=5, pady=5)
    combo_pagamento.bind("<<ComboboxSelected>>", habilitar_parcelas)

    ttk.Label(frame_pagamento, text="Parcelas (Crédito):").grid(row=1, column=0, padx=5, pady=5, sticky="w")
    entry_parcelas = ttk.Entry(frame_pagamento, width=5, state=tk.DISABLED)
    entry_parcelas.grid(row=1, column=1, padx=5, pady=5, sticky="w")
    entry_parcelas.insert(0, "1")

    # Total da Venda
    frame_total_venda = ttk.Frame(frame_direita_venda)
    frame_total_venda.pack(pady=20, fill="x", padx=5)
    lbl_total_venda_txt = ttk.Label(frame_total_venda, text="TOTAL: R$", font=("Arial", 16, "bold"))
    lbl_total_venda_txt.pack(side=tk.LEFT)
    lbl_total_venda = ttk.Label(frame_total_venda, text="0.00", font=("Arial", 16, "bold"))
    lbl_total_venda.pack(side=tk.LEFT, padx=10)

    # Botões de Finalização
    frame_finalizar = ttk.Frame(frame_direita_venda)
    frame_finalizar.pack(pady=10, fill="x", padx=5)
    btn_finalizar_venda = ttk.Button(frame_finalizar, text="Finalizar Venda", command=finalizar_venda_interface, width=20)
    btn_finalizar_venda.pack(pady=5)
    btn_cancelar_venda = ttk.Button(frame_finalizar, text="Cancelar Venda", command=limpar_venda, width=20)
    btn_cancelar_venda.pack(pady=5)

    # --- Aba Estoque --- #
    aba_estoque = ttk.Frame(abas)
    abas.add(aba_estoque, text="Controle de Estoque")

    # Frame para Registrar Entrada
    frame_entrada_est = ttk.LabelFrame(aba_estoque, text="Registrar Entrada Manual")
    frame_entrada_est.pack(padx=10, pady=10, fill="x")

    ttk.Label(frame_entrada_est, text="ID do Produto:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
    entry_produto_id_est = ttk.Entry(frame_entrada_est, width=10)
    entry_produto_id_est.grid(row=0, column=1, padx=5, pady=5, sticky="w")
    # TODO: Adicionar botão para buscar produto e preencher ID?

    ttk.Label(frame_entrada_est, text="Quantidade Entrada:").grid(row=0, column=2, padx=5, pady=5, sticky="w")
    entry_qtd_entrada = ttk.Entry(frame_entrada_est, width=10)
    entry_qtd_entrada.grid(row=0, column=3, padx=5, pady=5, sticky="w")

    ttk.Label(frame_entrada_est, text="Motivo (Ex: Compra NF 123):").grid(row=1, column=0, padx=5, pady=5, sticky="w")
    entry_motivo_entrada = ttk.Entry(frame_entrada_est, width=40)
    entry_motivo_entrada.grid(row=1, column=1, columnspan=3, padx=5, pady=5, sticky="ew")

    btn_registrar_entrada = ttk.Button(frame_entrada_est, text="Registrar Entrada", command=registrar_entrada_interface)
    btn_registrar_entrada.grid(row=2, column=0, columnspan=4, pady=10)

    # Frame para Listagem de Estoque
    frame_lista_est = ttk.LabelFrame(aba_estoque, text="Visão Geral do Estoque")
    frame_lista_est.pack(padx=10, pady=10, fill="both", expand=True)

    # Treeview para listar estoque
    cols_estoque = ("ID", "Cód. Barras", "Nome", "Estoque Atual", "Est. Mínimo")
    tree_estoque = ttk.Treeview(frame_lista_est, columns=cols_estoque, show="headings", height=15)
    for col in cols_estoque:
        tree_estoque.heading(col, text=col)
        tree_estoque.column(col, width=100, anchor=tk.CENTER)
    tree_estoque.column("Nome", width=300, anchor=tk.W)

    # Adicionar tags para cores
    tree_estoque.tag_configure("baixo", background="#FFDDDD") # Vermelho claro
    tree_estoque.tag_configure("ok", background="white")

    tree_estoque.pack(fill="both", expand=True, padx=5, pady=5)

    # Botão para atualizar lista
    btn_atualizar_lista_est = ttk.Button(frame_lista_est, text="Atualizar Lista", command=atualizar_lista_estoque)
    btn_atualizar_lista_est.pack(pady=5)

    # --- Aba Relatórios --- #
    aba_relatorio = ttk.Frame(abas)
    abas.add(aba_relatorio, text="Relatórios")

    # Frame para seleção e filtros
    frame_filtros_rel = ttk.LabelFrame(aba_relatorio, text="Opções de Relatório")
    frame_filtros_rel.pack(padx=10, pady=10, fill="x")

    ttk.Label(frame_filtros_rel, text="Tipo de Relatório:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
    combo_relatorio = ttk.Combobox(frame_filtros_rel, values=[
        "Vendas por Período",
        "Produtos Mais Vendidos",
        "Movimentações de Estoque"
    ], state="readonly", width=30)
    combo_relatorio.grid(row=0, column=1, columnspan=3, padx=5, pady=5, sticky="ew")
    combo_relatorio.current(0) # Padrão: Vendas por Período

    ttk.Label(frame_filtros_rel, text="Data Início (DD/MM/AAAA):").grid(row=1, column=0, padx=5, pady=5, sticky="w")
    entry_data_ini = ttk.Entry(frame_filtros_rel, width=12)
    entry_data_ini.grid(row=1, column=1, padx=5, pady=5)
    entry_data_ini.insert(0, (datetime.date.today() - datetime.timedelta(days=30)).strftime("%d/%m/%Y")) # Padrão: 30 dias atrás

    ttk.Label(frame_filtros_rel, text="Data Fim (DD/MM/AAAA):").grid(row=1, column=2, padx=5, pady=5, sticky="w")
    entry_data_fim = ttk.Entry(frame_filtros_rel, width=12)
    entry_data_fim.grid(row=1, column=3, padx=5, pady=5)
    entry_data_fim.insert(0, datetime.date.today().strftime("%d/%m/%Y")) # Padrão: Hoje

    # TODO: Adicionar filtro de produto para Movimentações de Estoque?

    btn_gerar_relatorio = ttk.Button(frame_filtros_rel, text="Gerar Relatório", command=gerar_relatorio_interface)
    btn_gerar_relatorio.grid(row=2, column=0, columnspan=4, pady=10)

    # Frame para exibir o relatório
    frame_exibicao_rel = ttk.LabelFrame(aba_relatorio, text="Resultado")
    frame_exibicao_rel.pack(padx=10, pady=10, fill="both", expand=True)

    # Treeview para exibir relatórios tabulares
    tree_relatorio = ttk.Treeview(frame_exibicao_rel, show="headings") # Colunas definidas dinamicamente
    tree_relatorio.pack(side=tk.LEFT, fill="both", expand=True, padx=5, pady=5)

    # Scrollbar para Treeview
    scrollbar_rel = ttk.Scrollbar(frame_exibicao_rel, orient="vertical", command=tree_relatorio.yview)
    scrollbar_rel.pack(side=tk.RIGHT, fill="y")
    tree_relatorio.configure(yscrollcommand=scrollbar_rel.set)

    # Botões de Exportação
    frame_export_rel = ttk.Frame(aba_relatorio)
    frame_export_rel.pack(pady=10)

    btn_export_pdf = ttk.Button(frame_export_rel, text="Exportar para PDF", command=exportar_pdf_interface)
    btn_export_pdf.pack(side=tk.LEFT, padx=10)
    btn_export_excel = ttk.Button(frame_export_rel, text="Exportar para Excel", command=exportar_excel_interface)
    btn_export_excel.pack(side=tk.LEFT, padx=10)

    # --- Empacotar Abas e Aplicar Permissões --- #
    abas.pack(expand=1, fill="both")
    aplicar_permissoes(abas, usuario_logado["tipo"])

    # --- Carregar Dados Iniciais --- #
    pesquisar_produto_interface("") # Carrega produtos no cadastro
    atualizar_lista_estoque() # Carrega estoque

    janela.mainloop()

# --- Funções da Aba Cadastro --- #
def limpar_campos_cadastro(limpar_selecao=False):
    global produto_selecionado_id
    entry_cod_barras_cad.delete(0, tk.END)
    entry_nome_cad.delete(0, tk.END)
    entry_custo_cad.delete(0, tk.END)
    entry_venda_cad.delete(0, tk.END)
    entry_estoque_cad.delete(0, tk.END)
    entry_fornecedor_cad.delete(0, tk.END)
    entry_minimo_cad.delete(0, tk.END)
    entry_estoque_cad.config(state=tk.NORMAL) # Habilita para novos cadastros
    if limpar_selecao:
        produto_selecionado_id = None
        try:
            tree_produtos_cadastro.selection_remove(tree_produtos_cadastro.selection()) # Limpa seleção visual
        except tk.TclError: # Ignora erro se a treeview não existir mais (janela fechada)
            pass
        # Resetar botões
        try:
            for child in frame_botoes_cad.winfo_children():
                if isinstance(child, ttk.Button):
                    if child.cget("text") == "Adicionar":
                        child.config(state=tk.NORMAL)
                    elif child.cget("text") in ["Salvar Edição", "Excluir"]:
                        child.config(state=tk.DISABLED)
        except tk.TclError:
            pass # Ignora erro se frame não existir mais

def adicionar_produto_interface():
    cod_barras = entry_cod_barras_cad.get().strip()
    nome = entry_nome_cad.get().strip()
    fornecedor = entry_fornecedor_cad.get().strip()
    try:
        preco_custo_str = entry_custo_cad.get().strip()
        preco_custo = validar_float(preco_custo_str) if preco_custo_str else 0.0
        preco_venda = validar_float(entry_venda_cad.get().strip())
        estoque = validar_int(entry_estoque_cad.get().strip())
        estoque_minimo_str = entry_minimo_cad.get().strip()
        estoque_minimo = validar_int(estoque_minimo_str) if estoque_minimo_str else 5 # Padrão 5 se vazio

        if not nome or preco_venda <= 0 or estoque < 0 or estoque_minimo < 0:
            messagebox.showwarning("Dados Inválidos", "Nome, Preço de Venda (>0), Estoque (>=0) e Estoque Mínimo (>=0) são obrigatórios.")
            return

        if db.adicionar_produto(cod_barras, nome, preco_custo, preco_venda, estoque, fornecedor, estoque_minimo):
            messagebox.showinfo("Sucesso", "Produto cadastrado com sucesso!")
            limpar_campos_cadastro()
            pesquisar_produto_interface("") # Atualiza lista
            atualizar_lista_estoque() # Atualiza estoque
        else:
            messagebox.showerror("Erro", "Código de barras já existe ou ocorreu um erro ao salvar.")
    except ValueError as e:
        messagebox.showerror("Erro de Entrada", str(e))
    except Exception as e:
        messagebox.showerror("Erro Inesperado", f"Ocorreu um erro: {str(e)}")

def pesquisar_produto_interface(termo):
    try:
        produtos = db.listar_produtos(termo)
        # Limpar treeview
        for i in tree_produtos_cadastro.get_children():
            tree_produtos_cadastro.delete(i)
        # Preencher com resultados
        for prod in produtos:
            tree_produtos_cadastro.insert("", tk.END, values=(
                prod["id"],
                prod["codigo_barras"],
                prod["nome"],
                f"{prod['preco_venda']:.2f}",
                prod["estoque"],
                prod["estoque_minimo"]
            ))
        limpar_campos_cadastro(True) # Limpa campos e seleção
    except tk.TclError:
        pass # Ignora erro se a treeview não existir mais
    except Exception as e:
        messagebox.showerror("Erro ao Pesquisar", f"Ocorreu um erro: {str(e)}")

def selecionar_produto_cadastro(event, btn_editar, btn_excluir):
    global produto_selecionado_id
    try:
        selected_item = tree_produtos_cadastro.focus() # Item focado
        if not selected_item:
            return

        item_values = tree_produtos_cadastro.item(selected_item, "values")
        if not item_values:
            return

        produto_selecionado_id = int(item_values[0])
        produto = db.buscar_produto_por_id(produto_selecionado_id)

        if produto:
            limpar_campos_cadastro()
            entry_cod_barras_cad.insert(0, produto["codigo_barras"] if produto["codigo_barras"] else "")
            entry_nome_cad.insert(0, produto["nome"])
            entry_custo_cad.insert(0, f"{produto['preco_custo']:.2f}" if produto["preco_custo"] else "0.00")
            entry_venda_cad.insert(0, f"{produto['preco_venda']:.2f}")
            entry_estoque_cad.insert(0, str(produto["estoque"]))
            entry_estoque_cad.config(state=tk.DISABLED) # Não edita estoque aqui
            entry_fornecedor_cad.insert(0, produto["fornecedor"] if produto["fornecedor"] else "")
            entry_minimo_cad.insert(0, str(produto["estoque_minimo"]))

            # Habilitar/Desabilitar botões
            btn_editar.config(state=tk.NORMAL)
            btn_excluir.config(state=tk.NORMAL)
            for child in frame_botoes_cad.winfo_children():
                 if isinstance(child, ttk.Button) and child.cget("text") == "Adicionar":
                     child.config(state=tk.DISABLED)
        else:
            messagebox.showerror("Erro", "Produto não encontrado no banco de dados.")
            produto_selecionado_id = None
            limpar_campos_cadastro(True)
    except tk.TclError:
        pass # Ignora erro se widget não existe mais
    except Exception as e:
        messagebox.showerror("Erro ao Selecionar", f"Ocorreu um erro: {str(e)}")
        produto_selecionado_id = None
        limpar_campos_cadastro(True)

def editar_produto_interface():
    if produto_selecionado_id is None:
        messagebox.showwarning("Nenhum Produto Selecionado", "Selecione um produto na lista para editar.")
        return

    cod_barras = entry_cod_barras_cad.get().strip()
    nome = entry_nome_cad.get().strip()
    fornecedor = entry_fornecedor_cad.get().strip()
    try:
        preco_custo_str = entry_custo_cad.get().strip()
        preco_custo = validar_float(preco_custo_str) if preco_custo_str else 0.0
        preco_venda = validar_float(entry_venda_cad.get().strip())
        # Estoque não é editado aqui, buscamos o valor atual
        produto_atual = db.buscar_produto_por_id(produto_selecionado_id)
        if not produto_atual:
             messagebox.showerror("Erro", "Produto selecionado não existe mais.")
             limpar_campos_cadastro(True)
             return
        estoque = produto_atual["estoque"]
        estoque_minimo_str = entry_minimo_cad.get().strip()
        estoque_minimo = validar_int(estoque_minimo_str) if estoque_minimo_str else 5

        if not nome or preco_venda <= 0 or estoque_minimo < 0:
            messagebox.showwarning("Dados Inválidos", "Nome, Preço de Venda (>0) e Estoque Mínimo (>=0) são obrigatórios.")
            return

        if db.atualizar_produto(produto_selecionado_id, cod_barras, nome, preco_custo, preco_venda, estoque, fornecedor, estoque_minimo):
            messagebox.showinfo("Sucesso", "Produto atualizado com sucesso!")
            limpar_campos_cadastro(True)
            pesquisar_produto_interface("") # Atualiza lista
            atualizar_lista_estoque() # Atualiza estoque (caso min tenha mudado)
        else:
            messagebox.showerror("Erro", "Código de barras duplicado ou erro ao salvar.")
    except ValueError as e:
        messagebox.showerror("Erro de Entrada", str(e))
    except Exception as e:
        messagebox.showerror("Erro Inesperado", f"Ocorreu um erro: {str(e)}")

def excluir_produto_interface():
    if produto_selecionado_id is None:
        messagebox.showwarning("Nenhum Produto Selecionado", "Selecione um produto na lista para excluir.")
        return

    if messagebox.askyesno("Confirmar Exclusão", f"Tem certeza que deseja excluir o produto ID {produto_selecionado_id}? Esta ação NÃO pode ser desfeita e removerá o produto de vendas anteriores!"):
        # Tentativa de exclusão (pode falhar devido a restrições de FK se não configurado ON DELETE CASCADE)
        # AVISO: A configuração atual ON DELETE RESTRICT em itens_venda impedirá a exclusão se o produto estiver em uma venda.
        # Para permitir, seria necessário mudar para SET NULL ou remover a restrição (arriscado para integridade)
        # Ou implementar uma lógica de 'produto inativo'.
        if db.excluir_produto(produto_selecionado_id):
            messagebox.showinfo("Sucesso", "Produto excluído com sucesso!")
            limpar_campos_cadastro(True)
            pesquisar_produto_interface("") # Atualiza lista
            atualizar_lista_estoque() # Atualiza estoque
        else:
            messagebox.showerror("Erro", "Não foi possível excluir o produto. Verifique se ele está associado a vendas registradas.")

# --- Funções da Aba Venda --- #
def buscar_produto_venda(termo):
    global produto_selecionado_venda_id
    try:
        produtos = db.listar_produtos(termo)
        tree_venda_busca.delete(*tree_venda_busca.get_children())
        produto_selecionado_venda_id = None # Reseta seleção
        for prod in produtos:
            if prod["estoque"] > 0: # Só lista produtos com estoque
                tree_venda_busca.insert("", tk.END, values=(
                    prod["id"],
                    prod["nome"],
                    f"{prod['preco_venda']:.2f}",
                    prod["estoque"]
                ))
    except tk.TclError:
        pass # Ignora erro se widget não existe mais
    except Exception as e:
        messagebox.showerror("Erro ao Buscar", f"Ocorreu um erro: {str(e)}")

def selecionar_produto_venda(event):
    global produto_selecionado_venda_id
    try:
        selected_item = tree_venda_busca.focus()
        if not selected_item:
            produto_selecionado_venda_id = None
            return
        item_values = tree_venda_busca.item(selected_item, "values")
        if item_values:
            produto_selecionado_venda_id = int(item_values[0])
        else:
            produto_selecionado_venda_id = None
    except tk.TclError:
        produto_selecionado_venda_id = None
    except Exception as e:
        print(f"Erro ao selecionar produto para venda: {e}")
        produto_selecionado_venda_id = None

def adicionar_item_venda(qtd_str):
    global itens_venda_atual
    if produto_selecionado_venda_id is None:
        messagebox.showwarning("Nenhum Produto", "Selecione um produto na lista de busca.")
        return

    try:
        quantidade = validar_int(qtd_str)
        if quantidade <= 0:
            messagebox.showwarning("Quantidade Inválida", "A quantidade deve ser maior que zero.")
            return
    except ValueError as e:
        messagebox.showerror("Erro de Entrada", str(e))
        return

    produto = db.buscar_produto_por_id(produto_selecionado_venda_id)
    if not produto:
        messagebox.showerror("Erro", "Produto não encontrado.")
        return

    # Verificar estoque
    estoque_atual = produto["estoque"]
    # Verificar se já existe no carrinho para somar quantidade
    qtd_ja_no_carrinho = 0
    item_existente_index = -1
    for i, item in enumerate(itens_venda_atual):
        if item["produto_id"] == produto_selecionado_venda_id:
            qtd_ja_no_carrinho = item["quantidade"]
            item_existente_index = i
            break

    if quantidade + qtd_ja_no_carrinho > estoque_atual:
        messagebox.showwarning("Estoque Insuficiente", f"Estoque disponível para '{produto['nome']}': {estoque_atual}. Você já tem {qtd_ja_no_carrinho} no carrinho.")
        return

    # Adicionar ou atualizar item no carrinho (lista global)
    if item_existente_index != -1:
        itens_venda_atual[item_existente_index]["quantidade"] += quantidade
    else:
        item = {
            "produto_id": produto["id"],
            "nome": produto["nome"],
            "quantidade": quantidade,
            "preco": produto["preco_venda"]
        }
        itens_venda_atual.append(item)

    atualizar_carrinho_e_total()
    # Limpar seleção da busca e quantidade
    try:
        tree_venda_busca.selection_remove(tree_venda_busca.selection())
        entry_qtd_item_venda.delete(0, tk.END)
        entry_qtd_item_venda.insert(0, "1")
    except tk.TclError:
        pass # Ignora erro se widget não existe mais
    produto_selecionado_venda_id = None

def remover_item_venda():
    global itens_venda_atual
    try:
        selected_item_carrinho = tree_venda_carrinho.focus()
        if not selected_item_carrinho:
            messagebox.showwarning("Nenhum Item", "Selecione um item no carrinho para remover.")
            return

        item_values = tree_venda_carrinho.item(selected_item_carrinho, "values")
        if not item_values:
            return

        produto_id_remover = int(item_values[0])

        # Encontrar e remover da lista global
        itens_venda_atual = [item for item in itens_venda_atual if item["produto_id"] != produto_id_remover]

        atualizar_carrinho_e_total()
    except tk.TclError:
        pass # Ignora erro se widget não existe mais
    except Exception as e:
        messagebox.showerror("Erro ao Remover Item", f"Ocorreu um erro: {str(e)}")

def atualizar_carrinho_e_total():
    try:
        # Limpar carrinho visual
        tree_venda_carrinho.delete(*tree_venda_carrinho.get_children())
        total_venda = 0
        # Preencher com itens da lista global
        for item in itens_venda_atual:
            subtotal = item["quantidade"] * item["preco"]
            tree_venda_carrinho.insert("", tk.END, values=(
                item["produto_id"],
                item["nome"],
                item["quantidade"],
                f"{item['preco']:.2f}",
                f"{subtotal:.2f}"
            ))
            total_venda += subtotal

        # Atualizar label total
        lbl_total_venda.config(text=f"{total_venda:.2f}")
    except tk.TclError:
        pass # Ignora erro se widget não existe mais
    except Exception as e:
        print(f"Erro ao atualizar carrinho: {e}")

def habilitar_parcelas(event=None):
    try:
        if var_pagamento.get() == "Crédito":
            entry_parcelas.config(state=tk.NORMAL)
        else:
            entry_parcelas.delete(0, tk.END)
            entry_parcelas.insert(0, "1")
            entry_parcelas.config(state=tk.DISABLED)
    except tk.TclError:
        pass # Ignora erro se widget não existe mais

def limpar_venda():
    global itens_venda_atual, produto_selecionado_venda_id
    itens_venda_atual = []
    produto_selecionado_venda_id = None
    try:
        tree_venda_busca.delete(*tree_venda_busca.get_children())
        entry_busca_prod_venda.delete(0, tk.END)
        entry_qtd_item_venda.delete(0, tk.END)
        entry_qtd_item_venda.insert(0, "1")
        var_pagamento.set("")
        entry_parcelas.delete(0, tk.END)
        entry_parcelas.insert(0, "1")
        entry_parcelas.config(state=tk.DISABLED)
        atualizar_carrinho_e_total()
    except tk.TclError:
        pass # Ignora erro se widgets não existem mais

def finalizar_venda_interface():
    if not itens_venda_atual:
        messagebox.showwarning("Carrinho Vazio", "Adicione itens ao carrinho antes de finalizar a venda.")
        return

    forma_pagamento = var_pagamento.get()
    if not forma_pagamento:
        messagebox.showwarning("Pagamento Inválido", "Selecione uma forma de pagamento.")
        return

    try:
        parcelas = validar_int(entry_parcelas.get()) if forma_pagamento == "Crédito" else 1
        if parcelas <= 0:
            messagebox.showwarning("Parcelas Inválidas", "Número de parcelas deve ser maior que zero.")
            return
    except ValueError as e:
        messagebox.showerror("Erro de Entrada", f"Parcelas: {str(e)}")
        return
    except tk.TclError:
        messagebox.showerror("Erro Interface", "Erro ao ler campo de parcelas.")
        return

    total_venda = 0
    try:
        total_venda = float(lbl_total_venda.cget("text"))
    except (ValueError, tk.TclError):
         messagebox.showerror("Erro Interface", "Erro ao ler total da venda.")
         return

    # Confirmar venda
    msg = f"Confirmar Venda:\n\n"
    for item in itens_venda_atual:
        msg += f"- {item['nome']} ({item['quantidade']}x R$ {item['preco']:.2f})\n"
    msg += f"\nTotal: R$ {total_venda:.2f}"
    msg += f"\nPagamento: {forma_pagamento}"
    if forma_pagamento == "Crédito":
        msg += f" ({parcelas}x)"

    if messagebox.askyesno("Confirmar Venda", msg):
        venda_id = db.registrar_venda(usuario_logado["id"], forma_pagamento, parcelas, total_venda, itens_venda_atual)

        if venda_id:
            messagebox.showinfo("Sucesso", f"Venda #{venda_id} registrada com sucesso!")

            # Gerar Recibo
            dados_recibo = {
                "data_hora": datetime.datetime.now(),
                "usuario_nome": usuario_logado["nome"],
                "forma_pagamento": forma_pagamento,
                "parcelas": parcelas
            }
            caminho_recibo = recibo.gerar_recibo(venda_id, dados_recibo, itens_venda_atual)

            if caminho_recibo:
                if messagebox.askyesno("Recibo Gerado", f"Recibo salvo em:\n{caminho_recibo}\n\nDeseja abrir o recibo agora?"):
                    try:
                        # Tenta abrir com o visualizador padrão do sistema
                        if os.name == "nt": # Windows
                            os.startfile(caminho_recibo)
                        elif os.uname().sysname == "Darwin": # macOS
                            os.system(f'open "{caminho_recibo}"')
                        else: # Linux
                            os.system(f'xdg-open "{caminho_recibo}"')
                    except Exception as e:
                        messagebox.showwarning("Erro ao Abrir", f"Não foi possível abrir o PDF automaticamente: {e}")
            else:
                messagebox.showerror("Erro Recibo", "Falha ao gerar o recibo em PDF.")

            limpar_venda()
            atualizar_lista_estoque() # Atualiza estoque visualmente
            pesquisar_produto_interface("") # Atualiza lista cadastro (estoque mudou)
        else:
            messagebox.showerror("Erro", "Falha ao registrar a venda no banco de dados.")

# --- Funções da Aba Estoque --- #
def atualizar_lista_estoque():
    try:
        produtos = db.listar_produtos()
        tree_estoque.delete(*tree_estoque.get_children())
        for prod in produtos:
            tag = "ok"
            if prod["estoque"] <= prod["estoque_minimo"]:
                tag = "baixo"
            tree_estoque.insert("", tk.END, values=(
                prod["id"],
                prod["codigo_barras"],
                prod["nome"],
                prod["estoque"],
                prod["estoque_minimo"]
            ), tags=(tag,))
    except tk.TclError:
        pass # Ignora erro se widget não existe mais
    except Exception as e:
        messagebox.showerror("Erro ao Atualizar Estoque", f"Ocorreu um erro: {str(e)}")

def registrar_entrada_interface():
    try:
        produto_id = validar_int(entry_produto_id_est.get().strip())
        quantidade = validar_int(entry_qtd_entrada.get().strip())
        motivo = entry_motivo_entrada.get().strip()

        if quantidade <= 0:
            messagebox.showwarning("Quantidade Inválida", "A quantidade de entrada deve ser maior que zero.")
            return

        # Verificar se produto existe
        produto = db.buscar_produto_por_id(produto_id)
        if not produto:
            messagebox.showerror("Erro", f"Produto com ID {produto_id} não encontrado.")
            return

        if db.registrar_movimentacao_estoque(produto_id, "entrada", quantidade, motivo, usuario_logado["id"]):
            messagebox.showinfo("Sucesso", f"Entrada de {quantidade} unidade(s) para o produto '{produto['nome']}' registrada com sucesso!")
            entry_produto_id_est.delete(0, tk.END)
            entry_qtd_entrada.delete(0, tk.END)
            entry_motivo_entrada.delete(0, tk.END)
            atualizar_lista_estoque() # Atualiza a lista visual
            pesquisar_produto_interface("") # Atualiza lista cadastro (estoque mudou)
        else:
            messagebox.showerror("Erro", "Falha ao registrar a entrada no banco de dados.")

    except ValueError as e:
        messagebox.showerror("Erro de Entrada", str(e))
    except tk.TclError:
        messagebox.showerror("Erro Interface", "Erro ao ler campos de entrada de estoque.")
    except Exception as e:
        messagebox.showerror("Erro Inesperado", f"Ocorreu um erro: {str(e)}")

# --- Funções da Aba Relatórios --- #
relatorio_atual_dados = []
relatorio_atual_colunas = []
relatorio_atual_titulo = ""

def gerar_relatorio_interface():
    global relatorio_atual_dados, relatorio_atual_colunas, relatorio_atual_titulo

    try:
        tipo = combo_relatorio.get()
        data_ini_str = entry_data_ini.get()
        data_fim_str = entry_data_fim.get()
        data_ini = formatar_data(data_ini_str)
        data_fim = formatar_data(data_fim_str)
    except ValueError as e:
        messagebox.showerror("Data Inválida", str(e))
        return
    except tk.TclError:
        messagebox.showerror("Erro Interface", "Erro ao ler opções de relatório.")
        return

    # Limpar treeview anterior
    try:
        tree_relatorio.delete(*tree_relatorio.get_children())
        # Remover colunas antigas
        for col in tree_relatorio["columns"]:
             tree_relatorio.heading(col, text="")
             tree_relatorio.column(col, width=0, minwidth=0, stretch=tk.NO)
        tree_relatorio["columns"] = ()
    except tk.TclError:
        pass # Ignora erro se widget não existe mais

    relatorio_atual_dados = []
    relatorio_atual_colunas = []
    relatorio_atual_titulo = f"{tipo} ({data_ini_str} a {data_fim_str})"

    try:
        if tipo == "Vendas por Período":
            dados = db.obter_vendas_por_periodo(data_ini, data_fim)
            colunas = ("ID Venda", "Data/Hora", "Usuário", "Pagamento", "Parcelas", "Total")
            tree_relatorio["columns"] = colunas
            for col in colunas:
                tree_relatorio.heading(col, text=col)
                tree_relatorio.column(col, anchor=tk.W, width=120)
            tree_relatorio.column("Total", anchor=tk.E, width=100)
            tree_relatorio.column("ID Venda", anchor=tk.CENTER, width=80)
            tree_relatorio.column("Parcelas", anchor=tk.CENTER, width=60)

            total_geral_vendas = 0
            for venda in dados:
                # Formatar data/hora se for objeto datetime
                data_hora_fmt = venda["data_hora"]
                if isinstance(data_hora_fmt, str):
                     try:
                         data_hora_fmt = datetime.datetime.fromisoformat(data_hora_fmt).strftime("%d/%m/%Y %H:%M")
                     except ValueError:
                         pass # Mantém como string se não for formato ISO
                elif isinstance(data_hora_fmt, datetime.datetime):
                     data_hora_fmt = data_hora_fmt.strftime("%d/%m/%Y %H:%M")

                tree_relatorio.insert("", tk.END, values=(
                    venda["id"],
                    data_hora_fmt,
                    venda["usuario"],
                    venda["forma_pagamento"],
                    venda["parcelas"],
                    f"R$ {venda['total']:.2f}"
                ))
                total_geral_vendas += venda["total"]
            # Adicionar linha de total
            tree_relatorio.insert("", tk.END, values=("", "", "", "", "TOTAL:", f"R$ {total_geral_vendas:.2f}"), tags=("total_row",))
            tree_relatorio.tag_configure("total_row", font=("Arial", 10, "bold"))
            relatorio_atual_dados = dados # Salva dados brutos para exportação
            relatorio_atual_colunas = list(colunas)

        elif tipo == "Produtos Mais Vendidos":
            dados = db.obter_produtos_mais_vendidos(data_ini, data_fim)
            colunas = ("Produto", "Quantidade Vendida")
            tree_relatorio["columns"] = colunas
            tree_relatorio.heading("Produto", text="Produto")
            tree_relatorio.heading("Quantidade Vendida", text="Quantidade Vendida")
            tree_relatorio.column("Produto", anchor=tk.W, width=300)
            tree_relatorio.column("Quantidade Vendida", anchor=tk.CENTER, width=150)

            for prod in dados:
                tree_relatorio.insert("", tk.END, values=(
                    prod["nome"],
                    prod["total_vendido"]
                ))
            relatorio_atual_dados = dados
            relatorio_atual_colunas = list(colunas)

        elif tipo == "Movimentações de Estoque":
            # TODO: Adicionar opção de filtrar por produto?
            dados = db.obter_movimentacoes_estoque(data_ini, data_fim)
            colunas = ("Data/Hora", "Produto", "Tipo", "Quantidade", "Motivo", "Usuário")
            tree_relatorio["columns"] = colunas
            for col in colunas:
                tree_relatorio.heading(col, text=col)
                tree_relatorio.column(col, anchor=tk.W, width=150)
            tree_relatorio.column("Tipo", anchor=tk.CENTER, width=80)
            tree_relatorio.column("Quantidade", anchor=tk.CENTER, width=80)

            for mov in dados:
                # Formatar data/hora
                data_hora_fmt = mov["data_hora"]
                if isinstance(data_hora_fmt, str):
                     try:
                         data_hora_fmt = datetime.datetime.fromisoformat(data_hora_fmt).strftime("%d/%m/%Y %H:%M")
                     except ValueError:
                         pass
                elif isinstance(data_hora_fmt, datetime.datetime):
                     data_hora_fmt = data_hora_fmt.strftime("%d/%m/%Y %H:%M")

                tree_relatorio.insert("", tk.END, values=(
                    data_hora_fmt,
                    mov["produto"],
                    mov["tipo"],
                    mov["quantidade"],
                    mov["motivo"],
                    mov["usuario"] if mov["usuario"] else "Sistema"
                ))
            relatorio_atual_dados = dados
            relatorio_atual_colunas = list(colunas)

    except tk.TclError:
         pass # Ignora erro se widget não existe mais
    except Exception as e:
        messagebox.showerror("Erro ao Gerar Relatório", f"Ocorreu um erro: {str(e)}")
        relatorio_atual_dados = []
        relatorio_atual_colunas = []
        relatorio_atual_titulo = ""

def exportar_pdf_interface():
    if not relatorio_atual_dados:
        messagebox.showwarning("Sem Dados", "Gere um relatório antes de exportar.")
        return

    filepath = filedialog.asksaveasfilename(
        defaultextension=".pdf",
        filetypes=[("PDF Files", "*.pdf"), ("All Files", "*.*")],
        title="Salvar Relatório PDF",
        initialfile=f"relatorio_{combo_relatorio.get().lower().replace(' ', '_')}.pdf"
    )

    if not filepath:
        return # Usuário cancelou

    try:
        # Passar os dados brutos para a função de exportação
        if relatorios.exportar_para_pdf(relatorio_atual_titulo, relatorio_atual_colunas, relatorio_atual_dados, filepath):
            messagebox.showinfo("Sucesso", f"Relatório salvo em:\n{filepath}")
            # Perguntar se quer abrir
            if messagebox.askyesno("Abrir PDF", "Deseja abrir o arquivo PDF gerado?"):
                 try:
                     if os.name == "nt": os.startfile(filepath)
                     elif os.uname().sysname == "Darwin": os.system(f'open "{filepath}"')
                     else: os.system(f'xdg-open "{filepath}"')
                 except Exception as e:
                     messagebox.showwarning("Erro ao Abrir", f"Não foi possível abrir o PDF automaticamente: {e}")
        else:
            messagebox.showerror("Erro", "Falha ao exportar relatório para PDF.")
    except Exception as e:
        messagebox.showerror("Erro Exportação PDF", f"Ocorreu um erro inesperado: {str(e)}")

def exportar_excel_interface():
    if not relatorio_atual_dados:
        messagebox.showwarning("Sem Dados", "Gere um relatório antes de exportar.")
        return

    filepath = filedialog.asksaveasfilename(
        defaultextension=".xlsx",
        filetypes=[("Excel Files", "*.xlsx"), ("All Files", "*.*")],
        title="Salvar Relatório Excel",
        initialfile=f"relatorio_{combo_relatorio.get().lower().replace(' ', '_')}.xlsx"
    )

    if not filepath:
        return # Usuário cancelou

    try:
        # Passar os dados brutos para a função de exportação
        if relatorios.exportar_para_excel(relatorio_atual_titulo, relatorio_atual_colunas, relatorio_atual_dados, filepath):
            messagebox.showinfo("Sucesso", f"Relatório salvo em:\n{filepath}")
            # Perguntar se quer abrir
            if messagebox.askyesno("Abrir Excel", "Deseja abrir o arquivo Excel gerado?"):
                 try:
                     if os.name == "nt": os.startfile(filepath)
                     elif os.uname().sysname == "Darwin": os.system(f'open "{filepath}"')
                     else: os.system(f'xdg-open "{filepath}"')
                 except Exception as e:
                     messagebox.showwarning("Erro ao Abrir", f"Não foi possível abrir o Excel automaticamente: {e}")
        else:
            messagebox.showerror("Erro", "Falha ao exportar relatório para Excel.")
    except Exception as e:
        messagebox.showerror("Erro Exportação Excel", f"Ocorreu um erro inesperado: {str(e)}")

# --- Funções de Permissão --- #
def aplicar_permissoes(notebook_abas, tipo_usuario):
    if tipo_usuario != "admin":
        try:
            # Tentar desabilitar por texto (mais robusto se a ordem mudar)
            for i in range(notebook_abas.index("end")):
                tab_text = notebook_abas.tab(i, "text")
                if tab_text in ["Cadastro de Produto", "Controle de Estoque", "Relatórios"]:
                    notebook_abas.tab(i, state="disabled")
        except tk.TclError as e:
             print(f"Erro ao desabilitar abas por texto: {e}")
             messagebox.showerror("Erro Permissões", "Não foi possível aplicar as permissões corretamente.")

# --- Inicialização --- #
if __name__ == "__main__":
    # Criar banco e tabelas se não existirem
    db.criar_tabelas()

    # Janela de Login
    janela_login = tk.Tk()
    janela_login.title("Login - Sistema Loja")
    janela_login.geometry("300x200")
    janela_login.resizable(False, False)

    frame_login = ttk.Frame(janela_login, padding="20")
    frame_login.pack(expand=True)

    ttk.Label(frame_login, text="Usuário:").pack(pady=5)
    entry_usuario = ttk.Entry(frame_login, width=25)
    entry_usuario.pack()
    entry_usuario.focus()

    ttk.Label(frame_login, text="Senha:").pack(pady=5)
    entry_senha = ttk.Entry(frame_login, show="*", width=25)
    entry_senha.pack()

    # Bind Enter key to login function
    entry_usuario.bind("<Return>", lambda event: entry_senha.focus())
    entry_senha.bind("<Return>", lambda event: fazer_login())

    btn_entrar = ttk.Button(frame_login, text="Entrar", command=fazer_login, width=10)
    btn_entrar.pack(pady=20)

    janela_login.mainloop()

