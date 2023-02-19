from player import *
import math
import random

settingStartingMoney = 1500


class cell:
    def __init__(self, name, type):
        self.name = name
        self.type = type

    def action(self, player):

        if self.type == "Tax":
            if self.name == "Income Tax":
                tax = player.moneyOut(100)
                print(f'{player.name} pays {tax} Income Tax')
            elif self.name == "Super Tax":
                tax = player.moneyOut(200)
                print(f'{player.name} pays {tax} Super Tax')
        elif self.type == "cc": ## to Do ######################
            print(f'draw a {self.name}')
        elif self.type == "chance": # to Do ###################
            print(f'draw a {self.name}')
        elif self.type == "goJail":
            print(f'{self.name}')
            player.position = 10
            self.inJail = True
        else:
            print(f'You are in {self.name}')

class Property:
    def __init__(self, name, type, price, rent_price, house_price, group):
        self.name = name
        self.type = type
        self.price = price
        self.rent_price = rent_price
        self.house_price = house_price
        self.group = group
        self.isFullSet = False
        self.houses = 0
        self.owner = ""


    def action(self, player, rent=None, board=None):
        # owned
        if self.owner == player:
            print(player.name + " is the owner of " + self.name)
            return

        # for sale
        elif self.owner == "":
            if player.money >= self.price:
                player.moneyOut(self.price)
                self.owner = player
                print(player.name + " buy " + self.name)
            else:
                print(player.name + " can't but" + self.name)

        # pay rent
        else:
            money_taken = player.moneyOut(rent)
            if not player.alive:
                board.sellAll(player)
                self.owner.moneyIn(money_taken)
            print(player.name + " pays " + str(money_taken) + " to " + self.owner.name + " for " + self.name)


