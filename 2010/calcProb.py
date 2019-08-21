import csv
import os
import math
import requests
import json
import sqlite3
import ast



conn = sqlite3.connect('/Users/sachin_rammoorthy/Downloads/ipl_csv/playerratings.db')
c = conn.cursor()

playerRatingsBatsmen = []
playerRatingsBowlers = []

c.execute('SELECT ratings FROM playerRatings')
for row in c:
    someArray = ast.literal_eval(str(row)[3:-3])
    playerRatingsBatsmen.append(someArray[0])
    playerRatingsBowlers.append(someArray[1])

#c = conn.cursor()




def getTeam(matchNumber, year, i):
    if len(matchNumber)<2:
        matchNumber = "0" + matchNumber
    link = "http://datacdn.iplt20.com/dynamic/data/core/cricket/2012/ipl" + year + '/ipl' + year + '-' + matchNumber + "/scoring.js"
    f = requests.get(link)
    f = f.text[10:-2]
    fjson = json.loads(f)
    return fjson["matchInfo"]["teams"][i]["team"]["abbreviation"]

def getTeamPlayers(matchNumber, year, j):
    if len(matchNumber)<2:
        matchNumber = "0" + matchNumber
    link = "http://datacdn.iplt20.com/dynamic/data/core/cricket/2012/ipl" + year + '/ipl' + year + '-' + matchNumber + "/scoring.js"
    f = requests.get(link)
    f = f.text[10:-2]

    fjson = json.loads(f)
    i=0;
    teamPlayers = []
    while i<11:
        player = fjson["matchInfo"]["teams"][j]["players"][i]["shortName"]
        if (player == "RG Sharma") or (player == "AB de Villiers") or (player == "C de Grandhomme") or (player == "Q de Kock"):
            player = player
        else:
            playerArr = player.split()
            if len(playerArr)>2:
                del playerArr[1]
            if len(playerArr[0])>1:
                playerArr[0] = playerArr[0][0:1]
            if len(playerArr)>1:
                player = playerArr[0] + " " + playerArr[1]
        teamPlayers.append(player)
        i+=1
    return teamPlayers

def calculateProbability(rating1, rating2):
    return 1.0 * 1.0 / (1 + 1.0 * math.pow(10, 1.0 * (rating1 - rating2) / 400))

