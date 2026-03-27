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

# --- FUNÇÃO JAVASCRIPT DE LEITURA COMPLETA ---
def injetar_leitura_automatica():
    if st.session_state.get("voz", False):
        components.html("""
            <script>
                function executarLeitura() {
                    // Cancela falas anteriores
                    window.speechSynthesis.cancel();

                    // Coleta textos importantes: Títulos, Nomes nos Cards e Informações de busca
                    const seletores = 'h1, h2, h3, [data-testid="stMarkdownContainer"] p, b, span';
                    const elementos = document.querySelectorAll(seletores);
                    
                    let textoFinal = "";
                    elementos.forEach(el => {
                        let t = el.innerText.trim();
                        // Filtra textos muito curtos, links ou ícones de botão
                        if (t.length > 3 && !t.includes("http") && !t.includes("📅")) {
                            textoFinal += t + ". ";
                        }
                    });

                    if (textoFinal.length > 0) {
                        const utterance = new SpeechSynthesisUtterance(textoFinal);
                        utterance.lang = 'pt-BR';
                        utterance.rate = 1.0; // Velocidade normal
                        utterance.pitch = 1.0;
                        window.speechSynthesis.speak(utterance);
                    }
                }
                
                // Aguarda o Streamlit renderizar os elementos dinâmicos
                setTimeout(executarLeitura, 1500);
            </script>
        """, height=0)

def check_login():
    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False
    if not st.session_state.logged_in:
        st.markdown("<h2 style='text-align: center;'>Portal de Escalas MMD</h2>", unsafe_allow_html=True)
        col1, col2, col3 = st.columns([1,1,1])
        with col2:
            with st.form("login_system"):
                u = st.text_input("Usuário").strip()
                p = st.text_input("Senha", type="password").strip()
                if st.form_submit_button("Acessar Painel", use_container_width=True):
                    if u == USER_ACCESS and p == PASS_ACCESS:
                        st.session_state.logged_in = True
                        st.rerun()
                    else:
                        st.error("Dados incorretos.")
        return False
    return True

def criar_link_outlook(data_str, reuniao, apresentador):
    try:
        data_obj = datetime.strptime(data_str, "%d/%m/%Y")
        data_iso = data_obj.strftime("%Y-%m-%d")
        hora = "09:45:00" if "Manhã" in reuniao else "15:00:00"
        assunto = urllib.parse.quote(f"Apresentação MMD: {reuniao}")
        return f"https://outlook.office.com/calendar/0/deeplink/compose?subject={assunto}&startdt={data_iso}T{hora}"
    except: return "#"

@st.cache_data(ttl=60)
def carregar_nomes():
    try:
        df = pd.read_csv(SHEET_URL)
        return sorted(df['Funcionario'].dropna().unique().tolist())
    except: return []

def gerar_escala(nomes):
    dias = pd.date_range(datetime(2026, 1, 1), datetime(2026, 12, 31), freq='B')
    fila_f, fila_d, escala = nomes.copy(), [n for n in nomes if n not in ["Dani", "Rafael"]], []
    idx_f, idx_d = 0, 0
    for dia in dias:
        data_s, sem, d_sem = dia.strftime("%d/%m/%Y"), dia.isocalendar()[1], dia.weekday()
        d_nome = ["Segunda", "Terça", "Quarta", "Quinta", "Sexta"][d_sem]
        aps_sem = [item['Apresentador'] for item in escala if item['Semana'] == sem]
        while fila_f[idx_f % len(fila_f)] in aps_sem: idx_f += 1
        ap_m = fila_f[idx_f % len(fila_f)]
        escala.append({"Semana": sem, "Data": data_s, "Dia": d_nome, "Reunião": "Flash Manhã", "Apresentador": ap_m, "Backup": MAPA_BACKUPS.get(ap_m, "N/A"), "Link": criar_link_outlook(data_s, "Flash Manhã", ap_m)})
        aps_sem.append(ap_m); idx_f += 1
        if d_sem in [1, 3]:
            while fila_d[idx_d % len(fila_d)] in aps_sem: idx_d += 1
            ap_d = fila_d[idx_d % len(fila_d)]
            escala.append({"Semana": sem, "Data": data_s, "Dia": d_nome, "Reunião": "DOR", "Apresentador": ap_d, "Backup": MAPA_BACKUPS.get(ap_d, "N/A"), "Link": criar_link_outlook(data_s, "DOR", ap_d)})
            idx_d += 1
        else:
            while fila_f[idx_f % len(fila_f)] in aps_sem: idx_f += 1
            ap_t = fila_f[idx_f % len(fila_f)]
            escala.append({"Semana": sem, "Data": data_s, "Dia": d_nome, "Reunião": "Flash Tarde", "Apresentador": ap_t, "Backup": MAPA_BACKUPS.get(ap_t, "N/A"), "Link": criar_link_outlook(data_s, "Flash Tarde", ap_t)})
            idx_f += 1
    return pd.DataFrame(escala)

def render_card(row):
    st.markdown(f"""
    <div style="background-color: #f0f2f6; padding: 15px; border-radius: 10px; border-left: 5px solid #ff4b4b; margin-bottom: 10px;">
        <b style="font-size: 14px;">{row['Reunião']}</b><br>
        <span style="font-size: 18px; font-weight: bold;">{row['Apresentador']}</span><br>
        <span style="font-size: 13px; color: #666;">Backup: {row['Backup']}</span>
    </div>
    """, unsafe_allow_html=True)

if check_login():
    lista = carregar_nomes()
    if lista:
        df_total = gerar_escala(lista)
        
        # --- SIDEBAR ---
        if "voz" not in st.session_state: st.session_state.voz = False
        btn_txt = "🔴 Desligar Áudio" if st.session_state.voz else "🔊 Ligar Leitura Completa"
        if st.sidebar.button(btn_txt):
            st.session_state.voz = not st.session_state.voz
            st.rerun()
        
        # --- CONTEÚDO ---
        st.title("🚀 MMD | Escala 2026")
        
        # Injeção da Voz
        injetar_leitura_automatica()

        nome_sel = st.selectbox("Filtrar por nome:", ["Todos"] + lista)
        if nome_sel != "Todos":
            df_p = df_total[df_total["Apresentador"] == nome_sel]
            st.info(f"{nome_sel} tem {len(df_p)} apresentações este ano.")
            st.dataframe(df_p[["Data", "Dia", "Reunião", "Backup"]], hide_index=True, use_container_width=True)

        st.divider()
        sem_atual = datetime.now().isocalendar()[1]
        s_busca = st.select_slider("Semana:", options=sorted(df_total["Semana"].unique()), value=sem_atual)
        
        df_s = df_total[df_total["Semana"] == s_busca]
        for dt, gp in df_s.groupby("Data", sort=False):
            st.markdown(f"### {gp['Dia'].iloc[0]} - {dt}")
            cols = st.columns(len(gp))
            for i, (_, r) in enumerate(gp.iterrows()):
                with cols[i]: render_card(r)
