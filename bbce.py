# !/usr/bin/env python
# -*- coding: utf-8 -*-
import dash
import dash_auth
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output
import plotly.graph_objs as go
import pandas as pd
import os
from datetime import datetime
import locale
import base64
import io
meses = {
    1:'JAN', 2:'FEV', 3:'MAR', 4:'ABR', 5:'MAI', 6:'JUN', 7:'JUL', 8:'AGO', 9:'SET', 10:'OUT', 11:'NOV', 12:'DEZ'
}

# localiza nomes dos meses em pt br
locale.setlocale(locale.LC_ALL, '')

def carrega_base():
    s = r'http://ec2-34-224-35-9.compute-1.amazonaws.com/bbce'
    df_completo = pd.read_excel(
        io=os.path.join(os.path.dirname(__file__), 'bbce_negociacoes.xlsx'),
        header=None,
        skiprows=1,
        names=['produto', 'tempo', 'mwh', 'mwm', 'preco', 'flag'],
    )

    # arrumação dos dados
    df_completo['tempo'] = pd.to_datetime(df_completo['tempo'], dayfirst=True)
    df_completo['flag'] = df_completo['flag'].str.slice(0, 1)
    df_completo['submercado'] = df_completo['produto'].str.slice(0, 2)
    df_completo['tipo_energia'] =  df_completo['produto'].str.slice(3, 6)
    df_completo['tipo_energia'] =  df_completo['tipo_energia'].str.strip()

    df_completo['tipo_periodo'] = df_completo['produto'].str.slice(6, 10)
    df_completo['tipo_periodo'] = df_completo['tipo_periodo'].str.strip()
    df_completo['produto'] = df_completo['produto'].str.upper()
    df_completo.sort_values(by=['submercado', 'tipo_energia', 'tipo_periodo'])
    df_completo['financeiro'] = df_completo['preco'] * df_completo['mwm']

    # remoção das operações canceladas
    df_completo = df_completo.loc[df_completo['flag'] == 'N']

    return df_completo

def cria_layout():
    # layout
    layout = html.Div([
        # dropdown menus
        html.Div([

            html.Div([
                dcc.Dropdown(
                    id='produto',
                    options=[{'label': i, 'value': i} for i in df_completo['produto'].unique()],
                    value='SE CON MEN {}/{:%y} - Preço Fixo'.format(
                       meses[datetime.now().month], datetime.now()).upper()
                ),
            ],
                style={'width': '40%', 'display': 'inline-block', 'float': 'left', 'verticalAlign': 'top'}
            ),

            html.Div([
                dcc.Dropdown(
                    id='discretizacao',
                    options=[
                        {'label': '3 h', 'value': '3H'},
                        {'label': '1 D', 'value': '1D'},
                        {'label': '2 D', 'value': '2D'},
                        {'label': '1 S', 'value': '7D'},
                        {'label': '1 M', 'value': '1M'}
                    ],
                    value='1D'
                )

            ],
                style={'width': '8%', 'display': 'inline-block', 'float': 'center', 'verticalAlign': 'top'}),

            # N desvios
            html.Div([
                dcc.Dropdown(
                    id='dp',
                    options=[
                        {'label': '1 D.P', 'value': 1},
                        {'label': '2 D.P', 'value': 2},
                        {'label': '3 D.P', 'value': 3}
                    ],
                    value=2
                )
            ],
                style={'width': '8%', 'display': 'inline-block', 'float': 'center', 'verticalAlign': 'top'}),

            # Media movel e Bollinger bandas
            html.Div([
                dcc.Dropdown(
                    id='media_movel',
                    options=[
                        {'label': 'MM20', 'value': 20},
                        {'label': 'MM12', 'value': 12},
                        {'label': 'MM8', 'value': 8},
                        {'label': 'MM5', 'value': 5},
                        {'label': 'MM3', 'value': 3},
                    ],
                    value=[12, 3],
                    multi=True
                )
            ],
                style={'width': '20%', 'display': 'inline-block', 'float': 'center', 'verticalAlign': 'top'}),

            # mudanca pra candle ou preco medio
            html.Div([
                dcc.Dropdown(
                    id='visao',
                    options=[
                        {'label': 'CandleSticks', 'value': 'CandleSticks'},
                        {'label': 'Preco Medio', 'value': 'medio'}
                    ],
                    value='CandleSticks'
                )
            ],
                style={'width': '15%', 'display': 'inline-block', 'float': 'center', 'verticalAlign': 'top'}),
        ]),

        # selecao de datas e upload
        html.Div([
            # botao de escolha de datas
            html.Div([
                dcc.DatePickerRange(
                    id='date_picker',
                    start_date=df_completo['tempo'].min(),
                    end_date=datetime.today(),
                    display_format='DD-MM-YYYY',
                    with_portal=False,
                ),

            ],
                style={'display': 'table-cell', 'verticalAlign': 'middle'}),

            html.Div(
                children='',
                id='output_upload'
            )
        ],
            style={
                'display': 'table'
            }
        ),

        # grafico
        html.Div([
            dcc.Graph(
                id='bbce',
                style={'height': '85vh', 'width': '90vw'}
            )
        ],
            style={'height': '85vh', 'width': '90vw'}
        ),

    ])
    return layout

