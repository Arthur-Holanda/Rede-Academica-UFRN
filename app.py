
import streamlit as st
import pandas as pd
import io
import re
from collections import defaultdict
import math
from pyvis.network import Network
import streamlit.components.v1 as components
import json
import networkx as nx
import matplotlib.pyplot as plt
from matplotlib.ticker import ScalarFormatter
import community as community_louvain # <-- ADICIONE ESTA LINHA
import streamlit.components.v1 as components

# --- 1. Configuração da Página Streamlit ---
st.set_page_config(
    page_title="Rede Acadêmica",
    layout="wide",
    page_icon=":material/school:",
)
st.title("Visualização da Rede Acadêmica")

with st.expander("Clique aqui para saber mais sobre este grafo"):
    st.markdown("""
        ### Sobre os Dados
        Este grafo foi construído a partir de dados extraídos manualmente da **[Plataforma Acácia](https://plataforma-acacia.org/)**, uma iniciativa que coleta e organiza dados públicos sobre a produção científica e acadêmica no Brasil. A coleta foi focada em professores da **Universidade Federal do Rio Grande do Norte (UFRN)**, pesquisando diretamente por aqueles com lotação associada ao Instituto Metrópole Digital (IMD), ao Departamento de Engenharia de Computação e Automação (DCA) e ao Departamento de Informática e Matemática Aplicada (DIMAp).

        O principal objetivo desta visualização é promover uma análise sobre a **conectividade dos pesquisadores**, revelando as redes de orientação que formam o tecido acadêmico e científico da instituição.

        ### O que são os Nós e as Arestas?
        Nesta rede, cada elemento visual tem um significado específico:

        * **Nós:** Cada nó representa um **pesquisador**, seja ele um professor ou um aluno (orientando). A cor do nó diferencia os professores da base de dados principal dos demais pesquisadores que compõem a rede. O tamanho do nó é proporcional ao seu número total de conexões de orientação (quantas vezes orientou e foi orientado).

        * **Arestas:** Cada aresta representa uma **relação de orientação acadêmica**, conectando um orientador a um orientado. A cor da aresta indica o nível da orientação (Mestrado, Doutorado ou Pós-Doutorado), e o estilo da linha diferencia orientações principais (linha sólida) de coorientações (linha tracejada).
    """)

# --- 2. Definições Globais e Funções Auxiliares ---

# 1. Paleta de Cores (ajuste conforme a imagem de referência)
PALETTE = {
    "dark_blue_purple": "#2c2a5a",
    "medium_blue_purple": "#4A478A", # Para docentes IMD
    "light_blue_cyan": "#5DD5F0",    # Para outros pesquisadores e arestas de Mestrado
    "accent_yellow_orange": "#F7B500",# Para arestas de Doutorado e destaques
    "pós_doutorado": "#7fff00",        # Verde para Pós-Doutorado (NOVO)
    "text_white": "#FFFFFF",
    "edge_co_mestrado": "#87CEEB",     # Azul claro para co-orientação mestrado
    "edge_co_doutorado": "#FFD700",   # Amarelo mais claro para co-orientação doutorado
    "edge_co_pos_doutorado": "#ADFF2F", # Verde amarelado para co-orientação pós-doutorado (NOVO)
    "edge_unified_color": "#FFFFFF"
}


# Regex para extrair nome antes do parêntese
name_regex = re.compile(r"(.+?)\s*\(")

# Tamanho base e máximo para os nós do grafo
BASE_NODE_SIZE = 8
MAX_NODE_SIZE = 100  


def get_orientation_details_from_string(details_str_original_case, entry_str_lower_for_co_check):
    parsed_orientations = []
    if not details_str_original_case:
        return parsed_orientations

    details_str_lower = details_str_original_case.lower()

    # Determina se é coorientação para esta entrada específica
    is_co_global = entry_str_lower_for_co_check.endswith(" co)") or \
                   details_str_lower.startswith("coorientador") or \
                   details_str_lower.startswith("co-orientador") or \
                   ("coorientador" in details_str_lower.split(',')[0])

    # Usamos IFs independentes (não elif) para garantir a leitura de graus compostos
    pos_doc_info = re.search(r"(?:pós-doutorado|pos-doutorado|pós doc)\s*(?:,\s*)?(\d{4})?", details_str_lower)
    if pos_doc_info:
        year_pd = pos_doc_info.group(1) if pos_doc_info.group(1) else "N/A"
        parsed_orientations.append({'type': "Pós-Doutorado", 'year': year_pd, 'co': is_co_global})

    doutorado_info = re.search(r"doutorado\s*(?:,\s*)?(\d{4})?", details_str_lower)
    if doutorado_info:
        year_d = doutorado_info.group(1) if doutorado_info.group(1) else "N/A"
        parsed_orientations.append({'type': "Doutorado", 'year': year_d, 'co': is_co_global})

    mestrado_info = re.search(r"mestrado\s*(?:,\s*)?(\d{4})?", details_str_lower)
    if mestrado_info:
        year_m = mestrado_info.group(1) if mestrado_info.group(1) else "N/A"
        parsed_orientations.append({'type': "Mestrado", 'year': year_m, 'co': is_co_global})

    # Fallback caso o padrão principal não seja encontrado
    if not parsed_orientations:
        degree_type_fallback = None
        year_fallback = "N/A"
        year_match_fallback = re.search(r"(\d{4})", details_str_lower)
        if year_match_fallback:
            year_fallback = year_match_fallback.group(1)

        if "pós-doutorado" in details_str_lower or "pos-doutorado" in details_str_lower or "pós doc" in details_str_lower:
            degree_type_fallback = "Pós-Doutorado"
        elif "doutorado" in details_str_lower:
            degree_type_fallback = "Doutorado"
        elif "mestrado" in details_str_lower:
            degree_type_fallback = "Mestrado"

        if degree_type_fallback:
             parsed_orientations.append({'type': degree_type_fallback, 'year': year_fallback, 'co': is_co_global})

    return parsed_orientations

# --- 3. Processamento de Dados ---
def default_node_factory():
    return {'Formacao': 'N/A', 'Campus': 'N/A', 'Lotacao': 'N/A', 'Mestrado_Orientador': [], 'Doutorado_Orientador': [], 'Pos_Doutorado_Supervisor': []}

