try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

setup(
    name = 'pwinty',
    packages = ['pwinty'],
    version = '0.3',
    description = 'Python client for the Pwinty photo printing API',
    author = 'Sam Willis',
    author_email = 'sam.willis@gmail.com',
    url = 'https://github.com/samwillis/py-pwinty',
    download_url = 'https://github.com/samwillis/py-pwinty/tarball/0.3',
    keywords = ['printing'],
    classifiers = [],
    install_requires = [
        "requests"
    ]
)
