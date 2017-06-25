from setuptools import setup, find_packages

with open("README.md", 'r') as f:
    long_description = f.read()

requirements = [i.strip() for i in open("requirements.txt").readlines()]

setup(
    name='scd',
    version='1.1',
    license='MIT',
    description='A program to deploy your shell configuration to remote hosts.',
    long_description=long_description,
    author='Tim Lindeberg',
    author_email='tim.lindeberg@gmail.com',
    url='https://github.com/timlindeberg/ShellConfigDeployer',
    packages=find_packages(),
    install_requires=requirements,
    scripts=['bin/sshop'],
    entry_points={'console_scripts': ['scd=scd.main:main']},
    platforms=['linux', 'macos'],
    keywords='shell configuration deployment'
)