# Removido o @st.cache_data temporariamente para debugar e garantir que os dados não se percam
def processar_dados_da_rede():
    df = pd.read_csv("dados_acacia.csv")

    all_nodes = set()
    imd_docentes = set()
    detailed_edges = []
    node_details = defaultdict(default_node_factory)

    for index, row in df.iterrows():
        current_person = row['NOME_PRINCIPAL'].strip()
        all_nodes.add(current_person)
        imd_docentes.add(current_person)

        node_details[current_person]['Formacao'] = row['FORMACAO_PRINCIPAL']
        node_details[current_person]['Campus'] = row['CAMPUS_PRINCIPAL']
        node_details[current_person]['Lotacao'] = row['LOTACAO']

        # Processar DESCENDENTES (ORIENTANDOS_ACADEMICOS)
        advisees_str = row['ORIENTANDOS_ACADEMICOS']
        if pd.notna(advisees_str) and isinstance(advisees_str, str):
            individual_advisee_entries = advisees_str.split(';')
            for entry in individual_advisee_entries:
                entry = entry.strip()
                if not entry: continue

                name_match = name_regex.match(entry)
                if name_match:
                    advisee_name = name_match.group(1).strip()
                    details_text = ""
                    details_match_re = re.search(r"\((.*)\)", entry)
                    if details_match_re:
                        details_text = details_match_re.group(1)

                    orientation_list = get_orientation_details_from_string(details_text, entry.lower())

                    for or_details in orientation_list:
                        degree_type = or_details['type']
                        year = or_details['year']
                        is_co_role = or_details['co']

                        if advisee_name and degree_type:
                            all_nodes.add(advisee_name)
                            detailed_edges.append({
                                'source': current_person, 'target': advisee_name,
                                'type': degree_type, 'co': is_co_role, 'year': year
                            })
                            # --- GARANTIA DE INSERÇÃO NA LISTA ---
                            if degree_type == "Mestrado":
                                node_details[advisee_name]['Mestrado_Orientador'].append(f"{year} por {current_person}{' (Co)' if is_co_role else ''}")
                            elif degree_type == "Doutorado":
                                node_details[advisee_name]['Doutorado_Orientador'].append(f"{year} por {current_person}{' (Co)' if is_co_role else ''}")
                            elif degree_type == "Pós-Doutorado":
                                node_details[advisee_name]['Pos_Doutorado_Supervisor'].append(f"{year} por {current_person}{' (Co)' if is_co_role else ''}")

        # Processar ASCENDENTES (ORIENTADORES_ACADEMICOS)
        academic_advisors_str = row['ORIENTADORES_ACADEMICOS']
        if pd.notna(academic_advisors_str) and isinstance(academic_advisors_str, str):
            individual_academic_advisor_entries = academic_advisors_str.split(';')
            for entry in individual_academic_advisor_entries:
                entry = entry.strip()
                if not entry: continue

                name_part_match = name_regex.match(entry)
                if not name_part_match: continue

                names_str = name_part_match.group(1).strip()
                details_text_asc = ""
                details_match_re_asc = re.search(r"\((.*)\)", entry)
                if details_match_re_asc:
                    details_text_asc = details_match_re_asc.group(1)

                orientation_list_asc = get_orientation_details_from_string(details_text_asc, entry.lower())
                actual_advisor_names = [name.strip() for name in names_str.split(" E ") if name.strip()]

                for advisor_name in actual_advisor_names:
                    for or_details in orientation_list_asc:
                        degree_type = or_details['type']
                        year = or_details['year']
                        is_co_role = or_details['co']

                        if advisor_name and degree_type:
                            all_nodes.add(advisor_name)
                            detailed_edges.append({
                                'source': advisor_name, 'target': current_person,
                                'type': degree_type, 'co': is_co_role, 'year': year
                            })
                            # --- GARANTIA DE INSERÇÃO NA LISTA ---
                            if degree_type == "Mestrado":
                                node_details[current_person]['Mestrado_Orientador'].append(f"{year} por {advisor_name}{' (Co)' if is_co_role else ''}")
                            elif degree_type == "Doutorado":
                                node_details[current_person]['Doutorado_Orientador'].append(f"{year} por {advisor_name}{' (Co)' if is_co_role else ''}")
                            elif degree_type == "Pós-Doutorado":
                                node_details[current_person]['Pos_Doutorado_Supervisor'].append(f"{year} por {advisor_name}{' (Co)' if is_co_role else ''}")

    unique_edges_tracker = set()
    final_detailed_edges = []
    for edge in detailed_edges:
        edge_tuple = (edge['source'], edge['target'], edge['type'], edge['co'], edge['year'])
        if edge_tuple not in unique_edges_tracker:
            unique_edges_tracker.add(edge_tuple)
            final_detailed_edges.append(edge)
    detailed_edges = final_detailed_edges

    out_degree_total = defaultdict(int)
    in_degree_total = defaultdict(int)
    for edge in detailed_edges:
        out_degree_total[edge['source']] += 1
        in_degree_total[edge['target']] += 1

    return all_nodes, imd_docentes, detailed_edges, node_details, out_degree_total, in_degree_total

all_nodes, imd_docentes, detailed_edges, node_details, out_degree_total, in_degree_total = processar_dados_da_rede()

# --- 4. Preparação de Dados para o D3.js ---
d3_nodes = []
d3_links = []
docent_advisors = set()

# Identificar orientadores de docentes
for edge in detailed_edges:
    if edge['target'] in imd_docentes:
        docent_advisors.add(edge['source'])

# 1. Montar JSON dos Nós
for node_name in all_nodes:
    is_docente = node_name in imd_docentes
    is_docent_advisor = node_name in docent_advisors
    node_color = PALETTE['medium_blue_purple'] if (is_docente or is_docent_advisor) else PALETTE['light_blue_cyan']
    
    total_degree = out_degree_total.get(node_name, 0) + in_degree_total.get(node_name, 0)
    node_size = min(BASE_NODE_SIZE + (total_degree ** 1.2) * 0.5, MAX_NODE_SIZE)

    # --- Construção do Tooltip Completo (Corrigido) ---
    title_text = f"<div style='margin-bottom: 5px; border-bottom: 1px solid rgba(255,255,255,0.2); padding-bottom: 5px; font-size: 14px;'><strong>{node_name}</strong></div>"
    
    if node_details[node_name]['Formacao'] != 'N/A':
        title_text += f"Formação: {node_details[node_name]['Formacao']}<br>"
    if node_details[node_name]['Campus'] != 'N/A':
        title_text += f"Campus: {node_details[node_name]['Campus']}<br>"
    if node_details[node_name]['Lotacao'] != 'N/A':
        title_text += f"Lotação: {node_details[node_name]['Lotacao']}<br>"
        
    if node_details[node_name]['Mestrado_Orientador']:
        mestres = list(set(node_details[node_name]['Mestrado_Orientador']))
        title_text += "Mestrado: " + " e ".join(mestres) + "<br>"
        
    if node_details[node_name]['Doutorado_Orientador']:
        doutores = list(set(node_details[node_name]['Doutorado_Orientador']))
        title_text += "Doutorado: " + " e ".join(doutores) + "<br>"
        
    if node_details[node_name]['Pos_Doutorado_Supervisor']:
        pos_docs = list(set(node_details[node_name]['Pos_Doutorado_Supervisor']))
        title_text += "Pós-Doutorado: " + " e ".join(pos_docs) + "<br>"
        
    if (out_degree_total[node_name] != 0) or (in_degree_total[node_name] != 0):
        title_text += "<br>"
    if (out_degree_total[node_name] != 0):
        title_text += f"Orientou {out_degree_total[node_name]} vez(es)<br>"
    if (in_degree_total[node_name] != 0):
        title_text += f"Foi Orientado {in_degree_total[node_name]} vez(es)"

    d3_nodes.append({
        "id": node_name, "color": node_color, "size": node_size, "title": title_text
    })


# ==== ADICIONE ISTO AQUI PARA DEPURAR ====
st.write("RAIO-X DO PRIMEIRO NÓ:", d3_nodes[0])
# ========================================

for edge in detailed_edges:
    edge_color = ""
    width = 1.5
    dashed = "0"
    
    if edge['type'] == 'Doutorado':
        edge_color = PALETTE['accent_yellow_orange']
        if edge['co']: dashed = "5,5"; edge_color = PALETTE['edge_co_doutorado']; width = 1
    elif edge['type'] == 'Mestrado':
        edge_color = PALETTE['light_blue_cyan']
        if edge['co']: dashed = "5,5"; edge_color = PALETTE['edge_co_mestrado']; width = 1
    elif edge['type'] == 'Pós-Doutorado':
        edge_color = PALETTE['pós_doutorado']
        if edge['co']: dashed = "5,5"; edge_color = PALETTE['edge_co_pos_doutorado']; width = 1

    if edge_color:
        d3_links.append({
            "source": edge['source'], "target": edge['target'], 
            "color": edge_color, "width": width, "dashed": dashed
        })

graph_data_json = json.dumps({"nodes": d3_nodes, "links": d3_links})

