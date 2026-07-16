import pandas as pd

def carregar_dados_planilha(sheet_id):
    """
    Consome os dados diretamente do Google Sheets para as duas abas necessárias.
    Compatível com variações de acentuação nas colunas.
    """
    URL_PAGINA1 = f"https://docs.google.com/spreadsheets/d/{sheet_id}/gviz/tq?tqx=out:csv&sheet=Página1"
    URL_BACKUPS = f"https://docs.google.com/spreadsheets/d/{sheet_id}/gviz/tq?tqx=out:csv&sheet=Backups"
    
    # 1. Carrega as informações de Backups
    df_backups = pd.read_csv(URL_BACKUPS)
    
    # Padroniza os nomes das colunas removendo acentos para evitar quebras
    df_backups.columns = [c.replace('í', 'i').replace('ó', 'o').strip() for c in df_backups.columns]
    
    # Mapeia dinamicamente usando as colunas corretas (Funcionario e Backups)
    col_func = 'Funcionario' if 'Funcionario' in df_backups.columns else df_backups.columns[0]
    col_back = 'Backups' if 'Backups' in df_backups.columns else df_backups.columns[1]
    
    df_backups[col_func] = df_backups[col_func].astype(str).str.strip()
    df_backups[col_back] = df_backups[col_back].astype(str).str.strip()
    mapa_referencia = dict(zip(df_backups[col_func], df_backups[col_back]))
    
    # 2. Carrega as informações de Funcionários
    df_funcionarios = pd.read_csv(URL_PAGINA1)
    df_funcionarios.columns = [c.replace('í', 'i').replace('ó', 'o').strip() for c in df_funcionarios.columns]
    
    col_func_p1 = 'Funcionario' if 'Funcionario' in df_funcionarios.columns else df_funcionarios.columns[0]
    df_funcionarios[col_func_p1] = df_funcionarios[col_func_p1].astype(str).str.strip()
    
    # Filtra os nomes para a escala
    nomes = [n for n in df_funcionarios[col_func_p1].unique() if n not in ["Faiha", "Bianca S.", "nan", "None"]]
    nomes = sorted(nomes)
    
    return nomes, mapa_referencia
