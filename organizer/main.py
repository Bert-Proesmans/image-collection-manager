import logging
from pathlib import Path

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
            target_path = Path(dup_dir) / (subj_name + '_dup_' + str(i) + subj_suffix)
            old_path = str(dup_path)
            # Move the duplicate image into the dup folder
            dup_path.rename(target_path)
            logger.warning('Moved duplicate `{}` to `{}`'.format(old_path, str(dup_path)))