# --- 5. Renderização com D3.js ---
# --- 5. Renderização com D3.js ---
html_d3 = f"""
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="utf-8">
    <script src="https://d3js.org/d3.v7.min.js"></script>
    <style>
        body {{ margin: 0; background-color: #222222; overflow: hidden; font-family: sans-serif; }}
        svg {{ width: 100vw; height: 100vh; display: block; cursor: grab; }}
        svg:active {{ cursor: grabbing; }}
        
        /* Interface de Busca e Legenda flutuante */
        #ui-container {{
            position: absolute; top: 15px; right: 15px;
            background-color: rgba(0, 0, 0, 0.2); 
            backdrop-filter: blur(4px);
            border: 1px solid rgba(255, 255, 255, 0.1);
            padding: 15px; border-radius: 8px; color: white;
            width: 250px; z-index: 10;
            transition: all 0.3s ease;
        }}
        #ui-container.minimized {{
            background-color: transparent; border-color: transparent;
            backdrop-filter: none; padding: 10px;
        }}
        #ui-header {{
            cursor: pointer; display: flex; justify-content: space-between; align-items: center; user-select: none;
        }}
        #ui-header h4 {{ margin: 0; font-size: 15px; }}
        #ui-body {{ display: block; margin-top: 15px; transition: opacity 0.3s; }}
        
        .search-box {{ width: 100%; padding: 8px; margin-bottom: 10px; border-radius: 4px; border: none; box-sizing: border-box; background: rgba(255, 255, 255, 0.9); }}
        .btn {{ width: 100%; padding: 8px; margin-bottom: 5px; border-radius: 4px; border: none; cursor: pointer; font-weight: bold; transition: 0.2s; }}
        .btn-search {{ background-color: #5DD5F0; color: #222; }}
        .btn-search:hover {{ background-color: #3cb8d3; }}
        .btn-reset {{ background-color: rgba(255, 255, 255, 0.15); color: white; }}
        .btn-reset:hover {{ background-color: rgba(255, 255, 255, 0.3); }}
        
        .legend-item {{ display: flex; align-items: center; margin-bottom: 8px; font-size: 12px; }}
        .color-box {{ width: 14px; height: 14px; border-radius: 50%; margin-right: 10px; border: 1px solid rgba(255, 255, 255, 0.3); }}
        .line-box {{ width: 20px; height: 3px; margin-right: 10px; }}

        #tooltip {{
            position: absolute; background-color: rgba(15, 15, 25, 0.95); color: #fff;
            padding: 10px 15px; border-radius: 6px; pointer-events: none;
            font-size: 13px; line-height: 1.4; border: 1px solid #5DD5F0;
            box-shadow: 0 4px 10px rgba(0,0,0,0.5); opacity: 0; transition: opacity 0.2s; z-index: 20;
        }}
    </style>
</head>
<body>
    <div id="tooltip"></div>

    <div id="ui-container">
        <div id="ui-header">
            <h4>Menu e Legenda</h4>
            <span id="ui-arrow">▼</span>
        </div>
        <div id="ui-body">
            <input type="text" id="search-input" class="search-box" placeholder="Digite o nome...">
            <button id="search-btn" class="btn btn-search">Buscar</button>
            <button id="reset-btn" class="btn btn-reset">Limpar Vista</button>
            <hr style="border-color: rgba(255,255,255,0.1); margin: 15px 0;">
            <h4 style="margin: 0 0 10px 0; font-size: 14px;">Legenda</h4>
            <div class="legend-item"><div class="color-box" style="background-color: {PALETTE['medium_blue_purple']};"></div>Professor IMD / Orientador</div>
            <div class="legend-item"><div class="color-box" style="background-color: {PALETTE['light_blue_cyan']};"></div>Outro Pesquisador</div>
            <div style="margin: 15px 0;"></div>
            <div class="legend-item"><div class="line-box" style="background-color: {PALETTE['light_blue_cyan']};"></div>Mestrado</div>
            <div class="legend-item"><div class="line-box" style="background-color: {PALETTE['accent_yellow_orange']};"></div>Doutorado</div>
            <div class="legend-item"><div class="line-box" style="background-color: {PALETTE['pós_doutorado']};"></div>Pós-Doutorado</div>
            <div class="legend-item"><div class="line-box" style="background: none; border-top: 2px dashed #FFF; height: 0;"></div>Coorientação</div>
        </div>
    </div>

    <svg id="network-graph"></svg>
    
    <script>
        const graphData = {graph_data_json};
        const width = window.innerWidth;
        const height = window.innerHeight;

        const svg = d3.select("#network-graph");
        const g = svg.append("g");

        const zoom = d3.zoom().scaleExtent([0.1, 4]).on("zoom", (event) => {{
            g.attr("transform", event.transform);
        }});
        svg.call(zoom);

        // ==========================================
        // CRIAR MARCADORES (SETAS)
        // ==========================================
        const defs = svg.append("defs");
        const uniqueColors = [...new Set(graphData.links.map(d => d.color))];
        
        defs.selectAll("marker")
            .data(uniqueColors)
            .enter().append("marker")
            .attr("id", d => `arrow-${{d.replace('#', '')}}`)
            .attr("viewBox", "0 -5 10 10")
            .attr("refX", 0) 
            .attr("refY", 0)
            .attr("markerWidth", 6)
            .attr("markerHeight", 6)
            .attr("orient", "auto")
            .append("path")
            .attr("d", "M0,-5L10,0L0,5")
            .attr("fill", d => d);

        // ==========================================
        // FÍSICA E DESENHO
        // ==========================================
        const simulation = d3.forceSimulation(graphData.nodes)
            .force("link", d3.forceLink(graphData.links).id(d => d.id).distance(70))
            .force("charge", d3.forceManyBody().strength(-150))
            .force("center", d3.forceCenter(width / 2, height / 2))
            .force("collision", d3.forceCollide().radius(d => d.size + 4));

        const link = g.append("g")
            .attr("stroke-opacity", 0.6)
            .selectAll("line")
            .data(graphData.links)
            .join("line")
            .attr("stroke", d => d.color)
            .attr("stroke-width", d => d.width)
            .attr("stroke-dasharray", d => d.dashed === "0" ? null : d.dashed)
            .attr("marker-end", d => `url(#arrow-${{d.color.replace('#', '')}})`);

        const node = g.append("g")
            .selectAll("circle")
            .data(graphData.nodes)
            .join("circle")
            .attr("r", d => d.size)
            .attr("fill", d => d.color)
            .attr("stroke", "#222222")
            .attr("stroke-width", 1.5)
            .call(drag(simulation));

        const tooltip = d3.select("#tooltip");

        node.on("mouseover", function(event, d) {{
            tooltip.transition().duration(200).style("opacity", 1);
            tooltip.html(d.title);
            d3.select(this).attr("stroke", "#FFF").attr("stroke-width", 3);
        }})
        .on("mousemove", function(event) {{
            tooltip.style("left", (event.pageX + 15) + "px")
                   .style("top", (event.pageY - 15) + "px");
        }})
        .on("mouseout", function(event, d) {{
            tooltip.transition().duration(500).style("opacity", 0);
            d3.select(this).attr("stroke", "#222222").attr("stroke-width", 1.5);
        }});
        

        // Lógica matemática para as setas pararem na borda
        simulation.on("tick", () => {{
            link
                .attr("x1", d => d.source.x)
                .attr("y1", d => d.source.y)
                .attr("x2", d => {{
                    const dx = d.target.x - d.source.x;
                    const dy = d.target.y - d.source.y;
                    const dist = Math.sqrt(dx * dx + dy * dy);
                    if (dist === 0) return d.target.x;
                    const padding = d.target.size + 8; // Raio do nó + compensação da seta
                    return d.target.x - (dx * padding) / dist;
                }})
                .attr("y2", d => {{
                    const dx = d.target.x - d.source.x;
                    const dy = d.target.y - d.source.y;
                    const dist = Math.sqrt(dx * dx + dy * dy);
                    if (dist === 0) return d.target.y;
                    const padding = d.target.size + 8; // Raio do nó + compensação da seta
                    return d.target.y - (dy * padding) / dist;
                }});

            node.attr("cx", d => d.x).attr("cy", d => d.y);
        }});

        function drag(simulation) {{
            function dragstarted(event) {{
                if (!event.active) simulation.alphaTarget(0.3).restart();
                event.subject.fx = event.subject.x;
                event.subject.fy = event.subject.y;
            }}
            function dragged(event) {{
                event.subject.fx = event.x;
                event.subject.fy = event.y;
            }}
            function dragended(event) {{
                if (!event.active) simulation.alphaTarget(0);
                event.subject.fx = null;
                event.subject.fy = null;
            }}
            return d3.drag().on("start", dragstarted).on("drag", dragged).on("end", dragended);
        }}

function searchNode() {{
            const term = document.getElementById('search-input').value.toLowerCase().trim();
            if (!term) {{ resetView(); return; }}

            const matchedNodes = graphData.nodes.filter(n => n.id.toLowerCase().includes(term));
            if (matchedNodes.length === 0) {{ alert('Nenhum pesquisador encontrado com esse nome.'); resetView(); return; }}

            // 1. Identifica os IDs de quem foi buscado
            const matchedIds = new Set(matchedNodes.map(n => n.id));

            // 2. Mapeia os vizinhos (conexões diretas) e as linhas que os unem
            const neighborIds = new Set();
            const connectedLinks = new Set();

            graphData.links.forEach(l => {{
                // No D3, após a simulação iniciar, source e target viram objetos
                if (matchedIds.has(l.source.id)) {{
                    neighborIds.add(l.target.id);
                    connectedLinks.add(l);
                }} else if (matchedIds.has(l.target.id)) {{
                    neighborIds.add(l.source.id);
                    connectedLinks.add(l);
                }}
            }});

            // 3. Destaca o pesquisador e seus vizinhos, esmaecendo o resto
            node.transition().duration(500)
                .attr("opacity", d => (matchedIds.has(d.id) || neighborIds.has(d.id)) ? 1 : 0.05)
                .attr("stroke", d => matchedIds.has(d.id) ? "#FFF" : "#222222")
                .attr("stroke-width", d => matchedIds.has(d.id) ? 3 : 1.5);
            
            // 4. Esconde as linhas distantes e suas setas alterando a "opacity" geral para zero
            link.transition().duration(500)
                .attr("opacity", d => connectedLinks.has(d) ? 1 : 0.0) 
                .attr("stroke-opacity", d => connectedLinks.has(d) ? 0.8 : 0.0);

            // 5. Move a câmera para o primeiro resultado
            const target = matchedNodes[0];
            const transform = d3.zoomIdentity.translate(width / 2, height / 2).scale(2).translate(-target.x, -target.y);
            svg.transition().duration(1200).call(zoom.transform, transform);
        }}

        function resetView() {{
            document.getElementById('search-input').value = '';
            
            node.transition().duration(500)
                .attr("opacity", 1)
                .attr("stroke", "#222222")
                .attr("stroke-width", 1.5);
                
            link.transition().duration(500)
                .attr("opacity", 1)          // Traz as setas de volta
                .attr("stroke-opacity", 0.6); // Retorna a transparência original da linha
                
            svg.transition().duration(1000).call(zoom.transform, d3.zoomIdentity);
        }}

        document.getElementById('search-btn').addEventListener('click', searchNode);
        document.getElementById('reset-btn').addEventListener('click', resetView);
        document.getElementById('search-input').addEventListener('keypress', function(e) {{
            if (e.key === 'Enter') searchNode();
        }});

        document.getElementById('ui-header').addEventListener('click', function() {{
            const body = document.getElementById('ui-body');
            const arrow = document.getElementById('ui-arrow');
            const container = document.getElementById('ui-container');
            
            if (body.style.display === 'none') {{
                body.style.display = 'block'; arrow.textContent = '▼'; container.classList.remove('minimized');
            }} else {{
                body.style.display = 'none'; arrow.textContent = '▶'; container.classList.add('minimized');
            }}
        }});
    </script>
</body>
</html>
"""

