import pandas as pd
from difflib import get_close_matches

class ArticleSearch:
    def __init__(self, scimago_data):
        self.scimago_data = scimago_data
        self.all_articles = None  # Armazenará todos os artigos concatenados

    def set_articles_data(self, curriculos_data):
        """Concatena todos os artigos de todos os docentes em um único DataFrame"""
        articles_list = []
        
        for curriculo_id, dados in curriculos_data.items():
            if 'ARTIGOS-PUBLICADOS' in dados:
                df = dados['ARTIGOS-PUBLICADOS'].copy()
                df['CURRICULO_ID'] = curriculo_id
                articles_list.append(df)
        
        if articles_list:
            self.all_articles = pd.concat(articles_list, ignore_index=True)
        else:
            self.all_articles = pd.DataFrame()

    def search_by_criteria(self, query, field, threshold=0.6):
        """Busca artigos usando diferentes critérios"""
        if not query or self.all_articles is None or self.all_articles.empty:
            return None

        query = str(query).lower().strip()
        
        # Mapeamento de campos
        field_map = {
            'title': 'TITULO-DO-ARTIGO',
            'issn': 'ISSN',
            'doi': 'DOI',
            'year': 'ANO'  # Adicionar ano como campo de busca
        }
        
        search_field = field_map.get(field)
        if not search_field or search_field not in self.all_articles.columns:
            return None

        # Busca nos artigos
        try:
            # Tratar valores nulos primeiro
            df = self.all_articles.copy()
            df[search_field] = df[search_field].fillna('').astype(str)
            
            if field in ['issn', 'doi']:
                # Remove hífens e espaços para ISSN/DOI
                clean_query = query.replace('-', '').replace(' ', '')
                mask = df[search_field].str.lower().str.replace('-', '').str.replace(' ', '') == clean_query
            elif field == 'year':
                # Busca exata por ano
                mask = df[search_field].str.strip() == query
            else:
                # Busca por contém para títulos
                mask = df[search_field].str.lower().str.contains(query, regex=False)

            results = df[mask]
            return results if not results.empty else None
            
        except Exception as e:
            print(f"Erro na busca: {e}")
            return None

    def filter_results(self, df, filters):
        """Aplica filtros aos resultados"""
        if df is None or df.empty:
            return pd.DataFrame()
            
        filtered_df = df.copy()
        
        for field, value in filters.items():
            if value:
                if field in ['SJR', 'H index']:
                    col_name = f'SCIMAGO_{field.replace(" ", "_")}'
                    if col_name in filtered_df.columns:
                        try:
                            min_val, max_val = value
                            filtered_df = filtered_df[
                                (filtered_df[col_name] >= min_val) & 
                                (filtered_df[col_name] <= max_val)
                            ]
                        except:
                            continue
                        
                elif field == 'Categories':
                    if 'SCIMAGO_Categories' in filtered_df.columns:
                        filtered_df = filtered_df[
                            filtered_df['SCIMAGO_Categories'].fillna('').str.contains(
                                value, case=False, na=False
                            )
                        ]
                    
                elif field == 'Year':
                    if 'ANO' in filtered_df.columns:
                        try:
                            year = str(value)
                            filtered_df['ANO'] = filtered_df['ANO'].astype(str)
                            filtered_df = filtered_df[filtered_df['ANO'] == year]
                        except:
                            continue

        return filtered_df

    def get_all_articles(self):
        """Retorna todos os artigos sem filtro"""
        return self.all_articles.copy() if self.all_articles is not None else None
