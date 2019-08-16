import csv
import os
import math
import mysql.connector
import requests
import json

mydb = mysql.connector.connect(
  host="localhost",
  user="root",
  passwd="password",
  database="mydatabase"
)

c = mydb.cursor()

#conn = sqlite3.connect('/Users/sachin_rammoorthy/Downloads/ipl_csv/playerratings.db')
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
    print(link)
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

    c.execute("SELECT batsmanName, eloRating, ballsFaced FROM batsmanRatings WHERE batsmanName=%s", (batsman, ))
    for row in c:
        batsman, oldBatsmanRating, ballsFaced = row
        break
    else:
        c.execute("INSERT INTO batsmanRatings VALUES ('" + batsman + "',1500,0)")
        oldBatsmanRating = 1500
        ballsFaced = 0;

    c.execute("SELECT bowlerName, eloRating, ballsBowled FROM bowlerRatings WHERE bowlerName=%s", (bowler, ))
    for row in c:
        bowler, oldBowlerRating, ballsBowled = row
        break
    else:
        c.execute("INSERT INTO bowlerRatings VALUES ('" + bowler + "',1500,0)")
        oldBowlerRating = 1500
        ballsBowled = 0

    pbatsman = calculateProbability(oldBowlerRating, oldBatsmanRating)
    pbowler = calculateProbability(oldBatsmanRating, oldBowlerRating)

    if event == "out":
        result = 0
    elif event == "0":
        result = 0.2
    elif event == "1":
        result = 0.45
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

    batsmanRating = oldBatsmanRating + 6 * (result - pbatsman)
    bowlerRating = oldBowlerRating + 6 * ((1 - result) - pbowler)

    #print("Old ratings > " + batsman + ": " + str(oldBatsmanRating) + ", " + bowler + ": " + str(oldBowlerRating) +
    #        "\nNew ratings > " + batsman + ": " + str(batsmanRating) + ", " + bowler + ": " + str(bowlerRating) + "\n\n")

    c.execute("""UPDATE batsmanRatings SET eloRating = %s, ballsFaced = %s WHERE batsmanName= %s """, (batsmanRating, ballsFaced + 1, batsman))
    c.execute("""UPDATE bowlerRatings SET eloRating = %s, ballsBowled = %s WHERE bowlerName= %s """, (bowlerRating, ballsBowled + 1, bowler))

#Bowler has to have bowled 300 balls
#Batting rating is aggregate of top 6 batsmen
def calculateTeamRating(teamPlayers):
    batsmenRatings = []
    bowlersRatings = []

    for player in teamPlayers:
        c.execute("SELECT batsmanName, eloRating, ballsFaced FROM batsmanRatings WHERE batsmanName=%s", (player, ))
        for row in c:
            player, battingRating, ballsFaced = row
            break
        else:
            c.execute("INSERT INTO batsmanRatings VALUES ('" + player + "',1500,0)")
            battingRating = 1500
            ballsFaced = 0;

        c.execute("SELECT bowlerName, eloRating, ballsBowled FROM bowlerRatings WHERE bowlerName=%s", (player, ))
        for row in c:
            bowler, bowlerRating, ballsBowled = row
            break
        else:
            c.execute("INSERT INTO bowlerRatings VALUES ('" + player + "',1500,0)")
            bowlerRating = 1500
            ballsBowled = 0
        batsmenRatings.append(battingRating)
        bowlersRatings.append(bowlerRating)

    batsmenRatings.sort(reverse = True)
    bowlersRatings.sort(reverse = True)
    teamRating = ((sum(bowlersRatings[:6]) /6) + (sum(batsmenRatings[:6]) /6))/2
    return teamRating

def predictOutcome(matchNumber, year, actual):
    if len(matchNumber)<2:
        matchNumber = "0" + matchNumber
    teamOneRating = calculateTeamRating(getTeamPlayers(matchNumber, year, 0))
    teamTwoRating = calculateTeamRating(getTeamPlayers(matchNumber, year, 1))
    #print(str(teamOneRating))
    #print(str(teamTwoRating))
    #print(str(calculateProbability(teamTwoRating, teamOneRating)))
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


print("2011 predictions based on previous years (and 2011 previous games):\n\n")
#for each file, get match number and year and input
for filename in os.listdir("/Users/sachin_rammoorthy/Downloads/ipl_csv/2011"):
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
    elif "Decc" in actual: actual = "DC"
    elif "Del" in actual: actual = "DD"
    else: actual = "Nat vurking"

    if matchNumber != "Nope":
        predictOutcome(matchNumber, season, actual)
    if "." not in filename:
        updateElo(filename + '.csv')


c.close()
