import streamlit as st
import pandas as pd
from datetime import datetime
import urllib.parse
import streamlit.components.v1 as components

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="MMD | Escala de Apresentações", layout="wide")

# Link da sua planilha Google Sheets (dados de funcionários)
SHEET_ID = "1rFbrhxG72T2qhT2lMclAyLtjlHgtqvbxHFrVZ_KlmAU"
SHEET_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv"

# Credenciais de acesso
USER_ACCESS = "MMD-Board"
PASS_ACCESS = "@MMD123#"

# Mapa de Backups (conforme sua última atualização)
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

# --- FUNÇÃO DE LEITURA DE TELA (JavaScript) ---
def ler_pagina_completa():
    """Varre os elementos de texto da página e utiliza a API de voz do navegador."""
    if st.session_state.get("voz", False):
        components.html("""
            <script>
                function lerTudo() {
                    // Cancela qualquer fala anterior para não sobrepor
                    window.speechSynthesis.cancel();
                    
                    // Seleciona títulos, negritos, spans e textos de markdown
                    let elementos = document.querySelectorAll('h1, h2, h3, b, span, .stMarkdown p');
                    let textoParaLer = "";
                    
                    elementos.forEach(el => {
                        let txt = el.innerText.trim();
                        // Filtra textos muito curtos ou ícones isolados
                        if(txt.length > 2) {
                            textoParaLer += txt + ". ";
                        }
                    });

                    if (textoParaLer.length > 0) {
                        var msg = new SpeechSynthesisUtterance(textoParaLer);
                        msg.lang = 'pt-BR';
                        msg.rate = 1.1; // Velocidade da voz
                        window.speechSynthesis.speak(msg);
                    }
                }
                // Aguarda 1 segundo para garantir que o Streamlit renderizou os dados
                setTimeout(lerTudo, 1000);
            </script>
        """, height=0)

def check_login():
    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False
    if not st.session_state.logged_in:
        st.markdown("<h2 style='text-align: center;'>Portal de Escalas MMD</h2>", unsafe_allow_html=True)
        col1, col2, col3 = st.columns([1,1,1])
        with col2:
            with st.form("login_system", clear_on_submit=False):
                user = st.text_input("Usuário").strip()
                password = st.text_input("Senha", type="password").strip()
                if st.form_submit_button("Acessar Painel", use_container_width=True):
                    if user == USER_ACCESS and password == PASS_ACCESS:
                        st.session_state.logged_in = True
                        st.rerun()
                    else:
                        st.error("Usuário ou senha incorretos.")
        return False
    return True

def criar_link_outlook(data_str, reuniao, apresentador):
    try:
        data_obj = datetime.strptime(data_str, "%d/%m/%Y")
        data_iso = data_obj.strftime("%Y-%m-%d")
        hora_start = "09:45:00" if "Manhã" in reuniao else "15:00:00"
        hora_end = "10:15:00" if "Manhã" in reuniao else "15:30:00"
        assunto = urllib.parse.quote(f"🔔 Apresentação MMD: {reuniao}")
        corpo = urllib.parse.quote(f"Apresentador: {apresentador}")
        return f"https://outlook.office.com/calendar/0/deeplink/compose?subject={assunto}&body={corpo}&startdt={data_iso}T{hora_start}&enddt={data_iso}T{hora_end}"
    except: return "#"

@st.cache_data(ttl=60)
def carregar_nomes():
    try:
        df_sheets = pd.read_csv(SHEET_URL)
        return sorted(df_sheets['Funcionario'].dropna().unique().tolist())
    except: return []

