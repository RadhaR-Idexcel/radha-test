from setuptools import setup, find_packages

setup(
    name='regex_utils',
    version='1.0.0',
    packages=find_packages(),
    install_requires=[],
    python_requires='>=3.7',
    description='Regex-based utilities for variable resolution',
    author='DevOps Team',
    py_modules=['variable_resolver'],
)
