Installation
------------

Install directly from github.com

    $ pip install git+git://github.com/yejianye/sc2analyzer.git

Or clone this repository and run

	$ python setup.py install

NOTES, this tool depends on the latest version of `sc2reader` on github.com (https://github.com/GraylinKim/sc2reader). sc2reader on PyPi is not up-to-date. To install latest version of sc2reader

	$ pip install git+git://github.com/GraylinKim/sc2reader.git 

sc2analyzer - A tool to analyze Starcraft2 Replay files
-------------------------------------------------------

sc2analyzer is used for extracting interesting game statistics from Starcraft2 replay files (.sc2replay), including:

- General game information including player names, player races, game result, version, map, length etc.
- Player names and races.
- Building orders, which would be useful for learning a specific game strategy.

The script requires the latest version of sc2reader package (https://github.com/GraylinKim/sc2reader).

Example usage:

	$ sc2analyzer example.sc2replay

sc2search - A tool to query Starcraft2 replay files based on various kinds of conditions
----------------------------------------------------------------------------------------
Assume you have tons of .sc2replay files on your computer, and you may want to categorize them by competition type, by players, even by strategies used in the game. Image you want to learn the building order for PVT dark templar rush, sc2search could help you search replays that uses this strategies within your replay collection. Supported filter condition includes,

- Player name
- Competition type (TVP, TVZ, PVZ etc)
- Game length 
- Strategy

To list all the strategies pre-defined, use 

	$ sc2search --list-strategies

Example usage:

	$ sc2search --strategy=pvt_dt_rush --max-length=12 --win-only

The above example will search all replays where the Protoss player uses dark templar rush against Terran player and he won the game within 12 minutes.

sc2search will place a default configuration file sc2search.ini under your home directory. To let sc2search know where all your replay files are, and where it should put its replay database file. You need specify the following options,

- rep_path: the root directory for all your replay files
- db_path: the directory where sc2search would store all the metadata for your replays


