#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Dashboard interativo para exploração de dados de ocultações estelares.
Este dashboard permite visualizar e interagir com os dados do banco de dados 
"stellar_occultations.db", facilitando a análise de curvas de luz.
"""

import os
import dash
from dash import html, dcc, dash_table, callback
from dash.dependencies import Input, Output, State
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import numpy as np

# Importa funções do módulo de banco de dados
from database import (
    get_all_objects, 
    get_observation_dates, 
    get_observers_for_date,
    get_light_curve_data,
    get_comparative_light_curves,
    get_database_statistics,
    get_object_summary
)

# Inicializa a aplicação Dash
app = dash.Dash(
    __name__,
    title='Banco de Dados - Curvas de Luz de Ocultações Estelares',
    meta_tags=[{"name": "viewport", "content": "width=device-width, initial-scale=1"}],
)

server = app.server

# Paleta de cores no tema azul
colors = {
    'primary': '#1e3a8a',
    'secondary': '#3b82f6',
    'accent': '#60a5fa',
    'background': '#f8fafc',
    'card': '#ffffff',
    'text': '#0f172a',
}

# Layout principal do app
app.layout = html.Div([
    # Cabeçalho
    html.Div([
        html.H1("Banco de Dados - Curvas de Luz de Ocultações Estelares", 
                className="app-header-title"),
    ], className="app-header"),
    
    # Conteúdo principal
    html.Div([
        # Linha com cards de estatísticas
        html.Div([
            html.Div([
                html.Div(id="stats-card-objects", className="stats-card"),
                html.Div(id="stats-card-observations", className="stats-card"),
                html.Div(id="stats-card-points", className="stats-card"),
            ], className="stats-container"),
        ], className="row"),
        
        # Divisor de seções
        html.Hr(className="section-divider"),
        
        # Seção de Navegação do Banco de Dados
        html.Div([
            html.H2("Explorador de Dados", className="section-title"),
            
            # Layout em grade para navegação
            html.Div([
                # Coluna da Esquerda (Seleção)
                html.Div([
                    # Card de Seleção de Objeto
                    html.Div([
                        html.H3("Selecionar Objeto", className="card-title"),
                        dcc.Dropdown(
                            id='object-dropdown',
                            options=[],
                            placeholder="Selecione um objeto",
                            className="dash-dropdown"
                        ),
                        html.Div(id="object-meta-info")
                    ], className="dashboard-card"),
                    
                    # Card de Seleção de Data
                    html.Div([
                        html.H3("Selecionar Data", className="card-title"),
                        dcc.Dropdown(
                            id='date-dropdown',
                            options=[],
                            placeholder="Selecione uma data",
                            className="dash-dropdown",
                            disabled=True
                        ),
                    ], className="dashboard-card"),
                    
                    # Card de Seleção de Observadores
                    html.Div([
                        html.H3("Observadores Disponíveis", className="card-title"),
                        html.Div(id="observers-container", className="observers-list"),
                        html.Div([
                            html.Button("Visualizar Selecionados", 
                                     id="view-selected-btn", 
                                     className="button",
                                     disabled=True),
                            html.Button("Selecionar Todos", 
                                     id="select-all-btn", 
                                     className="button secondary-button",
                                     disabled=True),
                            html.Button("Limpar Seleção", 
                                     id="clear-selection-btn", 
                                     className="button secondary-button",
                                     disabled=True),
                        ], className="buttons-container")
                    ], className="dashboard-card"),
                ], className="grid-column left-column"),
                
                # Coluna da Direita (Visualização)
                html.Div([
                    # Card do Gráfico de Curvas de Luz
                    html.Div([
                        html.H3("Curvas de Luz", className="card-title"),
                        dcc.Graph(
                            id='light-curve-plot',
                            className="interactive-graph",
                            figure={
                                'layout': {
                                    'xaxis': {'title': 'Tempo (JD)'},
                                    'yaxis': {'title': 'Fluxo Normalizado'},
                                    'paper_bgcolor': colors['card'],
                                    'plot_bgcolor': colors['background'],
                                    'font': {'color': colors['text']},
                                    'height': 550,
                                }
                            }
                        ),
                        # Controles adicionais para o gráfico
                        html.Div([
                            html.Div([
                                html.Label("Tipo de Gráfico:", className="control-label"),
                                dcc.RadioItems(
                                    id='plot-type-radio',
                                    options=[
                                        {'label': 'Linhas', 'value': 'lines'},
                                        {'label': 'Pontos', 'value': 'markers'},
                                        {'label': 'Linhas + Pontos', 'value': 'lines+markers'}
                                    ],
                                    value='lines',
                                    className="dash-radio-items"
                                ),
                            ], className="plot-control"),
                            html.Div([
                                html.Label("Normalização:", className="control-label"),
                                dcc.RadioItems(
                                    id='normalization-radio',
                                    options=[
                                        {'label': 'Normalizado', 'value': 'normalized'},
                                        {'label': 'Fluxo original', 'value': 'original'}
                                    ],
                                    value='normalized',
                                    className="dash-radio-items"
                                ),
                            ], className="plot-control"),
                        ], className="plot-controls-container"),
                    ], className="dashboard-card"),
                    
                    # Card de Detalhes da Curva de Luz
                    html.Div([
                        html.H3("Detalhes dos Dados", className="card-title"),
                        html.Div(id="data-details-container")
                    ], className="dashboard-card"),
                ], className="grid-column right-column"),
            ], className="grid-container"),
        ], className="section"),
        
        # Seção de Tabela de Dados
        html.Div([
            html.H2("Dados Numéricos", className="section-title"),
            html.Div([
                html.Div(id="data-table-container", className="data-table-wrapper")
            ], className="dashboard-card"),
        ], className="section"),
        
        # Armazenamentos para dados e estados
        dcc.Store(id='selected-observers-store'),
        dcc.Store(id='light-curves-data-store'),
        
        # Rodapé
        html.Footer([
            html.Div([
                html.P("Dashboard para visualização de dados de ocultações estelares"),
                html.P("Versão 1.0.0")
            ], className="footer-content")
        ], className="app-footer")
    ], className="main-container")
])

# Callback para atualizar o dropdown de objetos e estatísticas
@app.callback(
    [
        Output('object-dropdown', 'options'),
        Output('stats-card-objects', 'children'),
        Output('stats-card-observations', 'children'),
        Output('stats-card-points', 'children')
    ],
    [Input('object-dropdown', 'id')]  # Trigger no carregamento
)
def update_object_dropdown_and_stats(_):
    # Obtém a lista de objetos
    objects = get_all_objects()
    
    # Formata as opções para o dropdown
    options = [{'label': obj, 'value': obj} for obj in objects]
    
    # Obtém estatísticas do banco de dados
    stats = get_database_statistics()
    
    # Cria os cards de estatísticas
    objects_card = html.Div([
        html.H3(stats.get('total_objects', 0), className="stats-number"),
        html.P("Objetos Celestes", className="stats-label")
    ])
    
    observations_card = html.Div([
        html.H3(stats.get('total_observations', 0), className="stats-number"),
        html.P("Observações Totais", className="stats-label")
    ])
    
    points_card = html.Div([
        html.H3(f"{stats.get('total_points', 0):,}".replace(',', '.'), className="stats-number"),
        html.P("Pontos de Dados", className="stats-label")
    ])
    
    return options, objects_card, observations_card, points_card

# Callback para atualizar informações do objeto selecionado
@app.callback(
    Output('object-meta-info', 'children'),
    [Input('object-dropdown', 'value')]
)
def update_object_info(selected_object):
    if not selected_object:
        return html.Div()
    
    # Obtém resumo dos objetos
    df_summary = get_object_summary()
    
    # Filtra para o objeto selecionado
    if not df_summary.empty:
        row = df_summary[df_summary['object_name'] == selected_object]
        if not row.empty:
            observations = row['total_observations'].iloc[0]
            dates = row['distinct_dates'].iloc[0]
            
            return html.Div([
                html.P([
                    html.Span("Total de observações: ", className="info-label"),
                    html.Span(f"{observations}", className="info-value")
                ]),
                html.P([
                    html.Span("Datas disponíveis: ", className="info-label"),
                    html.Span(f"{dates}", className="info-value")
                ])
            ], className="object-info")
    
    return html.Div()

# Callback para atualizar o dropdown de datas quando um objeto é selecionado
@app.callback(
    [Output('date-dropdown', 'options'),
     Output('date-dropdown', 'disabled'),
     Output('date-dropdown', 'value')],
    [Input('object-dropdown', 'value')]
)
def update_date_dropdown(selected_object):
    if not selected_object:
        return [], True, None
    
    # Obtém datas disponíveis para o objeto
    dates = get_observation_dates(selected_object)
    
    # Formata as opções para o dropdown
    options = [{'label': date, 'value': date} for date in dates]
    
    return options, False, None

# Callback para atualizar a lista de observadores quando uma data é selecionada
@app.callback(
    [Output('observers-container', 'children'),
     Output('selected-observers-store', 'data'),
     Output('view-selected-btn', 'disabled'),
     Output('select-all-btn', 'disabled'),
     Output('clear-selection-btn', 'disabled')],
    [Input('object-dropdown', 'value'),
     Input('date-dropdown', 'value')],
    [State('selected-observers-store', 'data')]
)
def update_observers_list(selected_object, selected_date, current_selection):
    if not selected_object or not selected_date:
        return html.Div("Selecione um objeto e uma data para ver os observadores disponíveis."), {}, True, True, True
    
    # Obtém observadores para o objeto e data
    observers_df = get_observers_for_date(selected_object, selected_date)
    
    if observers_df.empty:
        return html.Div("Nenhum observador encontrado para esta data."), {}, True, True, True
    
    # Inicializa seleção
    if current_selection is None:
        current_selection = {}
    
    # Cria itens de observador com checkbox
    observer_items = []
    for _, row in observers_df.iterrows():
        observer_id = str(row['observation_id'])
        observer_name = row['observer_name']
        is_positive = row['is_positive']
        point_count = row['point_count']
        
        # Determina o status do checkbox (marcado ou não)
        checked = current_selection.get(observer_id, False)
        
        observer_items.append(html.Div([
            dcc.Checklist(
                id={'type': 'observer-checkbox', 'index': observer_id},
                options=[{'label': '', 'value': observer_id}],
                value=[observer_id] if checked else [],
                className="observer-checkbox"
            ),
            html.Div([
                html.Span(observer_name, className="observer-name"),
                html.Div([
                    html.Span(
                        "Positivo" if is_positive else "Negativo", 
                        className=f"observer-tag {'positive' if is_positive else 'negative'}"
                    ),
                    html.Span(f"{point_count} pontos", className="observer-tag points")
                ], className="observer-tags")
            ], className="observer-info")
        ], className="observer-item")
        )
    
    # Retorna a lista de observadores
    return html.Div(observer_items, className="observers-checklist"), current_selection, False, False, False

# Callback para atualizar a seleção de observadores quando um checkbox é clicado
@app.callback(
    Output('selected-observers-store', 'data', allow_duplicate=True),
    [Input({'type': 'observer-checkbox', 'index': dash.dependencies.ALL}, 'value')],
    [State({'type': 'observer-checkbox', 'index': dash.dependencies.ALL}, 'id'),
     State('selected-observers-store', 'data')],
    prevent_initial_call=True
)
def update_selected_observers(values, ids, current_selection):
    if current_selection is None:
        current_selection = {}
    
    # Atualiza a seleção com base nos checkboxes
    for i, checkbox_id in enumerate(ids):
        observer_id = checkbox_id['index']
        current_selection[observer_id] = bool(values[i])
    
    return current_selection

# Callback para selecionar todos os observadores
@app.callback(
    Output('selected-observers-store', 'data', allow_duplicate=True),
    [Input('select-all-btn', 'n_clicks')],
    [State('observers-container', 'children')],
    prevent_initial_call=True
)
def select_all_observers(n_clicks, observers_container):
    if n_clicks is None or not observers_container:
        raise dash.exceptions.PreventUpdate
    
    # Processa o conteúdo para encontrar todos os IDs
    selection = {}
    
    # Nota: Esta é uma implementação simplificada
    # Deveríamos usar padrões mais estruturados em um dashboard real
    # Aqui, estamos analisando a estrutura retornada pelo callback anterior
    observers = observers_container['props']['children']
    for observer in observers:
        if isinstance(observer, dict):
            checkboxes = [c for c in observer['props']['children'] if isinstance(c, dict) and c.get('type') == 'Checklist']
            for checkbox in checkboxes:
                if 'props' in checkbox and 'options' in checkbox['props']:
                    for option in checkbox['props']['options']:
                        observer_id = option['value']
                        selection[observer_id] = True
    
    return selection

# Callback para limpar a seleção de observadores
@app.callback(
    Output('selected-observers-store', 'data', allow_duplicate=True),
    [Input('clear-selection-btn', 'n_clicks')],
    prevent_initial_call=True
)
def clear_observer_selection(n_clicks):
    if n_clicks is None:
        raise dash.exceptions.PreventUpdate
    
    return {}

# Callback para carregar dados das curvas de luz quando o botão é clicado
@app.callback(
    Output('light-curves-data-store', 'data'),
    [Input('view-selected-btn', 'n_clicks')],
    [State('object-dropdown', 'value'),
     State('date-dropdown', 'value'),
     State('selected-observers-store', 'data')]
)
def load_light_curve_data(n_clicks, selected_object, selected_date, selected_observers):
    if n_clicks is None or not selected_object or not selected_date:
        raise dash.exceptions.PreventUpdate
    
    if not selected_observers:
        return {'curves': [], 'observers': [], 'metadata': []}
    
    # Filtra para observadores selecionados
    selected_ids = [int(obs_id) for obs_id, selected in selected_observers.items() if selected]
    
    if not selected_ids:
        return {'curves': [], 'observers': [], 'metadata': []}
    
    # Inicializa listas
    curves = []
    observers = []
    metadata = []
    
    # Obtém os dados para cada observador selecionado
    for obs_id in selected_ids:
        # Obtém a curva de luz
        curve_df = get_light_curve_data(obs_id)
        
        if not curve_df.empty:
            # Converte DataFrame para dicionário para serialização
            curves.append(curve_df.to_dict('records'))
            
            # Obtém informações do observador
            obs_info = {
                'id': obs_id,
                'object_name': selected_object,
                'observation_date': selected_date
            }
            
            metadata.append(obs_info)
    
    # Obtém lista de nomes de observadores
    observers_df = get_observers_for_date(selected_object, selected_date)
    observer_names = {}
    
    for _, row in observers_df.iterrows():
        observer_names[row['observation_id']] = row['observer_name']
    
    observers = [observer_names.get(obs_id, f"Observador {obs_id}") for obs_id in selected_ids]
    
    return {
        'curves': curves,
        'observers': observers,
        'metadata': metadata
    }

# Callback para atualizar o gráfico de curvas de luz
@app.callback(
    Output('light-curve-plot', 'figure'),
    [Input('light-curves-data-store', 'data'),
     Input('plot-type-radio', 'value'),
     Input('normalization-radio', 'value')]
)
def update_light_curve_plot(data, plot_type, normalization):
    if not data or not data.get('curves'):
        # Retorna um gráfico vazio
        return {
            'data': [],
            'layout': {
                'title': 'Nenhum dado para exibir',
                'xaxis': {'title': 'Tempo (JD)'},
                'yaxis': {'title': 'Fluxo Normalizado'},
                'paper_bgcolor': colors['card'],
                'plot_bgcolor': colors['background'],
                'font': {'color': colors['text']},
                'height': 550,
            }
        }
    
    # Inicializa a figura
    fig = go.Figure()
    
    # Adiciona cada curva de luz ao gráfico
    for i, (curve_data, observer) in enumerate(zip(data['curves'], data['observers'])):
        # Converte dados do dicionário para listas
        df = pd.DataFrame(curve_data)
        
        # Escolhe o campo de fluxo com base na normalização
        y_field = 'flux_normalized' if normalization == 'normalized' else 'flux'
        
        # Adiciona ao gráfico
        fig.add_trace(go.Scatter(
            x=df['time'],
            y=df[y_field],
            mode=plot_type,
            name=observer,
            line=dict(width=2),
        ))
    
    # Atualiza o layout
    fig.update_layout(
        title='Curvas de Luz Comparativas',
        xaxis_title='Tempo (JD)',
        yaxis_title='Fluxo Normalizado' if normalization == 'normalized' else 'Fluxo',
        paper_bgcolor=colors['card'],
        plot_bgcolor=colors['background'],
        font=dict(color=colors['text']),
        height=550,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        ),
        margin=dict(l=40, r=40, t=60, b=60),
    )
    
    return fig

# Callback para atualizar a tabela de dados
@app.callback(
    Output('data-table-container', 'children'),
    [Input('light-curves-data-store', 'data')]
)
def update_data_table(data):
    if not data or not data.get('curves'):
        return html.Div("Selecione curvas de luz para visualizar dados numéricos.")
    
    # Limita a 1000 pontos para melhor desempenho
    max_points = 1000
    
    # Seleciona a primeira curva
    first_curve = pd.DataFrame(data['curves'][0])
    first_observer = data['observers'][0]
    
    # Limita o número de pontos se necessário
    if len(first_curve) > max_points:
        first_curve = first_curve.iloc[:max_points]
        truncated_message = html.Div(
            f"Mostrando os primeiros {max_points} pontos de {len(data['curves'][0])} totais.",
            className="truncated-message"
        )
    else:
        truncated_message = html.Div()
    
    # Cria uma tabela para os dados
    table = dash_table.DataTable(
        data=first_curve.to_dict('records'),
        columns=[
            {"name": "Tempo (JD)", "id": "time"},
            {"name": "Fluxo", "id": "flux"},
            {"name": "Fluxo Normalizado", "id": "flux_normalized"}
        ],
        style_table={'overflowX': 'auto'},
        style_cell={
            'textAlign': 'center',
            'padding': '10px',
            'font-family': 'Segoe UI',
        },
        style_header={
            'backgroundColor': colors['secondary'],
            'color': 'white',
            'fontWeight': 'bold',
            'textAlign': 'center',
            'border': f'1px solid {colors["secondary"]}',
        },
        style_data_conditional=[
            {
                'if': {'row_index': 'odd'},
                'backgroundColor': colors['background'],
            }
        ],
        page_size=15,
    )
    
    # Retorna um container com seleção de curva e tabela
    return html.Div([
        html.Div([
            html.H4(f"Dados de {first_observer}", className="data-table-title"),
            html.P("Selecione diferentes curvas no gráfico para ver seus dados numéricos.", 
                  className="data-table-description"),
            truncated_message,
        ]),
        table
    ])

# Callback para atualizar os detalhes dos dados
@app.callback(
    Output('data-details-container', 'children'),
    [Input('light-curves-data-store', 'data')]
)
def update_data_details(data):
    if not data or not data.get('curves'):
        return html.Div("Selecione curvas de luz para visualizar detalhes.")
    
    details_cards = []
    
    for i, (curve_data, observer) in enumerate(zip(data['curves'], data['observers'])):
        df = pd.DataFrame(curve_data)
        
        # Calcula estatísticas básicas
        stats = {
            'Total de pontos': len(df),
            'Fluxo médio': f"{df['flux'].mean():.4f}",
            'Fluxo mínimo': f"{df['flux'].min():.4f}",
            'Fluxo máximo': f"{df['flux'].max():.4f}",
            'Duração': f"{df['time'].max() - df['time'].min():.6f} dias"
        }
        
        # Cria card de detalhes
        stats_items = [html.P([
            html.Span(f"{label}: ", className="detail-label"),
            html.Span(f"{value}", className="detail-value")
        ]) for label, value in stats.items()]
        
        card = html.Div([
            html.H4(observer, className="detail-title"),
            html.Div(stats_items, className="detail-stats")
        ], className="detail-card")
        
        details_cards.append(card)
    
    return html.Div(details_cards, className="details-grid")

# Resolve problemas de duplicação de callbacks
app.config.suppress_callback_exceptions = True

if __name__ == '__main__':
    print("Iniciando o servidor Dash...")
    print("Acesse http://127.0.0.1:8050/ no seu navegador")
    print("Para encerrar, pressione Ctrl+C")
    app.run(debug=True, port=8050, host="0.0.0.0")
    print("Servidor encerrado.") 