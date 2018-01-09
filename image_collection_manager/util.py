import mimetypes
from collections import deque
from pathlib import Path
import hashlib


def file_digest(path: Path):
    hasher = hashlib.md5()
    with open(path, 'rb') as f:
        for b_chunk in iter(lambda: f.read(4096), b""):
            hasher.update(b_chunk)
    return hasher.hexdigest()


def collect_images(path_list: list, recurse):
    image_paths = []
    l = deque(path_list)
    while len(l) > 0:
        item = l.popleft()
        # Convert to path object if it isn't one.
        item = item if isinstance(item, Path) else Path(item)
        if item.is_file():
            f_type, _ = mimetypes.guess_type(child.as_uri())
            if 'image' not in f_type:
                # File is not an image, skipping it!
                continue

            image_paths.append(child)
        elif item.is_dir():
            for child in item.iterdir():
                if recurse and child.is_dir():
                    l.append(child)
                    continue
                elif child.is_file():
                    f_type, _ = mimetypes.guess_type(child.as_uri())
                    if 'image' not in f_type:
                        # File is not an image, skipping it!
                        continue
                    image_paths.append(child)
                else:  # All other kinds of things a Path could be
                    pass
        else:
            raise ValueError('item is not a file nor directory!')

    return image_paths
