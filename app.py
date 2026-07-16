import streamlit as st

# Mude para True para tirar o app do ar e False para voltar ao normal
MODO_MANUTENCAO = True 

if MODO_MANUTENCAO:
    st.title("🚧 Portal MMD 🚧")
    st.subheader("Sistema em Manutenção")
    st.info("Estamos atualizando a base de dados e inserindo os novos colaboradores. O portal estará de volta em breve com novidades!")
    st.image("https://cdn-icons-png.flaticon.com/512/3251/3251465.png", width=200) # Opcional: ícone de engrenagem/construção
    st.stop() # Esta função interrompe a execução do restante do código do app

import pandas as pd
from datetime import datetime
import streamlit.components.v1 as components

# Importação dos módulos locais recém-criados!
from sheets_handler import carregar_dados_planilha
from escala_regras import (
    gerar_escala_balanceada, 
    exportar_excel_limpo, 
    MAPA_REFERENCIA_FALLBACK
)

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="MMD | Portal de Escalas", layout="wide")

# --- DICIONÁRIO DE TRADUÇÃO ---
I18N = {
    "PT": {
        "lang_code": "pt-BR",
        "titulo": "🚀 MMD | Portal de Escalas 2026",
        "login_tit": "Portal de Escalas MMD",
        "usuario": "Usuário",
        "senha": "Senha",
        "acessar": "Acessar Painel",
        "acessibilidade": "Ativar Acessibilidade",
        "roteiro_ter": "📝 Roteiro Terça: Práticas + Iniciativas",
        "roteiro_qui": "📝 Roteiro Quinta: Lead Time + SLA",
        "estrutura_tit": "👥 Estrutura de Times",
        "exp_mes": "📂 Exportar Mês",
        "exp_ano": "📅 Exportar Ano",
        "baixar": "Baixar",
        "buscar": "🔍 Buscar por Apresentador:",
        "todos": "Todos",
        "semana": "Semana:",
        "agendar": "📅 AGENDAR",
        "backup": "🔄 Backup",
        "backup2": "🛡️ Backup 2",
        "backup_oculto": "Backup Oculto",
        "stats": "📊 {nome}: {total} reuniões no ano (sendo {dor} reuniões DOR).",
        "reuniao": "Reunião",
        "flash_m": "Flash Manhã",
        "resp_m": "Responsável Manhã",
        "resp_t": "Responsável Tarde",
        "tipo_t": "Tipo Tarde/DOR",
        "mes_col": "Mês",
        "dias": ["Segunda-Feira", "Terça-Feira", "Quarta-Feira", "Quinta-Feira", "Sexta-Feira"],
        "meses": ["Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho", "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"],
        "pauta": {
            "lista": "📑 Lista de presença", "tk": "⏱ Timekeeper", "escala": "🗓 Escala", "behavior": "📈 Behavior",
            "plan": "🎯 Plano de ação", "prac": "✅ Práticas", "nps": "📊 NPS", "ini": "💡 Iniciativas",
            "track": "📉 Tracker", "work": "🛠 Work Plan", "issue": "⚠️ Issues", "she": "🛡 SHE",
            "lt": "🕒 Lead Time", "ftr": "✅ FTR", "cats": "📁 Cats+BH"
        }
    },
    "ES": {
        "lang_code": "es-ES",
        "titulo": "🚀 MMD | Portal de Escalas 2026",
        "login_tit": "Portal de Escalas MMD",
        "usuario": "Usuario",
        "senha": "Contraseña",
        "acessar": "Acceder al Panel",
        "acessibilidade": "Activar Accesibilidad",
        "roteiro_ter": "📝 Guion Martes: Prácticas + Iniciativas",
        "roteiro_qui": "📝 Guion Jueves: Lead Time + SLA",
        "estrutura_tit": "👥 Estructura de Equipos",
        "exp_mes": "📂 Exportar Mes",
        "exp_ano": "📅 Exportar Año",
        "baixar": "Descargar",
        "buscar": "🔍 Buscar por Presentador:",
        "todos": "Todos",
        "semana": "Semana:",
        "agendar": "📅 AGENDAR",
        "backup": "🔄 Backup",
        "backup2": "🛡️ Backup 2",
        "backup_oculto": "Backup Oculto",
        "stats": "📊 {nome}: {total} reuniones en el año ({dor} reuniones DOR).",
        "reuniao": "Reunión",
        "flash_m": "Flash Mañana",
        "resp_m": "Responsable Mañana",
        "resp_t": "Responsable Tarde",
        "tipo_t": "Tipo Tarde/DOR",
        "mes_col": "Mes",
        "dias": ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes"],
        "meses": ["Enero", "Febrero", "Março", "Abril", "Maio", "Junho", "Julho", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"],
        "pauta": {
            "lista": "📑 Lista de presencia", "tk": "⏱ Timekeeper", "escala": "🗓 Escala Horario", "behavior": "📈 Behavior",
            "plan": "🎯 Plan de accion", "prac": "✅ Practicas", "nps": "📊 NPS", "ini": "💡 Iniciativas",
            "track": "📉 Tracker", "work": "🛠 Work Plan", "issue": "⚠️ Issues", "she": "🛡 SHE",
            "lt": "🕒 Lead Time", "ftr": "✅ FTR", "cats": "📁 Cats+BH"
        }
    }
}

if "lang" not in st.session_state:
    st.session_state.lang = "PT"

t = I18N[st.session_state.lang]

# --- ACESSIBILIDADE ---
def injetar_leitor_acessibilidade(lang_code):
    components.html(f"""
        <script>
            const synth = window.speechSynthesis;
            let ultimoTexto = "";
            function falar(texto) {{
                if (!texto || texto === ultimoTexto) return;
                synth.cancel(); 
                const ut = new SpeechSynthesisUtterance(texto);
                ut.lang = '{lang_code}';
                ut.rate = 1.1;
                ultimoTexto = texto;
                synth.speak(ut);
                setTimeout(() => {{ ultimoTexto = ""; }}, 800);
            }}
            const docAlvo = window.parent.document;
            docAlvo.addEventListener('mouseover', (e) => {{
                const el = e.target;
                const textoParaLer = (el.innerText || el.textContent).trim();
                if (textoParaLer.length > 0 && !textoParaLer.includes("http")) {{
                    falar(textoParaLer);
                }}
            }}, true);
            docAlvo.addEventListener('mouseout', () => {{ synth.cancel(); }}, true);
        </script>
    """, height=0, width=0)

# --- CREDENCIAIS ---
SHEET_ID = "1rFbrhxG72T2qhT2lMclAyLtjlHgtqvbxHFrVZ_KlmAU"
USER_ACCESS = "MMD-Board"
PASS_ACCESS = "@MMD123#"

def check_login():
    if "logged_in" not in st.session_state: st.session_state.logged_in = False
    if not st.session_state.logged_in:
        st.markdown(f"<h2 style='text-align: center;'>{t['login_tit']}</h2>", unsafe_allow_html=True)
        col1, col2, col3 = st.columns([1,1,1])
        with col2:
            with st.form("login"):
                u = st.text_input(t["usuario"]).strip()
                p = st.text_input(t["senha"], type="password").strip()
                if st.form_submit_button(t["acessar"], use_container_width=True):
                    if u == USER_ACCESS and p == PASS_ACCESS:
                        st.session_state.logged_in = True
                        st.rerun()
                    else: st.error("Acesso negado / Acceso denegado")
        return False
    return True

def renderizar_card(row):
    st.markdown(f"""
    <div style="background-color: #f0f2f6; padding: 15px; border-radius: 10px; border-left: 5px solid #ff4b4b; min-height: 220px; margin-bottom: 10px; color: #333;">
        <b style="font-size: 14px; color: #555;">{row['Reunião']}</b><br><br>
        <span style="font-size: 18px; font-weight: bold; color: #111;">🏆 {row['Apresentador']}</span><br><br>
        <span style="font-size: 13px; color: #444;">{t['backup']}: {row['Backup']}</span><br>
        <span title="{t['backup_oculto']}: {row['BackupOculto']}" style="font-size: 13px; color: #444; cursor: help;">{t['backup2']}: {row['Backup2']}</span>
        <div style="margin-top: 15px;"><a href="{row['Link']}" target="_blank" style="display: block; text-decoration: none; color: white; background-color: #0078d4; padding: 8px; border-radius: 5px; font-size: 11px; text-align: center; font-weight: bold;">{t['agendar']}</a></div>
    </div>
    """, unsafe_allow_html=True)

# --- EXECUÇÃO ---
if check_login():
    st.sidebar.title("🌐 Idioma / Lenguaje")
    lang_opt = st.sidebar.radio("Selecione:", ["🇧🇷 Português", "🇪🇸 Español"], index=0 if st.session_state.lang == "PT" else 1)
    new_lang = "PT" if "Português" in lang_opt else "ES"
    if new_lang != st.session_state.lang:
        st.session_state.lang = new_lang
        st.rerun()

    st.sidebar.divider()
    if st.sidebar.toggle(t["acessibilidade"], value=False):
        injetar_leitor_acessibilidade(t["lang_code"])
    
    st.sidebar.divider()
    with st.sidebar.expander(t["roteiro_ter"], expanded=False):
        st.markdown(f"**Pauta:** {t['pauta']['prac']} + {t['pauta']['ini']} + {t['pauta']['track']} + {t['pauta']['work']}")
        st.markdown(f"- {t['pauta']['lista']}\n- {t['pauta']['tk']}\n- {t['pauta']['escala']}\n- {t['pauta']['behavior']}\n- {t['pauta']['plan']}\n- {t['pauta']['prac']}\n- {t['pauta']['nps']}\n- {t['pauta']['ini']}\n- {t['pauta']['track']}\n- {t['pauta']['work']}\n- {t['pauta']['plan']} ({t['pauta']['issue']})\n- 🛡 SHE\n- 🏆 Behavior")

    with st.sidebar.expander(t["roteiro_qui"], expanded=False):
        st.markdown(f"**Pauta:** {t['pauta']['lt']} + {t['pauta']['ftr']} + {t['pauta']['cats']} + {t['pauta']['work']}")
        st.markdown(f"- {t['pauta']['lista']}\n- {t['pauta']['tk']}\n- {t['pauta']['escala']}\n- {t['pauta']['behavior']}\n- {t['pauta']['plan']}\n- {t['pauta']['lt']}\n- {t['pauta']['ftr']}\n- {t['pauta']['cats']}\n- {t['pauta']['work']}\n- {t['pauta']['issue']}\n- {t['pauta']['plan']}\n- 🛡 SHE\n- 🏆 Behavior")

    with st.sidebar.expander(t["estrutura_tit"], expanded=False):
        st.markdown("""
        **Indireto Brasil:** Debora, Dani, Dyana, Abigail, Luca, Bruno, Thiago, Anna
        \n**Material Fert Brasil:** Amanda, Douglas, Renan
        \n**CRM:** Julia, Bruna 
        \n**Material Direto Brasil:** Livia, Rafael
        \n**Material Direto Latam:** Ariel, Enrique, Sonia, Jazmin, Gisele
        \n**Fert Latam:** Florencia, Jesus, Bianca, Soledad, Mijal, German, Sebastian, Andrea, Honorato, Nathan, Rocio, Faiha
        """)

    # 1. Carrega as informações das planilhas de forma segura utilizando o novo módulo
    try:
        nomes, MAPA_REFERENCIA = carregar_dados_planilha(SHEET_ID)
    except Exception as e:
        MAPA_REFERENCIA = MAPA_REFERENCIA_FALLBACK
        nomes = list(MAPA_REFERENCIA.keys())

    # 2. Gera a escala e renderiza a tela principal apenas para quem está logado!
    df_total = gerar_escala_balanceada(nomes, MAPA_REFERENCIA, t)
    st.title(t["titulo"])

    col_e1, col_e2 = st.columns(2)
    with col_e1:
        with st.expander(t["exp_mes"]):
            m_sel = st.selectbox(t["mes_col"] + ":", t["meses"])
            st.download_button(f"{t['baixar']} {m_sel}", exportar_excel_limpo(df_total, t, m_sel), f"Escala_{m_sel}.xlsx", use_container_width=True)
    with col_e2:
        with st.expander(t["exp_ano"]):
            st.download_button(t["baixar"] + f" {t['mes_col']} Completo", exportar_excel_limpo(df_total, t), "Escala_Anual.xlsx", use_container_width=True)

    st.divider()
    busca = st.selectbox(t["buscar"], [t["todos"]] + nomes)
    if busca != t["todos"]:
        df_b = df_total[df_total["Apresentador"] == busca].copy()
        st.info(t["stats"].format(nome=busca, total=len(df_b), dor=len(df_b[df_b["Reunião"] == "DOR"])))
        st.dataframe(df_b[["Data", "Dia", "Reunião", "Backup", "Backup2", "Link"]], column_config={"Link": st.column_config.LinkColumn(t["agendar"], display_text=t["agendar"], width="small")}, use_container_width=True, hide_index=True)

    st.divider()
    s_idx = st.select_slider(t["semana"], options=sorted(df_total["Semana"].unique()), value=datetime.now().isocalendar()[1])
    df_s = df_total[df_total["Semana"] == s_idx]
    for dt, gp in df_s.groupby("Data", sort=False):
        st.markdown(f"**{gp['Dia'].iloc[0]} - {dt}**")
        cols = st.columns(len(gp))
        for i, (_, r) in enumerate(gp.iterrows()):
            with cols[i]: renderizar_card(r)
