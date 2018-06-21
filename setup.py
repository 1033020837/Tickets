from setuptools import setup

"""
使用方法
python setup.py install
"""

setup(
    name='tickets',
    py_modules=['tickets', 'stations'],
    install_requires=['requests', 'docopt', 'prettytable', 'colorama'],
    entry_points={
        'console_scripts': ['tickets=tickets:cli']
    }
)