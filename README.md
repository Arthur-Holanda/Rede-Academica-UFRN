# Visualização da Rede Acadêmica - UFRN

Este projeto apresenta uma aplicação web interativa, desenvolvida com Streamlit, para visualizar e analisar a rede de orientação acadêmica de professores dos departamentos de IMD, DIMAP e DCA da Universidade Federal do Rio Grande do Norte (UFRN).

**[Acesse a aplicação online aqui!](URL_DA_SUA_APP_AQUI)**

## Sobre o Projeto

O objetivo principal desta visualização é promover uma análise sobre a conectividade dos pesquisadores, revelando as redes de orientação que formam o tecido acadêmico e científico da instituição. Os dados foram coletados manualmente da [Plataforma Acácia](https://plataforma-acacia.org/).

## Funcionalidades

- **Visualização Interativa do Grafo:** Explore a rede completa de pesquisadores, com zoom, busca e informações detalhadas ao passar o mouse.
- **Análise de Métricas da Rede:** A aplicação calcula e explica diversas métricas, incluindo:
  - Diâmetro e Periferia
  - Densidade e Assortatividade
  - Distribuição de Grau
  - Coeficientes de Clustering
- **Detecção de Comunidades:** Utiliza o método Louvain para identificar e visualizar clusters de pesquisadores fortemente conectados.
- **Previsão de Laços Futuros:** Emprega algoritmos (Adamic-Adar, Jaccard) para sugerir futuras conexões prováveis na rede.

## Como Executar Localmente

1.  Clone este repositório:
    ```bash
    git clone [https://github.com/SEU_USUARIO_GITHUB/Rede-Academica-UFRN.git](https://github.com/SEU_USUARIO_GITHUB/Rede-Academica-UFRN.git)
    ```
2.  Navegue até a pasta do projeto e instale as dependências:
    ```bash
    cd Rede-Academica-UFRN
    pip install -r requirements.txt
    ```
3.  Execute a aplicação Streamlit:
    ```bash
    streamlit run app.py
    ```
