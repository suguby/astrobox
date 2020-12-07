import os

import setuptools


README = open(os.path.join(os.path.dirname(__file__), 'README.md')).read()

# allow setup.py to be run from any path
os.chdir(os.path.normpath(os.path.join(os.path.abspath(__file__), os.pardir)))

with open('requirements.txt') as ff:
    install_requires = [line for line in ff.read().splitlines() if len(line) > 0]

setuptools.setup(
    name='astrobox',
    version='1.6.0',
    packages=setuptools.find_packages(),
    include_package_data=True,
    license='BSD License',
    description='The package allows you to create Astro Robo Game for programmers.',
    long_description=README,
    long_description_content_type="text/markdown",
    url='https://github.com/suguby/astrobox',
    author='Shandrinov Vadim',
    author_email='suguby@gmail.com',
    classifiers=[
        'Development Status :: 4 - Beta',
        'License :: OSI Approved :: BSD License',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
    ],
    install_requires=install_requires,
)
