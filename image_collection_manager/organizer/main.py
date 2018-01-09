import logging
from pathlib import Path
from math import isclose
import shutil

from PIL import Image
import click

from image_collection_manager.util import collect_images

DEFAULT_RATIOS = (
    (1.0 / 1, 'square'),
    (5.0 / 4, 'ratio 1.25'),
    (4.0 / 3, 'ratio 1.33'),
    (8.0 / 5, 'ratio 1.6'),
    (16.0 / 9, 'widescreen')
)

DEFAULT_HEIGHTS = (
    480, 720,
    1080,  # HD
    1440,  # QHD
    2160,  # 4K
    4320,  # 8k
)

logger = logging.getLogger(__name__)


def organize_duplicates(items: list, target_dir: Path = None):
    if target_dir and not target_dir.is_dir():
        raise ValueError('Target_dir must be a directory')

    for tup in items:
        tup = sorted(tup, key=lambda p: str(p).lower(), reverse=True)
        dups = enumerate(tup)
        # Take item with the shortest path as subject.
        # The subject will remain location invariant and it's name will be used
        # to rename duplicates.
        _, item_subj = next(dups)
        subj_name = item_subj.stem
        subj_suffix = item_subj.suffix
        # Use parent dir of subject if no duplicate directory is provided
        dup_dir = (item_subj.parent / 'dups') if target_dir is None else target_dir
        dup_dir.mkdir(exist_ok=True)

        # Move all duplicates into the dup_dir (including a rename)
        # This iterator will process all elements after the first (see next(..) when assigning item_subj
        for i, dup_path in dups:
            old_path = str(dup_path)
            # Auto icnrease dup counter for convenience, but hard limit the increment to 10.
            # If 10 increases are not enough the duplicate is NOT moved and a message is shown.
            j = i
            while j < (i + 10):
                target_path = Path(dup_dir) / (subj_name + '_dup_' + str(j) + subj_suffix)
                try:
                    # Move the duplicate image into the dup folder
                    dup_path.rename(target_path)
                    logger.warning('Moved duplicate `{}` to `{}`'.format(old_path, str(target_path)))
                    break
                except:
                    # The file possibly already exists
                    j += 1
            # Something bad happened, so we report it..
            if j == (i + 10):
                msg = 'Couldn\'t move duplicate file `{}` into duplicates folder with name prefix `{}`, it\'s still in' \
                      'the original location!'.format(old_path, subj_name + '_dup_')
                logger.error(msg)


def _retrieve_output_path(dirs: dict, ratio: float, img_height: int, def_ratios: tuple, def_heights: tuple):
    # Calculate ratio and height to use (rounded upwards)
    # For example: ratio 1.778 -> 1.777; 1.776 -> 1.777
    target_ratio, ratio_name = next(
        (i for i in reversed(def_ratios) if isclose(i[0], ratio, rel_tol=1e-03) or i[0] < ratio), None)
    # For example: height 480<X<=720 will be organized into height 720
    target_height = next((i for i in def_heights if i >= img_height), None)

    if not target_ratio:
        # Image has higher ratio than defined
        target_ratio = 'ratio unkn'

    if not target_height:
        # Image is higher than maximum defined
        target_height = 'Massive'

    # Find the precalculated path, if any..
    # The paths are constructed by the following template:
    # [BASE]/[RATIO]/[HEIGHT]
    target_ratio_path = dirs.get(target_ratio, None)
    if not target_ratio_path:
        target_ratio_path = {
            '_base': Path(dirs['_base']) / ratio_name,
        }
        dirs[target_ratio] = target_ratio_path

    target_height_path = target_ratio_path.get(target_height, None)
    if not target_height_path:
        target_height_path = Path(target_ratio_path['_base']) / ('h' + str(target_height))
        target_ratio_path[target_height] = target_height_path
        # Make sure this directory exists!
        target_height_path.mkdir(parents=True, exist_ok=True)

    return target_height_path


def organize_images(path_list: list, recurse: bool, target_dir: Path, copy):
    images = collect_images(path_list, recurse)
    ratios = DEFAULT_RATIOS
    heights = DEFAULT_HEIGHTS

    # Will contain all path objects used to organize your images into
    output_directories = {
        '_base': target_dir,
    }

    # Will contain all move operations
    move_ops = []

    # TODO; Replace with progress indicator
    logger.info('Working..')

    # Process all images
    for img_path in images:
        img = Image.open(img_path)
        img_width = img.width
        img_height = img.height
        img.close()
        img_ratio = float(img_width) / img_height
        target_path = _retrieve_output_path(output_directories, img_ratio, img_height,
                                            ratios, heights)
        img_name = img_path.name
        old_path = str(img_path)
        new_path = target_path / img_name
        move_ops.append((old_path, new_path))

    logger.info('Attempting to move {} images'.format(len(move_ops)))

    # Move all images
    for op in move_ops:
        old_path = op[0]
        new_path = op[1]
        # Move image to new_path
        img_path = Path(old_path)
        if not img_path.exists() or not img_path.is_file():
            logger.error('Path `{}` doesn\'t point to a valid image'.format(old_path))
            continue

        if copy:
            # Overwrites by default!
            shutil.copy(old_path, new_path)
            logger.info('Copied image `{}` to `{}`'.format(old_path, new_path))
        else:
            try:
                img_path.rename(new_path)
                logger.warning('Moved image `{}` to `{}`'.format(old_path, new_path))
            except:
                try:
                    msg = 'Target file `{}` possibly exist, overwrite?'.format(new_path)
                    if click.confirm(msg, abort=True):  # Allow aborting the program if the user wanted to
                        img_path.replace(new_path)
                        logger.warning('Replaced image at `{}` with `{}`'.format(new_path, old_path))
                except:
                    logger.exception('Couldn\'t move the file')
