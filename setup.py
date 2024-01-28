from setuptools import setup, find_packages

setup(
    name='pycoreapi',
    description="CoreAPI is a high-performance RSGI lightweight framework for building API's in python with no requirements",
    version='0.2.1',
    url='https://github.com/achaayb/CoreAPI',
    author='Ali Chaayb',
    author_email='achaayb.cheri.dev@gmail.com',
    license='MIT',
    packages=find_packages(),
    install_requires=[
        # Add your dependencies here
    ],
    extras_require={
        'pydantic': ['pydantic']
    }
)