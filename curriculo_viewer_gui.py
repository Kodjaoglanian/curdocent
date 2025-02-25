import sys
import os
import pandas as pd
import glob
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                            QHBoxLayout, QPushButton, QLabel, QLineEdit, 
                            QTableWidget, QTableWidgetItem, QTabWidget, 
                            QTreeWidget, QTreeWidgetItem, QSplitter, QScrollArea, 
                            QComboBox, QDialog, QMessageBox, QGridLayout,
                            QProgressDialog, QProgressBar)  # Adicionar QProgressDialog e QProgressBar
from PyQt5.QtCore import Qt, QTimer
from stats_analyzer import CurriculoAnalyzer
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from scimago_data import load_scimago_data
from advanced_search import ArticleSearch

class SplashScreen(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("")
        self.setFixedSize(600, 300)
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
        # Widget principal com scroll
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        
        # Container para o conteúdo
        container = QWidget()
        layout = QVBoxLayout(container)
        
        # Botões de controle
        controls = QHBoxLayout()
        self.stats_global_btn = QPushButton("Estatísticas Globais")
        self.stats_global_btn.clicked.connect(self.show_global_stats)
        self.stats_individual_btn = QPushButton("Estatísticas Individuais")
        self.stats_individual_btn.clicked.connect(self.show_individual_stats)
        
        controls.addWidget(self.stats_global_btn)
        controls.addWidget(self.stats_individual_btn)
        layout.addLayout(controls)
        
        # Área de visualização com scroll
        stats_container = QWidget()
        self.stats_area = QVBoxLayout(stats_container)
        layout.addWidget(stats_container)
        
        # Configurar scroll
        scroll.setWidget(container)
        
        return scroll

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
        self._clear_stats_area()
        stats = self.analyzer.analyze_all_curriculos()
        
        # Resumo geral
        self._add_stats_section("Resumo Geral", self._create_info_table(stats['resumo']))
        
        # Titulação
        if 'titulacao' in stats and 'distribuicao' in stats['titulacao']:
            self._add_stats_section("Titulação dos Docentes", self._create_pie_chart(
                stats['titulacao']['distribuicao'], "Distribuição de Titulação"))
        
        # Produção Científica - Correção
        if 'producao' in stats:
            producao_data = {}
            if 'volumes' in stats['producao']:
                volumes = stats['producao']['volumes']
                producao_data = {
                    'Artigos': volumes.get('artigos', 0),
                    'Livros': volumes.get('livros', 0),
                    'Capítulos': volumes.get('capitulos', 0),
                    'Eventos': volumes.get('eventos', 0)
                }
                
                if any(producao_data.values()):  # Verifica se há algum valor maior que 0
                    self._add_stats_section("Produção Científica", self._create_bar_chart(
                        producao_data, "Total de Produções por Tipo"))
        
        # Áreas
        if 'areas' in stats and 'grandes_areas' in stats['areas']:
            self._add_stats_section("Áreas de Atuação", self._create_horizontal_bar_chart(
                dict(stats['areas']['grandes_areas']), "Principais Áreas de Atuação"))
        
        # Tendências
        if 'tendencias' in stats and 'evolucao_anual' in stats['tendencias']:
            evolucao = stats['tendencias']['evolucao_anual']
            total_por_ano = {ano: sum(prods.values()) for ano, prods in evolucao.items()}
            self._add_stats_section("Evolução Temporal", self._create_line_chart(
                total_por_ano, "Produção Total por Ano"))

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
        if not data or all(v == 0 for v in data.values()):
            return QLabel("Sem dados disponíveis")

        fig = Figure(figsize=(8, 4))
        ax = fig.add_subplot(111)
        
        labels = list(data.keys())
        values = list(data.values())
        
        # Criar barras
        bars = ax.bar(range(len(data)), values)
        
        # Configurar eixos
        ax.set_xticks(range(len(data)))
        ax.set_xticklabels(labels, rotation=45, ha='right')
        
        # Adicionar valores sobre as barras
        for bar in bars:
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height,
                   f'{int(height)}',
                   ha='center', va='bottom')
        
        # Ajustar layout e título
        ax.set_title(title)
        fig.tight_layout()  # Ajusta automaticamente o layout
        
        canvas = FigureCanvas(fig)
        canvas.setMinimumSize(500, 300)
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
        if not data:
            return QLabel("Sem dados disponíveis")

        # Verificar se os dados são numéricos
        filtered_data = {k: v for k, v in data.items() if isinstance(v, (int, float))}
        if not filtered_data:
            return QLabel("Dados inválidos para o gráfico")

        fig = Figure(figsize=(10, 4))
        ax = fig.add_subplot(111)
        
        years = sorted(filtered_data.keys())
        values = [filtered_data[year] for year in years]
        
        ax.plot(years, values, marker='o')
        ax.set_xlabel('Ano')
        ax.set_ylabel('Quantidade')
        ax.set_title(title)
        ax.grid(True)
        
        canvas = FigureCanvas(fig)
        canvas.setMinimumSize(600, 300)
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
        search_type = self.search_type.currentText().lower()
        
        # Tratar busca por ano de forma especial
        if search_type == 'ano':
            year = self.filter_year.text().strip() or self.search_field.text().strip()
            if not year:
                QMessageBox.warning(self, "Aviso", "Digite um ano para filtrar")
                return
                
            results = self.article_search.get_all_articles()
            if results is not None and not results.empty:
                results = self.article_search.filter_results(results, {'Year': year})
        
        # Busca normal para outros tipos
        else:
            query = self.search_field.text().strip()
            if not query:
                QMessageBox.warning(self, "Aviso", "Digite um termo para busca")
                return
                
            field_map = {
                'título': 'title',
                'issn': 'issn',
                'doi': 'doi'
            }
            search_field = field_map.get(search_type, 'title')
            results = self.article_search.search_by_criteria(query, search_field)

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

def main():
    app = QApplication(sys.argv)
    viewer = CurriculoViewer()
    viewer.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()