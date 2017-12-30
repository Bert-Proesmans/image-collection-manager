# Image collection manager

Python tool to filter duplicates from- and organize your image collection.
This tool is tested with Python 3.6, other 3.X versions might work as well.

## Installation

1. Clone the repository;
2. Run the command `pip install .` from the root of the cloned repo;
    - It's recommended to install this tool into a virtual environment (`python -m venv [PATH]`)
3. The program is now usable from your terminal, see usage for more information.

## Usage

You can run this program directly from the terminal (when installed by pip) with
`image-collection-manager --help` or execute the `/image_collection_manager/scripts.py` module with
`python image_collection_manager/scripts.py --help`.

This program has two commands: `filter` and `organize`.

- Filter  
    Performs duplicate filtering within the provided sources.

- Organize  
    Organizes the provided sources into a directory structure according to this
    template: `[BASE]/[ratio]/[height]`.

At anytime you can use the option `--help` for information about possible input to
the program.

As sources you can provide both directory- and image paths. Use the recurse option
to automatically detect images from subdirectories.

## Planned work

The following features are planned to be implemented. Any help is appreciated, please
file a pull-request.

- [ ] Chain commands. 
    Click library allows command chaining, which executes both commands
    after each other (pipelining). There is an issue regarding variadic arguments defined
    on the command group which must be fixed first.

- [ ] Robustness improvements.
    The program should never exit because of an exception, which could leave your library
    in an inconsistent state. Also a warning MUST be printed for each possible destructive
    operation performed by the program on your data!

- [ ] Dry-run option.
    Following the ideals from the previous point, a dry-run option must be provided which
    ONLY calculates the operations without actually performing a copy or move.

- [ ] Progress reporting.
    Fancy progress bars are lit, use the TQDM library to report progress on image hashing and
    currently executing operations.

- [ ] Multi-thread img hashing.
    When processing large image collections this program could benefit from multi-threading or
    sub-processing image hash calculations (distributed work concurrency).