# carga inicial
df_completo = carrega_base()


# criação da instancia dash
# Auth
VALID_USERNAME_PASSWORD_PAIRS = [
    ['anderson.visconti', 'Abrate01'],
    ['enex.energia', 'enex#01']

]
app = dash.Dash(__name__)
server = app.server

auth = dash_auth.BasicAuth(
    app,
    VALID_USERNAME_PASSWORD_PAIRS
)

# criacao layout
app.layout = cria_layout


@app.callback(
    dash.dependencies.Output('date_picker', 'start_date'),
    [dash.dependencies.Input('produto', 'value')]
)
def update_data_inicial(produto):
    return df_completo.loc[df_completo['produto'] == produto, 'tempo'].min()

@app.callback(
    dash.dependencies.Output('date_picker', 'end_date'),
    [dash.dependencies.Input('produto', 'value')]
)
def update_data_inicial(produto):
    return df_completo.loc[df_completo['produto'] == produto, 'tempo'].max()

@app.callback(
    dash.dependencies.Output('bbce', 'figure'),
    [
        dash.dependencies.Input('produto', 'value'),
        dash.dependencies.Input('discretizacao', 'value'),
        dash.dependencies.Input('date_picker', 'start_date'),
        dash.dependencies.Input('date_picker', 'end_date'),
        dash.dependencies.Input('dp', 'value'),
        dash.dependencies.Input('media_movel', 'value'),
        dash.dependencies.Input('visao', 'value')
    ])
