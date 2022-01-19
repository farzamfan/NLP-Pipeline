#!/usr/bin/env python

from distutils.core import setup

setup(
    name="nlpipe",
    version="0.55",
    description="Simple NLP Pipelinining based on a file system",
    authors=["Wouter van Atteveldt", "Farzam Fanitabasi"],
    author_email="wouter@vanatteveldt.com",
    packages=["nlpipe", "nlpipe.Clients", "nlpipe.Servers", "nlpipe.Tools", "nlpipe.Workers"],
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
        "pytest-flask",
        "peewee"
    ]
)