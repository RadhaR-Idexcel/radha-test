from setuptools import setup

setup(
    name='logger_config',
    version='1.0.0',
    py_modules=['logger_config'],  # Changed from packages=find_packages() to py_modules
    install_requires=[],
    description='Logger configuration utility',
    python_requires='>=3.8',
)