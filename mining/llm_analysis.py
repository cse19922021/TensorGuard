import pandas as pd

def analysis():
    data = pd.read_csv('mining/commits/tensorflow/tensorflow.csv')
    for idx, row in data.iterrows():
        print(row.iloc[0])
    

if __name__ == '__main__':
    analysis()