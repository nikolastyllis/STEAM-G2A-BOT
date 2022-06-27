import discord
from discord.ext import commands
import requests
import json
from bs4 import BeautifulSoup
import re

#set intents
intents = discord.Intents().all()
intents.members = True

#set client
client = commands.Bot(command_prefix = '$', help_command = None, intents = intents)

@client.event
async def on_ready():
	print('Bot ready.')

#get response function
async def getResponse(url):
	print(url)
	headers = {
	'accept-language': 'en-GB,en-US;q=0.9,en;q=0.8',
	'user-agent': 'Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/97.0.4692.71 Mobile Safari/537.36'
	}
	response = requests.get(url, headers=headers)
	print(response.status_code)
	return response

async def loadResponseAsJson(response):
	json_data = json.loads(response.text)
	return json_data

async def getG2aGameLink(json_data):
	base = 'https://www.g2a.com'
	slug = json_data['data']['items'][0]['href']
	tag = '?gtag=aa4581e1ab'
	url = base + slug + tag
	return url

#form G2A results url function
async def formG2aResultsUrl(query):
	base = 'https://www.g2a.com/search/api/v2/products?itemsPerPage=1&phrase='
	query = query + ' steam GLOBAL'
	query = query.replace(' ', '+')
	resultsUrl = base + query
	return resultsUrl

#get G2A gameID
async def getG2aGameID(json_data):
	gameID = json_data['data']['items'][0]['marketplaceId']
	return gameID

#get G2A game title
async def getG2aGameTitle(json_data):
	gameTitle = json_data['data']['items'][0]['name']
	return gameTitle

#extract float from string
async def getFloatFromString(string):
	result = re.findall(r"[-+]?\d*\.\d+|\d+", string)
	return result[0]

#get G2A game price
async def getG2aGamePrice(json_data):
	price = json_data['a'][str(list(json_data['a'].keys())[0])]['fb']
	price = await getFloatFromString(price)
	return price

#form G2A price url
async def formG2aPriceUrl(gameID):
	base = 'https://www.g2a.com/marketplace/product/auctions/?id='
	priceUrl = base + str(gameID)
	return priceUrl

#get steam game image
async def getSteamGameImage(json_data, appID):
	gameImage = json_data[appID]['data']['header_image']
	return gameImage

#get steam game desc
async def getSteamGameDesc(json_data, appID):
	gameDesc = json_data[appID]['data']['short_description']
	return gameDesc

#get steam game title
async def getSteamGameTitle(json_data, appID):
	gameTitle = json_data[appID]['data']['name']
	return gameTitle

#get steam game price
async def getSteamGamePrice(json_data, appID):
	try:
		gamePrice = json_data[appID]['data']['price_overview']['final_formatted']
		gamePrice = await getFloatFromString(gamePrice)
	except:
		gamePrice = 0
	return gamePrice

#form G2A game object
async def getG2aGame(query):
	resultsUrl = await formG2aResultsUrl(query)
	response = await getResponse(resultsUrl)
	results_json_data = await loadResponseAsJson(response)
	if results_json_data['meta']['totalResults'] == 0:
		return [0,'?', '?', '?']

	#gameTitle = await getG2aGameTitle(results_json_data)
	gameID = await getG2aGameID(results_json_data)
	gameLink = await getG2aGameLink(results_json_data)
	priceUrl = await formG2aPriceUrl(gameID)
	response = await getResponse(priceUrl)
	price_json_data = await loadResponseAsJson(response)
	try:
		gamePrice = await getG2aGamePrice(price_json_data)
	except:
		return [0,'?', '?', '?']

	return [1, 'G2A', gamePrice, gameLink]

#form Steam game object
async def getSteamGame(query):
	resultsUrl = await formSteamResultsUrl(query)
	response = await getResponse(resultsUrl)
	try:
		gameLink = await getSteamGameLink(response)
	except:
		return [0, '?', '?', '?', '?']

	appID = await getSteamGameID(gameLink)
	apiLink = await getSteamPriceUrl(appID)
	response = await getResponse(apiLink)
	price_json_data = await loadResponseAsJson(response)
	gameTitle = await getSteamGameTitle(price_json_data, appID)
	gameImage = await getSteamGameImage(price_json_data, appID)
	#gameDesc = await getSteamGameDesc(price_json_data, appID)
	gamePrice = await getSteamGamePrice(price_json_data, appID)

	if gamePrice == 0:
		return [0, '?', '?', '?', '?']
	
	return [1, gameTitle, gamePrice, gameLink, gameImage]

#form Steam results url function
async def formSteamResultsUrl(query):
	base = 'https://store.steampowered.com/search/?term='
	query = query.replace(' ', '+')
	resultsUrl = base + query
	return resultsUrl

#get steam product link
async def getSteamGameLink(response):
	soup = BeautifulSoup(response.text,"lxml")
	a = soup.find('a',{'class':'search_result_row ds_collapse_flag'}, href=True)
	url = a['href']
	print(url)
	return url

#get int from string
async def getIntFromString(string):
	num = re.search(r'\d+', string).group()
	return num

#get steam gameID
async def getSteamGameID(url):
	gameID = await getIntFromString(url)
	return gameID

#get steam game details
async def getSteamPriceUrl(appID):
	base = 'http://store.steampowered.com/api/appdetails?appids='
	cc = '&cc=au'
	url = base + appID + cc
	return url