components.html(html_d3, height=800, scrolling=False)

# --- 6. Seção de Análise da Rede (com Layout de Colunas) ---

st.header("Análise da Rede", divider='rainbow')

# --- Preparação do Grafo para Análise com NetworkX ---
G = nx.Graph()
G.add_nodes_from(all_nodes)
edges_for_nx = [(edge['source'], edge['target']) for edge in detailed_edges]
G.add_edges_from(edges_for_nx)


# --- Layout de Duas Colunas para Análise Introdutória ---
# A coluna da esquerda terá 2 partes de largura, e a da direita 3 partes.
left_col, right_col = st.columns([2, 2], gap="large")


# --- Coluna da Esquerda: Textos e Explicações ---
with left_col:
    st.markdown("""
    A seguir, apresentamos algumas métricas fundamentais de análise de redes sociais (SNA) aplicadas ao nosso
    conjunto de dados. Essas métricas nos ajudam a compreender a estrutura, a coesão e a forma
    da rede de pesquisadores.
    """)

    # Verifica se o grafo é conectado e exibe a mensagem apropriada
    if nx.is_connected(G):
        st.info("A rede de pesquisadores é **conectada**, o que significa que é possível chegar de qualquer pesquisador a qualquer outro. As análises a seguir são baseadas no grafo completo.")
        graph_for_analysis = G
    else:
        st.warning("""
        A rede de pesquisadores **não é totalmente conectada**. Isso significa que existem "ilhas" ou
        grupos de pesquisadores isolados uns dos outros.
        """)

        # Encontra o maior componente conectado
        largest_cc_nodes = max(nx.connected_components(G), key=len)
        graph_for_analysis = G.subgraph(largest_cc_nodes).copy()

        st.info(f"O maior componente (Fracamente) conectado possui **{graph_for_analysis.number_of_nodes()} pesquisadores** (de um total de {G.number_of_nodes()}). Para calcular métricas como o diâmetro, a análise será realizada neste componente.")
        st.markdown("""
        A rede é majoritariamente coesa, com um componente principal gigante de 1199 pesquisadores.
        """)

        # --- Análise 2: Diâmetro e Periferia ---
        st.subheader("Diâmetro e Periferia da Rede")
        st.markdown("""
        O **diâmetro** de uma rede é a maior "distância" (menor número de laços) entre quaisquer dois pesquisadores. A **periferia** é o conjunto de pesquisadores que se encontram nas "pontas" desses caminhos mais longos.

        O diâmetro da rede de **18** é um valor consideravelmente alto, mesmo para uma rede de quase 1200 membros. Isso indica que a estrutura do componente principal, apesar de conectada, é **"longa" e "esguia"**.

        Na prática, isso significa que existem pesquisadores nas extremidades da rede que estão separados por uma longa cadeia de até **17 intermediários**. A disseminação de informações e a influência acadêmica entre esses pontos mais distantes podem ser lentas. Diferente de uma rede "mundo pequeno" (onde todos estão próximos), esta estrutura sugere a existência de longas "linhagens" de orientação ou "pontes" que conectam subgrupos temáticos que, de outra forma, estariam muito distantes.
        """)
        # Substitua pelo código abaixo:
        try:
            # Os cálculos continuam os mesmos
            diameter = nx.diameter(graph_for_analysis)
            periphery = nx.periphery(graph_for_analysis)

            # --- Layout em colunas para o Diâmetro e o Caminho de Exemplo ---
            col1, col2 = st.columns([1, 4], gap="large")

            # Coluna da esquerda para a métrica do diâmetro
            with col1:
                st.metric(label="Diâmetro", value=diameter,
                          help="A maior distância mínima entre quaisquer dois nós no maior componente conectado.")


            # Adiciona um espaço para melhor separação visual
            #st.write("")

            # --- Exibição da Periferia (agora abaixo das colunas, em largura total) ---
            with st.expander(f"Ver os {len(periphery)} Pesquisadores na Periferia da Rede"):
                st.write(", ".join(periphery))

        except Exception as e:
            st.error(f"Não foi possível calcular o diâmetro e a periferia. Motivo: {e}")



