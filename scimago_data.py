import pandas as pd
import difflib

class ScimagoData:
    def __init__(self, scimago_file):
        # Colunas numéricas do Scimago
        numeric_columns = [
            'SJR', 'H index', 'Total Docs. (2023)', 'Total Refs.',
            'Total Cites (3years)', 'Citable Docs. (3years)',
            'Cites / Doc. (2years)', 'Ref. / Doc.'
        ]
        
        # Função para converter valores numéricos, tratando valores vazios
        def convert_numeric(x):
            if pd.isna(x) or str(x).strip() == '':
                return 0.0
            try:
                return float(str(x).replace(',', '.'))
            except (ValueError, TypeError):
                return 0.0
        
        # Converter vírgula para ponto e transformar em float
        converters = {col: convert_numeric for col in numeric_columns}
        
        # Ler CSV com converters para colunas numéricas
        self.scimago_df = pd.read_csv(
            scimago_file,
            sep=';',
            encoding='utf-8',
            converters=converters
        )
        self.prepare_data()
        
    def prepare_data(self):
        """Prepara os dados do Scimago para busca eficiente"""
        # Converter títulos para minúsculo para comparação
        self.scimago_df['Title_lower'] = self.scimago_df['Title'].str.lower()
        # Criar índice de busca
        self.journal_titles = set(self.scimago_df['Title_lower'].dropna())
    
    def find_best_match(self, journal_name, min_score=0.85):
        """Encontra o título mais próximo no Scimago"""
        if not isinstance(journal_name, str):
            return None
            
        journal_lower = journal_name.lower()
        
        # Tentar match exato primeiro
        exact_match = self.scimago_df[self.scimago_df['Title_lower'] == journal_lower]
        if not exact_match.empty:
            return exact_match.iloc[0]
        
        # Procurar match aproximado
        matches = difflib.get_close_matches(
            journal_lower,
            self.journal_titles,
            n=1,
            cutoff=min_score
        )
        
        if matches:
            return self.scimago_df[
                self.scimago_df['Title_lower'] == matches[0]
            ].iloc[0]
            
        return None
    
    def enrich_article_data(self, articles_df):
        """Adiciona métricas do Scimago aos artigos"""
        # Criar colunas para métricas do Scimago
        new_columns = {
            'SJR': [],
            'H index': [],
            'Total Docs. (2023)': [],
            'Total Refs.': [],
            'Total Cites (3years)': [],
            'Citable Docs. (3years)': [],
            'Cites / Doc. (2years)': [],
            'Ref. / Doc.': []
        }
        
        # Para cada artigo, buscar informações do periódico
        for _, row in articles_df.iterrows():
            journal_name = row.get('REVISTA', '')
            match = self.find_best_match(journal_name)
            
            if match is not None:
                for col in new_columns:
                    try:
                        value = float(match[col])
                    except (ValueError, TypeError):
                        value = None
                    new_columns[col].append(value)
            else:
                for col in new_columns:
                    new_columns[col].append(None)
        
        # Adicionar novas colunas ao DataFrame como tipo float
        for col, values in new_columns.items():
            col_name = f'SCIMAGO_{col.replace(" ", "_")}'
            articles_df[col_name] = pd.Series(values, dtype='float64')
        
        return articles_df

def load_scimago_data():
    """Carrega e retorna uma instância de ScimagoData"""
    try:
        scimago_file = 'scimagojr 2023.csv'
        return ScimagoData(scimago_file)
    except Exception as e:
        print(f"Erro ao carregar dados Scimago: {e}")
        return None
