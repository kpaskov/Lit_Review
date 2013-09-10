'''
Created on Jan 11, 2013

@author: kpaskov
'''
import os
from setuptools import setup, find_packages

here = os.path.abspath(os.path.dirname(__file__))
README = open(os.path.join(here, 'README.rst')).read()

install_requires = [
    'Flask>=0.9',
    'Flask-Login>=0.1.3',
    'Jinja2>=2.6',
    'SQLAlchemy>=0.7.9',
    'WTForms>=1.0.2',
    'Werkzeug>=0.8.3',
    'numpy>=1.6.2',
    'biopython>=1.60',
    'cx-Oracle>=5.1.2',
    'distribute>=0.6.28',
    'jsonpickle>=0.4.0'
    ]

tests_require = [
    'WebTest',
    ]

setup(
    name='LitReview',
    version='0.7',
    description='Literature curation tool.',
    long_description=README,
    author='Kelley Paskov',
    author_email='kpaskov@stanford.edu',
    url="http://cherry-vm13.stanford.edu",
    license="MIT",
    install_requires=install_requires,
    packages=find_packages('src'),
    package_dir={'': 'src'},
    include_package_data=True,
    zip_safe=False,
    tests_require=tests_require,
    extras_require={
        'test': tests_require,
        },
    entry_points='''
        [paste.app_factory]
        main = mypackage:main
        ''',
    )