# --- Coluna da Direita: Visualização do Grafo ---
with right_col:
    # A visualização do subgrafo só aparece se a rede não for conectada
    if not nx.is_connected(G):
        # Filtra as arestas para incluir apenas aquelas do maior componente
        edges_subgraph = [
            edge for edge in detailed_edges
            if edge['source'] in largest_cc_nodes and edge['target'] in largest_cc_nodes
        ]

        # Cria uma nova instância do Pyvis para o subgrafo
        net_subgraph = Network(notebook=True, height="550px", width="100%", cdn_resources='remote', directed=True,
                               bgcolor="#222222", font_color="white")

        # Adiciona os nós e arestas do subgrafo (lógica reutilizada)
        for node_name in largest_cc_nodes:
            is_docente = node_name in imd_docentes
            is_docent_advisor = any(edge['source'] == node_name and edge['target'] in imd_docentes for edge in edges_subgraph)
            if is_docente or is_docent_advisor: node_color = "#4A478A"
            else: node_color = "#5DD5F0"
            total_degree = out_degree_total.get(node_name, 0) + in_degree_total.get(node_name, 0)
            node_size = BASE_NODE_SIZE + (total_degree ** 1.2) * 0.5
            node_size = min(node_size, MAX_NODE_SIZE)
            title_text = f"{node_name}"+ "\n" + f"Formação: {node_details[node_name]['Formacao']}"
            net_subgraph.add_node(node_name, label=node_name, color=node_color, size=node_size, title=title_text, font={'size': 12, 'color': PALETTE['text_white'] })

        for edge in edges_subgraph:
            edge_color = ""
            dashes = False
            width = 1.5
            if edge['type'] == 'Doutorado':
                edge_color = PALETTE['accent_yellow_orange']
                if edge['co']: dashes = True; edge_color = PALETTE['edge_co_doutorado']; width = 1
            elif edge['type'] == 'Mestrado':
                edge_color = PALETTE['light_blue_cyan']
                if edge['co']: dashes = True; edge_color = PALETTE['edge_co_mestrado']; width = 1
            elif edge['type'] == 'Pós-Doutorado':
                edge_color = PALETTE['pós_doutorado']
                if edge['co']: dashes = True; edge_color = PALETTE['edge_co_pos_doutorado']; width = 1
            edge_title = f"{edge['source']} -> {edge['target']}\\n{edge['type']} ({edge['year']}){' [Coorientação]' if edge['co'] else ''}"
            if edge_color: net_subgraph.add_edge(edge['source'], edge['target'], color=edge_color, dashes=dashes, title=edge_title, width=width)

        net_subgraph.set_options(options_str)
        try:
            subgraph_file_path = "subgraph_network.html"
            net_subgraph.save_graph(subgraph_file_path)
            with open(subgraph_file_path, 'r', encoding='utf-8') as f:
                html_content_subgraph = f.read()
            st.components.v1.html(html_content_subgraph, height=560, scrolling=True)
        except Exception as e:
            st.error(f"Ocorreu um erro ao gerar o grafo do subcomponente: {e}")


# --- Continuação da Análise (agora em largura total, abaixo das colunas) ---
st.divider() # Adiciona uma linha divisória

# --- Análise 1: Matriz de Adjacência ---
st.subheader("Matriz de Adjacência")
st.markdown("""
A matriz de adjacência é uma representação matemática da rede em formato de tabela. Nela, tanto as linhas quanto as colunas são os pesquisadores (nós). Uma célula na `linha X` e `coluna Y` terá o valor `1` se houver uma relação de orientação direta entre o pesquisador `X` e o pesquisador `Y`, e `0` caso contrário.
""")
with st.expander("Visualizar a Matriz de Adjacência"):
    adjacency_df = nx.to_pandas_adjacency(G)
    # Pega a lista de nomes (que são o índice do DataFrame) e a ordena alfabeticamente
    sorted_index = sorted(adjacency_df.index)

    # Reordena as linhas e as colunas do DataFrame para seguir a nova ordem alfabética
    sorted_adjacency_df = adjacency_df.reindex(index=sorted_index, columns=sorted_index)

    # Exibe o DataFrame ORDENADO
    st.dataframe(sorted_adjacency_df)
    st.caption(f"A matriz completa (ordenada alfabeticamente) possui dimensões de {sorted_adjacency_df.shape[0]}x{sorted_adjacency_df.shape[1]}.")

st.divider()

# --- Análise de Distribuição de Grau (Layout Final) ---
st.subheader("Histograma de Distribuição de Grau", divider="gray")
st.markdown("""
Este histograma nos mostra como as conexões estão distribuídas pela rede. O eixo X representa o **Grau** (o número de conexões que um pesquisador possui), e o eixo Y representa o **Número de Pesquisadores** que têm aquele grau exato.

Em muitas redes do mundo real, incluindo redes acadêmicas, esperamos ver um padrão onde muitos pesquisadores têm pouquíssimas conexões e um número muito pequeno de pesquisadores têm uma quantidade massiva de conexões.
""")

# O expander agora envolve apenas o gráfico e sua interpretação.
with st.expander("Visualizar o Histograma de Distribuição de Grau"):
    # Calcula os graus de todos os nós no grafo completo G
    degrees = [G.degree(n) for n in G.nodes()]
    degree_counts = pd.Series(degrees).value_counts().sort_index()

    # --- Criação do Gráfico com Matplotlib (escala linear) ---
    try:
        fig, ax = plt.subplots(figsize=(10, 6))
        ax.bar(degree_counts.index, degree_counts.values, color='#4A478A')

        ax.set_title('Distribuição de Grau da Rede (Escala Logarítmica)', fontsize=16)
        ax.set_xlabel('Grau (Número de Conexões)', fontsize=12)
        ax.set_ylabel('Número de Pesquisadores (em escala log)', fontsize=12)

        # Define a escala logarítmica para o eixo Y
        ax.set_yscale('log')

        # Formata o eixo Y para usar números normais em vez de notação científica (100 em vez de 10^2)
        ax.yaxis.set_major_formatter(ScalarFormatter())

        ax.grid(axis='y', linestyle='--', alpha=0.7)

        st.pyplot(fig)

        st.markdown("""
        #### Interpretação do Gráfico
        Com mais de 1400 pesquisadores no dataset, o padrão de **"cauda longa"** se torna ainda mais extremo e evidente, sendo a assinatura de uma rede de escala livre (*scale-free network*) madura.

        * **A "Cabeça" da Distribuição:** A "cabeça" da distribuição, na extrema esquerda, agora representa uma contagem massiva, na casa de **muitas centenas**, de indivíduos com grau 1 ou 2. Estes formam a vasta base da pirâmide acadêmica, composta majoritariamente por alunos e pesquisadores em início de carreira.

        * **A "Cauda Longa":** Em contrapartida, a "cauda longa" que se estende para a direita se torna ainda mais esparsa. Ela revela que a responsabilidade de conectar a rede recai sobre um grupo muito seleto de indivíduos.

        * **Os "Mega-Hubs":** Os poucos pontos isolados no extremo direito do gráfico são os pilares da rede. São professores com um número de orientações ordens de magnitude maior que a média, que não apenas produzem muitos pesquisadores, mas também servem como as "pontes" que garantem a coesão desta enorme comunidade de quase 1200 membros.
        """)

    except Exception as e:
        st.error(f"Ocorreu um erro ao gerar o histograma de grau: {e}")

