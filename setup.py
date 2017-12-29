from setuptools import setup, find_packages

setup(
    name='image-collection-manager',
    version='0.1',
    py_modules=find_packages(),
    include_package_data=True,
    install_requires=[
        'Click', 'imagehash', 'diskcache', 'Pillow',
    ],
    entry_points='''
        [console_scripts]
        main=main:cli
    ''',
)