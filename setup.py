from setuptools import find_packages, setup

with open("README.MD","r") as file:
    long_description = file.read()


setup(
    name="pysxt",
    version="0.0.1",
    description = "An SDK to easily interact with Space and Time",
    packages=["pysxt"],
    url="https://github.com/spaceandtimelabs/SxT-Python-SDK",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="",
    author_email="",
    license="ISC",
    classifiers=[
        "License :: OSI Approved :: ISC License (ISCL)",
        "Programming Language :: Python :: 3.9",
        "Operating System :: OS Independent"
    ],
    install_requires=["cryptography>=41.0.3","ed25519>=1.5","PyNaCl>=1.5.0","pycryptodomex>=3.18.0","python-dotenv>=1.0.0","Requests>=2.31.0","schedule>=1.2.0","biscuit-python>=0.1.0","setuptools>=67.6.1"],    
    extras_require={
        "dev":["twine>=4.0.2"],
    },
    python_requires=">=3.9",
)
