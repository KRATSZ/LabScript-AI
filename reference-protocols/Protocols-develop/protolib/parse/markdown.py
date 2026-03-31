import re

from bs4 import BeautifulSoup
import markdown

# NOTE(IL, 2021-03-16): these were gathered from existing READMEs.
ALLOWED_HEADERS = [
    'author',
    'categories',
    'deck-setup',
    'description',
    'internal',
    'modules',
    'notes',
    'labware',
    'partner',
    'pipettes',
    'preview',
    'process',
    'protocol-steps',
    'reagents',
    'reagent-setup',
    'robot',
    'subcategories',
    'time-estimate',
    'title'
]


def markdown_to_dom(text):
    """
    Parses :param:text into BeautifulSoup HTML DOM
    """
    html = markdown.markdown(text)
    return BeautifulSoup(html, 'html.parser')


def parse_list(text):
    """
    Converts extracts list items from
    markdown and converts them into the list of strings.
    """
    dom = markdown_to_dom(text)
    return [
        item.get_text()
        for item in dom.find_all('li')
    ]


def parse_nested_list(text):
    soup = BeautifulSoup(markdown.markdown(text), 'html.parser')

    def get_list(el):
        el = el.find('ol') or el.find('ul')
        return el.find_all('li', recursive=False) if el else []

    def parse(lis):
        return {
            next(li.stripped_strings): parse(get_list(li))
            for li in lis
        }
    tree = parse(get_list(soup))
    return {k: list(sorted(v.keys())) for k, v in tree.items()}


def get_text(document):
    """
    :param:document markdown document
    Returns text-only representation of the document.
    """
    return markdown_to_dom(document).get_text()


def get_title(document):
    """
    :param:document list of strings representing the document
    Returns the title of the document.
    """
    is_title = re.compile(r'# +(.+)')
    # Return next or none of there's nothing
    title = next((
        x for x in map(is_title.match, document)
        if x is not None
    ), None)

    return title.group(1) if title else None


def get_header(line):
    is_header = re.compile(r'^ *##+ *(.*)$')
    res = is_header.match(line)
    return res.group(1) if res else None


def header_to_key(header):
    """
    Converts Markdown header into JSON key.
    Case sensitive.
    """
    overrides = {
        'time estimate': 'time-estimate',
        'sub categories': 'subcategories',
        'additional notes': 'notes',
        'deck setup': 'deck-setup',
        'reagent setup': 'reagent-setup',
        'protocol steps': 'protocol-steps'
    }

    return overrides.get(header, header)


def convert_value(key, value):
    """
    Given :param:key and :param:value
    converts value from markdown to an object
    defined by mapping.
    """
    handlers = {
        'categories': parse_nested_list,
        'subcategories': parse_list,
        'modules': parse_list,
        'robot': parse_list,
        'reagents': parse_list
    }
    return handlers.get(key, get_text)(value)


def split_markdown(document):
    """
    Splits markdown document returning a dictionary with
    headers as keys and content as values.

    :param:document list of document lines.
    """
    header_indexes = [
        i for i, line in enumerate(document)
        if get_header(line)]

    header_indexes += [len(document)]

    keys = [get_header(document[i]) for i in header_indexes[:-1]]

    values = [
        ''.join(document[start + 1:end])
        for start, end in
        zip(header_indexes[:-1], header_indexes[1:])
    ]

    title = get_title(document)
    head = {
        'title': title
    } if title else {}

    tail = {
        key: value
        for key, value in
        zip(keys, values)
    }

    return {**head, **tail}


def parse_headers(document):
    """
    :param:document in dict form
    :returns: new document dictionary with keys
    converted from header text into their canonical
    representation
    """
    return {
        header_to_key(key.lower().strip()): value
        for key, value in document.items()
    }


def parse_values(document):
    """
    :param:document in dict form
    :returns: new document dictionary values parsed
    from markdown into their standard form
    (i.e. converting bullets to lists)
    """
    return {
        key: convert_value(key, value)
        for key, value in document.items()
    }


def parse(filename):
    """
    Parses markdown into protocol library document dictionary.
    """
    if not filename:
        return {}

    print('Parsing README: {}'.format(filename))

    with open(filename) as md:
        md = parse_headers(split_markdown(list(md)))

        for key, value in md.items():
            if key not in ALLOWED_HEADERS:
                raise ValueError("invalid header: '{}'".format(key))

        md = {
            key: value
            for key, value in md.items()
            if key in ALLOWED_HEADERS
        }

        return {
            **parse_values(md),
            'markdown': md
        }