def gerar_escala_final(nomes):
    ano_atual = 2026
    data_inicio = datetime(ano_atual, 1, 1)
    data_fim = datetime(ano_atual, 12, 31)
    dias = pd.date_range(data_inicio, data_fim, freq='B')
    fila_flash = nomes.copy()
    fila_dor = [n for n in nomes if n not in ["Dani", "Rafael"]]
    idx_f, idx_d, escala = 0, 0, []
    for dia in dias:
        data_s = dia.strftime("%d/%m/%Y")
        sem = dia.isocalendar()[1]
        dia_semana = dia.weekday()
        dia_nome = ["Segunda", "Terça", "Quarta", "Quinta", "Sexta"][dia_semana]
        apresentadores_na_semana = [item['Apresentador'] for item in escala if item['Semana'] == sem]
        
        # Manhã
        while fila_flash[idx_f % len(fila_flash)] in apresentadores_na_semana: idx_f += 1
        ap_m = fila_flash[idx_f % len(fila_flash)]
        escala.append({"Semana": sem, "Data": data_s, "Dia": dia_nome, "Reunião": "Flash Manhã", "Apresentador": ap_m, "Backup": MAPA_BACKUPS.get(ap_m, "N/A"), "Link": criar_link_outlook(data_s, "Flash Manhã", ap_m)})
        apresentadores_na_semana.append(ap_m)
        idx_f += 1
        
        # Tarde (DOR ou Flash)
        if dia_semana in [1, 3]: 
            while fila_dor[idx_d % len(fila_dor)] in apresentadores_na_semana: idx_d += 1
            ap_d = fila_dor[idx_d % len(fila_dor)]
            escala.append({"Semana": sem, "Data": data_s, "Dia": dia_nome, "Reunião": "DOR", "Apresentador": ap_d, "Backup": MAPA_BACKUPS.get(ap_d, "N/A"), "Link": criar_link_outlook(data_s, "DOR", ap_d)})
            idx_d += 1
        elif dia_semana in [0, 2, 4]: 
            while fila_flash[idx_f % len(fila_flash)] in apresentadores_na_semana: idx_f += 1
            ap_t = fila_flash[idx_f % len(fila_flash)]
            escala.append({"Semana": sem, "Data": data_s, "Dia": dia_nome, "Reunião": "Flash Tarde", "Apresentador": ap_t, "Backup": MAPA_BACKUPS.get(ap_t, "N/A"), "Link": criar_link_outlook(data_s, "Flash Tarde", ap_t)})
            idx_f += 1
    return pd.DataFrame(escala)

def renderizar_card(row):
    st.markdown(f"""
    <div style="background-color: #f0f2f6; padding: 15px; border-radius: 10px; border-left: 5px solid #ff4b4b; margin-bottom: 10px; box-shadow: 2px 2px 5px rgba(0,0,0,0.05);">
        <b style="font-size: 14px; color: #31333F;">{row['Reunião']}</b><br>
        <span style="font-size: 18px; color: #333; font-weight: bold;">🏆 {row['Apresentador']}</span><br>
        <span style="font-size: 13px; color: #666;">🔄 Backup: {row['Backup']}</span><br>
        <div style="margin-top: 10px;">
            <a href="{row['Link']}" target="_blank" style="display: block; text-decoration: none; color: white; background-color: #0078d4; padding: 8px; border-radius: 5px; font-size: 11px; text-align: center; font-weight: bold;">📅 AGENDAR</a>
        </div>
    </div>
    """, unsafe_allow_html=True)

# --- EXECUÇÃO DO APP ---
if check_login():
    nomes_lista = carregar_nomes()
    if nomes_lista:
        df_total = gerar_escala_final(nomes_lista)
        
        # Barra Lateral
        st.sidebar.title("Configurações")
        if "voz" not in st.session_state: st.session_state.voz = False
        btn_label = "🔴 Desativar Áudio" if st.session_state.voz else "🔊 Ativar Leitura Automática"
        if st.sidebar.button(btn_label):
            st.session_state.voz = not st.session_state.voz
            st.rerun()
        
        if st.sidebar.button("🚪 Sair do Sistema"):
            st.session_state.logged_in = False
            st.rerun()

        st.title("🚀 MMD | Dashboard de Apresentações")
        
        # Chama a função de voz se estiver ativa
        ler_pagina_completa()

        # Filtro de Apresentador
        filtro_nome = st.selectbox("🔍 Buscar por Apresentador:", ["Todos"] + nomes_lista)
        
        if filtro_nome != "Todos":
            df_pessoal = df_total[df_total["Apresentador"] == filtro_nome]
            st.info(f"📊 {filtro_nome} possui um total de {len(df_pessoal)} apresentações agendadas para 2026.")
            st.dataframe(df_pessoal[["Data", "Dia", "Reunião", "Backup"]], hide_index=True, use_container_width=True)
            st.markdown("---")

        st.subheader("🗓️ Visualização por Semana")
        sem_atual = datetime.now().isocalendar()[1]
        sem_busca = st.select_slider("Arraste para mudar a semana:", options=sorted(df_total["Semana"].unique()), value=sem_atual)
        
        df_semana = df_total[df_total["Semana"] == sem_busca]
        
        for d_label, group in df_semana.groupby("Data", sort=False):
            st.markdown(f"**{group['Dia'].iloc[0]} - {d_label}**")
            cols = st.columns(len(group))
            for i, (_, row) in enumerate(group.iterrows()):
                with cols[i]:
                    renderizar_card(row)