st.divider()

# --- Análise Adicional: Densidade e Assortatividade ---
st.subheader("Densidade e Assortatividade", divider="gray")

col1, col2 = st.columns(2, gap="large")

# --- Coluna da Esquerda: Densidade ---
with col1:
    density = nx.density(G)
    st.metric(
        label="Densidade da Rede",
        value=f"{density:.4%}",
        help="A proporção de conexões existentes em relação a todas as conexões possíveis na rede."
    )
    st.markdown("""
    A **densidade** mede quão "preenchida" a rede é. Com o aumento para mais de 1400 pesquisadores, a densidade da rede se torna ainda mais próxima de zero.

    Isso reforça a conclusão de que a rede é **extremamente esparsa**. As relações acadêmicas são altamente seletivas, e a estrutura geral é formada por um número relativamente pequeno de conexões significativas, e não por interações densas.
    """)

# --- Coluna da Direita: Assortatividade ---
with col2:
    try:
        assortativity = nx.degree_assortativity_coefficient(graph_for_analysis)
        st.metric(
            label="Coeficiente de Assortatividade",
            value=f"{assortativity:.4f}",
            help="Mede a tendência de nós se conectarem a outros nós de grau semelhante. Varia de -1 a 1."
        )
        st.markdown("""
        A **assortatividade** responde à pergunta: "Nós com muitas conexões se ligam a outros com muitas conexões?".

        O coeficiente de **-0.6343** é um valor **extremamente negativo**, oferecendo uma prova matemática contundente da estrutura hierárquica da rede. Esta é a assinatura inequívoca de uma rede de mentoria, onde:
        - **Professores** (hubs de altíssimo grau) se conectam quase que exclusivamente a **alunos** (nós de grau 1).

        Essa forte característica disassortativa é o motor da transferência de conhecimento na academia.
        """)
    except Exception as e:
        st.error(f"Não foi possível calcular a assortatividade. Motivo: {e}")
# --- Nova Seção: Força e Resiliência ---
st.subheader("Força e Resiliência da Rede", divider="gray")
st.markdown("""
As métricas que analisamos revelam uma rede com características estruturais muito claras, que definem tanto sua **Força** quanto sua **Resiliência**.

#### A Força de uma Rede Coesa e Estruturada
A **Força** de uma rede acadêmica como esta pode ser entendida como sua **coesão estrutural e sua capacidade de funcionar eficientemente**. Várias de nossas descobertas apontam para uma rede forte:

1.  **Coesão Massiva:** O fato de que **~85% de todos os pesquisadores formam um único e gigantesco componente conectado** é o principal indicador de força. A comunidade não é fragmentada, mas sim um ecossistema de pesquisa unificado.
2.  **Estrutura de Hubs:** A presença de "mega-hubs" (professores com altíssimo grau) cria uma **"espinha dorsal"** que organiza a rede e permite seu crescimento de forma escalável, garantindo que novos membros possam se conectar a este núcleo central.

#### O Paradoxo da Resiliência
Essa mesma estrutura de hubs que confere força à rede também define sua **Resiliência**, que é sua capacidade de resistir a falhas. A resiliência, no entanto, é um paradoxo:

* **Robustez a Falhas Aleatórias:** A rede é **extremamente robusta** contra a remoção aleatória de pesquisadores. Se um nó aleatório (provavelmente um aluno) for removido, o impacto na estrutura geral é quase nulo.

* **Vulnerabilidade a Ataques Direcionados:** Por outro lado, a rede é **altamente vulnerável** a ataques direcionados aos seus hubs. A remoção de um dos professores mais centrais teria um efeito catastrófico, quebrando o componente principal e isolando dezenas de pesquisadores.

Esses "mega-hubs" são, portanto, a fonte da força e coesão da rede, mas também representam seu "calcanhar de Aquiles".
""")
st.divider()
# --- Análise Final: Clustering e Componentes ---
st.subheader("Análise de Clustering e Componentes", divider="rainbow")

# --- Análise de Coeficiente de Clustering ---
st.markdown("O **coeficiente de clustering** mede a tendência dos nós em uma rede de formarem "
            "grupos ou 'triângulos'. Em outras palavras, ele responde à pergunta: 'O amigo do meu amigo também é meu amigo?'.")

col1, col2 = st.columns(2, gap="large")

# --- Coluna da Esquerda: Clustering Local ---
with col1:
    st.markdown("#### Clustering Local")

    # Permite ao usuário escolher um pesquisador do componente principal para analisar
    sorted_nodes = sorted(list(graph_for_analysis.nodes()))
    selected_node = st.selectbox(
        "Escolha um pesquisador para ver seu Coeficiente de Clustering Local:",
        options=sorted_nodes,
        index=sorted_nodes.index("Adrião Duarte Dória Neto") if "Adrião Duarte Dória Neto" in sorted_nodes else 0,
        help="Este valor representa a chance de dois orientandos/orientadores deste pesquisador também terem uma conexão entre si."
    )

    if selected_node:
        local_clustering_coeff = nx.clustering(graph_for_analysis, selected_node)
        st.metric(
            label=f"Clustering de {selected_node.split()[0]}",
            value=f"{local_clustering_coeff:.4f}"
        )
        st.markdown(f"Um valor de **{local_clustering_coeff:.2f}** indica que a vizinhança deste pesquisador é "
                    f"{'altamente conectada (um grupo coeso)' if local_clustering_coeff > 0.5 else ('moderadamente conectada' if local_clustering_coeff > 0.1 else 'pouco conectada (conexões em estrela)')}.")

# --- Coluna da Direita: Clustering Global ---
with col2:
    st.markdown("#### Clustering Global")
    global_clustering_coeff = nx.transitivity(graph_for_analysis)
    st.metric(
        label="Clustering Global da Rede (Transitividade)",
        value=f"{global_clustering_coeff:.4f}",
        help="A probabilidade geral na rede de que se A está ligado a B e B a C, A também esteja ligado a C."
    )
    st.markdown("""
    O valor global de **0.0027** é baixíssimo, aproximando-se de zero. Isso indica que a formação de "triângulos" de colaboração (onde por exemplom, o orientador do seu orientador também te orienta) é um evento **extremamente raro** na rede.

    Este resultado, em conjunto com a alta assortatividade negativa, é a confirmação mais forte de que a estrutura da rede é dominada pelo padrão "hub-and-spoke" (um professor no centro, e seus orientandos ao redor). A colaboração é quase que exclusivamente diádica (Orientador-Orientando) e hierárquica, com pouquíssimos "atalhos" ou grupos fechados onde todos colaboram com todos.
    """)



st.divider()

# --- Análise de Componentes Conectados ---
st.subheader("Análise de Componentes Conectados")
# Cria duas colunas para a análise de componentes
col1, col2 = st.columns(2, gap="large")

