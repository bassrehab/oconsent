from setuptools import setup, find_packages

setup(
    name="oconsent",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "web3>=6.0.0",
        "eth-typing>=3.0.0",
        "eth-utils>=5.0.0",
        "click>=8.0.0",
        "python-dateutil>=2.8.2",
        "requests>=2.25.0",
        "pycryptodome>=3.15.0",
    ],
    extras_require={
        'dev': [
            'pytest>=7.0.0',
            'pytest-cov>=4.0.0',
            'pytest-asyncio>=0.21.0',
            'pytest-mock>=3.10.0',
            'black>=22.3.0',
            'isort>=5.10.1',
        ],
        'ipfs': [
            'ipfshttpclient==0.4.13.2',
        ],
    },
    python_requires='>=3.8',
)