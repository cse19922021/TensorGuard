import pandas as pd
import matplotlib.pyplot as plt
import plotly.express as px
data = pd.read_csv('Torch_Vulnerabilities.csv', sep=',', encoding='utf-8')
		
selected_columns = ['Fuzzing Rule', 'Corner Case', 'Symptom']  # Replace with the columns you want to select
new_df = data[selected_columns]

color_map = {
    'Fuzzing Rule': 'blue',
    'Corner Case': 'green',
    'Symptom': 'red',
    # Add more categories and colors as needed
}

fig = px.parallel_categories(new_df, color_continuous_scale=color_map)
fig.update_traces(line_shape='hspline')
fig.update_layout(
    margin=dict(
        l=350,
        r=200,
        pad=4 
    ),
    font=dict(
        family="Arial, sans-serif",
        size=22,
        color="black"
    ),
    title_font=dict(
        family="Arial, sans-serif",
        size=22,
        color="black"
    ),
    hoverlabel=dict(
        font_size=14,
        font_family="Arial, sans-serif"
    )
)
fig.show()