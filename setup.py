from setuptools import setup

with open("README.md", 'r') as f:
    long_description = f.read()

requirements = [i.strip() for i in open("requirements.txt").readlines()]

setup(
    name='ShellConfigDeployer',
    version='1.0',
    license='MIT',
    description='A program to deploy your shell configuration to remote hosts.',
    long_description=long_description,
    author='Tim Lindeberg',
    author_email='tim.lindeberg@gmail.com',
    url='https://github.com/timlindeberg/ShellConfigDeployer',
    packages=['scd'],
    install_requires=requirements,
    platforms=['linux', 'macos'],
)
