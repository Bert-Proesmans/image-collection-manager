from setuptools import setup, find_packages

setup(
    name='image-collection-manager',
    version='0.1',
    packages=find_packages(),
    py_modules=["scripts"],
    include_package_data=True,
    install_requires=[
        'Click', 'imagehash', 'diskcache', 'Pillow',
    ],
    entry_points='''
        [console_scripts]
        image-collection-manager=image_collection_manager.scripts:cli
    ''',
)