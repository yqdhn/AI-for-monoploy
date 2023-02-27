from player import *
import math
import random

settingStartingMoney = 1500

class cell:
    def __init__(self, name, type):
        self.name = name
        self.type = type

    def action(self, player, board):

        if self.type == "Tax":
            if self.name == "Income Tax":
                tax = player.moneyOut(100, board)
                print(f'{player.name} pays {tax} {self.name}')
            elif self.name == "Super Tax":
                tax = player.moneyOut(200, board)
                print(f'{player.name} pays {tax} {self.name}')
        elif self.type == "cc":
            print(f'draw a {self.name}')
            self.community(player, board)
        elif self.type == "chance":
            print(f'draw a {self.name}')
            self.chance(player, board)
        elif self.type == "goJail":
            print(f'{self.name}')
            player.moveTo(10)
            self.inJail = True
        else:
            print(f'You are in {self.name}')

    def community(self, player, board):
        
        # draw a card
        card = board.communityCards.pop(0)

        # auctions
        match(card):
            case 0:
                print("Annuity matures collect 100")
                player.moneyIn(100)
            case 1:
                print("In come tax refund collect 50")
                player.moneyIn(50)
            case 2:
                print("From sale of stock you get 50")
                player.moneyIn(50)
            case 3:
                print("Advance to 'GO'. Collect 200")
                player.moveTo(0)
                player.moneyIn(200)
            case 4:
                print("Bank error in your favor. Collect 200")
                player.moneyIn(200)
            case 5:
                print("Doctor's fees. Pay 50.")
                player.moneyOut(50, board)
            case 6:
                print("Go directly to jail.")
                player.moveTo(10)
                player.inJail = True
            case 7:
                print("Pay hospital 100.")
                player.moneyOut(100, board)
            case 8:
                print("Go back to Old Kent road")
                player.moveTo(1, board)
            case 9:
                print("Receive interest on 7%' preference shares 50")
                player.moneyIn(50)
            case 10:
                print("It is your birthday collect 10 from each player")
                for p in board.players:
                    if p != player:
                        p.moneyOut(10, board)
                        player.moneyIn(10)
            case 11:
                print("pay your insurance premium 50")
                player.moneyOut(50, board)
            case 12:
                print("Get Inherit 100")
                player.moneyIn(100)
            case 13:
                print("you won a prize. Collect 10")
                player.moneyIn(10)
            case _:
                print("something wrong with community")

        board.communityCards.append(card)
    
    def chance(self, player, board):

        # draw a card
        card = board.chanceCards.pop(0)

        # auctions
        match(card):
            case 0:
                print("Take a trip to Marylebone Station. Get 200 if you pass go")
                if player.position > 15:
                    player.moneyIn(200)
                player.moveTo(15, board)
            case 1:
                print("Advance to Pall Mall. Get 200 if you pass go")
                if player.position > 11:
                    player.moneyIn(200)
                player.moveTo(11, board)
            case 2:
                print("Go directly to jail.")
                player.moveTo(10)
                player.inJail = True
            case 3:
                print("Make general repairs on all your property. For each house pay 25. For each hotel pay 100")
                houses = 0
                hotels = 0
                for prop in board.monopoly_board:
                    if prop == "property" and prop.owner == player:
                        if prop.house < 5:
                            houses += prop.house
                        elif prop.house == 5:
                            hotels += 1
                player.moneyOut(25*houses+100*hotels, board)
            case 4:
                print("You are assessed for street repair. 40 per house. 115 per hotel")
                houses = 0
                hotels = 0
                for prop in board.monopoly_board:
                    if prop == "property" and prop.owner == player:
                        if prop.house < 5:
                            houses += prop.house
                        elif prop.house == 5:
                            hotels += 1
                player.moneyOut(40*houses+115*hotels, board)
            case 5:
                print("Speeding fine 50.")
                player.moneyOut(50, board)
            case 6:
                print("Advance to Mayfair")
                player.moveTo(39, board)
            case 7:
                print("Your building loan matures receive 150")
                player.moneyIn(150)
            case 8:
                print("Pay school fees 150")
                player.moneyOut(150, board)
            case 9:
                print("You won a prize. Collect 100")
                player.moneyIn(100)
            case 10:
                print("Go back three spaces")
                player.position = player.position - 3
                player.moveTo(player.position, board)
            case 11:
                print("Advance to 'GO'. Collect 200")
                player.moveTo(0)
                player.moneyIn(200)
            case 12:
                print("Bank pays you dividend 50")
                player.moneyIn(50)
            case 13:
                print("'Drunk in charge'. fine 50")
                player.moneyOut(50, board)
            case 14:
                print("Advance to Trafalgar. Get 200 if you pass go")
                if player.position > 24:
                    player.moneyIn(200)
                player.moveTo(24, board)
            case _:
                print("something wrong with community")

        board.chanceCards.append(card)



