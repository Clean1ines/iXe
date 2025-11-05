from setuptools import setup, find_packages
setup(
    name="ix-common",
    version="0.1.0",
    packages=find_packages(),
    python_requires=">=3.9",
    install_requires=[
        "pydantic>=1.8",
        "sqlalchemy>=1.4"
    ]
)
