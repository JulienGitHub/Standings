# Standings
A Python script to generate Pokémon standings from RK9 pairings' page

This project was started to be able to follow an event from home: seeing who played against who, the standings, the resistances to be able to watch the top cut race.
The streams only showed sometimes some part of the standings.

This script loads a RK9 pairing page and produces json and csv files for each division.

This script accepts 4 parameters : 

	--url	: mandatory, to specify the RK9 tournament id. Only the id is needed, the rest of the url is added by the script. NAIC 2023 would be NA1KYsUUz7fBID8XkZHZ
 	--id	: mandatory, to specify the internal id of the tournament. Used by pokedata and pokestats.
	--decklists	: optional, false if not specified. Retrieves the decklists from the /roster/ page
 	--roster	: optional, false if not specified. Retrieves the players' data from the /roster/ page (in case the countries are in the roster but not in the pairings)

You can remove the parameters part and hardcode the data used by the mainWorker function.

Some standings get broken by bad encoding during tournaments, just hope it will be fixed.
DQs not being made public, the last parameter of the Standing() constructor is to manually add the names of DQed players.
After the tournament is over, DQs are found by not seeing a player in the standings.


Some parts could probably be optimized, most parts are probably looking bad code-wise, ¯\\_(ツ)_/¯


"pip install beautifulsoup4" for the Beautiful Soup library (for pulling data out of HTML and XML files)

"pip install regex" for the regex library

"pip install unicodedata2" for the unicode library


I hope I am not missing any other library needed, and I hope these are the right commands. A simple Google search with any missing import should bring you the solution.
