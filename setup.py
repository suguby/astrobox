import os

from setuptools import setup


README = open(os.path.join(os.path.dirname(__file__), 'README.rst')).read()

# allow setup.py to be run from any path
os.chdir(os.path.normpath(os.path.join(os.path.abspath(__file__), os.pardir)))

setup(
    name='astrobox',
    version='0.1.2',
    packages=['astrobox', 'astrobox.themes.default'],
    include_package_data=True,
    license='BSD License',
    description='The package allows you to create Astro Robo Game for programmers.',
    long_description=README,
    url='https://github.com/suguby/astrobox',
    author='Shandrinov Vadim',
    author_email='suguby@gmail.com',
    classifiers=[
        'Development Status :: 4 - Beta',
        'License :: OSI Approved :: BSD License',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3.6',
    ],
    install_requires=[
        'robogame_engine<0.9,>=0.8',
    ]
)
