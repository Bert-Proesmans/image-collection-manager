import mimetypes
import logging
import sys
import contextlib
import pathlib
import tempfile
import multiprocessing
from multiprocessing.util import Finalize
from pathlib import Path

import click
import diskcache

from image_collection_manager.duplicate_finder import do_filter_images
from image_collection_manager.organizer import organize_duplicates, organize_images

logger = logging.getLogger(__name__)

CONTEXT_SETTINGS = dict(
    default_map={'filter': {}, 'organize': {}}
)


@contextlib.contextmanager
def _setup_cache(location: pathlib.Path, **kwargs):
    cache_obj = None
    try:
        if not location:
            # Construct new cache location in temp folder
            location = pathlib.Path(tempfile.gettempdir())
            location = location / 'image_collection_manager'

        cache_obj = diskcache.FanoutCache(str(location), **kwargs)
        yield cache_obj
    finally:
        if cache_obj:
            cache_obj.close()


def _setup_logging():
    # Initialise logging
    logging.basicConfig(level=logging.WARNING, stream=sys.stdout,
                        # Or use filename='log.txt'
                        format='%(asctime)s:%(levelname)s:%(name)s: %(message)s')

    logging.getLogger('image_collection_manager.duplicate_finder').setLevel(logging.INFO)
    logging.getLogger('image_collection_manager.organizer').setLevel(logging.INFO)
    logger.setLevel(logging.INFO)


@click.group(invoke_without_command=False, context_settings=CONTEXT_SETTINGS)
@click.pass_context
def cli(ctx):
    _setup_logging()

    # Initialise file kind detection
    mimetypes.init()
    # Create context object for passing data into subcommands
    if ctx.obj is None:
        ctx.obj = {}

    if ctx.invoked_subcommand is not None:
        logger.info('Starting')


@cli.command('filter')
@click.argument('sources', nargs=-1,
                type=click.Path(exists=True, file_okay=True, dir_okay=True, readable=True, resolve_path=True))
@click.option('--recurse', '-r', is_flag=True, default=False, help='Pull images from subdirectories as well')
@click.option('--hash-verify', is_flag=True, default=False, help='Takes the content-hash of each image into '
                                                                 'consideration when memoizing perceptual hashes')
@click.option('--dup-dir', '-d', default=None,
              type=click.Path(exists=True, file_okay=False, dir_okay=True, writable=True, resolve_path=True))
@click.option('--cache-dir', type=click.Path(exists=False, file_okay=False, dir_okay=True, writable=True,
                                             readable=True, resolve_path=True))
@click.pass_context
def filter_duplicates(ctx, sources, recurse, hash_verify, dup_dir, cache_dir):
    with _setup_cache(cache_dir, tag_index=True) as cache:
        logger.info('Sources: {}'.format(', '.join(sources)))
        if dup_dir:
            logger.info('Duplicates folder: {}'.format(str(dup_dir)))

        duplicates = do_filter_images(sources, recurse, cache, hash_verify)
        logger.info('Found {} images which have at least one duplicate'.format(len(duplicates)))
        organize_duplicates(duplicates, dup_dir)
        logger.info('Filtering duplicates finished!')


def _proper_exit_generator(context_manager_exit: callable):
    def call_exit():
        exc_type, exc_value, exc_traceback = sys.exc_info()
        context_manager_exit(exc_type, exc_value, exc_traceback)

    return call_exit


def _multiprocessing_filter_entry(cache_dir: Path, hash_verification: bool):
    from image_collection_manager.duplicate_finder.main import set_global_verify_hash, set_global_cache_object
    # Setup all context managers to simulate the environment of the original process
    worker_id = multiprocessing.current_process().name
    _setup_logging()

    cache_cm = _setup_cache(cache_dir, tag_index=True)
    cache_res = cache_cm.__enter__()

    set_global_verify_hash(hash_verification)
    set_global_cache_object(cache_res)

    # AND register a cleanup after work is finished by this worker
    exit_cb = _proper_exit_generator(cache_cm.__exit__)
    Finalize(cache_cm, exit_cb, exitpriority=16)
    logger.info("Worker `{}` initialized".format(worker_id))


@cli.command('organize')
@click.argument('sources', nargs=-1,
                type=click.Path(exists=True, file_okay=True, dir_okay=True, readable=True, resolve_path=True))
@click.argument('target', nargs=1,
                type=click.Path(exists=True, file_okay=False, dir_okay=True, writable=True, resolve_path=True))
@click.option('--copy/--move', default=True, help="Only use copy (Default) or move operations.")
@click.option('--recurse', '-r', is_flag=True, default=False, help='Pull images from subdirectories as well')
@click.pass_context
def organize(ctx, sources, target, copy, recurse):
    logger.info('Sources: {}'.format(', '.join(sources)))
    logger.info('Target folder: {}'.format(str(target)))

    organize_images(sources, recurse, target, copy)
    logger.info('Organizing images finished!')


if __name__ == "__main__":
    cli()
