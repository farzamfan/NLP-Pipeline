#!/usr/bin/env python

from distutils.core import setup

setup(
    name="NLP_Pipeline",
    version="0.1",
    description="Simple NLP Pipelinining based on a file system",
    author="Farzam Fanitabasi",
    author_email="f.fanitabasi@vu.nl",
    packages=["NLP_Pipeline"],
    include_package_data=True,
    zip_safe=False,
    keywords=["NLP", "pipelining"],
    classifiers=[
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: MIT License",
        "Topic :: Text Processing",
    ],
    install_requires=[
        "Flask",
        "flask-cors",
        "requests",
        "pynlpl",
        "corenlp_xml>=1.0.4",
        "amcatclient>=3.4.9",
        "KafNafParserPy",
        "PyJWT",
        "pytest",
        "pytest-flask"
    ]
)
