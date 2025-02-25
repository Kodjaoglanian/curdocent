import os
import xml.etree.ElementTree as ET
import pandas as pd
import glob
import shutil

def create_directories():
    # Cria diretórios para organização
    base_dir = os.path.dirname(os.path.abspath(__file__))
    input_dir = os.path.join(base_dir, 'xml_input')
    output_dir = os.path.join(base_dir, 'csv_output')
    
    # Cria os diretórios se não existirem
    os.makedirs(input_dir, exist_ok=True)
    os.makedirs(output_dir, exist_ok=True)
    
    return base_dir, input_dir, output_dir

def move_xml_files(base_dir, input_dir):
    # Move arquivos XML do diretório base para input_dir
    xml_files = glob.glob(os.path.join(base_dir, '*.xml'))
    for xml_file in xml_files:
        filename = os.path.basename(xml_file)
        destination = os.path.join(input_dir, filename)
        if xml_file != destination:  # Evita tentar mover se já estiver no destino
            shutil.move(xml_file, destination)
            print(f'Movido: {filename} para pasta de entrada')

def extract_curriculo_data(xml_file):
    tree = ET.parse(xml_file)
    root = tree.getroot()
    
    curriculo_data = {
        'DADOS-GERAIS': [],
        'FORMACAO-ACADEMICA': [],
        'ATUACOES-PROFISSIONAIS': [],
        'ARTIGOS-PUBLICADOS': [],
        'LIVROS-PUBLICADOS': [],
        'TRABALHOS-EVENTOS': [],
        'CAPITULOS-LIVROS': [],
        'AREAS-DE-ATUACAO': [],
        'ORIENTACOES': [],
        'PALAVRAS-CHAVES': [],
        'SOFTWARE': [],
        'PATENTES': [],
        'PRODUTOS-TECNOLOGICOS': [],
        'TRABALHOS-TECNICOS': [],
        'DEMAIS-PRODUCOES-TECNICAS': [],
        'ORIENTACOES-MESTRADO': [],
        'ORIENTACOES-DOUTORADO': [],
        'ORIENTACOES-POS-DOUTORADO': [],
        'OUTRAS-ORIENTACOES': [],
        'PREMIOS-TITULOS': [],
        'PROJETOS-PESQUISA': []
    }
    
    def clean_value(value):
        if not value or value.lower() in ['', 'nan', 'none', 'nao_informado', 'nao informado']:
            return None
        return value
    
    # Dados Gerais - apenas informações relevantes
    dados_gerais = root.find('.//DADOS-GERAIS')
    if (dados_gerais is not None):
        dados_dict = {
            'NOME-COMPLETO': clean_value(dados_gerais.get('NOME-COMPLETO')),
            'CPF': clean_value(dados_gerais.get('NUMERO-DO-CPF')),
            'PAIS-DE-NASCIMENTO': clean_value(dados_gerais.get('PAIS-DE-NASCIMENTO')),
            'EMAIL': clean_value(dados_gerais.get('E-MAIL')),
        }
        
        # Endereço profissional relevante
        endereco = dados_gerais.find('.//ENDERECO-PROFISSIONAL')
        if endereco is not None:
            dados_dict.update({
                'INSTITUICAO': clean_value(endereco.get('NOME-INSTITUICAO-EMPRESA')),
                'CIDADE': clean_value(endereco.get('CIDADE')),
                'UF': clean_value(endereco.get('UF'))
            })
        
        curriculo_data['DADOS-GERAIS'].append(dados_dict)
    
    # Formação Acadêmica - apenas concluídos e em andamento
    for nivel in ['GRADUACAO', 'ESPECIALIZACAO', 'MESTRADO', 'DOUTORADO', 'POS-DOUTORADO']:
        for formacao in root.findall(f'.//FORMACAO-ACADEMICA-TITULACAO//{nivel}'):
            status = clean_value(formacao.get('STATUS-DO-CURSO'))
            if status in ['CONCLUIDO', 'EM_ANDAMENTO']:
                form_dict = {
                    'NIVEL': nivel,
                    'CURSO': clean_value(formacao.get('NOME-CURSO')),
                    'INSTITUICAO': clean_value(formacao.get('NOME-INSTITUICAO')),
                    'ANO-INICIO': clean_value(formacao.get('ANO-DE-INICIO')),
                    'ANO-CONCLUSAO': clean_value(formacao.get('ANO-DE-CONCLUSAO')),
                    'STATUS': 'Concluído' if status == 'CONCLUIDO' else 'Em Andamento'
                }
                curriculo_data['FORMACAO-ACADEMICA'].append(form_dict)
    
    # Atuações Profissionais - apenas vínculos ativos
    for atuacao in root.findall('.//ATUACAO-PROFISSIONAL'):
        vinculos = atuacao.findall('.//VINCULO-PROFISSIONAL')
        vinculos_ativos = []
        
        for vinculo in vinculos:
            ano_fim = clean_value(vinculo.get('ANO-FIM'))
            if not ano_fim:  # Vínculo atual
                vinc_dict = {
                    'INSTITUICAO': clean_value(atuacao.get('NOME-INSTITUICAO')),
                    'TIPO-VINCULO': clean_value(vinculo.get('TIPO-DE-VINCULO')),
                    'ANO-INICIO': clean_value(vinculo.get('ANO-INICIO')),
                    'ENQUADRAMENTO': clean_value(vinculo.get('ENQUADRAMENTO-FUNCIONAL'))
                }
                vinculos_ativos.append(vinc_dict)
        
        if vinculos_ativos:
            curriculo_data['ATUACOES-PROFISSIONAIS'].extend(vinculos_ativos)
    
    # Artigos Publicados - últimos 5 anos
    ano_atual = pd.Timestamp.now().year
    for artigo in root.findall('.//ARTIGO-PUBLICADO'):
        dados = artigo.find('.//DADOS-BASICOS-DO-ARTIGO')
        if dados is not None:
            ano = clean_value(dados.get('ANO-DO-ARTIGO'))
            if ano and int(ano) >= (ano_atual - 5):
                detalhes = artigo.find('.//DETALHAMENTO-DO-ARTIGO')
                art_dict = {
                    'TITULO': clean_value(dados.get('TITULO-DO-ARTIGO')),
                    'ANO': ano,
                    'REVISTA': clean_value(detalhes.get('TITULO-DO-PERIODICO-OU-REVISTA')) if detalhes is not None else None,
                    'ISSN': clean_value(detalhes.get('ISSN')) if detalhes is not None else None,
                    'DOI': clean_value(dados.get('DOI')),
                    'IDIOMA': clean_value(dados.get('IDIOMA'))
                }
                curriculo_data['ARTIGOS-PUBLICADOS'].append(art_dict)
    
    # Livros Publicados
    for livro in root.findall('.//LIVRO-PUBLICADO-OU-ORGANIZADO'):
        dados = livro.find('.//DADOS-BASICOS-DO-LIVRO')
        if dados is not None:
            ano = clean_value(dados.get('ANO'))
            if ano:
                detalhes = livro.find('.//DETALHAMENTO-DO-LIVRO')
                livro_dict = {
                    'TITULO': clean_value(dados.get('TITULO-DO-LIVRO')),
                    'ANO': ano,
                    'EDITORA': clean_value(detalhes.get('NOME-DA-EDITORA')) if detalhes is not None else None,
                    'ISBN': clean_value(detalhes.get('ISBN')) if detalhes is not None else None,
                    'TIPO': clean_value(dados.get('TIPO'))
                }
                curriculo_data['LIVROS-PUBLICADOS'].append(livro_dict)

    # Capítulos de Livros
    for capitulo in root.findall('.//CAPITULO-DE-LIVRO-PUBLICADO'):
        dados = capitulo.find('.//DADOS-BASICOS-DO-CAPITULO')
        if dados is not None:
            ano = clean_value(dados.get('ANO'))
            if ano:
                detalhes = capitulo.find('.//DETALHAMENTO-DO-CAPITULO')
                cap_dict = {
                    'TITULO-CAPITULO': clean_value(dados.get('TITULO-DO-CAPITULO-DO-LIVRO')),
                    'TITULO-LIVRO': clean_value(detalhes.get('TITULO-DO-LIVRO')) if detalhes is not None else None,
                    'ANO': ano,
                    'EDITORA': clean_value(detalhes.get('NOME-DA-EDITORA')) if detalhes is not None else None,
                    'ISBN': clean_value(detalhes.get('ISBN')) if detalhes is not None else None
                }
                curriculo_data['CAPITULOS-LIVROS'].append(cap_dict)

    # Trabalhos em Eventos
    for trabalho in root.findall('.//TRABALHO-EM-EVENTOS'):
        dados = trabalho.find('.//DADOS-BASICOS-DO-TRABALHO')
        if dados is not None:
            ano = clean_value(dados.get('ANO-DO-TRABALHO'))
            if ano:
                detalhes = trabalho.find('.//DETALHAMENTO-DO-TRABALHO')
                trab_dict = {
                    'TITULO': clean_value(dados.get('TITULO-DO-TRABALHO')),
                    'ANO': ano,
                    'EVENTO': clean_value(detalhes.get('NOME-DO-EVENTO')) if detalhes is not None else None,
                    'TIPO': clean_value(dados.get('NATUREZA')),
                    'PAIS': clean_value(dados.get('PAIS-DO-EVENTO'))
                }
                curriculo_data['TRABALHOS-EVENTOS'].append(trab_dict)

    # Áreas de Atuação - apenas com área definida
    for area in root.findall('.//AREA-DE-ATUACAO'):
        if clean_value(area.get('NOME-DA-AREA')):
            area_dict = {
                'GRANDE-AREA': clean_value(area.get('NOME-GRANDE-AREA')),
                'AREA': clean_value(area.get('NOME-DA-AREA')),
                'SUBAREA': clean_value(area.get('NOME-DA-SUB-AREA')),
                'ESPECIALIDADE': clean_value(area.get('NOME-DA-ESPECIALIDADE'))
            }
            curriculo_data['AREAS-DE-ATUACAO'].append(area_dict)
    
    # Extrair palavras-chaves
    palavras = root.findall('.//PALAVRA-CHAVE')
    for palavra in palavras:
        palavra_dict = {
            'PALAVRA': clean_value(palavra.get('TEXTO')),
            'SETOR': clean_value(palavra.find('../..').get('SETOR-DE-APLICACAO'))
        }
        curriculo_data['PALAVRAS-CHAVES'].append(palavra_dict)

    # Software
    for software in root.findall('.//SOFTWARE'):
        dados = software.find('.//DADOS-BASICOS-DO-SOFTWARE')
        if dados is not None:
            soft_dict = {
                'TITULO': clean_value(dados.get('TITULO-DO-SOFTWARE')),
                'ANO': clean_value(dados.get('ANO')),
                'SITUACAO': clean_value(software.find('.//DETALHAMENTO-DO-SOFTWARE').get('SITUACAO')),
                'NATUREZA': clean_value(dados.get('NATUREZA'))
            }
            curriculo_data['SOFTWARE'].append(soft_dict)

    # Patentes
    for patente in root.findall('.//PATENTE'):
        dados = patente.find('.//DADOS-BASICOS-DA-PATENTE')
        if dados is not None:
            pat_dict = {
                'TITULO': clean_value(dados.get('TITULO')),
                'ANO': clean_value(dados.get('ANO-DESENVOLVIMENTO')),
                'SITUACAO': clean_value(patente.find('.//DETALHAMENTO-DA-PATENTE').get('STATUS')),
                'TIPO': clean_value(dados.get('TIPO'))
            }
            curriculo_data['PATENTES'].append(pat_dict)

    # Produtos Tecnológicos
    for produto in root.findall('.//PRODUTO-TECNOLOGICO'):
        dados = produto.find('.//DADOS-BASICOS-DO-PRODUTO-TECNOLOGICO')
        if dados is not None:
            prod_dict = {
                'TITULO': clean_value(dados.get('TITULO-DO-PRODUTO')),
                'ANO': clean_value(dados.get('ANO')),
                'TIPO': clean_value(dados.get('TIPO')),
                'SITUACAO': clean_value(produto.find('.//DETALHAMENTO-DO-PRODUTO-TECNOLOGICO').get('FINALIDADE'))
            }
            curriculo_data['PRODUTOS-TECNOLOGICOS'].append(prod_dict)

    # Trabalhos Técnicos
    for trabalho in root.findall('.//TRABALHO-TECNICO'):
        dados = trabalho.find('.//DADOS-BASICOS-DO-TRABALHO-TECNICO')
        if dados is not None:
            tec_dict = {
                'TITULO': clean_value(dados.get('TITULO-DO-TRABALHO-TECNICO')),
                'ANO': clean_value(dados.get('ANO')),
                'TIPO': clean_value(dados.get('NATUREZA')),
                'INSTITUICAO': clean_value(trabalho.find('.//DETALHAMENTO-DO-TRABALHO-TECNICO').get('INSTITUICAO'))
            }
            curriculo_data['TRABALHOS-TECNICOS'].append(tec_dict)

    # Demais Produções Técnicas
    for producao in root.findall('.//DEMAIS-TIPOS-DE-PRODUCAO-TECNICA/*'):
        if producao.tag != 'TRABALHO-TECNICO':  # Evitar duplicação
            dados = producao.find('.//DADOS-BASICOS-DE-OUTRA-PRODUCAO')
            if dados is not None:
                prod_dict = {
                    'TITULO': clean_value(dados.get('TITULO')),
                    'ANO': clean_value(dados.get('ANO')),
                    'NATUREZA': clean_value(dados.get('NATUREZA')),
                    'TIPO': producao.tag
                }
                curriculo_data['DEMAIS-PRODUCOES-TECNICAS'].append(prod_dict)

    # Orientações
    for nivel in ['MESTRADO', 'DOUTORADO', 'POS-DOUTORADO']:
        for orientacao in root.findall(f'.//ORIENTACOES-CONCLUIDAS//{nivel}'):
            dados = orientacao.find(f'.//DADOS-BASICOS-DE-ORIENTACOES-CONCLUIDAS-PARA-{nivel}')
            if dados is not None:
                ori_dict = {
                    'TITULO': clean_value(dados.get('TITULO')),
                    'ANO': clean_value(dados.get('ANO')),
                    'TIPO': clean_value(dados.get('NATUREZA')),
                    'ORIENTANDO': clean_value(orientacao.find(f'.//DETALHAMENTO-DE-ORIENTACOES-CONCLUIDAS-PARA-{nivel}').get('NOME-DO-ORIENTANDO'))
                }
                curriculo_data[f'ORIENTACOES-{nivel}'].append(ori_dict)

    # Outras Orientações
    for orientacao in root.findall('.//OUTRAS-ORIENTACOES-CONCLUIDAS'):
        dados = orientacao.find('.//DADOS-BASICOS-DE-OUTRAS-ORIENTACOES-CONCLUIDAS')
        if dados is not None:
            ori_dict = {
                'TITULO': clean_value(dados.get('TITULO')),
                'ANO': clean_value(dados.get('ANO')),
                'NATUREZA': clean_value(dados.get('NATUREZA')),
                'ORIENTANDO': clean_value(orientacao.find('.//DETALHAMENTO-DE-OUTRAS-ORIENTACOES-CONCLUIDAS').get('NOME-DO-ORIENTANDO'))
            }
            curriculo_data['OUTRAS-ORIENTACOES'].append(ori_dict)

    # Prêmios e Títulos
    for premio in root.findall('.//PREMIO-TITULO'):
        premio_dict = {
            'TITULO': clean_value(premio.get('NOME-DO-PREMIO-OU-TITULO')),
            'ANO': clean_value(premio.get('ANO-DA-PREMIACAO')),
            'ENTIDADE': clean_value(premio.get('NOME-DA-ENTIDADE-PROMOTORA'))
        }
        curriculo_data['PREMIOS-TITULOS'].append(premio_dict)

    # Projetos de Pesquisa
    for projeto in root.findall('.//PROJETO-DE-PESQUISA'):
        proj_dict = {
            'TITULO': clean_value(projeto.get('NOME-DO-PROJETO')),
            'ANO-INICIO': clean_value(projeto.get('ANO-INICIO')),
            'ANO-FIM': clean_value(projeto.get('ANO-FIM')),
            'SITUACAO': clean_value(projeto.get('SITUACAO')),
            'NATUREZA': clean_value(projeto.get('NATUREZA'))
        }
        curriculo_data['PROJETOS-PESQUISA'].append(proj_dict)

    return {k: v for k, v in curriculo_data.items() if v}  # Remove seções vazias

