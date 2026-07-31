"""
Sistema de Caixa — Prime Informática
Duas lojas: 5/7 e 4/2
Autor: desenvolvido com Claude
"""

import sqlite3
import os
from datetime import date, datetime
from zoneinfo import ZoneInfo

BSB = ZoneInfo("America/Sao_Paulo")
from contextlib import contextmanager

import pandas as pd
import streamlit as st

# ============================================================
# CONFIGURAÇÃO
# ============================================================

st.set_page_config(
    page_title="Prime Informática — Caixa",
    page_icon="📱",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# CSS personalizado
st.markdown("""
<style>
    /* Oculta menu e rodapé do Streamlit */
    #MainMenu, footer, header { visibility: hidden; }

    /* Fundo geral */
    .stApp { background-color: #f0f2f6; }

    /* Forçar labels e textos visíveis */
    label, .stTextInput label, .stSelectbox label,
    .stNumberInput label, .stDateInput label,
    p, span, div { color: #1a237e !important; }

    /* Inputs com fundo branco e texto escuro */
    .stTextInput input, .stNumberInput input,
    [data-baseweb="input"] input {
        background-color: white !important;
        color: #1a1a1a !important;
        border: 1.5px solid #c5cae9 !important;
    }

    /* Selects — forçar visibilidade */
    [data-baseweb="select"] > div,
    [data-baseweb="select"] > div > div {
        background-color: white !important;
        border: 1.5px solid #c5cae9 !important;
        color: #1a1a1a !important;
    }
    [data-baseweb="select"] span,
    [data-baseweb="select"] div,
    [data-baseweb="select"] input,
    [data-baseweb="select"] * {
        color: #1a1a1a !important;
    }
    /* Placeholder */
    [data-baseweb="select"] [class*="placeholder"] {
        color: #888 !important;
    }
    /* Dropdown aberto */
    [data-baseweb="menu"],
    [data-baseweb="menu"] li,
    [data-baseweb="menu"] ul,
    [data-baseweb="popover"] *,
    [role="listbox"] * {
        color: #1a1a1a !important;
        background-color: white !important;
    }
    [data-baseweb="menu"] li:hover,
    [role="option"]:hover {
        background-color: #e8eaf6 !important;
    }

    /* Cabeçalho — manter branco */
    .cab, .cab * { color: white !important; }

    /* Métricas — manter cores */
    [data-testid="stMetricValue"] { color: #1a237e !important; }
    [data-testid="stMetricLabel"] { color: #555 !important; }

    /* Fundo dos tabs */
    [data-testid="stTabs"] { background: white; border-radius: 10px; padding: 8px; }

    /* Botão salvar */
    .stFormSubmitButton button {
        background-color: #1565c0 !important;
        color: white !important;
        font-weight: 700 !important;
    }

    /* Cabeçalho personalizado */
    .cab {
        background: #b71c1c;
        color: white;
        padding: 14px 24px;
        border-radius: 10px;
        display: flex;
        align-items: center;
        justify-content: space-between;
        margin-bottom: 20px;
        box-shadow: 0 2px 8px rgba(183,28,28,0.3);
    }
    .cab-titulo { font-size: 20px; font-weight: 700; }
    .cab-loja   { font-size: 13px; opacity: 0.85; }

    /* Cards de métricas */
    .metric-card {
        background: white;
        border-radius: 10px;
        padding: 16px;
        box-shadow: 0 1px 6px rgba(0,0,0,0.08);
        border-left: 4px solid #1565c0;
        margin-bottom: 12px;
    }
    .metric-card.verde  { border-left-color: #2e7d32; }
    .metric-card.verm   { border-left-color: #c62828; }
    .metric-card.amar   { border-left-color: #f57f17; }
    .metric-label { font-size: 11px; color: #666; text-transform: uppercase; letter-spacing: 0.5px; }
    .metric-value { font-size: 24px; font-weight: 700; color: #1a237e; margin-top: 4px; }
    .metric-card.verde .metric-value { color: #2e7d32; }
    .metric-card.verm  .metric-value { color: #c62828; }

    /* Badges de pagamento */
    .badge {
        display: inline-block; padding: 3px 10px;
        border-radius: 20px; font-size: 12px; font-weight: 600;
    }
    .badge-pix      { background: #e8f5e9; color: #2e7d32; }
    .badge-dinheiro { background: #fff8e1; color: #f57f17; }
    .badge-debito   { background: #e3f2fd; color: #1565c0; }
    .badge-credito  { background: #fce4ec; color: #c62828; }
    .badge-transf   { background: #f3e5f5; color: #6a1b9a; }
    .badge-outros   { background: #f5f5f5; color: #555; }

    /* Resultado fechamento */
    .fech-ok   { background: #e8f5e9; color: #2e7d32; padding: 14px; border-radius: 8px; text-align: center; font-weight: 700; font-size: 16px; }
    .fech-warn { background: #fff8e1; color: #f57f17; padding: 14px; border-radius: 8px; text-align: center; font-weight: 700; font-size: 16px; }
    .fech-err  { background: #ffebee; color: #c62828; padding: 14px; border-radius: 8px; text-align: center; font-weight: 700; font-size: 16px; }

    div[data-testid="stTabs"] button { font-size: 14px; font-weight: 600; }
</style>
""", unsafe_allow_html=True)

# ============================================================
# USUÁRIOS
# ============================================================

USUARIOS = {
    "loja57":  {"senha": "prime57",  "loja": "Prime Informática 5/7",  "cod": "57",  "admin": False},
    "loja42":  {"senha": "prime42",  "loja": "Prime Informática 4/2",  "cod": "42",  "admin": False},
    "admin":   {"senha": "primeadm", "loja": "Administrador",           "cod": "admin", "admin": True},
}

# ============================================================
# BANCO DE DADOS
# ============================================================

DB_DIR = "data"
os.makedirs(DB_DIR, exist_ok=True)

def get_db(cod_loja: str) -> str:
    return os.path.join(DB_DIR, f"caixa_{cod_loja}.db")

@contextmanager
def conn(cod_loja: str):
    c = sqlite3.connect(get_db(cod_loja), check_same_thread=False)
    c.row_factory = sqlite3.Row
    try:
        yield c
        c.commit()
    finally:
        c.close()

def init_db(cod_loja: str):
    with conn(cod_loja) as c:
        c.execute("""
            CREATE TABLE IF NOT EXISTS vendas (
                id        INTEGER PRIMARY KEY AUTOINCREMENT,
                data      TEXT NOT NULL,
                hora      TEXT NOT NULL,
                descricao TEXT NOT NULL,
                categoria TEXT NOT NULL,
                pagamento TEXT NOT NULL,
                valor     REAL NOT NULL,
                vendedor  TEXT,
                obs       TEXT,
                criado_em TEXT DEFAULT (datetime('now','localtime'))
            )
        """)
        c.execute("""
            CREATE TABLE IF NOT EXISTS despesas (
                id        INTEGER PRIMARY KEY AUTOINCREMENT,
                data      TEXT NOT NULL,
                hora      TEXT NOT NULL,
                descricao TEXT NOT NULL,
                categoria TEXT,
                valor     REAL NOT NULL,
                obs       TEXT,
                criado_em TEXT DEFAULT (datetime('now','localtime'))
            )
        """)

# ============================================================
# HELPERS
# ============================================================

def brl(v: float) -> str:
    return f"R$ {v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

def badge_pag(p: str) -> str:
    m = {
        "Pix": "pix", "Dinheiro": "dinheiro",
        "Cartão Débito": "debito", "Cartão Crédito": "credito",
        "Transferência": "transf",
    }
    cls = m.get(p, "outros")
    return f'<span class="badge badge-{cls}">{p}</span>'

CATEGORIAS = [
    "Capinhas", "Películas", "Cabos", "Carregadores", "Fontes",
    "Fones", "Relógios", "Assistência Técnica", "Caixas de Som",
    "Películas Hidrogel", "Suportes", "Outros",
]

PAGAMENTOS = [
    "Pix", "Dinheiro", "Cartão Débito", "Cartão Crédito",
    "Transferência", "Crediário", "Outros",
]

CAT_DESPESA = [
    "Fornecedor", "Aluguel", "Energia", "Internet",
    "Material", "Manutenção", "Transporte", "Outros",
]

# ============================================================
# LOGIN
# ============================================================

def tela_login():
    col1, col2, col3 = st.columns([1, 1.2, 1])
    with col2:
        st.markdown("""
        <div style="background:#b71c1c;color:white;padding:24px;border-radius:12px;text-align:center;margin-bottom:24px;box-shadow:0 4px 16px rgba(183,28,28,0.3)">
            <div style="font-size:32px;margin-bottom:6px">📱</div>
            <div style="font-size:22px;font-weight:700">Prime Informática</div>
            <div style="font-size:13px;opacity:.8;margin-top:4px">Sistema de Caixa</div>
        </div>
        """, unsafe_allow_html=True)

        with st.form("login"):
            usuario = st.text_input("Usuário", placeholder="loja57 ou loja42")
            senha   = st.text_input("Senha", type="password", placeholder="••••••••")
            entrar  = st.form_submit_button("Entrar →", use_container_width=True)

        if entrar:
            u = USUARIOS.get(usuario)
            if u and u["senha"] == senha:
                st.session_state["usuario"] = usuario
                st.session_state["loja"]    = u["loja"]
                st.session_state["cod"]     = u["cod"]
                st.session_state["admin"]   = u["admin"]
                if not u["admin"]:
                    init_db(u["cod"])
                st.rerun()
            else:
                st.error("Usuário ou senha incorretos.")

# ============================================================
# CABEÇALHO
# ============================================================

def cabecalho():
    loja = st.session_state["loja"]
    agora = datetime.now(BSB).strftime("%d/%m/%Y  %H:%M")
    st.markdown(f"""
    <div class="cab">
        <div>
            <div class="cab-titulo">📱 Prime Informática — Sistema de Caixa</div>
            <div class="cab-loja">🏪 {loja}</div>
        </div>
        <div style="text-align:right">
            <div style="font-size:14px;opacity:.85">{agora}</div>
            <div style="font-size:11px;opacity:.6;margin-top:2px">Dados salvos automaticamente</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

# ============================================================
# ABA: NOVA VENDA
# ============================================================

def aba_nova_venda(cod: str):
    st.markdown("### 🛒 Registrar Nova Venda")

    with st.form("nova_venda", clear_on_submit=True):
        c1, c2 = st.columns(2)
        with c1:
            descricao = st.text_input("📝 Descrição do Produto *", placeholder="Ex: Capinha iPhone 13 preta")
            categoria = st.selectbox("📦 Categoria *", CATEGORIAS)
            vendedor  = st.text_input("👤 Vendedor (opcional)")
        with c2:
            pagamento = st.selectbox("💳 Forma de Pagamento *", PAGAMENTOS)
            valor     = st.number_input("💵 Valor (R$) *", min_value=0.0, step=0.50, format="%.2f")
            obs       = st.text_input("💬 Observação (opcional)")

        salvar = st.form_submit_button("✅ Salvar Venda", use_container_width=True, type="primary")

    if salvar:
        erros = []
        if not descricao.strip(): erros.append("Descrição")
        if not categoria:         erros.append("Categoria")
        if not pagamento:         erros.append("Forma de Pagamento")
        if valor <= 0:            erros.append("Valor")

        if erros:
            st.error(f"⚠️ Preencha: {', '.join(erros)}")
        else:
            hoje = date.today().isoformat()
            hora = datetime.now(BSB).strftime("%H:%M")
            with conn(cod) as c:
                c.execute(
                    "INSERT INTO vendas (data,hora,descricao,categoria,pagamento,valor,vendedor,obs) VALUES (?,?,?,?,?,?,?,?)",
                    (hoje, hora, descricao.strip(), categoria, pagamento, valor, vendedor.strip(), obs.strip())
                )
            st.success(f"✅ Venda salva! **{descricao}** — {brl(valor)} via {pagamento}")
            st.balloons()

# ============================================================
# ABA: CAIXA DO DIA
# ============================================================

def aba_caixa_dia(cod: str):
    st.markdown("### 💰 Caixa do Dia")

    hoje = date.today().isoformat()

    with conn(cod) as c:
        vendas   = pd.DataFrame(c.execute("SELECT * FROM vendas WHERE data=?", (hoje,)).fetchall(),
                                columns=["id","data","hora","descricao","categoria","pagamento","valor","vendedor","obs","criado_em"])
        despesas = pd.DataFrame(c.execute("SELECT * FROM despesas WHERE data=?", (hoje,)).fetchall(),
                                columns=["id","data","hora","descricao","categoria","valor","obs","criado_em"])

    total_v   = vendas["valor"].sum() if not vendas.empty else 0
    total_d   = despesas["valor"].sum() if not despesas.empty else 0
    resultado = total_v - total_d
    ticket    = vendas["valor"].mean() if not vendas.empty else 0
    maior     = vendas["valor"].max() if not vendas.empty else 0
    qtde      = len(vendas)

    # Métricas
    c1, c2, c3, c4, c5, c6 = st.columns(6)
    with c1:
        st.metric("💵 Total Vendido", brl(total_v))
    with c2:
        st.metric("🛒 Qtde Vendas", qtde)
    with c3:
        st.metric("🎯 Ticket Médio", brl(ticket))
    with c4:
        st.metric("⬆️ Maior Venda", brl(maior))
    with c5:
        st.metric("💸 Despesas", brl(total_d))
    with c6:
        st.metric("📊 Resultado", brl(resultado), delta=f"{brl(resultado)}" if resultado != 0 else None)

    st.divider()

    # Por pagamento
    st.markdown("**💳 Por Forma de Pagamento**")
    cols = st.columns(len(PAGAMENTOS))
    for i, pag in enumerate(PAGAMENTOS):
        tot = vendas[vendas["pagamento"] == pag]["valor"].sum() if not vendas.empty else 0
        with cols[i]:
            st.metric(pag, brl(tot))

    st.divider()

    # Últimas vendas
    st.markdown("**📋 Vendas de Hoje**")
    if vendas.empty:
        st.info("Nenhuma venda registrada hoje ainda.")
    else:
        df_show = vendas[["hora","descricao","categoria","pagamento","valor"]].copy()
        df_show["valor"] = df_show["valor"].apply(brl)
        df_show.columns = ["Hora","Descrição","Categoria","Pagamento","Valor"]
        st.dataframe(df_show[::-1].reset_index(drop=True), use_container_width=True, hide_index=True)

# ============================================================
# ABA: HISTÓRICO
# ============================================================

def aba_historico(cod: str):
    st.markdown("### 📋 Histórico de Vendas")

    with conn(cod) as c:
        vendas = pd.DataFrame(
            c.execute("SELECT * FROM vendas ORDER BY data DESC, hora DESC").fetchall(),
            columns=["id","data","hora","descricao","categoria","pagamento","valor","vendedor","obs","criado_em"]
        )

    if vendas.empty:
        st.info("Nenhuma venda registrada ainda.")
        return

    # Filtros
    f1, f2, f3, f4 = st.columns([1.2, 1.2, 1.2, 0.6])
    with f1:
        datas = ["Todas"] + sorted(vendas["data"].unique().tolist(), reverse=True)
        f_data = st.selectbox("📅 Data", datas)
    with f2:
        f_cat = st.selectbox("📦 Categoria", ["Todas"] + CATEGORIAS)
    with f3:
        f_pag = st.selectbox("💳 Pagamento", ["Todos"] + PAGAMENTOS)
    with f4:
        st.markdown("<div style='margin-top:28px'>", unsafe_allow_html=True)
        limpar = st.button("✕ Limpar", use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

    df = vendas.copy()
    if f_data != "Todas": df = df[df["data"] == f_data]
    if f_cat  != "Todas": df = df[df["categoria"] == f_cat]
    if f_pag  != "Todos": df = df[df["pagamento"] == f_pag]

    total = df["valor"].sum()
    st.markdown(f"**{len(df)} venda(s) — Total: {brl(total)}**")

    # Exportar
    if not df.empty:
        csv = df[["data","hora","descricao","categoria","pagamento","valor","vendedor","obs"]].copy()
        csv.columns = ["Data","Hora","Descrição","Categoria","Pagamento","Valor","Vendedor","Observação"]
        csv["Valor"] = csv["Valor"].apply(lambda v: f"R$ {v:.2f}".replace(".", ","))
        st.download_button(
            "⬇️ Exportar CSV",
            csv.to_csv(index=False, sep=";", encoding="utf-8-sig"),
            file_name=f"vendas_{date.today()}.csv",
            mime="text/csv",
        )

    # Tabela com botão de excluir
    for _, row in df.iterrows():
        c1, c2, c3, c4, c5, c6, c7, c8 = st.columns([1.2, 0.7, 2.5, 1.5, 1.5, 1, 1, 0.4])
        with c1: st.write(pd.to_datetime(row["data"]).strftime("%d/%m/%Y"))
        with c2: st.write(row["hora"])
        with c3: st.write(row["descricao"])
        with c4: st.write(row["categoria"])
        with c5: st.write(row["pagamento"])
        with c6: st.write(brl(row["valor"]))
        with c7: st.write(row["vendedor"] or "—")
        with c8:
            if st.button("✕", key=f"del_{row['id']}", help="Excluir"):
                with conn(cod) as c:
                    c.execute("DELETE FROM vendas WHERE id=?", (row["id"],))
                st.rerun()
        st.divider()

# ============================================================
# ABA: DESPESAS
# ============================================================

def aba_despesas(cod: str):
    st.markdown("### 💸 Despesas")

    with st.form("nova_despesa", clear_on_submit=True):
        c1, c2 = st.columns(2)
        with c1:
            desc  = st.text_input("📝 Descrição *", placeholder="Ex: Compra de capas")
            cat   = st.selectbox("📦 Categoria", CAT_DESPESA)
        with c2:
            valor = st.number_input("💵 Valor (R$) *", min_value=0.0, step=0.50, format="%.2f")
            obs   = st.text_input("💬 Observação (opcional)")

        salvar = st.form_submit_button("✅ Salvar Despesa", use_container_width=True, type="primary")

    if salvar:
        if not desc.strip() or valor <= 0:
            st.error("⚠️ Preencha a descrição e o valor.")
        else:
            hoje = date.today().isoformat()
            hora = datetime.now(BSB).strftime("%H:%M")
            with conn(cod) as c:
                c.execute(
                    "INSERT INTO despesas (data,hora,descricao,categoria,valor,obs) VALUES (?,?,?,?,?,?)",
                    (hoje, hora, desc.strip(), cat, valor, obs.strip())
                )
            st.success(f"✅ Despesa registrada! {desc} — {brl(valor)}")

    st.divider()
    st.markdown("**📋 Despesas de Hoje**")

    hoje = date.today().isoformat()
    with conn(cod) as c:
        desp = pd.DataFrame(
            c.execute("SELECT * FROM despesas WHERE data=? ORDER BY hora DESC", (hoje,)).fetchall(),
            columns=["id","data","hora","descricao","categoria","valor","obs","criado_em"]
        )

    if desp.empty:
        st.info("Nenhuma despesa hoje.")
    else:
        total_d = desp["valor"].sum()
        st.markdown(f"**Total hoje: {brl(total_d)}**")
        df_show = desp[["hora","descricao","categoria","valor"]].copy()
        df_show["valor"] = df_show["valor"].apply(brl)
        df_show.columns = ["Hora","Descrição","Categoria","Valor"]
        st.dataframe(df_show.reset_index(drop=True), use_container_width=True, hide_index=True)

# ============================================================
# ABA: FECHAMENTO
# ============================================================

def aba_fechamento(cod: str):
    st.markdown("### 🔒 Fechamento de Caixa")

    c1, c2 = st.columns([1, 2])
    with c1:
        data_fech = st.date_input("📅 Data do Fechamento", value=date.today())

    data_str = data_fech.isoformat()

    with conn(cod) as c:
        vendas   = pd.DataFrame(
            c.execute("SELECT * FROM vendas WHERE data=?", (data_str,)).fetchall(),
            columns=["id","data","hora","descricao","categoria","pagamento","valor","vendedor","obs","criado_em"]
        )
        despesas = pd.DataFrame(
            c.execute("SELECT * FROM despesas WHERE data=?", (data_str,)).fetchall(),
            columns=["id","data","hora","descricao","categoria","valor","obs","criado_em"]
        )

    total_v    = vendas["valor"].sum() if not vendas.empty else 0
    total_d    = despesas["valor"].sum() if not despesas.empty else 0
    dinheiro   = vendas[vendas["pagamento"]=="Dinheiro"]["valor"].sum() if not vendas.empty else 0
    qtde       = len(vendas)

    st.divider()

    # Resumo
    m1, m2, m3, m4 = st.columns(4)
    with m1: st.metric("📦 Total Vendido",   brl(total_v))
    with m2: st.metric("🛒 Qtde de Vendas",  qtde)
    with m3: st.metric("💸 Total Despesas",  brl(total_d))
    with m4: st.metric("📊 Resultado",       brl(total_v - total_d))

    st.divider()

    # Conferência do dinheiro
    st.markdown("**💵 Conferência do Dinheiro**")
    c1, c2 = st.columns(2)
    with c1:
        troco   = st.number_input("🪙 Troco Inicial (R$)", min_value=0.0, step=0.50, format="%.2f", value=0.0)
    with c2:
        contado = st.number_input("💵 Dinheiro Contado em Caixa (R$)", min_value=0.0, step=0.50, format="%.2f", value=0.0)

    esperado  = dinheiro + troco
    diferenca = contado - esperado

    st.markdown(f"**Vendas em Dinheiro:** {brl(dinheiro)}  |  **Troco Inicial:** {brl(troco)}  |  **Esperado:** {brl(esperado)}")

    if diferenca == 0:
        st.markdown('<div class="fech-ok">✅ Caixa fechado corretamente!</div>', unsafe_allow_html=True)
    elif diferenca > 0:
        st.markdown(f'<div class="fech-warn">⚠️ Sobra de {brl(diferenca)} no caixa</div>', unsafe_allow_html=True)
    else:
        st.markdown(f'<div class="fech-err">❌ Falta de {brl(abs(diferenca))} no caixa</div>', unsafe_allow_html=True)

    # Breakdown por pagamento
    st.divider()
    st.markdown("**💳 Vendas por Forma de Pagamento**")
    cols = st.columns(len(PAGAMENTOS))
    for i, pag in enumerate(PAGAMENTOS):
        tot = vendas[vendas["pagamento"]==pag]["valor"].sum() if not vendas.empty else 0
        with cols[i]:
            st.metric(pag, brl(tot))

# ============================================================
# ABA: RELATÓRIO MENSAL
# ============================================================

def aba_relatorio(cod: str):
    st.markdown("### 📊 Relatório Mensal")

    with conn(cod) as c:
        vendas = pd.DataFrame(
            c.execute("SELECT * FROM vendas").fetchall(),
            columns=["id","data","hora","descricao","categoria","pagamento","valor","vendedor","obs","criado_em"]
        )
        despesas = pd.DataFrame(
            c.execute("SELECT * FROM despesas").fetchall(),
            columns=["id","data","hora","descricao","categoria","valor","obs","criado_em"]
        )

    if vendas.empty:
        st.info("Nenhuma venda registrada ainda.")
        return

    vendas["data"]   = pd.to_datetime(vendas["data"])
    despesas["data"] = pd.to_datetime(despesas["data"]) if not despesas.empty else despesas["data"]

    meses = vendas["data"].dt.to_period("M").astype(str).unique()
    meses = sorted(meses, reverse=True)

    mes_sel = st.selectbox("📅 Selecione o mês", meses)

    v_mes = vendas[vendas["data"].dt.to_period("M").astype(str) == mes_sel]
    d_mes = despesas[despesas["data"].dt.to_period("M").astype(str) == mes_sel] if not despesas.empty else pd.DataFrame()

    total_v = v_mes["valor"].sum()
    total_d = d_mes["valor"].sum() if not d_mes.empty else 0

    m1, m2, m3, m4, m5 = st.columns(5)
    with m1: st.metric("💵 Faturamento",   brl(total_v))
    with m2: st.metric("💸 Despesas",      brl(total_d))
    with m3: st.metric("📊 Resultado",     brl(total_v - total_d))
    with m4: st.metric("🛒 Vendas",        len(v_mes))
    with m5: st.metric("🎯 Ticket Médio",  brl(v_mes["valor"].mean()) if not v_mes.empty else brl(0))

    st.divider()

    # Por dia
    st.markdown("**📅 Faturamento por Dia**")
    por_dia = v_mes.groupby(v_mes["data"].dt.strftime("%d/%m"))["valor"].sum().reset_index()
    por_dia.columns = ["Dia", "Total (R$)"]
    st.line_chart(por_dia.set_index("Dia"), height=220, use_container_width=True)

    # Por categoria
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**📦 Por Categoria**")
        por_cat = v_mes.groupby("categoria")["valor"].sum().reset_index().sort_values("valor", ascending=False)
        por_cat["valor_fmt"] = por_cat["valor"].apply(brl)
        por_cat.columns = ["Categoria", "Valor", "Total"]
        st.dataframe(por_cat[["Categoria","Total"]].reset_index(drop=True), use_container_width=True, hide_index=True)

    with col2:
        st.markdown("**💳 Por Pagamento**")
        por_pag = v_mes.groupby("pagamento")["valor"].sum().reset_index().sort_values("valor", ascending=False)
        por_pag["valor_fmt"] = por_pag["valor"].apply(brl)
        por_pag.columns = ["Pagamento", "Valor", "Total"]
        st.dataframe(por_pag[["Pagamento","Total"]].reset_index(drop=True), use_container_width=True, hide_index=True)

    # Exportar mês
    st.divider()
    csv = v_mes[["data","hora","descricao","categoria","pagamento","valor","vendedor"]].copy()
    csv["data"]  = csv["data"].dt.strftime("%d/%m/%Y")
    csv["valor"] = csv["valor"].apply(lambda v: f"R$ {v:.2f}".replace(".", ","))
    csv.columns = ["Data","Hora","Descrição","Categoria","Pagamento","Valor","Vendedor"]
    st.download_button(
        f"⬇️ Exportar {mes_sel} (.csv)",
        csv.to_csv(index=False, sep=";", encoding="utf-8-sig"),
        file_name=f"relatorio_{mes_sel}.csv",
        mime="text/csv",
    )

# ============================================================
# PAINEL ADMIN
# ============================================================

def tela_admin():
    cabecalho()
    st.markdown("### 👑 Painel Administrativo")

    lojas = [("57", "Prime Informática 5/7"), ("42", "Prime Informática 4/2")]

    for cod, nome in lojas:
        db = get_db(cod)
        if not os.path.exists(db):
            st.warning(f"**{nome}** — sem dados ainda.")
            continue

        with conn(cod) as c:
            vendas   = pd.DataFrame(c.execute("SELECT * FROM vendas").fetchall(),
                                    columns=["id","data","hora","descricao","categoria","pagamento","valor","vendedor","obs","criado_em"])
            despesas = pd.DataFrame(c.execute("SELECT * FROM despesas").fetchall(),
                                    columns=["id","data","hora","descricao","categoria","valor","obs","criado_em"])

        total_v = vendas["valor"].sum() if not vendas.empty else 0
        total_d = despesas["valor"].sum() if not despesas.empty else 0
        hoje_v  = vendas[vendas["data"]==date.today().isoformat()]["valor"].sum() if not vendas.empty else 0

        with st.expander(f"🏪 {nome}", expanded=True):
            c1, c2, c3, c4 = st.columns(4)
            with c1: st.metric("💵 Total geral",   brl(total_v))
            with c2: st.metric("📅 Hoje",          brl(hoje_v))
            with c3: st.metric("💸 Despesas",      brl(total_d))
            with c4: st.metric("🛒 Total vendas",  len(vendas))

    if st.button("🚪 Sair"):
        for k in ["usuario","loja","cod","admin"]:
            st.session_state.pop(k, None)
        st.rerun()

# ============================================================
# APP PRINCIPAL
# ============================================================

if "usuario" not in st.session_state:
    tela_login()
else:
    cod   = st.session_state["cod"]
    admin = st.session_state["admin"]

    if admin:
        tela_admin()
    else:
        cabecalho()

        tab1, tab2, tab3, tab4, tab5 = st.tabs([
            "🛒 Nova Venda",
            "💰 Caixa do Dia",
            "📋 Histórico",
            "🔒 Fechamento",
            "📊 Relatório Mensal",
        ])

        with tab1: aba_nova_venda(cod)
        with tab2: aba_caixa_dia(cod)
        with tab3: aba_historico(cod)
        with tab4: aba_fechamento(cod)
        with tab5: aba_relatorio(cod)

        with st.sidebar:
            st.markdown(f"**🏪 {st.session_state['loja']}**")
            if st.button("🚪 Sair"):
                for k in ["usuario","loja","cod","admin"]:
                    st.session_state.pop(k, None)
                st.rerun()