def calculateElo(batsman, bowler, event):
    global playerRatingsBatsmen, playerRatingsBowlers
    if (batsman == "RG Sharma") or (batsman == "AB de Villiers") or (batsman == "C de Grandhomme") or (batsman == "Q de Kock"):
        batsman = batsman
    else:
        batsmanArr = batsman.split()
        if len(batsmanArr)>2:
            del batsmanArr[1]
        if len(batsmanArr[0])>1:
            batsmanArr[0] = batsmanArr[0][0:1]
        if len(batsmanArr)>1:
            batsman = batsmanArr[0] + " " + batsmanArr[1]

    bowlerArr = bowler.split()
    if len(bowlerArr)>2:
        del bowlerArr[1]
    if len(bowlerArr[0])>1:
        bowlerArr[0] = bowlerArr[0][0:1]
    if len(bowlerArr)>1:
        bowler = bowlerArr[0] + " " + bowlerArr[1]

    oldBatsmanRating = 1500
    ballsFaced = 0
    existsBatsman = False

    cBatsman = 0
    cBowler = 0
    batsmanIndex = 0
    bowlerIndex = 0

    for i in playerRatingsBatsmen:
        if batsman in i:
            row = i
            batsmanIndex = cBatsman
            oldBatsmanRating = float(row[1])
            ballsFaced = int(row[2])
            existsBatsman = True
        cBatsman = cBatsman + 1


    if existsBatsman == False:
        playerRatingsBatsmen.append([batsman, str(oldBatsmanRating), str(ballsFaced)])

    oldBowlerRating = 1500
    ballsBowled = 0
    existsBowler = False

    for i in playerRatingsBowlers:
        if bowler in i:
            row = i
            bowlerIndex = cBowler
            oldBowlerRating = float(row[1])
            ballsBowled = int(row[2])
            existsBowler = True
        cBowler = cBowler + 1

    if existsBowler == False:
        playerRatingsBowlers.append([bowler, str(oldBowlerRating), str(ballsBowled)])

    pbatsman = calculateProbability((oldBowlerRating), (oldBatsmanRating))
    pbowler = calculateProbability((oldBatsmanRating), (oldBowlerRating))

    if event == "out":
        result = 0
    elif event == "0":
        result = 0.25
    elif event == "1":
        result = 0.47
    elif event == "2":
        result = 0.67
    elif event == "3":
        result = 0.79
    elif event == "4":
        result = 0.9
    elif event == "6":
        result = 1
    else:
        result = 0.5

    batsmanRating = (oldBatsmanRating) + 10 * (result - pbatsman)
    bowlerRating = (oldBowlerRating) + 10 * ((1 - result) - pbowler)

    #print("Old ratings > " + batsman + ": " + str(oldBatsmanRating) + ", " + bowler + ": " + str(oldBowlerRating) +
    #        "\nNew ratings > " + batsman + ": " + str(batsmanRating) + ", " + bowler + ": " + str(bowlerRating) + "\n\n")

    #c.execute("""UPDATE batsmanRatings SET eloRating = %s, ballsFaced = %s WHERE batsmanName= %s """, (batsmanRating, ballsFaced + 1, batsman))
    #c.execute("""UPDATE bowlerRatings SET eloRating = %s, ballsBowled = %s WHERE bowlerName= %s """, (bowlerRating, ballsBowled + 1, bowler))
    #[w.replace(batsman + "," + str(oldBatsmanRating) + "," + str(ballsFaced), batsman + "," + str(batsmanRating) + "," + str(ballsFaced)) for w in playerRatingsBatsmen]
    ballsFaced = ballsFaced + 1
    ballsBowled = ballsBowled + 1
    
    
    for i in playerRatingsBatsmen:
        if batsman in i:
            playerRatingsBatsmen.remove(i)

    for i in playerRatingsBowlers:
        if bowler in i:
            playerRatingsBowlers.remove(i)

    playerRatingsBatsmen.append([batsman, str(batsmanRating), str(ballsFaced)])
    playerRatingsBowlers.append([bowler, str(bowlerRating), str(ballsBowled)])
#Bowler has to have bowled 300 balls
#Batting rating is aggregate of top 6 batsmen
def calculateTeamRating(teamPlayers):
    batsmenRatings = []
    bowlersRatings = []

    for player in teamPlayers:

        oldBatsmanRating = 1500
        ballsFaced = 0
        existsBatsman = False

        for i in playerRatingsBatsmen:
            if player in i:
                row = i
                oldBatsmanRating = float(row[1])
                batsmenRatings.append(oldBatsmanRating)
                existsBatsman = True

        if existsBatsman == False:
            playerRatingsBatsmen.append([player, str(oldBatsmanRating), str(ballsFaced)])

        oldBowlerRating = 1500
        ballsBowled = 0
        existsBowler = False

        for i in playerRatingsBowlers:
            if player in i:
                row = i
                oldBowlerRating = float(row[1])
                bowlersRatings.append(oldBowlerRating)
                existsBowler = True

        if existsBowler == False:
            playerRatingsBowlers.append([player, str(oldBowlerRating), str(ballsBowled)])

    for i in range(0, len(batsmenRatings)):
        batsmenRatings[i] = int(batsmenRatings[i])
    for i in range(0, len(bowlersRatings)):
        bowlersRatings[i] = int(bowlersRatings[i])
    batsmenRatings.sort(reverse = True)
    bowlersRatings.sort(reverse = True)
    teamRating = (float(sum(bowlersRatings[:3]))*0.25 + float(sum(bowlersRatings[3:5]))*0.125 + float(sum(batsmenRatings[:3]))*0.25 + float(sum(batsmenRatings[3:5]))*0.125 )/2
    return teamRating

