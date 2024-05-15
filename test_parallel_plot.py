from numpy.core.fromnumeric import resize, shape
import plotly.express as px
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import matplotlib.pyplot as plt
import pandas as pd

class Figures():
    def __init__(self, data) -> None:
        self.data = data
        self.cmin = -0.1
        self.cmax = 2.5

        self.adjust_layout()
        self.rootCause_to_symptom()

    def adjust_layout(self):
        df = [self.data['Big Rule'], self.data['Corner Case'], self.data['Bug']]

        result = pd.concat(df, axis=1)

        categorical_dimensions = ['Big Rule', 'Corner Case', 'Bug']
        dimensions = [dict(values=result[label], label=label)
                      for label in categorical_dimensions]

        dimensions[0]['Big Rule'] = 'Big Rule'
        dimensions[1]['Corner Case'] = 'Corner Case'
        dimensions[2]['Bug'] = 'Bug'

        # result["Symptom Vis"] = result["Symptom Vis"].map({'Segmentation Fault': 1, 'Crash': 2, 'Unexpected Behavior': 3, 'Resource Consumption': 4,
        #                                                    'Others': 5})

        color = result['Bug'].values

        colorscale = [[0, 'blue'], [0.33, 'red'], [0.33, 'aliceblue'], [
            0.66, 'green'], [0.66, 'black'], [1.0, 'darkcyan']]
        layout = go.Layout(
            autosize=False,
            width=1400,
            height=600,

            xaxis=go.layout.XAxis(linecolor='red',
                                  linewidth=10,
                                  mirror=True),

            yaxis=go.layout.YAxis(linecolor='black',
                                  linewidth=10,
                                  mirror=True),

            margin=go.layout.Margin(
                l=300,
                r=500,
                b=100,
                t=100,
                pad=8
            )
        )

        trace1 = go.Parcats(dimensions=dimensions,
                            line={'colorscale': colorscale, 'cmin': self.cmin, 'cmax': self.cmax, 'color': color, 'shape': 'hspline'})
        data = [trace1]

        fig = go.Figure(data=data, layout=layout)
        return fig, result, color, colorscale

    def rootCause_to_symptom(self):
        fig, result, color, colorscale = self.adjust_layout()
        colors = {
            'background': 'white',
            'text': 'black'
        }
        fig.update_layout(
            plot_bgcolor=colors['background'],
            paper_bgcolor=colors['background'],
            font_color=colors['text'],
            font_size=20
        )

        fig.show()
        fig.write_html("./rootcauseSymptom.html")

data = pd.read_csv('FSE24-Reported-Bugs - TensorFlow_Vulnerabilities.csv', sep=',', encoding='utf-8')

selected_columns = ['Big Rule', 'Corner Case', 'Bug']  # Replace with the columns you want to select
new_df = data[selected_columns]
Figures(new_df)