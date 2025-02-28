import sys
import os
import pandas as pd
import glob
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                            QHBoxLayout, QPushButton, QLabel, QLineEdit, 
                            QTableWidget, QTableWidgetItem, QTabWidget, 
                            QTreeWidget, QTreeWidgetItem, QSplitter, QScrollArea, 
                            QComboBox, QDialog, QMessageBox, QGridLayout,
                            QProgressDialog, QProgressBar, QInputDialog)
from PyQt5.QtCore import Qt, QTimer
import numpy as np
from stats_analyzer import CurriculoAnalyzer
from collections import defaultdict, Counter
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from scimago_data import load_scimago_data
from advanced_search import ArticleSearch
from stats_dashboard import StatsDashboard
import scholarly
from scholarly import scholarly

class SplashScreen(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("")
        self.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint)
        
        # Estilo geral
        self.setStyleSheet("""
            QDialog {
                background-color: #2C3E50;
                border-radius: 10px;
            }
            QLabel {
                color: white;
            }
            QProgressBar {
                border: 2px solid #3498DB;
                border-radius: 5px;
                text-align: center;
                background-color: #34495E;
            }
            QProgressBar::chunk {
                background-color: #3498DB;
                border-radius: 3px;
            }
        """)
        
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Título principal
        title = QLabel("Visualizador de Currículos")
        title.setStyleSheet("""
            font-size: 28px;
            font-weight: bold;
            margin-bottom: 20px;
            color: white;
        """)
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        
        # Subtítulo
        subtitle = QLabel("Sistema de Análise e Visualização de Dados")
        subtitle.setStyleSheet("""
            font-size: 14px;
            color: #BDC3C7;
            margin-bottom: 30px;
        """)
        subtitle.setAlignment(Qt.AlignCenter)
        layout.addWidget(subtitle)
        
        # Container para progress bar e status
        progress_container = QWidget()
        progress_layout = QVBoxLayout(progress_container)
        
        # Status label
        self.status = QLabel("Iniciando...")
        self.status.setStyleSheet("""
            font-size: 12px;
            color: #7F8C8D;
            margin-bottom: 5px;
        """)
        self.status.setAlignment(Qt.AlignCenter)
        progress_layout.addWidget(self.status)
        
        # Progress bar
        self.progress = QProgressBar()
        self.progress.setFixedHeight(15)
        self.progress.setMaximum(100)
        self.progress.setTextVisible(False)
        progress_layout.addWidget(self.progress)
        
        # Adicionar container ao layout principal
        layout.addWidget(progress_container)
        
        # Versão
        version = QLabel("v1.0.0")
        version.setStyleSheet("color: #7F8C8D; font-size: 12px;")
        version.setAlignment(Qt.AlignRight)
        layout.addWidget(version)
        
        self.setLayout(layout)
        
        # Centralizar na tela
        self._center()

    def _center(self):
        """Centraliza a janela na tela"""
        screen = QApplication.desktop().screenGeometry()
        size = self.geometry()
        self.move(
            (screen.width() - size.width()) // 2,
            (screen.height() - size.height()) // 2
        )

    def set_progress(self, value, text):
        """Atualiza progresso e mensagem"""
        self.progress.setValue(value)
        self.status.setText(text)
        QApplication.processEvents()

