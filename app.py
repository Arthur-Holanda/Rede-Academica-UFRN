
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
# Seus dados em formato CSV (como string)
csv_data_string = """"NOME_PRINCIPAL","FORMACAO_PRINCIPAL","CAMPUS_PRINCIPAL","LOTACAO","ORIENTADORES_ACADEMICOS","ORIENTANDOS_ACADEMICOS"
"Frederico Araújo Da Silva Lopes","Ciências Exatas e da Terra / Ciência Da Computação","Universidade Federal Do Rio Grande Do Norte","IMD","Thais Vasconcelos Batista (Orientadora de Mestrado, 2008); Thais Vasconcelos Batista E Flavia Delicato (Orientadoras de Doutorado, 2011)","Alison Hedigliranes Da Silva (Orientando de Mestrado 2024 Co); Allyson Bruno Campos Barros Vilela (Orientando de Mestrado 2018); Altair Brandao Mendes (Orientando de Mestrado 2018 Co); Cesimar Xavier De Souza Dias (Orientando de Mestrado 2019); Diogo Cirne Nunes (Orientando de Mestrado 2022); Eduardo Lima Ribeiro (Orientando de Mestrado 2016 Co); Emmanoel Monteiro De Sousa Junior (Orientando de Mestrado 2016); Fernando Da Cruz Lopes (Orientando de Mestrado 2021); Gustavo Nogueira Alves (Orientando de Mestrado 2014 Co); Jackson Meires Dantas Canuto (Orientando de Mestrado 2019); Jonas Jordao De Macedo (Orientando de Mestrado 2018); Leandro Silva Monteiro De Oliveira (Orientando de Mestrado 2021); Leonandro Valerio Barbosa Gurgel (Orientando de Mestrado 2023 Co); Lucas Simonetti Marinho Cardoso (Orientando de Mestrado 2020); Stefano Momo Loss (Orientando de Mestrado 2019 Co); Stefano Momo Loss (Orientando de Doutorado 2021 Co)"
"Heitor Medeiros Florencio","Outros / Robótica Mecatrônica E Automação","Universidade Federal Do Rio Grande Do Norte","IMD","Adrião Duarte Dória Neto (Orientador de Mestrado, 2015); Adrião Duarte Dória Neto (Orientador de Doutorado, 2019)","Italo Oliveira Fernandes (Orientando de Mestrado 2024 Co)"
"Bruno Santana Da Silva","Ciências Exatas e da Terra / Ciência Da Computação","Universidade Federal Do Rio Grande Do Norte","IMD","Simone Diniz Junqueira Barbosa (Orientadora de Mestrado, 2005); Simone Diniz Junqueira Barbosa (Orientadora de Doutorado, 2010)","Carlos Diego Franco Da Rocha (Orientando de Mestrado 2021 Co); Fernanda Kainara Marcelino Da Fonseca (Orientanda de Mestrado 2024); Jakeline Bandeira De Oliveira (Orientanda de Mestrado 2022 Co); Lorena Karen Praxedes Mariz (Orientanda de Mestrado 2024); Luciano Antônio Cordeiro De Sousa (Orientando de Mestrado 2016); Rafael Dias Santos (Orientando de Mestrado 2016)"
"Daniel Lopes Martins","Engenharias / Engenharia Elétrica","Universidade Federal Do Rio Grande Do Norte","IMD","Adrião Duarte Dória Neto (Orientador de Mestrado, 2011); Adrião Duarte Dória Neto (Orientador de Doutorado, 2017); Jorge Dantas De Melo (Coorientador de Mestrado, 2011); Jorge Dantas De Melo (Coorientador de Doutorado, 2017)",""
"Isabel Dillmann Nunes","Ciências Exatas e da Terra / Ciência Da Computação","Universidade Federal Do Rio Grande Do Norte","IMD","Daltro José Nunes (Orientador de Mestrado, 2001); Ulrich Schiel (Orientador de Doutorado, 2014)","Andressa Kroeff (Orientando de Mestrado 2020); Cintia Reis De Oliveira (Orientando de Mestrado 2019); Daniel Lucena (Orientando de Mestrado 2018); David Montalvao Junior (Orientando de Mestrado 2017); Eduardo Augusto Morais Rodrigues (Orientando de Mestrado 2020 Co); Eric Eduardo Alencar (Orientando de Mestrado 2020); Fernando Lucas De Oliveira Farias (Orientando de Mestrado 2018); Laís Michelle De Souza Araújo Bandeira (Orientando de Mestrado 2020); Lidiane Beatriz Ribeiro De Sousa (Orientando de Mestrado 2021); Maria Da Conceicao Araujo Moreno (Orientando de Mestrado 2021); Nathalie Rose Ramos Da Fonseca Araujo (Orientando de Mestrado 2018); Neide Aparecida Alves De Medeiros (Orientando de Mestrado 2020 Co); Pedrina Celia Brasil (Orientando de Mestrado 2017); Tobias Rocha (Orientando de Mestrado 2018)"
"Antonio Igor Silva De Oliveira","Mestrado em Matemática","Universidade Federal Do Rio Grande Do Norte","IMD","Antonio Pereira Brandao Junior (Orientador de Mestrado, 2011)",""
"Aluizio Ferreira Da Rocha Neto","Ciências Exatas e da Terra / Ciência Da Computação","Universidade Federal Do Rio Grande Do Norte","IMD","Flávia Coimbra Delicato (Orientador de Doutorado, 2021 Co); Ricardo De Oliveira Anido (Orientador de Mestrado, 1997); Thais Vasconcelos Batista (Orientador de Doutorado, 2021)",""
"Alyson Matheus De Carvalho Souza","Ciências Exatas e da Terra / Ciência Da Computação","Universidade Federal Do Rio Grande Do Norte","IMD","César Rennó Costa (Orientador de Doutorado, 2022); Izabel Augusta Hazin Pires (Orientador de Doutorado, 2022 Co); Selan Rodrigues Dos Santos (Orientador de Mestrado, 2014)",""
"Andre Luiz De Souza Brito","Mestrado profissional em Engenharia de Software.","Universidade Federal do Rio Grande do Norte","IMD","Charles Andryê Galvão Madeira (Orientador de Mestrado, 2017)",""
"Danilo Curvelo De Souza","Outros / Robótica Mecatrônica E Automação","Universidade Federal do Rio Grande do Norte","IMD","Adrião Duarte Dória Neto (Orientador de Mestrado, 2012); Adrião Duarte Dória Neto (Orientador de Doutorado, 2017); Jorge Dantas De Melo (Orientador de Mestrado, 2012 Co)",""
"Dennys Leite Maia","Ciências Humanas / Educação","Universidade Federal Do Rio Grande Do Norte","IMD","José Aires De Castro Filho (Orientador de Doutorado, 2016); Lia Matos Brito De Albuquerque (Orientador de Mestrado, 2011 Co); Marcilia Chagas Barreto (Orientador de Mestrado, 2012)","Carmélia Regina Silva Xavier (Orientando de Mestrado 2020); Eli Sales Muniz Lima (Orientando de Mestrado 2021); Elvis Medeiros De Melo (Orientando de Mestrado 2019); Fellipe Silva Câmara (Orientando de Mestrado 2023 Co); Giluiza Catarina Cardoso Alves Borges (Orientando de Mestrado 2024); Maria Luiza Dos Santos (Orientando de Mestrado 2024 Co); Maria Luziene Da Silva Azevedo Bandeira (Orientando de Mestrado 2019); Raiza De Araujo Domingos (Orientando de Mestrado 2023); Roberia Silva Da Penha Lourenco (Orientando de Mestrado 2024); Rodrigo Rodrigues Melo De Lima (Orientando de Mestrado 2019); Stella Layse Da Silva Lima Brito (Orientando de Mestrado 2024); Stênio Lúcio Da Rocha (Orientando de Mestrado 2020); Veridiana Kelin Appelt (Orientando de Mestrado 2022)"
"Eduardo Nogueira Cunha","Ciências Biológicas / Biotecnologia","Universidade Federal Do Rio Grande Do Norte","IMD","Carlos Eduardo Trabuco Dórea (Orientador de Mestrado, 2015); Daniel Carlos Ferreira Lanza (Orientador de Doutorado, 2020 Co); João Paulo Matos Santos Lima (Orientador de Doutorado, 2020)",""
"Gustavo Bezerra Paz Leitão","Ciências Exatas e da Terra / Ciência Da Computação","Universidade Federal Do Rio Grande Do Norte","IMD","Luiz Affonso Henderson Guedes De Oliveira (Orientador de Mestrado, 2008); Luiz Affonso Henderson Guedes De Oliveira (Orientador de Doutorado, 2018)",""
"Isaac Franco Fernandes","Engenharias / Engenharia De Produção","Universidade Federal Do Rio Grande Do Norte","IMD","Daniel Aloise (Orientador de Mestrado, 2010)",""
"Patrick Cesar Alves Terrematte","Ciências Exatas e da Terra / Ciência Da Computação","Universidade Federal Do Rio Grande Do Norte","IMD","Adrião Duarte Dória Neto (Orientador de Doutorado, 2022); Beatriz Stransky Ferreira (Orientador de Doutorado, 2022 Co); Daniel Sabino Amorim De Araújo (Orientador de Doutorado, 2022 Co); Joao Marcos De Almeida (Orientador de Mestrado, 2013)","Epitacio Dantas Farias Filho (Orientando de Mestrado 2023 Co)"
"Itamir De Morais Barroca Filho","Ciências Exatas e da Terra / Ciência Da Computação","Universidade Federal Do Rio Grande Do Norte","IMD","Gibeon Soares De Aquino Junior (Orientador de Mestrado, 2015); Gibeon Soares De Aquino Junior (Orientador de Doutorado, 2019)","Bruna Alice Oliveira De Brito (Orientando de Mestrado 2023); Cezar Miranda Paula De Souza (Orientando de Mestrado 2021); Diogo Eugenio Da Silva Cortez (Orientando de Mestrado 2020); Gildasio Da Costa Teixeira (Orientando de Mestrado 2021 Co); Iuri Janmichel De Sousa Lima (Orientando de Mestrado 2021); Ramon Santos Malaquias (Orientando de Mestrado 2020); Walter Lopes Neto (Orientando de Mestrado 2022)"
"Jean Mário Moreira De Lima","Ciências Exatas e da Terra / Ciência Da Computação","Universidade Federal Do Rio Grande Do Norte","IMD","Fábio Meneghetti Ugulino De Araújo (Orientador de Mestrado, 2018); Fábio Meneghetti Ugulino De Araújo (Orientador de Doutorado, 2021)",""
"Kayo Gonçalves E Silva","Ciências Exatas e da Terra / Ciência Da Computação","Universidade Federal Do Rio Grande Do Norte","IMD","Daniel Aloise (Orientador de Mestrado, 2013 Co); Samuel Xavier De Souza (Orientador de Mestrado, 2013); Samuel Xavier De Souza (Orientador de Doutorado, 2018)",""
"Lorena Azevedo De Sousa","Ciências Humanas / Educação","Universidade Federal Do Rio Grande Do Norte","IMD","Carlos Santos (Orientador de Doutorado, 2024 Co); Janaina Weissheimer (Orientador de Mestrado, 2014); Luis Pedro (Orientador de Doutorado, 2024)",""
"Nelson Ion De Oliveira","Ciências Exatas e da Terra / Ciência Da Computação","Universidade Federal Do Rio Grande Do Norte","IMD","Jorge Tarcisio Da Rocha Falcao (Orientador de Mestrado, 2017 Co); Marcel Vinicius Medeiros Oliveira (Orientador de Mestrado, 2017)",""
"Rafaela Horacina Silva Rocha","Mestrado em Matemática Aplicada e Estatística","Universidade Federal Do Rio Grande Do Norte","IMD","Débora Borges Ferreira (Orientador de Mestrado, 2013); Ronaldo Dias (Orientador de Mestrado, 2013 Co); Bruno Motta De Carvalho (Orientador de Doutorado, 2019)",""
"Ramon Dos Reis Fontes","Ciências Exatas e da Terra / Ciência Da Computação","UNICAMP","IMD","Christian Rodolfo Esteve Rothenberg (Orientador de Doutorado, 2018); Paulo Nazareno Maia Sampaio (Orientador de Mestrado, 2013)","Emídio De Paiva Neto (Orientando de Mestrado 2021 Co); Thiago De Abreu Lima (Orientando de Mestrado 2024)"
"Renan Cipriano Moioli","Ciências Exatas e da Terra / Ciência Da Computação","Universidade Federal Do Rio Grande Do Norte","IMD","Andrew Phillippides (Orientador de Doutorado, 2013 Co); Fernando José Von Zuben (Orientador de Mestrado, 2008); Patricia Amancio Vargas (Orientador de Mestrado, 2008 Co); Phil Husbands (Orientador de Doutorado, 2013)","Álisson De Oliveira Alves (Orientando de Mestrado 2019); Ana Cecília Sá Fernandes (Orientando de Mestrado 2019 Co); André Luiz De Lucena Moreira (Orientando de Mestrado 2021 Co); Brieuc Sauzeat (Orientando de Mestrado 2020 Co); Camila Sardeto Deolindo (Orientando de Mestrado 2015); Caroline Stephanie (Orientando de Mestrado 2017); Cecile Riquart (Orientando de Mestrado 2016 Co); Daria De Tinguy (Orientando de Mestrado 2020 Co); Eduardo Bacelar Jacobi (Orientando de Mestrado 2018); Eric Gabriel Oliveira Rodrigues (Orientando de Mestrado 2019 Co); Guilherme Fernandes De Araújo (Orientando de Doutorado 2021 Co); Ilyasse Fakhreddine (Orientando de Mestrado 2021 Co); Janany Kamalanadhan (Orientando de Mestrado 2022 Co); Jessica Winne (Orientando de Mestrado 2016 Co); Jéssica Winne Rodrigues De Freitas (Orientando de Mestrado 2016 Co); Jhielson Pimentel (Orientando de Doutorado 2023 Co); Juliana Avila De Souza (Orientando de Mestrado 2018 Co); Kelyson Nunes Dos Santos (Orientando de Mestrado 2016 Co); Lilian Fuhrmann Urbini (Orientando de Mestrado 2017 Co); Marcela De Angelis Vigas Pereira (Orientando de Mestrado 2018); Marcelo Ramos Romano (Orientando de Mestrado 2020 Co); Oscar Miranda (Orientando de Mestrado 2016 Co); Ramon Evangelista Dos Anjos Paiva (Orientando de Doutorado 2024 Co); Weslley Eunathan Fernandes Lima (Orientando de Mestrado 2018); Willian Barela Costa (Orientando de Mestrado 2019)"
"Adelson Dias De Araújo Júnior","Ciências Exatas e da Terra / Ciência Da Computação","University of Twente, UT, Holanda. & UFRN","IMD","Leonardo César Teonácio Bezerra (Orientador de Mestrado, 2019 Co); Nelio Alessandro Azevedo Cacho (Orientador de Mestrado, 2019); Pantelis M Papadopoulos (Orientador de Doutorado, 2024 Co); Ton De Jong Susan Mckenney (Orientador de Doutorado, 2024)",""
"Adja Ferreira De Andrade","Ciências Exatas e da Terra / Ciência Da Computação","Universidade Federal Do Rio Grande Do Norte","IMD","Lucia Maria Martins Giraffa (Orientador de Doutorado, 2003); Paul Brna Uk Rosa Vicari Br (Orientador de Doutorado, 2002); Raul Sidnei Wazlawick (Orientador de Mestrado, 1999); Rosa Maria Vicari (Orientador de Doutorado, 2003)","Aline Peroba Pitombeira (Orientando de Mestrado 2019); Alyana Canindé Macêdo De Barros (Orientando de Mestrado 2020); Camila Augusta Desiderio (Orientando de Mestrado 2019); Ciro Dias (Orientando de Mestrado 2023); David Harlyson Poroca Da Silva (Orientando de Mestrado 2019); Gisllayne Cristina De Araujo Brandao (Orientando de Mestrado 2021); Juliana Lacerda Da Silva Oliveira (Orientando de Mestrado 2020); Julio Cesar Da Silva Dantas (Orientando de Mestrado 2023); Maria Da Conceicao Lima Viera (Orientando de Mestrado 2020); Perla Carneiro Da Silva (Orientando de Mestrado 2019)"
"Adrião Duarte Dória Neto","Engenharias / Engenharia Elétrica","Universidade Federal Do Rio Grande Do Norte","IMD","Adaildo Gomes D Assuncao (Orientador de Mestrado, 1982); Attilio Jose Giarola (Orientador de Mestrado, 1982); Henri Baudrand (Orientador de Doutorado, 1989)","Aarão Lyra (Orientando de Doutorado 2003); Adriana Rosas De Souza (Orientando de Mestrado 1998); Adriana Takahashi (Orientando de Doutorado 2012); Adriano De Andrade Bresolin (Orientando de Doutorado 2008); Agostinho De Medeiros Brito Junior (Orientando de Doutorado 2005); Alan Paulo Oliveira Da Silva (Orientando de Mestrado 2010 Co); Aldayr Dantas De Araújo Júnior (Orientando de Mestrado 2010); Alessandra Mendes Pacheco Soares (Orientando de Mestrado 2002 Co); Allan David Garcia De Araújo (Orientando de Mestrado 2010); Allan De Medeiros Martins (Orientando de Mestrado 2001, Orientando de Doutorado 2005); Amanda Gondim De Oliveira (Orientando de Mestrado 2009 Co, Orientando de Doutorado 2018); Ana Claudia M L Albuquerque (Orientando de Mestrado 2005 Co); Ana Claudia Medeiros Lins De Albuquerque Lima (Orientando de Mestrado 2005 Co); Ana Maria Guimarães Guerreiro (Orientando de Mestrado 1999); Anderson Costa Dos Santos (Orientando de Doutorado 2019); Andrezza Cristina Da Silva Barros Souza (Orientando de Mestrado 2001); Angelo Leite Medeiros De Goes (Orientando de Mestrado 2025); Antônio De Pádua De Miranda Henriques (Orientando de Doutorado 2008); Arthur Diniz Flor Torquato Fernandes (Orientando de Mestrado 2023); Bruno Mattos Silva Wanderley (Orientando de Doutorado 2019); Bruno Vicente Alves De Lima (Orientando de Doutorado 2021); Bruno Xavier Da Costa (Orientando de Mestrado 2011); Carlos Alberto Da Silva (Orientando de Mestrado 2002); Carlos Alberto De Albuquerque Silva (Orientando de Mestrado 2010, Orientando de Doutorado 2015); Carlos Alberto De Araújo Padilha (Orientando de Mestrado 2013, Orientando de Doutorado 2017 Co); Claudilene Gomes Da Costa (Orientando de Doutorado 2012 Co); Daniel Lopes Martins (Orientando de Mestrado 2011, Orientando de Doutorado 2017); Daniel Sabino Amorim De Araújo (Orientando de Doutorado 2013); Danilo Curvelo De Souza (Orientando de Mestrado 2012, Orientando de Doutorado 2017); Danilo Lima De Souza (Orientando de Mestrado 2006); Danniel Cavalcante Lopes (Orientando de Doutorado 2009 Co); David Ricardo Do Vale Pereira (Orientando de Mestrado 2006); Débora Virgínia Da Costa E Lima (Orientando de Mestrado 2022); Diego De Miranda Gomes (Orientando de Mestrado 2006); Diego Rodrigo Cabral Silva (Orientando de Mestrado 2005, Orientando de Doutorado 2008 Co); Eduardo Henrique Silveira De Araújo (Orientando de Doutorado 2013 Co); Elionai Moura Cordeiro (Orientando de Mestrado 2018); Eloi Cagni Junior (Orientando de Mestrado 2007); Fabiana Tristão De Santana (Orientando de Doutorado 2011 Co); Fabiano Medeiros De Azevedo (Orientando de Mestrado 2009 Co); Fabio Adriano Lisboa (Orientando de Mestrado 2000); Fabio Adriano Lisboa Gomes (Orientando de Mestrado 2000); Francisca De Fátima Do Nascimento Silva (Orientando de Mestrado 2013, Orientando de Doutorado 2017); Francisco Chagas De Lima Júnior (Orientando de Doutorado 2009 Co); Francisco José Targino Vidal (Orientando de Doutorado 2013); Gláucia Regina Medeiros Azambuja Sizilio (Orientando de Doutorado 2012); Gustavo Fontoura De Souza (Orientando de Mestrado 2005 Co); Heitor Medeiros Florencio (Orientando de Mestrado 2015, Orientando de Doutorado 2019); Heliana Bezerra Soares (Orientando de Mestrado 2001, Orientando de Doutorado 2008); Helton Maia Peixoto (Orientando de Mestrado 2010 Co)"
"Anderson Paiva Cruz","Ciências Exatas e da Terra / Ciência Da Computação","Universidade Federal Do Rio Grande Do Norte","IMD","Benjamín René Callejas Bedregal (Orientador de Mestrado, 2008 Co); Benjamín René Callejas Bedregal (Orientador de Doutorado, 2012 Co); Regivan Hugo Nunes Santiago (Orientador de Mestrado, 2008); Regivan Hugo Nunes Santiago (Orientador de Doutorado, 2012)","Ramon Santos Malaquias (Orientando de Mestrado 2017)"
"André Luiz Da Silva Solino","Doutorado em Sistemas e Computação.","Universidade Federal do Rio Grande do Norte, UFRN, Brasil.","IMD","Everton Ranielly De Sousa Cavalcante (Orientador de Doutorado, 2023 Co); Silvia Regina Vergilio (Orientador de Mestrado, 2008); Thais Vasconcelos Batista (Orientador de Doutorado, 2023)",""
"Anna Giselle Camara Dantas Ribeiro","Engenharias / Engenharia Elétrica","Universidade Federal Do Rio Grande Do Norte","IMD","Ana Maria Guimarães Guerreiro (Orientador de Doutorado, 2014); André Laurindo Maitelli (Orientador de Mestrado, 2011); Luiz Marcos Garcia Goncalves (Supervisor de Pós-Doutorado, 2017)","Edilson Lobo De Medeiros Junior (Orientando de Mestrado 2021); Erick Odlanier Do Nascimento Xavier Cortez (Orientando de Mestrado 2020); Felipe Leite Guedes (Orientando de Mestrado 2018 Co); Marcos Oliveira (Orientando de Mestrado 2019); Mike Job Santos Pereira Da Silva (Orientando de Mestrado 2024); Ricardo Felipe Ferreira (Orientando de Mestrado 2021)"
"Apuena Vieira Gomes","Ciências Humanas / Educação","Universidade Federal Do Rio Grande Do Norte","IMD","Alex Sandro Gomes (Orientador de Doutorado, 2004 Co); Décio Fonseca (Orientador de Doutorado, 2004); Marcia De Paiva Bastos Gottgtroy (Orientador de Mestrado, 2000)","Barbara Fernandes Da Silva De Souza (Orientando de Mestrado 2018); Bianca Josefa Ribeiro De Oliveira (Orientando de Mestrado 2022); César Augusto Barreto Da Silva (Orientando de Mestrado 2012 Co); Clarissa Bezerra De Melo Pereira Nunes (Orientando de Mestrado 2021); Edith Cristina Da Nobrega (Orientando de Mestrado 2018); Everson Mizael Cortez Silva (Orientando de Mestrado 2017); Gelly Viana Mota (Orientando de Mestrado 2022); Gildasio Da Costa Teixeira (Orientando de Mestrado 2021); Igo Joventino Dantas Diniz (Orientando de Mestrado 2020); Iris Linhares Pimenta (Orientando de Mestrado 2012 Co); Iris Linhares Pimenta Gurgel (Orientando de Mestrado 2012 Co); Kleber Tavares Fernandes (Orientando de Mestrado 2014 Co); Leilanne Kelly Borges De Alguquerque Santos (Orientando de Mestrado 2017); Luana Talita Mateus De Souza (Orientando de Doutorado 2024 Co); Luciana De Sousa Azevedo (Orientando de Mestrado 2017); Makio Patricio Cassemiro De Souza (Orientando de Mestrado 2022); Maressa Maria Lemos De Sousa (Orientando de Mestrado 2023); Maria Gonçalves De Aquino (Orientando de Mestrado 2023); Micheli Gomes Da Silva (Orientando de Mestrado 2024); Raquel De Lima Silva Cavalcante (Orientando de Mestrado 2023); Rosângela Saraiva Carvalho (Orientando de Mestrado 2010 Co); Ynessa Beatriz Dantas De Farias (Orientando de Mestrado 2020); Ynessa Beatriz Dantas De Farias Santos (Orientando de Mestrado 2018)"
"Athanasios Tsouanas","Ciências Exatas e da Terra / Matemática","École Normale Supérieure de Lyon, ENS/Lyon, França.","IMD","Elaine Gouvêa Pimentel (Supervisor de Pós-Doutorado, 2015); Olivier Laurent (Orientador de Doutorado, 2014); Panos Rondogiannis (Orientador de Mestrado, 2010)",""
"César Rennó Costa","Engenharias / Engenharia Elétrica","Universidade Federal Do Rio Grande Do Norte","IMD","Adriano Bretanha Lopes Tort (Supervisor de Pós-Doutorado, 2016); Fernando José Von Zuben (Orientador de Mestrado, 2007); John Lisman (Orientador de Doutorado, 2012 Co); Jônatas Manzolli (Orientador de Mestrado, 2007 Co); Paul Verschure (Orientador de Doutorado, 2012)","Alyson Matheus De Carvalho Souza (Orientando de Doutorado 2022); Ana Cláudia Costa Da Silva (Orientando de Doutorado 2021 Co); André Luiz De Lucena Moreira (Orientando de Mestrado 2021); Daniel Garcia Teixeira (Orientando de Mestrado 2018); Dhiego Souto Andrade (Orientando de Doutorado 2023); Florentin Marty (Orientando de Mestrado 2012 Co); Paulo Henrique Lopes Carlos (Orientando de Mestrado 2021 Co)"
"Charles Andryê Galvão Madeira","Ciências Exatas e da Terra / Ciência Da Computação","Universidade Federal Do Rio Grande Do Norte","IMD","Geber Lisboa Ramalho (Orientador de Mestrado, 2001); Jean Gabriel Ganascia Vincent Corruble (Orientador de Doutorado, 2007)","Alexandre Ribeiro Da Silva (Orientando de Mestrado 2019 Co); Andre Luiz De Souza Brito (Orientando de Mestrado 2017); Andre Parducci Soares De Lima (Orientando de Mestrado 2024); Crisiany Alves De Sousa (Orientando de Mestrado 2021); Eduardo Henrique Rocha Do Nascimento (Orientando de Mestrado 2019 Co); Erick Bergamini Da Silva Lima (Orientando de Mestrado 2018); Eridiana Alves Da Silva Bezerra (Orientando de Mestrado 2023); Fabio Sampaio Dos Santos Camara (Orientando de Mestrado 2019); Fabio Thierry Domingues Da Silva (Orientando de Mestrado 2024); Fellipe Silva Câmara (Orientando de Mestrado 2023); Gabriel Caldas Barros E Sa (Orientando de Mestrado 2024); Giselia Maria Dos Santos Ferreira (Orientando de Mestrado 2020); Glice Rocha Pires (Orientando de Mestrado 2022); Gustavo Lima Do Nascimento (Orientando de Mestrado 2022); Jaime Bruno Cirne De Oliveira (Orientando de Mestrado 2019); Jeanne Da Silva Barbosa Bulcao (Orientando de Mestrado 2021); Joeldson Costa Damasceno (Orientando de Mestrado 2024); Jorge Felliphe Rodrigues Barbosa (Orientando de Mestrado 2018); Josiel Moreira Da Silva (Orientando de Mestrado 2022); Juliana Teixeira Da Câmara Reis (Orientando de Doutorado 2021 Co); Lucineide Cruz Araujo (Orientando de Mestrado 2020); Luiz De Franca Afonso Ferreira Filho (Orientando de Mestrado 2022); Marco Antonio Silva E Araujo (Orientando de Mestrado 2020); Neide Aparecida Alves De Medeiros (Orientando de Mestrado 2020); Samanta Ferreira Aires (Orientando de Mestrado 2020); Tathiany Deyse Fernandes Rocha (Orientando de Mestrado 2023)"
"Daniel Sabino Amorim De Araújo","Ciências Exatas e da Terra / Ciência Da Computação","Universidade Federal Do Rio Grande Do Norte","IMD","Adrião Duarte Dória Neto (Orientador de Doutorado, 2013); Allan De Medeiros Martins (Orientador de Doutorado, 2013 Co); Marcilio Carlos Pereira De Souto (Orientador de Mestrado, 2008)","Antonio Fernandes Da Silva Filho (Orientando de Mestrado 2016); Bruno Mattos Silva Wanderley (Orientando de Doutorado 2019 Co); Elionai Moura Cordeiro (Orientando de Mestrado 2018 Co); Gabriel Araujo De Souza (Orientando de Mestrado 2023 Co); Iaslan Do Nascimento Paulo Da Silva (Orientando de Mestrado 2020 Co); Igor Wescley Silva De Freitas (Orientando de Mestrado 2019); Italo Oliveira Fernandes (Orientando de Mestrado 2024); Iuri Cabral Paiva (Orientando de Mestrado 2023); Jhoseph Kelvin Lopes De Jesus (Orientando de Mestrado 2018 Co); Jhoseph Kelvin Lopes De Jesus (Orientando de Doutorado 2023 Co); Ormazabal Lima Do Nascimento (Orientando de Mestrado 2023); Patrick Cesar Alves Terrematte (Orientando de Doutorado 2022 Co); Ramiro De Vasconcelos Dos Santos Júnior (Orientando de Doutorado 2024 Co); Rodrigo Lafayette Da Silva (Orientando de Mestrado 2023 Co)"
"Eiji Adachi Medeiros Barbosa","Ciências Exatas e da Terra / Ciência Da Computação","Universidade Federal Do Rio Grande Do Norte","IMD","Alessandro Fabricio Garcia (Orientador de Mestrado, 2012); Alessandro Fabricio Garcia (Orientador de Doutorado, 2015)","Andre Santiago Da Fonseca Silva (Orientando de Mestrado 2020); Aryclenio Xavier Barros (Orientando de Mestrado 2023); Deyvisson Carlos Borges De Melo (Orientando de Mestrado 2020); Fábio Arruda Magalhães (Orientando de Mestrado 2022); Iuri Guerra De Freitas Pereira (Orientando de Mestrado 2019); Lucas Novais Assuncao (Orientando de Mestrado 2023); Renieri Rayron Da Silva Correia (Orientando de Mestrado 2018); Wallinson De Lima Silva (Orientando de Mestrado 2022); Willie Lawrence Da Paz Silva (Orientando de Mestrado 2023)"
"Elias Jacob De Menezes Neto","Ciências Exatas e da Terra / Probabilidade E Estatística","Universidade Federal Do Rio Grande Do Norte","IMD","Daniela Mesquita Leutchuk De Cademartori (Orientador de Mestrado, 2012); Jose Luis Bolzan De Morais (Orientador de Doutorado, 2016)","Marilia Gabriela Silva Lima (Orientando de Mestrado 2023); Murillo Cesar De Mello Brandão Filho (Orientando de Mestrado 2021 Co); Ramon Isaac Saldanha De Azevedo E Silva (Orientando de Mestrado 2023)"
"Gustavo Girão Barreto Da Silva","Ciências Exatas e da Terra / Ciência Da Computação","Universidade Federal Do Rio Grande Do Norte","IMD","Flávio Rech Wagner (Orientador de Mestrado, 2009); Flávio Rech Wagner (Orientador de Doutorado, 2014)","Alexandro Lima Damasceno (Orientando de Mestrado 2016 Co); Ari Barreto De Oliveira (Orientando de Mestrado 2018); Honoré Vicente Cesário (Orientando de Mestrado 2022 Co); Laysson Oliveira Luz (Orientando de Mestrado 2016 Co); Ramon Santos Nepomuceno (Orientando de Mestrado 2016 Co)"
"Iris Linhares Pimenta Gurgel","Ciências Sociais Aplicadas / Administração","Universidade Federal Do Rio Grande Do Norte","IMD","Anatália Saraiva Martins Ramos (Orientador de Mestrado, 2012); Anatália Saraiva Martins Ramos (Orientador de Doutorado, 2017); Apuena Vieira Gomes (Orientador de Mestrado, 2012 Co)",""
"Ismenia Blavatsky De Magalhaes","Ciências Exatas e da Terra / Probabilidade E Estatística","Universidade Federal Do Rio Grande Do Norte","IMD","Enrico Antonio Colosimo (Orientador de Mestrado, 2002); Fabio Gagliardi Cozman (Orientador de Doutorado, 2007)","Clarissa Bezerra De Melo Pereira Nunes (Orientando de Mestrado 2020 Co); Clesia Jordania Nunes Da Costa (Orientando de Mestrado 2023); Daniele Santos Machado (Orientando de Mestrado 2008 Co); Deise De Andrade Azevedo (Orientando de Mestrado 2008 Co); Gelly Viana Mota (Orientando de Mestrado 2022 Co); Jessica Agna C De Andrade Silva (Orientando de Mestrado 2023); Marcos Rangel De Lima (Orientando de Mestrado 2010 Co); Natália Cristina Corrêa Castelo Branco (Orientando de Mestrado 2009 Co); Rejane Leite De Souza Soares (Orientando de Mestrado 2009)"
"João Carlos Xavier Júnior","Ciências Exatas e da Terra / Ciência Da Computação","Universidade Federal Do Rio Grande Do Norte","IMD","Luiz Marcos Garcia Goncalves (Orientador de Doutorado, 2012); Nathan Gomes (Orientador de Mestrado, 2001); Teresa Bernarda Ludermir (Supervisor de Pós-Doutorado, 2017)","Anderson Pablo Nascimento Da Silva (Orientando de Mestrado 2018 Co); Artejose Revoredo Da Silva (Orientando de Mestrado 2016); Carine Azevedo Dantas (Orientando de Mestrado 2017 Co); Carlos Antonio Ramirez Beltran (Orientando de Mestrado 2021); Cephas Alves Da Silveira Barreto (Orientando de Mestrado 2018); Cephas Alves Da Silveira Barreto (Orientando de Doutorado 2023 Co); David Coelho Dos Santos (Orientando de Mestrado 2018); Diego Henrique Pegado Benício (Orientando de Mestrado 2020); Diego Soares Dos Santos (Orientando de Mestrado 2018); Dinarte Alves Martins Filho (Orientando de Mestrado 2017 Co); Yves Dantas Neves (Orientando de Mestrado 2023)"
"Jorge Estefano Santana De Souza","Ciências Exatas e da Terra / Ciência Da Computação","Universidade Federal Do Rio Grande Do Norte","IMD","Sandro José De Souza (Orientador de Doutorado, 2008)","Daniel Henrique Ferreira Gomes (Orientando de Mestrado 2024); Danilo Lopes Martins (Orientando de Mestrado 2020); Inácio Gomes Medeiros (Orientando de Doutorado 2021); Leonardo René Dos Santos Campos (Orientando de Doutorado 2018 Co); Lucas Felipe Da Silva (Orientando de Mestrado 2018); Pitágoras De Azevedo Alves Sobrinho (Orientando de Mestrado 2021 Co); Priscilla Machado Do Nascimento (Orientando de Mestrado 2018); Raul Maia Falcão (Orientando de Mestrado 2019); Raul Maia Falcão (Orientando de Doutorado 2024); Rayson Carvalho Barbosa (Orientando de Mestrado 2017 Co); Ruth Flávia Barros Setúbal (Orientando de Mestrado 2023)"
"José Ivonildo Do Rêgo","Engenharias / Engenharia Elétrica","Universidade Federal Do Rio Grande Do Norte","IMD","Liu Hsu (Orientador de Doutorado, 1982); Shankar P Bhattacharyya (Orientador de Mestrado, 1977)",""
"Julio Cesar Paulino De Melo","Engenharias / Engenharia Elétrica","Universidade Federal do Rio Grande do Norte, UFRN, Brasil.","IMD","Luiz Eduardo Cunha Leite (Orientador de Mestrado, 2010); Luiz Eduardo Cunha Leite (Orientador de Doutorado, 2015)",""
"Leonardo César Teonácio Bezerra","Ciências Exatas e da Terra / Ciência Da Computação","Université Libre de Bruxelles, ULB, Bélgica.","IMD","Elizabeth Ferreira Gouvêa (Orientador de Mestrado, 2011); Luciana Salete Buriol (Orientador de Mestrado, 2010 Co); Manuel Lopez Ibanez (Orientador de Doutorado, 2016 Co); Thomas Stutzle (Orientador de Doutorado, 2016)","Adelson Dias De Araújo Júnior (Orientando de Mestrado 2019 Co); Carlos Eduardo Morais Vieira (Orientando de Mestrado 2020); Fernanda Monteiro De Almeida (Orientando de Mestrado 2021); Lucas Hiago De Azevedo Dantas (Orientando de Mestrado 2018); Sabrina Moreira De Oliveira (Orientando de Doutorado 2022 Co); Wellerson Viana De Oliveira (Orientando de Mestrado 2021)"
"Leonardo Enzo Brito Da Silva","Engenharias / Engenharia Elétrica","Missouri University of Science and Technology, MS&T, Estados Unidos.","IMD","Donald C Wunsch Ii (Orientador de Doutorado, 2019); José Alfredo Ferreira Costa (Orientador de Mestrado, 2013)",""
"Lourena Karin De Medeiros Rocha","Ciências Exatas e da Terra / Matemática","Universidade Federal Do Rio Grande Do Norte","IMD","Paulo Cezar Pinto Carvalho (Orientador de Mestrado, 2004)",""
"Lucélio Dantas De Aquino","Linguistica Letras E Artes / Lingüística","Universidade Federal Do Rio Grande Do Norte","IMD","Luis Álvaro Sgadari Passeggi (Orientador de Doutorado, 2015); Maria Medianeira De Souza (Orientador de Mestrado, 2010)","Claudia De Souza Dantas Azevedo (Orientando de Mestrado 2021); Delanne Paulino Da Silva (Orientando de Mestrado 2023); Ednny Kelly De Almeida Sales (Orientando de Mestrado 2022); Lizândra Medeiros Dos Santos (Orientando de Mestrado 2019); Marcilene Paulino Da Silva Manso (Orientando de Mestrado 2023); Marcos Antonio De Farias Dantas (Orientando de Mestrado 2021); Maria Clara Medeiros Silva (Orientando de Mestrado 2022); Maria Do Livramento Silva Assuncao De Carvalho (Orientando de Mestrado 2021); Nathalie Rose Ramos Da Fonseca Araujo (Orientando de Mestrado 2020 Co); Russiana Costa Santos Da Silva (Orientando de Mestrado 2023)"
"Muller Moreira Souza Lopes","Ciências Exatas e da Terra / Astronomia","Instituto Nacional de Pesquisas Espaciais, INPE, Brasil.","IMD","Cassio Machiaveli Oishi (Supervisor de Pós-Doutorado, 2023); Margarete Oliveira Domingues (Orientador de Mestrado, 2014); Margarete Oliveira Domingues (Orientador de Doutorado, 2019); Odim Mendes Junior (Orientador de Mestrado, 2014 Co); Odim Mendes Junior (Orientador de Doutorado, 2019 Co)","Randall Hell Vargas Pradinett (Orientando de Mestrado 2023 Co)"
"Roger Kreutz Immich","Ciências Exatas e da Terra / Ciência Da Computação","Universidade Federal Do Rio Grande Do Norte","IMD","Edmundo Roberto Mauro Madeira (Supervisor de Pós-Doutorado, 2018); Eduardo Cerqueira (Orientador de Doutorado, 2017 Co); Luiz Carlos Zancanella (Orientador de Mestrado, 2006); Marília Curado (Orientador de Doutorado, 2017)","Alex Augusto De Souza Santos (Orientando de Mestrado 2023); Degemar Pereira Da Silva (Orientando de Mestrado 2023); Emídio De Paiva Neto (Orientando de Mestrado 2022 Co); Fillipe Dos Santos Silva (Orientando de Mestrado 2020 Co); Honoré Vicente Cesário (Orientando de Mestrado 2022); Pedro Borges (Orientando de Mestrado 2014 Co); Pedro Henrique Rodrigues Emerick (Orientando de Mestrado 2023); Rivaldo Fernandes De Albuquerque Pereira (Orientando de Mestrado 2023)"
"Samyr Silva Bezerra Jácome","Ciências Exatas e da Terra / Física","Universidade Federal Do Rio Grande Do Norte","IMD","André Auto Moreira (Orientador de Doutorado, 2009); Claudionor Gomes Bezerra (Orientador de Mestrado, 2005); José Soares De Andrade Júnior (Orientador de Doutorado, 2009 Co); Liacir Dos Santos Lucena (Supervisor de Pós-Doutorado, 2009)","Gilyan Medeiros (Orientando de Mestrado 2022)"
"Tetsu Sakamoto","Ciências Biológicas / Biologia Geral","Universidade Federal Do Rio Grande Do Norte","IMD","Elizabeth Pacheco Batista Fontes (Orientador de Mestrado, 2012); José Miguel Ortega (Orientador de Doutorado, 2016); Poliane Alfenas Zerbini (Orientador de Mestrado, 2012 Co)","Beatriz Moura Kfoury De Castro (Orientando de Mestrado 2018 Co); Eliseu Jayro De Souza Medeiros (Orientando de Mestrado 2021); Fenícia Brito Santos (Orientando de Mestrado 2017 Co); Fenícia Brito Santos (Orientando de Doutorado 2017 Co); Fernanda Stussi Duarte Lage (Orientando de Mestrado 2019 Co); João Victor Villas Bôas Spelta (Orientando de Mestrado 2024); Leonardo Cabral Afonso Ferreira (Orientando de Mestrado 2023); Matheus Miguel Soares De Medeiros Lima (Orientando de Mestrado 2024); Priscila Caroline De Sousa Costa (Orientando de Mestrado 2022); Renata Lilian Dantas Cavalcante (Orientando de Mestrado 2020); Ruth Flávia Barros Setúbal (Orientando de Mestrado 2023 Co)"
"Tibério Azevedo Pereira","Ciências Exatas e da Terra / Astronomia","Universidade Federal do Rio Grande do Norte, UFRN, Brasil.","IMD","Raimundo Silva Junior (Orientador de Mestrado, 2018); Riccardo Sturani (Orientador de Doutorado, 2023)",""
"Wellington Silva De Souza","Graduação em Engenharia da Computação.","Universidade Federal do Rio Grande do Norte, UFRN, Brasil.","IMD","Sergio Vianna Fialho (Orientador de Mestrado, 2012); Vanessa Aparecida Feijó De Souza (Orientador de Mestrado, 2018)",""
"Wesley Canedo De Souza Junior","Engenharias / Engenharia De Produção","Universidade Federal Do Rio Grande Do Norte","IMD","Noel Torres Júnior (Orientador de Mestrado, 2015); Raoni Barros Bagno (Orientador de Doutorado, 2021); Rodrigo Magalhães Ribeiro (Orientador de Doutorado, 2021 Co)",""
"William Brenno Dos Santos Oliveira","Linguistica Letras E Artes / Lingüística","Universidade Federal Do Rio Grande Do Norte","IMD","Maria Da Penha Casado Alves (Orientador de Mestrado, 2015); Maria Da Penha Casado Alves (Orientador de Doutorado, 2023)",""
"Eugênio Paccelli Aguiar Freire","Ciências Humanas / Educação","Universidade Federal do Rio Grande do Norte, UFRN, Brasil.","IMD","Arnon Alberto Mascarenhas De Andrade (Orientador de Mestrado, 2010); Arnon Alberto Mascarenhas De Andrade (Orientador de Doutorado, 2013); Maria Das Graças Pinto Coelho (Orientador de Doutorado, 2022)",""
"André Maurício Cunha Campos","Ciências Exatas e da Terra / Ciência Da Computação","Universidade Federal Do Rio Grande Do Norte","DIMAP","Marcelo Gattass (Orientador de Mestrado, 1996); Philippe Mahey (Orientador de Doutorado, 2000)","Alberto Signoretti (Orientando de Doutorado 2012 Co); Alvaro Hermano Da Silva (Orientando de Mestrado 2016); André Medeiros Dantas (Orientando de Mestrado 2008); Danielle Gomes De Freitas (Orientando de Mestrado 2011 Co); Danielle Gomes De Freitas Medeiros (Orientando de Mestrado 2011 Co); Elizama Das Chagas Lemos (Orientando de Mestrado 2011); Leonidas Da Silva Barbosa (Orientando de Mestrado 2011); Marcelo Varela De Souza (Orientando de Mestrado 2016); Rômulo De Oliveira Nunes (Orientando de Mestrado 2014); Verner Rafael Ferreira (Orientando de Mestrado 2014)"
"Anne Magaly De Paula Canuto","Ciências Exatas e da Terra / Ciência Da Computação","Universidade Federal Do Rio Grande Do Norte","DIMAP","Edson Costa De Barros Carvalho Filho (Orientador de Mestrado, 1995); Michael C Fairhurst (Orientador de Doutorado, 2001)","Alba Sandyra Bezerra Lopes Campos (Orientando de Doutorado 2021 Co); Antonino Alves Feitosa Neto (Orientando de Mestrado 2012); Antonino Alves Feitosa Neto (Orientando de Doutorado 2016); Araken De Medeiros Santos (Orientando de Mestrado 2007); Araken De Medeiros Santos (Orientando de Doutorado 2012); Arthur Costa Gorgônio (Orientando de Mestrado 2021); Carine Azevedo Dantas (Orientando de Mestrado 2017); Carine Azevedo Dantas (Orientando de Doutorado 2021); Cephas Alves Da Silveira Barreto (Orientando de Doutorado 2023); Danilo Rodrigo Cavalcante Bandeira (Orientando de Mestrado 2020); Diego Silveira Costa Nascimento (Orientando de Doutorado 2014); Diogo Fagundes De Oliveira (Orientando de Mestrado 2006 Co); Fernando Pintro (Orientando de Doutorado 2013); Fillipe Morais Rodrigues (Orientando de Mestrado 2013); Givanaldo Rocha De Souza (Orientando de Doutorado 2013 Co); Heloisa Frazão Da Silva Santiago (Orientando de Doutorado 2024); Huliane Medeiros Da Silva (Orientando de Mestrado 2016); Huliane Medeiros Da Silva (Orientando de Doutorado 2021 Co); Isaac De Lima Oliveira Filho (Orientando de Doutorado 2014 Co); Jhoseph Kelvin Lopes De Jesus (Orientando de Mestrado 2018); Jhoseph Kelvin Lopes De Jesus (Orientando de Doutorado 2023); José Augusto Saraiva Lustosa Filho (Orientando de Doutorado 2018); José Gilmar Alves Santos Junior (Orientando de Mestrado 2015); Karliane Medeiros Ovidio Vale (Orientando de Mestrado 2009); Karliane Medeiros Ovidio Vale (Orientando de Doutorado 2019); Kelyson Nunes Dos Santos (Orientando de Mestrado 2011); Laura Emmanuella Alves Dos Santos Santana (Orientando de Mestrado 2007); Laura Emmanuella Alves Dos Santos Santana (Orientando de Doutorado 2012); Lígia Maria Moura E Silva (Orientando de Mestrado 2010); Liliane Ribeiro Da Silva (Orientando de Doutorado 2015 Co); Manuel Ferreira Gomes Junior (Orientando de Mestrado 2005); Marcelo Damasceno De Melo (Orientando de Doutorado 2016); Marcílio De Oliveira Meira (Orientando de Mestrado 2011); Marjory Cristiany Da Costa Abreu (Orientando de Mestrado 2006); Mateus Silvério De Assis (Orientando de Mestrado 2016); Natássia Rafaelle Medeiros Siqueira (Orientando de Mestrado 2023); Priscilla Suene De Santana Nogueira Silverio (Orientando de Mestrado 2015); Raul Benites Paradeda (Orientando de Mestrado 2007); Regina Rosa Parente (Orientando de Mestrado 2012); Robercy Alves Da Silva (Orientando de Doutorado 2020); Rodrigo André Cuevas Gaete (Orientando de Mestrado 2008); Rômulo De Oliveira Nunes (Orientando de Doutorado 2019); Susanny Mirelli Silveira Silva (Orientando de Mestrado 2007); Valéria Maria Siqueira Bezerra (Orientando de Mestrado 2006)"
"Augusto José Venâncio Neto","Ciências Exatas e da Terra / Ciência Da Computação","Universidade Federal Do Rio Grande Do Norte","DIMAP","Edmundo Heitor Da Silva Monteiro (Orientador de Doutorado, 2008); Elizabeth Sueli Specialski (Orientador de Mestrado, 2001); Marília Curado (Orientador de Doutorado, 2008 Co)","Alisson Patrick Medeiros De Lima (Orientando de Mestrado 2019); Charles Baudouin Akono Akono (Orientando de Mestrado 2014); Charles Hallan Fernandes Dos Santos (Orientando de Mestrado 2024); Douglas Braz Maciel (Orientando de Mestrado 2020); Elifranio Alves Cruz (Orientando de Mestrado 2012); Emídio De Paiva Neto (Orientando de Mestrado 2022); Evarist Logota (Orientando de Doutorado 2013 Co); Everton Fagner Costa De Almeida (Orientando de Mestrado 2014); Fábio Henrique Cabrini (Orientando de Doutorado 2022 Co); Felipe Sampaio Dantas Da Silva (Orientando de Mestrado 2015); Felipe Sampaio Dantas Da Silva (Orientando de Doutorado 2023); Flávio De Sousa Ramalho (Orientando de Mestrado 2016); Helber Wagner Da Silva (Orientando de Doutorado 2017); Helber Wagner Da Silva (Supervisionando de Pós-Doutorado 2023); Hugo Barros Camboim (Orientando de Mestrado 2015); José Castillo Lema (Orientando de Mestrado 2014); Kelyson Nunes Dos Santos (Orientando de Mestrado 2016); Kevin Barros Costa (Orientando de Mestrado 2023); Leandro Alexandre Freitas (Orientando de Mestrado 2011); Liliane Ribeiro Da Silva (Supervisionando de Pós-Doutorado 2019); Mathews Phillipp Santos De Lima (Orientando de Mestrado 2021); Maxweel Silva Carmo (Orientando de Doutorado 2019); Paulo Eugênio Da Costa Filho (Orientando de Mestrado 2024 Co); Rui Pedro De Sa Valbom (Orientando de Mestrado 2009 Co); Sandino Barros Jardim (Orientando de Mestrado 2012); Sandino Barros Jardim (Orientando de Doutorado 2020); Tiago Silvestre Condeixa (Orientando de Mestrado 2009 Co); Wanderson Modesto Da Silva (Orientando de Mestrado 2021)"
"Benjamín René Callejas Bedregal","Ciências Exatas e da Terra / Ciência Da Computação","Universidade Federal Do Rio Grande Do Norte","DIMAP","Benedito Melo Acióly (Orientador de Doutorado, 1996); Manoel Agamemnon Lopes (Orientador de Mestrado, 1987)","Aarão Lyra (Orientando de Mestrado 1999); Aarão Lyra (Orientando de Doutorado 2003 Co); Adriana Takahashi (Orientando de Mestrado 2005); Adriana Takahashi (Orientando de Doutorado 2012 Co); Ana Maria Barbosa Abeijon (Orientando de Mestrado 2011 Co); Anderson Paiva Cruz (Orientando de Mestrado 2008 Co); Anderson Paiva Cruz (Orientando de Doutorado 2012 Co); Annaxsuel Araújo De Lima (Orientando de Doutorado 2019); Antonio Diego Silva Farias (Orientando de Doutorado 2018 Co); Camila De Araújo (Orientando de Mestrado 2006); Carlos Gustavo Araujo Da Rocha (Orientando de Mestrado 2003 Co); Claudilene Gomes Da Costa (Orientando de Doutorado 2012); Claudio Andrés Callejas Olguín (Orientando de Mestrado 2012); Claudio Andrés Callejas Olguín (Orientando de Doutorado 2016); Eduardo Silva Palmeira (Orientando de Doutorado 2013); Eduardo Silva Palmeira (Supervisionando de Pós-Doutorado 2018); Felipe Antunes Dos Santos (Orientando de Doutorado 2020); Fernando Neres De Oliveira (Orientando de Doutorado 2023 Co); Gesner Antônio Azevedo Dos Reis (Orientando de Mestrado 2010 Co); Giovani Ângelo Silva Da Nóbrega (Orientando de Mestrado 2010); Hélida Salles Santos (Orientando de Mestrado 2008); Hélida Salles Santos (Orientando de Doutorado 2016); Heloína Alves Arnaldo (Orientando de Mestrado 2014); Hortevan Marrocos Frutuoso (Orientando de Mestrado 2019); Huliane Medeiros Da Silva (Orientando de Mestrado 2016); Huliane Medeiros Da Silva (Orientando de Doutorado 2021 Co); Isaac De Lima Oliveira Filho (Orientando de Mestrado 2010); Isaac De Lima Oliveira Filho (Orientando de Doutorado 2014); Ivan Mezzomo (Orientando de Doutorado 2013); Ivanosca Andrade Da Silva (Orientando de Mestrado 2001); Ivanosca Andrade Da Silva (Orientando de Doutorado 2016); José Enéas Montenegro Dutra (Orientando de Mestrado 2000); José Frank Viana Da Silva (Orientando de Mestrado 2007); Karla Darlene Nepomuceno Ramos (Orientando de Mestrado 2002 Co); Landerson Bezerra Santiago (Orientando de Doutorado 2023); Liliane Ribeiro Da Silva (Supervisionando de Pós-Doutorado 2015); Lucélia Marques Lima Da Rocha (Orientando de Doutorado 2016); Luiz Ranyer De Araújo Lopes (Orientando de Mestrado 2019); Marcus Pinto Da Costa Da Rocha (Supervisionando de Pós-Doutorado 2013); Maria Monica Macedo Torres Silveira (Orientando de Mestrado 2002); Marília Do Amaral Dias (Orientando de Mestrado 2011 Co); Nicolas Eduardo Zumelzu Carcamo (Orientando de Doutorado 2024); Nicolas Jacobino Martins (Orientando de Mestrado 2024); Nicolás Zumelzu (Orientando de Doutorado 2024); Osmar Fernandes De Oliveira Júnior (Orientando de Mestrado 2004); Raquel Esperanza Patiño Escarcina (Orientando de Mestrado 2004); Rogério Rodrigues De Vargas (Orientando de Doutorado 2012); Ronildo Pinheiro De Araujo Moura (Orientando de Mestrado 2014); Ronildo Pinheiro De Araujo Moura (Orientando de Doutorado 2018); Roque Mendes Prado Trindade (Orientando de Doutorado 2009 Co); Rosana Medina Zanotelli (Orientando de Doutorado 2020 Co); Samara Pereira Da Costa Melo (Orientando de Mestrado 2003); Thadeu Ribeiro Benicio Milfont (Orientando de Doutorado 2021); Thiago Vinícius Vieira Batista (Orientando de Doutorado 2022); Valdigleis Da Silva Costa (Orientando de Mestrado 2016); Valdigleis Da Silva Costa (Orientando de Doutorado 2020)"
"Bruno Motta De Carvalho","Ciências Exatas e da Terra / Ciência Da Computação","Universidade Federal Do Rio Grande Do Norte","DIMAP","Gabor T Herman (Orientador de Doutorado, 2003); Jose Ricardo De Almeida Torreao (Orientador de Mestrado, 1995)","Addson Araújo Da Costa (Orientando de Mestrado 2016); Allisson Dantas De Oliveira (Orientando de Doutorado 2019); Arthur Anthony Da Cunha Romão E Silva (Orientando de Mestrado 2025); Carlos Diego Franco Da Rocha (Orientando de Mestrado 2021); Edson Alyppyo Gomes Coutinho (Orientando de Doutorado 2024); Fabiano Papaiz (Orientando de Mestrado 2013); Fellipe Matheus Costa Barbosa (Orientando de Mestrado 2020); Gabriel De Almeida Araujo (Orientando de Mestrado 2018); Hélio De Albuquerque Siebra (Orientando de Mestrado 2013); Iaslan Do Nascimento Paulo Da Silva (Orientando de Mestrado 2020); Iraçú Oliveira Santos (Orientando de Doutorado 2014); Íria Caline Saraiva Cosme (Orientando de Mestrado 2008); José Francisco Da Silva Neto (Orientando de Mestrado 2014); Jose Renato De Araujo Souto (Orientando de Mestrado 2023); Laurindo De Sousa Britto Neto (Orientando de Mestrado 2007); Lucas De Melo Oliveira (Orientando de Mestrado 2007); Luiz Fernando Virgínio Da Silva (Orientando de Mestrado 2017); Natal Henrique Cordeiro (Orientando de Mestrado 2008); Rafael Beserra Gomes (Orientando de Mestrado 2009 Co); Rafael Beserra Gomes (Orientando de Doutorado 2013 Co); Rafaela Horacina Silva Rocha (Orientando de Doutorado 2019); Samuel Da Silva Oliveira (Orientando de Doutorado 2023); Severino Paulo Gomes Neto (Orientando de Doutorado 2014); Tiago Souza Dos Santos (Orientando de Mestrado 2012); Waldson Patricio Do Nascimento Leandro (Orientando de Doutorado 2019); Ystallonne Carlos Da Silva Alves (Orientando de Mestrado 2019)"
"Carlos Augusto Prolo","Ciências Exatas e da Terra / Ciência Da Computação","Universidade Federal Do Rio Grande Do Norte","DIMAP","Aravind K Joshi (Orientador de Doutorado, 2003); Maurizio Tazza (Orientador de Mestrado, 1990)",""
"Edgard De Faria Corrêa","Ciências Exatas e da Terra / Ciência Da Computação","Universidade Federal Do Rio Grande Do Norte","DIMAP","Flávio Rech Wagner (Orientador de Doutorado, 2007 Co); Luigi Carro (Orientador de Doutorado, 2007); Luis Fernando Friedrich (Orientador de Mestrado, 1998)","Albano Rocha Da Costa (Orientando de Mestrado 2018 Co); Ana Caline Escariao De Oliveira (Orientando de Mestrado 2021); Andreia Marcelino Ernesto Ribeiro (Orientando de Mestrado 2018); Claudia Larissa Coutinho Marques (Orientando de Mestrado 2018); Lucielly Oliveira Watson (Orientando de Mestrado 2022 Co); Mathieu Jean François Sebastien Duvignaud (Orientando de Mestrado 2018 Co); Moises Cirilo De Brito Souto (Orientando de Mestrado 2017); Mona Paula Santos Da Nobrega (Orientando de Mestrado 2022 Co); Rubens Campos De Almeida Junior (Orientando de Mestrado 2021); Soraya Christiane Silva De Sousa (Orientando de Mestrado 2018); Vanderli Dantas De Araujo Junior (Orientando de Mestrado 2018)"
"Eduardo Henrique Da Silva Aranha","Ciências Exatas e da Terra / Ciência Da Computação","Universidade Federal Do Rio Grande Do Norte","DIMAP","Paulo Henrique Monteiro Borba (Orientador de Mestrado, 2002); Paulo Henrique Monteiro Borba (Orientador de Doutorado, 2009)","Alan De Oliveira Santana (Orientando de Mestrado 2017); Alan De Oliveira Santana (Orientando de Doutorado 2024); Alexandre Gomes De Lima (Orientando de Doutorado 2023); Amaro Elton Fagundes Silva (Orientando de Mestrado 2009); Breno Alexandro Ferreira De Miranda (Orientando de Mestrado 2011 Co); Cristiano Bertolini (Orientando de Doutorado 2010 Co); Francisco Genivan Silva (Orientando de Mestrado 2018); Glauber Galvão De Araujo (Orientando de Mestrado 2013); Gustavo Sizílio Nery (Orientando de Mestrado 2015); Heitor Mariano De Aquino Câmara (Orientando de Doutorado 2016); Hugo Henrique De Oliveira Mesquita (Orientando de Mestrado 2017); Jairo Rodrigo Soares Carneiro (Orientando de Mestrado 2023); Jéssica Laisa Dias Da Silva (Orientando de Mestrado 2018); Kleber Tavares Fernandes (Orientando de Doutorado 2021); Luiz Fernando Rodrigues De Barros Correa (Orientando de Mestrado 2009); Marcelo Rômulo Fernandes (Orientando de Doutorado 2023 Co); Marilia Aranha Freire (Orientando de Doutorado 2014 Co); Melissa Barbosa Pontes (Orientando de Mestrado 2009); Murilo Regalado Rocha (Orientando de Mestrado 2016); Rochely Estevam Pinto Padilha (Orientando de Mestrado 2011); Sebastião Ricardo Costa Rodrigues (Orientando de Mestrado 2019); Tainá Jesus Medeiros (Orientando de Mestrado 2014); Thiago Reis Da Silva (Orientando de Doutorado 2017); Thiago Silva Toscano De Brito (Orientando de Mestrado 2011); Vanessa Freitas Candido (Orientando de Mestrado 2009); Wellington Alexandre Fernandes (Orientando de Mestrado 2013); Wendell Oliveira De Araújo (Orientando de Mestrado 2018)"
"Everton Ranielly De Sousa Cavalcante","Ciências Exatas e da Terra / Ciência Da Computação","Universidade Federal Do Rio Grande Do Norte","DIMAP","Thais Vasconcelos Batista (Orientador de Mestrado, 2012); Thais Vasconcelos Batista (Orientador de Doutorado, 2016)","André Luiz Da Silva Solino (Orientando de Doutorado 2023 Co); Camila De Araujo (Orientando de Doutorado 2017 Co); César Augusto Perdigão Batista (Orientando de Mestrado 2019 Co); Felipe Morais Da Silva (Orientando de Mestrado 2021 Co); João Victor Lopes Da Silva (Orientando de Mestrado 2022 Co); Lucas Cristiano Calixto Dantas (Orientando de Mestrado 2020 Co); Pedro Victor Borges Caldas Da Silva (Orientando de Mestrado 2020 Co); Rodrigo Lafayette Da Silva (Orientando de Mestrado 2023); Tiago Vinicius Remigio Da Costa (Orientando de Mestrado 2023)"
"Fernando Marques Figueira Filho","Ciências Exatas e da Terra / Ciência Da Computação","Universidade Federal Do Rio Grande Do Norte","DIMAP","Paulo Lício De Geus (Orientador de Doutorado, 2011)","Fabio Freire Da Silva Junior (Orientando de Mestrado 2019); Jakeline Bandeira De Oliveira (Orientando de Mestrado 2022); Leandro De Almeida Melo (Orientando de Mestrado 2016); Leandro De Almeida Melo (Orientando de Doutorado 2020); Narallynne Maciel De Araújo (Orientando de Mestrado 2017); Tiago Henrique Da Silva Leite (Orientando de Mestrado 2019)"
"Gibeon Soares De Aquino Junior","Ciências Exatas e da Terra / Ciência Da Computação","Federal University of Pernambuco (UFPE)","DIMAP","Paulo Henrique Monteiro Borba (Orientador de Mestrado, 2002); Silvio Romero De Lemos Meira (Orientador de Doutorado, 2010)","Adorilson Bezerra De Araújo (Orientando de Mestrado 2013); Ana Carina Mendes Almeida (Orientando de Mestrado 2010 Co); Anderson Pablo Nascimento Da Silva (Orientando de Mestrado 2018); Cícero Alves Da Silva (Orientando de Mestrado 2015); Cícero Alves Da Silva (Orientando de Doutorado 2020); Dannylo Johnathan Bernardino Egídio (Orientando de Mestrado 2018); David Coelho Dos Santos (Orientando de Mestrado 2018 Co); Emanuella Aleixo De Barros (Orientando de Mestrado 2010 Co); Felipe Furtado (Orientando de Mestrado 2009 Co); Glauber Mendes Da Silva Barros (Orientando de Mestrado 2023); Héldon José Oliveira Albuquerque (Orientando de Mestrado 2014); Itamir De Morais Barroca Filho (Orientando de Mestrado 2015); Itamir De Morais Barroca Filho (Orientando de Doutorado 2019); Jean Guerethes Fernandes Guedes (Orientando de Mestrado 2015); Laudson Silva De Souza (Orientando de Mestrado 2014); Mário Andrade Vieira De Melo Neto (Orientando de Mestrado 2016); Mário Andrade Vieira De Melo Neto (Orientando de Doutorado 2021); Renan De Oliveira Silva (Orientando de Mestrado 2018); Renata De Avelar (Orientando de Mestrado 2010 Co); Sávio Rennan Menêzes Melo (Orientando de Mestrado 2021); Suzana Candido De Barros Sampaio (Orientando de Mestrado 2010 Co); Vicente De Paula Melo Filho (Orientando de Mestrado 2011)"
"Jair Cavalcanti Leite","Ciências Exatas e da Terra / Ciência Da Computação","Universidade Federal Do Rio Grande Do Norte","DIMAP","Clarisse Sieckenius De Souza (Orientador de Mestrado, 1991); Clarisse Sieckenius De Souza (Orientador de Doutorado, 1998)","Alexandre Oliveira De Meira Gusmão (Orientando de Mestrado 2001); Antonio Cosme De Souza Júnior (Orientando de Mestrado 2011); Antonio Jose Portella Almeida (Orientando de Mestrado 2002); Carlos Breno Pereira Silva (Orientando de Mestrado 2012); Cassio Higino De Freitas (Orientando de Mestrado 2010); Daniel Cunha Da Silva (Orientando de Doutorado 2015); Fabiola Mariz Da Fonseca (Orientando de Mestrado 2008); George Henrique Costa Dantas (Orientando de Mestrado 2001); Heremita Brasileiro Lira (Orientando de Mestrado 2006); Lirisnei Gomes De Sousa (Orientando de Mestrado 2007); Macilon Araujo Costa Neto (Orientando de Mestrado 2005); Macilon Araujo Costa Neto (Orientando de Doutorado 2013); Marcelo De Barros Barbosa (Orientando de Mestrado 2013); Salerno Ferreira De Sousa E Silva (Orientando de Mestrado 2007); Tatiana Aires Tavares (Orientando de Mestrado 2001); Thais Lima Machado Erhardt (Orientando de Mestrado 2006); Zalkind Lincoln Dantas Rocha (Orientando de Mestrado 2003)"
"Leonardo Cunha De Miranda","Ciências Exatas e da Terra / Ciência Da Computação","Universidade Federal Do Rio Grande Do Norte","DIMAP","Fabio Ferrentini Sampaio (Orientador de Mestrado, 2006); Jose Antonio Dos Santos Borges (Orientador de Mestrado, 2006 Co); Maria Cecília Calani Baranauskas (Orientador de Doutorado, 2010); Maria Cecília Calani Baranauskas (Supervisor de Pós-Doutorado, 2011)","Alessandro Luiz Stamatto Ferreira (Orientando de Mestrado 2014); Ana Carla De Carvalho Correia (Orientando de Mestrado 2014); Fábio Andrews Rocha Marques (Orientando de Mestrado 2018); Fábio Phillip Rocha Marques (Orientando de Mestrado 2018); Franklin Matheus Da Costa Lima (Orientando de Mestrado 2024); Gabriel Alves Vasiljevic Mendes (Orientando de Mestrado 2017); Gabriel Alves Vasiljevic Mendes (Orientando de Doutorado 2022); Juvane Nunes Marciano (Orientando de Mestrado 2014); Juvane Nunes Marciano (Orientando de Doutorado 2018); Manoel Pedro De Medeiros Neto (Orientando de Mestrado 2016); Paulo Leonardo Souza Brizolara (Orientando de Mestrado 2022); Samuel Oliveira De Azevedo (Supervisionando de Pós-Doutorado 2017); Sarah Gomes Sakamoto (Orientando de Mestrado 2014)"
"Lyrene Fernandes Da Silva","Ciências Exatas e da Terra / Ciência Da Computação","Universidade Federal Do Rio Grande Do Norte","DIMAP","Julio Cesar Sampaio Do Prado Leite (Orientador de Doutorado, 2006); Virginia Carvalho Carneiro De Paula (Orientador de Mestrado, 2002)","Ceres Germanna Braga Morais (Orientando de Mestrado 2010); Edir Lucas Icety (Orientando de Mestrado 2020); Joao Epifanio (Orientando de Doutorado 2018); João Manuel Pimentel Seabra (Orientando de Mestrado 2024); Larissa De Alencar Sobral (Orientando de Mestrado 2013); Lidiane Oliveira Dos Santos (Orientando de Mestrado 2012 Co); Maíra De Faria Barros Medeiros Andrade (Orientando de Mestrado 2013); Maira Medeiros (Orientando de Mestrado 2011); Rafael De Morais Pinto (Orientando de Mestrado 2016 Co); Rafael De Morais Pinto (Orientando de Doutorado 2022); Romeu Ferreira De Oliveira (Orientando de Mestrado 2014)"
"Marcel Vinicius Medeiros Oliveira","Ciências Exatas e da Terra / Ciência Da Computação","Universidade Federal Do Rio Grande Do Norte","DIMAP","Ana Lúcia Caneca Cavalcanti (Orientador de Mestrado, 2002); Ana Lúcia Caneca Cavalcanti (Orientador de Doutorado, 2005); Augusto Cezar Alves Sampaio (Supervisor de Pós-Doutorado, 2012)","Dalay Israel De Almeida Pereira (Orientando de Mestrado 2017); Diego Henrique Oliveira De Souza (Orientando de Mestrado 2011); Fagner Morais Dias (Orientando de Mestrado 2022); Ivan Soares De Medeiros Júnior (Orientando de Mestrado 2012); Luciano Alexandre De Farias Silva (Orientando de Mestrado 2022); Madiel De Sousa Conserva Filho (Orientando de Mestrado 2011); Madiel De Sousa Conserva Filho (Orientando de Doutorado 2016); Nelson Ion De Oliveira (Orientando de Mestrado 2017); Paulo Eneas Rolim Bezerra (Orientando de Mestrado 2023); Samuel Lincoln Magalhaes Barrocas (Orientando de Mestrado 2011); Samuel Lincoln Magalhaes Barrocas (Orientando de Doutorado 2018); Sarah Raquel Da Rocha Silva (Orientando de Mestrado 2013)"
"Marcia Jacyntha Nunes Rodrigues Lucena","Ciências Exatas e da Terra / Ciência Da Computação","Universidade Federal Do Rio Grande Do Norte","DIMAP","Carla Taciana Lima Lourenco Silva Schuenemann (Orientador de Doutorado, 2010 Co); Jaelson Freire Brelaz De Castro (Orientador de Doutorado, 2010)","Aline De Oliveira Prata Jaqueira (Orientando de Mestrado 2013); Eltoni Alves Guimarães (Orientando de Mestrado 2022); Erica Esteves Cunha De Miranda (Orientando de Doutorado 2021); Eriton De Barros Farias (Orientando de Mestrado 2018); Fábio Alexandre Gonçalves Silva (Orientando de Mestrado 2013); Fábio Fernandes Penha (Orientando de Mestrado 2017); Gabriela Oliveira Da Trindade (Orientando de Mestrado 2018); Ilueny Constâncio Chaves Dos Santos (Orientando de Mestrado 2016); Ivanosca Andrade Da Silva (Orientando de Mestrado 2001 Co); João Carlos Epifânio Da Silva (Orientando de Mestrado 2018); Kleber Tavares Fernandes (Orientando de Mestrado 2014); Kleber Tavares Fernandes (Orientando de Doutorado 2021 Co); Luana Talita Mateus De Souza (Orientando de Mestrado 2019); Luana Talita Mateus De Souza (Orientando de Doutorado 2024); Rafael De Morais Pinto (Orientando de Mestrado 2016); Rafael Jullian Oliveira Do Nascimento (Orientando de Doutorado 2023); Ramon Williams Siqueira Fonseca (Orientando de Mestrado 2022); Renato Mesquita Soares (Orientando de Mestrado 2020); Robson Paulo Da Silva (Orientando de Mestrado 2016); Sara Guimaraes Negreiros (Orientando de Mestrado 2024 Co)"
"Márcio Eduardo Kreutz","Ciências Exatas e da Terra / Ciência Da Computação","Universität Oldenburg&Technische Universität Dresden","DIMAP","Altamiro Amadeu Susin (Orientador de Mestrado, 1997; Orientador de Doutorado, 2005)","Anderson Egberto Cavalcante Salles (Orientando de Mestrado 2021); Aparecida Lopes De Medeiros Lima (Orientando de Mestrado 2014); Christiane De Araújo Nobre (Orientando de Mestrado 2012); Dênis Freire Lopes Nunes (Orientando de Doutorado 2021); Hadley Magno Da Costa Siqueira (Orientando de Mestrado 2015, Orientando de Doutorado 2020); Jefferson Igor Duarte Silva (Orientando de Mestrado 2018); Jonathan Wanderley De Mesquita (Orientando de Mestrado 2016); Max Miller Da Silveira (Orientando de Mestrado 2013); Paulo Eugênio Da Costa Filho (Orientando de Mestrado 2024); Samuel Da Silva Oliveira (Orientando de Mestrado 2018, Orientando de Doutorado 2023 Co)"
"Marcos Cesar Madruga Alves Pinheiro","Ciências Exatas e da Terra / Ciência Da Computação","Universidade Federal Do Rio Grande Do Norte","DIMAP","Guido Lemos De Souza Filho (Orientador de Mestrado, 2001); Luiz Affonso Henderson Guedes De Oliveira (Orientador de Doutorado, 2006 Co); Thais Vasconcelos Batista (Orientadora de Mestrado, 2001 Co; Orientadora de Doutorado, 2006)","Dhiego Fernandes Carvalho (Orientando de Mestrado 2014); Leonardo Dantas De Oliveira (Orientando de Mestrado 2014)"
"Martin Alejandro Musicante","Ciências Exatas e da Terra / Ciência Da Computação","Universidade Federal Do Rio Grande Do Norte","DIMAP","Rafael Dueire Lins (Orientador de Mestrado, 1990); Silvio Romero De Lemos Meira (Orientador de Doutorado, 1996)","Andre Murbach Maidl (Orientando de Mestrado 2007); Ciro Morais Medeiros (Orientando de Mestrado 2018, Orientando de Doutorado 2022); Claudio Ricardo Vieira Carvilhe (Orientando de Mestrado 2002); Daniel Aguiar Da Silva Oliveira Carvalho (Orientando de Mestrado 2013); Diógenes Cogo Furlan (Orientando de Mestrado 2000); Edinardo Potrich (Orientando de Mestrado 2006); Emerson Faria Nobre (Orientando de Mestrado 2001 Co); Evando Carlos Pessini (Orientando de Doutorado 2014); Fabio De Souza Leal (Orientando de Mestrado 2016); Handerson Bezerra Medeiros (Orientando de Mestrado 2013); Henrique Denes Hilgenberg Fernandes (Orientando de Mestrado 2001); Jaylson Teixeira (Orientando de Mestrado 2000); João Batista De Souza Neto (Orientando de Doutorado 2020); Josiane Michalak Hauagge Dall Agnol (Orientando de Mestrado 2000); Julio Cesar Teodoro Da Silva (Orientando de Mestrado 2007 Co); Marcelo Araújo (Orientando de Mestrado 2004); Marcelo Guerra (Orientando de Mestrado 2010); Márcio Alves De Macêdo (Orientando de Mestrado 2015); Marcos Aurélio Carrero (Orientando de Mestrado 2006); Plácido Antonio De Souza Neto (Orientando de Doutorado 2012); Roberta Cynthia Barbosa De Freitas (Orientando de Mestrado 2020); Robson Joao Padilha Da Luz (Orientando de Mestrado 2007); Sandra Mara Guse Scós Venske (Orientando de Mestrado 2004); Simone Nasser Matos (Orientando de Mestrado 2001); Simone Nasser Matos Ferreira (Orientando de Mestrado 2001)"
"Matheus Da Silva Menezes","Ciências Exatas e da Terra / Matemática","Universidade Federal Do Rio Grande Do Norte","DIMAP","Marco Cesar Goldbarg (Orientador de Doutorado, 2014); Roberto Quirino Do Nascimento (Orientador de Mestrado, 2006)","Francisco David Kelliton Alves Cruz (Orientando de Mestrado 2024); Julia Madalena Miranda Campos (Orientando de Doutorado 2023 Co); Quezia Emanuelly De Oliveira Souza (Orientando de Mestrado 2022 Co); Ranmsés Emanuel Martins Bastos (Orientando de Doutorado 2023 Co)"
"Monica Magalhães Pereira","Ciências Exatas e da Terra / Ciência Da Computação","Universidade Federal Do Rio Grande Do Norte","DIMAP","Ivan Saraiva Silva (Orientador de Mestrado, 2008); Luigi Carro (Orientador de Doutorado, 2012)","Alba Sandyra Bezerra Lopes Campos (Orientando de Doutorado 2021); Eliselma Vieira Dos Santos (Orientando de Mestrado 2015); Elisio Breno Garcia Cardoso (Orientando de Mestrado 2021); Hiago Mayk Gomes De Araújo Rocha (Orientando de Mestrado 2019); Lavinia Medeiros Miranda (Orientando de Mestrado 2022); Luana Pereira Barreto (Orientando de Mestrado 2016); Marcos Oliveira Da Cruz (Orientando de Mestrado 2015); Maria Fernanda Cabral Ribeiro (Orientando de Mestrado 2024)"
"Nelio Alessandro Azevedo Cacho","Ciências Exatas e da Terra / Ciência Da Computação","Universidade Federal Do Rio Grande Do Norte","DIMAP","Alessandro Fabricio Garcia (Orientador de Doutorado, 2009); Thais Vasconcelos Batista (Orientadora de Mestrado, 2006)","Adelson Dias De Araújo Júnior (Orientando de Mestrado 2019); Alison Hedigliranes Da Silva (Orientando de Mestrado 2024); Arthur Emanoel Cássio Da Silva E Souza (Orientando de Mestrado 2015, Orientando de Doutorado 2022); Eliezio Soares De Sousa Neto (Orientando de Mestrado 2014); Everton Tavares Guimaraes (Orientando de Mestrado 2010 Co); Fernando Castor (Orientando de Mestrado 2010 Co); Frederico Nunes Do Pranto Filho (Orientando de Mestrado 2016); Gabriel Araujo De Souza (Orientando de Mestrado 2023); Israel Barbosa Garcia (Orientando de Mestrado 2013); José Alex Medeiros De Lima (Orientando de Mestrado 2015); Jose Lucas Santos Ribeiro (Orientando de Mestrado 2020); Juliana De Araújo Oliveira (Orientando de Mestrado 2015, Orientando de Doutorado 2021); Larysse Savanna (Orientando de Mestrado 2020); Leandro Silva Monteiro De Oliveira (Orientando de Mestrado 2021 Co); Matheus Alves De Sousa (Orientando de Mestrado 2009 Co); Mickael Raninson Carneiro Figueredo (Orientando de Mestrado 2019); Ramiro De Vasconcelos Dos Santos Júnior (Orientando de Doutorado 2024); Stefano Momo Loss (Orientando de Mestrado 2019); Thomas Filipe Da Silva Diniz (Orientando de Mestrado 2016)"
"Rafael Beserra Gomes","Ciências Exatas e da Terra / Ciência Da Computação","Universidade Federal Do Rio Grande Do Norte","DIMAP","Bruno Motta De Carvalho (Orientador de Mestrado, 2009 Co; Orientador de Doutorado, 2013 Co); Luiz Marcos Garcia Goncalves (Orientador de Mestrado, 2009; Orientador de Doutorado, 2013)","Fabio Fonseca De Oliveira (Orientando de Mestrado 2017); Fellipe Matheus Costa Barbosa (Orientando de Mestrado 2020 Co); Petrúcio Ricardo Tavares De Medeiros (Orientando de Mestrado 2016, Orientando de Doutorado 2020)"
"Ranniery Da Silva Maia","Engenharias / Engenharia Elétrica","Universidade Federal Do Rio Grande Do Norte","DIMAP","Fernando Gil Vianna Resende Junior (Orientador de Mestrado, 2000 Co; Orientador de Doutorado, 2005 Co); Keiichi Tokuda (Orientador de Doutorado, 2006); Rui Seara (Supervisor de Pós-Doutorado, 2020); Sergio Lima Netto (Orientador de Mestrado, 2000)",""
"Regivan Hugo Nunes Santiago","Ciências Exatas e da Terra / Ciência Da Computação","Universidade Federal Do Rio Grande Do Norte","DIMAP","Benedito Melo Acióly (Orientador de Mestrado, 1995; Orientador de Doutorado, 1999; Supervisor de Pós-Doutorado, 2011)","Adriano Xavier Carvalho (Orientando de Mestrado 2005); Alexsandra Oliveira Andrade (Orientando de Doutorado 2014 Co); Anderson Paiva Cruz (Orientando de Mestrado 2008, Orientando de Doutorado 2012); Antônia Jocivania Pinheiro (Orientando de Doutorado 2019); Antonio Diego Silva Farias (Orientando de Doutorado 2018); Emmanuelly Monteiro Silva De Sousa (Orientando de Mestrado 2015, Orientando de Doutorado 2020); Fabiana Tristão De Santana (Orientando de Doutorado 2011); Fágner Lemos De Santana (Orientando de Doutorado 2012); Fernando Neres De Oliveira (Orientando de Doutorado 2023); Flaulles Boone Bergamaschi (Orientando de Doutorado 2015, Orientando de Pós-doutorado 2020); Ivan Mezzomo (Orientando de Doutorado 2013 Co); José Frank Viana Da Silva (Orientando de Mestrado 2006 Co); José Medeiros Dos Santos (Orientando de Mestrado 2001); Juscelino Pereira De Araújo (Orientando de Doutorado 2025); Katiane Ribeiro Lopes (Orientando de Mestrado 2004); Liliane Ribeiro Da Silva (Orientando de Doutorado 2015); Marcia Maria De Castro Cruz (Orientando de Mestrado 2000, Orientando de Doutorado 2008 Co); Marciano Lourenço Da Silva Gonçalves (Orientando de Mestrado 2012); Maria José Lima Dos Santos (Orientando de Mestrado 2002 Co); Rui Eduardo Brasileiro Paiva (Orientando de Doutorado 2019); Suene Campos Duarte (Orientando de Doutorado 2022); Valdigleis Da Silva Costa (Orientando de Doutorado 2020 Co)"
"Roberta De Souza Coelho","Ciências Exatas e da Terra / Ciência Da Computação","Universidade Federal Do Rio Grande Do Norte","DIMAP","Arndt Von Staa (Orientador de Doutorado, 2008); Silvio Romero De Lemos Meira (Orientador de Mestrado, 2002)","Alexandre Strapacao Guedes Vianna (Orientando de Mestrado 2012 Co); Carlos Antônio De Oliveira Neto (Orientando de Mestrado 2019); Carlos Breno Pereira Silva (Orientando de Mestrado 2012 Co); Demóstenes Santos De Sena (Orientando de Doutorado 2017); Eduardo Henrique Rocha Do Nascimento (Orientando de Mestrado 2019); Francisco Diogo Oliveira De Queiroz (Orientando de Mestrado 2016); Heitor Mariano De Aquino Câmara (Orientando de Mestrado 2011 Co); Hugo Faria Melo (Orientando de Mestrado 2012, Orientando de Doutorado 2019); João Maria Guedes Da Cruz Júnior (Orientando de Mestrado 2014 Co); Joilson Vidal Abrantes (Orientando de Mestrado 2016); Leandro Dias Beserra (Orientando de Mestrado 2019); Lucas Mariano Galdino De Almeida (Orientando de Mestrado 2018); Lucas Rodrigues Silva (Orientando de Mestrado 2021); Marcio David De Magalhaes Santos (Orientando de Mestrado 2010 Co); Ricardo Jose Sales Junior (Orientando de Mestrado 2013); Sara Guimarães Negreiros (Orientando de Mestrado 2024); Taiza Montenegro (Orientando de Mestrado 2017); Teresa Do Carmo Barreto Fernandes (Orientando de Mestrado 2017); Vicente Pires Lustosa Neto (Orientando de Mestrado 2013)"
"Selan Rodrigues Dos Santos","Ciências Exatas e da Terra / Ciência Da Computação","Universidade Federal Do Rio Grande Do Norte","DIMAP","Ken Brodlie (Orientador de Doutorado, 2004); Marcelo De Andrade Dreux (Orientador de Mestrado, 1996)","Alyson Matheus De Carvalho Souza (Orientando de Mestrado 2014); Daniel Soares Brandão (Orientando de Mestrado 2014); Edson Alyppyo Gomes Coutinho (Orientando de Mestrado 2012, Orientando de Doutorado 2024 Co); Italo Mendes Da Silva Ribeiro (Orientando de Mestrado 2011, Orientando de Doutorado 2014); Luciane Machado Fraga (Orientando de Doutorado 2014); Matheus Abrantes Gadelha (Orientando de Mestrado 2012); Philip Michel Duarte (Orientando de Mestrado 2011); Waldson Patricio Do Nascimento Leandro (Orientando de Mestrado 2013, Orientando de Doutorado 2019 Co)"
"Sílvia Maria Diniz Monteiro Maia","Ciências Exatas e da Terra / Ciência Da Computação","Universidade Federal Do Rio Grande Do Norte","DIMAP","Elizabeth Ferreira Gouvêa (Orientadora de Doutorado, 2013); Marco Cesar Goldbarg (Orientador de Mestrado, 2011)","Hiago Mayk Gomes De Araújo Rocha (Orientando de Mestrado 2019 Co); Lucas Daniel Monteiro Dos Santos Pinheiro (Orientando de Mestrado 2016 Co); Luis Tertulino Da Cunha Neto (Orientando de Mestrado 2021); Sidemar Fideles Cezario (Orientando de Mestrado 2019 Co); Thiago Soares Marques (Orientando de Mestrado 2019 Co)"
"Thais Vasconcelos Batista","Ciências Exatas e da Terra / Ciência Da Computação","Universidade Federal Do Rio Grande Do Norte","DIMAP","Luiz Fernando Gomes Soares (Orientador de Mestrado, 1994); Noemi De La Rocque Rodriguez (Orientadora de Doutorado, 2000)","Altair Brandao Mendes (Orientando de Mestrado 2018); Aluizio Ferreira Da Rocha Neto (Orientando de Doutorado 2021); Ana Luisa Ferreira De Medeiros (Orientando de Mestrado 2008, Orientando de Doutorado 2012); André Gustavo Duarte De Almeida (Orientando de Mestrado 2008, Orientando de Doutorado 2015); André Luiz Da Silva Solino (Orientando de Doutorado 2023); Arthur Emanoel Cássio Da Silva E Souza (Orientando de Mestrado 2015 Co); Bartira Paraguaçu Falcão Dantas Rocha (Orientando de Doutorado 2020); Caio Sérgio De Vasconcelos Batista (Orientando de Mestrado 2004, Orientando de Doutorado 2014); Camila De Araújo (Orientando de Doutorado 2023); Carlos Alberto Nunes Machado (Orientando de Doutorado 2015); César Augusto Perdigão Batista (Orientando de Mestrado 2019); Douglas Arthur De Abreu Rolim (Orientando de Mestrado 2020); Eduardo Alexandre Ferreira Silva (Orientando de Mestrado 2015, Orientando de Doutorado 2018); Everton Ranielly De Sousa Cavalcante (Orientando de Mestrado 2012, Orientando de Doutorado 2016); Everton Tavares Guimaraes (Orientando de Mestrado 2010); Fabrício De Alexandria Fernandes (Orientando de Mestrado 2004); Felipe Morais Da Silva (Orientando de Mestrado 2024); Frederico Araújo Da Silva Lopes (Orientando de Mestrado 2008, Orientando de Doutorado 2011); Gustavo Nogueira Alves (Orientando de Mestrado 2014); Joao Gabriel Quaresma De Almeida (Orientando de Mestrado 2021); João Victor Lopes Da Silva (Orientando de Mestrado 2022); Jorge Pereira Da Silva (Orientando de Mestrado 2017, Orientando de Doutorado 2021); José Diego Saraiva Da Silva (Orientando de Mestrado 2009); Jose Neilton Dias De Morais (Orientando de Mestrado 2003); Keivilany Janielle De Lima Coelho (Orientando de Mestrado 2012); Larysse Savanna Izidio Da Silva (Orientando de Mestrado 2020 Co); Lidiane Oliveira Dos Santos (Orientando de Mestrado 2012, Orientando de Doutorado 2020); Lucas Cristiano Calixto Dantas (Orientando de Mestrado 2020); Lucas Silva Pereira (Orientando de Mestrado 2010); Marcos Cesar Madruga Alves Pinheiro (Orientando de Mestrado 2001 Co, Orientando de Doutorado 2006); Matheus Alves De Sousa (Orientando de Mestrado 2010); Nelio Alessandro Azevedo Cacho (Orientando de Mestrado 2006); Pedro Petrovitch Caetano Maia (Orientando de Mestrado 2011); Pedro Victor Borges Caldas Da Silva (Orientando de Mestrado 2020 Co, Orientando de Doutorado 2022 Co); Porfírio Dantas Gomes (Orientando de Mestrado 2016); Priscilla Victor Dantas (Orientando de Mestrado 2012 Co); Rommel Wladimir De Lima (Orientando de Mestrado 2003); Samuel De Medeiros Queiroz (Orientando de Mestrado 2018); Stéphany Moraes Martins (Orientando de Mestrado 2003); Taniro Chacon Rodrigues (Orientando de Doutorado 2015); Tássia Aparecida Vieira De Freitas (Orientando de Mestrado 2009); Thiago Pereira Da Silva (Orientando de Mestrado 2012, Orientando de Doutorado 2023); Vagner Jose Do Sacramento Rodrigues (Orientando de Mestrado 2002); Vagner Sacramento (Orientando de Mestrado 2002)"
"Uira Kulesza","Ciências Exatas e da Terra / Ciência Da Computação","Universidade Federal Do Rio Grande Do Norte","DIMAP","Carlos José Pereira De Lucena (Orientador de Doutorado, 2007); Dilma Menezes Da Silva (Orientadora de Mestrado, 2000)","Adorilson Bezerra De Araújo (Orientando de Mestrado 2017); Alexandre Strapacao Guedes Vianna (Orientando de Mestrado 2012); Andre Luis Sequeira De Sousa (Orientando de Mestrado 2008 Co); Camila Patricia Bazilio Nunes (Orientando de Mestrado 2009 Co); Christoph Treude (Orientando de Pós-doutorado 2015); Daniel Alencar Da Costa (Orientando de Mestrado 2013, Orientando de Doutorado 2017); Danielle Gomes De Freitas Medeiros (Orientando de Mestrado 2011); Demóstenes Santos De Sena (Orientando de Doutorado 2017 Co); Dhiego Abrantes De Oliveira Martins (Orientando de Mestrado 2013 Co); Edmilson Barbalho Campos Neto (Orientando de Mestrado 2013, Orientando de Doutorado 2018); Elder José Reioli Cirilo (Orientando de Mestrado 2008 Co, Orientando de Pós-doutorado 2023); Eliezio Soares De Sousa Neto (Orientando de Doutorado 2023); Erick Sharlls Ramos De Pontes (Orientando de Mestrado 2017); Felipe Alves Pereira Pinto (Orientando de Doutorado 2015); Fellipe Araújo Aleixo (Orientando de Doutorado 2013); Fladson Thiago Oliveira Gomes (Orientando de Mestrado 2016); Geam Carlos De Araújo Filgueira (Orientando de Mestrado 2009); Gleydson De Azevedo Ferreira Lima (Orientando de Doutorado 2014 Co); Guilherme Dutra Diniz De Freitas (Orientando de Mestrado 2020); Gustavo Sizílio Nery (Orientando de Mestrado 2015 Co, Orientando de Doutorado 2020); Heitor Mariano De Aquino Câmara (Orientando de Mestrado 2011); Henrique Andre Barbosa Bittencourt Dutra (Orientando de Mestrado 2017 Co); Hugo Faria Melo (Orientando de Mestrado 2012 Co); Ingrid Oliveira De Nunes (Orientando de Mestrado 2009 Co); Jackson Meires Dantas Canuto (Orientando de Mestrado 2018 Co); Jadson Jose Dos Santos (Orientando de Mestrado 2015, Orientando de Doutorado 2024); Jalerson Raposo Ferreira De Lima (Orientando de Mestrado 2014); João Helis Junior De Azevedo Bernardo (Orientando de Mestrado 2017); João Maria Guedes Da Cruz Júnior (Orientando de Mestrado 2014); Joao Victor De Oliveira Neto (Orientando de Mestrado 2017 Co); Jose Carrera Alvares Neto (Orientando de Mestrado 2009); José Diego Saraiva Da Silva (Orientando de Doutorado 2023); José Gameleira Do Rêgo Neto (Orientando de Mestrado 2021); José Pergentino De Araújo Neto (Orientando de Mestrado 2009); Julio Cesar Leoncio Da Silva (Orientando de Mestrado 2016); Klessis Lopes Dias (Orientando de Mestrado 2008 Co); Leo Moreira Silva (Orientando de Mestrado 2017); Marcelo Rômulo Fernandes (Orientando de Doutorado 2023); Marcos Alexandre De Melo Medeiros (Orientando de Mestrado 2020); Marilia Aranha Freire (Orientando de Doutorado 2014); Mario Sergio Scaramuzzini Torres (Orientando de Mestrado 2011); Miguel De Oliveira Ataide (Orientando de Mestrado 2024); Rodrigo Rebouças De Almeida (Orientando de Doutorado 2022); Samuel Lucas De Moura Ferino (Orientando de Mestrado 2023); Thiago David Dos Santos Marinho (Orientando de Mestrado 2016); Thiago De Farias Costa (Orientando de Mestrado 2009); Victor Hugo Freire Ramalho (Orientando de Mestrado 2024); Wanderson Câmara Dos Santos (Orientando de Mestrado 2011)"
"Umberto Souza Da Costa","Ciências Exatas e da Terra / Ciência Da Computação","Universidade Federal Do Rio Grande Do Norte","DIMAP","Anamaria Martins Moreira (Orientadora de Mestrado, 2001); Sergio Vale Aguiar Campos (Orientador de Doutorado, 2005)","Ciro Morais Medeiros (Orientando de Mestrado 2018 Co); Denis José Sousa De Albuquerque (Orientando de Mestrado 2019); Fred De Castro Santos (Orientando de Mestrado 2018); José Sueney De Lima (Orientando de Mestrado 2014); Rafael Ferreira Toledo (Orientando de Mestrado 2018); Sidney Soares Marcelino (Orientando de Mestrado 2013)"
"Valdigleis Da Silva Costa","Ciências Exatas e da Terra / Ciência Da Computação","Universidade Federal Do Rio Grande Do Norte","DIMAP","Benjamín René Callejas Bedregal (Orientador de Mestrado, 2016; Orientador de Doutorado, 2020); Regivan Hugo Nunes Santiago (Orientador de Doutorado, 2020 Co)",""
"Adelardo Adelino Dantas De Medeiros","Engenharias / Engenharia Elétrica","Universidade Federal Do Rio Grande Do Norte","DCA","Elder Moreira Hemerly (Orientador de Mestrado, 1991); Raja Chatila (Orientador de Doutorado, 1997)","Allan Aminadab André Freire Soares (Orientando de Mestrado 2004 Co); Anderson Abner De Santana Souza (Orientando de Mestrado 2008 Co); Andre Macedo Santana (Orientando de Mestrado 2007, Orientando de Doutorado 2011); Andre Tavares Da Silva (Orientando de Mestrado 2014); Anfranserai Morais Dias (Orientando de Mestrado 2002 Co); Clauber Gomes Bezerra (Orientando de Mestrado 2004 Co); Daniel Silva De Morais (Orientando de Mestrado 2024 Co); Diogo Pinheiro Fernandes Pedrosa (Orientando de Mestrado 2001, Orientando de Doutorado 2006); Ellon Paiva Mendes (Orientando de Mestrado 2011); Filipe Campos De Alcantara Lins (Orientando de Mestrado 2010, Orientando de Doutorado 2023 Co); Frederico Carvalho Vieira (Orientando de Mestrado 2005); Gutemberg Santos Santiago (Orientando de Mestrado 2008); João Paulo Ferreira Guimarães (Orientando de Mestrado 2012); Kaiser Magalde C Magalhaes (Orientando de Mestrado 2003); Kelson Romulo Teixeira Aires (Orientando de Mestrado 2001 Co, Orientando de Doutorado 2009); Lennedy Campos Soares (Orientando de Mestrado 2010); Luiz Henrique Rodrigues Da Silva (Orientando de Mestrado 2013); Marcelo Borges Nogueira (Orientando de Mestrado 2005); Marcelo Minicuci Yamamoto (Orientando de Mestrado 2005); Patricia Nishimura Guerra (Orientando de Mestrado 2005 Co); Ricardo De Sousa Britto (Orientando de Mestrado 2007); Ricardo Wagner De Araujo (Orientando de Doutorado 2005); Rodrigo Barbosa De Souza (Orientando de Mestrado 2003); Rodrigo Pereira Bandeira (Orientando de Mestrado 2002); Vitor Meneghetti Ugulino De Araujo (Orientando de Mestrado 2011)"
"Agostinho De Medeiros Brito Junior","Engenharias / Engenharia Elétrica","Universidade Federal Do Rio Grande Do Norte","DCA","Adrião Duarte Dória Neto (Orientador de Doutorado, 2005); Clesio Luis Tozzi (Orientador de Mestrado, 1996); Jorge Dantas De Melo (Orientador de Doutorado, 2005 Co)","Adelson Luiz De Lima (Orientando de Mestrado 2012); Aguinaldo Bezerra Batista Júnior (Orientando de Mestrado 2009 Co); João Paulo De Souza Medeiros (Orientando de Mestrado 2009)"
"Anderson Luiz De Oliveira Cavalcanti","Engenharias / Engenharia Elétrica","Universidade Federal Do Rio Grande Do Norte","DCA","Adhemar De Barros Fontes (Orientador de Mestrado, 2003 Co; Orientador de Doutorado, 2008 Co); André Laurindo Maitelli (Orientador de Mestrado, 2003; Orientador de Doutorado, 2008); Karl Heinz Kienitz (Supervisor de Pós-Doutorado, 2017)","Alessandro José De Souza (Orientando de Doutorado 2016); Fernando Hilton Teixeira Ferreira (Orientando de Mestrado 2010); Humberto Araujo Da Silva (Orientando de Mestrado 2010); João Teixeira De Carvalho Neto (Orientando de Mestrado 2012); José Soares Batista Lopes (Orientando de Mestrado 2011)"
"André Laurindo Maitelli","Engenharias / Engenharia Elétrica","Universidade Federal Do Rio Grande Do Norte","DCA","Carlos Lisboa (Orientador de Mestrado, 1988); Takashi Yoneyama (Orientador de Doutorado, 1994)","Abenildo Alves De Oliveira (Orientando de Mestrado 2002); Aderson Jamier Santos Reis (Orientando de Mestrado 2009, Orientando de Doutorado 2015); Adhemar De Barros Fontes (Orientando de Doutorado 2002); Adjair Ferreira Barros Filho (Orientando de Mestrado 2002); Alessandro De Souza Lima (Orientando de Mestrado 2019); Alexandre Magnus Fernandes Guimarães (Orientando de Doutorado 2009 Co); Amanda Danielle Oliveira Da Silva Dantas (Orientando de Mestrado 2013 Co); Ana Carla Costa Andrade (Orientando de Mestrado 2015, Orientando de Doutorado 2021); Anderson Luiz De Oliveira Cavalcanti (Orientando de Mestrado 2003, Orientando de Doutorado 2008); André Felipe Oliveira De Azevedo Dantas (Orientando de Mestrado 2012, Orientando de Doutorado 2015); André Quintiliano Bezerra Silva (Orientando de Mestrado 2016); Andrew Vinícius Silva Moreira (Orientando de Mestrado 2019 Co); Anna Giselle Camara Dantas Ribeiro (Orientando de Mestrado 2011); Antônio Pereira De Araújo Junior (Orientando de Mestrado 2014); Auciomar Carlos Teixeira De Cerqueira (Orientando de Mestrado 2009); Bernardo Fonseca Andrade De Lima (Orientando de Mestrado 2019); Brenna Karolyna Dos Santos Silva (Orientando de Mestrado 2015); Carlos Deyvinson Reges Bessa (Orientando de Mestrado 2016, Orientando de Doutorado 2018); Carlos Eduardo Guimaraes De Lima (Orientando de Mestrado 2000); Daniel Guerra Vale Da Fonseca (Orientando de Mestrado 2012, Orientando de Doutorado 2019); Danielle Simone Da Silva Casillo (Orientando de Doutorado 2009); Danielson Flávio Xavier Da Silva (Orientando de Mestrado 2017); Danise Suzy Da Silva Oliveira (Orientando de Mestrado 2009); Diego De Araújo Moreira (Orientando de Mestrado 2012); Djanilton Fernandes Rego (Orientando de Mestrado 2002 Co); Eliara De Melo Medeiros (Orientando de Mestrado 2019); Emanoel Raimundo Queiroz Chaves Junior (Orientando de Doutorado 2019); Evellyne Da Silva Batista (Orientando de Mestrado 2009); Everton José De Castro Rego (Orientando de Mestrado 2017 Co); Ewerton Alexandre Pinheiro Moura (Orientando de Mestrado 2004); Fábio Araújo De Lima (Orientando de Mestrado 2011); Fábio Câmara Araújo De Carvalho (Orientando de Mestrado 1997); Felipe Emmanuel Ferreira De Castro (Orientando de Mestrado 2004 Co); Flavio Gentil De Araujo Filho (Orientando de Doutorado 2017); Francisco Canindé Holanda De Queiroz (Orientando de Mestrado 2008 Co); Francisco Elvis Carvalho Souza (Orientando de Mestrado 2006); Francisco Guerra Fernandes Júnior (Orientando de Mestrado 2005); Francisco José Targino Vidal (Orientando de Mestrado 2005 Co); Gabriel Bessa De Freitas Fuezi Oliva (Orientando de Mestrado 2017, Orientando de Doutorado 2021); Gabriell John Medeiros De Araujo (Orientando de Mestrado 2012); Gilbert Azevedo Da Silva (Orientando de Mestrado 1998, Orientando de Doutorado 2005); Hannah Lícia Cruz Galvão (Orientando de Mestrado 2016, Orientando de Doutorado 2022); Harlene Cristina Ambrósio Gomes Soares (Orientando de Mestrado 2019); Heitor Penalva Gomes (Orientando de Mestrado 2009); Helio Henrique Cunha Pinheiro (Orientando de Mestrado 2011); Humberto Araujo Da Silva (Orientando de Mestrado 2010 Co); Ícaro Bezerra Queiroz De Araújo (Orientando de Mestrado 2015); Jacimario Rego Da Silva (Orientando de Mestrado 1999 Co); Jacqueline Aparecida Araújo Barbosa (Orientando de Mestrado 2007); Jan Erik Mont Gomery Pinto (Orientando de Mestrado 2014, Orientando de Doutorado 2019)"
"Andrés Ortiz Salazar","Engenharias / Engenharia Elétrica","Universidade Federal Do Rio Grande Do Norte","DCA","Richard Magdalena Stephan (Orientador de Mestrado, 1989; Orientador de Doutorado, 1994)","A Alex Fabiano (Orientando de Mestrado 1997); Abenildo Alves De Oliveira (Orientando de Mestrado 2002 Co); Ademar De Barros Fontes (Orientando de Doutorado 2002 Co); Adjair Ferreira Barros Filho (Orientando de Mestrado 2002, Orientando de Doutorado 2017); Alan Cássio Queiroz Bezerra Leite (Orientando de Mestrado 2017); Alberto Soto Lock (Orientando de Pós-doutorado 2011); Alex Fabiano De Araújo Furtunato (Orientando de Mestrado 1997); Alexandre Magnus Fernandes Guimarães (Orientando de Mestrado 1997, Orientando de Doutorado 2009); Álvaro Medeiros Avelino (Orientando de Mestrado 2009); Anderson Eugênio Silva Da Costa (Orientando de Mestrado 2025); Arlindo Ricarte Primo Junior (Orientando de Mestrado 2002); Benno Waldemar Assmann (Orientando de Doutorado 2008); Carlo Frederico Pereira De Siqueira Campos (Orientando de Mestrado 2006); Carlos Yuri Ferreira Silva (Orientando de Mestrado 2019); Danielle Simone Da Silva Casillo (Orientando de Mestrado 2004); Diego Antonio De Moura Fonseca (Orientando de Doutorado 2018); Djanilton Fernandes Do Rego (Orientando de Mestrado 2002); Elmer Rolando Llanos Villarreal (Orientando de Pós-doutorado 2019); Evandro Ailson De Freitas Nunes (Orientando de Doutorado 2021); Fabiano Medeiros De Azevedo (Orientando de Mestrado 2009); Fábio Soares De Lima (Orientando de Mestrado 2004 Co); Fabricio Roosevelt Melo Da Silva (Orientando de Mestrado 2017); Felipe Denis Mendonça De Oliveira (Orientando de Mestrado 2009, Orientando de Doutorado 2015); Felipe Emmanuel Ferreira De Castro (Orientando de Mestrado 2004); Felipe Oliveira Simões Gama (Orientando de Mestrado 2017 Co, Orientando de Doutorado 2021); Filipe De Oliveira Quintaes (Orientando de Mestrado 2006, Orientando de Doutorado 2010); Flávio Gonçalves Dantas (Orientando de Mestrado 2011); Francisco Canindé Holanda De Queiroz (Orientando de Mestrado 2008); Francisco Elvis Carvalho Souza (Orientando de Doutorado 2017); Francisco José Targino Vidal (Orientando de Mestrado 2005); Geraldo De Moura Lacerda (Orientando de Mestrado 2009); Giancarlos Costa Barbosa (Orientando de Mestrado 2012); Glauco George Cipriano Maniçoba (Orientando de Mestrado 2013, Orientando de Doutorado 2018); Gustavo Fernandes De Lima (Orientando de Mestrado 2014, Orientando de Doutorado 2019); Ildefonso Martins Dos Santos (Orientando de Mestrado 2007 Co); Irlete Pereira Mota Alves (Orientando de Mestrado 2023); Jean Paul Dubut (Orientando de Mestrado 2000, Orientando de Doutorado 2010); Jefferson Doolan Fernandes (Orientando de Mestrado 2010, Orientando de Doutorado 2017); Jefferson Pereira Da Silva (Orientando de Mestrado 1998); João Batista Dolvim Dantas (Orientando de Mestrado 2006); João Coelho De Sousa Filho (Orientando de Mestrado 2011); João De Deus Freire De Araújo (Orientando de Mestrado 2009); João Teixeira De Carvalho Neto (Orientando de Doutorado 2016); Jose Alberto Diaz Amado (Orientando de Mestrado 2008, Orientando de Doutorado 2013); José Álvaro De Paiva (Orientando de Mestrado 1999, Orientando de Doutorado 2007); José Edenilson Oliveira Reges (Orientando de Doutorado 2016); José Soares Batista Lopes (Orientando de Doutorado 2016); Jossana Maria De Souza Ferreira (Orientando de Mestrado 2002, Orientando de Doutorado 2006); Jossana Maria Ferreira Souza (Orientando de Mestrado 2002); Luciano Pereira Dos Santos Júnior (Orientando de Mestrado 2009, Orientando de Doutorado 2017)"
"Carlos Eduardo Trabuco Dórea","Engenharias / Engenharia Elétrica","Universidade Federal Do Rio Grande Do Norte","DCA","Basilio Ernesto De Almeida Milani (Orientador de Mestrado, 1993); Jean Claude Hennet (Orientador de Doutorado, 1997)","Amanda Danielle Oliveira Da Silva Dantas (Orientando de Mestrado 2013, Orientando de Doutorado 2018); Ana Theresa Fernandes De Oliveira Mancini (Orientando de Mestrado 2021); Andreza Crystine Carvalho De Oliveira (Orientando de Mestrado 2020); Antonio Carlos Caldeira Pimenta (Orientando de Mestrado 2004); Armando Sanca Sanca (Orientando de Mestrado 2006 Co); Danilo Chaves De Sousa Ichihara (Orientando de Mestrado 2018); Eduardo José Lima Ii (Orientando de Mestrado 2002); Eduardo Nogueira Cunha (Orientando de Mestrado 2015); Evangivaldo Almeida Lima (Orientando de Mestrado 2002); Everton José De Castro Rego (Orientando de Mestrado 2017); Fábio Henrique De Carvalho Ferraz (Orientando de Mestrado 2022); Francisco Jadilson Dos Santos Silva (Orientando de Doutorado 2018 Co); Gaspar Fontineli Dantas Junior (Orientando de Mestrado 2014); Isaac Dantas Isidório (Orientando de Doutorado 2023); Jhonat Heberson Avelino De Souza (Orientando de Mestrado 2023); Joalbo Borges Santos (Orientando de Mestrado 2012 Co); Joao Gutemberg Barbosa De Farias Filho (Orientando de Mestrado 2016); João Ricardo Tavares Gadelha (Orientando de Mestrado 2019); José Ilton Sarmento Silveira Júnior (Orientando de Mestrado 2016, Orientando de Doutorado 2023); José Kleiton Ewerton Da Costa Martins (Orientando de Doutorado 2023); Jose Mario Araujo (Orientando de Doutorado 2011); Júlio César Lins Barreto Sobrinho (Orientando de Mestrado 2011); Leonardo Araújo Nunes (Orientando de Mestrado 2022); Leonardo Vale De Araujo (Orientando de Mestrado 2014 Co); Lorena Medeiros Santana (Orientando de Mestrado 2010 Co); Luiz André Pontarolo (Orientando de Mestrado 2019); Manoel De Oliveira Santos Sobrinho (Orientando de Doutorado 2013 Co); Márcio Ribeiro Da Silva Garcia (Orientando de Mestrado 2008 Co); Matheus Vítor De Andrade Pedrosa (Orientando de Mestrado 2018 Co); Milena De Albuquerque Moreira (Orientando de Mestrado 2007); Nelson Jose Bonfim Dantas (Orientando de Mestrado 2019, Orientando de Doutorado 2023); Nicholas De Bastos Melo (Orientando de Doutorado 2017); Nivaldo Ferreira Da Silva Junior (Orientando de Doutorado 2018 Co); Tiago Alves De Almeida (Orientando de Mestrado 2015, Orientando de Doutorado 2020)"
"Carlos Manuel Dias Viegas","Ciências Exatas e da Terra / Ciência Da Computação","Universidade Federal Do Rio Grande Do Norte","DCA","Francisco Vasques (Orientador de Doutorado, 2015); Luiz Affonso Henderson Guedes De Oliveira (Orientador de Mestrado, 2009); Paulo Portugal (Orientador de Doutorado, 2015 Co)",""
"Diogo Pinheiro Fernandes Pedrosa","Engenharias / Engenharia Elétrica","Universidade Federal Do Rio Grande Do Norte","DCA","Adelardo Adelino Dantas De Medeiros (Orientador de Mestrado, 2001; Orientador de Doutorado, 2006); Pablo Javier Alsina (Orientador de Mestrado, 2001 Co; Orientador de Doutorado, 2006 Co)",""
"Eduardo De Lucena Falcão","Ciências Exatas e da Terra / Ciência Da Computação","Universidade Federal Do Rio Grande Do Norte","DCA","Alexandre Nóbrega Duarte (Orientador de Mestrado, 2014); Andrey Elisio Monteiro Brito (Orientador de Doutorado, 2018 Co); Francisco Vilar Brasileiro (Orientador de Doutorado, 2018); Tiago Maritan Ugulino De Araújo (Orientador de Mestrado, 2014 Co)",""
"Fábio Meneghetti Ugulino De Araújo","Engenharias / Engenharia Elétrica","Universidade Federal Do Rio Grande Do Norte","DCA","Clivaldo Silva De Araújo (Orientador de Mestrado, 1998); Takashi Yoneyama (Orientador de Doutorado, 2002)","Alcemy Gabriel Vitor Severino (Orientando de Mestrado 2017, Orientando de Doutorado 2024); Andre Galvao De Araujo (Orientando de Mestrado 2019); André Henrique Matias Pires (Orientando de Mestrado 2017, Orientando de Doutorado 2023); André Luiz Aguiar Sousa (Orientando de Mestrado 2018); Brunna Santana De Vasconcellos Pinheiro (Orientando de Mestrado 2017); Carlos André Guerra Fonseca (Orientando de Mestrado 2005, Orientando de Doutorado 2012); Diogo Leite Rebouças (Orientando de Mestrado 2011); Emânuel Guerra De Barros Filho (Orientando de Mestrado 2012); Fabio Ricardo De Lima Souza (Orientando de Mestrado 2018); Ian Da Silva Vigano (Orientando de Mestrado 2021); Ícaro Bezerra Queiroz De Araújo (Orientando de Doutorado 2019); Jean Mário Moreira De Lima (Orientando de Mestrado 2018, Orientando de Doutorado 2021); Jobson Francisco Da Silva (Orientando de Mestrado 2012); José Kleber Costa De Oliveira (Orientando de Mestrado 2012); José Kleiton Ewerton Da Costa Martins (Orientando de Mestrado 2017, Orientando de Doutorado 2023 Co); José Medeiros De Araújo Júnior (Orientando de Mestrado 2007, Orientando de Doutorado 2014); Leandro Luttiane Da Silva Linhares (Orientando de Mestrado 2010, Orientando de Doutorado 2015); Marcílio De Paiva Onofre Filho (Orientando de Mestrado 2011); Márcio Emanuel Ugulino De Araújo Júnior (Orientando de Mestrado 2011); Marconi Camara Rodrigues (Orientando de Mestrado 2006, Orientando de Doutorado 2010); Maria Izabel Da Silva Guerra (Orientando de Doutorado 2022); Mário Sérgio Freitas Ferreira Cavalcante (Orientando de Mestrado 2017, Orientando de Doutorado 2023); Milton Medeiros Da Silva (Orientando de Mestrado 2013); Missilene Da Silva Farias (Orientando de Doutorado 2019); Pedro André Nogueira Souza De Oliveira Vale (Orientando de Mestrado 2018); Pedro Berretta De Lucena (Orientando de Mestrado 2005); Pedro Henrique De Medeiros Leite (Orientando de Mestrado 2021); Rafaelle De Aguiar Correia (Orientando de Mestrado 2012); Romênia Gurgel Vieira (Orientando de Doutorado 2021); Rosana Cibely Batista Rego (Orientando de Doutorado 2022); Willians Ribeiro Mendes (Orientando de Doutorado 2020)"
"Francisco Das Chagas Mota","Engenharias / Engenharia Elétrica","Universidade Federal Do Rio Grande Do Norte","DCA","Amit Bhaya (Orientador de Mestrado, 1990; Orientador de Doutorado, 1995)","Caio Dorneles Cunha (Orientando de Mestrado 2001 Co, Orientando de Doutorado 2008 Co); Fernando Cesar De Miranda (Orientando de Doutorado 2013); Glauberto Leilson Alves De Albuquerque (Orientando de Mestrado 2009); José Marcelo Lima Duarte (Orientando de Mestrado 2007); Plinio Altoe Costa Vieira (Orientando de Mestrado 2009); Renato Eduardo Farias De Sousa (Orientando de Mestrado 2004 Co); Sérgio José Gonçalves E Silva (Orientando de Mestrado 2007); Tullio Emmanuel Messias Raposo (Orientando de Mestrado 2011)"
"Carlos Alberto V. G. De Carvalho","Ciências Exatas e da Terra / Ciência Da Computação","Universidade Federal Rural de Pernambuco","DCA","Geber De Melo Ramalho (Orientador de Mestrado, 1994); Yves Demazeau (Orientador de Doutorado, 1999)","Alexandre Augusto De Lima Rodrigues (Orientando de Mestrado 2008, Orientando de Doutorado 2012); Alyne Ribeiro De Araújo (Orientando de Doutorado 2021); Antonio Vinicius De Oliveira Oliveira (Orientando de Mestrado 2020); Augusto César Vieira De Santana (Orientando de Mestrado 2011, Orientando de Doutorado 2017); Caio Eduardo De Melo Corréa (Orientando de Mestrado 2018); Carlos Eduardo Barbosa (Orientando de Mestrado 2002); Dacyr De Assis Gatto (Orientando de Doutorado 2021); Daniel Cunha De Andrade (Orientando de Mestrado 2008, Orientando de Doutorado 2016); Diego Marcon Farias (Orientando de Mestrado 2007); Diogo Ferreira De Lima Melo (Orientando de Mestrado 2013); Diogo Lima De Oliveira (Orientando de Doutorado 2018); Felippe Souto Gouvea (Orientando de Mestrado 2011); Gustavo Henrique Rodrigues Pinto De Queiroz (Orientando de Mestrado 2009, Orientando de Doutorado 2012); Jeferson Marques De Araujo (Orientando de Mestrado 2016); Jefferson De Souza Dantas (Orientando de Mestrado 2012); João Almeida E Silva (Orientando de Doutorado 2015); Leonardo Cunha De Miranda (Orientando de Mestrado 2005); Luciana Oliveira De Araujo (Orientando de Mestrado 2015); Luiz Carlos Firmino (Orientando de Doutorado 2010); Magno Leite De Farias (Orientando de Mestrado 2005); Marcus Vinicius Dos Santos De Oliveira (Orientando de Mestrado 2010, Orientando de Doutorado 2015); Nathalia Neves Lins De Oliveira (Orientando de Mestrado 2015); Patrícia D. L. Machado (Orientando de Doutorado 2004); Paulo Ricardo Dos Santos (Orientando de Mestrado 2006); Rafael Gonçalves De Lima (Orientando de Mestrado 2006)"
"Ivanovitch Medeiros Dantas Da Silva","Engenharias / Engenharia Elétrica","Universidade Federal Do Rio Grande Do Norte","DCA","Luiz Affonso Henderson Guedes De Oliveira (Orientador de Mestrado, 2008; Orientador de Doutorado, 2013); Paulo Portugal (Orientador de Doutorado 2013 Co)","Aguinaldo Bezerra Batista Júnior (Orientando de Doutorado 2021); Alexandre Henrique Soares Dias (Orientando de Mestrado 2023); Anderson Costa Silva Dos Santos (Orientando de Mestrado 2015); Artejose Revoredo Da Silva (Orientando de Mestrado 2016 Co); Breno Santana Santos (Orientando de Doutorado 2023); Cephas Alves Da Silveira Barreto (Orientando de Mestrado 2018 Co); Daniel Enos Cavalcanti Rodrigues De Macedo (Orientando de Mestrado 2014 Co); Danielle Brito Marques (Orientando de Mestrado 2015); Elvis Medeiros De Melo (Orientando de Doutorado 2023); Eridenes Fernandes De Queiroz (Orientando de Mestrado 2015 Co); Gabriel Lucas Albuquerque Maia Signoretti (Orientando de Mestrado 2021); Gilles Velleneuve Trindade Silvano (Orientando de Mestrado 2017; Orientando de Doutorado 2020); Gisliany Lillian Alves De Oliveira (Orientando de Mestrado 2020); Guilherme Pereira Marchioro Bertelli (Orientando de Mestrado 2017); Hagi Jakobson Dantas Da Costa (Orientando de Mestrado 2024); Hilário José Silveira Castro (Orientando de Mestrado 2018); Israel Eduardo De Barros Filho (Orientando de Doutorado 2020); Jordão Paulino Cassiano Da Silva (Orientando de Mestrado 2023); Júlio César Melo Gomes De Oliveira (Orientando de Mestrado 2017); Marianne Batista Diniz Da Silva (Orientando de Doutorado 2022); Pedro Henrique Meira De Andrade (Orientando de Doutorado 2024); Rute Souza De Abreu (Orientando de Doutorado 2024); Silvan Ferreira Da Silva Junior (Orientando de Mestrado 2020 Co); Thiago Medeiros Barros (Orientando de Doutorado 2021 Co); Tomaz Filgueira Nunes (Orientando de Mestrado 2018 Co)"
"José Ivonildo Do Rêgo","Engenharias / Engenharia Elétrica","Universidade Federal Do Rio Grande Do Norte","DCA","Liu Hsu (Orientador de Doutorado, 1982); Shankar P Bhattacharyya (Orientador de Mestrado, 1977)",""
"Luiz Affonso Henderson Guedes De Oliveira","Engenharias / Engenharia Elétrica","Universidade Federal Do Rio Grande Do Norte","DCA","Elder Moreira Hemerly (Orientador de Mestrado, 1991); Eleri Cardozo (Orientador de Doutorado, 1999)","Aderson Cleber Pifer (Orientando de Mestrado 2006; Orientando de Doutorado 2011); Alessandro José De Souza (Orientando de Mestrado 2005); Allan Robson Silva Venceslau (Orientando de Mestrado 2012); Amanda Lucena Germano (Orientando de Mestrado 2017); Ana Claudia Da Silva Gomes (Orientando de Mestrado 2002); Andre Lucena De Almeida (Orientando de Mestrado 2010); Andressa Stefany Oliveira (Orientando de Mestrado 2021); Andreya Prestes Da Silva (Orientando de Mestrado 2002 Co); Beatriz Soares De Souza (Orientando de Mestrado 2024); Bianchi Serique Meiguins (Orientando de Doutorado 2003); Breno Serique Meiguins (Orientando de Mestrado 2002); Bruno Sielly Jales Costa (Orientando de Mestrado 2009; Orientando de Doutorado 2014); Carlos Manuel Dias Viegas (Orientando de Mestrado 2009); Cicero Josean Mateus Nunes Da Silva (Orientando de Mestrado 2021); Clauber Gomes Bezerra (Orientando de Doutorado 2017); Daniel Enos Cavalcanti Rodrigues De Macedo (Orientando de Mestrado 2014); Daniel Gouveia Costa (Orientando de Doutorado 2013); Deivison Luan Xavier Silva (Orientando de Mestrado 2024); Diego Rodrigo Cabral Silva (Orientando de Mestrado 2005 Co; Orientando de Doutorado 2008); Edson Jackson De Medeiros Neto (Orientando de Mestrado 2015); Eduardo Augusto Morais Rodrigues (Orientando de Mestrado 2021); Eliane Cristina Flexa Duarte (Orientando de Mestrado 2006); Elionai Gomes De Almeida Sobrinho (Orientando de Mestrado 2002); Emerson Vilar De Oliveira (Orientando de Mestrado 2020); Erico Meneses Leão (Orientando de Mestrado 2007); Fábio Soares De Lima (Orientando de Mestrado 2004; Orientando de Doutorado 2014); Felipe César Alves Do Couto (Orientando de Mestrado 2009); Glaucio Haroldo Silva De Carvalho (Orientando de Mestrado 2001 Co); Gustavo Bezerra Paz Leitão (Orientando de Mestrado 2008; Orientando de Doutorado 2018); Ivanovitch Medeiros Dantas Da Silva (Orientando de Mestrado 2008; Orientando de Doutorado 2013); Jackson Da Cruz Costa (Orientando de Mestrado 2022); Jasmine Priscyla Leite De Araujo (Orientando de Mestrado 2002); Johnny Marcus Gomes Rocha (Orientando de Mestrado 2003); Jorge Eider Florentino Da Silva (Orientando de Mestrado 2015); José Reinaldo Barbosa De Moraes (Orientando de Mestrado 2002); Juliano Rafael Sena De Araújo (Orientando de Mestrado 2011); Mailson Ribeiro Santos (Orientando de Mestrado 2021; Orientando de Doutorado 2024); Marcelo Henrique Ramalho Nobre (Orientando de Mestrado 2011; Orientando de Doutorado 2015); Marcos Cesar Madruga Alves Pinheiro (Orientando de Doutorado 2006 Co); Marlos André Marques Simões De Oliveira (Orientando de Doutorado 2010); Paulo Victor Queiroz Correia (Orientando de Mestrado 2021); Rafael Heider Barros Feijó (Orientando de Mestrado 2007); Raimundo Santos Moura (Orientando de Doutorado 2009); Raimundo Viégas Junior (Orientando de Mestrado 2002; Orientando de Doutorado 2010); Raphaela Galhardo Fernandes Lima (Orientando de Mestrado 2007; Orientando de Doutorado 2014); Rejane De Barros Araujo (Orientando de Mestrado 2003); Ricardo Alexsandro De Medeiros Valentim (Orientando de Mestrado 2006; Orientando de Doutorado 2008); Rivaldo Rodrigues Machado Júnior (Orientando de Mestrado 2013); Rute Souza De Abreu (Orientando de Mestrado 2018); Silvano Carlos Lopes Junior (Orientando de Mestrado 2024)"
"Luiz Felipe De Queiroz Silveira","Engenharias / Engenharia Elétrica","Universidade Federal Do Rio Grande Do Norte","DCA","Ernesto Leite Pinto (Orientador de Doutorado 2006 Co); Francisco Marcos De Assis (Orientador de Mestrado, 2002; Orientador de Doutorado, 2006)","Alex Carlos Rodrigues Alves (Orientando de Doutorado 2025); Aluisio Igor Rego Fontes (Orientando de Mestrado 2012; Orientando de Doutorado 2015); Antonio Alcir De Freitas Junior (Orientando de Mestrado 2024); Arthur Diego De Lira Lima (Orientando de Mestrado 2014); Carlos Avelino De Barros (Orientando de Doutorado 2016 Co); Cassiano Perin De Carvalho (Orientando de Mestrado 2022 Co); Eduardo Nunes Velloso (Orientando de Mestrado 2024); Felipe Oliveira Simões Gama (Orientando de Mestrado 2017; Orientando de Doutorado 2021 Co); Francisco Sales De Lima Filho (Orientando de Doutorado 2019); Frankelene Pinheiro De Souza (Orientando de Mestrado 2017); Frederico Augusto Fernandes Silveira (Orientando de Mestrado 2020); Hugo Rafael Gonçalves Cavalcante (Orientando de Mestrado 2018); Igor Gadelha Pereira (Orientando de Doutorado 2019); Lucas Costa Pereira Cavalcante (Orientando de Mestrado 2014); Pedro Thiago Valério De Souza (Orientando de Mestrado 2017; Orientando de Doutorado 2020); Tadeu Ferreira Oliveira (Orientando de Doutorado 2021); Tales Vinícius Rodrigues De Oliveira Câmara (Orientando de Doutorado 2020); Talles Rodrigues Ferreira (Orientando de Mestrado 2009 Co); Vinícius Sousa De Oliveira (Orientando de Mestrado 2021 Co); Vítor Saraiva Ramos (Orientando de Mestrado 2021); Yuri Pedro Dos Santos (Orientando de Mestrado 2019; Orientando de Doutorado 2023)"
"Luiz Marcos Garcia Goncalves","Ciências Exatas e da Terra / Ciência Da Computação","Universidade Federal Do Rio Grande Do Norte","DCA","Antonio Alberto Fernandes De Oliveira (Orientador de Mestrado, 1995; Orientador de Doutorado, 1999); Roderic Allan Grupen (Orientador de Doutorado 1999 Co)","Alessandro Assi Marro (Orientando de Mestrado 2012); Alexandre José Braga Da Silva (Orientando de Mestrado 2014 Co); Alexandre Jose Da Silva Braga (Orientando de Mestrado 2014 Co); Alexsandra Oliveira Andrade (Orientando de Pós-Doutorado 2018); Álvaro Pinto Fernandes De Negreiros (Orientando de Mestrado 2019; Orientando de Doutorado 2023); Alysson Nascimento De Lucena (Orientando de Doutorado 2022; Orientando de Pós-Doutorado 2023); Alzira Ferreira Da Silva (Orientando de Doutorado 2009); Anderson Abner De Santana Souza (Orientando de Mestrado 2008; Orientando de Doutorado 2012; Orientando de Pós-Doutorado 2017); Andouglas Gonçalves Da Silva Júnior (Orientando de Mestrado 2015; Orientando de Doutorado 2021); André Paulo Dantas De Araújo (Orientando de Mestrado 2022 Co); Anna Giselle Camara Dantas Ribeiro (Orientando de Pós-Doutorado 2017); Antônio Péricles Bonfim Saraiva De Oliveira (Orientando de Mestrado 2012); Aquiles Medeiros Filgueira Burlamaqui (Orientando de Doutorado 2008); Arthur Andrade Bezerra (Orientando de Mestrado 2022); Bruno Marques Ferreira Da Silva (Orientando de Mestrado 2011; Orientando de Doutorado 2015); Carla Da Costa Fernandes (Orientando de Pós-Doutorado 2018); Carla Da Costa Fernandes Curvelo (Orientando de Mestrado 2013; Orientando de Doutorado 2017); Carlos Magno De Lima (Orientando de Doutorado 2005); Cassiano Perin De Carvalho (Orientando de Mestrado 2022); Davi Henrique Dos Santos (Orientando de Mestrado 2016; Orientando de Doutorado 2020; Orientando de Pós-Doutorado 2022); Denilton Silveira De Oliveira (Orientando de Mestrado 2019 Co; Orientando de Doutorado 2022 Co); Dennis Barrios Aranibar (Orientando de Doutorado 2009; Orientando de Pós-Doutorado 2019); Diego Ramon Bezerra Da Silva (Orientando de Doutorado 2024); Douglas Machado Tavares (Orientando de Mestrado 2004); Dunfrey Pires Aragão (Orientando de Doutorado 2024); Einstein Gomes Dos Santos (Orientando de Mestrado 2014); Elizabeth Viviana Cabrera Avila (Orientando de Mestrado 2017; Orientando de Doutorado 2022); Emerson Vilar De Oliveira (Orientando de Doutorado 2024); Erika Akemi Yanaguibashi Albuquerque (Orientando de Mestrado 2021); Francinaldo De Almeida Pereira (Orientando de Mestrado 2023); George Christian Basilio Tho (Orientando de Mestrado 2005); Gianna Rodrigues De Araújo (Orientando de Mestrado 2010); Harold Ivan Angulo Bustos (Orientando de Pós-Doutorado 2003); Ícaro Lins Leitão Da Cunha (Orientando de Doutorado 2014); Igor Gadelha Pereira (Orientando de Doutorado 2019 Co; Orientando de Pós-Doutorado 2021); Igor Pinheiro Lagreca De Sales Cabral (Orientando de Mestrado 2006; Orientando de Doutorado 2008); Italo De Oliveira Matias (Orientando de Mestrado 2001 Co); João Carlos Xavier Júnior (Orientando de Doutorado 2012); João Moreno Vilas Boas De Souza Silva (Orientando de Pós-Doutorado 2016); João Paulo De Araújo Bezerra (Orientando de Mestrado 2007); Jordan Jusbig Salas Cuno (Orientando de Doutorado 2024 Co); Joris Michel Gérard Daniel Guérin (Orientando de Pós-Doutorado 2020); Jose Mario Araujo (Orientando de Pós-Doutorado 2016); José Wanderson Oliveira Silva (Orientando de Doutorado 2023); Justo Emilio Alvarez Jacobo (Orientando de Pós-Doutorado 2017); Kerolayne Paiva Soares (Orientando de Doutorado 2017 Co); Kliger Kissinger Fernandes Rocha (Orientando de Mestrado 2005); Leizza Ferreira Rodrigues (Orientando de Mestrado 2002 Co); Leonardo Angelo Virgínio De Souto (Orientando de Doutorado 2020); Leonardo Campos Do Amaral Bezerra (Orientando de Mestrado 2004)"
"Manoel Firmino De Medeiros Júnior","Engenharias / Engenharia Elétrica","Universidade Federal Do Rio Grande Do Norte","DCA","Drumond Xavier Cavalcanti (Orientador de Mestrado, 1979); Hans Juergen Koglin (Orientador de Doutorado, 1987)","Arrhenius Vinicius Da Costa Oliveira (Orientando de Mestrado 2003 Co; Orientando de Doutorado 2011); Arthur Salgado De Medeiros (Orientando de Mestrado 2012; Orientando de Doutorado 2020); Aylanna Raquel Da Costa Oliveira (Orientando de Mestrado 2013; Orientando de Doutorado 2019); Bezaliel Albuquerque Da Silva Pires (Orientando de Mestrado 2011); Clóvis Bôsco Mendonça Oliveira (Orientando de Mestrado 2006; Orientando de Doutorado 2010); Crisluci Karina Souza Santos (Orientando de Mestrado 2004; Orientando de Doutorado 2008); Crisluci Karina Souza Santos Cândido (Orientando de Mestrado 2004; Orientando de Doutorado 2008); Delson Alves Da Costa (Orientando de Mestrado 2016 Co); Diego Deyvid Dantas De Medeiros (Orientando de Mestrado 2015); Ednardo Pereira Da Rocha (Orientando de Doutorado 2020); Francisco De Assis Ferreira Matias (Orientando de Mestrado 2007 Co); Gileno Jose De Vasconcelos Villar (Orientando de Mestrado 1997); Hudson Da Silva Resende (Orientando de Mestrado 2016); Joaz Santana Praxedes (Orientando de Mestrado 1999); Jonatha Revoredo Leite Da Fonseca (Orientando de Doutorado 2023); José Adriano Da Costa (Orientando de Mestrado 2002); José Alberto Nicolau De Oliveira (Orientando de Doutorado 2007); Jose Luiz Da Silva Junior (Orientando de Doutorado 2012); Joselia Dos Anjos Lucas (Orientando de Mestrado 2001); Juliano Costa Leal Da Silva (Orientando de Doutorado 2021); Marcos Antonio Dias De Almeida (Orientando de Doutorado 2003); Max Chianca Pimentel Filho (Orientando de Mestrado 1997; Orientando de Doutorado 2005); Melinda Cesianara Silva Da Cruz (Orientando de Mestrado 2010; Orientando de Doutorado 2015); Paulo Cesar De Souza Camara (Orientando de Mestrado 2002); Rafaela Vilela Franca (Orientando de Mestrado 2010); Roana D Ávila Souza Monteiro (Orientando de Doutorado 2021); Rodrigo Augusto Do Nascimento Gomes (Orientando de Mestrado 2016); Rogério Nicolau Dos Santos (Orientando de Mestrado 2001); Romilson Do Nascimento Barros (Orientando de Mestrado 1996); Rômulo Alves De Oliveira (Orientando de Doutorado 2015); Thales Augusto De Oliveira Ramos (Orientando de Mestrado 2011; Orientando de Doutorado 2020)"
"Marcelo Augusto Costa Fernandes","Engenharias / Engenharia Elétrica","Universidade Federal Do Rio Grande Do Norte","DCA","Adrião Duarte Dória Neto (Orientador de Mestrado, 1998); Dalton Soares Arantes (Orientador de Doutorado, 2010); Joao Batista Bezerra (Orientador de Mestrado 1999 Co)","Atila Varela Ferreira Medeiros De Oliveira (Orientando de Mestrado 2015); Caio José Borba Vilar Guimarães (Orientando de Mestrado 2020); Carlos Eduardo De Barros Santos Júnior (Orientando de Mestrado 2018; Orientando de Doutorado 2024); Caroline Albuquerque Dantas Silva (Orientando de Mestrado 2016; Orientando de Doutorado 2021); Daniel Holanda Noronha (Orientando de Mestrado 2017); Denis Ricardo Da Silva Medeiros (Orientando de Mestrado 2020); Emanoel Lucas Rodrigues Costa (Orientando de Mestrado 2022); Fabio Fonseca De Oliveira (Orientando de Doutorado 2024); Felipe Fernandes Lopes (Orientando de Mestrado 2021); Gabriel Bezerra Motta Câmara (Orientando de Doutorado 2024); Heberht Antonio Silva Dias (Orientando de Mestrado 2023); Jackson Gomes De Souza (Orientando de Doutorado 2024); Jampierre Vieira Rocha (Orientando de Doutorado 2024); José Cláudio Vieira E Silva Junior (Orientando de Doutorado 2020); Karolayne Santos De Azevedo (Orientando de Mestrado 2022); Leonardo Alves Dias (Orientando de Doutorado 2020); Lucileide Medeiros Dantas Da Silva (Orientando de Mestrado 2016; Orientando de Doutorado 2023; Orientando de Pós-Doutorado 2023); Luisa Christina De Souza (Orientando de Mestrado 2022); Marcio Luiz Bezerra Lopes Junior (Orientando de Mestrado 2022); Maria Gracielly Fernandes Coutinho (Orientando de Mestrado 2019; Orientando de Doutorado 2023); Mateus Arnaud Santos De Sousa Goldbarg (Orientando de Mestrado 2023); Matheus Fernandes Torquato (Orientando de Mestrado 2017); Náthalee Cavalcanti De Almeida Lima (Orientando de Doutorado 2015 Co); Pedro Victor Andrade Alves (Orientando de Mestrado 2023); Sérgio Natan Silva (Orientando de Mestrado 2016; Orientando de Doutorado 2021; Orientando de Pós-Doutorado 2023); Tiago Fernando Barbosa De Sousa (Orientando de Mestrado 2013; Orientando de Doutorado 2019); Wysterlânya Kyury Pereira Barros (Orientando de Mestrado 2021)"
"Pablo Javier Alsina","Engenharias / Engenharia Elétrica","Universidade Federal Do Rio Grande Do Norte","DCA","Narpat Singh Gehlot (Orientador de Mestrado, 1991; Orientador de Doutorado, 1996)","Adriano De Andrade Bresolin (Orientando de Doutorado 2008 Co); Alexandre Bezerra Viana (Orientando de Mestrado 1998 Co); Algeir Prazeres Sampaio (Orientando de Mestrado 1999 Co); Allan Aminadab André Freire Soares (Orientando de Mestrado 2004); Alysson Paulo Holanda Lima (Orientando de Mestrado 2024); Anfranserai Morais Dias (Orientando de Mestrado 2002; Orientando de Doutorado 2007); Armando Sanca Sanca (Orientando de Doutorado 2013); Clauber Gomes Bezerra (Orientando de Mestrado 2004); Cristiany De Nazaré Moscoso Do Amaral Ferreira (Orientando de Mestrado 1999 Co); Daniel Henrique Silva Fernandes (Orientando de Mestrado 2019); Daniel Silva De Morais (Orientando de Mestrado 2024); Dennis Barrios Aranibar (Orientando de Mestrado 2005); Deyvid Lucas Leite (Orientando de Mestrado 2019); Diego Antonio De Moura Fonseca (Orientando de Mestrado 2011); Diego Da Silva Pereira (Orientando de Doutorado 2023); Diogo Pinheiro Fernandes Pedrosa (Orientando de Mestrado 2001 Co; Orientando de Doutorado 2006 Co); Esdras Ferreira Sales Júnior (Orientando de Mestrado 1997 Co); Filipe Campos De Alcantara Lins (Orientando de Doutorado 2023); Frederico Carvalho Vieira (Orientando de Mestrado 2005); Guilherme Leal Santos (Orientando de Mestrado 2010); Ivo Alves De Oliveira Neto (Orientando de Mestrado 2013); Jaime Barros Filho (Orientando de Mestrado 2002); Joao Maria Araujo Do Nascimento (Orientando de Mestrado 2005); José Aniceto Duarte Costa (Orientando de Mestrado 2012); Jose Savio Alves De Sousa Segundo (Orientando de Mestrado 2007); Kaiser Magalde Costa Magalhaes (Orientando de Mestrado 2003 Co); Kassio Janielson Da Silva Eugenio (Orientando de Mestrado 2018); Kelson Romulo Teixeira Aires (Orientando de Mestrado 2001); Luís Bruno Pereira Do Nascimento (Orientando de Doutorado 2021); Marcelo Minicuci Yamamoto (Orientando de Mestrado 2005 Co); Márcio Valério De Araújo (Orientando de Mestrado 2010; Orientando de Doutorado 2015); Mauricio Rabello Silva (Orientando de Mestrado 2017; Orientando de Doutorado 2024); Nicholas De Bastos Melo (Orientando de Doutorado 2017 Co); Osmar De Araujo Dourado Junior (Orientando de Doutorado 2011 Co); Patricia Nishimura Guerra (Orientando de Mestrado 2005); Rodrigo Pereira Bandeira (Orientando de Mestrado 2002 Co); Samaherni Morais Dias (Orientando de Mestrado 2007 Co; Orientando de Doutorado 2010 Co); Tania Luna Laura (Orientando de Doutorado 2013); Vitor Gaboardi Dos Santos (Orientando de Mestrado 2020); Yuri Sarmento Silveira (Orientando de Mestrado 2017)"
"Paulo Sergio Da Motta Pires","Engenharias / Engenharia Elétrica","Depto Eng Computacao","DCA","Attilio Jose Giarola (Orientador de Doutorado, 1986); David Anthony Rogers (Orientador de Mestrado, 1980); Rui Fragassi Souza (Orientador de Doutorado 1986 Co)","Aguinaldo Bezerra Batista Júnior (Orientando de Mestrado 2009); Flavio Marcelo Cavalcante Bandeira Do Amaral (Orientando de Mestrado 2002); João Paulo De Souza Medeiros (Orientando de Doutorado 2013); Miriam Valenca Massud (Orientando de Mestrado 2005); Teobaldo Adelino Dantas De Medeiros (Orientando de Mestrado 2005); Tiago Hiroshi Kobayashi (Orientando de Mestrado 2009)"
"Ricardo Ferreira Pinheiro","Engenharias / Engenharia Elétrica","Universidade Federal Do Rio Grande Do Norte","DCA","Antonio Marcus Nogueira Lima (Orientador de Doutorado, 2001); Cursino Brandão Jacobina (Orientador de Doutorado, 2001); Jose Carlos De Oliveira (Orientador de Mestrado, 1980)","Aldrin Bezerra Dias (Orientando de Mestrado 2018); Ariel Sullivan Lins Patriota (Orientando de Mestrado 2020); Delson Alves Da Costa (Orientando de Mestrado 2016); Francisco David Mota Silva (Orientando de Mestrado 2018); Joale De Carvalho Pereira (Orientando de Mestrado 2018); Leandro Alves Ribeiro Da Silva (Orientando de Mestrado 2016); Lorena Maria Morais Fernandes Coelho (Orientando de Mestrado 2023); Paulo Vitor Silva (Orientando de Mestrado 2010; Orientando de Doutorado 2015); Ricardo Barros De Mendonca (Orientando de Mestrado 2007)"
"Samuel Xavier De Souza","Ciências Exatas e da Terra / Ciência Da Computação","Universidade Federal Do Rio Grande Do Norte","DCA","Johan Suykens (Orientador de Doutorado, 2007)","Alex Fabiano De Araújo Furtunato (Orientando de Doutorado 2021); Anderson Braulio Nobrega Da Silva (Orientando de Mestrado 2013); Carla Dos Santos Santana (Orientando de Mestrado 2020); Carlos Avelino De Barros (Orientando de Doutorado 2016); Demetrios Araújo Magalhães Coutinho (Orientando de Mestrado 2014; Orientando de Doutorado 2021); Desnes Augusto Nunes Do Rosário (Orientando de Mestrado 2012); Disraelly Hander Gurgel Pereira (Orientando de Doutorado 2014); Fabricio Costa Silva (Orientando de Mestrado 2015); Francisco Ary Alves De Souza (Orientando de Mestrado 2012); Hugo Rafael Gonçalves Cavalcante (Orientando de Mestrado 2018 Co); Igor Macedo Silva (Orientando de Mestrado 2021); Íria Caline Saraiva Cosme (Orientando de Doutorado 2018); Ítalo Augusto Souza De Assis (Orientando de Mestrado 2015; Orientando de Doutorado 2019; Orientando de Pós-Doutorado 2021); João Batista Fernandes (Orientando de Mestrado 2020); Julio Gustavo Soares Firmo Da Costa (Orientando de Mestrado 2020); Kayo Gonçalves E Silva (Orientando de Mestrado 2013; Orientando de Doutorado 2018); Lucas Costa Pereira Cavalcante (Orientando de Pós-Doutorado 2017); Raffael Sadite Cordoville Gomes De Lima (Orientando de Mestrado 2021); Reinaldo Agostinho De Souza Filho (Orientando de Mestrado 2022); Roger Rommel Ferreira De Araújo (Orientando de Mestrado 2016; Orientando de Doutorado 2021); Tiago Tavares Leite Barros (Orientando de Pós-Doutorado 2018); Victor Hugo Freitas De Oliveira (Orientando de Mestrado 2019); Vitor Hugo Mickus Rodrigues (Orientando de Mestrado 2020)"
"Sebastian Yuri Cavalcanti Catunda","Engenharias / Engenharia Elétrica","Universidade Federal Do Rio Grande Do Norte","DCA","Gurdip Singh Deep (Orientador de Mestrado, 1996; Orientador de Doutorado, 2000); Raimundo Carlos Silvério Freire (Orientador de Mestrado 1996 Co; Orientador de Doutorado 2000 Co)","Adriana Guimarães Costa (Orientando de Mestrado 2002 Co); Andrea Fagundes Ferreira (Orientando de Mestrado 2002 Co); Antonio Wallace Antunes Soares (Orientando de Doutorado 2018); Bernardo Nogueira Neto (Orientando de Mestrado 2010 Co); Bruno Augusto Ferreira Vitorino (Orientando de Doutorado 2018); Carlos Antonio Mendes Da Costa Júnior (Orientando de Mestrado 2014); Carlos Cesar Texeira Ferreira (Orientando de Mestrado 2004 Co); Catherine Pancotto (Orientando de Mestrado 2017 Co); Diomadson Rodrigues Belfort (Orientando de Mestrado 2007; Orientando de Pós-Doutorado 2014); Eridenes Fernandes De Queiroz (Orientando de Mestrado 2015); Evandro De Carvalho Gomes (Orientando de Mestrado 2009 Co); Evandson Claude Seabra Dantas (Orientando de Doutorado 2022); Francisco Jadilson Dos Santos Silva (Orientando de Mestrado 2011; Orientando de Doutorado 2018); Freud Sebastian Bach Carvalho Lima (Orientando de Mestrado 2011); Giselia Andrea Lopes Pinheiro Sousa (Orientando de Mestrado 2004); Guilherme Augusto Limeira Araujo (Orientando de Doutorado 2007 Co); Heraldo Antunes Silva Filho (Orientando de Doutorado 2014 Co); Icaro Gonzales Da Silva (Orientando de Mestrado 2015 Co); Icaro Gonzalez Da Silva Brito (Orientando de Mestrado 2015 Co); Jaderson Pereira Oliveira (Orientando de Mestrado 2006); José Batista De Sales Filho (Orientando de Mestrado 2016 Co); José Igor Santos De Oliveira (Orientando de Mestrado 2005); Juan Moises Mauricio Villanueva (Orientando de Mestrado 2005; Orientando de Doutorado 2009 Co); Leonardo Vale De Araujo (Orientando de Mestrado 2014); Luis Hermano Casado De Lima Junior (Orientando de Mestrado 2003 Co); Marcia Maria Moreira Viana (Orientando de Mestrado 2010); Mauro Sergio Silva Pinto (Orientando de Mestrado 2006); Michel Santana De Deus (Orientando de Mestrado 2014; Orientando de Doutorado 2023); Michel Valenca Gabriel (Orientando de Mestrado 2004); Paulo Rannier Costa Da Silva (Orientando de Mestrado 2022); Pedro Augusto Lopes Abreu (Orientando de Mestrado 2011); Petrov Crescencio Lobo (Orientando de Mestrado 2015 Co); Rafael Ferreira Alves De Assis (Orientando de Mestrado 2018); Rafael Oliveira Nunes (Orientando de Mestrado 2010); Ricardo Rodrigues Robson (Orientando de Mestrado 2007 Co); Shirlen Viana Leal (Orientando de Mestrado 2010); Thiago Brito Bezerra (Orientando de Mestrado 2012); Verônica Maria Lima Silva (Orientando de Mestrado 2014 Co); Will Ribamar Mendes Almeida (Orientando de Mestrado 2004; Orientando de Doutorado 2009 Co)"
"Tiago Tavares Leite Barros","Engenharias / Engenharia Elétrica","Universidade Federal Do Rio Grande Do Norte","DCA","Renato Da Rocha Lopes (Orientador de Mestrado, 2012; Orientador de Doutorado, 2018); Samuel Xavier De Souza (Supervisor de Pós-Doutorado, 2018)","Joao Batista Fernandes (Orientando de Mestrado 2020 Co); Tainá Souza (Orientando de Mestrado 2021 Co)"
"""

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