# --- Coluna da Esquerda: Componentes Fracos ---
with col1:
    st.markdown("#### Componentes Fracamente Conectados")
    st.markdown("Estes são os 'grupos' ou 'ilhas' de pesquisadores que você obtém se ignorar a direção das setas. "
                "Eles nos mostram quantas sub-redes distintas existem no dataset geral.")

    weak_components = list(nx.connected_components(G))
    st.metric(
        label="Número Total de 'Ilhas' na Rede",
        value=len(weak_components),
        help="Cada 'ilha' é um grupo de pesquisadores que não possui nenhuma conexão com as outras ilhas."
    )
    st.markdown(f"A rede se divide em **{len(weak_components)} componentes desconectados**. O maior deles, com **{len(weak_components[0])} membros**, "
                "é o que analisamos nas métricas de diâmetro e clustering. Os outros são grupos muito menores e isolados.")
    st.markdown("""
    Notasse que a rede é **extremamente centralizada**, com um único componente massivo contendo **1199 membros** (cerca de 85% do total). As outras 24 'ilhas' são fragmentos muito pequenos, geralmente representando um único professor e seus orientandos diretos, sem outras conexões no dataset.

    Isso demonstra uma comunidade de pesquisa **majoritariamente unificada e coesa**, e não um campo fragmentado em múltiplos grupos isolados.
    """)


# --- Coluna da Direita: Componentes Fortes ---
with col2:
    st.markdown("#### Componentes Fortemente Conectados")
    st.markdown("Aqui, usamos o **dígrafo** (respeitando as setas `Orientador → Orientado`). "
                "Um 'SCC' é um grupo onde, para qualquer par (A, B) dentro dele, "
                "é possível ir de A para B **e** voltar de B para A apenas seguindo as setas.")

    # Cria um grafo dirigido para esta análise específica
    D = nx.DiGraph()
    D.add_edges_from(edges_for_nx)
    strong_components = list(nx.strongly_connected_components(D))

    # Filtra para mostrar apenas os SCCs com mais de 1 membro
    sccs_gt1 = [list(c) for c in strong_components if len(c) > 1]

    st.metric(
        label="Núcleos de Colaboração Mútua (SCCs > 1)",
        value=len(sccs_gt1),
        help="Grupos onde a colaboração é recíproca, provavelmente via coorientações."
    )

    if sccs_gt1:
        st.markdown("Os grupos encontrados representam **núcleos de colaboração mútua**, provavelmente formados por coorientações complexas entre professores.")
        with st.expander("Ver os Núcleos de Colaboração"):
            st.json(sccs_gt1)
    else:
        st.markdown("Não foram encontrados núcleos de colaboração mútua (com mais de 1 membro), indicando uma estrutura majoritariamente hierárquica.")

# --- Análise Final: Centralidade da Rede ---
st.header("Análise de Centralidade: Quem são os Pesquisadores Mais Influentes?", divider='rainbow')
st.markdown("""
A 'importância' ou 'influência' de um pesquisador em uma rede pode ser medida de várias formas. Abaixo, exploramos quatro medidas de centralidade diferentes, cada uma revelando um tipo distinto de influência estrutural. As análises são feitas sobre o maior componente conectado da rede.
""")

# --- Explicação das Métricas de Centralidade ---
st.subheader("Entendendo as Métricas de Centralidade")
col1, col2 = st.columns(2, gap="large")
with col1:
    st.markdown("""
    #### Grau (Degree)
    **"Quem tem mais conexões diretas?"**

    Mede o número de orientações diretas (como orientador ou orientando). Um pesquisador com alto grau é um "hub" local, diretamente ativo em muitas frentes.
    """)
    st.markdown("""
    #### Proximidade (Closeness)
    **"Quem alcança todos os outros mais rapidamente?"**

    Mede a proximidade média de um pesquisador a todos os outros na rede. Um valor alto indica que a pessoa está em uma posição estrutural para disseminar informações de forma eficiente para toda a comunidade.
    """)
with col2:
    st.markdown("""
    #### Intermediação (Betweenness)
    **"Quem atua como as 'pontes' mais importantes?"**

    Mede a frequência com que um pesquisador aparece nos caminhos mais curtos entre outros dois pesquisadores. Um valor alto revela atores cruciais que conectam diferentes subgrupos.
    """)
    st.markdown("""
    #### Autovetor (Eigenvector)
    **"Quem é amigo das pessoas mais influentes?"**

    Mede a influência de um nó com base na influência de seus vizinhos. Ter uma conexão com um "mega-hub" vale mais do que ter várias conexões com nós periféricos.
    """)

st.divider()

# --- Tabela Comparativa de Centralidade ---
st.subheader("Tabela Comparativa das Centralidades")

# Slider para o usuário escolher o número de pesquisadores a serem exibidos
top_n = st.slider(
    "Selecione o número de 'Top' pesquisadores para exibir:",
    min_value=5,
    max_value=30,
    value=10,
    step=5
)

try:
    # Calcula as 4 métricas de centralidade
    degree_centrality = nx.degree_centrality(graph_for_analysis)
    betweenness_centrality = nx.betweenness_centrality(graph_for_analysis)
    closeness_centrality = nx.closeness_centrality(graph_for_analysis)
    eigenvector_centrality = nx.eigenvector_centrality(graph_for_analysis, max_iter=1000)

    # Consolida os resultados em um DataFrame do Pandas
    df_centrality = pd.DataFrame({
        'Degree': degree_centrality,
        'Betweenness': betweenness_centrality,
        'Closeness': closeness_centrality,
        'Eigenvector': eigenvector_centrality
    })

    # Calcula o ranking para cada métrica
    df_centrality['Degree_Rank'] = df_centrality['Degree'].rank(ascending=False, method='min').astype(int)
    df_centrality['Betweenness_Rank'] = df_centrality['Betweenness'].rank(ascending=False, method='min').astype(int)
    df_centrality['Closeness_Rank'] = df_centrality['Closeness'].rank(ascending=False, method='min').astype(int)
    df_centrality['Eigenvector_Rank'] = df_centrality['Eigenvector'].rank(ascending=False, method='min').astype(int)

    # Identifica os 'Top N' nós de cada categoria para garantir que todos os mais importantes apareçam
    top_degree = df_centrality.nlargest(top_n, 'Degree').index
    top_betweenness = df_centrality.nlargest(top_n, 'Betweenness').index
    top_closeness = df_centrality.nlargest(top_n, 'Closeness').index
    top_eigenvector = df_centrality.nlargest(top_n, 'Eigenvector').index

    # Une todos os 'Top N' em uma lista única, sem duplicatas
    union_of_top_nodes = list(dict.fromkeys(
        top_degree.tolist() + top_betweenness.tolist() + top_closeness.tolist() + top_eigenvector.tolist()
    ))

    # Filtra o DataFrame para mostrar apenas os nós mais importantes e as colunas de ranking
    df_display = df_centrality.loc[union_of_top_nodes][[
        'Degree_Rank', 'Betweenness_Rank', 'Closeness_Rank', 'Eigenvector_Rank'
    ]].sort_values(by='Degree_Rank')

    st.markdown(f"A tabela abaixo mostra o ranking dos pesquisadores mais centrais, de acordo com cada métrica. Um ranking de **1** significa a maior importância naquela categoria.")
    st.dataframe(df_display, use_container_width=True)

    st.markdown("""
    **Como interpretar a tabela:** Observe como alguns pesquisadores podem ter um **Grau** alto (muitas conexões diretas), mas uma **Intermediação** baixa (não atuam como pontes), enquanto outros podem ter o oposto. Essa comparação revela os diferentes papéis que os pesquisadores desempenham na estrutura da rede.
    """)

except Exception as e:
    st.error(f"Ocorreu um erro ao calcular as métricas de centralidade: {e}")

# --- Análise Final: Detecção de Comunidades (Método Louvain) ---
st.header("Detecção de Comunidades (Método Louvain)", divider='rainbow')
st.markdown("""
A detecção de comunidades busca identificar "grupos" ou "clusters" de pesquisadores que estão mais densamente conectados entre si do que com o resto da rede. O **Método Louvain** faz isso ao tentar maximizar uma métrica chamada "modularidade".

Essas comunidades podem representar grupos de pesquisa, laboratórios, ou pesquisadores com forte afinidade temática ou histórica.
""")

