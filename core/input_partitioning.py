import pandas as pd
from collections import Counter


def calculate_rule_importance(data):
    element_frequency = Counter(data['Anomaly'].values.flatten())
    total_elements = len(data['Anomaly'].values.flatten())
    element_importance = {element: frequency /
                          total_elements for element, frequency in element_frequency.items()}
    return sorted(element_importance.items(), key=lambda x: x[1], reverse=True)


def main():
    data = pd.read_csv('data/TF_RECORDS.csv', sep=',', encoding='utf-8')
    weights_ = calculate_rule_importance(data)
    unique_types = data['Category'].unique()
    unique_types = list(unique_types)
    for dtype in unique_types:
        anomalies = data.loc[data['Category'] == dtype, 'Anomaly']
        anomalies_unique = list(anomalies.unique())
        print('')


if __name__ == '__main__':
    main()
