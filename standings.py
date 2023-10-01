import time
import requests
from datetime import datetime
from bs4 import BeautifulSoup
import unicodedata
import sys
import json
import re
import argparse

#my imports
from standing import Standing
from player import Player
from decklists import Decklists, PlayersData


import math
from collections import Counter

def RemoveCountry(name):
	start = name.find(' [')
	stop = name.find(']')
	if(stop-start == 4):
		return name[0:start]
	return name

#removing accents (for js calls)
def strip_accents(input_str):
	nfkd_form = unicodedata.normalize('NFKD', input_str)
	only_ascii = nfkd_form.encode('ASCII', 'ignore')
	return only_ascii

#points access for sorting function
def Points(elem):
	return elem.points

def mainWorker(directory, link, getDecklists, getRoster):
	lastPageLoaded = ""
	page = None
	soup = None

	#sys.stdout.flush()
	starttime = time.time()
	try:
		url = 'https://rk9.gg/tournament/' + link
		page = requests.get(url)
		soup = BeautifulSoup(page.content, "lxml")

		pageTitle = soup.find('h3', {'class': 'mb-0'}).text
		title = pageTitle.split('\n')[0]
		date =  pageTitle.split('\n')[1]

		winners = []
		rounds = []
		nbplayers = []
		now = datetime.now() #current date and time
		strTime = now.strftime("%Y/%m/%d - %H:%M:%S")
		print('starting at : ' + strTime)

		standings = []		
		
		standings.append(Standing(title, directory, 'juniors', 'Juniors', [link], []))
		standings.append(Standing(title, directory, 'seniors', 'Seniors', [link], []))
		standings.append(Standing(title, directory, 'masters', 'Masters', [link], []))
		
		decklists_players = None
		roster = None
		if getDecklists:
			print('Reading decklists')
			decklists_players = Decklists(link)
		else:
			print('Not reading decklists')
		if getRoster:
			print('Reading roster')
			roster = PlayersData(link)
		else:
			print('Not reading roster')

		for standing in standings:
			print("Standing : " + standing.tournamentName + " - in " + standing.tournamentDirectory + "/" + standing.directory + " for " + standing.divisionName + " [" + standing.level + "/" + str(standing.roundsDay1) + "/" + str(standing.roundsDay2) + "]")
			winner = None
			for url in standing.urls:
				#requesting RK9 pairings webpage
				url = 'https://rk9.gg/pairings/' + url
				print("\t" + url)
				if(lastPageLoaded != url):
					lastPageLoaded = url
					page = requests.get(url)
					#page content to BeautifulSoup
					soup = BeautifulSoup(page.content, "lxml")

				#finding out how many rounds on the page							
				iRoundsFromUrl = 0
				for ultag in soup.find_all('ul', {'class': 'nav nav-pills'}):
					for litag in ultag.find_all('li'):
						for aria in litag.find_all('a'):
							sp = aria.text.split(" ")
							if(sp[0][0:-1].lower() == standing.divisionName[0:len(sp[0][0:-1])].lower()):
								iRoundsFromUrl = int(sp[len(sp)-1])
								standing.level = str(aria['aria-controls'])

				roundsSet = False
				standing.currentRound = iRoundsFromUrl

				rounds.append(iRoundsFromUrl)

				#scrapping standings if available, to compare results later
				strToFind = standing.level + "-standings"
				standingPublishedData = soup.find('div', attrs={'id':strToFind})
				publishedStandings = []
				if(standingPublishedData):
					standingPublished = [y for y in [x.strip() for x in standingPublishedData.text.split('\n')] if y]
					for line in standingPublished:
						data = line.split(' ')
						pos = data[0].replace('.', '')
						player = ''
						for i in range(1, len(data)):
							if(i > 1):
								player += ' '
							player += data[i]
						publishedStandings.append(player.replace('  ', ' '))

				jsonExportTables = open(standing.directory + standing.tournamentDirectory + "tables.json", 'wb')
				jsonExportTables.write(('[').encode())

				stillPlaying = 0

				for iRounds in range(iRoundsFromUrl):
					firstTableData = True
					if(iRounds > 0):
						jsonExportTables.write((',').encode())
					jsonExportTables.write(('{"tables":[').encode())
					strToFind = standing.level + "R" + str(iRounds+1)
					round_data = soup.find('div', attrs={'id':strToFind})
					stillPlaying = 0
					for match_data in round_data.find_all('div', attrs={'class':'match'}):							
						player1 = ""
						player2 = ""
						p1status = -1
						p2status = -1
						p1dropped = False
						p2dropped = False
						p1late = 0
						p2late = 0
						scores1 = []
						scores2 = []
						p1 = None
						p2 = None
						addP1 = True
						addP2 = True
						table = "0"
						tableData = match_data.find('div', attrs={'class':'col-2'})
						if tableData:
							tableData = tableData.find('span', attrs={'class':'tablenumber'})
							if tableData:
								table = tableData.text								
						player_data = match_data.find('div', attrs={'class':'player1'})
						textData = player_data.text.split("\n")
						name = player_data.find('span', attrs={'class':'name'})
						if(name):
							score = textData[3].strip().replace('(', '').replace(')', '')
							scores1 = re.split('-', score)
							player1 = re.sub('\s+',' ', name.text)
							if(str(player_data).find(" dropped") != -1):
								p1dropped = True
							if(str(player_data).find(" winner") != -1):
								p1status = 2
							if(str(player_data).find(" loser") != -1):
								p1status = 0
							if(str(player_data).find(" tie") != -1):
								p1status = 1
							if(p1status == -1 and not p1dropped):
								if(iRounds+1 < iRoundsFromUrl):
									p1status = 0
									if(iRounds == 0):
										p1late = -1
								
								
						player_data = match_data.find('div', attrs={'class':'player2'})
						textData = player_data.text.split("\n")
						name = player_data.find('span', attrs={'class':'name'})
						if(name):
							score = textData[3].strip().replace('(', '').replace(')', '')
							scores2 = re.split('-', score)
							player2 = re.sub('\s+',' ', name.text)
							if(str(player_data).find(" dropped") != -1):
								p2dropped = True
							if(str(player_data).find(" winner") != -1):
								p2status = 2
							if(str(player_data).find(" loser") != -1):
								p2status = 0
							if(str(player_data).find(" tie") != -1):
								p2status = 1
							if(p2status == -1 and not p2dropped):
								if(iRounds+1 < iRoundsFromUrl):
									p2status = 0
									if(iRounds == 0):
										p2late = -1
						
						if(len(player1) > 0):								
							for player in filter(lambda y: y.name == player1, standing.players):
								if(p1status == -1 and (player.wins == int(scores1[0]) and player.losses == int(scores1[1]) and player.ties == int(scores1[2]))):
									p1 = player
									addP1 = False
								if(p1status == 0 and (player.wins == int(scores1[0]) and player.losses + 1 == int(scores1[1]) and player.ties == int(scores1[2]))):
									p1 = player
									addP1 = False
								if(p1status == 1 and (player.wins == int(scores1[0]) and player.losses == int(scores1[1]) and player.ties + 1 == int(scores1[2]))):
									p1 = player
									addP1 = False
								if(p1status == 2 and (player.wins + 1 == int(scores1[0]) and player.losses == int(scores1[1]) and player.ties == int(scores1[2]))):
									p1 = player
									addP1 = False
								if(p1dropped):
									if(p1 == None):
										if(player.wins == int(scores1[0]) and player.losses == int(scores1[1]) and player.ties == int(scores1[2])):
											p1 = player
											player.dropRound = iRounds+1
											addP1 = False

							for player in filter(lambda y: y.name == player2, standing.players):
								if(p2status == -1 and (player.wins == int(scores2[0]) and player.losses == int(scores2[1]) and player.ties == int(scores2[2]))):
									p2 = player
									addP2 = False
								if(p2status == 0 and (player.wins == int(scores2[0]) and player.losses + 1 == int(scores2[1]) and player.ties == int(scores2[2]))):
									p2 = player
									addP2 = False
								if(p2status == 1 and (player.wins == int(scores2[0]) and player.losses == int(scores2[1]) and player.ties + 1 == int(scores2[2]))):
									p2 = player
									addP2 = False
								if(p2status == 2 and (player.wins + 1 == int(scores2[0]) and player.losses == int(scores2[1]) and player.ties == int(scores2[2]))):
									p2 = player
									addP2 = False
								if(p2dropped):
									if(p2 == None):
										if(player.wins == int(scores2[0]) and player.losses == int(scores2[1]) and player.ties == int(scores2[2])):
											p2 = player
											player.dropRound = iRounds+1
											addP2 = False							

						if(p1 == None):
							if(len(player1) > 0):
								standing.playerID = standing.playerID + 1										
								p1 = Player(player1, standing.divisionName, standing.playerID, p1late)
								if(p1.country == "" and roster != None):
									p1.country = roster.GetCountry(p1)
								if(p1.name in standing.dqed or (len(publishedStandings) > 0 and p1.name not in publishedStandings)):
									p1.dqed = True
						if(p2 == None):
							if(len(player2) > 0):
								standing.playerID = standing.playerID + 1
								p2 = Player(player2, standing.divisionName, standing.playerID, p2late)
								if(p2.country == "" and roster != None):
									p2.country = roster.GetCountry(p2)
								if(p2.name in standing.dqed or (len(publishedStandings) > 0 and p2.name not in publishedStandings)):
									p2.dqed = True
						if(p1 != None):
							if(p2 == None):
								p1.addMatch(None, p1status, p1dropped, iRounds+1 > standing.roundsDay1, iRounds+1 > standing.roundsDay2, table)
							else:
								p1.addMatch(p2, p1status, p1dropped, iRounds+1 > standing.roundsDay1, iRounds+1 > standing.roundsDay2, table)
							if(addP1 == True):
								standing.players.append(p1)
							if p1status == -1 and not p1.dropRound>-1:
								stillPlaying += 1

						if(p2 != None):
							if(p1 == None):
								p2.addMatch(None, p2status, p2dropped, iRounds+1 > standing.roundsDay1, iRounds+1 > standing.roundsDay2, table)
							else:
								p2.addMatch(p1, p2status, p2dropped, iRounds+1 > standing.roundsDay1, iRounds+1 > standing.roundsDay2, table)
							if(addP2 == True):
								standing.players.append(p2)
						
						if(p1 != None and p2 != None):
							if(not firstTableData):
								jsonExportTables.write((',').encode())
							jsonExportTables.write(('{').encode())
							jsonExportTables.write(('"table":'+str(table)+",").encode())
							jsonExportTables.write(('"players":[{"name":').encode())
							if(p1 != None):
								jsonExportTables.write(('"'+p1.name.replace('"', '\\"')+'"').encode())
							else:
								jsonExportTables.write(('null').encode())
							jsonExportTables.write((',"result":').encode())
							if(p1status == 0):
								jsonExportTables.write(('"L"').encode())
							if(p1status == 1):
								jsonExportTables.write(('"T"').encode())
							if(p1status == 2):
								jsonExportTables.write(('"W"').encode())
							if(p1status == -1):
								jsonExportTables.write(('null').encode())
							jsonExportTables.write((',"record":{"wins":' + str(p1.wins) + ',"losses":' + str(p1.losses) + ',"ties":' + str(p1.ties) + '}').encode())
							jsonExportTables.write(('},{"name":').encode())
							if(p2 != None):
								jsonExportTables.write(('"'+p2.name.replace('"', '\\"')+'"').encode())
							else:
								jsonExportTables.write(('null').encode())
							jsonExportTables.write((',"result":').encode())
							if(p2status == 0):
								jsonExportTables.write(('"L"').encode())
							if(p2status == 1):
								jsonExportTables.write(('"T"').encode())
							if(p2status == 2):
								jsonExportTables.write(('"W"').encode())
							if(p2status == -1):
								jsonExportTables.write(('null').encode())
							jsonExportTables.write((',"record":{"wins":' + str(p2.wins) + ',"losses":' + str(p2.losses) + ',"ties":' + str(p2.ties) + '}}').encode())
							jsonExportTables.write((']').encode())
							jsonExportTables.write(('}').encode())
							firstTableData = False
					
					if(len(standing.hidden)>0):
						for player in standing.players:
							if(player.name in standing.hidden):
								standing.players.remove(player)

					nbPlayers = len(standing.players)

					for player in standing.players:
						if((len(player.matches) >= standing.roundsDay1) or standing.roundsDay1 > iRounds+1):
							player.UpdateWinP(standing.roundsDay1, standing.roundsDay2, iRounds+1)
					for player in standing.players:
						if((len(player.matches) >= standing.roundsDay1) or standing.roundsDay1 > iRounds+1):
							player.UpdateOppWinP(standing.roundsDay1, standing.roundsDay2, iRounds+1)
					for player in standing.players:
						if((len(player.matches) >= standing.roundsDay1) or standing.roundsDay1 > iRounds+1):
							player.UpdateOppOppWinP(standing.roundsDay1, standing.roundsDay2, iRounds+1)

					if(iRounds+1 <= standing.roundsDay2):
						standing.players.sort(key=lambda p:(not p.dqed, p.points, p.late, round(p.OppWinPercentage*100, 2), round(p.OppOppWinPercentage*100, 2)), reverse=True)
						placement = 1
						for player in standing.players:
							if(not player.dqed):
								player.topPlacement = placement
								placement = placement + 1
							else:
								player.topPlacement = 9999
					else:
						if(iRounds+1 > standing.roundsDay2):
							for place in range(nbPlayers):
								if(len(standing.players[place].matches) == iRounds+1):
									if(standing.players[place].matches[len(standing.players[place].matches)-1].status == 2):#if top win
										stop = False
										for above in range(place-1, -1, -1):
											if(stop == False):
												if(len(standing.players[place].matches) == len(standing.players[above].matches)):
													if(standing.players[above].matches[len(standing.players[place].matches)-1].status == 2):#if player above won, stop searching
														stop = True
													if(standing.players[above].matches[len(standing.players[place].matches)-1].status == 0):#if player above lost, swap placement
														tempPlacement = standing.players[above].topPlacement
														standing.players[above].topPlacement = standing.players[place].topPlacement
														standing.players[place].topPlacement = tempPlacement
														standing.players.sort(key=lambda p:(not p.dqed, nbPlayers-p.topPlacement-1, p.points, p.late, round(p.OppWinPercentage*100, 2), round(p.OppOppWinPercentage*100, 2)), reverse=True)
														place = place - 1
														above = -1
					
					#rounds depending on attendance
					if(standing.type == "TCG" or standing.type == "VGC2"):
						if(standing.roundsDay1 == 999):
							roundsSet = True
							if(4 <= nbPlayers <= 8):
								standing.roundsDay1 = 3
								standing.roundsDay2 = 3
							if(9 <= nbPlayers <= 12):
								standing.roundsDay1 = 4
								standing.roundsDay2 = 4
							if(13 <= nbPlayers <= 20):
								standing.roundsDay1 = 5
								standing.roundsDay2 = 5
							if(21 <= nbPlayers <= 32):
								standing.roundsDay1 = 5
								standing.roundsDay2 = 5
							if(33 <= nbPlayers <= 64):
								standing.roundsDay1 = 6
								standing.roundsDay2 = 6
							if(65 <= nbPlayers <= 128):
								standing.roundsDay1 = 7
								standing.roundsDay2 = 7
							if(129 <= nbPlayers <= 226):
								standing.roundsDay1 = 8
								standing.roundsDay2 = 8
							if(227 <= nbPlayers <= 799):
								standing.roundsDay1 = 9
								standing.roundsDay2 = 14
							if(nbPlayers >= 800):
								standing.roundsDay1 = 9
								standing.roundsDay2 = 15
					if(standing.type == "VGC1"):
						if(standing.roundsDay1 == 999):
							roundsSet = True
							if(4 and nbPlayers < 8):
								standing.roundsDay1 = 3
							if(nbPlayers == 8):
								standing.roundsDay1 = 3
							if(9 <= nbPlayers <= 16):
								standing.roundsDay1 = 4
							if(17 <= nbPlayers <= 32):
								standing.roundsDay1 = 5
							if(33 <= nbPlayers <= 64):
								standing.roundsDay1 = 6
							if(65 <= nbPlayers <= 128):
								standing.roundsDay1 = 7
							if(129 <= nbPlayers <= 226):
								standing.roundsDay1 = 8
							if(227 <= nbPlayers <= 256):
								standing.roundsDay1 = 8
							if(257 <= nbPlayers <= 409):
								standing.roundsDay1 = 9
							if(410 <= nbPlayers <= 512):
								standing.roundsDay1 = 9
							if(nbPlayers >= 513):
								standing.roundsDay1 = 10
							standing.roundsDay2 = standing.roundsDay1						
					if(roundsSet == True and iRounds == 0):
						print("Standing : " + standing.type + " - " + standing.tournamentName + " - in " + standing.tournamentDirectory + "/" + standing.directory + " for " + standing.divisionName + " NbPlayers: "+ str(len(standing.players)) + " -> [" + standing.level + "/" + str(standing.roundsDay1) + "/" + str(standing.roundsDay2) + "]")
						jsonPlayers = open(standing.directory + standing.tournamentDirectory + "players.json", 'wb')
						jsonPlayers.write(('{"players":[').encode())
						for player in standing.players:
							jsonPlayers.write(('{"id":"'+str(player.id)+'","name":"'+str(player.name)+'"},').encode())
						jsonPlayers.write((']}').encode())
						jsonPlayers.close()

					if(decklists_players):
						for player in standing.players:
							deck_index = -1
							pos = -1
							for p in decklists_players.players:
								pos = pos + 1
								if((p.name.upper() == player.name.upper() or RemoveCountry(p.name).upper() == RemoveCountry(player.name).upper()) and p.level == player.level):
									deck_index = pos
									break
							if(deck_index != -1):
								player.decklist_ptcgo = decklists_players.players[deck_index].ptcgo_decklist
								player.decklist_json = decklists_players.players[deck_index].json_decklist
					
					
					if(iRounds+1 == standing.roundsDay2+3 and stillPlaying == 0):
						winner = standing.players[0]
							
					jsonExportTables.write((']}').encode())
			
			countries = []
			for player in standing.players:
				countries.append(player.country)
			countryCounter=Counter(countries)
			namesCountries=list(countryCounter.keys())
			countCountries=list(countryCounter.values())

			if len(countries)>0:
				countCountries, namesCountries = zip(*sorted(zip(countCountries, namesCountries), reverse=True))
			
			f = open('tournaments.json', encoding="utf-8")
			data = json.load(f)
			f.close()

			# Iterating through the json
			# list
			if(data != None):
				dataAdded = False				
				for tourn in data:
					if(tourn['id'] == standing.tournamentDirectory):
						if(len(standing.players) > 0):
							tourn['lastUpdated'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")
							tourn['roundNumbers'][standing.directory.lower()] = iRoundsFromUrl
							if "players" not in tourn:
								tourn['players'] = {}
							tourn['players'][standing.directory.lower()] = len(standing.players)
							if(winner != None):
								tourn['winners'][standing.directory.lower()] = winner.name
							if(winner != None and standing.directory.lower() == 'masters'):
								tourn['tournamentStatus'] = "finished"
							else:
								tourn['tournamentStatus'] = "running"
						dataAdded = True
				if(not dataAdded):
					months = {'jan': '01', 'feb': '02', 'mar': '03', 'apr': '04', 'may': '05', 'jun': '06', 'jul': '07', 'aug': '08', 'sep': '09', 'oct': '10', 'nov': '11', 'dec': '12'}
					dateFields = date.replace('–', ' ').replace('-', ' ').replace(', ', ' ').split(" ")
					if len(dateFields) > 4:
						startDate = dateFields[4] + '-' + months[dateFields[0].strip()[:3].lower()] + '-' + f'{int(dateFields[1]):02d}'
						endDate = dateFields[4] + '-' + months[dateFields[2].strip()[:3].lower()] + '-' + f'{int(dateFields[3]):02d}'
					else:
						startDate = dateFields[3] + '-' + months[dateFields[0].strip()[:3].lower()] + '-' + f'{int(dateFields[1]):02d}'
						endDate = dateFields[3] + '-' + months[dateFields[0].strip()[:3].lower()] + '-' + f'{int(dateFields[2]):02d}'
					
					newData = {"id": standing.tournamentDirectory, "name": standing.tournamentName, "date": {"start": startDate, "end": endDate}, "decklists": 0, "players": {"juniors": 0, "seniors": 0, "masters": 0}, "winners": {"juniors": None, "seniors": None, "masters": None}, "tournamentStatus": "not-started", "roundNumbers": {"juniors": None, "seniors": None, "masters": None}, "lastUpdated": datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f"), "rk9link": standing.urls[0]}
					data.append(newData)

			with open("tournaments.json", "w") as outfile:
				json.dump(data, outfile)
			nbRounds = 0

			csvExport = open(standing.directory + standing.tournamentDirectory + ".csv", 'wb')
			for player in standing.players:
				if(player):
					player.ToCSV(csvExport)
			csvExport.close()
			
			if(decklists_players):
				for player in standing.players:
					deck_index = -1
					pos = -1
					for p in decklists_players.players:
						pos = pos + 1
						if((p.name == player.name or RemoveCountry(p.name) == player.name) and p.level == player.level):
							deck_index = pos
							break
					if(deck_index != -1):
						player.decklist_ptcgo = decklists_players.players[deck_index].ptcgo_decklist
						player.decklist_json = decklists_players.players[deck_index].json_decklist
				
			jsonExport = open(standing.directory + standing.tournamentDirectory + ".json", 'wb')
			jsonExport.write(('[').encode())
			first = True
			for player in standing.players:
				if(player):
					if(not first):
						jsonExport.write((',').encode())
					player.ToJSON(jsonExport)
					first = False
			jsonExport.write((']').encode())
			jsonExport.close()

			jsonExportTables.write((']').encode())
			jsonExportTables.close()
			
		now = datetime.now() #current date and time
		print('Ending at ' + now.strftime("%Y/%m/%d - %H:%M:%S") + " with no issues")
	except Exception as e:
		print(e)
		now = datetime.now() #current date and time
		print('Ending at ' + now.strftime("%Y/%m/%d - %H:%M:%S") + " WITH ISSUES")

if __name__ == "__main__":
	parser = argparse.ArgumentParser()
	parser.add_argument("--url")
	parser.add_argument("--id")
	parser.add_argument("--decklists", action="store_true", help="read decklists from /roster/ page")
	parser.add_argument("--roster", action="store_true", help="read roster from /roster/ page")
	
	args = parser.parse_args()

	"""exemple: (Barcelona)
	id = '0000090'
	url = 'BA189xznzDvlCdfoQlBC'
	"""
	starttime = time.time()
	while True:
		try:
			mainWorker(args.id, args.url, args.decklists, args.roster)
		except Exception as e:
			print(e)
		time.sleep(240.0 - ((time.time() - starttime) % 120.0))
