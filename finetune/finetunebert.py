from datasets import load_dataset
from transformers import AutoTokenizer
tokenizer = AutoTokenizer.from_pretrained("bert-base-cased")
import numpy as np
import evaluate
import tensorflow as tf

def split_data(dataset):
    train = dataset["train"].shuffle(seed=42).select(range(1000))
    test = dataset["train"].shuffle(seed=42).select(range(500))
    x_train = []
    y_train = []
    x_test = []
    y_test = []
    for idx, item in enumerate(train):
        x_train.append(item['text'])
        y_train.append(item['label'])
    
    for idx, item in enumerate(test):
        x_test.append(item['text'])
        y_test.append(item['label'])

    return x_test, x_test, y_train, y_test

def tokenize(data):
    # padding makes sure that the input data have the same length
    # truncation just remove the white spaces
    return tokenizer(data, padding=True, truncation=True)

def ttrain():
    dataset = load_dataset("yelp_review_full")
    x_train, x_test, y_train, y_test = split_data(dataset)
    x_train_encoded = tokenizer(x_train)
    x_test_encoded = tokenizer(x_test)
    
    # convert the encodings into dataset objects
    x_train_encoded = tf.ragged.constant(x_train_encoded)
    x_test_encoded = tf.ragged.constant(x_test_encoded)

    train_dataset = tf.data.Dataset.from_tensor_slices((
        dict(x_train_encoded), 
        y_train
        ))
    test_dataset = tf.data.Dataset.from_tensor_slices((
        dict(x_test_encoded),
          y_test
        ))

    print(train_dataset)


    
    




    # tokenized_datasets = dataset.map(tokenize_function, batched=True)

if __name__ == '__main__':
    ttrain()