class Property:
    def __init__(self, name, type, price, rent_price, house_price, group):
        self.name = name
        self.type = type
        self.price = price
        self.rent_price = rent_price
        self.house_price = house_price
        self.group = group
        self.isFullSet = False
        self.isMortgaged = False
        self.houses = 0
        self.owner = ""
        self.valueToOwner = 0

    def action(self, player, board, rent=None):
        # owned
        if self.owner == player:
            print(player.name + " is the owner of " + self.name)
            return

        # for sale
        elif self.owner == "":
            if player.money >= self.price:
                player.moneyOut(self.price, board)
                self.owner = player
                print(player.name + " buy " + self.name)
            else:
                print(player.name + " can't buy " + self.name)

        # pay rent
        else:
            if self.isMortgaged:
                print(f'{self.name} is mortgaged, no rent for {self.owner.name}')
            else:
                money_taken = player.moneyOut(rent, board)
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

        # Community Chest
        self.communityCards = list(range(0, 14))
        random.shuffle(self.communityCards)
        # Chance
        self.chanceCards = list(range(0, 15))
        random.shuffle(self.chanceCards)


    ## used to check if property sets, utils, or stations owned by the same player
    # it update 'isFullSet' for each
    def isSets(self):
        groups = {}
        for prop in self.monopoly_board:
            if type(prop) == Property:
                if prop.group in groups and prop.owner != groups[prop.group] or prop.owner == "" or prop.isMortgaged:
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
            if type(prop) == Property and prop.type == "station" and station.owner == prop.owner and not prop.isMortgaged:
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
    # store all properties the player can build in player.toBuild list
    def toBuild(self, player):
        # list player can build
        toBuildLits = []

        for prop in self.monopoly_board:
            if type(prop) == Property and prop.type == "property" and prop.isFullSet and prop.owner == player and prop.houses < 5:
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
        self.toBuild(player)
        # first check the number of houses in the first set (in toBuild)
        if player.toBuild == []:
            return False
        
        build = None
        for i, prop in enumerate(player.toBuild):
            if prop.house_price <= maxMoneyToBuild and prop.houses < 5:
                build = player.toBuild[i]
                buildGroup = build.group
                break
        if build == None:
            return False

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
            if prop.house_price <= maxMoneyToBuild and prop.houses < average and prop.group == buildGroup:
                return prop
        return False

    # this function do build in properties
    def build(self, player, maxMoneyToBuild):
        if maxMoneyToBuild < 50:
            return False

        buildMe = self.whatToBuild(player, maxMoneyToBuild)

        if buildMe == False:
            return False
        else:
            buildMe.houses += 1
            player.moneyOut(buildMe.house_price, self)
            print(f'Build {buildMe.name}')
            return True
    
    ## return all properties to the game (if player lost)
    def sellAll(self, player):
        for prop in self.monopoly_board:
            if type(prop) == Property and prop.owner == player:
                prop.owner = ""
                prop.houses = 0
                prop.isMortgaged = False
                prop.isFullSet = False
                self.valueToOwner = 0

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
            theReturn.append(rent / (property.house_price*i + property.price))

        return theReturn
    
    # check ability to build
    # return average number of houses can build according to money have
    def financialStatus(self, player, property):
        numberOfHousesCanBuild = (player.money - player.cashLimit) / property.house_price
        average =  min(numberOfHousesCanBuild / (2 if  property.group in ["dark blue", "brown"] else 3), 5)
        return average


    def propertyValue(self, player, property):
        share = self.propertyShareInGroup(property.group, player) * 10 # just scaling (to be out of 10)
        rent = self.rentReturn(property)
        financial = self.financialStatus(player, property)
        valueOfHouses = rent[property.houses] * 10/1.622  # calculate the value of having houses (and calling to 10) 

    	# check rent return according to the financial status
        idx = int(financial)
        rentFinancial = 0
        if financial < 5:
            rentFinancial = (rent[idx] * (idx + 1 - financial)) + (rent[idx + 1] * (financial - idx))
        else:
            rentFinancial = rent[idx]
        rentFinancial = rentFinancial * 10/1.622 # just scaling (to be out of 10)

        value = round(share + max(rentFinancial, valueOfHouses), 3)
        return value

    def wantedProperties(self, player):
        for prop in self.monopoly_board:
            if prop.type == "property" and prop.owner != player and prop.owner != "" and prop.houses == 0:
                player.wanted[prop] = self.propertyValue(player, prop)


    # The value of all properties the player own (add in the board)
    def valuePlayersProperties(self, player):
        for prop in self.monopoly_board:
            if prop.type == "property" and prop.owner == player:
                prop.valueToOwner = self.propertyValue(player, prop)
            elif prop.type in ["util", "station"]:
                prop.valueToOwner == 1

    ## this make it easier to recall functions after any changes in the board
    def recalculateChanges(self):
        self.isSets()
        for player in self.players:
            self.wantedProperties(player)
            self.valuePlayersProperties(player)

    def action(self, player, position):
        # Landed on a property - calculate rent first
        if type(self.monopoly_board[position]) == Property:
            # calculate the rent one would have to pay (but not pay it yet)
            rent = self.calculateRent(position)
            # pass action to to the cell
            self.monopoly_board[position].action(player, self, rent)
        # other cells
        else:
            self.monopoly_board[position].action(player, self)

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
    a = Player("Alex", "cheapest", 500)
    b = Player("Bop", "cheapest", 500)
    c = Player("Alice", "cheapest", 500)
    d = Player("Said", "cheapest", 500)

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
        


