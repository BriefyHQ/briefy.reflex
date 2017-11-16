"""Copy of assets from Google Drive to S3 and add them to briefy.alexandria."""
from setuptools import find_packages
from setuptools import setup

import os

here = os.path.abspath(os.path.dirname(__file__))
with open(os.path.join(here, 'README.rst')) as f:
    README = f.read()
with open(os.path.join(here, 'HISTORY.rst')) as f:
    CHANGES = f.read()

requires = [
    'briefy.common[db]',
    'briefy.gdrive',
    'celery',
    'eventlet',
    'flower',
    'prettyconf',
    'setuptools',
]

test_requirements = [
    'flake8',
    'pytest'
]

setup(
    name='briefy.reflex',
    version='0.1.0',
    description='Copy of assets from Google Drive to S3 and add them to briefy.alexandria.',
    long_description=README + '\n\n' + CHANGES,
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
    ],
    author='Briefy Tech Team',
    author_email='developers@briefy.co',
    url='https://github.com/BriefyHQ/briefy.reflex',
    keywords='copy,gdrive,aws,s3,dal',
    packages=find_packages('src'),
    package_dir={'': 'src'},
    namespace_packages=['briefy', ],
    include_package_data=True,
    zip_safe=False,
    test_suite='tests',
    tests_require=test_requirements,
    install_requires=requires,
    entry_points="""
    [console_scripts]
      tasks_worker = briefy.reflex.tasks.worker:main
      queue_worker = briefy.reflex.queue.worker:main
    """,
)
