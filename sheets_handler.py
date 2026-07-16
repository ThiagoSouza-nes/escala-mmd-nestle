import pandas as pd

def carregar_dados_planilha(sheet_id):
    """
    Consome os dados diretamente do Google Sheets para as duas abas necessárias.
    Mantém o tratamento idêntico ao processo original.
    """
    URL_PAGINA1 = f"https://docs.google.com/spreadsheets/d/{sheet_id}/gviz/tq?tqx=out:csv&sheet=Página1"
    URL_BACKUPS = f"https://docs.google.com/spreadsheets/d/{sheet_id}/gviz/tq?tqx=out:csv&sheet=Backups"
    
    # 1. Carrega as informações de Backups
    df_backups = pd.read_csv(URL_BACKUPS)
    df_backups['Funcionario'] = df_backups['Funcionario'].astype(str).str.strip()
    df_backups['Backups'] = df_backups['Backups'].astype(str).str.strip()
    mapa_referencia = dict(zip(df_backups['Funcionario'], df_backups['Backups']))
    
    # 2. Carrega as informações de Funcionários
    df_funcionarios = pd.read_csv(URL_PAGINA1)
    df_funcionarios['Funcionario'] = df_funcionarios['Funcionario'].astype(str).str.strip()
    
    # Filtra os nomes para a escala
    nomes = [n for n in df_funcionarios['Funcionario'].unique() if n not in ["Faiha", "Bianca S.", "nan", "None"]]
    nomes = sorted(nomes)
    
    return nomes, mapa_referencia