# Função para parsear os detalhes da string de orientação (CORRIGIDA)
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

    # --- CORREÇÃO: Lógica reordenada e alterada para if/elif para evitar duplicidade ---
    # Primeiro, procuramos pelo termo mais específico: "pós-doutorado".
    pos_doc_info = re.search(r"(?:pós-doutorado|pos-doutorado|pós doc)\s*(?:,\s*)?(\d{4})?", details_str_lower)
    if pos_doc_info:
        year_pd = pos_doc_info.group(1) if pos_doc_info.group(1) else "N/A"
        parsed_orientations.append({'type': "Pós-Doutorado", 'year': year_pd, 'co': is_co_global})

    # Se não for pós-doc, verificamos por "doutorado".
    elif re.search(r"doutorado\s*(?:,\s*)?(\d{4})?", details_str_lower):
        doutorado_info = re.search(r"doutorado\s*(?:,\s*)?(\d{4})?", details_str_lower)
        year_d = doutorado_info.group(1) if doutorado_info.group(1) else "N/A"
        parsed_orientations.append({'type': "Doutorado", 'year': year_d, 'co': is_co_global})

    # Se não for nenhum dos anteriores, verificamos por "mestrado".
    elif re.search(r"mestrado\s*(?:,\s*)?(\d{4})?", details_str_lower):
        mestrado_info = re.search(r"mestrado\s*(?:,\s*)?(\d{4})?", details_str_lower)
        year_m = mestrado_info.group(1) if mestrado_info.group(1) else "N/A"
        parsed_orientations.append({'type': "Mestrado", 'year': year_m, 'co': is_co_global})
    # --- FIM DA CORREÇÃO ---


    # Fallback se nenhum match explícito for encontrado (também ajustado para if/elif)
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
            current_types_in_list = [o['type'] for o in parsed_orientations]
            if degree_type_fallback not in current_types_in_list:
                 parsed_orientations.append({'type': degree_type_fallback, 'year': year_fallback, 'co': is_co_global})

    return parsed_orientations


