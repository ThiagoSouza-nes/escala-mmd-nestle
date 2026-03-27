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

# --- FUNÇÃO DE ACESSIBILIDADE (LEITURA AO PASSAR O MOUSE) ---
def injetar_leitor_acessibilidade():
    """Injeta um script que lê o texto sob o cursor do mouse (Hover)."""
    components.html("""
        <script>
            const synth = window.speechSynthesis;
            let ultimaLeitura = "";

            function falar(texto) {
                if (texto === ultimaLeitura || synth.speaking) return;
                synth.cancel(); // Para a fala anterior para ler a nova imediatamente
                
                const ut = new SpeechSynthesisUtterance(texto);
                ut.lang = 'pt-BR';
                ut.rate = 1.1;
                ultimaLeitura = texto;
                synth.speak(ut);
                
                // Limpa o cache da última leitura após breve delay
                setTimeout(() => { ultimaLeitura = ""; }, 1500);
            }

            // Acessa o documento principal do Streamlit
            const docAlvo = window.parent.document;

            // Detecta quando o mouse passa sobre um elemento
            docAlvo.addEventListener('mouseover', (e) => {
                const el = e.target;
                const tagsInteresse = ['B', 'SPAN', 'P', 'H1', 'H2', 'H3', 'A', 'BUTTON', 'LABEL'];
                
                if (tagsInteresse.includes(el.tagName)) {
                    const texto = el.innerText.trim();
                    if (texto.length > 1 && !texto.includes("http")) {
                        falar(texto);
                    }
                }
            });
            
            // Suporte para navegação via teclado (TAB)
            docAlvo.addEventListener('focusin', (e) => {
                const texto = e.target.innerText || e.target.value;
                if (texto) falar(texto);
            });
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
        return f"https://outlook.office.com/calendar/0/deeplink/compose?subject={assunto}&startdt={data_iso}T{hora_start}&enddt={data_iso}T{hora_end}"
    except: return "#"

@st.cache_data(ttl=60)
def carregar_nomes():
    try:
        df = pd.read_csv(SHEET_URL)
        return sorted(df['Funcionario'].dropna().unique().tolist())
    except: return []

def gerar_escala_final(nomes):
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

def renderizar_card(row):
    st.markdown(f"""
    <div style="background-color: #f0f2f6; padding: 15px; border-radius: 10px; border-left: 5px solid #ff4b4b; min-height: 190px; margin-bottom: 10px; box-shadow: 2px 2px 5px rgba(0,0,0,0.05);">
        <b style="font-size: 14px; color: #31333F;">{row['Reunião']}</b><br><br>
        <span style="font-size: 18px; color: #333; font-weight: bold;">🏆 {row['Apresentador']}</span><br><br>
        <span style="font-size: 13px; color: #666;">🔄 Backup: {row['Backup']}</span><br>
        <div style="margin-top: 10px;">
            <a href="{row['Link']}" target="_blank" style="display: block; text-decoration: none; color: white; background-color: #0078d4; padding: 8px; border-radius: 5px; font-size: 11px; text-align: center; font-weight: bold;">📅 AGENDAR</a>
        </div>
    </div>
    """, unsafe_allow_html=True)

# --- INÍCIO DO APP ---
if check_login():
    nomes_lista = carregar_nomes()
    if nomes_lista:
        # Injeta o leitor de mouse hover automaticamente
        injetar_leitor_acessibilidade()
        
        df_total = gerar_escala_final(nomes_lista)
        
        st.title("🚀 MMD | Dashboard de Apresentações")
        
        # Filtros
        filtro_nome = st.selectbox("🔍 Buscar por Apresentador:", ["Todos"] + nomes_lista)
        if filtro_nome != "Todos":
            df_p = df_total[df_total["Apresentador"] == filtro_nome]
            st.info(f"📊 {filtro_nome} tem {len(df_p)} apresentações em 2026.")
            st.dataframe(df_p[["Data", "Dia", "Reunião", "Backup"]], hide_index=True, use_container_width=True)

        st.subheader("🗓️ Visualização por Semana")
        sem_atual = datetime.now().isocalendar()[1]
        sem_busca = st.select_slider("Semana:", options=sorted(df_total["Semana"].unique()), value=sem_atual)
        
        df_semana = df_total[df_total["Semana"] == sem_busca]
        for d_label, group in df_semana.groupby("Data", sort=False):
            st.markdown(f"**{group['Dia'].iloc[0]} - {d_label}**")
            cols = st.columns(len(group))
            for i, (_, row) in enumerate(group.iterrows()):
                with cols[i]: renderizar_card(row)
