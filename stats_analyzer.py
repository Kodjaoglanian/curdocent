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
            'impacto': self._analyze_impacto_producao(),
            'areas': self._analyze_areas_conhecimento(),
            'colaboracao': self._analyze_colaboracoes(),
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
            'por_ano': defaultdict(Counter),
            'areas_publicacao': Counter(),
            'principais_veiculos': Counter(),
            'idiomas': Counter()
        }

        for dados in self.dataframes.values():
            # Contagem de artigos
            if 'ARTIGOS-PUBLICADOS' in dados:
                producao['volumes']['artigos'] += len(dados['ARTIGOS-PUBLICADOS'])
            
            # Contagem de livros
            if 'LIVROS-PUBLICADOS' in dados:
                producao['volumes']['livros'] += len(dados['LIVROS-PUBLICADOS'])
            
            # Contagem de capítulos
            if 'CAPITULOS-LIVROS' in dados:
                producao['volumes']['capitulos'] += len(dados['CAPITULOS-LIVROS'])
            
            # Contagem de trabalhos em eventos
            if 'TRABALHOS-EVENTOS' in dados:
                producao['volumes']['eventos'] += len(dados['TRABALHOS-EVENTOS'])

        return producao

    def _analyze_impacto_producao(self):
        """Análise do impacto da produção"""
        impacto = {
            'artigos_por_docente': [],
            'producao_recente': defaultdict(int),  # últimos 5 anos
            'principais_colaboracoes': Counter(),
            'revistas_alto_impacto': Counter()  # revistas com DOI
        }

        for dados in self.dataframes.values():
            if 'ARTIGOS-PUBLICADOS' in dados:
                artigos = dados['ARTIGOS-PUBLICADOS']
                total_artigos = len(artigos)
                impacto['artigos_por_docente'].append(total_artigos)

                if not artigos.empty:
                    for _, artigo in artigos.iterrows():
                        ano = artigo.get('ANO')
                        if pd.notna(ano) and int(ano) >= (self.ano_atual - 5):
                            impacto['producao_recente'][int(ano)] += 1
                        
                        doi = artigo.get('DOI')
                        revista = artigo.get('REVISTA')
                        if pd.notna(doi) and pd.notna(revista):
                            impacto['revistas_alto_impacto'][revista] += 1

        return impacto

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
        """Análise de tendências temporais"""
        tendencias = {
            'evolucao_anual': defaultdict(Counter),
            'temas_emergentes': Counter(),
            'crescimento_areas': {},
            'producao_projetada': {}
        }

        # Análise de evolução temporal
        for dados in self.dataframes.values():
            for tipo in ['ARTIGOS-PUBLICADOS', 'LIVROS-PUBLICADOS', 'TRABALHOS-EVENTOS']:
                if tipo in dados:
                    df = dados[tipo]
                    if not df.empty and 'ANO' in df.columns:
                        for _, row in df.iterrows():
                            ano = row.get('ANO')
                            if pd.notna(ano):
                                tendencias['evolucao_anual'][int(ano)][tipo] += 1

        # Calcular tendências de crescimento
        anos = sorted(tendencias['evolucao_anual'].keys())
        if len(anos) >= 2:
            for tipo in ['ARTIGOS-PUBLICADOS', 'LIVROS-PUBLICADOS', 'TRABALHOS-EVENTOS']:
                valores = [tendencias['evolucao_anual'][ano][tipo] for ano in anos]
                if len(valores) >= 2:
                    crescimento = (valores[-1] - valores[0]) / len(anos)
                    tendencias['crescimento_areas'][tipo] = crescimento

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
                'principais_revistas': Counter()
            },
            'livros': {
                'total': 0,
                'principais_editoras': Counter()
            },
            'eventos': {
                'total': 0,
                'principais_tipos': Counter()
            }
        }
        
        ano_atual = pd.Timestamp.now().year
        
        if 'ARTIGOS-PUBLICADOS' in dados:
            artigos = dados['ARTIGOS-PUBLICADOS']
            producao['artigos']['total'] = len(artigos)
            producao['artigos']['ultimos_5_anos'] = len(
                artigos[artigos['ANO'].astype(int) >= (ano_atual - 5)]
            )
            for revista in artigos['REVISTA'].dropna():
                producao['artigos']['principais_revistas'][revista] += 1
        
        if 'LIVROS-PUBLICADOS' in dados:
            livros = dados['LIVROS-PUBLICADOS']
            producao['livros']['total'] = len(livros)
            for editora in livros['EDITORA'].dropna():
                producao['livros']['principais_editoras'][editora] += 1
        
        if 'TRABALHOS-EVENTOS' in dados:
            eventos = dados['TRABALHOS-EVENTOS']
            producao['eventos']['total'] = len(eventos)
            for tipo in eventos['TIPO'].dropna():
                producao['eventos']['principais_tipos'][tipo] += 1
        
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