# --- 3. Processamento de Dados (Adaptado para Cache) ---
def default_node_factory():
    return {'Formacao': 'N/A', 'Campus': 'N/A', 'Lotacao': 'N/A', 'Mestrado_Orientador': [], 'Doutorado_Orientador': [], 'Pos_Doutorado_Supervisor': []}


@st.cache_data
def processar_dados_da_rede():
    # Usar io.StringIO para ler a string como se fosse um arquivo
    data_io = io.StringIO(csv_data_string)

    # Carregar os dados para um DataFrame do pandas
    df = pd.read_csv(data_io)

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
                    advisee_name = name_match.group(1).strip() # Variável é criada como 'advisee_name'

                    details_text = ""
                    details_match_re = re.search(r"\((.*)\)", entry)
                    if details_match_re:
                        details_text = details_match_re.group(1)

                    orientation_list = get_orientation_details_from_string(details_text, entry.lower())

                    for or_details in orientation_list:
                        degree_type = or_details['type']
                        year = or_details['year']
                        is_co_role = or_details['co']

                        # --- CORREÇÃO: Corrigido o nome da variável de 'advise_name' para 'advisee_name' ---
                        if advisee_name and degree_type:
                            all_nodes.add(advisee_name)
                            detailed_edges.append({
                                'source': current_person, 'target': advisee_name,
                                'type': degree_type, 'co': is_co_role, 'year': year
                            })
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
                            if degree_type == "Mestrado":
                                node_details[current_person]['Mestrado_Orientador'].append(f"{year} por {advisor_name}{' (Co)' if is_co_role else ''}")
                            elif degree_type == "Doutorado":
                                node_details[current_person]['Doutorado_Orientador'].append(f"{year} por {advisor_name}{' (Co)' if is_co_role else ''}")
                            elif degree_type == "Pós-Doutorado":
                                node_details[current_person]['Pos_Doutorado_Supervisor'].append(f"{year} por {advisor_name}{' (Co)' if is_co_role else ''}")

    # Filtrar arestas duplicadas
    unique_edges_tracker = set()
    final_detailed_edges = []
    for edge in detailed_edges:
        edge_tuple = (edge['source'], edge['target'], edge['type'], edge['co'], edge['year'])
        if edge_tuple not in unique_edges_tracker:
            unique_edges_tracker.add(edge_tuple)
            final_detailed_edges.append(edge)
    detailed_edges = final_detailed_edges


    # Calcular in_degree e out_degree (total) para tooltip e tamanho do nó
    out_degree_total = defaultdict(int)
    in_degree_total = defaultdict(int)

    for edge in detailed_edges:
        out_degree_total[edge['source']] += 1
        in_degree_total[edge['target']] += 1

    return all_nodes, imd_docentes, detailed_edges, node_details, out_degree_total, in_degree_total