class Board:
    def __init__(self, players):
        self.players = players

        self.monopoly_board = [
            cell("Go", "go"),
                     #    name              type         price     rent price             house price   group
            Property("Old Kent Road",       "property",   60,    (2, 10, 30,  90, 160, 250),     50,  "brown"),
            cell("Community Chest", "cc"),
            Property("Whitechapel Road",    "property",   60,    (4, 20, 60, 180, 320, 450),     50,  "brown"),
            cell("Income Tax", "Tax"), # 100
            Property("King’s Cross Station","station",    200,   (0,25,50,100,200),              0,   "station"),
            Property("The Angel Islington", "property",   100,   (6, 30, 90, 270, 400, 550),     50,  "blue"),
            cell("Chance", "chance"), 
            Property("Euston Road",        "property",    100,   (6, 30, 90, 270, 400, 550),     50,  "blue"),
            Property("Pentonville Road",   "property",    120,   (8, 40, 100, 300, 450, 600),    50,  "blue"),
            cell("Jail", "jail"),
            Property("Pall Mall",          "property",    140,   (10, 50, 150, 450, 625, 750),   100, "pink"),
            Property("Electric Company",   "util"    ,    150,   (0,0,0,0,0),                    0,   "util"),
            Property("Whitehall",          "property",    140,   (10, 50, 150, 450, 625, 750),   100, "pink"),
            Property("Northumberland Avenue","property",  140,   (12, 60, 180, 500, 700, 900),   100, "pink"),
            Property("Marylebone Station", "station",     200,   (0,25,50,100,200),              0,   "station"),
            Property("Bow Street",         "property",    180,   (14, 70, 200, 550, 700, 950),   100, "orange"),
            cell("Community Chest", "cc"),
            Property("Marlborough Street", "property",    180,   (14, 70, 200, 550, 700, 950),   100, "orange"),
            Property("Vine Street",        "property",    200,   (16, 80, 220, 600, 800, 1000),  100, "orange"),
            cell("Free Parking",           "parking"),
            Property("The Strand",         "property",    220,   (18, 90, 250, 700, 875, 1050),  150, "red"),
            cell("Chance", "chance"),
            Property("Fleet Street",       "property",    220,   (18, 90, 250, 700, 875, 1050),  150, "red"),
            Property("Trafalgar Square",       "property",240,   (18, 100, 300, 750, 925, 1100), 150, "red"),
            Property("Fenchurch Street Station","station",200,   (0,25,50,100,200),              0,   "station"),
            Property("Leicester Square",   "property",    260,   (22, 110, 330, 800, 975, 1150), 150, "yellow"),
            Property("Coventry Street",    "property",    260,   (22, 110, 330, 800, 975, 1150), 150, "yellow"),
            Property("Water Works",        "util"    ,    150,   (0,0,0,0,0),                    0,   "util"),
            Property("Piccadilly",         "property",    280,   (24,120, 360, 850, 1025, 1200), 150, "yellow"),
            cell("Go to Jail", "goJail"),
            Property("Regent Street",      "property",    300,   (26,130, 390, 900, 1100, 1275), 200, "green"),
            Property("Oxford Street",      "property",    300,   (26,130, 390, 900, 1100, 1275), 200, "green"),
            cell("Community Chest", "cc"),
            Property("Bond Street",      "property",      320,   (28,150, 450, 100, 1200, 1400), 200, "green"),
            Property("Liverpool Street Station","station",200,   (0,25,50,100,200),              0,   "station"),
            cell("Chance", "chance"),
            Property("Park Lane",         "property",     350,   (35, 175, 500, 1100, 1300, 1500), 200,"dark blue"),
            cell("Super Tax", "Tax"), #200
            Property("Mayfair",           "property",     400,   (50,200, 600, 1400, 1700, 2000),  200,"dark blue")
        ]


    ## used to check if property sets, utils, or stations owned by the same player
    # it update 'isFullSet' for each
    def isSets(self):
        groups = {}
        for prop in self.monopoly_board:
            if type(prop) == Property:
                if prop.group in groups and prop.owner != groups[prop.group] or prop.owner == "":
                    groups[prop.group] = False
                else:
                    groups[prop.group] = prop.owner
                
        for prop in self.monopoly_board:
            if type(prop) == Property:
                if prop.group in groups and groups[prop.group] != False:
                    prop.isFullSet = True
                else:
                    prop.isFullSet = False

    ## 
    def calculateStations(self, station):
        stationsCount = 0
        for prop in self.monopoly_board:
            if type(prop) == Property and prop.type == "station" and station.owner == prop.owner:
                stationsCount += 1
        return stationsCount


    def calculateRent(self, position):
        prop = self.monopoly_board[position]
        if type(prop) == Property:
            
            ## normal property rent (count houses if there some)
            if prop.type == "property":
                if prop.houses == 0 and prop.isFullSet:
                    return prop.rent_price[0]*2
                else:
                    return prop.rent_price[prop.houses]

            ## utility rent (if have 1 or 2) 
            elif prop.type == "util":
                if prop.isFullSet:
                    return (random.randint(1, 6)+random.randint(1, 6)) * 10
                else:
                    return (random.randint(1, 6)+random.randint(1, 6)) * 4
            
            ## station rent (consider how many player own)
            elif prop.type == "station":
                return prop.rent_price[self.calculateStations(prop)]

            else:
                return "something wrong with rent"
        else:
            return 0

    ## check if there a full set with a player
    # store all properties the player can build in player.tobuild list
    def toBuild(self, player):
        # list player can build
        toBuildLits = []

        for prop in self.monopoly_board:
            if type(prop) == Property and prop.type == "property" and prop.isFullSet and prop.owner == player:
                toBuildLits.append(prop)
                # print(prop.name + " added")

        # for i in toBuildLits:
        #     print(i.name)

        # three techniques to build houses
        if player.buildTechnique == "random":
            random.shuffle(toBuildLits)
        elif player.buildTechnique == "cheapest":
            toBuildLits.sort(key=lambda x: (x.house_price, x.rent_price[0]))
        elif player.buildTechnique == "expensive":
            toBuildLits.sort(key=lambda x: (-x.house_price, -x.rent_price[0]))
        else:
            return "something wrong with buildTechnique"
        
        player.toBuild = toBuildLits
    
    # this help to find a property to build (already sorted according the build technique)
    # check if the player can build (how much they can pay)
    def whatToBuild(self, player, maxMoneyToBuild):
        # first check the number of houses in the first set (in tobuild)
        if player.toBuild == []:
            return False
        
        for i, prop in enumerate(player.toBuild):
            if prop.house_price <= maxMoneyToBuild and prop.houses < 5:
                break
    
        build = player.toBuild[i]
        buildGroup = build.group
        numberOfHousesInSet = 0
        numberOfProperties = 0
        for prop in player.toBuild:
            if prop.group == buildGroup:
                numberOfHousesInSet += prop.houses
                numberOfProperties += 1
        
        # check max build in the properties in a set
        # that ensure we build all properties evenly (max 1 house difference)
        average = min((math.ceil(numberOfHousesInSet / numberOfProperties + 0.1)), 5) # add 0.1 is a hack to round up always :) # can't build more that 5 
        
        for prop in player.toBuild:
            if prop.house_price <= maxMoneyToBuild and prop.houses < average:
                print(prop.name)
                return prop
        return False

    # this function do build in properties
    def build(self, player, maxMoneyToBuild):
        buildme = self.whatToBuild(player, maxMoneyToBuild)

        if buildme == False:
            return False
        else:
            buildme.houses += 1
            player.moneyOut(buildme.house_price)
    
    ## return all properties to the game (if player lost)
    def sellAll(self, player):
        for prop in self.monopoly_board:
            if type(prop) == Property and prop.owner == player:
                prop.owner = ""
                prop.houses = 0

    ## check how valuable the property of some player
    def propertyShareInGroup(self, group, player):
        propertiesCount = 0
        ownedProperties = 0
        for prop in self.monopoly_board:
            if prop.type == "property" and prop.group == group:
                propertiesCount += 1
                if prop.owner == player:
                    ownedProperties += 1
        
        return ownedProperties / propertiesCount
    
    def rentReturn(self, property):
        theReturn = []
        for i, rent in enumerate(property.rent_price):
            theReturn.append(round(rent / (property.house_price*i + property.price), 3))

        return theReturn
    
    # check ability to build
    # return average number of houses can build according to money have
    def financialStatus(self, player, property):
        numberOfHousesCanBuild = (player.money - player.cashLimit) / property.house_price
        average =  min(numberOfHousesCanBuild / (2 if  property.group in ["dark blue", "brown"] else 3), 5)
        return average


    def propertyValue(self, player, property):
        share = round(self.propertyShareInGroup(property.group, player), 3) * 10 # just scaling (to be out of 10)
        rent = self.rentReturn(property)
        financial = round(self.financialStatus(player, property),3)

        idx = int(financial)
        rentFinancial = 0
        if financial < 5:
            rentFinancial = (rent[idx] * (idx + 1 - financial)) + (rent[idx + 1] * (financial - idx))
        else:
            rentFinancial = rent[idx]
        
        rentFinancial = round(rentFinancial * 10/1.622, 3) # just scaling (to be out of 10)
        return share + rentFinancial

    def wantedProperties(self, player):
        for prop in self.monopoly_board:
            if prop.type == "property" and prop.owner != player:
                player.wanted[prop] = self.propertyValue(player, prop)


    ## this make it easier to recall functions after any changes in the board
    def recalculateChanges(self):
        self.isSets()
        for player in self.players:
            self.toBuild(player)
            self.wantedProperties(player)

    def action(self, player, position):
        # Landed on a property - calculate rent first
        if type(self.monopoly_board[position]) == Property:
            # calculate the rent one would have to pay (but not pay it yet)
            rent = self.calculateRent(position)
            # pass action to to the cell
            self.monopoly_board[position].action(player, rent, self)
        # other cells
        else:
            self.monopoly_board[position].action(player)

