from setuptools import setup, find_packages

setup(
    name="py_arrakis",
    version="0.2.0",
    description="Python SDK for Arrakis MicroVM Management with RPC Callback Support",
    packages=find_packages(),
    python_requires=">=3.8",
    install_requires=[
        "requests>=2.25.0",
        "websocket-client>=1.0.0",
    ],
)