@client.command()
async def help(ctx):
	embed=discord.Embed(title="")
	embed.set_author(name="Steam Key Deals Help", icon_url='https://kingairnation.com/wp-content/uploads/2013/07/wrench.png')
	embed.add_field(name = '`$game <game name>`', value = 'This command makes me search Steam and G2A for the best price on a Steam game. Simply click the price when you get your result to buy the game.', inline = False)
	embed.add_field(name = '`$check <@user>`', value = 'This command makes me search Steam and G2A for the best price on a game your friend is playing. Simply click the price when you get your result to buy the game.', inline = False)
	embed.add_field(name = 'Tip 1:', value = 'The more key words included in your search the more accurate I will be!', inline = True)
	embed.add_field(name = 'Tip 2:', value = 'Unreleased games will yield no results!', inline = True)
	embed.add_field(name = 'Tip 3:', value = 'Games that are free on Steam will yield no results!', inline = True)
	embed.add_field(name = 'DISCLAIMER:', value = 'I only search for global keys so there may be a better deal for your location available!', inline = True)
	embed.add_field(name = 'Need me?', value = '[Add me to your server!](https://discord.com/api/oauth2/authorize?client_id=935437726088581140&permissions=139586817088&scope=bot)', inline = False)
	await ctx.send(embed=embed)

#handle commands
@client.command()
async def game(ctx):
	await ctx.send('*Finding your best deal...*', delete_after=1)
	
	query = ctx.message.content.replace('$game', '')

	query = query.strip()

	print(query)

	steamGame = await getSteamGame(query)
	
	if steamGame[0] != 0:
		gameTitle = steamGame[1]
		gameImage = steamGame[4]
		steamGameList = [1, 'Steam', steamGame[2], steamGame[3]]
		g2aGame = await getG2aGame(gameTitle)

		gameList = [steamGameList, g2aGame]

		gameList.sort(key=lambda x: x[2])


		embed=discord.Embed(title="")
		embed.set_author(name=gameTitle, icon_url=gameImage)
		if gameList[0][0] != 0:
			string = '[$' + str(gameList[0][2]) + ' AUD](' + gameList[0][3] + ')'
			embed.add_field(name='1. ' + gameList[0][1], value=string, inline=True)
		if gameList[1][0] != 0:
			string = '[$' + str(gameList[1][2]) + ' AUD](' + gameList[1][3] + ')'
			embed.add_field(name='2. ' + gameList[1][1], value=string, inline=True)
		
		embed.set_footer(text = "For invite and more information type '$help'")
		await ctx.send(embed=embed)

	else:
		embed=discord.Embed(title="")
		embed.set_author(name="It looks like I can't find a deal... :/", icon_url='https://upload.wikimedia.org/wikipedia/commons/thumb/4/46/Question_mark_%28black%29.svg/480px-Question_mark_%28black%29.svg.png')
		embed.set_footer(text = "Try refining your search or type '$help'")
		await ctx.send(embed=embed)

#handle commands
@client.command()
async def check(ctx):
	if not ctx.message.mentions:
		embed=discord.Embed(title="")
		embed.set_author(name="It looks like you didn't mention anyone... :/", icon_url='https://upload.wikimedia.org/wikipedia/commons/thumb/4/46/Question_mark_%28black%29.svg/480px-Question_mark_%28black%29.svg.png')
		embed.set_footer(text = "Try to mention a user or type '$help'")
		await ctx.send(embed=embed)
		return

	if not ctx.message.mentions[0].activities:
		embed=discord.Embed(title="")
		embed.set_author(name="It looks like your friend is not playing anything... :/", icon_url='https://upload.wikimedia.org/wikipedia/commons/thumb/4/46/Question_mark_%28black%29.svg/480px-Question_mark_%28black%29.svg.png')
		embed.set_footer(text = "Try to mention a user that is playing something or type '$help'")
		await ctx.send(embed=embed)
		return

	await ctx.send('*Finding a deal on your friends game...*', delete_after=1)
	
	query = ctx.message.mentions[0].activities[0].name

	print(query)

	steamGame = await getSteamGame(query)
	
	if steamGame[0] != 0:
		gameTitle = steamGame[1]
		gameImage = steamGame[4]
		steamGameList = [1, 'Steam', steamGame[2], steamGame[3]]
		g2aGame = await getG2aGame(gameTitle)

		gameList = [steamGameList, g2aGame]

		gameList.sort(key=lambda x: x[2])


		embed=discord.Embed(title="")
		embed.set_author(name=gameTitle, icon_url=gameImage)
		if gameList[0][0] != 0:
			string = '[$' + str(gameList[0][2]) + ' AUD](' + gameList[0][3] + ')'
			embed.add_field(name='1. ' + gameList[0][1], value=string, inline=True)
		if gameList[1][0] != 0:
			string = '[$' + str(gameList[1][2]) + ' AUD](' + gameList[1][3] + ')'
			embed.add_field(name='2. ' + gameList[1][1], value=string, inline=True)
		
		embed.set_footer(text = "For invite and more information type '$help'")
		await ctx.send(embed=embed)

	else:
		embed=discord.Embed(title="")
		embed.set_author(name="It looks like I can't find a deal... :/", icon_url='https://upload.wikimedia.org/wikipedia/commons/thumb/4/46/Question_mark_%28black%29.svg/480px-Question_mark_%28black%29.svg.png')
		embed.set_footer(text = "Try refining your search or type '$help'")
		await ctx.send(embed=embed)


#run client
client.run('OTM1NDM3NzI2MDg4NTgxMTQw.Ye-oRQ.Pm5Tofj2sbVogBa058WPY5u_pTE')