def predictOutcome(matchNumber, year, actual):
    if len(matchNumber)<2:
        matchNumber = "0" + matchNumber
    teamOneRating = calculateTeamRating(getTeamPlayers(matchNumber, year, 0))
    teamTwoRating = calculateTeamRating(getTeamPlayers(matchNumber, year, 1))
    predictedTeam = "";
    predictionProb = 0;
    if calculateProbability(teamTwoRating, teamOneRating) > 0.5:
        predictedTeam = getTeam(matchNumber, year, 0)
        predictionProb = calculateProbability(teamTwoRating, teamOneRating)
    else:
        predictedTeam = getTeam(matchNumber, year, 1)
        predictionProb = calculateProbability(teamOneRating, teamTwoRating)
    result = "0"
    if actual == predictedTeam: result = "1"
    print(actual + "," + predictedTeam + "," + str(predictionProb) + "," + result + ",  RATINGS: " + str(teamOneRating) + " " + str(teamTwoRating))


def updateElo(filename):
    if filename.endswith(".csv") and "_1" not in filename:
        filename = filename[:-4]
        filename_output = filename + "_1"
        with open(filename + '.csv', 'rb') as csvfile, open(filename_output + '.csv', 'wb') as result:
            csvreader = csv.reader(csvfile)
            csvwriter = csv.writer(result)

            for row in csvreader:
                if "ball" in row[0]:
                    if "caught" in row or "bowled" in row or "lbw" in row or "stumped" in row:
                        csvwriter.writerow( (row[4], row[6], "out") )
                    else:
                        csvwriter.writerow( (row[4], row[6], row[7]) )
        with open(filename_output + '.csv', 'rb') as newInput:
            csvreaderNew = csv.reader(newInput)
            for row in csvreaderNew:
                calculateElo(row[0], row[1], str(row[2]))

        os.remove(filename_output + '.csv')


print("\n\n2010:\n\n")
#for each file, get match number and year and input
for filename in os.listdir("/Users/sachin_rammoorthy/Downloads/ipl_csv/2010"):
    matchNumber = "Nope"
    season = ""
    actual = ""
    if filename.endswith(".csv") and "_1" not in filename:
        filename = filename[:-4]
        with open(filename + '.csv', 'rb') as csvfile:
            csvreader = csv.reader(csvfile)
            for row in csvreader:
                if "match_number" in row[1]:
                    matchNumber = row[2]
                    if len(matchNumber)<2:
                        matchNumber = "0" + matchNumber
                if "season" in row[1]:
                    season = row[2]
                if "winner" in row[1] and "winner_wickets" not in row[1] and "winner_runs" not in row[1]:
                    actual = row[2]
    if "Raja" in actual: actual = "RR"
    elif "Chen" in actual: actual = "CSK"
    elif "Chal" in actual: actual = "RCB"
    elif "Kolk" in actual: actual = "KKR"
    elif "King" in actual: actual = "KXIP"
    elif "Mumb" in actual: actual = "MI"
    elif "Decc" in actual: actual = "SRH"
    elif "Dared" in actual: actual = "DD"
    elif "Capit" in actual: actual = "DC"
    elif "Keral" in actual: actual = "KTK"
    elif "Warri" in actual: actual = "PWI"
    elif "Sunri" in actual: actual = "SRH"
    elif "Superg" in actual: actual = "RPS"
    elif "Gujara" in actual: actual = "GL"
    else: actual = "Nat vurking"

    if matchNumber != "Nope":
        predictOutcome(matchNumber, season, actual)
    if "." not in filename:
        updateElo(filename + '.csv')


c.execute("UPDATE playerRatings SET ratings=?", ((str(playerRatingsBatsmen) + "," + str(playerRatingsBowlers)), ))

conn.commit()
conn.close()