# --- Cálculo da Partição de Comunidades ---
# A partição é calculada aqui, dentro de sua própria seção
try:
    partition = community_louvain.best_partition(G)

    # --- Visualização do Grafo Colorido por Comunidades ---
    st.subheader("Visualização das Comunidades no Grafo")
    st.markdown("Abaixo, a rede completa é renderizada novamente, mas desta vez cada nó é colorido de acordo com a comunidade à qual pertence. Isso permite uma identificação visual imediata dos principais agrupamentos.")

    # Cria uma nova instância do Pyvis para o grafo de comunidades
    net_community = Network(notebook=True, height="750px", width="100%", cdn_resources='remote', directed=True, bgcolor="#222222", font_color="white")

    # Define uma paleta de cores para as comunidades
    community_palette = ["#E63946", "#F1FAEE", "#A8DADC", "#457B9D", "#1D3557",
                         "#FFC300", "#588157", "#3A5A40", "#E07A5F", "#3D405B",
                         "#81B29A", "#F2CC8F", "#D5573B", "#6A994E", "#F7B500"]

    # Adiciona os nós com a cor da sua comunidade
    for node_name in G.nodes():
        community_id = partition.get(node_name, -1)
        node_color = community_palette[community_id % len(community_palette)]
        # Reutiliza os dados já processados para tamanho e tooltip
        total_degree = out_degree_total.get(node_name, 0) + in_degree_total.get(node_name, 0)
        node_size = BASE_NODE_SIZE + (total_degree ** 1.2) * 0.5
        node_size = min(node_size, MAX_NODE_SIZE)
        # (O código completo do tooltip não foi adicionado aqui para simplicidade, mas poderia ser)
        title_text = f"Comunidade: {community_id}"+ "\n"+f"Nome:{node_name}"
        net_community.add_node(node_name, label=node_name, color=node_color, size=node_size, title=title_text)

    # Adiciona as arestas com um estilo neutro e uniforme
    for edge in detailed_edges:
        # Define uma cor cinza claro para todas as arestas
        edge_color = "#999999" 
        width = 1
        dashes = False
        
        # Mantém a diferenciação para coorientação, que é uma informação estrutural
        if edge['co']:
            dashes = True
            width = 0.8

        edge_title = f"{edge['source']} -> {edge['target']}\\n{edge['type']} ({edge['year']}){' [Coorientação]' if edge['co'] else ''}"
        net_community.add_edge(edge['source'], edge['target'], color=edge_color, dashes=dashes, title=edge_title, width=width)

    # Exibe o novo grafo
    net_community.set_options(options_str)
    community_graph_path = "community_graph.html"
    net_community.save_graph(community_graph_path)
    with open(community_graph_path, 'r', encoding='utf-8') as f:
        html_content_community = f.read()
    st.components.v1.html(html_content_community, height=750, scrolling=True)

    st.divider()

    # --- Estatísticas e Explorador de Comunidades ---
    st.subheader("Explore as Comunidades Detectadas")
    num_communities = len(set(partition.values()))
    communities = {}
    for node, community_id in partition.items():
        if community_id not in communities: communities[community_id] = []
        communities[community_id].append(node)

    community_sizes = {cid: len(nodes) for cid, nodes in communities.items()}
    largest_community_id = max(community_sizes, key=community_sizes.get)
    largest_community_size = community_sizes[largest_community_id]

    col1, col2 = st.columns(2)
    col1.metric("Número de Comunidades Detectadas", num_communities)
    col2.metric(f"Tamanho da Maior Comunidade (ID {largest_community_id})", f"{largest_community_size} membros")

    sorted_communities = sorted(communities.items(), key=lambda item: len(item[1]), reverse=True)
    community_options = [f"Comunidade {cid} ({len(nodes)} membros)" for cid, nodes in sorted_communities]
    selected_community_str = st.selectbox("Selecione uma comunidade para ver seus membros:", options=community_options)

    if selected_community_str:
        selected_cid = int(selected_community_str.split(" ")[1])
        members_to_show = communities[selected_cid]
        with st.expander(f"Membros da Comunidade {selected_cid}", expanded=True):
            st.write(", ".join(sorted(members_to_show)))

except Exception as e:
    st.error(f"Ocorreu um erro ao calcular ou exibir as comunidades: {e}. Verifique se a biblioteca 'python-louvain' está instalada.")



# --- Análise Final: Previsão de Laços (Link Prediction) ---
st.header("Previsão de Laços: Futuras Conexões e Colaborações", divider='rainbow')
st.markdown("""
A previsão de laços utiliza a estrutura atual da rede para prever quais novas conexões são mais prováveis de se formar no futuro.
Isso pode revelar potenciais colaborações, coorientações ou relações de orientação que são estruturalmente favorecidas.
A análise é feita sobre o maior componente conectado da rede.
""")

# --- Seleção do Algoritmo ---
st.subheader("Selecione um Algoritmo de Previsão")

algorithm_option = st.selectbox(
    "Escolha o método para calcular a probabilidade de novas conexões:",
    ("Índice Adamic-Adar (Recomendado)", "Coeficiente de Jaccard"),
    help="Adamic-Adar dá mais peso a vizinhos em comum que são mais 'exclusivos', sendo geralmente mais preciso."
)

top_n_links = st.slider(
    "Selecione o número de 'Top' previsões para exibir:",
    min_value=5, max_value=50, value=10, step=5
)

try:
    # Gera uma lista de todos os laços que NÃO existem atualmente no grafo
    non_edges = list(nx.non_edges(graph_for_analysis))

    predictions = None
    if algorithm_option == "Coeficiente de Jaccard":
        st.markdown("O **Coeficiente de Jaccard** calcula a similaridade com base na proporção de vizinhos em comum.")
        predictions = nx.jaccard_coefficient(graph_for_analysis, non_edges)

    elif algorithm_option == "Índice Adamic-Adar (Recomendado)":
        st.markdown("O **Índice Adamic-Adar** mede a similaridade dando mais peso a vizinhos em comum que têm poucas conexões.")
        predictions = nx.adamic_adar_index(graph_for_analysis, non_edges)

    if predictions:
        # Processa os resultados
        predictions_list = [(u, v, p) for u, v, p in predictions if p > 0]

        # Cria um DataFrame do Pandas com os resultados
        df_predictions = pd.DataFrame(predictions_list, columns=['Pesquisador A', 'Pesquisador B', 'Índice de Previsão'])

        # Ordena o DataFrame para mostrar as previsões mais fortes primeiro
        df_sorted = df_predictions.sort_values(by='Índice de Previsão', ascending=False)

        st.subheader(f"As {top_n_links} Conexões Futuras Mais Prováveis")
        # Exibe a tabela com os top N resultados
        st.dataframe(
            df_sorted.head(top_n_links),
            use_container_width=True,
            hide_index=True,
            column_config={
                "Índice de Previsão": st.column_config.ProgressColumn(
                    "Índice de Previsão",
                    help="Quanto maior o índice, mais provável a conexão.",
                    format="%.4f",
                    min_value=0,
                    max_value=float(df_sorted['Índice de Previsão'].max()),
                ),
            }
        )

        st.markdown("""
        #### Como Interpretar os Resultados
        A tabela acima mostra os pares de pesquisadores com maior probabilidade de formar um laço. Analise os pares para identificar:
        - **Professor-Professor:** Pode sugerir uma futura coorientação ou colaboração em projeto.
        - **Professor-Aluno:** Pode indicar uma forte afinidade para uma futura orientação.
        - **Aluno-Aluno:** Pode revelar estudantes com linhas de pesquisa muito próximas, sugerindo potencial para grupos de estudo ou futuras parcerias acadêmicas.
        """)
except Exception as e:
    st.error(f"Ocorreu um erro ao realizar a previsão de laços: {e}")
