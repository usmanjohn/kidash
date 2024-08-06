data_table_styles = {
    #'style_table': {'overflowX': 'auto'},
    #'sort_action': "native",
    #'sort_mode': "multi",
    #'column_selectable': "single",
    #'row_selectable': "multi",
    #'row_deletable': True,
    
    #
    #
    #'page_current': 0,
    #'page_size': 10,
    #'page_action':'custom',
    
    'style_table':{'height': '300px', 'overflowY': 'auto'},
        
    'style_data': {
        'color': 'black',
        'backgroundColor': 'white'
    },
    'style_data_conditional': [
        {
            'if': {'row_index': 'odd'},
            'backgroundColor': 'rgb(220, 220, 220)',
        }
    ],

    'style_cell_conditional':[
        {
            'if': {'column_id': ['보험사+업적월+상품군 key', '보험사']},
            'textAlign': 'left'
        }
    ],
    'style_header':{
        #'whiteSpace': 'normal',
        'height': 'auto',
        'width':10,
        'textAlign': 'center',
        'fontWeight': 'bold',
        'padding': '10px 5px',
        'backgroundColor': '#f8f9fa',
    }
}