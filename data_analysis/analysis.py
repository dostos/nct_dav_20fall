import argparse
import json
import math
from argparse import Namespace
from collections import defaultdict
from pathlib import Path
from pprint import pprint
from typing import Union, List, Dict
import warnings

from scipy.stats.stats import pearsonr
import yaml
from tqdm import tqdm

from cache import cache

warnings.filterwarnings(action='ignore')

with open('config.yaml', 'r') as f:
    config = yaml.load(f)

CACHED_DIR = config['cache_dir']
PUBLICATION_BIAS = config['publication_bias']


def get_word_count_from_dict(count_dict: Dict[str, int], word: str, relative_count: bool) -> Union[int, float]:
    """
    get cached keyword count
    """
    if word not in count_dict:
        return 0
    if relative_count:
        return count_dict[word] / sum(count_dict.values())
    else:
        return count_dict[word]


def get_year_correlation(key_count_dict: Dict[str, Dict[str, int]], word: str, relative_count: bool) -> (float, float):
    keys = sorted(key_count_dict.keys())
    counts = [get_word_count_from_dict(key_count_dict[key], word, relative_count) for key in keys]
    years = [int(key) for key in keys]
    return pearsonr(years, counts)


def get_publication_correlation(key_count_dict: Dict[str, Dict[str, int]], word: str, relative_count: bool) -> (
        float, float):
    keys = sorted(key_count_dict.keys())
    counts, biases = [], []
    for key in keys:
        if PUBLICATION_BIAS[key] != -1:
            counts.append(get_word_count_from_dict(key_count_dict[key], word, relative_count))
            biases.append(PUBLICATION_BIAS[key])
    return pearsonr(biases, counts)


def get_all_words(key_count_dict: Dict[str, Dict[str, int]], min_occurrence: int = 10) -> List[str]:
    total_count_dict = defaultdict(lambda: 0)
    for key, count_dict in key_count_dict.items():
        for word, count in count_dict.items():
            total_count_dict[word] += count
    return [word for word, count in total_count_dict.items() if count >= min_occurrence]


def get_cached_count_dicts(field: str, key_column: str) -> Dict[str, Dict[str, int]]:
    if len(list(Path(f'{CACHED_DIR}/{field}/{key_column}').glob('*.json'))) == 0:
        cache(field, key_column, reset=True)
    key_count_dict = {}
    for cached_filepath in Path(f'{CACHED_DIR}/{field}/{key_column}').glob('*.json'):
        key = cached_filepath.stem
        with cached_filepath.open('r') as f:
            key_count_dict[key] = json.load(f)
    return key_count_dict


def analysis(field: str, key_column: str, relative_count: bool) -> None:
    """
    Get pearson coefficient with given key_column and word count
    """
    key_count_dict = get_cached_count_dicts(field, key_column)
    words = get_all_words(key_count_dict)
    results = []
    for word in tqdm(words):
        if key_column == 'publication':
            corr, p_value = get_publication_correlation(key_count_dict, word, relative_count)
        elif key_column == 'year':
            corr, p_value = get_year_correlation(key_count_dict, word, relative_count)
        else:
            raise ValueError(f'Wrong key_column: {key_column}')
        if not math.isnan(corr) and not math.isnan(p_value):
            results.append((word, corr, p_value))
    results.sort(key=lambda e: e[1])
    pprint(results[:10])
    pprint(results[-10:])


def parse_args() -> Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument('--key-column', default='publication', choices=['publication', 'year'])
    parser.add_argument('--field', default='title', choices=['title', 'article'])
    parser.add_argument('--relative-count', action='store_true')
    args = parser.parse_args()
    return args


def main():
    args = parse_args()
    analysis(args.field, args.key_column, args.relative_count)


if __name__ == '__main__':
    main()
