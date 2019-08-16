import csv
import os
import math
import mysql.connector

#conn = sqlite3.connect('/Users/sachin_rammoorthy/Downloads/ipl_csv/playerratings.db')
#c = conn.cursor()

mydb = mysql.connector.connect(
  host="localhost",
  user="root",
  passwd="password",
  database="mydatabase"
)

c = mydb.cursor()

c.execute("CREATE TABLE IF NOT EXISTS batsmanRatings (batsmanName VARCHAR(30), eloRating INT, ballsFaced INT)")
c.execute("CREATE TABLE IF NOT EXISTS bowlerRatings (bowlerName VARCHAR(30), eloRating INT, ballsBowled INT)")

#c.execute('''DROP TABLE batsmanRatings''')
#c.execute('''DROP TABLE bowlerRatings''')

#c.execute('''CREATE TABLE IF NOT EXISTS batsmanRatings
#        (batsmanName text, eloRating real, ballsFaced int)''')

#c.execute('''CREATE TABLE IF NOT EXISTS bowlerRatings
#        (bowlerName text, eloRating real, ballsBowled int)''')

c.execute('''DELETE FROM batsmanRatings''')
c.execute('''DELETE FROM bowlerRatings''')

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
'''

#conn.commit()
#conn.close()

c.close()
