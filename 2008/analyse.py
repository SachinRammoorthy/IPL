import csv
import os
import math
import mysql.connector
import sqlite3
import ast


conn = sqlite3.connect('/Users/sachin_rammoorthy/Downloads/ipl_csv/playerratings.db')
c = conn.cursor()
'''
mydb = mysql.connector.connect(
  host="localhost",
  user="root",
  passwd="password",
  database="elo"
)

c = mydb.cursor()
c.execute("INSERT INTO batsmanRatings VALUES ('AB de Villiers',2400,2000)")
'''
c.execute("CREATE TABLE IF NOT EXISTS playerRatings (ratings LONGTEXT)")
#c.execute("CREATE TABLE IF NOT EXISTS bowlerRatings (bowlerName LONGTEXT, eloRating INT, ballsBowled INT)")

#c.execute('''DROP TABLE batsmanRatings''')
#c.execute('''DROP TABLE bowlerRatings''')

#c.execute('''CREATE TABLE IF NOT EXISTS batsmanRatings
#        (batsmanName text, eloRating real, ballsFaced int)''')

#c.execute('''CREATE TABLE IF NOT EXISTS bowlerRatings
#        (bowlerName text, eloRating real, ballsBowled int)''')

c.execute('''DELETE FROM playerRatings''')
#c.execute('''DELETE FROM bowlerRatings''')

playerRatingsBatsmen = []
playerRatingsBowlers = []

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

#LOOP THROUGH ALL FILES
for filename in os.listdir("/Users/sachin_rammoorthy/Downloads/ipl_csv/2008"):
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


'''
print("Bowler Ratings:")

c.execute('SELECT * FROM bowlerRatings ORDER BY eloRating')
for row in c:
    bowler, oldBowlerRating, ballsBowled = row
    if ballsBowled > 180:
        print row

print("\n\nBatsman Ratings:")

c.execute('SELECT * FROM batsmanRatings ORDER BY eloRating')
for row in c:
    batsman, oldBatsmanRating, ballsFaced = row
    if ballsFaced > 100:
        print row

c.execute("SELECT batsmanName, eloRating, ballsFaced FROM batsmanRatings")
for row in c:
    print(row)
    break
else:
    print("We good")
'''
'''
print("Batsmen Ratings: \n\n")
playerRatingsBatsmen.sort(key = lambda x: x[1], reverse = True)
print("\n\nBowlers Ratings: \n\n")
playerRatingsBowlers.sort(key = lambda x: x[1], reverse = True)
'''

c.execute("INSERT INTO playerRatings VALUES (?)", ((str(playerRatingsBatsmen) + "," + str(playerRatingsBowlers)), ))

print((str(playerRatingsBatsmen) + "," + str(playerRatingsBowlers)))
print(ast.literal_eval((str(playerRatingsBatsmen) + "," + str(playerRatingsBowlers))))

conn.commit()
conn.close()
#mydb.close()

'''
c.execute("SELECT batsmanName, eloRating, ballsFaced FROM batsmanRatings WHERE batsmanName= %s", (batsman, ))
for row in c:
    batsman, oldBatsmanRating, ballsFaced = row
    break
else:
    c.execute("INSERT INTO batsmanRatings VALUES ('" + batsman + "',1500,0)")
    oldBatsmanRating = 1500
    ballsFaced = 0;

c.execute("SELECT bowlerName, eloRating, ballsBowled FROM bowlerRatings WHERE bowlerName= %s", (bowler, ))
for row in c:
    bowler, oldBowlerRating, ballsBowled = row
    break
else:
    c.execute("INSERT INTO bowlerRatings VALUES ('" + bowler + "',1500,0)")
    oldBowlerRating = 1500
    ballsBowled = 0
'''
