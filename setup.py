# coding: utf-8
import re
import os
from setuptools import setup, find_packages


def fpath(name):
    return os.path.join(os.path.dirname(__file__), name)


def read(fname):
    return open(fpath(fname)).read()


file_text = read(fpath('chiki/__init__.py'))


def grep(attrname):
    pattern = r"{0}\W*=\W*'([^']+)'".format(attrname)
    strval, = re.findall(pattern, file_text)
    return strval


def get_data_files(*dirs):
    results = []
    for src_dir in dirs:
        for root, dirs, files in os.walk(src_dir):
            results.append((root, map(lambda f: root + "/" + f, files)))
    return results


setup(
    name='chiki',
    version=grep('__version__'),
    url='http://www.chiki.org/',
    author=grep('__author__'),
    author_email=grep('__email__'),
    description='Common libs of flask web develop',
    packages=find_packages(),
    entry_points={
        'console_scripts': [
            'chiki = chiki.cli:main',
        ]
    },
    include_package_data=True,
    package_data={
        '': ['*.rst'],
    },
    data_files=get_data_files('docs'),
    zip_safe=False,
    platforms='any',
    install_requires=[
        'urllib3==1.22',
        'Flask==0.10.1',
        'Flask-Cache==0.13.1',
        'Flask-BabelEx==0.9.2',
        'Flask-Login==0.2.11',
        'mongoengine==0.10.1',
        'flask-mongoengine==0.7.1',
        'Flask-WTF==0.11',
        'Flask-Mail==0.9.1',
        'Flask-RESTful==0.3.3',
        'Jinja2==2.7.3',
        'WTForms==2.0.2',
        'Flask-Script==2.0.5',
        'wheezy.captcha==0.1.44',
        'Pillow==2.7.0',
        'Flask-SQLAlchemy==2.0',
        'Flask-Migrate==1.3.0',
        'blinker==1.3',
        'cookiecutter==1.1.0',
        'WeRoBot==0.6.1',
        'redis',
        'WeRoBot==0.6.1',
        'Flask-WeRoBot==0.1.2',
        'xmltodict==0.9.2',
        'dicttoxml==1.6.6',
        'qrcode==5.3',
        'Flask-DebugToolbar==0.10.0',
        'Flask-DebugToolbar-LineProfilerPanel==1.0.2',
        'Flask-Session==0.2.3',
        'rsa==3.4.2',
    ],
)
