#class Decklists
from bs4 import BeautifulSoup
import requests
import re
import time
import concurrent.futures

class Player:
	def __init__(self, name, level, decklist):
		self.name = name		
		self.level = level
		self.ptcgo_decklist = RK9ToPTCGO(decklist)
		self.json_decklist = RK9ToJSON(decklist)

class PlayerData:
	def __init__(self, name, level, country):
		self.name = name		
		self.level = level
		self.country = country

def RK9ToPTCGO(page):
	output = ""
	data = page.text
	start = 0
	start = data.find('data-setnum="', start)
	while(start != -1):
		end = data.find('"', start+13)
		if(end != -1 and end != start+13):
			cardData = data[start+13:end]
			basic = cardData.find('misc-')
			if(basic == 0):
				temp = cardData.replace("misc-", "")
				cardData = temp + " Energy Energy "
				if(temp.lower() == "Grass".lower()):
					cardData = cardData + " 1"
				if(temp.lower() == "Fire".lower()):
					cardData = cardData + " 2"
				if(temp.lower() == "Water".lower()):
					cardData = cardData + " 3"
				if(temp.lower() == "Lightning".lower()):
					cardData = cardData + " 4"
				if(temp.lower() ==  "Psychic".lower()):
					cardData = cardData + " 5"
				if(temp.lower() == "Fighting".lower()):
					cardData = cardData + " 6"
				if(temp.lower() == "Darkness".lower()):
					cardData = cardData + " 7"
				if(temp.lower() == "Metal".lower()):
					cardData = cardData + " 8"
				if(temp.lower() == "Fairy".lower()):
					cardData = cardData + " 9"
			
			if(cardData.find('-') == 3):
				cardData = cardData.replace('-', ' ')
			else:
				set = cardData[0:5]
				try:
					if(basic == 0):
						number = cardData[5]
					else:
						number = re.sub("/[^0-9]/", "",cardData[5])
					cardData = set + " " + number
				except:
					cardData = cardData
			start = data.find('data-language="', end+1)
			if(start != -1):
				end = data.find('"', start+15)
				if(end != -1):
					lang = data[start+15:end]
					if(lang == "EN"):
						start = data.find('data-quantity="', end+1)
						if(start != -1):
							end = data.find('"', start+15)
							if(end != -1):
								count = data[start+15:end]
								output = output + "* " + count + " " + cardData + "\n"
								start = data.find('data-setnum="', end+1)
					else:
						start = -1
		else:
			start += 1
	return output


def RK9ToJSON(page):
	output = '{'
	soup = BeautifulSoup(page.content, "lxml")
	table = soup.find("table", {"class":"decklist"})
	pokemonList = table.find("ul", {"class":"pokemon"})
	trainerList = table.find("ul", {"class":"trainer"})
	energyList = table.find("ul", {"class":"energy"})
	pokemons = None
	if pokemonList != None:
		pokemons = pokemonList.find_all("li")
	trainers = None
	if trainerList != None:
		trainers = trainerList.find_all("li")
	energies = None
	if energyList != None:
		energies = energyList.find_all("li")
	output = output + '"pokemon":['
	groupData = ""
	if pokemons != None:
		for card in pokemons:
			count = card.get("data-quantity")
			name = card.get("data-cardname")
			setnumber = card.get("data-setnum")
			number = setnumber.split("-")[1]
			set = setnumber.split("-")[0]
			data = '{"count":' + count + ', "name": "' + name + '", "number":"' + number + '", "set": "' + set + '"}'
			if(len(groupData) > 0):
				groupData = groupData + ","
			groupData = groupData + data
	output = output + groupData
	output = output + ']'

	output = output + ',"trainer":['
	groupData = ""
	if trainers != None:
		for card in trainers:
			count = card.get("data-quantity")
			name = card.get("data-cardname")
			setnumber = card.get("data-setnum")
			if len(setnumber) > 0:
				number = setnumber.split("-")[1]
				set = setnumber.split("-")[0]
				data = '{"count":' + count + ', "name": "' + name + '", "number":"' + number + '", "set": "' + set + '"}'
				if(len(groupData) > 0):
					groupData = groupData + ","
				groupData = groupData + data
	output = output + groupData
	output = output + ']'
	
	output = output + ',"energy":['
	groupData = ""
	if energies != None:
		for card in energies:
			count = card.get("data-quantity")
			name = card.get("data-cardname")
			setnumber = card.get("data-setnum")
			number = setnumber.split("-")[1]
			set = setnumber.split("-")[0]
			data = '{"count":' + count + ', "name": "' + name + '", "number":"' + number + '", "set": "' + set + '"}'
			if(len(groupData) > 0):
				groupData = groupData + ","
			groupData = groupData + data
	output = output + groupData
	output = output + ']'

	output = output + '}'
	return output

