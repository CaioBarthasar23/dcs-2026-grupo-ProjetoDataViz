"""Aplicação Streamlit da pergunta 1."""
from pathlib import Path

import streamlit as st

from dashboard.common import carregar_silver
from dashboard.p1 import preparar_ranking_p1
from src.fx_asof import converter_precos


def main() -> None:
    st.set_page_config(page_title="Pergunta 1 — valorização", layout="wide")
    st.title("Quais cartas mais valorizaram e desvalorizaram?")
    moeda = st.radio("Moeda", ["R$", "US$"], horizontal=True)
    dados = carregar_silver(Path("data_local/silver"))
    fato = converter_precos(dados["precos"], dados["cambios"])
    ranking = preparar_ranking_p1(fato, dados["produtos"], moeda="brl" if moeda == "R$" else "usd")
    st.caption(f"Período disponível: {ranking['data_inicio']} a {ranking['data_fim']}")
    st.caption(f"Comparações carta/acabamento elegíveis: {ranking['quantidade_comparacoes']}")
    st.caption("Ausência de preço no primeiro ou último dia exclui a comparação; lacunas não são interpoladas.")
    st.write("Exclusões", ranking["excluidas"])
    col_altas, col_quedas = st.columns(2)
    for coluna, titulo, chave in (
        (col_altas, "Maiores altas", "maiores_altas"),
        (col_quedas, "Maiores quedas", "maiores_quedas"),
    ):
        with coluna:
            st.subheader(titulo)
            for row in ranking[chave]:
                st.markdown(f"**product_id {row['product_id']} · {row['acabamento']}**")
                if row.get("image_url"):
                    st.image(row["image_url"], width=120)
                if row.get("url"):
                    st.link_button("Produto no TCGplayer", row["url"])
                st.write({
                    "variação (R$)" if moeda == "R$" else "variação (US$)":
                        f"R$ {row['variacao_brl']:.2f}" if moeda == "R$" else f"US$ {row['variacao_usd']:.2f}",
                    "variação percentual": f"{row['variacao_percentual']:.2%}",
                    "efeito da carta": f"{row['efeito_carta']:.2%}",
                    "efeito do câmbio": row["rotulo_efeito_cambio"] or f"{row['efeito_cambio']:.2%}",
                    "efeito cruzado": row["rotulo_efeito_cruzado"] or f"{row['efeito_cruzado']:.2%}",
                })


if __name__ == "__main__":
    main()
