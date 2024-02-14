import pandas as pd
import random
data = pd.read_csv('mining/commits/tensorflow/tensorflow.csv', sep=',')

x = data.sample(100)
x.to_csv('sampled_data.csv')