## check if there is a winner (one player alive)
def gameOver(players):
    playersAlive = 0
    for player in players:
        if player.alive:
            playersAlive += 1
        
    if playersAlive > 1:
        return False
    else:
        return True


def play(players, max_rounds):
    a = Player("Alex", settingStartingMoney, "cheapest", 500)
    b = Player("Bop", settingStartingMoney, "cheapest", 500)
    c = Player("Alice", settingStartingMoney, "cheapest", 500)
    d = Player("Said", settingStartingMoney, "cheapest", 500)

    players = [a, b, c, d]
    
    random.shuffle(players)

    gameBoard = Board(players)

    stop = True
    rounds = 0
    while stop and rounds <= max_rounds:
        for player in players:
            player.makeAMove(gameBoard)
            print("")
        if gameOver(players):
            stop = False
            for player in players:
                if player.alive:
                    print(f'Number of rounds is {rounds}')
                    print(player.name + " is the winner.\n")
                    return player.name
        rounds += 1
    return False

def game(players, max_rounds, game_num):
    ## there an issue with initializing players outside the function
    wins = {}
    game_played = 0
    while game_played < game_num:
        winner = play(players, max_rounds)
        if winner == False:
            pass #continue
        else:
            if winner not in wins:
                wins[winner] = 0
            wins[winner] = wins.get(winner) + 1

        game_played += 1
    
    return wins
        


