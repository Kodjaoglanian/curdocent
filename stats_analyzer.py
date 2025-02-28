import pandas as pd
import numpy as np
from collections import Counter, defaultdict
from datetime import datetime

class CurriculoAnalyzer:
    def __init__(self, dataframes):
        self.dataframes = dataframes
        self.ano_atual = datetime.now().year

    def analyze_single_curriculo(self, curriculo_id):
        """Análise detalhada de um único currículo"""
        if curriculo_id not in self.dataframes:
            return None
            
        dados = self.dataframes[curriculo_id]
        stats = {}
        
        # Dados básicos
        if 'DADOS-GERAIS' in dados:
            stats['dados_basicos'] = {
                'nome': dados['DADOS-GERAIS']['NOME-COMPLETO'].iloc[0],
                'instituicao': dados['DADOS-GERAIS'].get('INSTITUICAO', ['Não informado']).iloc[0]
            }
        
        # Análise de Formação
        if 'FORMACAO-ACADEMICA' in dados:
            formacao = dados['FORMACAO-ACADEMICA']
            stats['formacao'] = {
                'maior_titulacao': self._get_highest_degree(formacao),
                'total_formacoes': len(formacao),
                'instituicoes': formacao['INSTITUICAO'].unique().tolist()
            }
        
        # Análise de Produção
        stats['producao'] = self._analyze_production(dados)
        
        # Análise temporal
        stats['temporal'] = self._analyze_temporal_data(dados)
        
        return stats
    
    def analyze_all_curriculos(self):
        """Análise estatística global do corpo docente"""
        stats = {
            'resumo': self._get_resumo_geral(),
            'titulacao': self._analyze_titulacao(),
            'producao': self._analyze_producao_global(),
            'colaboracao': self._analyze_colaboracoes(),
            'orientacoes': self._analyze_orientacoes(),
            'areas': self._analyze_areas_conhecimento(),
            'impacto': self._analyze_impacto_producao(),
            'tendencias': self._analyze_tendencias()
        }
        return stats

    def _get_resumo_geral(self):
        """Resumo geral do corpo docente"""
        total_docentes = len(self.dataframes)
        total_producao = 0
        media_exp = 0
        instituicoes = set()

        for dados in self.dataframes.values():
            # Contagem de produção
            if 'ARTIGOS-PUBLICADOS' in dados:
                total_producao += len(dados['ARTIGOS-PUBLICADOS'])
            if 'LIVROS-PUBLICADOS' in dados:
                total_producao += len(dados['LIVROS-PUBLICADOS'])
            if 'CAPITULOS-LIVROS' in dados:
                total_producao += len(dados['CAPITULOS-LIVROS'])
            
            # Experiência e instituições
            if 'ATUACOES-PROFISSIONAIS' in dados:
                atuacoes = dados['ATUACOES-PROFISSIONAIS']
                if not atuacoes.empty and 'ANO-INICIO' in atuacoes.columns:
                    anos_exp = atuacoes['ANO-INICIO'].astype(float).min()
                    if not pd.isna(anos_exp):
                        media_exp += self.ano_atual - int(anos_exp)
                
                if 'INSTITUICAO' in atuacoes.columns:
                    instituicoes.update(atuacoes['INSTITUICAO'].dropna().unique())

        return {
            'total_docentes': total_docentes,
            'media_producao': total_producao / total_docentes if total_docentes > 0 else 0,
            'media_experiencia': media_exp / total_docentes if total_docentes > 0 else 0,
            'instituicoes_vinculadas': len(instituicoes)
        }

    def _analyze_titulacao(self):
        """Análise detalhada da titulação"""
        titulacoes = Counter()
        areas_formacao = Counter()
        evolucao_formacao = defaultdict(list)

        for dados in self.dataframes.values():
            if 'FORMACAO-ACADEMICA' in dados:
                formacao = dados['FORMACAO-ACADEMICA']
                if not formacao.empty:
                    # Maior titulação
                    maior_tit = self._get_highest_degree(formacao)
                    if maior_tit != 'Não informado':  # Só conta se tiver titulação válida
                        titulacoes[maior_tit] += 1

                    # Áreas de formação
                    if 'AREA' in formacao.columns:
                        for area in formacao['AREA'].dropna():
                            areas_formacao[area] += 1

                    # Evolução da formação
                    if 'ANO-CONCLUSAO' in formacao.columns and 'NIVEL' in formacao.columns:
                        for _, row in formacao.iterrows():
                            if pd.notna(row['ANO-CONCLUSAO']):
                                evolucao_formacao[row['NIVEL']].append(int(row['ANO-CONCLUSAO']))

        # Garantir que há dados válidos
        if not titulacoes:
            titulacoes['Não informado'] = 1  # Adiciona valor default

        return {
            'distribuicao': dict(titulacoes),
            'principais_areas': dict(areas_formacao.most_common(10)),
            'evolucao_temporal': {nivel: sorted(anos) for nivel, anos in evolucao_formacao.items()}
        }

    def _analyze_producao_global(self):
        """Análise da produção científica global"""
        producao = {
            'volumes': {
                'artigos': 0,
                'livros': 0,
                'capitulos': 0,
                'eventos': 0
            },
            'recentes': {},  # Últimos 5 anos
            'historico': {},  # Anos anteriores
            'areas_publicacao': Counter(),
            'principais_veiculos': Counter()
        }
        
        ano_atual = datetime.now().year
        ano_corte = ano_atual - 5
        
        for dados in self.dataframes.values():
            for tipo in ['ARTIGOS-PUBLICADOS', 'LIVROS-PUBLICADOS', 'CAPITULOS-LIVROS', 'TRABALHOS-EVENTOS']:
                if tipo in dados and not dados[tipo].empty:
                    df = dados[tipo]
                    total = len(df)
                    producao['volumes'][tipo.split('-')[0].lower()] = total
                    
                    # Separar produção recente e histórica
                    if 'ANO' in df.columns:
                        recentes = len(df[df['ANO'].astype(int) >= ano_corte])
                        historico = total - recentes
                        
                        tipo_norm = tipo.split('-')[0].lower()
                        producao['recentes'][tipo_norm] = recentes
                        producao['historico'][tipo_norm] = historico
        
        return producao

    def _analyze_impacto_producao(self):
        """Análise detalhada do impacto da produção"""
        citacoes = []
        sjr_values = []
        total_artigos = 0
        artigos_q1 = 0
        
        # Coletar dados
        for dados in self.dataframes.values():
            if 'ARTIGOS-PUBLICADOS' in dados:
                df = dados['ARTIGOS-PUBLICADOS']
                total_artigos += len(df)
                
                if 'SCIMAGO_Total_Cites_(3years)' in df.columns:
                    valores = df['SCIMAGO_Total_Cites_(3years)'].dropna()
                    citacoes.extend([float(v) for v in valores if float(v) > 0])
                
                if 'SCIMAGO_SJR' in df.columns:
                    valores = df['SCIMAGO_SJR'].dropna()
                    sjr_values.extend([float(v) for v in valores if float(v) > 0])
                
                if 'SCIMAGO_Quartile' in df.columns:
                    artigos_q1 += len(df[df['SCIMAGO_Quartile'] == 'Q1'])
        
        # Garantir valores default para evitar erros
        if not citacoes:
            citacoes = [0]
        if not sjr_values:
            sjr_values = [0]
        
        return {
            'citacoes': {
                'distribuicao': citacoes,
                'media': np.mean(citacoes),
                'mediana': np.median(citacoes),
                'quartis': np.percentile(citacoes, [25, 50, 75])
            },
            'metricas': {
                'citacoes_por_artigo': sum(citacoes) / total_artigos if total_artigos > 0 else 0,
                'sjr_medio': np.mean(sjr_values),
                'percentual_q1': (artigos_q1 / total_artigos * 100) if total_artigos > 0 else 0,
                'total_artigos': total_artigos
            }
        }

    def _analyze_citations_distribution(self):
        """Analisa a distribuição de citações"""
        citacoes = []
        for dados in self.dataframes.values():
            if 'ARTIGOS-PUBLICADOS' in dados and 'SCIMAGO_Total_Cites_(3years)' in dados['ARTIGOS-PUBLICADOS'].columns:
                valores = dados['ARTIGOS-PUBLICADOS']['SCIMAGO_Total_Cites_(3years)'].dropna()
                citacoes.extend([float(v) for v in valores if v > 0])  # Converte para float e remove zeros
        
        # Garantir que há dados válidos
        if not citacoes:
            citacoes = [0]  # Valor default para evitar erro
        
        return {
            'distribuicao': citacoes,
            'media': np.mean(citacoes),
            'mediana': np.median(citacoes),
            'quartis': np.percentile(citacoes, [25, 50, 75])
        }

    def _analyze_journal_metrics(self):
        """Analisa métricas dos periódicos"""
        journals = defaultdict(list)
        for dados in self.dataframes.values():
            if 'ARTIGOS-PUBLICADOS' in dados:
                df = dados['ARTIGOS-PUBLICADOS']
                if 'REVISTA' in df.columns and 'SCIMAGO_SJR' in df.columns:
                    for _, row in df.iterrows():
                        journals[row['REVISTA']].append({
                            'sjr': row.get('SCIMAGO_SJR', 0),
                            'h_index': row.get('SCIMAGO_H_index', 0)
                        })
        
        return {
            'metricas_por_journal': dict(journals),
            'total_journals': len(journals),
            'top_journals': sorted(journals.items(), key=lambda x: np.mean([m['sjr'] for m in x[1]]), reverse=True)[:10]
        }

    def _calculate_impact_metrics(self):
        """Calcula métricas de impacto agregadas"""
        total_citacoes = 0
        total_artigos = 0
        sjr_medio = []
        
        for dados in self.dataframes.values():
            if 'ARTIGOS-PUBLICADOS' in dados:
                df = dados['ARTIGOS-PUBLICADOS']
                total_artigos += len(df)
                
                if 'SCIMAGO_Total_Cites_(3years)' in df.columns:
                    total_citacoes += df['SCIMAGO_Total_Cites_(3years)'].sum()
                
                if 'SCIMAGO_SJR' in df.columns:
                    sjr_medio.extend(df['SCIMAGO_SJR'].dropna().tolist())
        
        return {
            'citacoes_por_artigo': total_citacoes / total_artigos if total_artigos > 0 else 0,
            'sjr_medio': np.mean(sjr_medio) if sjr_medio else 0,
            'percentual_q1': self._calculate_q1_percentage()
        }

    def _calculate_q1_percentage(self):
        """Calcula o percentual de publicações em periódicos Q1"""
        total_artigos = 0
        artigos_q1 = 0
        
        for dados in self.dataframes.values():
            if 'ARTIGOS-PUBLICADOS' in dados and 'SCIMAGO_Quartile' in dados['ARTIGOS-PUBLICADOS'].columns:
                df = dados['ARTIGOS-PUBLICADOS']
                total_artigos += len(df)
                artigos_q1 += len(df[df['SCIMAGO_Quartile'] == 'Q1'])
        
        return (artigos_q1 / total_artigos * 100) if total_artigos > 0 else 0

    def _analyze_areas_conhecimento(self):
        """Análise das áreas de conhecimento"""
        areas = {
            'grandes_areas': Counter(),
            'subareas': Counter(),
            'interdisciplinaridade': defaultdict(set),
            'concentracao_areas': {}
        }

        for dados in self.dataframes.values():
            if 'AREAS-DE-ATUACAO' in dados:
                areas_doc = dados['AREAS-DE-ATUACAO']
                if not areas_doc.empty:
                    for _, area in areas_doc.iterrows():
                        grande_area = area.get('GRANDE-AREA')
                        subarea = area.get('SUBAREA')
                        
                        if pd.notna(grande_area):
                            areas['grandes_areas'][grande_area] += 1
                            if pd.notna(subarea):
                                areas['subareas'][subarea] += 1
                                areas['interdisciplinaridade'][grande_area].add(subarea)

        # Calcular concentração
        total = sum(areas['grandes_areas'].values())
        areas['concentracao_areas'] = {
            area: (count/total)*100 
            for area, count in areas['grandes_areas'].items()
        }

        return areas

    def _analyze_tendencias(self):
        """Análise de tendências temporais com foco em crescimento"""
        tendencias = {
            'evolucao_anual': defaultdict(Counter),
            'crescimento_areas': {},
            'temas_emergentes': Counter()
        }
        
        # Calcular crescimento por área
        dados_anuais = defaultdict(lambda: defaultdict(int))
        for dados in self.dataframes.values():
            for tipo in ['ARTIGOS-PUBLICADOS', 'LIVROS-PUBLICADOS', 'CAPITULOS-LIVROS', 'TRABALHOS-EVENTOS']:
                if tipo in dados and not dados[tipo].empty:
                    df = dados[tipo]
                    if 'ANO' in df.columns:
                        for ano in df['ANO'].astype(int).unique():
                            dados_anuais[tipo][ano] += len(df[df['ANO'].astype(int) == ano])
        
        # Calcular taxa de crescimento
        for tipo, anos in dados_anuais.items():
            if len(anos) >= 2:
                anos_ord = sorted(anos.keys())
                primeiro_ano = sum(anos[ano] for ano in anos_ord[:2]) / 2  # Média dos 2 primeiros anos
                ultimo_ano = sum(anos[ano] for ano in anos_ord[-2:]) / 2   # Média dos 2 últimos anos
                
                if primeiro_ano > 0:
                    crescimento = ((ultimo_ano - primeiro_ano) / primeiro_ano) * 100
                    tipo_norm = tipo.split('-')[0].title()
                    tendencias['crescimento_areas'][tipo_norm] = crescimento
        
        return tendencias

    def _analyze_colaboracoes(self):
        """Análise de colaborações"""
        colaboracoes = {
            'entre_instituicoes': Counter(),
            'redes_pesquisa': defaultdict(set),
            'grupos_tematicos': defaultdict(set)
        }

        # [Implementar análise de colaborações aqui]

        return colaboracoes

    def _analyze_orientacoes(self):
        """Análise das orientações"""
        orientacoes = {
            'total': {
                'mestrado': 0,
                'doutorado': 0,
                'pos_doutorado': 0,
                'outras': 0
            },
            'em_andamento': {
                'mestrado': 0,
                'doutorado': 0,
                'pos_doutorado': 0,
                'outras': 0
            },
            'evolucao_temporal': defaultdict(int),
            'areas': Counter(),
            'detalhamento': {}
        }

        for dados in self.dataframes.values():
            # Mestrado
            if 'ORIENTACOES-MESTRADO' in dados:
                df = dados['ORIENTACOES-MESTRADO']
                orientacoes['total']['mestrado'] += len(df)
                
                if 'ANO' in df.columns:
                    for ano in df['ANO'].dropna():
                        orientacoes['evolucao_temporal'][int(ano)] += 1

            # Doutorado
            if 'ORIENTACOES-DOUTORADO' in dados:
                df = dados['ORIENTACOES-DOUTORADO']
                orientacoes['total']['doutorado'] += len(df)
                
                if 'ANO' in df.columns:
                    for ano in df['ANO'].dropna():
                        orientacoes['evolucao_temporal'][int(ano)] += 1

            # Pós-Doutorado
            if 'ORIENTACOES-POS-DOUTORADO' in dados:
                df = dados['ORIENTACOES-POS-DOUTORADO']
                orientacoes['total']['pos_doutorado'] += len(df)
                
                if 'ANO' in df.columns:
                    for ano in df['ANO'].dropna():
                        orientacoes['evolucao_temporal'][int(ano)] += 1

            # Outras Orientações
            if 'OUTRAS-ORIENTACOES' in dados:
                df = dados['OUTRAS-ORIENTACOES']
                orientacoes['total']['outras'] += len(df)
                
                if 'ANO' in df.columns:
                    for ano in df['ANO'].dropna():
                        orientacoes['evolucao_temporal'][int(ano)] += 1

        # Calcular médias e porcentagens
        total_docentes = len(self.dataframes)
        if total_docentes > 0:
            orientacoes['detalhamento'] = {
                'Media_orientacoes_mestrado': orientacoes['total']['mestrado'] / total_docentes,
                'Media_orientacoes_doutorado': orientacoes['total']['doutorado'] / total_docentes,
                'Media_orientacoes_pos_doc': orientacoes['total']['pos_doutorado'] / total_docentes,
                'Total_orientacoes': sum(orientacoes['total'].values()),
                'Media_orientacoes_por_docente': sum(orientacoes['total'].values()) / total_docentes
            }

        return orientacoes

    def _get_highest_degree(self, formacao):
        """Determina a maior titulação"""
        ordem = ['GRADUACAO', 'ESPECIALIZACAO', 'MESTRADO', 'DOUTORADO', 'POS-DOUTORADO']
        niveis = formacao['NIVEL'].unique()
        for nivel in reversed(ordem):
            if nivel in niveis:
                return nivel
        return 'Não informado'
    
    def _analyze_production(self, dados):
        """Análise detalhada da produção científica"""
        producao = {
            'artigos': {
                'total': 0,
                'ultimos_5_anos': 0,
                'principais_revistas': Counter(),
                'impacto': {
                    'citacoes_total': 0,
                    'sjr_medio': 0.0,
                    'h_index_medio': 0.0
                }
            },
            'livros': {
                'total': 0,
                'principais_editoras': Counter(),
                'por_tipo': Counter()
            },
            'eventos': {
                'total': 0,
                'principais_tipos': Counter(),
                'internacionais': 0
            }
        }
        
        ano_atual = pd.Timestamp.now().year
        
        # Análise de artigos
        if 'ARTIGOS-PUBLICADOS' in dados:
            artigos = dados['ARTIGOS-PUBLICADOS']
            producao['artigos']['total'] = len(artigos)
            
            # Artigos recentes
            artigos_recentes = artigos[artigos['ANO'].astype(int) >= (ano_atual - 5)]
            producao['artigos']['ultimos_5_anos'] = len(artigos_recentes)
            
            # Análise de revistas e impacto
            for _, artigo in artigos.iterrows():
                revista = artigo.get('REVISTA')
                if pd.notna(revista):
                    producao['artigos']['principais_revistas'][revista] += 1
                
                # Métricas Scimago
                if 'SCIMAGO_SJR' in artigo and pd.notna(artigo['SCIMAGO_SJR']):
                    producao['artigos']['impacto']['sjr_medio'] += artigo['SCIMAGO_SJR']
                if 'SCIMAGO_H_index' in artigo and pd.notna(artigo['SCIMAGO_H_index']):
                    producao['artigos']['impacto']['h_index_medio'] += artigo['SCIMAGO_H_index']
            
            # Calcular médias
            if producao['artigos']['total'] > 0:
                producao['artigos']['impacto']['sjr_medio'] /= producao['artigos']['total']
                producao['artigos']['impacto']['h_index_medio'] /= producao['artigos']['total']
        
        # Análise de livros
        if 'LIVROS-PUBLICADOS' in dados:
            livros = dados['LIVROS-PUBLICADOS']
            producao['livros']['total'] = len(livros)
            
            for _, livro in livros.iterrows():
                editora = livro.get('EDITORA')
                tipo = livro.get('TIPO')
                
                if pd.notna(editora):
                    producao['livros']['principais_editoras'][editora] += 1
                if pd.notna(tipo):
                    producao['livros']['por_tipo'][tipo] += 1
        
        # Análise de eventos
        if 'TRABALHOS-EVENTOS' in dados:
            eventos = dados['TRABALHOS-EVENTOS']
            producao['eventos']['total'] = len(eventos)
            
            for _, evento in eventos.iterrows():
                tipo = evento.get('TIPO')
                pais = evento.get('PAIS')
                
                # Contar eventos internacionais
                if pd.notna(pais) and pais.upper() != 'BRASIL':
                    producao['eventos']['internacionais'] += 1
        
        return producao
    
    def _analyze_temporal_data(self, dados):
        """Análise temporal da produção"""
        temporal = {
            'producao_por_ano': Counter(),
            'primeiro_registro': 9999,
            'ultimo_registro': 0
        }
        
        for tipo in ['ARTIGOS-PUBLICADOS', 'LIVROS-PUBLICADOS', 'TRABALHOS-EVENTOS']:
            if tipo in dados:
                anos = dados[tipo]['ANO'].dropna().astype(int)
                for ano in anos:
                    temporal['producao_por_ano'][ano] += 1
                    temporal['primeiro_registro'] = min(temporal['primeiro_registro'], ano)
                    temporal['ultimo_registro'] = max(temporal['ultimo_registro'], ano)
        
        return temporal
    
    def _merge_temporal_stats(self, total, new):
        """Combina estatísticas temporais"""
        total['producao_por_ano'].update(new['producao_por_ano'])
        return total