def update_figure(produto, discretizacao, start_date, end_date, dp, media_movel, visao):
    aggregation = {
        'preco': {
            'preco_medio': 'mean',
            'preco_max': 'max',
            'preco_min': 'min',
            'preco_vol': 'std',
            'preco_ini': 'first',
            'preco_fim': 'last'
        },
        'mwm': {
            'mwm_soma': 'sum'
        },
        'financeiro': {
            'financeiro_soma': 'sum'
        }
    }
    df_filtrado = pd.DataFrame(df_completo.loc[df_completo['produto'] == produto, :])
    df_filtrado = df_filtrado.resample(rule=discretizacao, on='tempo').agg(aggregation)
    df_filtrado.columns = df_filtrado.columns.droplevel(level=0)

    # remoção dos finais de semana
    df_filtrado = df_filtrado.loc[df_filtrado.index.dayofweek < 5, :]

    # filtro de data
    df_filtrado = df_filtrado.loc[start_date:end_date]

    # preco medio ponderado
    df_filtrado['preco_medio'] = df_filtrado['financeiro_soma'] / df_filtrado['mwm_soma']

    if visao == 'CandleSticks':
        # criacao da MM e bollinger bands
        for i, media in enumerate(media_movel):
            df_filtrado['media_movel_{}'.format(media)] = df_filtrado['preco_fim'].rolling(
                min_periods=1,
                center=False,
                window=media,
            ).mean()

        # Centralizado no ultimo negocio
        #df_filtrado['vol_p'] = df_filtrado['preco_fim'] + dp * \
        #                       df_filtrado['preco_fim'].rolling(
        #                           min_periods=1,
        #                           center=False,
        #                           window=media_movel[0]
        #                       ).std()

        #df_filtrado['vol_n'] = df_filtrado['preco_fim'] - dp * \
        #                       df_filtrado['preco_fim'].rolling(
        #                           min_periods=1,
        #                           center=False,
        #                           window=media_movel[0]
        #                       ).std()


        # Centralizado na media movel
        df_filtrado['vol_p'] = df_filtrado['media_movel_{}'.format(media_movel[0])] + dp * \
                               df_filtrado['preco_fim'].rolling(
                                   min_periods=1,
                                   center=False,
                                   window=media_movel[0]
                               ).std()

        df_filtrado['vol_n'] = df_filtrado['media_movel_{}'.format(media_movel[0])] - dp * \
                               df_filtrado['preco_fim'].rolling(
                                   min_periods=1,
                                   center=False,
                                   window=media_movel[0]
                               ).std()

    elif visao == 'medio':
        # criacao da MM e bollinger bands
        df_filtrado['media_movel'] = df_filtrado['preco_medio'].rolling(
            min_periods=1,
            center=False,
            window=media_movel
        ).mean()

        df_filtrado['vol_p'] = df_filtrado['preco_medio'] + dp * df_filtrado['preco_vol'].rolling(
            min_periods=1,
            center=False,
            window=media_movel
        ).std()

        df_filtrado['vol_n'] = df_filtrado['preco_medio'] - dp * df_filtrado['preco_vol'].rolling(
            min_periods=1,
            center=False,
            window=media_movel
        ).std()

    df_filtrado['mm_volume'] = df_filtrado['mwm_soma'].rolling(
        min_periods=1,
        center=False,
        window=media_movel[0]).mean()

    # Criacao dos candles
    trace_candle = go.Candlestick(
        x=df_filtrado.index,
        yaxis='y',
        name='candle',
        open=df_filtrado['preco_ini'],
        high=df_filtrado['preco_max'],
        low=df_filtrado['preco_min'],
        close=df_filtrado['preco_fim'],
    )

    # Criacao dos tracos
    trace_preco_medio = go.Scatter(
        x=df_filtrado.index,
        y=df_filtrado['preco_medio'],
        yaxis='y',
        name='Preco Medio',
        mode='lines+markers',
        connectgaps=False,
        line=dict(
            color='#3498DB',
            width=3.5,
        )
    )

    trace_preco_vol_p = go.Scatter(
        x=df_filtrado.index,
        y=df_filtrado['vol_p'],
        yaxis='y',
        name='Vol'.format(dp),
        legendgroup='Vol',
        mode='lines',
        connectgaps=False,
        opacity=0.5,
        line=dict(
            dash='dot',
            width=1.75,
            color='#117A65',
        )
    )

    trace_preco_vol_n = go.Scatter(
        x=df_filtrado.index,
        y=df_filtrado['vol_n'],
        yaxis='y',
        name='Vol'.format(dp),
        showlegend=False,
        legendgroup='Vol',
        mode='lines',
        #fill='tonexty',
        opacity=0.5,
        connectgaps=False,
        line=dict(
            dash='dot',
            width=1.75,
            color='#117A65',
        )
    )

    trace_media_movel = go.Scatter(
        x=df_filtrado.index,
        y=df_filtrado['media_movel_{}'.format(media_movel[0])],
        yaxis='y',
        name='MM{}'.format(media_movel[0]),
        mode='lines',
        connectgaps=False,
        line=dict(
            dash='line',
            width=1.75,
            color='#FF00CC'
        )
    )

    trace_media_movel_2 = go.Scatter(
        x=df_filtrado.index,
        y=df_filtrado['media_movel_{}'.format(media_movel[1])],
        yaxis='y',
        name='MM{}'.format(media_movel[1]),
        mode='lines',
        connectgaps=False,
        line=dict(
            dash='line',
            width=1.75,
            color='#3442DB'
        )
    )

    trace_volume = go.Bar(
        x=df_filtrado.index,
        y=df_filtrado['mwm_soma'],
        yaxis='y2',
        name='Volume',
        marker=dict(
            color='#E74C3C'
        )
    )

    trace_media_movel_volume = go.Scatter(
        x=df_filtrado.index,
        y=df_filtrado['mm_volume'],
        yaxis='y2',
        name='MM{} - Volume'.format(media_movel[0]),
        mode='lines',
        connectgaps=False,
        line=dict(
            width=1.75,
            color='#F4D03F'
        )
    )
    layout = dict()
    data = list()
    fig = dict(data=data, layout=layout)
    if visao == 'CandleSticks':
        fig['data'].append(trace_candle)
    else:
        fig['data'].append(trace_preco_medio)

    fig['data'].append(trace_media_movel)
    fig['data'].append(trace_media_movel_2)
    fig['data'].append(trace_preco_vol_p)
    fig['data'].append(trace_preco_vol_n)
    fig['data'].append(trace_volume)
    fig['data'].append(trace_media_movel_volume)

    # Definicao do layout da figura
    fig['layout'].update(
        title = produto,
        autosize = True,
        #width=1200,
        #height=1200,
        legend = dict(
            orientation='v',
            font=dict(
                size=10
            )
        ),
        yaxis1=dict(
            autotick=True,
            showgrid=True,
            showticklabels=True,
            title='R$/MWh',
            titlefont=dict(
                size=12
            ),
            domain=[0.30, 1.0],
            hoverformat='.2f'
        ),
        xaxis=dict(
            autorange=True,
            autotick=True,
            showgrid=True,
            showticklabels=True,
            domain=[0, 0.95],
            rangeselector=dict(
                x=0.05,
                y=1.0,
                visible=True,
                buttons=list([
                    dict(
                        count=1,
                        label='1m',
                        step='month',
                        stepmode='backward'
                    ),
                    dict(
                        count=2,
                        label='2m',
                        step='month',
                        stepmode='backward'
                    ),
                    dict(
                        count=3,
                        label='3m',
                        step='month',
                        stepmode='backward'
                    ),
                    dict(
                        count=6,
                        label='6m',
                        step='month',
                        stepmode='backward'
                    ),
                    dict(
                        count=1,
                        label='1y',
                        step='year',
                        stepmode='todate'
                    ),
                    dict(step='all'),
                ]),
            ),
            rangeslider=dict(
                visible=False
            ),
            type='date',

        ),
        yaxis2=dict(
            autorange=True,
            autotick=True,
            showgrid=True,
            showticklabels=True,
            title='MWmedio',
            titlefont=dict(
                size=12
            ),
            domain=[0.0, 0.20],
            hoverformat='.2f',
        ),
    )
    # Salvando dados
    df_filtrado = pd.DataFrame(df_filtrado)
    df_filtrado.to_excel(excel_writer=os.path.join(os.path.dirname(__file__), 'export.xlsx'))
    return fig


if __name__ == '__main__':
    app.run_server()