class CurriculoViewer(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Visualizador de Currículos")
        self.setGeometry(100, 100, 1200, 800)
        self.dataframes = {}
        self.analyzer = None
        self.stats_area = None  # Será inicializado no create_stats_tab
        
        # Criar e mostrar splash screen
        self.splash = SplashScreen()
        self.splash.show()
        
        # Inicializar aplicação com delay
        QTimer.singleShot(100, self.initialize_application)

    def initialize_application(self):
        """Inicializa a aplicação com barra de progresso"""
        # Carregar Scimago (20%)
        self.splash.set_progress(20, "Carregando base Scimago...")
        self.scimago_data = load_scimago_data()
        
        # Inicializar busca (40%)
        self.splash.set_progress(40, "Inicializando sistema de busca...")
        self.article_search = ArticleSearch(self.scimago_data)
        
        # Configurar UI (60%)
        self.splash.set_progress(60, "Configurando interface...")
        self.setup_ui()
        
        # Carregar dados (80%)
        self.splash.set_progress(80, "Carregando currículos...")
        self.load_data()
        
        # Finalizar (100%)
        self.splash.set_progress(100, "Concluído!")
        
        # Fechar splash e mostrar janela principal
        QTimer.singleShot(500, self._finish_loading)

    def _finish_loading(self):
        """Fecha splash e mostra janela principal"""
        self.splash.close()
        self.show()

    def setup_ui(self):
        # Widget central
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)  # Changed to VBox to stack controls vertically
        
        # Add search panel at the top
        search_panel = self._create_search_panel()
        layout.addWidget(search_panel)
        
        # Main content area
        content = QWidget()
        content_layout = QHBoxLayout(content)
        
        # Splitter principal
        splitter = QSplitter(Qt.Horizontal)
        content_layout.addWidget(splitter)
        
        # Painel esquerdo (navegação)
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        
        # Campo de busca
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Buscar...")
        self.search_input.textChanged.connect(self.search_data)
        left_layout.addWidget(self.search_input)

        # Árvore de currículos
        self.tree = QTreeWidget()
        self.tree.setHeaderLabel("Currículos")
        self.tree.itemClicked.connect(self.on_tree_item_clicked)
        left_layout.addWidget(self.tree)

        # Painel direito (conteúdo)
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        
        # Abas para diferentes visualizações
        self.tab_widget = QTabWidget()
        self.setup_tabs()
        right_layout.addWidget(self.tab_widget)

        # Adicionar painéis ao splitter
        splitter.addWidget(left_panel)
        splitter.addWidget(right_panel)
        splitter.setSizes([300, 900])  # Largura inicial dos painéis
        
        layout.addWidget(content)

    def _create_search_panel(self):
        """Cria o painel de pesquisa global"""
        panel = QWidget()
        panel.setMaximumHeight(100)  # Limita altura do painel
        
        # Usar grid layout para organizar melhor os controles
        layout = QGridLayout(panel)
        layout.setSpacing(5)  # Reduz espaçamento entre elementos
        
        # Linha 1: Busca principal
        layout.addWidget(QLabel("Buscar artigos:"), 0, 0)
        
        self.search_field = QLineEdit()
        self.search_field.setPlaceholderText("Digite sua busca...")
        layout.addWidget(self.search_field, 0, 1)
        
        self.search_type = QComboBox()
        self.search_type.addItems(['Título', 'ISSN', 'DOI', 'Ano'])  # Adicionar opção Ano
        self.search_type.setMaximumWidth(100)
        layout.addWidget(self.search_type, 0, 2)
        
        search_btn = QPushButton("Buscar")
        search_btn.clicked.connect(self._perform_search)
        search_btn.setMaximumWidth(100)
        layout.addWidget(search_btn, 0, 3)
        
        # Adicionar botão Scholar
        scholar_btn = QPushButton("Google Scholar")
        scholar_btn.clicked.connect(self.show_scholar_info)
        scholar_btn.setMaximumWidth(120)
        layout.addWidget(scholar_btn, 0, 4)
        
        # Linha 2: Filtros
        layout.addWidget(QLabel("Filtros:"), 1, 0)
        
        filter_widget = QWidget()
        filter_layout = QHBoxLayout(filter_widget)
        filter_layout.setSpacing(5)
        filter_layout.setContentsMargins(0, 0, 0, 0)
        
        self.filter_sjr = QLineEdit()
        self.filter_sjr.setPlaceholderText("SJR (min-max)")
        self.filter_sjr.setMaximumWidth(100)
        
        self.filter_hindex = QLineEdit()
        self.filter_hindex.setPlaceholderText("H-index (min-max)")
        self.filter_hindex.setMaximumWidth(100)
        
        self.filter_category = QLineEdit()
        self.filter_category.setPlaceholderText("Categoria")
        self.filter_category.setMaximumWidth(100)
        
        self.filter_year = QLineEdit()
        self.filter_year.setPlaceholderText("Ano")
        self.filter_year.setMaximumWidth(100)
        
        filter_layout.addWidget(self.filter_sjr)
        filter_layout.addWidget(self.filter_hindex)
        filter_layout.addWidget(self.filter_category)
        filter_layout.addWidget(self.filter_year)
        layout.addWidget(filter_widget, 1, 1, 1, 3)
        
        return panel

    def setup_tabs(self):
        self.tabs = {
            'DADOS-GERAIS': self.create_table_tab("Dados Gerais"),
            'FORMACAO-ACADEMICA': self.create_table_tab("Formação Acadêmica"),
            'ATUACOES-PROFISSIONAIS': self.create_table_tab("Atuações Profissionais"),
            
            # Produção Bibliográfica
            'ARTIGOS-PUBLICADOS': self.create_table_tab("Artigos Publicados"),
            'LIVROS-PUBLICADOS': self.create_table_tab("Livros Publicados"),
            'CAPITULOS-LIVROS': self.create_table_tab("Capítulos de Livros"),
            'TRABALHOS-EVENTOS': self.create_table_tab("Trabalhos em Eventos"),
            
            # Produção Técnica
            'SOFTWARE': self.create_table_tab("Software"),
            'PATENTES': self.create_table_tab("Patentes"),
            'PRODUTOS-TECNOLOGICOS': self.create_table_tab("Produtos Tecnológicos"),
            'TRABALHOS-TECNICOS': self.create_table_tab("Trabalhos Técnicos"),
            'DEMAIS-PRODUCOES-TECNICAS': self.create_table_tab("Demais Produções Técnicas"),
            
            # Orientações
            'ORIENTACOES-MESTRADO': self.create_table_tab("Orientações de Mestrado"),
            'ORIENTACOES-DOUTORADO': self.create_table_tab("Orientações de Doutorado"),
            'ORIENTACOES-POS-DOUTORADO': self.create_table_tab("Orientações de Pós-Doutorado"),
            'OUTRAS-ORIENTACOES': self.create_table_tab("Outras Orientações"),
            
            # Prêmios e Projetos
            'PREMIOS-TITULOS': self.create_table_tab("Prêmios e Títulos"),
            'PROJETOS-PESQUISA': self.create_table_tab("Projetos de Pesquisa"),
            
            'AREAS-DE-ATUACAO': self.create_table_tab("Áreas de Atuação"),
            'PALAVRAS-CHAVES': self.create_table_tab("Palavras-chave"),
        }
        
        # Organizar as abas em grupos
        tab_groups = {
            "Informações Básicas": ['DADOS-GERAIS', 'FORMACAO-ACADEMICA', 'ATUACOES-PROFISSIONAIS'],
            "Produção Bibliográfica": ['ARTIGOS-PUBLICADOS', 'LIVROS-PUBLICADOS', 'CAPITULOS-LIVROS', 'TRABALHOS-EVENTOS'],
            "Produção Técnica": ['SOFTWARE', 'PATENTES', 'PRODUTOS-TECNOLOGICOS', 'TRABALHOS-TECNICOS', 'DEMAIS-PRODUCOES-TECNICAS'],
            "Orientações": ['ORIENTACOES-MESTRADO', 'ORIENTACOES-DOUTORADO', 'ORIENTACOES-POS-DOUTORADO', 'OUTRAS-ORIENTACOES'],
            "Prêmios e Projetos": ['PREMIOS-TITULOS', 'PROJETOS-PESQUISA'],
            "Áreas e Palavras-chave": ['AREAS-DE-ATUACAO', 'PALAVRAS-CHAVES']
        }

        for group_name, tab_keys in tab_groups.items():
            for key in tab_keys:
                if key in self.tabs:
                    self.tab_widget.addTab(self.tabs[key], key.replace('-', ' ').title())

        # Adicionar aba de estatísticas
        stats_tab = self.create_stats_tab()
        self.tab_widget.addTab(stats_tab, "Estatísticas")

    def create_table_tab(self, title):
        # Widget com scroll
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        
        # Container para o conteúdo
        container = QWidget()
        layout = QVBoxLayout(container)
        
        # Header label
        header_label = QLabel()
        header_label.setStyleSheet("color: blue; padding: 5px;")
        layout.addWidget(header_label)
        
        # Tabela
        table = QTableWidget()
        table.setEditTriggers(QTableWidget.NoEditTriggers)
        layout.addWidget(table)
        
        # Guardar referências
        container.table = table
        container.header_label = header_label
        
        # Configurar scroll
        scroll.setWidget(container)
        
        return scroll

    def create_stats_tab(self):
        """Cria aba de estatísticas"""
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        
        container = QWidget()
        layout = QVBoxLayout(container)
        
        # Adicionar controles de seleção no topo
        controls = QWidget()
        controls_layout = QHBoxLayout(controls)
        
        # Seletor de tipo de análise
        controls_layout.addWidget(QLabel("Tipo de Análise:"))
        self.analysis_type = QComboBox()
        self.analysis_type.addItem("Análise Geral", "global")
        self.analysis_type.addItem("Análise Individual", "individual")
        controls_layout.addWidget(self.analysis_type)
        
        # Label para seletor de pesquisador
        self.researcher_label = QLabel("Pesquisador:")
        self.researcher_label.setVisible(False)
        controls_layout.addWidget(self.researcher_label)
        
        # Seletor de pesquisador (inicialmente oculto)
        self.researcher_selector = QComboBox()
        self.researcher_selector.setVisible(False)
        self.researcher_selector.setMinimumWidth(300)  # Tornar combobox mais largo
        
        # Preencher seletor com nomes dos pesquisadores
        # self.update_researcher_selector()  # Removido daqui
        
        controls_layout.addWidget(self.researcher_selector)
        
        # Adicionar espaçador para alinhar à esquerda
        controls_layout.addStretch()
        
        # Adicionar controles ao layout principal
        layout.addWidget(controls)
        
        # Widget para estatísticas
        stats_widget = QWidget()
        layout.addWidget(stats_widget)
        
        # Inicializar área de estatísticas
        self.stats_area = QVBoxLayout(stats_widget)
        
        # Função para atualizar visualização
        def update_view(index=None):
            analysis_type_value = self.analysis_type.currentData()
            if analysis_type_value == "global":
                self.researcher_label.setVisible(False)
                self.researcher_selector.setVisible(False)
                self.update_stats()
            else:
                self.researcher_label.setVisible(True)
                self.researcher_selector.setVisible(True)
                # Pegar ID atual do pesquisador selecionado
                curriculo_id = self.researcher_selector.currentData()
                if curriculo_id:  # Só atualiza se houver um ID válido
                    self.update_individual_stats(curriculo_id)
        
        # Conectar sinais
        self.analysis_type.currentIndexChanged.connect(update_view)
        self.researcher_selector.currentIndexChanged.connect(update_view)
        
        # Inicializar com análise global
        if self.dataframes:
            self.update_stats()
        
        scroll.setWidget(container)
        return scroll

    def update_researcher_selector(self):
        """Atualiza o QComboBox com os nomes dos pesquisadores"""
        self.researcher_selector.clear()  # Limpa itens existentes
        for curriculo_id, dados in self.dataframes.items():
            if 'DADOS-GERAIS' in dados and not dados['DADOS-GERAIS'].empty:
                nome = dados['DADOS-GERAIS']['NOME-COMPLETO'].iloc[0]
                self.researcher_selector.addItem(nome, curriculo_id)  # Nome como texto, ID como dados

    def load_data(self):
        csv_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'csv_output')
        csv_files = glob.glob(os.path.join(csv_dir, '*.csv'))

        # Agrupar arquivos por ID do currículo
        curriculos = {}
        for file in csv_files:
            basename = os.path.basename(file)
            parts = basename.split('_', 1)
            if len(parts) != 2:
                continue
                
            id_curriculo, resto = parts
            tipo = resto.replace('.csv', '')
            
            if id_curriculo not in curriculos:
                curriculos[id_curriculo] = {}
            
            try:
                df = pd.read_csv(file)
                # Enriquece dados de artigos com informações do Scimago
                if tipo == 'ARTIGOS-PUBLICADOS' and self.scimago_data:
                    df = self.scimago_data.enrich_article_data(df)
                curriculos[id_curriculo][tipo] = df
            except Exception as e:
                print(f"Erro ao carregar {file}: {str(e)}")

        # Preencher a árvore com grupos organizados
        for id_curriculo, dados in curriculos.items():
            item = QTreeWidgetItem(self.tree)
            nome = "Sem nome"
            
            if 'DADOS-GERAIS' in dados and not dados['DADOS-GERAIS'].empty:
                if 'NOME-COMPLETO' in dados['DADOS-GERAIS'].columns:
                    nome = dados['DADOS-GERAIS']['NOME-COMPLETO'].iloc[0]
            
            item.setText(0, f"{nome} ({id_curriculo})")
            item.setData(0, Qt.UserRole, id_curriculo)
            
            # Criar grupos na árvore
            grupos = {
                "Informações Básicas": ['DADOS-GERAIS', 'FORMACAO-ACADEMICA', 'ATUACOES-PROFISSIONAIS'],
                "Produção Bibliográfica": ['ARTIGOS-PUBLICADOS', 'LIVROS-PUBLICADOS', 'CAPITULOS-LIVROS', 'TRABALHOS-EVENTOS'],
                "Produção Técnica": ['SOFTWARE', 'PATENTES', 'PRODUTOS-TECNOLOGICOS', 'TRABALHOS-TECNICOS', 'DEMAIS-PRODUCOES-TECNICAS'],
                "Orientações": ['ORIENTACOES-MESTRADO', 'ORIENTACOES-DOUTORADO', 'ORIENTACOES-POS-DOUTORADO', 'OUTRAS-ORIENTACOES'],
                "Prêmios e Projetos": ['PREMIOS-TITULOS', 'PROJETOS-PESQUISA'],
                "Áreas e Palavras-chave": ['AREAS-DE-ATUACAO', 'PALAVRAS-CHAVES']
            }

            # Criar grupos na árvore com seus itens
            for grupo_nome, tipos in grupos.items():
                grupo_item = QTreeWidgetItem(item)
                grupo_item.setText(0, grupo_nome)
                
                # Adicionar subseções do grupo
                for tipo in tipos:
                    if tipo in dados and not dados[tipo].empty:
                        child = QTreeWidgetItem(grupo_item)
                        display_name = tipo.replace('-', ' ').title()
                        child.setText(0, display_name)
                        child.setData(0, Qt.UserRole, (id_curriculo, tipo))
                        
                # Remover grupo se não tiver itens
                if grupo_item.childCount() == 0:
                    item.removeChild(grupo_item)

        self.dataframes = curriculos
        self.analyzer = CurriculoAnalyzer(self.dataframes)
        
        # Inicializar a busca com todos os artigos
        self.article_search.set_articles_data(self.dataframes)
        
        # Atualizar estatísticas
        self.update_stats()
        
        # Atualizar o seletor de pesquisadores
        self.update_researcher_selector()

    def update_stats(self):
        """Atualiza a visualização das estatísticas"""
        if not hasattr(self, 'stats_area') or self.stats_area is None:
            return
            
        try:
            # Limpar área anterior
            self._clear_stats_area()
            
            if not self.dataframes:
                # Mostrar mensagem se não houver dados
                msg = QLabel("Nenhum dado disponível para análise")
                msg.setStyleSheet("font-size: 14px; color: #666; padding: 20px;")
                msg.setAlignment(Qt.AlignCenter)
                self.stats_area.addWidget(msg)
                return
                
            # Criar dashboard
            stats_dashboard = StatsDashboard(self.dataframes, self.analyzer)
            
            # Container para métricas
            metrics_panel = stats_dashboard.create_metrics_panel()
            if metrics_panel:
                self.stats_area.addWidget(metrics_panel)
            
            # Container para gráficos principais
            charts_container = QWidget()
            charts_layout = QHBoxLayout(charts_container)
            
            # Gráfico de produção
            prod_chart = stats_dashboard.create_production_chart()
            if prod_chart:
                charts_layout.addWidget(prod_chart)
                
            # Análise temporal
            temporal_chart = stats_dashboard.create_temporal_analysis()
            if temporal_chart:
                charts_layout.addWidget(temporal_chart)
                
            self.stats_area.addWidget(charts_container)
            
            # Container para análises adicionais
            analysis_container = QWidget()
            analysis_layout = QHBoxLayout(analysis_container)
            
            # Distribuição por área
            area_chart = stats_dashboard.create_area_distribution()
            if area_chart:
                analysis_layout.addWidget(area_chart)
                
            # Análise de impacto
            impact_chart = stats_dashboard.create_impact_analysis()
            if impact_chart:
                analysis_layout.addWidget(impact_chart)
                
            self.stats_area.addWidget(analysis_container)
        
        except Exception as e:
            print(f"Erro ao atualizar estatísticas: {e}")
            # Mostrar mensagem de erro
            error_msg = QLabel(f"Erro ao gerar estatísticas: {str(e)}")
            error_msg.setStyleSheet("color: red; padding: 20px;")
            self.stats_area.addWidget(error_msg)

    def update_individual_stats(self, curriculo_id):
        """Atualiza estatísticas individuais para um pesquisador específico"""
        if not hasattr(self, 'stats_area') or self.stats_area is None:
            return
            
        try:
            self._clear_stats_area()
            
            if not curriculo_id or curriculo_id not in self.dataframes:
                return
                
            stats_dashboard = StatsDashboard(self.dataframes, self.analyzer)
            individual_analysis = stats_dashboard.create_individual_analysis(curriculo_id)
            self.stats_area.addWidget(individual_analysis)
        
        except Exception as e:
            print(f"Erro ao atualizar estatísticas individuais: {e}")
            error_msg = QLabel(f"Erro ao gerar estatísticas: {str(e)}")
            error_msg.setStyleSheet("color: red; padding: 20px;")
            self.stats_area.addWidget(error_msg)

    def on_tree_item_clicked(self, item):
        data = item.data(0, Qt.UserRole)
        if isinstance(data, tuple):  # Clicou em um tipo específico
            id_curriculo, tipo = data
            if id_curriculo in self.dataframes and tipo in self.dataframes[id_curriculo]:
                self.display_data(self.dataframes[id_curriculo][tipo], tipo)
                self.tab_widget.setCurrentWidget(self.tabs[tipo])

    def display_data(self, df, tab_name):
        if tab_name not in self.tabs:
            return
        
        tab_widget = self.tabs[tab_name]
        table = tab_widget.widget().table
        header_label = tab_widget.widget().header_label
        
        # Remover colunas vazias
        df = df.dropna(axis=1, how='all')
        
        # Ordenar dados
        if tab_name == 'ARTIGOS-PUBLICADOS':
            # Ordenar por SJR (se disponível) e depois por ano
            if 'SCIMAGO_SJR' in df.columns:
                df = df.sort_values(['ANO', 'SCIMAGO_SJR'], ascending=[False, False])
            else:
                df = df.sort_values('ANO', ascending=False)
            # Adicionar informações do Scimago ao cabeçalho
            if 'SCIMAGO_SJR' in df.columns:
                media_sjr = df['SCIMAGO_SJR'].mean()
                media_citacoes = df['SCIMAGO_Cites_/_Doc._(2years)'].mean()
                info_text = (f"Total de artigos: {len(df)}\n"
                           f"SJR médio: {media_sjr:.3f}\n"
                           f"Média de citações por documento: {media_citacoes:.2f}")
                header_label.setText(info_text)
        else:
            if 'ANO' in df.columns:
                df = df.sort_values('ANO', ascending=False)
            elif 'ANO-INICIO' in df.columns:
                df = df.sort_values('ANO-INICIO', ascending=False)

        # Calcular completude apenas para campos não-nulos
        total_cells = df.size
        filled_cells = df.count().sum()
        completeness = (filled_cells / total_cells * 100) if total_cells > 0 else 0

        # Atualizar cabeçalho com informações mais detalhadas
        info_text = f"Total de registros: {len(df)}\n"
        info_text += f"Campos preenchidos: {completeness:.1f}%"
        header_label.setText(info_text)
        header_label.setStyleSheet("color: blue; padding: 5px;")

        # Preparar dados - substituir None/NaN por texto informativo
        df_display = df.fillna('Não disponível')

        # Configurar tabela
        table.setRowCount(len(df_display))
        table.setColumnCount(len(df_display.columns))
        
        # Renomear colunas para melhor legibilidade
        headers = [col.replace('-', ' ').title() for col in df_display.columns]
        table.setHorizontalHeaderLabels(headers)

        # Preencher dados
        for i, row in df_display.iterrows():
            for j, value in enumerate(row):
                item = QTableWidgetItem(str(value))
                if value == 'Não disponível':
                    item.setForeground(Qt.gray)
                table.setItem(i, j, item)
        
        # Ajustar visualização
        table.resizeColumnsToContents()
        for col in range(table.columnCount()):
            if table.columnWidth(col) > 300:
                table.setColumnWidth(col, 300)
        
        self.tab_widget.setCurrentWidget(tab_widget)

    def search_data(self):
        search_text = self.search_input.text().lower()
        for i in range(self.tree.topLevelItemCount()):
            item = self.tree.topLevelItem(i)
            item.setHidden(search_text not in item.text(0).lower())

    def show_global_stats(self):
        """Mostra estatísticas globais"""
        if not self.dataframes:
            return
            
        self._clear_stats_area()

        # Criar painel de métricas principais
        metrics_widget = QWidget()
        metrics_layout = QHBoxLayout(metrics_widget)

        # Total de docentes
        total_docentes = len(self.dataframes)
        metrics_layout.addWidget(self._create_metric_card(
            "Total de Docentes",
            total_docentes,
            color="#3498db"
        ))

        # Total de artigos
        total_artigos = sum(
            len(dados['ARTIGOS-PUBLICADOS']) 
            for dados in self.dataframes.values() 
            if 'ARTIGOS-PUBLICADOS' in dados
        )
        metrics_layout.addWidget(self._create_metric_card(
            "Total de Artigos",
            total_artigos,
            color="#2ecc71"
        ))

        # Índice de colaboração
        colab_index = self._calculate_collaboration_index()
        metrics_layout.addWidget(self._create_metric_card(
            "Índice de Colaboração",
            f"{colab_index:.2f}",
            color="#e74c3c"
        ))

        self.stats_area.addWidget(metrics_widget)

        # Gráficos
        charts_widget = QWidget()
        charts_layout = QHBoxLayout(charts_widget)

        # Distribuição de produção
        prod_chart = self._create_bar_chart({
            'Artigos': total_artigos,
            'Livros': sum(len(dados['LIVROS-PUBLICADOS']) for dados in self.dataframes.values() if 'LIVROS-PUBLICADOS' in dados),
            'Capítulos': sum(len(dados['CAPITULOS-LIVROS']) for dados in self.dataframes.values() if 'CAPITULOS-LIVROS' in dados),
            'Eventos': sum(len(dados['TRABALHOS-EVENTOS']) for dados in self.dataframes.values() if 'TRABALHOS-EVENTOS' in dados)
        }, "Distribuição da Produção")

        if prod_chart:
            charts_layout.addWidget(prod_chart)

        # Tendência temporal
        producao_anual = defaultdict(int)
        for dados in self.dataframes.values():
            if 'ARTIGOS-PUBLICADOS' in dados and not dados['ARTIGOS-PUBLICADOS'].empty:
                for ano in dados['ARTIGOS-PUBLICADOS']['ANO'].dropna():
                    try:
                        producao_anual[int(ano)] += 1
                    except ValueError:
                        continue

        if producao_anual:
            temporal_chart = self._create_line_chart(dict(sorted(producao_anual.items())), 
                                                "Evolução Temporal da Produção")
            if temporal_chart:
                charts_layout.addWidget(temporal_chart)

        self.stats_area.addWidget(charts_widget)

        # Impacto e colaborações
        impact_collab_widget = QWidget()
        impact_collab_layout = QHBoxLayout(impact_collab_widget)

        # Análise de impacto
        impact_chart = self._create_impact_analysis()
        if impact_chart:
            impact_collab_layout.addWidget(impact_chart)

        # Rede de colaborações
        collab_chart = self._create_collaboration_network()
        if collab_chart:
            impact_collab_layout.addWidget(collab_chart)

        self.stats_area.addWidget(impact_collab_widget)

    def show_individual_stats(self):
        selected_items = self.tree.selectedItems()
        if not selected_items:
            return

        item = selected_items[0]
        curriculo_id = item.data(0, Qt.UserRole)
        if isinstance(curriculo_id, tuple):
            curriculo_id = curriculo_id[0]
            
        self._clear_stats_area()
        stats = self.analyzer.analyze_single_curriculo(curriculo_id)

        if stats and 'producao' in stats:
            # Informações básicas
            if 'dados_basicos' in stats:
                self._add_stats_section("Informações Básicas", 
                    self._create_info_table(stats['dados_basicos']))

            # Formação
            if 'formacao' in stats:
                self._add_stats_section("Formação", 
                    self._create_info_table(stats['formacao']))
            
            # Produção Bibliográfica
            producao = stats['producao']
            producao_data = {
                'Artigos': producao.get('artigos', {}).get('total', 0),
                'Livros': producao.get('livros', {}).get('total', 0),
                'Capítulos': producao.get('capitulos_livros', {}).get('total', 0),
                'Trabalhos em Eventos': producao.get('eventos', {}).get('total', 0)
            }
            
            if any(producao_data.values()):
                self._add_stats_section("Produção Bibliográfica", 
                    self._create_bar_chart(producao_data, "Total de Produções Bibliográficas"))

            # ...rest of stats sections...

    def _clear_stats_area(self):
        """Limpa a área de estatísticas"""
        if hasattr(self, 'stats_area') and self.stats_area is not None:
            while self.stats_area.count():
                item = self.stats_area.takeAt(0)
                if item.widget():
                    item.widget().deleteLater()

    def _add_stats_section(self, title, widget):
        section = QWidget()
        layout = QVBoxLayout(section)
        
        # Título da seção
        label = QLabel(f"<h3>{title}</h3>")
        layout.addWidget(label)
        
        # Adicionar widget do gráfico/tabela
        if isinstance(widget, (QTableWidget, FigureCanvas)):
            layout.addWidget(widget)
        
        # Adicionar espaçamento
        layout.addSpacing(20)
        
        self.stats_area.addWidget(section)

    # Métodos auxiliares para criar gráficos e tabelas
    def _create_pie_chart(self, data, title):
        if not data:
            return QLabel("Sem dados disponíveis")

        # Verificar se os dados são numéricos
        filtered_data = {k: v for k, v in data.items() if isinstance(v, (int, float))}
        if not filtered_data:
            return QLabel("Dados inválidos para o gráfico")

        fig = Figure(figsize=(6, 4))
        ax = fig.add_subplot(111)
        
        labels = list(filtered_data.keys())
        values = list(filtered_data.values())
        
        # Calcular porcentagens
        total = sum(values)
        sizes = [(v/total)*100 for v in values]
        
        ax.pie(sizes, labels=labels, autopct='%1.1f%%')
        ax.set_title(title)
        
        canvas = FigureCanvas(fig)
        canvas.setMinimumSize(400, 300)
        return canvas

    def _create_bar_chart(self, data, title):
        """Cria um gráfico de barras com dados válidos"""
        if not data or all(v == 0 for v in data.values()):
            return None

        fig = Figure(figsize=(6, 4))
        canvas = FigureCanvas(fig)
        ax = fig.add_subplot(111)
        
        # Preparar dados
        labels = list(data.keys())
        values = list(data.values())
        
        # Definir cores atraentes
        colors = ['#3498db', '#2ecc71', '#e74c3c', '#f1c40f', '#9b59b6'][:len(data)]
        
        # Criar barras
        bars = ax.bar(range(len(data)), values, color=colors)
        
        # Configurar eixos
        ax.set_xticks(range(len(data)))
        ax.set_xticklabels(labels, rotation=45, ha='right')
        
        # Adicionar valores sobre as barras
        for bar in bars:
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height,
                   f'{int(height)}',
                   ha='center', va='bottom')
        
        ax.set_title(title)
        fig.tight_layout()
        
        return canvas

    def _create_horizontal_bar_chart(self, data, title):
        if not data:
            return QLabel("Sem dados disponíveis")

        # Verificar se os dados são numéricos e limitar a 10 itens
        filtered_data = {k: v for k, v in data.items() if isinstance(v, (int, float))}
        sorted_data = dict(sorted(filtered_data.items(), key=lambda x: x[1], reverse=True)[:10])
        
        if not sorted_data:
            return QLabel("Dados inválidos para o gráfico")

        fig = Figure(figsize=(8, 6))
        ax = fig.add_subplot(111)
        
        y = range(len(sorted_data))
        ax.barh(y, list(sorted_data.values()))
        ax.set_yticks(y)
        ax.set_yticklabels(sorted_data.keys())
        ax.set_title(title)
        
        canvas = FigureCanvas(fig)
        canvas.setMinimumSize(500, 400)
        return canvas
    
    def _create_line_chart(self, data, title):
        """Cria um gráfico de linha com dados válidos"""
        if not data:
            return None

        fig = Figure(figsize=(6, 4))
        canvas = FigureCanvas(fig)
        ax = fig.add_subplot(111)
        
        years = sorted(data.keys())
        values = [data[year] for year in years]
        
        ax.plot(years, values, marker='o', color='#3498db', linewidth=2)
        
        # Adicionar valores sobre os pontos
        for x, y in zip(years, values):
            ax.text(x, y, str(y), ha='center', va='bottom')
        
        ax.set_xlabel('Ano')
        ax.set_ylabel('Quantidade')
        ax.set_title(title)
        ax.grid(True, alpha=0.3)
        
        # Rotacionar labels do eixo x
        plt.setp(ax.get_xticklabels(), rotation=45, ha='right')
        
        fig.tight_layout()
        return canvas
    
    def _create_info_table(self, data):
        table = QTableWidget()
        table.setColumnCount(2)
        table.setRowCount(len(data))
        table.setHorizontalHeaderLabels(['Campo', 'Valor'])

        for i, (key, value) in enumerate(data.items()):
            key_item = QTableWidgetItem(key.replace('_', ' ').title())
            value_item = QTableWidgetItem(str(value))
            table.setItem(i, 0, key_item)
            table.setItem(i, 1, value_item)
        
        table.resizeColumnsToContents()
        table.setMinimumHeight(len(data) * 30 + 30)
        return table
    
    def _create_production_summary(self, data):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Artigos
        art_label = QLabel("<h4>Artigos</h4>")
        art_table = QTableWidget()
        art_table.setColumnCount(2)
        art_table.setRowCount(2)
        art_table.setHorizontalHeaderLabels(['Métrica', 'Valor'])
        art_table.setItem(0, 0, QTableWidgetItem('Total'))
        art_table.setItem(0, 1, QTableWidgetItem(str(data['artigos']['total'])))
        art_table.setItem(1, 0, QTableWidgetItem('Últimos 5 anos'))
        art_table.setItem(1, 1, QTableWidgetItem(str(data['artigos']['ultimos_5_anos'])))
        
        layout.addWidget(art_label)
        layout.addWidget(art_table)
        
        # Livros
        book_label = QLabel("<h4>Livros</h4>")
        book_table = QTableWidget()
        book_table.setColumnCount(2)
        book_table.setRowCount(1)
        book_table.setHorizontalHeaderLabels(['Métrica', 'Valor'])
        
        book_table.setItem(0, 0, QTableWidgetItem('Total'))
        book_table.setItem(0, 1, QTableWidgetItem(str(data['livros']['total'])))
        
        layout.addWidget(book_label)
        layout.addWidget(book_table)

        # Eventos
        event_label = QLabel("<h4>Trabalhos em Eventos</h4>")
        event_table = QTableWidget()
        event_table.setColumnCount(2)
        event_table.setRowCount(1)
        event_table.setHorizontalHeaderLabels(['Métrica', 'Valor'])
        
        event_table.setItem(0, 0, QTableWidgetItem('Total'))
        event_table.setItem(0, 1, QTableWidgetItem(str(data['eventos']['total'])))
        layout.addWidget(event_label)
        layout.addWidget(event_table)
        
        for table in [art_table, book_table, event_table]:
            table.resizeColumnsToContents()
            table.setMinimumHeight(table.rowCount() * 30 + 30)
        
        return widget

    def _create_full_production_summary(self, data):
        """Cria uma tabela detalhada com todas as produções"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Função auxiliar para criar tabelas de seção
        def create_section_table(section_data, metrics):
            table = QTableWidget()
            table.setColumnCount(2)
            table.setRowCount(len(metrics))
            table.setHorizontalHeaderLabels(['Métrica', 'Valor'])
            
            for i, (metric, key) in enumerate(metrics.items()):
                table.setItem(i, 0, QTableWidgetItem(metric))
                value = section_data.get(key, 0)
                if isinstance(value, dict):
                    value = value.get('total', 0)
                table.setItem(i, 1, QTableWidgetItem(str(value)))
            
            table.resizeColumnsToContents()
            table.setMinimumHeight(len(metrics) * 30 + 30)
            return table
        
        # Produção Bibliográfica
        layout.addWidget(QLabel("<h4>Produção Bibliográfica</h4>"))
        biblio_metrics = {
            'Total de Artigos': 'total',
            'Artigos nos Últimos 5 Anos': 'ultimos_5_anos',
        }
        layout.addWidget(create_section_table(data['artigos'], biblio_metrics))
        
        # Produção Técnica
        layout.addWidget(QLabel("<h4>Produção Técnica</h4>"))
        tecnica_metrics = {
            'Software': 'total',
            'Patentes': 'total',
            'Produtos Tecnológicos': 'total',
            'Trabalhos Técnicos': 'total',
            'Outras Produções Técnicas': 'total'
        }
        layout.addWidget(create_section_table({
            'Software': data['software'],
            'Patentes': data['patentes'],
            'Produtos Tecnológicos': data['produtos_tecnologicos'],
            'Trabalhos Técnicos': data['trabalhos_tecnicos'],
            'Outras Produções Técnicas': data['producoes_tecnicas']
        }, tecnica_metrics))

        # Orientações
        layout.addWidget(QLabel("<h4>Orientações</h4>"))
        orient_metrics = {
            'Mestrado Total': 'total',
            'Mestrado em Andamento': 'em_andamento',
            'Doutorado Total': 'total',
            'Doutorado em Andamento': 'em_andamento',
            'Pós-Doutorado Total': 'total',
            'Pós-Doutorado em Andamento': 'em_andamento',
            'Outras Orientações': 'total'
        }
        layout.addWidget(create_section_table({
            'Mestrado Total': data['orientacoes']['mestrado'],
            'Mestrado em Andamento': data['orientacoes']['mestrado'],
            'Doutorado Total': data['orientacoes']['doutorado'],
            'Doutorado em Andamento': data['orientacoes']['doutorado'],
            'Pós-Doutorado Total': data['orientacoes']['pos_doutorado'],
            'Pós-Doutorado em Andamento': data['orientacoes']['pos_doutorado'],
            'Outras Orientações': data['orientacoes']['outras']
        }, orient_metrics))

        # Prêmios e Projetos
        layout.addWidget(QLabel("<h4>Prêmios e Projetos</h4>"))
        premios_metrics = {
            'Total de Prêmios': 'total',
            'Projetos Total': 'total',
            'Projetos em Andamento': 'em_andamento'
        }
        layout.addWidget(create_section_table({
            'Total de Prêmios': data['premios'],
            'Projetos Total': data['projetos'],
            'Projetos em Andamento': data['projetos']
        }, premios_metrics))
        
        return widget

    def _add_search_controls(self, container):
        """Adiciona controles de pesquisa avançada"""
        search_panel = QWidget()
        layout = QHBoxLayout(search_panel)

        # Campo de busca
        self.search_field = QLineEdit()
        self.search_field.setPlaceholderText("Digite sua busca...")
        
        # Combo para tipo de busca
        self.search_type = QComboBox()
        self.search_type.addItems(['Título', 'ISSN', 'DOI'])
        
        # Botão de busca
        search_btn = QPushButton("Buscar")
        search_btn.clicked.connect(self._perform_search)
        
        # Filtros
        self.filter_sjr = QLineEdit()
        self.filter_sjr.setPlaceholderText("SJR (min-max)")
        
        self.filter_hindex = QLineEdit()
        self.filter_hindex.setPlaceholderText("H-index (min-max)")
        
        self.filter_category = QLineEdit()
        self.filter_category.setPlaceholderText("Categoria")
        
        self.filter_year = QLineEdit()
        self.filter_year.setPlaceholderText("Ano")
        
        # Adicionar widgets ao layout
        layout.addWidget(self.search_field)
        layout.addWidget(self.search_type)
        layout.addWidget(search_btn)
        layout.addWidget(QLabel("Filtros:"))
        layout.addWidget(self.filter_sjr)
        layout.addWidget(self.filter_hindex)
        layout.addWidget(self.filter_category)
        layout.addWidget(self.filter_year)
        
        # Inserir painel de busca no container
        container_layout = container.layout()
        container_layout.insertWidget(0, search_panel)

    def _perform_search(self):
        """Executa a pesquisa avançada"""
        search_text = self.search_field.text().strip()
        search_type = self.search_type.currentText().lower()
        
        # Converter tipo de busca para o formato esperado pelo ArticleSearch
        field_map = {
            'título': 'title',
            'issn': 'issn',
            'doi': 'doi',
            'ano': 'year'
        }
        search_field = field_map.get(search_type, 'title')
        
        # Tratar busca por ano de forma especial
        if search_type == 'ano':
            year = self.filter_year.text().strip() or search_text
            if not year:
                QMessageBox.warning(self, "Aviso", "Digite um ano para filtrar")
                return
                
            results = self.article_search.get_all_articles()
            if results is not None and not results.empty:
                results = self.article_search.filter_results(results, {'Year': year})
        # Busca normal para outros tipos
        else:
            if not search_text:
                QMessageBox.warning(self, "Aviso", "Digite um termo para busca")
                return
            
            results = self.article_search.search_by_criteria(search_text, search_field)
        
        # Mostrar resultados...
        if results is not None and not results.empty:
            self._show_search_results(results)
        else:
            QMessageBox.information(self, "Busca", "Nenhum resultado encontrado")

    def _show_search_results(self, df):
        """Mostra os resultados da busca em uma nova janela"""
        dialog = QDialog(self)
        dialog.setWindowTitle("Resultados da Busca")
        dialog.setMinimumSize(1000, 600)
        layout = QVBoxLayout(dialog)
        
        # Adicionar informações de resumo
        info_label = QLabel()
        info_label.setText(f"Total de artigos encontrados: {len(df)}")
        layout.addWidget(info_label)
        
        # Tabela de resultados
        table = QTableWidget()
        table.setRowCount(len(df))
        
        # Definir ordem das colunas e seus nomes de exibição
        column_order = [
            ('TITULO-DO-ARTIGO', 'Título'),
            ('REVISTA', 'Revista'),
            ('ANO', 'Ano'),
            ('ISSN', 'ISSN'),
            ('DOI', 'DOI'),
            ('SCIMAGO_SJR', 'SJR'),
            ('SCIMAGO_H_index', 'H-index'),
            ('CURRICULO_ID', 'ID Currículo')
        ]
        
        # Filtrar apenas colunas que existem no DataFrame
        visible_columns = [(col, display) for col, display in column_order if col in df.columns]
        
        # Configurar colunas da tabela
        table.setColumnCount(len(visible_columns))
        table.setHorizontalHeaderLabels([display for _, display in visible_columns])

        # Preencher dados
        for row_idx, (_, row_data) in enumerate(df.iterrows()):
            for col_idx, (col_name, _) in enumerate(visible_columns):
                value = row_data.get(col_name, '')
                
                # Tratar tipos de dados específicos
                if pd.isna(value):
                    str_value = ''
                elif isinstance(value, float):
                    str_value = f"{value:.2f}"
                else:
                    str_value = str(value)

                item = QTableWidgetItem(str_value)
                item.setFlags(item.flags() & ~Qt.ItemIsEditable)  # Fazer célula read-only
                table.setItem(row_idx, col_idx, item)
        
        # Ajustar tamanho das colunas
        table.resizeColumnsToContents()
        for col in range(table.columnCount()):
            width = table.columnWidth(col)
            if width > 300:
                table.setColumnWidth(col, 300)
        
        # Habilitar ordenação
        table.setSortingEnabled(True)
        layout.addWidget(table)

        # Botões
        button_layout = QHBoxLayout()
        
        export_btn = QPushButton("Exportar CSV")
        export_btn.clicked.connect(lambda: self._export_results(df))
        button_layout.addWidget(export_btn)
        
        close_btn = QPushButton("Fechar")
        close_btn.clicked.connect(dialog.close)
        button_layout.addWidget(close_btn)
        
        layout.addLayout(button_layout)
        dialog.exec_()

    def _export_results(self, df):
        """Exporta os resultados da busca para CSV"""
        try:
            filename = 'resultados_busca.csv'
            df.to_csv(filename, index=False, encoding='utf-8-sig')
            QMessageBox.information(self, "Sucesso", f"Dados exportados para {filename}")
        except Exception as e:
            QMessageBox.warning(self, "Erro", f"Erro ao exportar: {str(e)}")

    def _calculate_average_impact(self):
        """Calcula o impacto médio baseado no SJR dos artigos"""
        if not hasattr(self, 'all_articles') or self.all_articles is None:
            return 0
            
        if 'SCIMAGO_SJR' not in self.all_articles.columns:
            return 0
            
        sjr_values = self.all_articles['SCIMAGO_SJR'].dropna()
        return sjr_values.mean() if len(sjr_values) > 0 else 0

    def _calculate_collaboration_index(self):
        """Calcula o índice de colaboração baseado em coautorias"""
        total_autores = 0
        total_artigos = 0
        
        for dados in self.dataframes.values():
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

    def _calculate_productivity_trend(self):
        """Calcula tendência de produtividade nos últimos anos"""
        anos_recentes = {}
        ano_atual = pd.Timestamp.now().year
        
        # Coletar produção dos últimos 5 anos
        for dados in self.dataframes.values():
            if 'ARTIGOS-PUBLICADOS' in dados:
                df = dados['ARTIGOS-PUBLICADOS']
                if 'ANO' in df.columns:
                    for ano in df['ANO'].astype(int):
                        if ano >= (ano_atual - 5):
                            anos_recentes[ano] = anos_recentes.get(ano, 0) + 1

        # Calcular tendência
        if len(anos_recentes) >= 2:
            anos = sorted(anos_recentes.keys())
            primeiro_ano = anos_recentes[anos[0]]
            ultimo_ano = anos_recentes[anos[-1]]
            tendencia = ((ultimo_ano - primeiro_ano) / primeiro_ano * 100) if primeiro_ano > 0 else 0
            return tendencia
        
        return 0

    def _get_unique_areas(self):
        """Retorna lista de áreas únicas de todos os currículos"""
        areas = set(['Todas'])
        for dados in self.dataframes.values():
            if 'AREAS-DE-ATUACAO' in dados:
                df = dados['AREAS-DE-ATUACAO']
                if 'AREA' in df.columns:
                    areas.update(df['AREA'].dropna().unique())
        
        return sorted(list(areas))

    def _create_interactive_time_series(self):
        """Cria gráfico de série temporal interativo"""
        from matplotlib.figure import Figure

        fig = Figure(figsize=(10, 5))
        canvas = FigureCanvas(fig)
        ax = fig.add_subplot(111)

        # Coletar dados de produção por ano
        producao_anual = defaultdict(int)
        
        for dados in self.dataframes.values():
            if 'ARTIGOS-PUBLICADOS' in dados and not dados['ARTIGOS-PUBLICADOS'].empty:
                df = dados['ARTIGOS-PUBLICADOS']
                if 'ANO' in df.columns:
                    for ano in df['ANO'].dropna().astype(int):
                        producao_anual[ano] += 1
        
        # Criar gráfico somente se houver dados
        if producao_anual:
            anos = sorted(producao_anual.keys())
            valores = [producao_anual[ano] for ano in anos]
            
            ax.plot(anos, valores, marker='o', color='#3498db', linewidth=2)
            ax.set_xlabel('Ano', fontsize=12)
            ax.set_ylabel('Número de Publicações', fontsize=12)
            ax.set_title('Evolução da Produção Científica', fontsize=14)
            ax.grid(True, linestyle='--', alpha=0.7)
            
            # Adicionar valores sobre os pontos
            for x, y in zip(anos, valores):
                ax.annotate(f"{y}", 
                           (x, y), 
                           xytext=(0, 5), 
                           textcoords='offset points',
                           ha='center')
            
            # Rotacionar labels do eixo x para melhor legibilidade
            ax.tick_params(axis='x', rotation=45)
        else:
            ax.text(0.5, 0.5, "Sem dados disponíveis", 
                    horizontalalignment='center',
                    verticalalignment='center',
                    transform=ax.transAxes,
                    fontsize=14)
            ax.set_xticks([])
            ax.set_yticks([])
        
        fig.tight_layout()
        return canvas

    def _create_production_distribution(self):
        """Cria gráfico de distribuição de produção"""
        fig = Figure(figsize=(8, 6))
        canvas = FigureCanvas(fig)
        ax = fig.add_subplot(111)

        # Coletar dados
        tipos_producao = {
            'Artigos': 'ARTIGOS-PUBLICADOS',
            'Livros': 'LIVROS-PUBLICADOS',
            'Capítulos': 'CAPITULOS-LIVROS',
            'Trabalhos em Eventos': 'TRABALHOS-EVENTOS'
        }
        
        contagem = {tipo: 0 for tipo in tipos_producao}
        for dados in self.dataframes.values():
            for tipo, chave in tipos_producao.items():
                if chave in dados and not dados[chave].empty:
                    contagem[tipo] += len(dados[chave])

        # Verificar se há dados para mostrar
        if any(contagem.values()):
            # Usar cores atrativas
            colors = ['#3498db', '#2ecc71', '#e74c3c', '#f39c12', '#9b59b6']
            
            # Criar gráfico
            bars = ax.bar(contagem.keys(), contagem.values(), color=colors[:len(contagem)])
            ax.set_ylabel('Quantidade', fontsize=12)
            ax.set_title('Distribuição por Tipo de Produção', fontsize=14)
            
            # Adicionar valores sobre as barras
            for bar in bars:
                height = bar.get_height()
                ax.text(bar.get_x() + bar.get_width()/2., height,
                       f'{int(height)}',
                       ha='center', va='bottom')
            
            # Rotacionar labels
            plt.setp(ax.get_xticklabels(), rotation=45, ha='right')
        else:
            ax.text(0.5, 0.5, "Sem dados disponíveis", 
                    horizontalalignment='center',
                    verticalalignment='center',
                    transform=ax.transAxes,
                    fontsize=14)
            ax.set_xticks([])
            ax.set_yticks([])
        
        fig.tight_layout()
        return canvas

    def _create_impact_analysis(self):
        """Cria gráfico de análise de impacto"""
        fig = Figure(figsize=(8, 6))
        canvas = FigureCanvas(fig)
        ax = fig.add_subplot(111)
        
        # Coletar dados de impacto (SJR)
        impacto_por_ano = defaultdict(list)
        
        for dados in self.dataframes.values():
            if 'ARTIGOS-PUBLICADOS' in dados and not dados['ARTIGOS-PUBLICADOS'].empty:
                df = dados['ARTIGOS-PUBLICADOS']
                if 'ANO' in df.columns and 'SCIMAGO_SJR' in df.columns:
                    for _, row in df.iterrows():
                        if pd.notna(row['ANO']) and pd.notna(row['SCIMAGO_SJR']):
                            ano = int(row['ANO'])
                            impacto_por_ano[ano].append(float(row['SCIMAGO_SJR']))

        # Verificar se há dados para plotar
        if impacto_por_ano:
            # Calcular médias
            anos = sorted(impacto_por_ano.keys())
            medias = [np.mean(impacto_por_ano[ano]) for ano in anos]
            
            # Criar gráfico
            ax.plot(anos, medias, marker='o', color='#e74c3c', linewidth=2)
            ax.set_xlabel('Ano', fontsize=12)
            ax.set_ylabel('Impacto Médio (SJR)', fontsize=12)
            ax.set_title('Evolução do Impacto das Publicações', fontsize=14)
            ax.grid(True, linestyle='--', alpha=0.7)
            
            # Adicionar valores sobre os pontos
            for x, y in zip(anos, medias):
                ax.annotate(f"{y:.2f}", 
                           (x, y), 
                           xytext=(0, 5), 
                           textcoords='offset points',
                           ha='center')
        else:
            ax.text(0.5, 0.5, "Sem dados de impacto disponíveis", 
                    horizontalalignment='center',
                    verticalalignment='center',
                    transform=ax.transAxes,
                    fontsize=14)
            ax.set_xticks([])
            ax.set_yticks([])
        
        fig.tight_layout()
        return canvas

    def _create_citations_heatmap(self):
        """Cria mapa de calor de citações por ano e área"""
        fig = Figure(figsize=(8, 6))
        canvas = FigureCanvas(fig)
        ax = fig.add_subplot(111)

        # Coletar dados de citações por ano e área
        citacoes = defaultdict(lambda: defaultdict(int))
        areas = set()
        anos = set()

        try:
            for curriculo_id, dados in self.dataframes.items():
                # Verificar se existem artigos e áreas
                if ('ARTIGOS-PUBLICADOS' not in dados or 
                    'AREAS-DE-ATUACAO' not in dados or 
                    dados['ARTIGOS-PUBLICADOS'].empty or 
                    dados['AREAS-DE-ATUACAO'].empty):
                    continue
                    
                artigos = dados['ARTIGOS-PUBLICADOS']
                areas_doc = dados['AREAS-DE-ATUACAO']
                
                # Verificar se as colunas necessárias existem
                if ('SCIMAGO_Total_Cites_(3years)' not in artigos.columns or 
                    'ANO' not in artigos.columns or
                    'AREA' not in areas_doc.columns):
                    continue
                
                # Obter a primeira área do pesquisador
                area = None
                if not areas_doc.empty and 'AREA' in areas_doc.columns:
                    area_values = areas_doc['AREA'].dropna()
                    if not area_values.empty:
                        area = area_values.iloc[0]
                
                if not area:  # Se não houver área definida, continue
                    area = "Não especificada"
                    
                # Processar artigos
                for _, artigo in artigos.iterrows():
                    if (pd.notna(artigo['ANO']) and 
                        pd.notna(artigo['SCIMAGO_Total_Cites_(3years)'])):
                        try:
                            ano = int(artigo['ANO'])
                            cites = float(artigo['SCIMAGO_Total_Cites_(3years)'])
                            citacoes[area][ano] += cites
                            areas.add(area)
                            anos.add(ano)
                        except (ValueError, TypeError):
                            continue

        except Exception as e:
            print(f"Erro ao processar dados para o mapa de calor: {e}")
            ax.text(0.5, 0.5, "Erro ao processar dados", 
                    ha='center', va='center', transform=ax.transAxes)
            return canvas

        if not areas or not anos:
            ax.text(0.5, 0.5, "Sem dados suficientes para o mapa de calor", 
                    horizontalalignment='center',
                    verticalalignment='center',
                    transform=ax.transAxes,
                    fontsize=14)
            return canvas

        try:
            # Criar matriz de dados para o mapa de calor
            areas_list = sorted(areas)
            anos_list = sorted(anos)
            data = np.zeros((len(areas_list), len(anos_list)))
            
            for i, area in enumerate(areas_list):
                for j, ano in enumerate(anos_list):
                    data[i, j] = citacoes[area][ano]

            # Criar mapa de calor
            im = ax.imshow(data, cmap='YlOrRd', aspect='auto')
            
            # Configurar eixos
            ax.set_xticks(range(len(anos_list)))
            ax.set_yticks(range(len(areas_list)))
            ax.set_xticklabels(anos_list, rotation=45)
            ax.set_yticklabels(areas_list)

            # Adicionar barra de cores e título
            fig.colorbar(im, ax=ax, label='Número de Citações')
            ax.set_title('Mapa de Calor de Citações por Área e Ano', fontsize=14)
            
            # Adicionar valores nas células
            for i in range(len(areas_list)):
                for j in range(len(anos_list)):
                    if data[i, j] > 0:
                        text = ax.text(j, i, f"{int(data[i,j])}",
                                      ha="center", va="center", 
                                      color="black" if data[i,j] < np.max(data)/2 else "white")
        
        except Exception as e:
            print(f"Erro ao criar mapa de calor: {e}")
            ax.clear()
            ax.text(0.5, 0.5, "Erro ao gerar visualização", 
                    ha='center', va='center', transform=ax.transAxes)
        
        fig.tight_layout()
        return canvas

    def _create_collaboration_network(self):
        """Cria visualização da rede de colaborações"""
        fig = Figure(figsize=(8, 6))
        canvas = FigureCanvas(fig)
        ax = fig.add_subplot(111)

        # Coletar dados de colaboração
        colaboracoes = defaultdict(int)
        instituicoes = set()

        # Primeiro, vamos verificar se temos dados de instituições
        has_institution_data = False
        for dados in self.dataframes.values():
            if 'ARTIGOS-PUBLICADOS' in dados and not dados['ARTIGOS-PUBLICADOS'].empty:
                df = dados['ARTIGOS-PUBLICADOS']
                if 'INSTITUICAO' in df.columns:
                    has_institution_data = True
                    break
        
        if not has_institution_data:
            # Criar texto informativo
            ax.text(0.5, 0.5, "Dados de instituições não disponíveis", 
                    horizontalalignment='center',
                    verticalalignment='center',
                    transform=ax.transAxes,
                    fontsize=14)
            ax.set_xticks([])
            ax.set_yticks([])
            return canvas

        # Se há dados, coletá-los
        for dados in self.dataframes.values():
            if 'ARTIGOS-PUBLICADOS' in dados and not dados['ARTIGOS-PUBLICADOS'].empty:
                df = dados['ARTIGOS-PUBLICADOS']
                if 'INSTITUICAO' in df.columns:
                    for _, row in df.iterrows():
                        instituicao = row.get('INSTITUICAO')
                        if pd.notna(instituicao):
                            # Separar múltiplas instituições se houver
                            insts = [i.strip() for i in str(instituicao).split(';')]
                            for inst in insts:
                                if inst:  # Verificar se não é string vazia
                                    instituicoes.add(inst)
                                    
                            # Registrar colaborações
                            for i in range(len(insts)):
                                for j in range(i+1, len(insts)):
                                    if insts[i] and insts[j]:  # Verificar se não são strings vazias
                                        par = tuple(sorted([insts[i], insts[j]]))
                                        colaboracoes[par] += 1

        if not colaboracoes or len(instituicoes) < 2:
            ax.text(0.5, 0.5, "Sem dados suficientes para rede de colaboração", 
                    horizontalalignment='center',
                    verticalalignment='center',
                    transform=ax.transAxes,
                    fontsize=14)
            ax.set_xticks([])
            ax.set_yticks([])
            return canvas

        try:
            # Limitar para as 10 instituições mais frequentes em colaborações
            inst_freq = Counter()
            for (inst1, inst2), weight in colaboracoes.items():
                inst_freq[inst1] += weight
                inst_freq[inst2] += weight
                
            if len(instituicoes) > 10:
                top_insts = [inst for inst, _ in inst_freq.most_common(10)]
                instituicoes = set(top_insts)
                # Filtrar colaborações para incluir apenas top instituições
                colaboracoes = {k: v for k, v in colaboracoes.items() 
                               if k[0] in instituicoes and k[1] in instituicoes}

            # Criar layout circular
            instituicoes = list(instituicoes)
            n = len(instituicoes)
            angles = np.linspace(0, 2*np.pi, n, endpoint=False)

            # Plotar nós (instituições)
            x = np.cos(angles)
            y = np.sin(angles)
            ax.scatter(x, y, s=100, color='#3498db', edgecolor='white', linewidth=1.5)

            # Plotar arestas (colaborações)
            max_colab = max(colaboracoes.values())
            for (inst1, inst2), weight in colaboracoes.items():
                if inst1 in instituicoes and inst2 in instituicoes:
                    i1 = instituicoes.index(inst1)
                    i2 = instituicoes.index(inst2)
                    alpha = 0.3 + 0.7 * (weight / max_colab)  # Mínimo 0.3 de opacidade
                    thickness = 0.5 + 2.5 * (weight / max_colab)  # Espessura entre 0.5 e 3
                    ax.plot([x[i1], x[i2]], [y[i1], y[i2]], 
                          color='gray', alpha=alpha, linewidth=thickness)
            
            # Adicionar rótulos
            for i, inst in enumerate(instituicoes):
                # Limitar tamanho do nome para exibição
                nome_display = inst[:15] + "..." if len(inst) > 15 else inst
                
                # Posicionar rótulos um pouco além dos nós
                offset = 1.1  # Fator de deslocamento
                ax.annotate(nome_display, 
                           (offset * x[i], offset * y[i]), 
                           ha='center' if -0.1 < x[i] < 0.1 else ('right' if x[i] < 0 else 'left'),
                           va='center' if -0.1 < y[i] < 0.1 else ('top' if y[i] < 0 else 'bottom'),
                           fontsize=8)

            ax.set_title('Rede de Colaborações entre Instituições', fontsize=14)
        except Exception as e:
            print(f"Erro ao gerar rede de colaboração: {e}")
            ax.clear()
            ax.text(0.5, 0.5, "Erro ao gerar rede de colaboração", 
                    ha='center', va='center', transform=ax.transAxes)
        
        ax.axis('equal')
        ax.axis('off')
        fig.tight_layout()
        return canvas

    def _create_impact_by_area(self):
        """Cria gráfico de métricas de impacto por área"""
        fig = Figure(figsize=(10, 6))
        canvas = FigureCanvas(fig)
        ax = fig.add_subplot(111)

        # Coletar métricas por área
        impact_metrics = defaultdict(list)

        try:
            for dados in self.dataframes.values():
                if ('ARTIGOS-PUBLICADOS' in dados and 
                    'AREAS-DE-ATUACAO' in dados and 
                    not dados['ARTIGOS-PUBLICADOS'].empty and 
                    not dados['AREAS-DE-ATUACAO'].empty):
                    
                    artigos = dados['ARTIGOS-PUBLICADOS']
                    areas = dados['AREAS-DE-ATUACAO']
                    
                    if 'SCIMAGO_SJR' not in artigos.columns or 'AREA' not in areas.columns:
                        continue
                    
                    # Obter áreas do pesquisador
                    area_values = areas['AREA'].dropna()
                    if area_values.empty:
                        continue
                        
                    area = area_values.iloc[0]  # Usar primeira área
                    
                    # Coletar valores SJR
                    sjr_values = artigos['SCIMAGO_SJR'].dropna()
                    for sjr in sjr_values:
                        try:
                            impact_metrics[area].append(float(sjr))
                        except (ValueError, TypeError):
                            continue

        except Exception as e:
            print(f"Erro ao coletar dados de impacto por área: {e}")

        if not impact_metrics:
            ax.text(0.5, 0.5, "Sem dados de impacto por área disponíveis", 
                    horizontalalignment='center',
                    verticalalignment='center',
                    transform=ax.transAxes,
                    fontsize=14)
            ax.set_xticks([])
            ax.set_yticks([])
            return canvas
        
        try:
            # Calcular médias e criar gráfico
            areas = []
            means = []
            std = []
            
            for area, values in impact_metrics.items():
                if values:  # Verificar se há valores
                    areas.append(area)
                    means.append(np.mean(values))
                    std.append(np.std(values))
            
            # Limitar a 10 áreas para melhor visualização
            if len(areas) > 10:
                # Ordenar por média e pegar os 10 maiores
                sorted_indices = np.argsort(means)[::-1][:10]
                areas = [areas[i] for i in sorted_indices]
                means = [means[i] for i in sorted_indices]
                std = [std[i] for i in sorted_indices]
            
            # Criar gráfico de barras com desvio padrão
            bars = ax.bar(range(len(areas)), means, yerr=std, 
                         capsize=5, color='#3498db', edgecolor='black', linewidth=0.5)

            # Configurar eixos
            ax.set_xticks(range(len(areas)))
            ax.set_xticklabels(areas, rotation=45, ha='right')
            ax.set_ylabel('SJR Médio', fontsize=12)
            ax.set_title('Impacto (SJR) por Área de Conhecimento', fontsize=14)
            ax.grid(True, linestyle='--', alpha=0.3, axis='y')

            # Adicionar valores sobre as barras
            for bar in bars:
                height = bar.get_height()
                ax.text(bar.get_x() + bar.get_width()/2., height + 0.02,
                       f'{height:.2f}',
                       ha='center', va='bottom', fontsize=9)
        
        except Exception as e:
            print(f"Erro ao criar gráfico de impacto por área: {e}")
            ax.clear()
            ax.text(0.5, 0.5, "Erro ao gerar visualização de impacto", 
                    ha='center', va='center', transform=ax.transAxes,
                    fontsize=14)
        
        fig.tight_layout()
        return canvas

    def _create_trends_analysis(self):
        """Cria visualização de análise de tendências"""
        fig = Figure(figsize=(12, 6))
        canvas = FigureCanvas(fig)
        
        # Criar dois subplots lado a lado
        ax1 = fig.add_subplot(121)
        ax2 = fig.add_subplot(122)

        # Análise de tendência temporal
        producao_anual = defaultdict(lambda: defaultdict(int))
        has_data = False

        try:
            for dados in self.dataframes.values():
                for tipo in ['ARTIGOS-PUBLICADOS', 'LIVROS-PUBLICADOS', 'CAPITULOS-LIVROS']:
                    if tipo in dados and not dados[tipo].empty and 'ANO' in dados[tipo].columns:
                        for ano in dados[tipo]['ANO'].dropna().astype(int):
                            producao_anual[tipo][ano] += 1
                            has_data = True
            
            if has_data:
                # Plotar tendências por tipo
                anos = sorted(set().union(*[d.keys() for d in producao_anual.values()]))
                
                # Definir cores para cada tipo
                colors = {
                    'ARTIGOS-PUBLICADOS': '#3498db',  # Azul
                    'LIVROS-PUBLICADOS': '#2ecc71',    # Verde
                    'CAPITULOS-LIVROS': '#e74c3c'      # Vermelho
                }
                
                for tipo, dados in producao_anual.items():
                    valores = [dados.get(ano, 0) for ano in anos]
                    label = tipo.split('-')[0].title()
                    ax1.plot(anos, valores, marker='o', label=label, color=colors.get(tipo, 'gray'))
                    
                ax1.set_xlabel('Ano', fontsize=12)
                ax1.set_ylabel('Quantidade', fontsize=12)
                ax1.set_title('Tendências de Produção por Tipo', fontsize=14)
                ax1.grid(True, linestyle='--', alpha=0.7)
                ax1.legend()
            else:
                ax1.text(0.5, 0.5, "Sem dados de tendências disponíveis", 
                        ha='center', va='center', transform=ax1.transAxes, fontsize=14)
                ax1.set_xticks([])
                ax1.set_yticks([])
        except Exception as e:
            print(f"Erro ao analisar tendências de produção: {e}")
            ax1.text(0.5, 0.5, "Erro ao analisar tendências", 
                    ha='center', va='center', transform=ax1.transAxes)

        # Análise de impacto ao longo do tempo
        impacto_anual = defaultdict(list)
        has_impact_data = False

        try:
            for dados in self.dataframes.values():
                if 'ARTIGOS-PUBLICADOS' in dados and not dados['ARTIGOS-PUBLICADOS'].empty:
                    df = dados['ARTIGOS-PUBLICADOS']
                    if 'ANO' in df.columns and 'SCIMAGO_SJR' in df.columns:
                        for _, row in df.iterrows():
                            if pd.notna(row['ANO']) and pd.notna(row['SCIMAGO_SJR']):
                                try:
                                    ano = int(row['ANO'])
                                    sjr = float(row['SCIMAGO_SJR'])
                                    impacto_anual[ano].append(sjr)
                                    has_impact_data = True
                                except (ValueError, TypeError):
                                    continue

            if has_impact_data:
                # Plotar evolução do impacto
                anos_impacto = sorted(impacto_anual.keys())
                medias_impacto = [np.mean(impacto_anual[ano]) for ano in anos_impacto]
                
                ax2.plot(anos_impacto, medias_impacto, marker='s', color='#9b59b6', linewidth=2)
                ax2.set_xlabel('Ano', fontsize=12)
                ax2.set_ylabel('SJR Médio', fontsize=12)
                ax2.set_title('Evolução do Impacto (SJR)', fontsize=14)
                ax2.grid(True, linestyle='--', alpha=0.7)
                
                # Adicionar valores sobre os pontos
                for x, y in zip(anos_impacto, medias_impacto):
                    ax2.annotate(f"{y:.2f}", 
                               (x, y), 
                               xytext=(0, 5), 
                               textcoords='offset points',
                               ha='center')
            else:
                ax2.text(0.5, 0.5, "Sem dados de impacto disponíveis", 
                        ha='center', va='center', transform=ax2.transAxes, fontsize=14)
                ax2.set_xticks([])
                ax2.set_yticks([])
        except Exception as e:
            print(f"Erro ao analisar evolução do impacto: {e}")
            ax2.text(0.5, 0.5, "Erro ao analisar impacto", 
                    ha='center', va='center', transform=ax2.transAxes)
        
        fig.tight_layout()
        return canvas

    def _create_production_forecast(self):
        """Cria previsão de produção futura"""
        fig = Figure(figsize=(8, 6))
        canvas = FigureCanvas(fig)
        ax = fig.add_subplot(111)

        # Coletar dados históricos
        producao_anual = defaultdict(int)
        for dados in self.dataframes.values():
            if 'ARTIGOS-PUBLICADOS' in dados and not dados['ARTIGOS-PUBLICADOS'].empty:
                df = dados['ARTIGOS-PUBLICADOS']
                if 'ANO' in df.columns:
                    for ano in df['ANO'].dropna().astype(int):
                        producao_anual[ano] += 1

        if not producao_anual:
            ax.text(0.5, 0.5, "Dados insuficientes para previsão", 
                    horizontalalignment='center',
                    verticalalignment='center',
                    transform=ax.transAxes,
                    fontsize=14)
            ax.set_xticks([])
            ax.set_yticks([])
            return canvas

        try:
            # Preparar dados para previsão
            anos = sorted(producao_anual.keys())
            valores = [producao_anual[ano] for ano in anos]
            
            # Calcular tendência linear simples
            if len(anos) < 2:
                ax.text(0.5, 0.5, "Dados insuficientes para previsão (mínimo 2 anos)", 
                        horizontalalignment='center',
                        verticalalignment='center',
                        transform=ax.transAxes,
                        fontsize=14)
                return canvas

            x = np.array(anos)
            y = np.array(valores)
            z = np.polyfit(x, y, 1)
            p = np.poly1d(z)
            
            # Projetar próximos 3 anos
            ultimo_ano = max(anos)
            anos_futuros = list(range(ultimo_ano + 1, ultimo_ano + 4))
            previsao = p(anos_futuros)

            # Plotar dados históricos e previsão
            ax.plot(anos, valores, 'bo-', label='Dados Históricos')
            ax.plot(anos_futuros, previsao, 'r--', label='Previsão')

            # Adicionar intervalo de confiança
            std_dev = np.std(valores)
            ax.fill_between(anos_futuros, 
                           previsao - std_dev, 
                           previsao + std_dev, 
                           color='red', alpha=0.2)

            ax.set_xlabel('Ano', fontsize=12)
            ax.set_ylabel('Quantidade de Publicações', fontsize=12)
            ax.set_title('Previsão de Produção', fontsize=14)
            ax.legend()
            ax.grid(True, linestyle='--', alpha=0.7)
            
            # Adicionar valores sobre pontos de previsão
            for x, y in zip(anos_futuros, previsao):
                ax.annotate(f"{int(y)}", 
                           (x, y), 
                           xytext=(0, 5), 
                           textcoords='offset points',
                           ha='center')

        except Exception as e:
            print(f"Erro ao gerar previsão: {e}")
            ax.clear()
            ax.text(0.5, 0.5, "Erro ao gerar previsão", 
                    ha='center', va='center', transform=ax.transAxes)
        
        fig.tight_layout()
        return canvas

    def _create_emerging_topics(self):
        """Analisa tópicos emergentes nas publicações recentes"""
        fig = Figure(figsize=(8, 6))
        canvas = FigureCanvas(fig)
        ax = fig.add_subplot(111)

        try:
            # Coletar palavras-chave dos últimos anos
            palavras_recentes = Counter()
            ano_atual = pd.Timestamp.now().year
            
            for dados in self.dataframes.values():
                # Verificar palavras-chave específicas
                if 'PALAVRAS-CHAVES' in dados and not dados['PALAVRAS-CHAVES'].empty:
                    df = dados['PALAVRAS-CHAVES']
                    if 'PALAVRA' in df.columns:
                        for palavra in df['PALAVRA'].dropna():
                            palavras_recentes[palavra.lower()] += 1
                
                # Verificar palavras do título (para enriquecer análise)
                if 'ARTIGOS-PUBLICADOS' in dados and not dados['ARTIGOS-PUBLICADOS'].empty:
                    df = dados['ARTIGOS-PUBLICADOS']
                    if 'TITULO-DO-ARTIGO' in df.columns and 'ANO' in df.columns:
                        # Filtrar artigos recentes (últimos 3 anos)
                        recentes = df[df['ANO'].astype(int) >= (ano_atual - 3)]
                        for titulo in recentes['TITULO-DO-ARTIGO'].dropna():
                            # Dividir o título em palavras
                            for palavra in titulo.lower().split():
                                # Filtrar palavras significativas com mais de 3 caracteres
                                if len(palavra) > 3:
                                    palavras_recentes[palavra] += 1

            if not palavras_recentes:
                ax.text(0.5, 0.5, "Sem dados suficientes para análise de tópicos", 
                        horizontalalignment='center',
                        verticalalignment='center',
                        transform=ax.transAxes,
                        fontsize=14)
                ax.set_xticks([])
                ax.set_yticks([])
                return canvas
            
            # Filtrar palavras comuns (stop words simples)
            stop_words = ['the', 'and', 'for', 'with', 'from', 'this', 'that', 'com', 'para', 'dos', 'das', 'uma', 'sobre']
            palavras_recentes = {k: v for k, v in palavras_recentes.items() if k not in stop_words}
            
            # Pegar os top N tópicos
            top_palavras = dict(palavras_recentes.most_common(10))

            # Criar gráfico horizontal de barras
            y_pos = np.arange(len(top_palavras))
            colors = plt.cm.viridis(np.linspace(0, 0.8, len(top_palavras)))
            bars = ax.barh(y_pos, list(top_palavras.values()), color=colors)
            ax.set_yticks(y_pos)
            ax.set_yticklabels(list(top_palavras.keys()))
            ax.set_xlabel('Frequência', fontsize=12)
            ax.set_title('Tópicos Mais Frequentes', fontsize=14)
            
            # Adicionar valores
            for i, bar in enumerate(bars):
                width = bar.get_width()
                ax.text(width + 0.5, bar.get_y() + bar.get_height()/2, 
                       f'{width}', 
                       ha='left', va='center')
        
        except Exception as e:
            print(f"Erro ao analisar tópicos emergentes: {e}")
            ax.clear()
            ax.text(0.5, 0.5, "Erro ao analisar tópicos", 
                    ha='center', va='center', transform=ax.transAxes)
        
        fig.tight_layout()
        return canvas

    def _create_network_metrics(self):
        """Cria painel de métricas de rede"""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        
        # Calcular métricas de rede
        try:
            metricas = self._calculate_network_metrics()

            # Criar tabela de métricas
            table = QTableWidget()
            table.setColumnCount(2)
            table.setRowCount(len(metricas))
            table.setHorizontalHeaderLabels(['Métrica', 'Valor'])
            
            for i, (metrica, valor) in enumerate(metricas.items()):
                table.setItem(i, 0, QTableWidgetItem(metrica))
                table.setItem(i, 1, QTableWidgetItem(f"{valor:.2f}" if isinstance(valor, float) else str(valor)))
            
            table.resizeColumnsToContents()
            layout.addWidget(QLabel("<h3>Métricas de Rede</h3>"))
            layout.addWidget(table)
        
        except Exception as e:
            print(f"Erro ao calcular métricas de rede: {e}")
            layout.addWidget(QLabel("Erro ao gerar métricas de rede"))
        
        return panel

    def _calculate_network_metrics(self):
        """Calcula métricas básicas da rede de colaboração"""
        metricas = {
            'Total de Colaborações': 0,
            'Média de Autores por Artigo': 0,
            'Maior Grupo de Colaboração': 0,
            'Índice de Colaboração': 0
        }
        
        try:
            total_artigos = 0
            total_autores = 0
            max_autores = 0
            colaboracoes = 0

            for dados in self.dataframes.values():
                if 'ARTIGOS-PUBLICADOS' in dados and not dados['ARTIGOS-PUBLICADOS'].empty:
                    df = dados['ARTIGOS-PUBLICADOS']
                    total_artigos += len(df)
                    
                    if 'AUTORES' in df.columns:
                        for autores in df['AUTORES'].dropna():
                            # Contar autores usando delimitadores comuns
                            separadores = [';', ',', 'and', 'e']
                            for sep in separadores:
                                if sep in autores:
                                    num_autores = len([a for a in autores.split(sep) if a.strip()])
                                    total_autores += num_autores
                                    max_autores = max(max_autores, num_autores)
                                    if num_autores > 1:  # Se houver mais de um autor
                                        colaboracoes += 1
                                    break
                            else:  # Se não encontrar separadores, conta como 1 autor
                                total_autores += 1

            # Calcular métricas
            metricas['Total de Colaborações'] = colaboracoes
            if total_artigos > 0:
                metricas['Média de Autores por Artigo'] = total_autores / total_artigos
            metricas['Maior Grupo de Colaboração'] = max_autores
            metricas['Índice de Colaboração'] = self._calculate_collaboration_index()

            # Adicionar densidade da rede se houver pelo menos algumas colaborações
            if colaboracoes > 0:
                metricas['Densidade da Rede'] = colaboracoes / (total_artigos * (total_artigos - 1) / 2) if total_artigos > 1 else 0
        
        except Exception as e:
            print(f"Erro ao calcular métricas de rede: {e}")
        
        return metricas

    def _create_coauthorship_network(self):
        """Cria visualização da rede de coautoria"""
        fig = Figure(figsize=(8, 6))
        canvas = FigureCanvas(fig)
        ax = fig.add_subplot(111)

        try:
            # Coletar dados de coautoria
            coautorias = defaultdict(int)
            autores = set()

            for dados in self.dataframes.values():
                if 'ARTIGOS-PUBLICADOS' in dados and not dados['ARTIGOS-PUBLICADOS'].empty:
                    df = dados['ARTIGOS-PUBLICADOS']
                    if 'AUTORES' in df.columns:
                        for autores_str in df['AUTORES'].dropna():
                            # Processar string de autores
                            for separador in [';', ',', ' and ', ' e ']:
                                if separador in autores_str:
                                    lista_autores = [a.strip() for a in autores_str.split(separador) if a.strip()]
                                    break
                            else:
                                lista_autores = [autores_str.strip()]
                                
                            # Adicionar autores e registrar colaborações
                            if len(lista_autores) > 1:  # Precisa ter pelo menos 2 autores para colaboração
                                autores.update(lista_autores)
                                
                                # Registrar colaborações
                                for i in range(len(lista_autores)):
                                    for j in range(i + 1, len(lista_autores)):
                                        par = tuple(sorted([lista_autores[i], lista_autores[j]]))
                                        coautorias[par] += 1

            if not coautorias or len(autores) < 2:
                ax.text(0.5, 0.5, "Sem dados de coautoria disponíveis", 
                        horizontalalignment='center',
                        verticalalignment='center',
                        transform=ax.transAxes,
                        fontsize=14)
                ax.set_xticks([])
                ax.set_yticks([])
                return canvas

            # Limitar número de autores para visualização
            if len(autores) > 15:
                # Calcular frequência de cada autor em colaborações
                autores_freq = Counter()
                for (autor1, autor2), freq in coautorias.items():
                    autores_freq[autor1] += freq
                    autores_freq[autor2] += freq
                
                # Selecionar os 15 autores mais frequentes
                autores = set(dict(autores_freq.most_common(15)).keys())
                
                # Filtrar coautorias apenas desses autores
                coautorias = {k: v for k, v in coautorias.items() 
                             if k[0] in autores and k[1] in autores}
            
            # Criar layout circular
            autores = list(autores)
            n = len(autores)
            angles = np.linspace(0, 2*np.pi, n, endpoint=False)

            # Plotar nós (autores)
            x = np.cos(angles)
            y = np.sin(angles)
            ax.scatter(x, y, s=100, color='skyblue', edgecolor='white', linewidth=1.5, zorder=10)

            # Plotar arestas (colaborações)
            max_colab = max(coautorias.values()) if coautorias else 1
            for (autor1, autor2), weight in coautorias.items():
                if autor1 in autores and autor2 in autores:
                    i1 = autores.index(autor1)
                    i2 = autores.index(autor2)
                    alpha = 0.3 + 0.7 * (weight / max_colab)  # Mínimo 0.3 de opacidade
                    thickness = 0.5 + 2.5 * (weight / max_colab)  # Espessura entre 0.5 e 3
                    ax.plot([x[i1], x[i2]], [y[i1], y[i2]], 
                          color='gray', alpha=alpha, linewidth=thickness, zorder=5)
            
            # Adicionar rótulos dos autores
            for i, autor in enumerate(autores):
                # Encurtar nome para exibição
                nome_curto = autor.split()
                if len(nome_curto) > 1:
                    nome_display = f"{nome_curto[0][0]}. {nome_curto[-1]}"
                else:
                    nome_display = autor
                    
                # Posicionar rótulos ligeiramente fora dos nós
                offset = 1.1
                ax.annotate(nome_display, 
                            (offset * x[i], offset * y[i]), 
                            ha='center' if -0.1 < x[i] < 0.1 else ('right' if x[i] < 0 else 'left'),
                            va='center' if -0.1 < y[i] < 0.1 else ('top' if y[i] < 0 else 'bottom'),
                            fontsize=9,
                            fontweight='bold',
                            zorder=15)

            ax.set_title('Rede de Coautoria', fontsize=14)
            ax.axis('equal')
            ax.axis('off')
        
        except Exception as e:
            print(f"Erro ao gerar rede de coautoria: {e}")
            ax.clear()
            ax.text(0.5, 0.5, "Erro ao gerar rede de coautoria", 
                    ha='center', va='center', transform=ax.transAxes)
        
        fig.tight_layout()
        return canvas

    def _create_institutions_network(self):
        """Cria visualização da rede de instituições"""
        fig = Figure(figsize=(8, 6))
        canvas = FigureCanvas(fig)
        ax = fig.add_subplot(111)

        try:
            # Coletar dados de colaboração institucional
            colaboracoes = defaultdict(int)
            instituicoes = set()

            for dados in self.dataframes.values():
                if 'ARTIGOS-PUBLICADOS' in dados and not dados['ARTIGOS-PUBLICADOS'].empty:
                    df = dados['ARTIGOS-PUBLICADOS']
                    # Verificar se há coluna de instituição
                    inst_cols = [col for col in df.columns if 'INSTITUIC' in col.upper()]
                    if not inst_cols:
                        continue
                        
                    inst_col = inst_cols[0]  # Usar a primeira coluna de instituição encontrada
                    
                    for _, row in df.iterrows():
                        if pd.notna(row.get(inst_col)):
                            # Separar instituições por algum delimitador comum
                            inst_text = str(row.get(inst_col))
                            for sep in [';', ',']:
                                if sep in inst_text:
                                    inst_list = [i.strip() for i in inst_text.split(sep) if i.strip()]
                                    break
                            else:
                                inst_list = [inst_text.strip()]
                            
                            # Adicionar instituições
                            instituicoes.update(inst_list)
                            
                            # Registrar colaborações entre instituições
                            inst_list = list(set(inst_list))  # Remover duplicatas
                            for i in range(len(inst_list)):
                                for j in range(i + 1, len(inst_list)):
                                    par = tuple(sorted([inst_list[i], inst_list[j]]))
                                    colaboracoes[par] += 1

            if not colaboracoes or len(instituicoes) < 2:
                ax.text(0.5, 0.5, "Sem dados de colaboração institucional disponíveis", 
                        horizontalalignment='center',
                        verticalalignment='center',
                        transform=ax.transAxes,
                        fontsize=14)
                ax.set_xticks([])
                ax.set_yticks([])
                return canvas

            # Limitar número de instituições para visualização
            if len(instituicoes) > 12:
                # Pegar as instituições mais frequentes em colaborações
                inst_freq = Counter()
                for (inst1, inst2), freq in colaboracoes.items():
                    inst_freq[inst1] += freq
                    inst_freq[inst2] += freq
                instituicoes = set(dict(inst_freq.most_common(12)).keys())
                
                # Filtrar colaborações
                colaboracoes = {k: v for k, v in colaboracoes.items() 
                                if k[0] in instituicoes and k[1] in instituicoes}

            # Criar layout circular
            instituicoes = list(instituicoes)
            n = len(instituicoes)
            angles = np.linspace(0, 2*np.pi, n, endpoint=False)

            # Plotar nós (instituições)
            x = np.cos(angles)
            y = np.sin(angles)
            ax.scatter(x, y, s=120, c='lightgreen', edgecolor='darkgreen', linewidth=1, zorder=10)

            # Plotar arestas (colaborações)
            max_colab = max(colaboracoes.values()) if colaboracoes else 1
            for (inst1, inst2), weight in colaboracoes.items():
                if inst1 in instituicoes and inst2 in instituicoes:
                    i1 = instituicoes.index(inst1)
                    i2 = instituicoes.index(inst2)
                    alpha = 0.3 + 0.6 * (weight / max_colab)
                    thickness = 0.5 + 2 * (weight / max_colab)
                    ax.plot([x[i1], x[i2]], [y[i1], y[i2]], 
                           color='gray', alpha=alpha, linewidth=thickness, zorder=5)

            # Adicionar rótulos das instituições
            for i, inst in enumerate(instituicoes):
                # Abreviar nome da instituição
                nome_curto = inst.split()
                if len(nome_curto) > 2:
                    nome_display = ' '.join(nome_curto[:2]) + '...'
                else:
                    nome_display = inst
                
                # Posicionar rótulos ligeiramente fora dos nós
                offset = 1.1
                ax.annotate(nome_display, 
                           (offset * x[i], offset * y[i]), 
                           ha='center' if -0.1 < x[i] < 0.1 else ('right' if x[i] < 0 else 'left'),
                           va='center' if -0.1 < y[i] < 0.1 else ('top' if y[i] < 0 else 'bottom'),
                           fontsize=8,
                           fontweight='bold',
                           zorder=15)

            ax.set_title('Rede de Colaboração Institucional', fontsize=14)
            ax.axis('equal')
            ax.axis('off')
        
        except Exception as e:
            print(f"Erro ao gerar rede institucional: {e}")
            ax.clear()
            ax.text(0.5, 0.5, "Erro ao gerar rede institucional", 
                    ha='center', va='center', transform=ax.transAxes)
        
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

    def get_scholar_info(self, researcher_name):
        """Busca informações completas do pesquisador no Google Scholar"""
        try:
            # Mostrar diálogo de progresso
            progress = QProgressDialog("Buscando dados no Google Scholar...", "Cancelar", 0, 100, self)
            progress.setWindowTitle("Google Scholar")
            progress.setWindowModality(Qt.WindowModal)
            progress.show()
            
            # Buscar autor
            progress.setValue(10)
            search_query = scholarly.search_author(researcher_name)
            author = next(search_query, None)
            
            if not author:
                progress.cancel()
                return None
                
            # Preencher dados básicos do autor
            progress.setValue(30)
            progress.setLabelText("Carregando perfil do pesquisador...")
            author = scholarly.fill(author)
            
            # Preparar para buscar artigos
            progress.setValue(50)
            progress.setLabelText("Buscando artigos...")
            
            # Coletar todos os artigos (isso pode demorar)
            articles = []
            for i, pub in enumerate(author.get('publications', [])):
                try:
                    # Atualizar progresso, limitando em 90%
                    progress_val = min(50 + int((i / len(author['publications'])) * 40), 90)
                    progress.setValue(progress_val)
                    progress.setLabelText(f"Buscando artigo {i+1} de {len(author['publications'])}...")
                    
                    # Verificar se o usuário cancelou
                    if progress.wasCanceled():
                        return None
                    
                    # Preencher dados do artigo
                    filled_pub = scholarly.fill(pub)
                    articles.append(filled_pub)
                except Exception as e:
                    print(f"Erro ao processar artigo: {e}")
                    continue
                    
            progress.setValue(95)
            progress.setLabelText("Organizando dados...")
            
            # Organizar resultados
            result = {
                'profile': {
                    'name': author.get('name', ''),
                    'affiliation': author.get('affiliation', ''),
                    'interests': author.get('interests', []),
                    'citedby': author.get('citedby', 0),
                    'h_index': author.get('hindex', 0),
                    'i10_index': author.get('i10index', 0),
                    'scholar_id': author.get('scholar_id', '')
                },
                'articles': articles
            }
            
            progress.setValue(100)
            progress.close()
            return result
            
        except Exception as e:
            print(f"Erro ao buscar informações no Google Scholar: {e}")
            if 'progress' in locals():
                progress.cancel()
            return None

    def show_scholar_info(self):
        """Mostra janela para consulta e exibição de dados do Google Scholar"""
        # Mostrar diálogo para input do nome do pesquisador
        researcher_name, ok = QInputDialog.getText(
            self, "Buscar Pesquisador", 
            "Digite o nome do pesquisador:"
        )
        
        if not ok or not researcher_name.strip():
            return
            
        # Buscar dados
        scholar_data = self.get_scholar_info(researcher_name)
        
        if not scholar_data:
            QMessageBox.warning(self, "Busca Scholar", "Não foi possível encontrar o pesquisador ou a busca foi cancelada.")
            return
            
        # Criar janela de exibição
        dialog = QDialog(self)
        dialog.setWindowTitle(f"Perfil Scholar: {scholar_data['profile']['name']}")
        dialog.setMinimumSize(900, 700)
        layout = QVBoxLayout(dialog)
        
        # Adicionar abas
        tabs = QTabWidget()
        layout.addWidget(tabs)
        
        # Aba de perfil
        profile_tab = QWidget()
        profile_layout = QVBoxLayout(profile_tab)
        
        # Informações do perfil
        profile_info = QWidget()
        profile_info_layout = QGridLayout(profile_info)
        
        # Nome
        profile_info_layout.addWidget(QLabel("<b>Nome:</b>"), 0, 0)
        profile_info_layout.addWidget(QLabel(scholar_data['profile']['name']), 0, 1)
        
        # Afiliação
        profile_info_layout.addWidget(QLabel("<b>Afiliação:</b>"), 1, 0)
        profile_info_layout.addWidget(QLabel(scholar_data['profile']['affiliation']), 1, 1)
        
        # Interesses
        profile_info_layout.addWidget(QLabel("<b>Interesses:</b>"), 2, 0)
        interests_text = ", ".join(scholar_data['profile']['interests'])
        profile_info_layout.addWidget(QLabel(interests_text), 2, 1)
        
        # Métricas
        profile_info_layout.addWidget(QLabel("<b>Total de Citações:</b>"), 3, 0)
        profile_info_layout.addWidget(QLabel(str(scholar_data['profile']['citedby'])), 3, 1)
        
        profile_info_layout.addWidget(QLabel("<b>Índice H:</b>"), 4, 0)
        profile_info_layout.addWidget(QLabel(str(scholar_data['profile']['h_index'])), 4, 1)
        
        profile_info_layout.addWidget(QLabel("<b>Índice i10:</b>"), 5, 0)
        profile_info_layout.addWidget(QLabel(str(scholar_data['profile']['i10_index'])), 5, 1)
        
        # Link para perfil
        profile_info_layout.addWidget(QLabel("<b>ID Scholar:</b>"), 6, 0)
        scholar_id = scholar_data['profile']['scholar_id']
        id_label = QLabel(f'<a href="https://scholar.google.com/citations?user={scholar_id}">{scholar_id}</a>')
        id_label.setOpenExternalLinks(True)
        profile_info_layout.addWidget(id_label, 6, 1)
        
        profile_layout.addWidget(profile_info)
        
        # Criar gráfico de citações
        profile_layout.addWidget(QLabel("<h3>Citações por Artigo</h3>"))
        citations_chart = self._create_scholar_citations_chart(scholar_data['articles'])
        profile_layout.addWidget(citations_chart)
        
        # Adicionar aba de perfil
        tabs.addTab(profile_tab, "Perfil")
        
        # Aba de artigos
        articles_tab = QWidget()
        articles_layout = QVBoxLayout(articles_tab)
        
        # Tabela de artigos
        articles_table = QTableWidget()
        articles_table.setColumnCount(5)
        articles_table.setHorizontalHeaderLabels(["Título", "Ano", "Revista/Conferência", "Citações", "Link"])
        articles_table.setRowCount(len(scholar_data['articles']))
        
        # Preencher tabela
        for row, article in enumerate(scholar_data['articles']):
            # Título
            title_item = QTableWidgetItem(article.get('bib', {}).get('title', ''))
            articles_table.setItem(row, 0, title_item)
            
            # Ano
            year = article.get('bib', {}).get('pub_year', '')
            year_item = QTableWidgetItem(str(year))
            articles_table.setItem(row, 1, year_item)
            
            # Revista/Conferência
            venue = article.get('bib', {}).get('venue', '')
            venue_item = QTableWidgetItem(venue)
            articles_table.setItem(row, 2, venue_item)
            
            # Citações
            citations = article.get('num_citations', 0)
            citations_item = QTableWidgetItem(str(citations))
            articles_table.setItem(row, 3, citations_item)
            
            # Link
            link = article.get('pub_url', '')
            link_item = QTableWidgetItem(link)
            articles_table.setItem(row, 4, link_item)
        
        articles_layout.addWidget(articles_table)
        articles_table.resizeColumnsToContents()
        
        # Adicionar aba de artigos
        tabs.addTab(articles_tab, "Artigos")
        
        # Botões de ação
        buttons_layout = QHBoxLayout()
        
        # Botão para exportar dados
        export_btn = QPushButton("Exportar Dados")
        export_btn.clicked.connect(lambda: self._export_scholar_data(scholar_data))
        buttons_layout.addWidget(export_btn)
        
        # Botão para importar artigos para o sistema
        import_btn = QPushButton("Importar Artigos")
        import_btn.clicked.connect(lambda: self._import_scholar_articles(scholar_data))
        buttons_layout.addWidget(import_btn)
        
        layout.addLayout(buttons_layout)
        
        dialog.exec_()

    def _create_scholar_citations_chart(self, articles):
        """Cria um gráfico de citações dos artigos do pesquisador"""
        fig = Figure(figsize=(8, 5))
        canvas = FigureCanvas(fig)
        ax = fig.add_subplot(111)
        
        # Preparar dados - top 10 artigos mais citados
        article_data = []
        for article in articles:
            title = article.get('bib', {}).get('title', '')
            citations = article.get('num_citations', 0)
            year = article.get('bib', {}).get('pub_year', '')
            
            if title and citations:
                article_data.append((title, citations, year))
        
        # Ordenar por citações e pegar top 10
        article_data.sort(key=lambda x: x[1], reverse=True)
        top_articles = article_data[:10]
        
        if not top_articles:
            ax.text(0.5, 0.5, "Sem dados de citações disponíveis", 
                    horizontalalignment='center',
                    verticalalignment='center',
                    transform=ax.transAxes,
                    fontsize=14)
            return canvas
        
        # Criar gráfico
        titles = [f"{a[0][:30]}... ({a[2]})" if len(a[0]) > 30 else f"{a[0]} ({a[2]})" for a in top_articles]
        citations = [a[1] for a in top_articles]
        
        y_pos = range(len(titles))
        ax.barh(y_pos, citations, align='center', color='skyblue', edgecolor='navy')
        ax.set_yticks(y_pos)
        ax.set_yticklabels(titles)
        ax.invert_yaxis()  # Inverter para que o maior apareça no topo
        ax.set_xlabel('Número de Citações')
        ax.set_title('Top 10 Artigos por Citações')
        
        # Adicionar valores nas barras
        for i, v in enumerate(citations):
            ax.text(v + 0.5, i, str(v), va='center')
        
        fig.tight_layout()
        return canvas

    def _export_scholar_data(self, data):
        """Exporta os dados do scholar para CSV"""
        try:
            # Exportar perfil
            profile_df = pd.DataFrame([data['profile']])
            profile_df.to_csv(f"scholar_profile_{data['profile']['name'].replace(' ', '_')}.csv", 
                              index=False, encoding='utf-8-sig')
            
            # Exportar artigos
            articles_data = []
            for article in data['articles']:
                bib = article.get('bib', {})
                articles_data.append({
                    'title': bib.get('title', ''),
                    'year': bib.get('pub_year', ''),
                    'venue': bib.get('venue', ''),
                    'citations': article.get('num_citations', 0),
                    'url': article.get('pub_url', '')
                })
            
            articles_df = pd.DataFrame(articles_data)
            articles_df.to_csv(f"scholar_articles_{data['profile']['name'].replace(' ', '_')}.csv", 
                               index=False, encoding='utf-8-sig')
                               
            QMessageBox.information(self, "Exportação", "Dados exportados com sucesso!")
        except Exception as e:
            QMessageBox.warning(self, "Erro", f"Erro ao exportar dados: {e}")

    def _import_scholar_articles(self, scholar_data):
        """Importa artigos do Google Scholar para o sistema atual"""
        try:
            # Verificar se tem um currículo selecionado
            selected_items = self.tree.selectedItems()
            if not selected_items:
                QMessageBox.warning(self, "Importação", "Selecione um currículo para importar os artigos.")
                return
                
            item = selected_items[0]
            curriculo_id = item.data(0, Qt.UserRole)
            if isinstance(curriculo_id, tuple):
                curriculo_id = curriculo_id[0]
                
            if curriculo_id not in self.dataframes:
                QMessageBox.warning(self, "Importação", "Currículo inválido selecionado.")
                return
                
            # Criar DataFrame de artigos
            articles_data = []
            for article in scholar_data['articles']:
                bib = article.get('bib', {})
                
                # Converter dados para o formato esperado pelo sistema
                articles_data.append({
                    'TITULO-DO-ARTIGO': bib.get('title', ''),
                    'ANO': bib.get('pub_year', ''),
                    'REVISTA': bib.get('venue', ''),
                    'DOI': '',  # Scholar não fornece DOI diretamente
                    'GOOGLE_SCHOLAR_CITATIONS': article.get('num_citations', 0),
                    'URL': article.get('pub_url', ''),
                    'AUTORES': bib.get('author', ''),
                    'IMPORTADO_GOOGLE_SCHOLAR': 'Sim'
                })
            
            # Criar DataFrame
            scholar_df = pd.DataFrame(articles_data)
            
            # Verificar se já existe o DataFrame para artigos publicados
            if 'ARTIGOS-PUBLICADOS' in self.dataframes[curriculo_id]:
                # Perguntar se deve mesclar ou substituir
                reply = QMessageBox.question(
                    self, 'Importar Artigos',
                    'Deseja mesclar com artigos existentes ou substituir?',
                    QMessageBox.Abort | QMessageBox.Yes | QMessageBox.No,
                    QMessageBox.Yes
                )
                
                if reply == QMessageBox.Abort:
                    return
                elif reply == QMessageBox.Yes:  # Mesclar
                    # Identificar artigos que podem ser duplicados (pelo título)
                    existing_df = self.dataframes[curriculo_id]['ARTIGOS-PUBLICADOS']
                    
                    # Encontrar títulos que não existem no DataFrame atual
                    new_articles = scholar_df[~scholar_df['TITULO-DO-ARTIGO'].isin(
                        existing_df['TITULO-DO-ARTIGO'])]
                    
                    if len(new_articles) == 0:
                        QMessageBox.information(self, "Importação", 
                                               "Não foram encontrados novos artigos para importar.")
                        return
                    
                    # Concatenar com artigos existentes
                    self.dataframes[curriculo_id]['ARTIGOS-PUBLICADOS'] = pd.concat(
                        [existing_df, new_articles], ignore_index=True)
                    
                    QMessageBox.information(self, "Importação", 
                                           f"{len(new_articles)} novos artigos foram importados.")
                
                else:  # Substituir
                    self.dataframes[curriculo_id]['ARTIGOS-PUBLICADOS'] = scholar_df
                    QMessageBox.information(self, "Importação", 
                                           f"{len(scholar_df)} artigos foram importados, substituindo os anteriores.")
            
            else:
                # Criar novo DataFrame de artigos
                self.dataframes[curriculo_id]['ARTIGOS-PUBLICADOS'] = scholar_df
                QMessageBox.information(self, "Importação", 
                                       f"{len(scholar_df)} artigos foram importados.")
            
            # Atualizar visualização se necessário
            self.display_data(self.dataframes[curriculo_id]['ARTIGOS-PUBLICADOS'], 'ARTIGOS-PUBLICADOS')
            
        except Exception as e:
            QMessageBox.warning(self, "Erro", f"Erro ao importar artigos: {e}")

def main():
    app = QApplication(sys.argv)
    viewer = CurriculoViewer()
    viewer.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
