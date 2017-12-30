import logging
import itertools

import diskcache

from .hashes import ahash, phash
from image_collection_manager.util import collect_images

logger = logging.getLogger(__name__)


def _collect_duplicate_paths_first(all_paths: list, cache: diskcache.FanoutCache):
    hash_collection = {}
    for path in all_paths:
        # Load hashes from cache
        i_hash = ahash(cache, path, hash_size=8)
        if i_hash not in hash_collection:
            hash_collection[i_hash] = [path]
        else:
            hash_collection[i_hash].append(path)

    duplicates = [tuple(v) for (k, v) in hash_collection.items() if len(v) > 1]
    return duplicates


def _first_pass_filter(image_paths: list, cache: diskcache.FanoutCache):
    """
    Do a first pass with a high tolerance hash algorithm to allow for
    'easy' zero-distance clashes (aka false positives).
    The results are double checked with a more precise algorithm during a second pass.
    :param image_paths:
    :param cache:
    :return:
    """
    for path in image_paths:
        # Results are stored into the cache
        ahash(cache, path, hash_size=8)


def _collect_duplicate_paths_second(all_paths: list, cache: diskcache.FanoutCache):
    hash_collection = {}
    for path in all_paths:
        # Load hashes from cache
        i_hash = phash(cache, path, hash_size=8, highfreq_factor=4)
        if i_hash not in hash_collection:
            hash_collection[i_hash] = [path]
        else:
            hash_collection[i_hash].append(path)

    duplicates = [tuple(v) for (k, v) in hash_collection.items() if len(v) > 1]
    return duplicates


def _second_pass_filter(image_paths: list, cache: diskcache.FanoutCache):
    for path in image_paths:
        # Results are stored into the cache
        phash(cache, path, hash_size=8, highfreq_factor=4)


def do_filter_images(path_list: list, recurse: bool, cache: diskcache.FanoutCache):
    """

    :param path_list: List of strings indicating folder or image paths
    :param recurse:
    :param cache:
    :return:
    """
    images = collect_images(path_list, recurse)
    # Here it might be possible to split work accross threads
    _first_pass_filter(images, cache)
    duplicate_images = _collect_duplicate_paths_first(images, cache)
    # Flatten list of tuples
    # A list is built because the next methods exhaust all elements from the iterator
    duplicate_images = list(itertools.chain.from_iterable(duplicate_images))

    _second_pass_filter(duplicate_images, cache)
    duplicate_images = _collect_duplicate_paths_second(duplicate_images, cache)
    # List of tuples of images which resemble each other closely!
    return duplicate_images
