import nltk
import json
from nltk.util import ngrams
from collections import Counter


def extract_frequent_patterns(sentences, ngram_size, min_frequency):
    # Tokenize the sentences into words
    words = [
        word for sentence in sentences for word in nltk.word_tokenize(sentence)]

    # Generate n-grams of specified size
    ngrams_list = list(ngrams(words, n=ngram_size))

    # Count the occurrences of each n-gram
    ngram_counts = Counter(ngrams_list)

    # Filter the n-grams based on the minimum frequency
    frequent_patterns = [ngram for ngram,
                         count in ngram_counts.items() if count >= min_frequency]

    return frequent_patterns


def run():
    lib_name = 'tf'
    rules = []
    with open(f'rulebase/{lib_name}_rules_general.json') as json_file:
        data = json.load(json_file)
        for item in data:
            rules.append(item['Root Cause'])

    frequent_patterns = extract_frequent_patterns(
        rules, ngram_size=3, min_frequency=5)

    # Print the frequent patterns
    for pattern in frequent_patterns:
        print(' '.join(pattern))


if __name__ == '__main__':
    run()
