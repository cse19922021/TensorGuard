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
import numpy as np
from pydriller import Repository
# test
ROOT_DIR = os.getcwd()


def read_txt(fname):
    with open(fname, 'r') as fileReader:
        data = fileReader.read().splitlines()
    return data


def write_list_to_txt4(data, filename):
    with open(filename, "a", encoding='utf-8') as file:
        file.write(data+'\n')


def write_list_to_txt2(data, filename):
    with open(filename, "w") as file:
        for row in data:
            file.write(row+'\n')


def decompose_code_linens(splitted_lines):
    super_temp = []
    j = 0
    indices = []
    while j < len(splitted_lines):
        if '\n' in splitted_lines[j]:
            indices.append(j)
        j += 1

    if bool(indices) == False:
        return splitted_lines

    if len(indices) == 1:
        for i, item in enumerate(splitted_lines):
            if i != 0:
                super_temp.append(item)
        super_temp = [super_temp]
    else:
        i = 0
        j = 1
        while True:
            temp = []
            for row in range(indices[i], indices[j]):
                temp.append(splitted_lines[row+1])
            super_temp.append(temp)
            if j == len(indices)-1:
                temp = []
                for row in range(indices[j], len(splitted_lines)):
                    temp.append(splitted_lines[row])
                super_temp.append(temp)
                break
            i += 1
            j += 1

    return super_temp


def parse_sub_element(data):
    for elem in data.contents:
        if isinstance(elem, str):
            return elem
        else:
            return parse_sub_element(elem)


def recursive_parse_api_description(data):
    g = []
    for elem in data.contents:
        if isinstance(elem, str):
            g.append(elem)
        else:
            x = parse_sub_element(elem)
            g.append(x)
    return g


def recursive_parse_api_sequence(data):
    if isinstance(data.contents[0], str):
        return data.contents[0]
    for elem in data.contents:
        if not isinstance(elem, str):
            return recursive_parse_api_sequence(elem)


def format_code(code_):
    lines_decomposed = decompose_code_linens(code_)
    code = ''
    for line in lines_decomposed:
        line = "".join(line)
        code = code + line
    return code


def get_code_change(sha):
    changes = []
    try:
        for commit in Repository('repos/tensorflow', single=sha).traverse_commits():
            for modification in commit.modified_files:
                changes.append(modification.diff)
    except Exception as e:
        print(e)
    return changes
    # api_link = f"https://api.github.com/repos/tensorflow/tensorflow/commits/{sha}"


def scrape_security_page(link):
    code_flag = False
    change_flag = False

    sub_content = requests.get(link)
    page_soup_home = soup(sub_content.text, "html.parser")
    app_main_ = page_soup_home.contents[3].contents[3].contents[1].contents[9]
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
        data = {'Bug description': description_,
                'Sample Code': code_formated,
                'Bug fix': changes}
    elif code_flag == True and change_flag == False:
        data = {'Bug description': description_,
                'Sample Code': code_formated,
                'Bug fix': ''}
    elif code_flag == False and change_flag == True:
        data = {'Bug description': description_,
                'Sample Code': '',
                'Bug fix': changes}
    else:
        data = {'Bug description': description_,
                'Sample Code': '',
                'Bug fix': ''
                }

    return data


def scrape_tensorflow_security():

    for page_num in range(1, 43):
        sub_content = requests.get(
            f"https://github.com/tensorflow/tensorflow/security/advisories?page={page_num}")
        page_soup2 = soup(sub_content.text, "html.parser")
        app_main_ = page_soup2.contents[3].contents[3].contents[1].contents[9]
        box_content = app_main_.contents[1].contents[3].contents[
            1].contents[3].contents[1].contents[3].contents[1].contents[5]
        records = box_content.contents[1].contents[1]

        data_list = []

        for record in records.contents:
            if not isinstance(record, str):
                link_text = record.contents[1].contents[3].contents[1].contents
                partial_link = link_text[1].attrs['href']
                record_title = link_text[1].contents[0]

                full_link = f"https://github.com/{partial_link}"
                data_ = scrape_security_page(full_link)
                data_.update({'Title': record_title})
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

    if not os.path.exists('repos/tensorflow'):
        subprocess.call(
            f'git clone https://github.com/tensorflow/tensorflow.git repos/tensorflow', shell=True)

    scrape_tensorflow_security()


if __name__ == '__main__':
    main()
