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
		if caminho.name == nome or (caminho.exists() and nome in str(caminho)):
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

# ---------- KPIs ----------
st.subheader(f"📊 {fonte}")
c1, c2, c3, c4 = st.columns(4)
c1.metric("Total de vagas", len(df))
col_score = next((c for c in df.columns if "score" in c.lower() or "pontua" in c.lower()), None)
if col_score:
	c2.metric("Score médio", f"{df[col_score].mean():.0f}")
	c3.metric("Boas vagas (score ≥ 70)", int((df[col_score] >= 70).sum()))
c4.metric("Colunas detectadas", len(df.columns))

st.sidebar.markdown("---")
st.sidebar.caption("Colunas: " + ", ".join(f"`{c}`" for c in df.columns))

# ---------- Filtros ----------
st.subheader("🔎 Explorar")
col_a, col_b = st.columns([3, 1])
busca = col_a.text_input("🔍 Buscar")
score_min = 0
if col_score:
	score_min = col_b.slider("Score mínimo", 0, 100, 50)
	df_filtrado = df[df[col_score] >= score_min]
else:
	df_filtrado = df

if busca:
	mask = df_filtrado.apply(lambda r: busca.lower() in str(r.values).lower(), axis=1)
	df_filtrado = df_filtrado[mask]

st.dataframe(df_filtrado, use_container_width=True, height=500)

st.download_button(
	"⬇️ Baixar seleção (CSV)",
	df_filtrado.to_csv(index=False).encode("utf-8"),
	"vagas_filtradas.csv",
	"text/csv",
)
