# Dashboard de Ocultações Estelares

Dashboard interativo para exploração de dados de ocultações estelares armazenados no banco de dados SQLite.

## Descrição

Este dashboard web permite visualizar e interagir com curvas de luz de ocultações estelares, oferecendo uma interface intuitiva para navegação nos dados do banco de dados `stellar_occultations.db`. O sistema funciona como um explorador de arquivos, facilitando a seleção e visualização de objetos, datas e observadores.

## Funcionalidades

- **Navegação hierárquica**: Exploração de dados por objeto → data → observador
- **Visualização de curvas de luz**: Gráficos interativos das curvas de luz selecionadas
- **Comparação visual**: Possibilidade de sobrepor múltiplas curvas de luz para comparação
- **Detalhes estatísticos**: Estatísticas básicas para cada curva de luz
- **Tabela de dados**: Visualização tabular dos dados numéricos das curvas
- **Opções de exibição**: Escolha entre diferentes tipos de gráficos (linhas, pontos, ou ambos)
- **Normalização**: Opção para visualizar fluxo normalizado ou original

## Estrutura do Projeto

```
dashboard_occultations/
├── assets/
│   ├── custom.css       # Tema principal (azul, branco e preto)
│   └── styles.css       # Estilos específicos de componentes
├── app.py               # Aplicação principal Dash
├── database.py          # Funções de acesso ao banco de dados
└── README.md            # Documentação
```

## Instalação

1. Certifique-se de ter Python 3.7+ instalado

2. Instale as dependências necessárias:

```bash
pip install dash pandas plotly numpy sqlite3
```

3. Verifique se o banco de dados `stellar_occultations.db` está presente no caminho `../data_warehouse/` relativo à pasta do dashboard

## Uso

1. Execute o dashboard a partir da pasta principal do projeto:

```bash
cd dashboard_occultations
python app.py
```

2. Abra o navegador em [http://127.0.0.1:8050](http://127.0.0.1:8050)

3. Use a interface para navegar pelos dados:
   - Selecione um objeto no primeiro dropdown
   - Escolha uma data de observação no segundo dropdown
   - Marque os observadores que deseja visualizar
   - Clique em "Visualizar Selecionados" para ver as curvas de luz

4. Explore as opções adicionais:
   - Alterne entre diferentes tipos de visualização
   - Veja estatísticas e valores numéricos
   - Compare curvas de luz de diferentes observadores

## Personalização

Você pode personalizar o dashboard modificando:

- `assets/custom.css` - Para alterar o tema de cores e aparência geral
- `assets/styles.css` - Para ajustar estilos específicos de componentes
- `app.py` - Para adicionar novos componentes ou funcionalidades

## Requisitos

- Python 3.7 ou superior
- Dash 2.0 ou superior
- Pandas
- Plotly
- SQLite3 