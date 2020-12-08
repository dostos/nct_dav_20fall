import argparse
import json
import math
import os
import re
from argparse import Namespace
from collections import defaultdict, Counter
from pathlib import Path

import pandas as pd
import yaml
from pandas import DataFrame
from tqdm import tqdm


with open('config.yaml', 'r') as f:
    config = yaml.load(f)

CACHED_DIR = config['cache_dir']
CSV_DATA_PATH = Path('/data/all-the-news-2-1.csv')
TOTAL_LINES = 2688879
CHUNK_SIZE = 100000
NON_ALPHABET_PATTERN = re.compile('[^a-zA-Z0-9]')


def get_data_generator(chunksize=CHUNK_SIZE) -> DataFrame:
    for chunk in pd.read_csv(CSV_DATA_PATH, chunksize=chunksize):
        yield chunk


def update_count_dict_with_content(key: str, count_dict: defaultdict, content: str) -> None:
    """
    Count keyword in single content and increase count in count_dict
    """
    try:
        content = str(content)
        content = NON_ALPHABET_PATTERN.sub(' ', content).lower()
        for word, count in Counter(content.split()).items():
            count_dict[key][word] += count
    except:
        pass


def update_count_dict_with_chunk(count_dict: defaultdict, df: DataFrame, field: str, key_column: str) -> None:
    """
    Count keyword in data chunk and increase count in count_dict
    """
    keys = df[key_column]
    contents = df[field].loc[keys.notna()]
    keys.dropna()
    for key, content in zip(keys, contents):
        update_count_dict_with_content(key, count_dict, content)


def get_count_dict(field: str, key_column: str) -> defaultdict:
    """
    Count words in given field and arrange count with given key_column
    """
    data_generator = get_data_generator()
    count_dict = defaultdict(lambda: defaultdict(lambda: 0))  # count_dict[key][word] = count
    print(f'{field} {key_column} Counting...')
    for df in tqdm(data_generator, total=math.ceil(TOTAL_LINES/CHUNK_SIZE)):
        update_count_dict_with_chunk(count_dict, df, field, key_column)
    return count_dict


def cache_count_dict(count_dict: defaultdict, field: str, key_column: str) -> None:
    """
    Cache the number of the words with given field and key_column pair
    Save {word: count} dictionary to "{field}/{key_column}/{key}.json"
    ex.
        Save {"a": 10, "the": 5, ...}
          in "statistics/title/publication/New York Times.json"
    """
    print(f'{field} {key_column} Caching...')
    for key, word_count_dict in tqdm(count_dict.items()):
        save_filepath = Path(f'{CACHED_DIR}/{field}/{key_column}/{key}.json')
        if not os.path.exists(f'{CACHED_DIR}/{field}'):
            os.mkdir(f'{CACHED_DIR}/{field}')
        if not os.path.exists(f'{CACHED_DIR}/{field}/{key_column}'):
            os.mkdir(f'{CACHED_DIR}/{field}/{key_column}')
        if save_filepath.stem == 'nan' or len(str(save_filepath)) > 200 or str(save_filepath).count('/') > 3:
            print(f'Wrong filepath: {str(save_filepath)}')
            continue
        with save_filepath.open('w') as f:
            json.dump(word_count_dict, f, indent=4, sort_keys=True)


def cache(field: str, key_column: str) -> None:
    """
    1. Count words in given field and arrange count with given key_column
    2. Cache the number of the words
    """
    count_dict = get_count_dict(field, key_column)
    cache_count_dict(count_dict, field, key_column)


def parse_args() -> Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument('--all', action='store_true')
    parser.add_argument('--key-column', default='year', choices=['publication', 'year'],
                        help='select a column to arrange the counts')
    parser.add_argument('--field', default='article', choices=['title', 'article'],
                        help='count words in this column')
    args = parser.parse_args()
    return args


def main() -> None:
    """
    if not args.all:
        Count words in given field and arrange count with given key_column
        Cache the number of the words
    else:
        Cache the number of all words with possible field and key_column pair
    """
    if not Path(CACHED_DIR).exists():
        Path(CACHED_DIR).mkdir()
    args = parse_args()
    if args.all:
        for field in ['title', 'article']:
            for key_column in ['publication', 'year']:
                cache(field, key_column)
    else:
        cache(args.field, args.key_column)


if __name__ == '__main__':
    main()
