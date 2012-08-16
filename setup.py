import setuptools, sys

setuptools.setup(
    name="sc2analyzer",
    version='0.1.0',
    license="MIT",

    author="Ryan Ye",
    author_email="yejianye@gmail.com",
    url="https://github.com/yejianye/sc2analyzer",

    description="Utility for analyzing interesting events and statistics in Starcraft2 Replay files",
    long_description=open("README.txt").read(),
    keywords=["starcraft 2","sc2","replay"],
    classifiers=[
            "Environment :: Console",
            "Development Status :: 3 - Alpha",
            "Programming Language :: Python",
            "Programming Language :: Python :: 2.7",
            "Intended Audience :: Developers",
            "License :: OSI Approved :: MIT License",
            "Natural Language :: English",
            "Operating System :: OS Independent",
            "Environment :: Other Environment",
            "Topic :: Utilities",
            "Topic :: Software Development :: Libraries",
            "Topic :: Games/Entertainment :: Real Time Strategy",
        ],
    entry_points={
        'console_scripts': [
            'sc2analyzer = sc2analyzer.analyzer:main',
            'sc2search = sc2analyzer.search:main',
        ]
    },
    install_requires=['sc2reader'],
    packages=['sc2analyzer', 'msgpack'],
)
