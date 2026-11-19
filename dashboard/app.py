import streamlit as st
import pandas as pd
import json
from pathlib import Path

st.set_page_config(page_title="🎯 Painel de Vagas BR", layout="wide")

BASE = Path(__file__).parent.parent  # raiz do repo

@st.cache_data(ttl=600)
def carregar(nome):
    for caminho, tipo in [
        (BASE / "remote_latam" / "br_remoto_final.json", "json"),
        (BASE / "vagas_compativeis.csv", "csv"),
        (BASE / "vagas_remotas_sul_america.csv", "csv"),
    ]:
        if nome in str(caminho) and caminho.exists():
            try:
                if tipo == "json":
                    return pd.DataFrame(json.loads(caminho.read_text(encoding="utf-8")))
                return pd.read_csv(caminho)
            except Exception as e:
                st.error(f"Erro ao ler {caminho.name}: {e}")
    return pd.DataFrame()

st.title("🎯 Painel de Vagas — Remoto Brasil")

fonte = st.sidebar.radio(
    "Base de dados",
    ["br_remoto_final.json", "vagas_compativeis.csv", "vagas_remotas_sul_america.csv"],
)

df = carregar(fonte)

if df.empty:
    st.warning("Nenhum dado carregado. Verifique se os arquivos estão no repo.")
    st.stop()

# ---------- Detectar colunas automaticamente ----------
col_link   = next((c for c in df.columns if "link" in c.lower() or "url" in c.lower()), None)
col_titulo = next((c for c in df.columns if "titulo" in c.lower() or "title" in c.lower() or "vaga" in c.lower()), None)
col_score  = next((c for c in df.columns if "score" in c.lower() or "pontua" in c.lower()), None)
col_local  = next((c for c in df.columns if "local" in c.lower() or "location" in c.lower() or "pais" in c.lower()), None)
col_data   = next((c for c in df.columns if "data" in c.lower() or "date" in c.lower()), None)

# ---------- KPIs ----------
st.subheader(f"📊 {fonte}")
c1, c2, c3, c4 = st.columns(4)
c1.metric("Total de vagas", len(df))
if col_score:
    c2.metric("Score médio", f"{df[col_score].mean():.0f}")
    c3.metric("Boas vagas (score ≥ 70)", int((df[col_score] >= 70).sum()))
c4.metric("Colunas", len(df.columns))

st.sidebar.markdown("---")
st.sidebar.caption("Colunas: " + ", ".join(f"`{c}`" for c in df.columns))

# ---------- Filtros ----------
st.subheader("🔎 Explorar")
col_a, col_b = st.columns([3, 1])
busca = col_a.text_input("🔍 Buscar")
df_filtrado = df.copy()
if col_score:
    score_min = col_b.slider("Score mínimo", 0, 100, 50)
    df_filtrado = df_filtrado[df_filtrado[col_score] >= score_min]
if busca:
    df_filtrado = df_filtrado[
        df_filtrado.apply(lambda r: busca.lower() in str(r.values).lower(), axis=1)
    ]

# ---------- Colunas a exibir (ordem amigável) ----------
colunas_exibir = [c for c in [col_titulo, col_local, col_score, col_data, col_link] if c]
colunas_restantes = [c for c in df_filtrado.columns if c not in colunas_exibir]
df_filtrado = df_filtrado[colunas_exibir + colunas_restantes]

# ---------- Tabela com link clicável ----------
config_colunas = {}
if col_titulo:
    config_colunas[col_titulo] = st.column_config.TextColumn("Vaga", width="medium")
if col_link:
    config_colunas[col_link] = st.column_config.LinkColumn(
        "🔗 Link da vaga",
        help="Clique para abrir a vaga no LinkedIn",
        display_text="Abrir vaga ↗",   # texto do botão em vez da URL gigante
        validate="^https?://",          # só aceita URLs válidas
    )
if col_score:
    config_colunas[col_score] = st.column_config.ProgressColumn(
        "Score", min_value=0, max_value=100, format="%.0f"
    )

st.dataframe(
    df_filtrado,
    use_container_width=True,
    height=500,
    column_config=config_colunas or None,
)

st.download_button(
    "⬇️ Baixar seleção (CSV)",
    df_filtrado.to_csv(index=False).encode("utf-8"),
    "vagas_filtradas.csv",
    "text/csv",
)