def get_status(url, name, level):
	return Player(name, level, requests.get(url=url))

class PlayersData:
	def __init__(self, url):
		self.players = []
		url = 'https://rk9.gg/roster/' + url
		page = requests.get(url)
		soup = BeautifulSoup(page.content, "lxml")
		table = soup.find("table", {"id":"dtLiveRoster"})
		thead = table.find("thead")
		tr = thead.find('tr')
		ths = tr.find_all('th')
		idIndex = -1
		fnIndex = -1
		lnIndex = -1
		cnIndex = -1
		divIndex = -1
		dlIndex = -1
		currentIndex = 0
		for th in ths:
			if th != None:
				if 'ID' in th.text.upper():
					idIndex = currentIndex
				if 'FIRST' in th.text.upper():
					fnIndex = currentIndex
				if 'LAST' in th.text.upper():
					lnIndex = currentIndex
				if 'COUNTRY' in th.text.upper():
					cnIndex = currentIndex
				if 'DIV' in th.text.upper():
					divIndex = currentIndex
				if 'LIST' in th.text.upper():
					dlIndex = currentIndex
				currentIndex += 1
		tbody = table.find("tbody")
		trs = tbody.find_all("tr")
		for tr in trs:
			if tr != None:
				tds = tr.find_all("td")
				popid = ''
				if(idIndex > -1):
					popid = tds[idIndex].text.replace("\n\n", " ").strip()
				surname = ''
				if(fnIndex > -1):
					surname = tds[fnIndex].text.replace("\n\n", " ").strip()
				name = ''
				if(lnIndex > -1):
					name = tds[lnIndex].text.replace("\n\n", " ").strip()
				country = ''
				if(cnIndex > -1):
					country = tds[cnIndex].text.replace("\n\n", " ").strip()
				level = ''
				if(divIndex > -1):
					level = tds[divIndex].text.replace("\n\n", " ").strip()
				if(level == "Junior"):
					level = "Juniors"
				if(level == "Senior"):
					level = "Seniors"
				self.players.append(PlayerData(surname + " " + name, level, country))
	
	def GetCountry(self, p):
		for player in self.players:
			if player.name == p.name and player.level == p.level:
				return player.country.lower()
		return ''



class Decklists:
	def __init__(self, url):
		self.players = []
		urls = []
		names = []
		levels = []
		url = 'https://rk9.gg/roster/' + url
		page = requests.get(url)
		soup = BeautifulSoup(page.content, "lxml")
		table = soup.find("table", {"id":"dtLiveRoster"})
		thead = table.find("thead")
		tr = thead.find('tr')
		ths = tr.find_all('th')
		idIndex = -1
		fnIndex = -1
		lnIndex = -1
		cnIndex = -1
		divIndex = -1
		dlIndex = -1
		currentIndex = 0
		for th in ths:
			if th != None:
				if 'ID' in th.text.upper():
					idIndex = currentIndex
				if 'FIRST' in th.text.upper():
					fnIndex = currentIndex
				if 'LAST' in th.text.upper():
					lnIndex = currentIndex
				if 'COUNTRY' in th.text.upper():
					cnIndex = currentIndex
				if 'DIV' in th.text.upper():
					divIndex = currentIndex
				if 'LIST' in th.text.upper():
					dlIndex = currentIndex
				currentIndex += 1
		tbody = table.find("tbody")
		trs = tbody.find_all("tr")
		for tr in trs:
			if tr != None:
				tds = tr.find_all("td")
				popid = ''
				if(idIndex > -1):
					popid = tds[idIndex].text.replace("\n\n", " ").strip()
				surname = ''
				if(fnIndex > -1):
					surname = tds[fnIndex].text.replace("\n\n", " ").strip()
				name = ''
				if(lnIndex > -1):
					name = tds[lnIndex].text.replace("\n\n", " ").strip()
				country = ''
				if(cnIndex > -1):
					country = tds[cnIndex].text.replace("\n\n", " ").strip()
				level = ''
				if(divIndex > -1):
					level = tds[divIndex].text.replace("\n\n", " ").strip()
				if(level == "Junior"):
					level = "Juniors"
				if(level == "Senior"):
					level = "Seniors"
				listText = ''
				if(dlIndex > -1):
					listText = tds[dlIndex].text.strip().replace(" ", "").replace("\n\n", " ")
				if(listText == "View"):
					a = tds[dlIndex].find('a', href=True)
					urls.append("https://rk9.gg/" + a['href'])
					names.append(surname + " " + name)
					levels.append(level)
		#threading
		with concurrent.futures.ThreadPoolExecutor() as executor:
			futures = []
			for i in range(0, len(urls)):
				futures.append(executor.submit(get_status, url=urls[i], name=names[i], level=levels[i]))

			for future in concurrent.futures.as_completed(futures):
				self.players.append(future.result())
