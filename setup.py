from setuptools import setup, find_packages

setup(
    name='ryzen-master-commander',
    version='0.1.5',
    packages=find_packages(),
    install_requires=[
        'matplotlib',
        'ttkbootstrap',
    ],
    entry_points={
        'console_scripts': [
            'ryzen-master-commander = app:main',
        ],
    },
)