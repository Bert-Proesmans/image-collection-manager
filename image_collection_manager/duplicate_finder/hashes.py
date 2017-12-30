import logging
from pathlib import Path

import diskcache
import imagehash
from PIL import Image

logger = logging.getLogger(__name__)

_glob_ahasher = None
_glob_dhasher = None
_glob_phasher = None


# Substitute methods are used because we want to memoize by path.
# The hashing functions take a PIL.Image object which is not desired as cache key.

def _ahash_substitute(img_path: Path, **kwargs):
    img = Image.open(img_path)
    logger.debug("A-HASH {}", str(img_path))
    return imagehash.average_hash(img, **kwargs)


def _dhash_substitute(img_path: Path, **kwargs):
    img = Image.open(img_path)
    logger.debug("D-HASH {}", str(img_path))
    return imagehash.dhash(img, **kwargs)


def _phash_substitute(img_path: Path, **kwargs):
    img = Image.open(img_path)
    logger.debug("P-HASH {}", str(img_path))
    return imagehash.phash(img, **kwargs)


def ahash(cache: diskcache.FanoutCache, img_path: Path, **kwargs):
    global _glob_ahasher
    if not _glob_ahasher:
        _glob_ahasher = cache.memoize(typed=True, tag='A-hash')(_ahash_substitute)

    return _glob_ahasher(img_path, **kwargs)


def dhash(cache: diskcache.FanoutCache, img_path: Path, **kwargs):
    global _glob_dhasher
    if not _glob_dhasher:
        _glob_dhasher = cache.memoize(typed=True, tag='D-hash')(_dhash_substitute)

    return _glob_dhasher(img_path, **kwargs)


def phash(cache: diskcache.FanoutCache, img_path: Path, **kwargs):
    global _glob_phasher
    if not _glob_phasher:
        _glob_phasher = cache.memoize(typed=True, tag='P-hash')(_phash_substitute)

    return _glob_phasher(img_path, **kwargs)
