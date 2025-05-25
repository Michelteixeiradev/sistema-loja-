# -*- coding: utf-8 -*-
import sqlite3
import datetime
import hashlib
import os

# --- Definição do Caminho do Banco de Dados ---
# Obtém o caminho absoluto do diretório onde este script (database.py) está
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
# Cria o caminho completo para o arquivo loja.db dentro desse diretório
DATABASE = os.path.join(SCRIPT_DIR, 'loja.db')
# ----------------------------------------------

def conectar_bd():
    """Conecta ao banco de dados SQLite."""
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row # Retorna dicionários em vez de tuplas
    return conn

def criar_tabelas():
    """Cria as tabelas do banco de dados se não existirem."""
    conn = conectar_bd()
    cursor = conn.cursor()

    # Tabela de Usuários
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS usuarios (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT NOT NULL,
        usuario TEXT UNIQUE NOT NULL,
        senha TEXT NOT NULL,
        tipo TEXT NOT NULL CHECK(tipo IN ('admin', 'vendedor'))
    )
    ''')

    # Tabela de Produtos
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS produtos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        codigo_barras TEXT UNIQUE,
        nome TEXT NOT NULL,
        preco_custo REAL,
        preco_venda REAL NOT NULL,
        estoque INTEGER NOT NULL DEFAULT 0,
        fornecedor TEXT,
        estoque_minimo INTEGER DEFAULT 5
    )
    ''')

    # Tabela de Vendas
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS vendas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        data_hora DATETIME DEFAULT CURRENT_TIMESTAMP,
        usuario_id INTEGER NOT NULL,
        forma_pagamento TEXT NOT NULL CHECK(forma_pagamento IN ('Dinheiro', 'Débito', 'Crédito')),
        parcelas INTEGER DEFAULT 1,
        total REAL NOT NULL,
        FOREIGN KEY (usuario_id) REFERENCES usuarios(id)
    )
    ''')

    # Tabela de Itens da Venda
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS itens_venda (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        venda_id INTEGER NOT NULL,
        produto_id INTEGER NOT NULL,
        quantidade INTEGER NOT NULL,
        preco_unitario REAL NOT NULL,
        FOREIGN KEY (venda_id) REFERENCES vendas(id) ON DELETE CASCADE, -- Cascata para limpar itens se venda for deletada
        FOREIGN KEY (produto_id) REFERENCES produtos(id) ON DELETE RESTRICT -- Impede excluir produto se estiver em item_venda
    )
    ''')

    # Tabela de Movimentações de Estoque
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS movimentacoes_estoque (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        produto_id INTEGER NOT NULL,
        tipo TEXT NOT NULL CHECK(tipo IN ('entrada', 'saida', 'inicial', 'ajuste')),
        quantidade INTEGER NOT NULL,
        data_hora DATETIME DEFAULT CURRENT_TIMESTAMP,
        motivo TEXT, -- Ex: 'Venda #123', 'Compra NF 456', 'Ajuste Inventário'
        usuario_id INTEGER,
        FOREIGN KEY (produto_id) REFERENCES produtos(id) ON DELETE CASCADE, -- Cascata se produto for deletado
        FOREIGN KEY (usuario_id) REFERENCES usuarios(id)
    )
    ''')

    # Adicionar usuário admin padrão se não existir
    cursor.execute("SELECT id FROM usuarios WHERE usuario = 'admin'") # Fechar parêntese aqui
    if not cursor.fetchone():
        senha_hash = hashlib.sha256('admin'.encode('utf-8')).hexdigest()
        cursor.execute("INSERT INTO usuarios (nome, usuario, senha, tipo) VALUES (?, ?, ?, ?)",
                       ('Administrador', 'admin', senha_hash, 'admin'))

    conn.commit()
    conn.close()

def hash_senha(senha):
    """Gera o hash SHA256 de uma senha."""
    return hashlib.sha256(senha.encode('utf-8')).hexdigest()

# --- Funções de Autenticação ---

def autenticar_usuario(usuario, senha):
    """Verifica as credenciais do usuário no banco de dados."""
    conn = conectar_bd()
    cursor = conn.cursor()
    senha_hash = hash_senha(senha)
    cursor.execute("SELECT id, nome, tipo FROM usuarios WHERE usuario = ? AND senha = ?", (usuario, senha_hash))
    resultado = cursor.fetchone()
    conn.close()
    if resultado:
        return dict(resultado)
    return None

# --- Funções CRUD Produtos ---

def adicionar_produto(codigo_barras, nome, preco_custo, preco_venda, estoque, fornecedor, estoque_minimo):
    """Adiciona um novo produto ao banco de dados."""
    conn = conectar_bd()
    cursor = conn.cursor()
    try:
        cursor.execute('''INSERT INTO produtos (codigo_barras, nome, preco_custo, preco_venda, estoque, fornecedor, estoque_minimo)
                      VALUES (?, ?, ?, ?, ?, ?, ?)''',
                      (codigo_barras, nome, preco_custo, preco_venda, estoque, fornecedor, estoque_minimo))
        produto_id = cursor.lastrowid
        # Registrar estoque inicial
        if estoque > 0:
            registrar_movimentacao_estoque(produto_id, 'inicial', estoque, motivo='Cadastro inicial')
        conn.commit()
        return True
    except sqlite3.IntegrityError: # Caso código de barras já exista
        return False
    finally:
        conn.close()

def listar_produtos(termo_busca=''):
    """Lista todos os produtos ou filtra por nome ou código."""
    conn = conectar_bd()
    cursor = conn.cursor()
    if termo_busca:
        cursor.execute("SELECT * FROM produtos WHERE nome LIKE ? OR codigo_barras LIKE ? ORDER BY nome", ('%'+termo_busca+'%', '%'+termo_busca+'%'))
    else:
        cursor.execute("SELECT * FROM produtos ORDER BY nome")
    produtos = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return produtos

def buscar_produto_por_id(produto_id):
    """Busca um produto pelo seu ID."""
    conn = conectar_bd()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM produtos WHERE id = ?", (produto_id,))
    produto = cursor.fetchone()
    conn.close()
    return dict(produto) if produto else None

def atualizar_produto(produto_id, codigo_barras, nome, preco_custo, preco_venda, estoque, fornecedor, estoque_minimo):
    """Atualiza os dados de um produto existente."""
    conn = conectar_bd()
    cursor = conn.cursor()
    try:
        cursor.execute('''UPDATE produtos SET
                      codigo_barras = ?, nome = ?, preco_custo = ?, preco_venda = ?, estoque = ?, fornecedor = ?, estoque_minimo = ?
                      WHERE id = ?''',
                      (codigo_barras, nome, preco_custo, preco_venda, estoque, fornecedor, estoque_minimo, produto_id))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False # Provavelmente código de barras duplicado
    finally:
        conn.close()

def excluir_produto(produto_id):
    """Exclui um produto do banco de dados. Retorna True se sucesso, False se falhar (provavelmente por restrição FK)."""
    conn = conectar_bd()
    cursor = conn.cursor()
    try:
        # Tenta excluir. Se o produto estiver em itens_venda, a restrição FK (ON DELETE RESTRICT) causará um erro.
        cursor.execute("DELETE FROM produtos WHERE id = ?", (produto_id,))
        # Se chegou aqui, a exclusão foi permitida (produto não estava em itens_venda)
        # Excluir movimentações de estoque relacionadas (ON DELETE CASCADE faz isso automaticamente, mas podemos garantir)
        cursor.execute("DELETE FROM movimentacoes_estoque WHERE produto_id = ?", (produto_id,))
        conn.commit()
        return True
    except sqlite3.IntegrityError as e:
        # Erro esperado se o produto estiver em itens_venda
        print(f"Erro de integridade ao excluir produto {produto_id} (provavelmente está em uma venda): {e}")
        conn.rollback()
        return False
    except Exception as e:
        print(f"Erro inesperado ao excluir produto {produto_id}: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()

def atualizar_estoque_produto(produto_id, quantidade_alteracao, tipo_movimentacao):
    """Atualiza o estoque de um produto (soma ou subtrai). Usado internamente por outras funções."""
    conn = conectar_bd()
    cursor = conn.cursor()
    if tipo_movimentacao == 'entrada':
        cursor.execute("UPDATE produtos SET estoque = estoque + ? WHERE id = ?", (quantidade_alteracao, produto_id))
    elif tipo_movimentacao == 'saida':
        cursor.execute("UPDATE produtos SET estoque = estoque - ? WHERE id = ?", (quantidade_alteracao, produto_id))
    else: # inicial ou ajuste - define o estoque diretamente (embora ajuste possa ser +/-)
         # Para simplificar, vamos tratar ajuste como entrada/saída manual via registrar_movimentacao_estoque
         pass
    conn.commit()
    conn.close()

# --- Funções de Venda ---

def registrar_venda(usuario_id, forma_pagamento, parcelas, total, itens_venda):
    """Registra uma nova venda e seus itens, atualizando o estoque."""
    conn = conectar_bd()
    cursor = conn.cursor()
    try:
        # Iniciar transação
        conn.execute('BEGIN TRANSACTION')

        # Registrar a venda
        cursor.execute('''INSERT INTO vendas (usuario_id, forma_pagamento, parcelas, total)
                      VALUES (?, ?, ?, ?)''',
                      (usuario_id, forma_pagamento, parcelas, total))
        venda_id = cursor.lastrowid

        # Registrar os itens da venda e atualizar estoque
        for item in itens_venda:
            # Verificar estoque novamente dentro da transação para segurança
            cursor.execute("SELECT estoque FROM produtos WHERE id = ?", (item['produto_id'],))
            estoque_atual = cursor.fetchone()['estoque']
            if item['quantidade'] > estoque_atual:
                raise ValueError(f"Estoque insuficiente para {item['nome']} no momento da finalização.")

            cursor.execute('''INSERT INTO itens_venda (venda_id, produto_id, quantidade, preco_unitario)
                          VALUES (?, ?, ?, ?)''',
                          (venda_id, item['produto_id'], item['quantidade'], item['preco']))

            # Atualizar estoque do produto
            cursor.execute("UPDATE produtos SET estoque = estoque - ? WHERE id = ?", (item['quantidade'], item['produto_id']))

            # Registrar saída no histórico de movimentações
            # Usando a mesma conexão para manter a transação
            registrar_movimentacao_estoque(item['produto_id'], 'saida', item['quantidade'],
                                           motivo=f'Venda #{venda_id}', usuario_id=usuario_id, conn_externa=conn)

        # Finalizar transação
        conn.commit()
        return venda_id
    except ValueError as ve:
        print(f"Erro ao registrar venda (ValueError): {ve}")
        conn.rollback()
        raise ve # Re-lança a exceção para ser tratada na interface
    except Exception as e:
        print(f"Erro geral ao registrar venda: {e}")
        conn.rollback()
        return None
    finally:
        conn.close()

# --- Funções de Estoque ---

def registrar_movimentacao_estoque(produto_id, tipo, quantidade, motivo='', usuario_id=None, conn_externa=None):
    """Registra uma movimentação de estoque (entrada, saida, inicial, ajuste)."""
    # Permite usar uma conexão externa para transações (como em registrar_venda)
    is_external_conn = conn_externa is not None
    conn = conn_externa if is_external_conn else conectar_bd()
    cursor = conn.cursor()

    try:
        # Insere o registro da movimentação
        cursor.execute('''INSERT INTO movimentacoes_estoque (produto_id, tipo, quantidade, motivo, usuario_id)
                      VALUES (?, ?, ?, ?, ?)''',
                      (produto_id, tipo, quantidade, motivo, usuario_id))

        # Atualiza o estoque na tabela produtos APENAS se for entrada manual ou ajuste
        # Saída é tratada na venda, Inicial é tratado no cadastro.
        if tipo == 'entrada':
             cursor.execute("UPDATE produtos SET estoque = estoque + ? WHERE id = ?", (quantidade, produto_id))
        # Adicionar lógica para 'ajuste' se necessário (ex: ajuste positivo/negativo)
        # elif tipo == 'ajuste':
        #    cursor.execute("UPDATE produtos SET estoque = estoque + ? WHERE id = ?", (quantidade, produto_id)) # Exemplo: ajuste positivo

        if not is_external_conn: # Só commita se não for conexão externa
            conn.commit()
        return True
    except Exception as e:
        print(f"Erro ao registrar movimentação de estoque ({tipo}): {e}")
        if not is_external_conn:
            conn.rollback()
        # Se for conexão externa, o rollback deve ser feito pela função chamadora (registrar_venda)
        return False
    finally:
        if not is_external_conn:
            conn.close()

def obter_estoque_atual(produto_id):
    """Obtém o estoque atual de um produto."""
    conn = conectar_bd()
    cursor = conn.cursor()
    cursor.execute("SELECT estoque FROM produtos WHERE id = ?", (produto_id,))
    resultado = cursor.fetchone()
    conn.close()
    return resultado['estoque'] if resultado else 0

# --- Funções de Relatório ---

def obter_vendas_por_periodo(data_inicio, data_fim):
    """Busca vendas realizadas dentro de um período."""
    conn = conectar_bd()
    cursor = conn.cursor()
    # Adiciona a hora final para incluir o dia todo
    data_fim_ajustada = f"{data_fim} 23:59:59"
    cursor.execute('''SELECT v.id, v.data_hora, u.nome as usuario, v.forma_pagamento, v.parcelas, v.total
                  FROM vendas v
                  JOIN usuarios u ON v.usuario_id = u.id
                  WHERE v.data_hora BETWEEN ? AND ?
                  ORDER BY v.data_hora DESC''',
                  (data_inicio, data_fim_ajustada))
    vendas = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return vendas

def obter_itens_venda(venda_id):
    """Busca os itens de uma venda específica."""
    conn = conectar_bd()
    cursor = conn.cursor()
    cursor.execute('''SELECT p.nome, iv.quantidade, iv.preco_unitario
                  FROM itens_venda iv
                  JOIN produtos p ON iv.produto_id = p.id
                  WHERE iv.venda_id = ?''',
                  (venda_id,))
    itens = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return itens

def obter_produtos_mais_vendidos(data_inicio, data_fim, limite=10):
    """Busca os produtos mais vendidos em um período."""
    conn = conectar_bd()
    cursor = conn.cursor()
    data_fim_ajustada = f"{data_fim} 23:59:59"
    cursor.execute('''SELECT p.nome, SUM(iv.quantidade) as total_vendido
                  FROM itens_venda iv
                  JOIN vendas v ON iv.venda_id = v.id
                  JOIN produtos p ON iv.produto_id = p.id
                  WHERE v.data_hora BETWEEN ? AND ?
                  GROUP BY p.id, p.nome
                  ORDER BY total_vendido DESC
                  LIMIT ?''',
                  (data_inicio, data_fim_ajustada, limite))
    produtos = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return produtos

def obter_movimentacoes_estoque(data_inicio, data_fim, produto_id=None):
    """Busca as movimentações de estoque em um período, opcionalmente por produto."""
    conn = conectar_bd()
    cursor = conn.cursor()
    data_fim_ajustada = f"{data_fim} 23:59:59"
    query = '''SELECT m.data_hora, p.nome as produto, m.tipo, m.quantidade, m.motivo, u.nome as usuario
             FROM movimentacoes_estoque m
             JOIN produtos p ON m.produto_id = p.id
             LEFT JOIN usuarios u ON m.usuario_id = u.id
             WHERE m.data_hora BETWEEN ? AND ?'''
    params = [data_inicio, data_fim_ajustada]

    if produto_id:
        query += " AND m.produto_id = ?"
        params.append(produto_id)

    query += " ORDER BY m.data_hora DESC"

    cursor.execute(query, params)
    movimentacoes = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return movimentacoes

# --- Inicialização ---

# Descomente a linha abaixo APENAS se precisar recriar o banco do zero
# import os; os.remove(DATABASE) if os.path.exists(DATABASE) else None

criar_tabelas() # Garante que as tabelas existam ao importar o módulo
# print("Banco de dados inicializado e tabelas criadas/verificadas.") # Opcional: remover print

