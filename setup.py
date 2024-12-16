from setuptools import setup, find_packages

setup(
    name="oconsent",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "web3>=6.0.0",
        "click>=8.0.0",
        "python-dateutil>=2.8.2",
        "requests>=2.25.0",
        "pycryptodome>=3.15.0",
        "ipfsapi>=0.4.4",
    ],
    entry_points={
        'console_scripts': [
            'oconsent=oconsent.cli.commands:cli',
        ],
    },
)