a = Player("Alex", "cheapest", 500)
b = Player("Bop", "cheapest", 500)
c = Player("Alice", "cheapest", 500)
d = Player("Said", "cheapest", 500)

players = [a, b, c, d]
# wins = game(players, 200, 10)
# print(wins)

gameBoard = Board(players)

playing = True
rounds = 0
while playing:
    for player in players:
        player.makeAMove(gameBoard)
        print("")
    if gameOver(players):
        playing = False
        for player in players:
            if player.alive:
                print(f'Number of rounds is {rounds}')
                print(player.name + " is the winner.\n")
    if rounds > 500:
        print("number of rounds exceeded\n")
        playing = False
    rounds += 1

for player in players:
    print(f'{player.name:6} have {player.money}')
    for build in player.toBuild:
        print(build.name)

for x in gameBoard.monopoly_board:
        if x.type == "property":
            if x.owner != "":
                print(f'{x.name:21}: {x.houses} and {x.owner.name:6} is the owner. Value {x.valueToOwner}')
            else:
                print(f'{x.name:21}: {x.houses} and {x.owner:6} is the owner.')


# y = 1
# for x in gameBoard.monopoly_board:
#     if x.type == "property":
#         if y==1:
#             x.owner = a
#             y=0
#         else:
#             x.owner = b
#             y=1

# a.money = 700
# gameBoard.recalculateChanges()
# for x in gameBoard.monopoly_board:
#         if x.type == "property" and x.owner == a:
#             print(f'{x.name:17} {x.valueToOwner}')
# print("\n")
# b.wanted = {k: v for k, v in sorted(b.wanted.items(), key=lambda item: -item[1])}

# for prop in a.wanted:
#     print(f'{prop.name:17}: {a.wanted[prop]}')





# for x in gameBoard.monopoly_board:
#     if type(x) == Property:
#         if x.group == "pink" or x.group == "green" or x.group == "red":
#             x.owner = a

# gameBoard.recalculateChanges()
# # print(gameBoard.calculateRent(1))
# # gameBoard.toBuild(a)
# a.money = 1000000
# print(a.toBuild)
# for x in range(500):
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