def verify_data_completeness(curriculo_data):
    """Verifica a completude dos dados e gera relatório"""
    report = []
    total_items = sum(len(items) for items in curriculo_data.values())
    
    for section, items in curriculo_data.items():
        if not items:
            report.append(f"AVISO: Seção {section} está vazia")
            continue
            
        filled_fields = 0
        total_fields = 0
        
        for item in items:
            total_fields += len(item)
            filled_fields += sum(1 for v in item.values() if v and v != 'NAO_INFORMADO')
        
        completeness = (filled_fields / total_fields * 100) if total_fields > 0 else 0
        report.append(f"{section}: {len(items)} itens, {completeness:.1f}% completo")
    
    return report

def xml_to_csv(xml_file, output_dir):
    try:
        curriculo_data = extract_curriculo_data(xml_file)
        
        # Verificar completude dos dados
        report = verify_data_completeness(curriculo_data)
        print(f"\nRelatório de completude para {os.path.basename(xml_file)}:")
        for line in report:
            print(line)
        
        # Criar e salvar DataFrames
        filename = os.path.splitext(os.path.basename(xml_file))[0]
        for section, items in curriculo_data.items():
            if items:
                df = pd.DataFrame(items)
                csv_file = os.path.join(output_dir, f'{filename}_{section}.csv')
                df.to_csv(csv_file, index=False, encoding='utf-8')
                print(f'Convertido: {section} -> {os.path.basename(csv_file)}')
    
    except Exception as e:
        print(f'Erro ao converter {xml_file}: {str(e)}')

def main():
    # Cria e obtém os diretórios
    base_dir, input_dir, output_dir = create_directories()
    
    # Move os arquivos XML para a pasta de entrada
    move_xml_files(base_dir, input_dir)
    
    # Encontra todos os arquivos XML na pasta de entrada
    xml_files = glob.glob(os.path.join(input_dir, '*.xml'))
    
    if not xml_files:
        print("Nenhum arquivo XML encontrado na pasta de entrada!")
        return
    
    # Converte cada arquivo
    for xml_file in xml_files:
        try:
            xml_to_csv(xml_file, output_dir)
        except Exception as e:
            print(f'Erro ao converter {os.path.basename(xml_file)}: {str(e)}')

if __name__ == '__main__':
    main()
