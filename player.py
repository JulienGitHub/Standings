#class Match : VS a player, with a status [W/L/T -> 2/0/1] and a table number
class Match:
	def __init__(self, player, status, table):
		self.player = player
		self.status = status
		self.table = table

#class Player
class Player:
	#player constructor
	def __init__(self, name, level, id, late):	#(name, level[junior, senior, master], id [unique number, incremental], late [0 if not, -1 if late])
		self.name = name
		self.level = level
		
		#W/T/L counters
		self.wins = 0
		self.ties = 0
		self.losses = 0
		#W/T/L counters for day 2
		self.wins2 = 0
		self.ties2 = 0
		self.losses2 = 0

		#minimum/maximum points. Used for the R/Y/G colors for Day2/TopCut (not 100% working) 
		self.minPoints = 0
		self.maxPoints = 0

		#nb matches completed
		self.completedMatches = 0

		#points (3*W+T)
		self.points = 0

		#list of matches
		self.matches = []
		#player id in tournament (from 1 to ...) : incremented everytime a new player is found on the RK9 pairings' page
		self.id = id
		
		#resistances, minimum 0
		#refers to https://www.pokemon.com/us/play-pokemon/about/tournaments-rules-and-resources > Play! Pokémon Tournament Rules Handbook
		self.WinPercentage = 0.25			#player resistance
		self.OppWinPercentage = 0.25		#opponents' resistance
		self.OppOppWinPercentage = 0.25		#opponents' opponents' resistance

		#if player is dropped, dropRound > 0
		self.dropRound = -1

		#placement after sorting players
		self.topPlacement = 0

		#country if found in /roster/ or within the player's name in the pairings (between [])
		self.country = ""

		#if late : loss round 1 with a drop but back playing round 2
		self.late = late

		#dqed flag : manually added if known, or if player is not in the final published standings
		self.dqed = False

		#country extraction ISO 3166-1 alpha-2 (2 letters)
		if(self.name[len(self.name)-1] == ']'):
			self.country = self.name[len(self.name)-3:len(self.name)-1].lower()

		#decklists (found in /roster/ long after the tournament, or never)
		#ptcgo format
		self.decklist_ptcgo = ""
		#json format
		self.decklist_json = ""

	#addMatch function : adding a game versus another player
	#player : VS player
	#status : -1 still playing / 0 loss / 1 tie / 2 win
	#drop : drop found (loss+drop attributes)
	#isDay2 : is a day 2 match
	#isTop : is a top cut match
	#table : table #
	def addMatch(self, player, status, dropped, isDay2, isTop, table):
		if(self.dropRound > -1):
			#reset for late players
			self.dropRound = -1
		if(status == 0): 									#if loss
			if(player == None): 								#if loss against no one, it means the player is late
				player = Player("LATE", "none", 0, 0) 				#use of a "LATE" player, no level, id 0, not late
			self.losses += 1 									#losses incremented
			if(isDay2 and not isTop): 							#if it is a day 2 match, but not a top cut
				self.losses2 += 1 									#day 2 losses incremented
			self.completedMatches += 1 							#completed matches incremented
		if(status == 1): 									#if tie
			self.ties += 1										#ties incremented
			if(isDay2 and not isTop):							#if it is a day 2 match, but not a top cut
				self.ties2 += 1										#day 2 ties incremented
			self.completedMatches += 1							#completed matches incremented
		if(status == 2): 									#if win
			if(player == None):									#if win against no one, it means the player got a bye
				player = Player("BYE", "none", 0, 0)				#use of a "BYE" player, no level, id 0, not late
			self.wins += 1										#wins incremented
			if(isDay2 and not isTop):							#if it is a day 2 match, but not a top cut
				self.wins2 += 1										#day2 wins incremented
			self.completedMatches += 1							#completed matches incremented
		self.points = self.wins * 3 + self.ties				#compute points
		self.matches.append(Match(player, status, table))	#add match to matches list
		if(dropped):										#if dropped
			self.dropRound = len(self.matches)					#dropround is the number of games played

	#update player's win percentage
	#day1Rounds : number of round in day 1
	#day2Rounds : number of round in day 2
	#currentRound...
	#resistance is calculated every round
	def UpdateWinP(self, day1Rounds, day2Rounds, currentRound):
		if((self.dropRound == -1 or self.dropRound == currentRound)): #if not dropped or dropped this round
			self.WinPercentage = 0
			val = 0
			count = 0
			counter = 0
			for match in self.matches:	#go through all the matches
				if((len(self.matches) >= day1Rounds and counter >= day1Rounds and counter < day2Rounds) or len(self.matches) <= day1Rounds or day1Rounds == 0): #if resistance day2 or resistance day1
					if(match.player != None and not (match.player.name == "BYE")): #do not count at all if BYE
						if(match.status == 2):
							val = val + 1	#+1 for a win
						if(match.status == 1):
							val = val + 0.5 #+0.5 for a tie
						if(match.status == 0):
							val = val + 0	#0 for a loss
						if(match.status != -1):
							count = count + 1 #increment counter
				counter = counter + 1
			if count > 0:
				val = val / count #(wins+0.5ties)/count
			if(val < 0.25):	#if win percentage is less than 0.25, it is defaulted to 0.25
				val = 0.25
			if(self.dropRound > 0 and self.dqed == False): #if dropped, can't be more than 0.75
				if(val > 0.75):
					val = 0.75
			self.WinPercentage = val
	
	#same as UpdateWinP but Opp Win percentage
	def UpdateOppWinP(self, day1Rounds, day2Rounds, currentRound):		
		if((self.dropRound == -1 or self.dropRound == currentRound) and ((currentRound > day1Rounds  and len(self.matches) > day1Rounds) or (currentRound <= day1Rounds))):
			val = 0
			count = 0
			counter = 0
			for match in self.matches:
				if((len(self.matches) >= day1Rounds and counter >= day1Rounds and counter < day2Rounds) or len(self.matches) <= day1Rounds or day1Rounds == 0):
					if(match.player != None and not (match.player.name == "BYE")):
						winP = match.player.WinPercentage
						if winP > 0:
							val = val + winP
							count = count + 1
				counter = counter + 1
			if count > 0:
				val = val / count				
			if(val < 0.25):
				val = 0.25
			self.OppWinPercentage = val

	#same as UpdateWinP but Opp Opp Win percentage
	def UpdateOppOppWinP(self, day1Rounds, day2Rounds, currentRound):				
		if((self.dropRound == -1 or self.dropRound == currentRound) and ((currentRound > day1Rounds  and len(self.matches) > day1Rounds) or (currentRound <= day1Rounds))):
			val = 0
			count = 0
			counter = 0
			for match in self.matches:
				if((len(self.matches) >= day1Rounds and counter >= day1Rounds and counter < day2Rounds) or len(self.matches) <= day1Rounds or day1Rounds == 0):
					if(match.player != None and not (match.player.name == "BYE")):
						val = val + match.player.OppWinPercentage		
						count = count + 1
				counter = counter + 1		
			if count > 0:
				val = val / count
			if(val < 0.25):
				val = 0.25
			self.OppOppWinPercentage = val	

	#special logging/debug methods to output some data
	def __repr__(self):
		output = self.name + " (" + self.level + ") " + str(self.wins) + "-" + str(self.losses) + "-" + str(self.ties) + " -- " + str(self.points) + "pts"
		for match in self.matches:
			output += "\n"
			output += "Vs. " + match.player + " "
			if(match.status == 0):
				output += "L"
			if(match.status == 1):
				output += "T"
			if(match.status == 2):
				output += "W"
		return output

	def __str__(self):
		output = self.name + " (" + self.level + ") " + str(self.wins) + "-" + str(self.losses) + "-" + str(self.ties) + " -- " + str(self.points) + "pts"
		for match in self.matches:
			output += "\n"
			output += "\tVs. " + match.player + " "
			if(match.status == 0):
				output += "L"
			if(match.status == 1):
				output += "T"
			if(match.status == 2):
				output += "W"
		output += "\n\n"
		return output

	#ToText
	def ToTxt(self, rank):
		output = str(rank) + " - " + self.name + " " + str(self.wins) + "-" + str(self.losses) + "-" + str(self.ties) + " -- " + str(self.points) + "pts " + str('%.2f' % (self.OppWinPercentage*100)) + "% " + str('%.2f' % (self.OppOppWinPercentage*100)) + "%"
		output += "\n"
		return output
	
	#ToCSV
	def ToCSV(self, file):
		round = 1
		points = 0
		for match in self.matches:
			file.write((self.name + '\t').encode())
			if(match.player != None):
				file.write((match.player.name + '\t').encode())
			if(match.status == 0):
				file.write(('L\t').encode())
			if(match.status == 1):
				file.write(('T\t').encode())
				points += 1
			if(match.status == 2):
				file.write(('W\t').encode())
				points += 3
			file.write((str(points) + '\t').encode())
			file.write((str(round) + '\n').encode())
			round += 1
	#toJson
	def ToJSON(self, file):
		file.write(('{').encode())
		file.write(('"name":"' + self.name.replace('"', '\\"') + '",').encode())
		file.write(('"placing":' + str(self.topPlacement) + ',').encode())
		file.write(('"record":{"wins":' + str(self.wins) + ',"losses":' + str(self.losses) + ',"ties":' + str(self.ties) + '},').encode())
		file.write(('"resistances":{"self":' + str(self.WinPercentage) + ',"opp":' + str(self.OppWinPercentage) + ',"oppopp":' + str(self.OppOppWinPercentage) + '},').encode())
		if(len(self.decklist_json) > 0):
			file.write(('"decklist":'+ self.decklist_json +',').encode())
		else:
			file.write(('"decklist":"",').encode())
		file.write(('"drop":'+ str(self.dropRound) + ',').encode())
		
		file.write(('"rounds":{').encode())
		round = 1
		for match in self.matches:
			name = "none"
			if(match.player != None):
				name = match.player.name
			file.write(('"' + str(round) + '":{"name":"'+ name.replace('"', '\\"') + '","result":').encode())
			if(match.status == 0):
				file.write(('"L"').encode())
			if(match.status == 1):
				file.write(('"T"').encode())
			if(match.status == 2):
				file.write(('"W"').encode())
			if(match.status == -1):
				file.write(('null').encode())
			file.write((',"table":').encode())
			file.write((str(match.table)).encode())
			file.write(('}').encode())
			if(round < len(self.matches)):
				file.write((',').encode())
			round += 1
		file.write(('}').encode())
		
		file.write(('}').encode())

	#toHTML
	def ToHtml(self):
		output = ""
		round = 0
		for match in self.matches:
			if(match.player != None):
				output += '<p'
				cssColor = ""
				if(match.status == -1):
					cssColor = ' class="r"'
				if(match.status == 0):
					cssColor = ' class="l"'
				if(match.status == 1):
					cssColor = ' class="t"'
				if(match.status == 2):
					cssColor = ' class="w"'
				output += cssColor + '>R' + str(round+1) + ' ['+str(match.table)+'] Vs. <a href="#' + str(match.player.id) +'" '+ cssColor+'>' + match.player.name + "</a> "
				if(not(match.player.name == 'BYE' or match.player.name == 'LATE')):
					output += str(match.player.wins) + "-" + str(match.player.losses) + "-" + str(match.player.ties)
				
				if(match.status == -1 and match.player.dropRound == -1):
					output += " Currently Playing"
				if(match.status == 0):
					output += " L"
				if(match.status == 1):
					output += " T"
				if(match.status == 2):
					output += " W"
				if(match.player.dqed):
					output += "<i> dqed</i>"
				else:
					if(match.player.dropRound > 0):
						output += "<i> dropped</i>"
				output += "</p>"
			round = round+1
		
		return output