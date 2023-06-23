from bs4 import BeautifulSoup as soup
from selenium import webdriver
# driver = webdriver.Firefox(executable_path= r"/home/nimashiri/geckodriver-v0.32.0-linux64/geckodriver")
from requests.adapters import HTTPAdapter
from urllib3.util import Retry
import re
from csv import writer
import pandas as pd
import ast
import subprocess
import json
import requests
import os
import time
from collections import Counter
import numpy as np
from pydriller import Repository
from utils.helper_functions import recursive_parse_api_description, get_code_change, format_code, search
# test
ROOT_DIR = os.getcwd()


def read_txt(fname):
    with open(fname, 'r') as fileReader:
        data = fileReader.read().splitlines()
    return data

    # api_link = f"https://api.github.com/repos/tensorflow/tensorflow/commits/{sha}"


def scrape_security_page(link):
    code_flag = False
    change_flag = False

    sub_content = requests.get(link)
    page_soup_home = soup(sub_content.text, "html.parser")
    app_main_ = page_soup_home.contents[3].contents[3].contents[1].contents[9]

    title_ = app_main_.contents[1].contents[3].contents[1].contents[
        1].contents[1].contents[1].contents[1].contents[1].contents[0]

    main_elements = app_main_.contents[1].contents[3].contents[1].contents[1].contents[
        3].contents[1].contents[1].contents[1].contents[3].contents[3].contents[1].contents

    description_ = recursive_parse_api_description(main_elements[3])
    description_ = list(filter(lambda item: item is not None, description_))
    description_ = " ".join(description_)

    for j, item in enumerate(main_elements):
        if not isinstance(item, str):
            d_ = recursive_parse_api_description(item)
            d_ = list(filter(lambda x: x is not None, d_))
            matching_sentences = [
                sentence for sentence in d_ if 'patched' in sentence]
            if matching_sentences:
                if d_[-1] == '.':
                    changes = get_code_change(d_[1])
                    if changes:
                        change_flag = True
                    break
                # else:
                #     for i in range(j+1, len(main_elements)-1):
                #         if not isinstance(main_elements[i], str):
                #             p = recursive_parse_api_description(
                #                 main_elements[i])
                #             print('')

    for item in main_elements:
        if not isinstance(item, str):
            if 'class' in item.attrs and "highlight-source-python" in item.attrs['class']:
                code_ = recursive_parse_api_description(item.contents[0])
                code_formated = format_code(code_)
                code_flag = True

    if code_flag and change_flag:
        data = {'Title': title_,
                'Bug description': description_,
                'Sample Code': code_formated,
                'Code change': changes}
    elif code_flag == True and change_flag == False:
        data = {'Title': title_,
                'Bug description': description_,
                'Sample Code': code_formated}
    elif code_flag == False and change_flag == True:
        data = {'Title': title_,
                'Bug description': description_,
                'Sample Code': '',
                'Code change': changes}
    else:
        data = {'Title': title_,
                'Bug description': description_,
                'Sample Code': ''
                }

    return data


def calculate_rule_importance(data):
    element_frequency = Counter(data['Anomaly'].values.flatten())
    total_elements = len(data['Anomaly'].values.flatten())
    element_importance = {element: frequency /
                          total_elements for element, frequency in element_frequency.items()}
    return sorted(element_importance.items(), key=lambda x: x[1], reverse=True)


def scrape_tensorflow_security_from_list(hash_table):
    data = pd.read_csv('data/TF_RECORDS.csv', encoding='utf-8', delimiter=',')
    weights_ = calculate_rule_importance(data)
    data_list = []
    for idx, row in data.iterrows():
        print(row['API'])
        _target_api = search(hash_table, target_api=row['API'])
        full_link = row['Advisory Link']
        data_ = scrape_security_page(full_link)
        data_.update({'Link': full_link})
        data_.update({'API Signature': _target_api})

        # data_list.append(data_)
        print(data_)

        with open("data/tf_bug_data.json", "a") as json_file:
            json.dump(data_, json_file, indent=4)
            json_file.write(',')
            json_file.write('\n')


def scrape_tensorflow_security():

    data_list = []
    for page_num in range(1, 43):
        time.sleep(2)
        sub_content = requests.get(
            f"https://github.com/tensorflow/tensorflow/security/advisories?page={page_num}")
        page_soup2 = soup(sub_content.text, "html.parser")
        app_main_ = page_soup2.contents[3].contents[3].contents[1].contents[9]
        box_content = app_main_.contents[1].contents[3].contents[
            1].contents[3].contents[1].contents[3].contents[1].contents[5]
        records = box_content.contents[1].contents[1]

        for record in records.contents:
            if not isinstance(record, str):
                link_text = record.contents[1].contents[3].contents[1].contents
                partial_link = link_text[1].attrs['href']
                record_title = link_text[1].contents[0]

                full_link = f"https://github.com/{partial_link}"
                data_ = scrape_security_page(full_link)
                data_.update({'Title': record_title})
                data_.update({'Link': full_link})

                data_list.append(data_)
                print(data_)

    with open("data/tf_bug_data.json", "a") as json_file:
        json.dump(data_list, json_file, indent=4)
        json_file.write('\n')


def ckeckList(lst):
    return len(set(lst)) == 1


def search_dict(d, q):
    if any([True for k, v in d.items() if v == q]):
        return True
    else:
        return False


def main():

    lib_name = 'tf'

    with open(f'API signatures/{lib_name}_API_table.json') as json_file:
        hash_table = json.load(json_file)

    if not os.path.exists('repos/tensorflow'):
        subprocess.call(
            f'git clone https://github.com/tensorflow/tensorflow.git repos/tensorflow', shell=True)

    scrape_tensorflow_security_from_list(hash_table)


if __name__ == '__main__':
    main()
