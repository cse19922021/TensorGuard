from pydriller import Repository


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


def search(data, target_api):
    try:
        for element in data:
            for key, value in element.items():
                if key == target_api:
                    return value
    except Exception as e:
        return 'Could not find your target API from the database!'


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