a = Player("Alex", settingStartingMoney, "cheapest", 500)
b = Player("Bop", settingStartingMoney, "cheapest", 500)
c = Player("Alice", settingStartingMoney, "cheapest", 500)
d = Player("Said", settingStartingMoney, "cheapest", 500)

players = [a, b, c, d]
# wins = game(players, 200, 10)
# print(wins)

gameBoard = Board(players)


stop = True
rounds = 0
while stop:
    for player in players:
        player.makeAMove(gameBoard)
        print("")
    if gameOver(players):
        stop = False
        for player in players:
            if player.alive:
                print(f'Number of rounds is {rounds}')
                print(player.name + " is the winner.\n")
    if rounds > 500:
        print("number of rounds exceeded\n")
        stop = False
    rounds += 1

for player in players:
    print(f'{player.name:6} have {player.money}')

for x in gameBoard.monopoly_board:
        if x.type == "property":
            if x.owner != "":
                print(f'{x.name:21}: {x.houses} and {x.owner.name:6} is the owner')
            else:
                print(f'{x.name:21}: {x.houses} and {x.owner:6} is the owner')




# gameBoard.recalculateChanges()

# for x in gameBoard.monopoly_board:
#     if x.type == "property":
#         if x.group in ["brown", "green", "red"]:
#             x.owner = a

# a.money = 500
# for x in gameBoard.monopoly_board:
#         if x.type == "property" and x.owner == a:
#             print(f'{x.name:17} {gameBoard.propertyValue(a,x)}')
# print("\n")
# b.wanted = {k: v for k, v in sorted(b.wanted.items(), key=lambda item: -item[1])}

# for prop in b.wanted:
#     prop.owner = a
#     print(f'{prop.name:17}: {b.wanted[prop]}')





# for x in gameBoard.monopoly_board:
#     if type(x) == Property:
#         if x.group == "pink" or x.group == "green" or x.group == "red":
#             x.owner = a.name

# gameBoard.recalculateChanges()
# print(gameBoard.calculateRent(1))
# gameBoard.toBuild(a)
# print(a.tobuild)
# for x in range(25):
#     gameBoard.build(a, a.money)

# for x in gameBoard.monopoly_board:
#     if type(x) == Property:
#         if x.group == "pink" or x.group == "green" or x.group == "red":
#             print(x.name + ": " + str(x.houses))




# for i in gameBoard.monopoly_board:
#     if type(i) == Property:
#         print(i.isFullSet)

# for x in gameBoard.monopoly_board[:30]:
#     if type(x) == Property:
#         if x.type == "station":
#             x.owner = a

# print(gameBoard.calculateRent(5))


# next add function to trade and to downgrade