# --- 4. Execução e Construção do Grafo ---

# Chama a função de processamento para obter os dados (usará o cache se já tiver sido executada)
all_nodes, imd_docentes, detailed_edges, node_details, out_degree_total, in_degree_total = processar_dados_da_rede()

# ADICIONE ESTAS LINHAS PARA DEPURAR:
#st.write(f"Nós encontrados na rede: {len(all_nodes)}")
#st.write(f"Arestas encontradas na rede: {len(detailed_edges)}")

# Mostra as 5 primeiras arestas para ver se os dados parecem corretos
#if detailed_edges:
#    st.dataframe(detailed_edges[:5])

# O código das células "Criação e Configuração do Grafo PyVis" e
# "Configurações de Física e Interação do Grafo" vem aqui.
# A lógica interna delas não muda.

# --- Criação do Grafo com PyVis ---
net = Network(notebook=True, height="800px", width="100%", cdn_resources='remote', directed=True,
              bgcolor="#222222", font_color="white")

# Conjunto para armazenar os orientadores de docentes
docent_advisors = set()

# Itera sobre todas as arestas para identificar quem orientou um docente do IMD
for edge in detailed_edges:
    if edge['target'] in imd_docentes:
        docent_advisors.add(edge['source'])

# Adicionar Nós
for node_name in all_nodes:
    is_docente = node_name in imd_docentes
    is_docent_advisor = node_name in docent_advisors

    if is_docente or is_docent_advisor:
        node_color = "#4A478A"
    else:
        node_color = "#5DD5F0"

    total_degree = out_degree_total.get(node_name, 0) + in_degree_total.get(node_name, 0)
    node_size = BASE_NODE_SIZE + (total_degree ** 1.2) * 0.5
    node_size = min(node_size, MAX_NODE_SIZE) # Garante que os nós não fiquem excessivamente grandes

    # Construir o title_text (tooltip) usando o caractere de nova linha '\n'
    title_text = f"{node_name}\n"  # Removemos o <b> e usamos \n
    if node_details[node_name]['Formacao'] != 'N/A':
        title_text += f"Formação: {node_details[node_name]['Formacao']}\n"
    if node_details[node_name]['Campus'] != 'N/A':
        title_text += f"Campus: {node_details[node_name]['Campus']}\n"
    if node_details[node_name]['Lotacao'] != 'N/A':
        title_text += f"Lotação: {node_details[node_name]['Lotacao']}\n"
    if node_details[node_name]['Mestrado_Orientador']:
        title_text += "Mestrado: " + "; ".join(node_details[node_name]['Mestrado_Orientador']) + "\n"
    if node_details[node_name]['Doutorado_Orientador']:
        title_text += "Doutorado: " + "; ".join(node_details[node_name]['Doutorado_Orientador']) + "\n"
    if node_details[node_name]['Pos_Doutorado_Supervisor']:
        title_text += "Pós-Doutorado: " + "; ".join(node_details[node_name]['Pos_Doutorado_Supervisor']) + "\n"
    if (out_degree_total[node_name] != 0):
        title_text += f"Orientou {out_degree_total[node_name]} vez(es)\n"
    if (in_degree_total[node_name] != 0):
        title_text += f"Foi Orientado {in_degree_total[node_name]} vez(es)"

    # Remove qualquer espaço em branco ou quebra de linha extra no final do texto
    title_text = title_text.strip()

    font_node_color = PALETTE['text_white']
    net.add_node(node_name, label=node_name, color=node_color, size=node_size, title=title_text,
                 font={'size': 12, 'color': font_node_color })
