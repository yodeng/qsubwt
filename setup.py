import os

from setuptools import setup

from src import __version__


def getdes():
    des = ""
    if os.path.isfile(os.path.join(os.getcwd(), "README.md")):
        with open(os.path.join(os.getcwd(), "README.md")) as fi:
            des = fi.read()
    return des


setup(
    name="qsubwt",
    version=__version__,
    packages=["qsubwt"],
    package_dir={"qsubwt": "src"},
    author="Deng Yong",
    author_email="yodeng@tju.edu.cn",
    url="https://github.com/yodeng/qsubwt.git",
    license="BSD",
    python_requires='>=3.5',
    long_description=getdes(),
    long_description_content_type='text/markdown',
    entry_points={
        'console_scripts': [
            'qsubwt = qsubwt.qsubwt:main',
        ]
    }
)
