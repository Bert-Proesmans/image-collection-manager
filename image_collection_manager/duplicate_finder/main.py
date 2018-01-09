import os
import logging
import itertools
from multiprocessing import Pool
from pathlib import Path

import diskcache

from .hashes import ahash, phash
from image_collection_manager.util import collect_images, file_digest

logger = logging.getLogger(__name__)

# Global object representing the cache
# This is necessary because of multiprocessing
_CACHE = None
_VERIFY_HASH = False


def set_global_cache_object(cache: diskcache.FanoutCache):
    global _CACHE
    _CACHE = cache


def set_global_verify_hash(verify: bool):
    global _VERIFY_HASH
    _VERIFY_HASH = verify


def _collect_duplicate_paths_first(all_paths: list):
    assert _CACHE is not None, 'No global cache object set!'

    hash_collection = {}
    for path in all_paths:
        # Load hashes from cache
        i_hash = ahash(_CACHE, path, hash_size=8)
        if i_hash not in hash_collection:
            hash_collection[i_hash] = [path]
        else:
            hash_collection[i_hash].append(path)

    duplicates = [tuple(v) for (k, v) in hash_collection.items() if len(v) > 1]
    return duplicates


def _first_pass_filter(image_path: Path):
    """
    Do a first pass with a high tolerance hash algorithm to allow for
    'easy' zero-distance clashes (aka false positives).
    The results are double checked with a more precise algorithm during a second pass.
    :param image_paths:
    :param cache:
    :return:
    """
    assert _CACHE is not None, 'No global cache object set!'
    img_hash = file_digest(image_path) if _VERIFY_HASH else None
    # Results are stored into the cache
    ahash(_CACHE, image_path, hash_size=8, digest=img_hash)


def _collect_duplicate_paths_second(all_paths: list):
    assert _CACHE is not None, 'No global cache object set!'

    hash_collection = {}
    for path in all_paths:
        # Load hashes from cache
        i_hash = phash(_CACHE, path, hash_size=8, highfreq_factor=4)
        if i_hash not in hash_collection:
            hash_collection[i_hash] = [path]
        else:
            hash_collection[i_hash].append(path)

    duplicates = [tuple(v) for (k, v) in hash_collection.items() if len(v) > 1]
    return duplicates


def _second_pass_filter(image_path: Path):
    assert _CACHE is not None, 'No global cache object set!'

    img_hash = file_digest(image_path) if _VERIFY_HASH else None
    # Results are stored into the cache
    phash(_CACHE, image_path, hash_size=8, highfreq_factor=4, digest=img_hash)


def do_filter_images(path_list: list, recurse: bool, cache: diskcache.FanoutCache, hash_verification: bool):
    """
    :param hash_verification:
    :param path_list: List of strings indicating folder or image paths
    :param recurse:
    :param cache:
    :return:
    """
    from ..scripts import _multiprocessing_filter_entry

    logger.info('Using cache directory: {}'.format(cache.directory))

    set_global_cache_object(cache)
    set_global_verify_hash(hash_verification)

    # Single processing preparation steps
    images = collect_images(path_list, recurse)

    # Multiprocessing work
    num_procs = os.cpu_count()
    initializer = _multiprocessing_filter_entry
    init_args = (cache.directory,hash_verification)
    with Pool(processes=num_procs, initializer=initializer, initargs=init_args) as pool:
        # TODO; Replace with progress indicator
        logger.info('Working..')

        # Here it might be possible to split work accross threads
        logger.info("Starting _first_ pass")
        pool.map(_first_pass_filter, images)
        possible_duplicate_images = _collect_duplicate_paths_first(images)
        # Flatten list of tuples
        # A list is built because the next methods exhaust all elements from the iterator
        # and we reuse the iterator
        possible_duplicate_images = list(itertools.chain.from_iterable(possible_duplicate_images))

        logger.info("Starting _second_ pass")
        pool.map(_second_pass_filter, possible_duplicate_images)
        actual_duplicate_images = _collect_duplicate_paths_second(possible_duplicate_images)
        # List of tuples of images which resemble each other closely!
        return actual_duplicate_images
