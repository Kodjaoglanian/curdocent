import numpy as np
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                            QTableWidget, QTableWidgetItem, QPushButton,
                            QTabWidget)
from matplotlib.figure import Figure
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from PyQt5.QtCore import Qt
from collections import defaultdict, Counter
import pandas as pd
from datetime import datetime
from scholarly import scholarly

class StatsDashboard:
    def __init__(self, dataframes, analyzer):
        self.dataframes = dataframes
        self.analyzer = analyzer
        
    def create_global_analysis(self):
        """Cria painel de análise global"""
        container = QTabWidget()
        
        # Aba 1: Visão Geral
        overview_tab = QWidget()
        overview_layout = QVBoxLayout(overview_tab)
        
        # Métricas principais
        overview_layout.addWidget(self.create_metrics_panel())
        
        # Gráficos de produção e temporal
        charts_widget = QWidget()
        charts_layout = QHBoxLayout(charts_widget)
        charts_layout.addWidget(self.create_production_chart())
        charts_layout.addWidget(self.create_temporal_analysis())
        overview_layout.addWidget(charts_widget)
        
        container.addTab(overview_tab, "Visão Geral")
        
        # Aba 2: Análise de Impacto
        impact_tab = QWidget()
        impact_layout = QVBoxLayout(impact_tab)
        
        # Adicionar gráficos de impacto
        impact_charts = QWidget()
        impact_charts_layout = QHBoxLayout(impact_charts)
        impact_charts_layout.addWidget(self.create_impact_analysis())
        impact_charts_layout.addWidget(self.create_area_distribution())
        impact_layout.addWidget(impact_charts)
        
        # Adicionar métricas de impacto
        impact_layout.addWidget(self._create_impact_metrics_table())
        
        container.addTab(impact_tab, "Análise de Impacto")
        
        # Aba 3: Colaborações
        collab_tab = QWidget()
        collab_layout = QVBoxLayout(collab_tab)
        
        # Adicionar rede de colaborações
        collab_layout.addWidget(self._create_collaboration_analysis())
        
        container.addTab(collab_tab, "Colaborações")
        
        # Aba 4: Tendências
        trends_tab = QWidget()
        trends_layout = QVBoxLayout(trends_tab)
        
        # Adicionar análise de tendências
        trends_layout.addWidget(self._create_trends_analysis())
        
        container.addTab(trends_tab, "Tendências")
        
        return container
        
    def create_individual_analysis(self, curriculo_id):
        """Cria painel de análise individual"""
        container = QTabWidget()
        
        # Aba 1: Perfil do Pesquisador
        profile_tab = QWidget()
        profile_layout = QVBoxLayout(profile_tab)
        
        # Informações básicas do pesquisador
        profile_layout.addWidget(self._create_researcher_profile(curriculo_id))
        
        # Métricas individuais
        profile_layout.addWidget(self._create_individual_metrics(curriculo_id))
        
        container.addTab(profile_tab, "Perfil")
        
        # Aba 2: Produção Científica
        production_tab = QWidget()
        prod_layout = QVBoxLayout(production_tab)
        
        # Análise detalhada da produção
        prod_layout.addWidget(self._create_detailed_production(curriculo_id))
        
        container.addTab(production_tab, "Produção")
        
        # Aba 3: Impacto Individual
        impact_tab = QWidget()
        impact_layout = QVBoxLayout(impact_tab)
        
        # Análise de impacto individual
        impact_layout.addWidget(self._create_individual_impact(curriculo_id))
        
        container.addTab(impact_tab, "Impacto")
        
        return container

    def _create_researcher_profile(self, curriculo_id):
        """Cria perfil detalhado do pesquisador"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        dados = self.dataframes[curriculo_id]
        
        if 'DADOS-GERAIS' in dados:
            info = dados['DADOS-GERAIS'].iloc[0]
            
            # Cabeçalho com nome e título
            header = QLabel(f"<h2>{info.get('NOME-COMPLETO', 'Nome não disponível')}</h2>")
            header.setStyleSheet("color: #2c3e50; margin-bottom: 10px;")
            layout.addWidget(header)
            
            # Criar cards com informações
            cards_widget = QWidget()
            cards_layout = QHBoxLayout(cards_widget)
            
            # Formação
            if 'FORMACAO-ACADEMICA' in dados:
                formacao = self._get_highest_formation(dados['FORMACAO-ACADEMICA'])
                cards_layout.addWidget(self._create_info_card(
                    "Formação",
                    formacao,
                    icon="🎓"
                ))
            
            # Área principal
            if 'AREAS-DE-ATUACAO' in dados and not dados['AREAS-DE-ATUACAO'].empty:
                area = dados['AREAS-DE-ATUACAO'].iloc[0].get('AREA', 'Não informada')
                cards_layout.addWidget(self._create_info_card(
                    "Área Principal",
                    area,
                    icon="📚"
                ))
            
            # Tempo de carreira
            if 'ATUACOES-PROFISSIONAIS' in dados:
                anos_carreira = self._calculate_career_time(dados['ATUACOES-PROFISSIONAIS'])
                cards_layout.addWidget(self._create_info_card(
                    "Tempo de Carreira",
                    f"{anos_carreira} anos",
                    icon="⏳"
                ))
            
            layout.addWidget(cards_widget)
        
        return widget

    def _create_individual_metrics(self, curriculo_id):
        """Cria painel com métricas individuais do pesquisador"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        dados = self.dataframes[curriculo_id]
        
        # Calcular métricas
        metricas = {
            'Total de Artigos': len(dados.get('ARTIGOS-PUBLICADOS', pd.DataFrame())),
            'Média de Impacto': self._calculate_average_impact(dados),
            'Índice de Colaboração': self._calculate_collaboration_index(dados),
            'Produtividade Anual': self._calculate_yearly_productivity(dados)
        }
        
        # Buscar Índice H
        nome_pesquisador = dados['DADOS-GERAIS']['NOME-COMPLETO'].iloc[0]
        indice_h = self._get_h_index(nome_pesquisador)
        metricas['Índice H'] = indice_h
        
        # Criar gráfico de radar com as métricas
        radar_chart = self._create_metrics_radar_chart(metricas)
        layout.addWidget(radar_chart)
        
        # Adicionar Índice H como texto
        h_index_label = QLabel(f"Índice H: {indice_h}")
        h_index_label.setStyleSheet("font-size: 16px; color: #2c3e50; margin-top: 10px;")
        layout.addWidget(h_index_label)
        
        return widget

    def _create_detailed_production(self, curriculo_id):
        """Cria análise detalhada da produção"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        dados = self.dataframes[curriculo_id]
        
        # Gráfico de evolução temporal
        temporal_chart = self._create_individual_temporal_chart(dados)
        layout.addWidget(temporal_chart)
        
        # Tabela de resumo por tipo de produção
        summary_table = self._create_production_summary_table(dados)
        layout.addWidget(summary_table)
        
        return widget

    def _create_individual_impact(self, curriculo_id):
        """Cria análise de impacto individual"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        dados = self.dataframes[curriculo_id]
        
        if 'ARTIGOS-PUBLICADOS' in dados and 'SCIMAGO_SJR' in dados['ARTIGOS-PUBLICADOS'].columns:
            # Gráfico de evolução do impacto
            impact_chart = self._create_individual_impact_chart(dados)
            layout.addWidget(impact_chart)
            
            # Comparação com média da área
            comparison_chart = self._create_impact_comparison_chart(dados)
            layout.addWidget(comparison_chart)
        else:
            layout.addWidget(QLabel("Dados de impacto não disponíveis"))
        
        return widget

    def create_metrics_panel(self):
        """Cria painel com métricas principais"""
        widget = QWidget()
        layout = QHBoxLayout(widget)
        
        # Total de docentes
        total_docentes = len(self.dataframes)
        layout.addWidget(self._create_metric_card(
            "Total de Docentes",
            total_docentes,
            "👥"
        ))
        
        # Total de artigos
        total_artigos = sum(
            len(dados['ARTIGOS-PUBLICADOS']) 
            for dados in self.dataframes.values() 
            if 'ARTIGOS-PUBLICADOS' in dados
        )
        layout.addWidget(self._create_metric_card(
            "Total de Artigos",
            total_artigos,
            "📚"
        ))
        
        # Total de citações
        total_citacoes = 0
        for dados in self.dataframes.values():
            if 'ARTIGOS-PUBLICADOS' in dados:
                df = dados['ARTIGOS-PUBLICADOS']
                if 'SCIMAGO_Total_Cites_(3years)' in df.columns:
                    total_citacoes += df['SCIMAGO_Total_Cites_(3years)'].sum()
        
        layout.addWidget(self._create_metric_card(
            "Total de Citações",
            int(total_citacoes),
            "📊"
        ))
        
        # Média SJR
        sjr_values = []
        for dados in self.dataframes.values():
            if 'ARTIGOS-PUBLICADOS' in dados:
                df = dados['ARTIGOS-PUBLICADOS']
                if 'SCIMAGO_SJR' in df.columns:
                    sjr_values.extend(df['SCIMAGO_SJR'].dropna())
        
        media_sjr = np.mean(sjr_values) if sjr_values else 0
        layout.addWidget(self._create_metric_card(
            "SJR Médio",
            f"{media_sjr:.2f}",
            "⭐"
        ))
        
        return widget

    def create_production_chart(self):
        """Cria gráfico de produção científica"""
        fig = Figure(figsize=(6, 4))
        canvas = FigureCanvas(fig)
        ax = fig.add_subplot(111)
        
        # Coletar dados de produção
        producao = {
            'Artigos': 0,
            'Livros': 0,
            'Capítulos': 0,
            'Eventos': 0
        }
        
        for dados in self.dataframes.values():
            if 'ARTIGOS-PUBLICADOS' in dados:
                producao['Artigos'] += len(dados['ARTIGOS-PUBLICADOS'])
            if 'LIVROS-PUBLICADOS' in dados:
                producao['Livros'] += len(dados['LIVROS-PUBLICADOS'])
            if 'CAPITULOS-LIVROS' in dados:
                producao['Capítulos'] += len(dados['CAPITULOS-LIVROS'])
            if 'TRABALHOS-EVENTOS' in dados:
                producao['Eventos'] += len(dados['TRABALHOS-EVENTOS'])
        
        # Criar gráfico
        colors = ['#3498db', '#2ecc71', '#e74c3c', '#f1c40f']
        bars = ax.bar(range(len(producao)), producao.values(), color=colors)
        
        # Configurar eixos
        ax.set_xticks(range(len(producao)))
        ax.set_xticklabels(producao.keys(), rotation=45)
        ax.set_title('Produção por Tipo', pad=15)
        
        # Adicionar valores sobre as barras
        for bar in bars:
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height,
                   f'{int(height)}',
                   ha='center', va='bottom')
        
        fig.tight_layout()
        return canvas

    def create_temporal_analysis(self):
        """Cria análise temporal da produção"""
        fig = Figure(figsize=(6, 4))
        canvas = FigureCanvas(fig)
        ax = fig.add_subplot(111)
        
        # Coletar dados temporais
        producao_anual = defaultdict(int)
        
        for dados in self.dataframes.values():
            if 'ARTIGOS-PUBLICADOS' in dados:
                df = dados['ARTIGOS-PUBLICADOS']
                if 'ANO' in df.columns:
                    for ano in df['ANO'].dropna():
                        try:
                            producao_anual[int(ano)] += 1
                        except ValueError:
                            continue
        
        if producao_anual:
            anos = sorted(producao_anual.keys())
            valores = [producao_anual[ano] for ano in anos]
            
            # Criar gráfico
            ax.plot(anos, valores, marker='o', color='#3498db', linewidth=2)
            ax.set_xlabel('Ano')
            ax.set_ylabel('Número de Publicações')
            ax.set_title('Evolução Temporal da Produção')
            ax.grid(True, alpha=0.3)
            
            # Adicionar valores sobre os pontos
            for x, y in zip(anos, valores):
                ax.text(x, y, str(y), ha='center', va='bottom')
            
            # Rotacionar labels do eixo x
            plt.setp(ax.get_xticklabels(), rotation=45)
            
        fig.tight_layout()
        return canvas

    def create_area_distribution(self):
        """Cria gráfico de distribuição por área"""
        fig = Figure(figsize=(6, 4))
        canvas = FigureCanvas(fig)
        ax = fig.add_subplot(111)
        
        # Coletar áreas
        areas = Counter()
        for dados in self.dataframes.values():
            if 'AREAS-DE-ATUACAO' in dados:
                df = dados['AREAS-DE-ATUACAO']
                if 'AREA' in df.columns:
                    for area in df['AREA'].dropna():
                        areas[area] += 1
        
        if areas:
            # Pegar top 5 áreas
            top_areas = dict(areas.most_common(5))
            
            # Criar gráfico de pizza
            wedges, texts, autotexts = ax.pie(
                top_areas.values(),
                labels=top_areas.keys(),
                autopct='%1.1f%%',
                colors=plt.cm.Pastel1(np.linspace(0, 1, len(top_areas)))
            )
            
            ax.set_title('Distribuição por Área')
            plt.setp(autotexts, size=8, weight="bold")
            plt.setp(texts, size=8)
            
        fig.tight_layout()
        return canvas

    def create_impact_analysis(self):
        """Cria análise de impacto"""
        fig = Figure(figsize=(6, 4))
        canvas = FigureCanvas(fig)
        ax = fig.add_subplot(111)
        
        # Coletar dados de impacto
        impacto_por_ano = defaultdict(list)
        
        for dados in self.dataframes.values():
            if 'ARTIGOS-PUBLICADOS' in dados:
                df = dados['ARTIGOS-PUBLICADOS']
                if 'ANO' in df.columns and 'SCIMAGO_SJR' in df.columns:
                    for _, row in df.iterrows():
                        if pd.notna(row['ANO']) and pd.notna(row['SCIMAGO_SJR']):
                            ano = int(row['ANO'])
                            impacto_por_ano[ano].append(float(row['SCIMAGO_SJR']))
        
        if impacto_por_ano:
            anos = sorted(impacto_por_ano.keys())
            medias = [np.mean(impacto_por_ano[ano]) for ano in anos]
            
            ax.plot(anos, medias, marker='o', color='#e74c3c', linewidth=2)
            ax.set_xlabel('Ano')
            ax.set_ylabel('SJR Médio')
            ax.set_title('Evolução do Impacto')
            ax.grid(True, alpha=0.3)
            
            # Adicionar valores sobre os pontos
            for x, y in zip(anos, medias):
                ax.text(x, y, f'{y:.2f}', ha='center', va='bottom')
            
            # Rotacionar labels do eixo x
            plt.setp(ax.get_xticklabels(), rotation=45)
            
        fig.tight_layout()
        return canvas

    def _create_metric_card(self, title, value, icon):
        """Cria card de métrica estilizado"""
        card = QWidget()
        card.setStyleSheet("""
            QWidget {
                background-color: #f8f9fa;
                border-radius: 10px;
                padding: 15px;
                margin: 5px;
            }
            QLabel {
                color: #2c3e50;
            }
        """)
        
        layout = QVBoxLayout(card)
        layout.setSpacing(5)
        
        # Ícone e título
        header = QLabel(f"{icon} {title}")
        header.setStyleSheet("font-size: 14px; font-weight: bold;")
        layout.addWidget(header)
        
        # Valor
        value_label = QLabel(str(value))
        value_label.setStyleSheet("font-size: 24px; font-weight: bold; color: #3498db;")
        value_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(value_label)
        
        return card

    def _create_info_card(self, title, value, icon=""):
        """Cria card de informação estilizado"""
        card = QWidget()
        card.setStyleSheet("""
            QWidget {
                background-color: white;
                border-radius: 10px;
                padding: 15px;
                border: 1px solid #ddd;
            }
            QLabel {
                margin: 5px;
            }
        """)
        
        layout = QVBoxLayout(card)
        
        # Título com ícone
        title_label = QLabel(f"{icon} {title}")
        title_label.setStyleSheet("font-size: 14px; color: #666; font-weight: bold;")
        layout.addWidget(title_label)
        
        # Valor
        value_label = QLabel(str(value))
        value_label.setStyleSheet("font-size: 18px; color: #2980b9; font-weight: bold;")
        layout.addWidget(value_label)
        
        return card

    def _get_highest_formation(self, formacao):
        """Determina a maior titulação"""
        ordem = ['GRADUACAO', 'ESPECIALIZACAO', 'MESTRADO', 'DOUTORADO', 'POS-DOUTORADO']
        niveis = formacao['NIVEL'].unique()
        for nivel in reversed(ordem):
            if nivel in niveis:
                return nivel
        return 'Não informado'

    def _calculate_average_impact(self, dados):
        """Calcula o impacto médio baseado no SJR dos artigos"""
        if 'ARTIGOS-PUBLICADOS' not in dados:
            return 0
        
        df = dados['ARTIGOS-PUBLICADOS']
        if 'SCIMAGO_SJR' not in df.columns:
            return 0
        
        sjr_values = df['SCIMAGO_SJR'].dropna()
        return sjr_values.mean() if len(sjr_values) > 0 else 0

    def _calculate_collaboration_index(self, dados):
        """Calcula o índice de colaboração baseado em coautorias"""
        total_autores = 0
        total_artigos = 0
        
        if 'ARTIGOS-PUBLICADOS' in dados:
            df = dados['ARTIGOS-PUBLICADOS']
            total_artigos += len(df)
            
            # Se houver coluna de autores, conte-os
            if 'AUTORES' in df.columns:
                for autores in df['AUTORES'].dropna():
                    # Assume que os autores são separados por vírgula ou ponto-e-vírgula
                    separadores = [';', ',']
                    for sep in separadores:
                        if sep in autores:
                            total_autores += len(autores.split(sep))
                            break
                    else:  # Se não encontrar separadores, conta como 1 autor
                        total_autores += 1

        return total_autores / total_artigos if total_artigos > 0 else 0

    def _calculate_yearly_productivity(self, dados):
        """Calcula a produtividade anual do pesquisador"""
        if 'ARTIGOS-PUBLICADOS' not in dados:
            return 0
        
        df = dados['ARTIGOS-PUBLICADOS']
        if 'ANO' not in df.columns:
            return 0
        
        anos = df['ANO'].dropna().astype(int)
        if anos.empty:
            return 0
        
        primeiro_ano = anos.min()
        ultimo_ano = anos.max()
        
        return len(anos) / (ultimo_ano - primeiro_ano + 1) if (ultimo_ano - primeiro_ano + 1) > 0 else 0

    def _create_metrics_radar_chart(self, metricas):
        """Cria gráfico de radar com as métricas"""
        labels = list(metricas.keys())
        values = list(metricas.values())
        
        num_vars = len(labels)
        angles = np.linspace(0, 2 * np.pi, num_vars, endpoint=False).tolist()
        values += values[:1]
        angles += angles[:1]
        
        fig, ax = plt.subplots(figsize=(6, 6), subplot_kw=dict(polar=True))
        ax.plot(angles, values, 'o-', linewidth=2)
        ax.fill(angles, values, alpha=0.25)
        ax.set_yticklabels([])
        ax.set_xticks(angles[:-1])
        ax.set_xticklabels(labels)
        ax.set_title('Métricas Individuais')
        
        canvas = FigureCanvas(fig)
        return canvas

    def _create_individual_temporal_chart(self, dados):
        """Cria gráfico de evolução temporal individual"""
        fig = Figure(figsize=(6, 4))
        canvas = FigureCanvas(fig)
        ax = fig.add_subplot(111)
        
        # Coletar dados temporais
        producao_anual = defaultdict(int)
        
        if 'ARTIGOS-PUBLICADOS' in dados:
            df = dados['ARTIGOS-PUBLICADOS']
            if 'ANO' in df.columns:
                for ano in df['ANO'].dropna():
                    try:
                        producao_anual[int(ano)] += 1
                    except ValueError:
                        continue
        
        if producao_anual:
            anos = sorted(producao_anual.keys())
            valores = [producao_anual[ano] for ano in anos]
            
            # Criar gráfico
            ax.plot(anos, valores, marker='o', color='#27ae60', linewidth=2)
            ax.set_xlabel('Ano')
            ax.set_ylabel('Número de Publicações')
            ax.set_title('Evolução Temporal da Produção Individual')
            ax.grid(True, alpha=0.3)
            
            # Adicionar valores sobre os pontos
            for x, y in zip(anos, valores):
                ax.text(x, y, str(y), ha='center', va='bottom')
            
            # Rotacionar labels do eixo x
            plt.setp(ax.get_xticklabels(), rotation=45)
            
        fig.tight_layout()
        return canvas

    def _create_production_summary_table(self, dados):
        """Cria tabela de resumo da produção"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Inicializar dados
        artigos_total = len(dados.get('ARTIGOS-PUBLICADOS', pd.DataFrame()))
        livros_total = len(dados.get('LIVROS-PUBLICADOS', pd.DataFrame()))
        capitulos_total = len(dados.get('CAPITULOS-LIVROS', pd.DataFrame()))
        eventos_total = len(dados.get('TRABALHOS-EVENTOS', pd.DataFrame()))
        
        # Criar tabela
        table = QTableWidget()
        table.setColumnCount(2)
        table.setRowCount(4)
        table.setHorizontalHeaderLabels(['Tipo', 'Quantidade'])
        
        # Preencher tabela
        table.setItem(0, 0, QTableWidgetItem('Artigos'))
        table.setItem(0, 1, QTableWidgetItem(str(artigos_total)))
        table.setItem(1, 0, QTableWidgetItem('Livros'))
        table.setItem(1, 1, QTableWidgetItem(str(livros_total)))
        table.setItem(2, 0, QTableWidgetItem('Capítulos'))
        table.setItem(2, 1, QTableWidgetItem(str(capitulos_total)))
        table.setItem(3, 0, QTableWidgetItem('Eventos'))
        table.setItem(3, 1, QTableWidgetItem(str(eventos_total)))
        
        # Ajustar tamanho das colunas
        table.resizeColumnsToContents()
        
        layout.addWidget(table)
        return widget

    def _create_individual_impact_chart(self, dados):
        """Cria gráfico de evolução do impacto individual"""
        fig = Figure(figsize=(6, 4))
        canvas = FigureCanvas(fig)
        ax = fig.add_subplot(111)
        
        if 'ARTIGOS-PUBLICADOS' not in dados or 'SCIMAGO_SJR' not in dados['ARTIGOS-PUBLICADOS'].columns:
            ax.text(0.5, 0.5, "Dados de impacto não disponíveis", 
                    ha='center', va='center', transform=ax.transAxes, fontsize=14)
            ax.set_xticks([])
            ax.set_yticks([])
            return canvas
        
        # Coletar dados de impacto por ano
        impacto_anual = defaultdict(list)
        
        df = dados['ARTIGOS-PUBLICADOS']
        if 'ANO' in df.columns:
            for _, row in df.iterrows():
                if pd.notna(row['ANO']) and pd.notna(row['SCIMAGO_SJR']):
                    try:
                        ano = int(row['ANO'])
                        sjr = float(row['SCIMAGO_SJR'])
                        impacto_anual[ano].append(sjr)
                    except (ValueError, TypeError):
                        continue
        
        if not impacto_anual:
            ax.text(0.5, 0.5, "Sem dados suficientes para análise de impacto", 
                    ha='center', va='center', transform=ax.transAxes, fontsize=14)
            ax.set_xticks([])
            ax.set_yticks([])
            return canvas
            
        # Calcular média por ano e plotar
        anos = sorted(impacto_anual.keys())
        valores = [np.mean(impacto_anual[ano]) for ano in anos]
        
        ax.plot(anos, valores, marker='o', color='#9b59b6', linewidth=2)
        ax.set_xlabel('Ano')
        ax.set_ylabel('Impacto SJR')
        ax.set_title('Evolução do Impacto Individual')
        ax.grid(True, alpha=0.3)
        
        # Adicionar valores sobre pontos
        for x, y in zip(anos, valores):
            ax.text(x, y, f'{y:.2f}', ha='center', va='bottom')
        
        plt.setp(ax.get_xticklabels(), rotation=45)
        fig.tight_layout()
        
        return canvas

    def _create_impact_comparison_chart(self, dados):
        """Cria gráfico de comparação de impacto com média da área"""
        fig = Figure(figsize=(6, 4))
        canvas = FigureCanvas(fig)
        ax = fig.add_subplot(111)
        
        if 'ARTIGOS-PUBLICADOS' not in dados or 'SCIMAGO_SJR' not in dados['ARTIGOS-PUBLICADOS'].columns:
            ax.text(0.5, 0.5, "Dados de impacto não disponíveis", 
                    ha='center', va='center', transform=ax.transAxes, fontsize=14)
            ax.set_xticks([])
            ax.set_yticks([])
            return canvas
        
        # Calcular impacto médio do pesquisador
        df = dados['ARTIGOS-PUBLICADOS']
        sjr_values = df['SCIMAGO_SJR'].dropna()
        if len(sjr_values) == 0:
            ax.text(0.5, 0.5, "Sem dados suficientes para análise de impacto", 
                    ha='center', va='center', transform=ax.transAxes, fontsize=14)
            ax.set_xticks([])
            ax.set_yticks([])
            return canvas
            
        impacto_pesquisador = np.mean(sjr_values)
        
        # Obter área do pesquisador
        area = "Não especificada"
        if 'AREAS-DE-ATUACAO' in dados and not dados['AREAS-DE-ATUACAO'].empty:
            area_values = dados['AREAS-DE-ATUACAO']['AREA'].dropna()
            if not area_values.empty:
                area = area_values.iloc[0]
        
        # Calcular média da área considerando todos os pesquisadores
        sjr_area = []
        for id_curriculo, dados_outros in self.dataframes.items():
            if 'ARTIGOS-PUBLICADOS' not in dados_outros or 'SCIMAGO_SJR' not in dados_outros['ARTIGOS-PUBLICADOS'].columns:
                continue
                
            # Verificar se é da mesma área
            mesma_area = False
            if 'AREAS-DE-ATUACAO' in dados_outros and not dados_outros['AREAS-DE-ATUACAO'].empty:
                outras_areas = dados_outros['AREAS-DE-ATUACAO']['AREA'].dropna()
                if not outras_areas.empty and area in outras_areas.values:
                    mesma_area = True
            
            # Se for da mesma área ou área não especificada, adiciona ao cálculo
            if mesma_area or area == "Não especificada":
                sjr_area.extend(dados_outros['ARTIGOS-PUBLICADOS']['SCIMAGO_SJR'].dropna())
        
        impacto_area = np.mean(sjr_area) if sjr_area else 0
        
        # Calcular média global (todos os pesquisadores)
        sjr_global = []
        for dados_outros in self.dataframes.values():
            if 'ARTIGOS-PUBLICADOS' in dados_outros and 'SCIMAGO_SJR' in dados_outros['ARTIGOS-PUBLICADOS'].columns:
                sjr_global.extend(dados_outros['ARTIGOS-PUBLICADOS']['SCIMAGO_SJR'].dropna())
        
        impacto_global = np.mean(sjr_global) if sjr_global else 0
        
        # Criar gráfico de barras comparativo
        labels = ['Pesquisador', 'Média da Área', 'Média Global']
        valores = [impacto_pesquisador, impacto_area, impacto_global]
        colors = ['#3498db', '#e74c3c', '#2ecc71']
        
        bars = ax.bar(labels, valores, color=colors)
        ax.set_ylabel('SJR Médio')
        ax.set_title('Comparação de Impacto')
        
        # Adicionar valores sobre barras
        for bar in bars:
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height,
                   f'{height:.2f}',
                   ha='center', va='bottom')
        
        fig.tight_layout()
        return canvas

    def _get_h_index(self, researcher_name):
        """Busca o Índice H do pesquisador no Google Scholar"""
        try:
            search_query = scholarly.search_author(researcher_name)
            author = next(search_query, None)
            if author:
                author = scholarly.fill(author, sections=['indices'])
                return author.get('hindex', 'Não disponível')
        except Exception as e:
            print(f"Erro ao buscar Índice H: {e}")
        return 'Não disponível'

    # ... Continuar implementando os demais métodos auxiliares ...

