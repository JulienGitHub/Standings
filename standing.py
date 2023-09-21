#class Standing
class Standing:
	def __init__(self, tournamentName, tournamentDirectory, folder, divisionName, urls, dqed, type="TCG"):
		self.tournamentName = str(tournamentName)
		self.tournamentDirectory = str(tournamentDirectory)
		self.divisionName = str(divisionName)
		self.urls = urls
		self.level = ""
		self.roundsDay1 = 999
		self.roundsDay2 = 999
		self.players = []
		self.playerID = 1
		self.directory = folder
		self.dqed = dqed
		self.hidden = []
		self.currentRound = 0
		self.type = type	#TCG/VGC1(1 Day)/VGC2(2Days)

	def __repr__(self):
		output = self.tournamentName + " (in " + self.tournamentDirectory + ") " + self.divisionName
		output += "\n\tURLS:"
		for url in self.urls:
			output += "\n"
			output += url
		return output

	def __str__(self):
		output = self.tournamentName + " (in " + self.tournamentDirectory + ") " + self.divisionName
		output += "\n\tURLS:"
		for url in self.urls:
			output += "\n\t\t"
			output += url
		return output