# Adicionar Arestas
for edge in detailed_edges:
    edge_color = ""
    dashes = False
    width = 1.5

    # Lógica de coloração baseada no tipo de orientação
    if edge['type'] == 'Doutorado':
        edge_color = PALETTE['accent_yellow_orange']
        if edge['co']:
            dashes = True
            edge_color = PALETTE['edge_co_doutorado']
            width = 1
    elif edge['type'] == 'Mestrado':
        edge_color = PALETTE['light_blue_cyan']
        if edge['co']:
            dashes = True
            edge_color = PALETTE['edge_co_mestrado']
            width = 1
    elif edge['type'] == 'Pós-Doutorado':
        edge_color = PALETTE['pós_doutorado']
        if edge['co']:
            dashes = True
            edge_color = PALETTE['edge_co_pos_doutorado']
            width = 1

    edge_title = f"{edge['source']} -> {edge['target']}\\n{edge['type']} ({edge['year']}){' [Coorientação]' if edge['co'] else ''}"

    # Agora a condição if edge_color: funcionará corretamente
    if edge_color:
        net.add_edge(edge['source'], edge['target'], color=edge_color, dashes=dashes, title=edge_title, width=width)


# --- Opções de visualização ---
# (Copiado da sua célula "Configurações de Física e Interação do Grafo")
options_str = """
{
  "physics": { "forceAtlas2Based": { "gravitationalConstant": -100, "centralGravity": 0.01, "springLength": 230, "springConstant": 0.08, "damping": 0.4, "avoidOverlap": 1 }, "maxVelocity": 50, "minVelocity": 0.1, "solver": "forceAtlas2Based", "stabilization": { "enabled": true, "iterations": 1000, "updateInterval": 50 }, "adaptiveTimestep": true },
  "interaction": { "hover": true, "tooltipDelay": 200, "navigationButtons": false, "keyboard": {"enabled" : true} },
  "nodes": { "font": { "size": 12, "strokeWidth": 2, "strokeColor": "#222222" } },
  "edges": { "smooth": { "type": "dynamic", "forceDirection": "none", "roundness": 0.3 }, "arrows": { "to": { "enabled": true, "scaleFactor": 0.7 } }, "font": { "size": 9, "align": "middle" }, "selfReferenceSize": null, "selfReference": { "size": 1, "angle": 0.785398163375, "renderBehindTheNode": true } }
}
"""
net.set_options(options_str)

