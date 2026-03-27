import streamlit as st
import pandas as pd
from datetime import datetime
import urllib.parse
import streamlit.components.v1 as components

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="MMD | Escala de Apresentações", layout="wide")

SHEET_ID = "1rFbrhxG72T2qhT2lMclAyLtjlHgtqvbxHFrVZ_KlmAU"
SHEET_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv"

USER_ACCESS = "MMD-Board"
PASS_ACCESS = "@MMD123#"

MAPA_BACKUPS = {
    "Abigail": "Dani", "Amanda": "Mijal", "Anna": "Soledad", 
    "Ariel": "Rafael", "Bianca M.": "Ariel", "Bianca S.": "Amanda", 
    "Bruna": "Anna Laura", "Bruno": "Bianca M.", "Enrique": "Jazmin", 
    "Dani": "Sonia", "Debora": "Bruna", "Diana": "Julia", 
    "Florencia": "Diana", "Gisele": "Thiago", 
    "Honorato": "Bruno", "Jazmin": "Abigail", "Jesus": "Luca", 
    "Julia": "Honorato", "Livia": "Bianca S.", "Luca": "Enrique", 
    "Mijal": "Livia", "Rafael": "Florencia", "Renan": "Debora", 
    "Sonia": "Jesus", "Soledad": "Gisele", "Thiago": "Renan"
}

# --- FUNÇÃO DE VOZ (VERSÃO CORRIGIDA PARA STREAMLIT) ---
def disparar_leitura_total():
    """Injeta um script que acessa o documento pai para ler os textos da página."""
    components.html("""
        <script>
            function executarLeitura() {
                // Cancela qualquer fala anterior
                window.speechSynthesis.cancel();
                
                // Acessa o documento pai (onde o Streamlit renderiza os elementos)
                const docAlvo = window.parent.document;
                
                // Seleciona títulos, parágrafos, spans e containers de markdown do Streamlit
                let elementos = docAlvo.querySelectorAll('h1, h2, h3, [data-testid="stMarkdownContainer"] p, b, span');
                
                let narracao = "";
                elementos.forEach(el => {
                    let t = el.innerText.trim();
                    // Filtra ruídos, links e textos muito curtos
                    if(t.length > 2 && !t.includes("http") && !t.includes("://")) {
                        narracao += t + ". ";
                    }
                });

                if(narracao.length > 0) {
                    let msg = new SpeechSynthesisUtterance(narracao);
                    msg.lang = 'pt-BR';
                    msg.rate = 1.0;
                    window.speechSynthesis.speak(msg);
                }
            }
            // Delay de 1 segundo para garantir que os cards carregaram
            setTimeout(executarLeitura, 1000);
        </script>
    """, height=0, width=0)

def check_login():
    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False
    if not st.session_state.logged_in:
        st.markdown("<h2 style='text-align: center;'>Portal de Escalas MMD</h2>", unsafe_allow_html=True)
        col1, col2, col3 = st.columns([1,1,1])
        with col2:
            with st.form("login_system"):
                user = st.text_
