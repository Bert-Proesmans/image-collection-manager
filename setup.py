from setuptools import setup, find_packages

setup(
    name='image-collection-manager',
    version='0.1',
    packages=find_packages(),
    py_modules=["scripts"],
    include_package_data=True,
    install_requires=[
        'Click>=6.0.0,<7.0.0', 'imagehash>=4.0.0, <5.0.0', 'diskcache>=3.0.0, <4.0.0', 'Pillow==5.0.0',
    ],
    entry_points='''
        [console_scripts]
        image-collection-manager=image_collection_manager.scripts:cli
    ''',
)