# --- 5. Geração e Exibição do HTML com Busca (VERSÃO CORRIGIDA) ---

# Salva o grafo em um arquivo HTML temporário
file_path = "network_graph_with_search.html"
net.save_graph(file_path)

# Lê o conteúdo do arquivo HTML gerado
with open(file_path, 'r', encoding='utf-8') as f:
    html_content = f.read()

# --- Bloco de HTML e CSS para a caixa de busca e legenda ---
search_and_legend_html = f"""
<style>
    #search-container {{
        position: fixed;
        top: 20px;
        right: 20px;
        background-color: rgba(255, 255, 255, 0.95);
        border: 1px solid #ccc;
        border-radius: 8px;
        padding: 15px;
        z-index: 1001;
        font-family: sans-serif;
        box-shadow: 0 4px 8px rgba(0,0,0,0.2);
        max-width: 300px;
    }}
    #legend-toggle {{
        cursor: pointer;
        font-weight: bold;
        font-size: 16px;
        color: #333;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }}
    #legend-content {{
        margin-top: 15px;
        border-top: 1px solid #eee;
        padding-top: 15px;
        display: none; /* Começa escondido */
    }}
    #search-input {{
        padding: 8px; border: 1px solid #ccc; border-radius: 4px;
        width: 180px; margin-right: 5px;
    }}
    #search-button {{
        padding: 8px 12px; border: none;
        background-color: {PALETTE['medium_blue_purple']};
        color: white; border-radius: 4px; cursor: pointer;
    }}
    .legend-item {{
        display: flex; align-items: center; margin-top: 8px;
        font-size: 12px; color: #333;
    }}
    .legend-color {{
        width: 15px; height: 15px; margin-right: 8px; border: 1px solid #555;
    }}
</style>

<div id="search-container">
    <div id="legend-toggle" onclick="toggleLegend()">
        <span>Busca e Legenda</span>
        <span id="legend-arrow">▶</span>
    </div>

    <div id="legend-content">
        <h4>Buscar Pesquisador</h4>
        <div>
            <input type="text" id="search-input" placeholder="Digite o nome...">
            <button id="search-button" onclick="searchNode()">Buscar</button>
        </div>
        <hr style="margin: 15px 0;">
        <h4>Legenda:</h4>
        <div class="legend-item"><div class="legend-color" style="background-color: {PALETTE['medium_blue_purple']}; border-radius: 50%;"></div>Professor</div>
        <div class="legend-item"><div class="legend-color" style="background-color: {PALETTE['light_blue_cyan']}; border-radius: 50%;"></div>Pesquisador</div>
        <div class="legend-item"><div class="legend-color" style="height: 2px; background-color: #333; width: 20px;"></div>Orientação</div>
        <div class="legend-item"><div class="legend-color" style="height: 2px; border-top: 2px dashed #333; background: none; width: 20px;"></div>Coorientação</div>
        <div style="margin-top: 15px;"></div>
        <div class="legend-item"><div class="legend-color" style="height: 3px; background-color: {PALETTE['light_blue_cyan']};"></div>Mestrado</div>
        <div class="legend-item"><div class="legend-color" style="height: 3px; background-color: {PALETTE['accent_yellow_orange']};"></div>Doutorado</div>
        <div class="legend-item"><div class="legend-color" style="height: 3px; background-color: {PALETTE['pós_doutorado']};"></div>Pós-Doutorado</div>
    </div>
</div>
"""

# --- Bloco de JavaScript para a funcionalidade de busca (CORRIGIDO) ---
# Desta vez, o script é mais simples e não tenta recriar funções.
javascript_injection = """
<script type="text/javascript">
    // ADICIONE A NOVA FUNÇÃO AQUI
    function toggleLegend() {
        var content = document.getElementById('legend-content');
        var arrow = document.getElementById('legend-arrow');
        if (content.style.display === 'none' || content.style.display === '') {
            content.style.display = 'block';
            arrow.textContent = '▼';
        } else {
            content.style.display = 'none';
            arrow.textContent = '▶';
        }
    }

    function searchNode() {
        var searchTerm = document.getElementById('search-input').value.toLowerCase();

        if (!searchTerm) {
            // Se a busca estiver vazia, reseta a visão e a seleção
            window.network.fit();
            window.network.unselectAll();
            return;
        }

        // Usa o dataset de nós que agora é global (window.nodes)
        var allNodes = window.nodes.get({
            filter: function(node) {
                // Procura pelo termo de busca no 'label' de cada nó
                return node.label.toLowerCase().includes(searchTerm);
            }
        });

        var foundNodeIds = allNodes.map(node => node.id);

        if (foundNodeIds.length > 0) {
            // Foca nos nós encontrados
            window.network.fit({
                nodes: foundNodeIds,
                animation: {
                    duration: 1000,
                    easingFunction: 'easeInOutQuad'
                }
            });
            // Destaca (seleciona) os nós encontrados
            window.network.selectNodes(foundNodeIds);
        } else {
            alert('Nenhum pesquisador encontrado com esse termo.');
            // Se não encontrou, reseta a visão
            window.network.fit();
            window.network.unselectAll();
        }
    }

    // Garante que o listener só seja adicionado depois que o elemento existir
    document.addEventListener('DOMContentLoaded', (event) => {{
        var searchInput = document.getElementById('search-input');
        if(searchInput) {{
            searchInput.addEventListener('keyup', function(event) {
                if (event.key === 'Enter') {
                    searchNode();
                }
            });
        }}
    }});
</script>
"""

# --- Modificação do HTML (LÓGICA CORRIGIDA) ---

# 1. Torna as variáveis 'nodes' e 'network' globais, anexando-as ao objeto 'window'
# O Pyvis pode usar nomes de variáveis diferentes, então verificamos os padrões comuns.
if "var nodes = new vis.DataSet(nodes_data);" in html_content:
    html_content = html_content.replace(
        "var nodes = new vis.DataSet(nodes_data);",
        "window.nodes = new vis.DataSet(nodes_data);", 1)
else:
     html_content = html_content.replace(
        "var nodes = new vis.DataSet();",
        "window.nodes = new vis.DataSet();", 1)
     html_content = html_content.replace(
        "nodes.add(nodes_data);",
        "window.nodes.add(nodes_data);", 1)

html_content = html_content.replace(
    "var network = new vis.Network(container, data, options);",
    "window.network = new vis.Network(container, data, options);", 1)


# 2. Insere a caixa de busca e o script funcional antes de fechar o </body>
html_content = html_content.replace("</body>", search_and_legend_html + javascript_injection + "</body>")


# Exibe o grafo modificado na página
try:
    st.components.v1.html(html_content, height=810, scrolling=True)
except Exception as e:
    st.error(f"Ocorreu um erro ao gerar o grafo com a busca: {e}")

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
