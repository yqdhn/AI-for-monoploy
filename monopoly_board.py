import random
import copy

global stut

class Player:
    def __init__(self, name, strategy):
        self.name = name
        self.position = 0
        self.money = 1500
        self.strategy = strategy
        self.inJail = False
        self.roundsInJail = 0
        self.dicesDoubleCount = 0
        self.alive = True

    def update_player(self, newSelf):
        self.name = newSelf.name
        self.position = newSelf.position
        self.money = newSelf.money  # start 1500
        self.inJail = newSelf.inJail
        self.roundsInJail = newSelf.roundsInJail
        self.dicesDoubleCount = newSelf.dicesDoubleCount
        self.alive = newSelf.alive
        
    # money management
    # get paid
    def moneyIn(self, amount):
        game_output(str(amount) + " added to " + self.name)
        self.money += amount
        game_output(self.name + " money become " + str(self.money))

    # pay someone or buy
    def moneyOut(self, amount, state):
        game_output(self.name + " money was " + str(self.money))
        money_taken = 0
        self.bankruptPlayer(amount, state)
        if self.money >= amount:
            self.money -= amount
            money_taken = amount
        else:
            money_taken = self.money
            self.money -= money_taken
        
        game_output("become " + str(self.money) + " paid " + str(money_taken))
        return money_taken

    # positions
    def moveTo(self, position, state):
        self.position = position
        state.board.action(state, self)

    def makeAMove(self, state):
        # player must be alive to play
        if not self.alive:
            return False

        state.board.recalculateChanges()

        ## check if there is a property to un mortgage
        while self.unMortgage(state):
            state.board.recalculateChanges()

        # check if the player can have a property to build and can build it
        while state.board.build(self, state):
            pass

        playAgain = False
        dice1 = random.randint(1, 6)
        dice2 = random.randint(1, 6)

        if not self.inJail and dice1 == dice2:
            playAgain = True
            self.dicesDoubleCount += 1
            # go to jail if 3 dices doubles
            if self.dicesDoubleCount == 3:
                self.inJail = True
                playAgain = False
                self.moveTo(10, state)
                self.dicesDoubleCount = 0
                game_output(f'{self.name} went to jail after 3 doubles')
                return False
        else:
            self.dicesDoubleCount = 0

        if self.inJail:
            if dice1 != dice2:
                self.roundsInJail += 1
                if self.roundsInJail > 3:
                    game_output(f'{self.name} get out of jail after 3 rounds')
                elif self.money >= 50:
                    jailFine = self.moneyOut(50, state)
                    game_output(f'{self.name} pays {jailFine} to get out of jail')
                    self.roundsInJail = 0
                else:
                    return False
            else:
                playAgain = False
        # player got out of the jail
        self.roundsInJail = 0
        self.inJail = False

        if not self.alive:
            return False

        # move the piece
        game_output(f'{self.name} position is {self.position} and dices total is {dice1+dice2}')
        self.position += dice1+dice2
        # calculate correct cell (if more that 40)
        # and get salary for passing GO (200)
        if self.position >= len(state.board.monopoly_board):
            self.position = self.position - len(state.board.monopoly_board)
            self.moneyIn(200)

        game_output(f'{self.name} new position is {state.board.monopoly_board[self.position].name}({self.position})')
        state.board.action(state, self)

        if playAgain:
            game_output(f'{self.name} plays again {dice1}={dice2}')
            self.makeAMove(state)
    
    # take an action if player doesn't have money
    def bankruptPlayer(self, amount, state):
        playerProperties = [prop for prop in state.board.monopoly_board
                            if prop.type in ["property", "util", "station"]
                            and prop.owner == self]
        while self.money - amount < 0:
            # find all possible state of Mortgage
            possibleStatesOfMortgage = [
                self.stateOfMortgage(state, prop) for prop in playerProperties
                if not prop.isMortgaged]

            #there is no property to mortgage
            if len(possibleStatesOfMortgage) == 0:
                self.alive = False
                state.board.sellAll(self) # return all properties to bank
                game_output(f'{self.name} is out (no money) ############')
                return

            ## chose the best state
            resultsOfMortgage = [
                self.strategy.heuristic(stateOfMortgage.players[state.players.index(self)], stateOfMortgage)
                for stateOfMortgage in possibleStatesOfMortgage]

            maxValueState = possibleStatesOfMortgage[resultsOfMortgage.index(max(resultsOfMortgage))]

            ## update everything to the best state for player
            state.update_state(maxValueState)
            state.board.recalculateChanges()
 
    def stateOfMortgage(self, state, space):
        newState = state.newState()
        prop = newState.board.monopoly_board[state.board.monopoly_board.index(space)]
        ## sell houses
        if prop.houses > 0:
            newState.players[state.players.index(self)].moneyIn(int(prop.price/2))
            prop.houses -= 1
        else:
            prop.isMortgaged = True
            newState.players[state.players.index(self)].moneyIn(int(prop.price/2))

        return newState

    def unMortgage(self, state):
        # find all possible state of UnMortgage
        possibleStatesOfUnMortgage = [
            self.stateOfUnMortgage(state, prop) for prop in state.board.monopoly_board
            if prop.type in ["property", "util", "station"]
            and prop.owner == self
            and prop.isMortgaged
            and prop.price/2 <= self.money]
        
        if len(possibleStatesOfUnMortgage) == 0:
            return False
        
        resultsOfUnMortgage = [
            self.strategy.heuristic(stateOfUnMortgage.players[state.players.index(self)], stateOfUnMortgage)
            for stateOfUnMortgage in possibleStatesOfUnMortgage]
        
        maxValueState = possibleStatesOfUnMortgage[resultsOfUnMortgage.index(max(resultsOfUnMortgage))]
        
        state.update_state(maxValueState)

        return True

    def stateOfUnMortgage(self, state, space):
        newState = state.newState()
        prop = newState.board.monopoly_board[state.board.monopoly_board.index(space)]
        prop.isMortgaged = False
        newState.players[state.players.index(self)].moneyOut(int(prop.price/2), newState)
        return newState

    # def tradeProperty(self, board):

class cell:
    def __init__(self, name, type):
        self.name = name
        self.type = type

    def action(self, player, state):

        if self.type == "Tax":
            if self.name == "Income Tax":
                tax = player.moneyOut(100, state)
                game_output(f'{player.name} pays {tax} {self.name}')
            elif self.name == "Super Tax":
                tax = player.moneyOut(200, state)
                game_output(f'{player.name} pays {tax} {self.name}')
        elif self.type == "cc":
            game_output(f'draw a {self.name}')
            self.community(player, state)
        elif self.type == "chance":
            game_output(f'draw a {self.name}')
            self.chance(player, state)
        elif self.type == "goJail":
            game_output(f'{self.name}')
            player.moveTo(10, state)
            player.inJail = True
        else:
            game_output(f'You are in {self.name}')

    def community(self, player, state):
        
        # draw a card
        card = state.board.communityCards.pop(0)

        # auctions
        if card == 0:
            game_output("Annuity matures collect 100")
            player.moneyIn(100)
        elif card == 1:
            game_output("In come tax refund collect 50")
            player.moneyIn(50)
        elif card == 2:
            game_output("From sale of stock you get 50")
            player.moneyIn(50)
        elif card == 3:
            game_output("Advance to 'GO'. Collect 200")
            player.moveTo(0, state)
            player.moneyIn(200)
        elif card == 4:
            game_output("Bank error in your favor. Collect 200")
            player.moneyIn(200)
        elif card == 5:
            game_output("Doctor's fees. Pay 50.")
            player.moneyOut(50, state)
        elif card == 6:
            game_output("Go directly to jail.")
            player.moveTo(10, state)
            player.inJail = True
        elif card == 7:
            game_output("Pay hospital 100.")
            player.moneyOut(100, state)
        elif card == 8:
            game_output("Go back to Old Kent road")
            player.moveTo(1, state)
        elif card == 9:
            game_output("Receive interest on 7%' preference shares 50")
            player.moneyIn(50)
        elif card == 10:
            game_output("It is your birthday collect 10 from each player")
            for p in state.players:
                if p != player:
                    p.moneyOut(10, state)
                    player.moneyIn(10)
        elif card == 11:
            game_output("pay your insurance premium 50")
            player.moneyOut(50, state)
        elif card == 12:
            game_output("Get Inherit 100")
            player.moneyIn(100)
        elif card == 13:
            game_output("you won a prize. Collect 10")
            player.moneyIn(10)
        else:
            game_output("something wrong with community")

        state.board.communityCards.append(card)
    
    def chance(self, player, state):

        # draw a card
        card = state.board.chanceCards.pop(0)

        # auctions
        if card == 0:
            game_output("Take a trip to Marylebone Station. Get 200 if you pass go")
            if player.position > 15:
                player.moneyIn(200)
            player.moveTo(15, state)
        elif card == 1:
            game_output("Advance to Pall Mall. Get 200 if you pass go")
            if player.position > 11:
                player.moneyIn(200)
            player.moveTo(11, state)
        elif card == card == 2:
            game_output("Go directly to jail.")
            player.moveTo(10, state)
            player.inJail = True
        elif card == 3:
            game_output("Make general repairs on all your property. For each house pay 25. For each hotel pay 100")
            houses = 0
            hotels = 0
            for prop in state.board.monopoly_board:
                if prop == "property" and prop.owner == player:
                    if prop.house < 5:
                        houses += prop.house
                    elif prop.house == 5:
                        hotels += 1
            player.moneyOut(25*houses+100*hotels, state)
        elif card == 4:
            game_output("You are assessed for street repair. 40 per house. 115 per hotel")
            houses = 0
            hotels = 0
            for prop in state.board.monopoly_board:
                if prop == "property" and prop.owner == player:
                    if prop.house < 5:
                        houses += prop.house
                    elif prop.house == 5:
                        hotels += 1
            player.moneyOut(40*houses+115*hotels, state)
        elif card == 5:
            game_output("Speeding fine 50.")
            player.moneyOut(50, state)
        elif card == 6:
            game_output("Advance to Mayfair")
            player.moveTo(39, state)
        elif card == 7:
            game_output("Your building loan matures receive 150")
            player.moneyIn(150)
        elif card == 8:
            game_output("Pay school fees 150")
            player.moneyOut(150, state)
        elif card == 9:
            game_output("You won a prize. Collect 100")
            player.moneyIn(100)
        elif card == 10:
            game_output("Go back three spaces")
            player.moveTo(player.position - 3, state)
        elif card == 11:
            game_output("Advance to 'GO'. Collect 200")
            player.moveTo(0, state)
            player.moneyIn(200)
        elif card == 12:
            game_output("Bank pays you dividend 50")
            player.moneyIn(50)
        elif card == 13:
            game_output("'Drunk in charge'. fine 50")
            player.moneyOut(50, state)
        elif card == 14:
            game_output("Advance to Trafalgar. Get 200 if you pass go")
            if player.position > 24:
                player.moneyIn(200)
            player.moveTo(24, state)
        else:
            game_output("something wrong with community")

        state.board.chanceCards.append(card)



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
    
    def update_property(self, newSelf):
        self.isFullSet = newSelf.isFullSet
        self.isMortgaged = newSelf.isMortgaged
        self.houses = newSelf.houses
        if self.owner != "":
            self.owner.update_player(newSelf.owner)
        self.valueToOwner = newSelf.valueToOwner

    def action(self, player, state, rent=None):
        # owned
        if self.owner == player:
            game_output(player.name + " is the owner of " + self.name)
            return

        # for sale
        elif self.owner == "":
            if player.money >= self.price:
                player.moneyOut(self.price, state)
                self.owner = player
                game_output(player.name + " buy " + self.name)
            else:
                game_output(player.name + " can't buy " + self.name)

        # pay rent
        else:
            if self.isMortgaged:
                game_output(f'{self.name} is mortgaged, no rent for {self.owner.name}')
            else:
                money_taken = player.moneyOut(rent, state)
                self.owner.moneyIn(money_taken)
                game_output(player.name + " pays " + str(money_taken) + " to " + self.owner.name + " for " + self.name)


class Board:
    def __init__(self):
        self.monopoly_board = [
            cell("Go", "go"),
                    #    name              type         price     rent price             house price   group
            Property("Old Kent Road",       "property",   60,    (2, 10, 30,  90, 160, 250),     50,  "brown"),
            cell("Community Chest", "cc"),
            Property("Whitechapel Road",    "property",   60,    (4, 20, 60, 180, 320, 450),     50,  "brown"),
            cell("Income Tax", "Tax"), # 100
            Property("King Cross Station","station",    200,   (0, 25, 50, 100, 200),           0,  "station"),
            Property("The Angel Islington", "property",   100,   (6, 30, 90, 270, 400, 550),     50,  "blue"),
            cell("Chance", "chance"), 
            Property("Euston Road",        "property",    100,   (6, 30, 90, 270, 400, 550),     50,  "blue"),
            Property("Pentonville Road",   "property",    120,   (8, 40, 100, 300, 450, 600),    50,  "blue"),
            cell("Jail", "jail"),
            Property("Pall Mall",          "property",    140,   (10, 50, 150, 450, 625, 750),   100, "pink"),
            Property("Electric Company",   "util"    ,    150,   (0,0,0,0,0),                    0,   "util"),
            Property("Whitehall",          "property",    140,   (10, 50, 150, 450, 625, 750),   100, "pink"),
            Property("Northumberland Avenue","property",  140,   (12, 60, 180, 500, 700, 900),   100, "pink"),
            Property("Marylebone Station", "station",     200,   (0, 25, 50, 100, 200),           0,  "station"),
            Property("Bow Street",         "property",    180,   (14, 70, 200, 550, 700, 950),   100, "orange"),
            cell("Community Chest", "cc"),
            Property("Marlborough Street", "property",    180,   (14, 70, 200, 550, 700, 950),   100, "orange"),
            Property("Vine Street",        "property",    200,   (16, 80, 220, 600, 800, 1000),  100, "orange"),
            cell("Free Parking",           "parking"),
            Property("The Strand",         "property",    220,   (18, 90, 250, 700, 875, 1050),  150, "red"),
            cell("Chance", "chance"),
            Property("Fleet Street",       "property",    220,   (18, 90, 250, 700, 875, 1050),  150, "red"),
            Property("Trafalgar Square",       "property",240,   (18, 100, 300, 750, 925, 1100), 150, "red"),
            Property("Fenchurch Street Station","station",200,   (0, 25, 50, 100, 200),            0, "station"),
            Property("Leicester Square",   "property",    260,   (22, 110, 330, 800, 975, 1150), 150, "yellow"),
            Property("Coventry Street",    "property",    260,   (22, 110, 330, 800, 975, 1150), 150, "yellow"),
            Property("Water Works",        "util"    ,    150,   (0,0,0,0,0),                    0,   "util"),
            Property("Piccadilly",         "property",    280,   (24,120, 360, 850, 1025, 1200), 150, "yellow"),
            cell("Go to Jail", "goJail"),
            Property("Regent Street",      "property",    300,   (26,130, 390, 900, 1100, 1275), 200, "green"),
            Property("Oxford Street",      "property",    300,   (26,130, 390, 900, 1100, 1275), 200, "green"),
            cell("Community Chest", "cc"),
            Property("Bond Street",      "property",      320,   (28,150, 450, 100, 1200, 1400), 200, "green"),
            Property("Liverpool Street Station","station",200,   (0, 25, 50, 100, 200),            0, "station"),
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

    def update_board(self, newSelf):
        for i, updatedProp in enumerate(newSelf.monopoly_board):
            if type(self.monopoly_board[i]) == Property:
                self.monopoly_board[i].update_property(updatedProp)

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

    ## return the number of stations
    def calculateStations(self, station):
        stationsCount = 0
        for prop in self.monopoly_board:
            if type(prop) == Property and prop.type == "station" and station.owner == prop.owner and not prop.isMortgaged:
                stationsCount += 1
        return stationsCount

    ## return the rent amount of stations
    def calculateRent(self, property):
        if type(property) == Property and not property.isMortgaged:
            ## normal property rent (count houses if there some)
            if property.type == "property":
                if property.houses == 0 and property.isFullSet:
                    return property.rent_price[0]*2
                else:
                    return property.rent_price[property.houses]

            ## utility rent (if have 1 or 2) 
            elif property.type == "util":
                if property.isFullSet:
                    return (random.randint(1, 6)+random.randint(1, 6)) * 10
                else:
                    return (random.randint(1, 6)+random.randint(1, 6)) * 4
            
            ## station rent (consider how many player own)
            elif property.type == "station":
                return property.rent_price[self.calculateStations(property)]

            else:
                return "something went wrong with rent"
        else:
            return 0
        
    def totalRent(self, player):
        rent = 0
        for prop in self.monopoly_board:
            if prop.type in ["property","station"] and prop.owner != '' and\
                prop.owner.name == player.name and not prop.isMortgaged:
                rent += self.calculateRent(prop)
        return rent
    
    # this help to find a property to build (already sorted according the build technique)
    # check if the player can build (how much they can pay)
    def whatToBuild(self, player, state):
        # find all possible state of building
        possibleStatesOfBuilding = [self.stateOfBuilding(state, prop) for prop in state.board.monopoly_board \
            if prop.type == "property" and prop.isFullSet and prop.owner == player and prop.houses < 5]
        
        #there is no property to build
        if len(possibleStatesOfBuilding) == 0:
            game_output(f'There is nothing to build')
            return False
        
        resultsOfBuilding = [self.strategy.heuristic(\
            stateOfBuilding.players[state.players.index(self)], stateOfBuilding)\
                for stateOfBuilding in possibleStatesOfBuilding]
        
        maxValueState = possibleStatesOfBuilding[resultsOfBuilding.index(max(resultsOfBuilding))]
        
        state.update_state(maxValueState)

    # this function do build in properties
    def build(self, player, state):
        # find all possible state of building
        possibleStatesOfBuilding = [
            self.stateOfBuilding(state, player, prop)
            for prop in state.board.monopoly_board
            if prop.type == "property"
            and prop.isFullSet
            and prop.owner == player
            and prop.houses < 5
            and prop.house_price <= player.money]
        
        #there is no property to build
        if len(possibleStatesOfBuilding) == 0:
            game_output(f'There is nothing to build')
            return False
        
        resultOfCurrentState = player.strategy.heuristic(player, state)
        resultsOfBuilding = [
            player.strategy.heuristic(stateOfBuilding.players[state.players.index(player)], stateOfBuilding)
            for stateOfBuilding in possibleStatesOfBuilding]
        
        maxValueState = resultsOfBuilding.index(max(resultsOfBuilding))
        
        if resultsOfBuilding[maxValueState] - resultOfCurrentState < player.strategy.build_margin:
            game_output(f'Refuse to build, not much gain')
            return False
        
        state.update_state(possibleStatesOfBuilding[maxValueState])
        
    def stateOfBuilding(self, state, player, space):
        # Create a new state
        new_state = state.newState()

        # Increment the number of houses on the specified property
        targetProp = new_state.board.monopoly_board[state.board.monopoly_board.index(space)]
        targetProp.houses += 1

        # Reduce the player's money by the cost of building a house on the property
        targetPlayer = new_state.players[state.players.index(player)]
        targetPlayer.moneyOut(targetProp.house_price, new_state)

        return new_state
    
    ## return all properties to the game (if player lost)
    def sellAll(self, player):
        for prop in self.monopoly_board:
            if type(prop) == Property and prop.owner == player:
                prop.owner = ""
                prop.houses = 0
                prop.isMortgaged = False
                prop.isFullSet = False

    # calculate the number of deadly properties
    def dangerousProperties(self, player):
        deadly = 0
        propCount = 0
        for prop in self.monopoly_board:
            if prop.type in ["property"]:
                if prop.owner != player and self.calculateRent(prop) > player.money:
                    deadly += 1
                propCount += 1
        
        return deadly / propCount

    ## this make it easier to recall functions after any changes in the board
    def recalculateChanges(self):
        self.isSets()

    def action(self, state, player):
        # Landed on a property - calculate rent first
        if type(self.monopoly_board[player.position]) == Property:
            # calculate the rent one would have to pay (but not pay it yet)
            rent = self.calculateRent(self.monopoly_board[player.position])
            # pass action to to the property
            self.monopoly_board[player.position].action(player, state, rent)
        # other cells
        else:
            self.monopoly_board[player.position].action(player, state)

    ## check if there is a winner (one player alive)
    def gameOver(self, players):
        playersAlive = sum(1 for player in players if player.alive)
        return playersAlive <= 1

class GameState:
    def __init__(self):
        pass

    @staticmethod
    def startState(players):
        starting = GameState()
        # starting.game = game
        starting.board = Board()
        starting.players = copy.deepcopy(players)
        starting.round = 0

        return starting
    
    def newState(self):
        newState = GameState()
        # newState.game = copy.deepcopy(self.game)
        newState.board = copy.deepcopy(self.board)
        newState.players = copy.deepcopy(self.players)
        newState.round = copy.deepcopy(self.round)
        
        return newState
       
    def update_state(self, newState):
        # self.game = newState.game
        self.board.update_board(newState.board)
        for i, player in enumerate(newState.players):
            self.players[i].update_player(player)
        self.round = newState.round

class Game:
    def __init__(self, players, max_rounds):
        self.max_rounds = max_rounds
        self.state = GameState.startState(players)

    def play(self):
        global GAME_OUTPUT
        playing = True
        while playing:
            for player in self.state.players:
                player.strategy.heuristic(player, self.state)
                player.makeAMove(self.state)
                game_output("")
                if self.state.board.gameOver(self.state.players):
                    playing = False
                    GAME_OUTPUT = True
                    for player in self.state.players:
                        if player.alive:
                            game_output(f'Number of rounds is {self.state.round}')
                            game_output(player.name + " is the winner.\n")
                            return player.name
                    break
            if self.state.round > self.max_rounds:
                playing = False
                GAME_OUTPUT = True
                game_output("number of rounds exceeded\n")
            self.state.round += 1

class Strategy:
    def __init__(self, mv, rr, ct, cp, dp, bm):
        self.money_value = mv              # how the player value money
        self.rent_return = rr              # total paid comparing the the rent return
        self.cash_threshold = ct           # minimum cash the player should have
        self.cash_penalty = cp             # negative applied if money lower than cash threshold
        self.deadly_properties = dp        # negative value applied to the number of deadly spaces
        self.build_margin = bm             # gain in heuristic required to build property
          
    def heuristic(self, player, state):
        value =  player.money * self.money_value #the value of money comparing to threshold
        value += state.board.totalRent(player) * self.rent_return

        value -= state.board.dangerousProperties(player) * self.deadly_properties
        if (player.money < self.cash_threshold):
            value -= self.cash_penalty

        return value


def test_series(players, max_rounds, game_num, output):
    global GAME_OUTPUT
    wins = {}
    game_played = 0
    while game_played < game_num:
        game_output(f'\n\nGame {game_played+1}:')
        GAME_OUTPUT = output
        random.shuffle(players)
        game = Game( players, max_rounds )
        winner = game.play()
        if winner == False:
            pass #continue
        else:
            if winner not in wins:
                wins[winner] = 0
            wins[winner] = wins.get(winner) + 1

        game_played += 1

        for player in game.state.players:
            game_output(f'{player.name:6} have {player.money}')

        for x in game.state.board.monopoly_board:
            if x.type == "property":
                if x.owner != "":
                    game_output(f'{x.name:21}: {x.houses} and {x.owner.name:6} is the owner.')
                else:
                    game_output(f'{x.name:21}: {x.houses} and {x.owner:6} is the owner.')
    return wins

global GAME_OUTPUT
GAME_OUTPUT = True
def game_output(*args, end="\n"):
    if GAME_OUTPUT:
       print(*args, end=end)


# self.money_value = mv              # how the player value money
# self.rent_multi = rm               # positive rent return multiplier of property
# self.rent_return = rr              # total paid comparing the the rent return
# self.cash_threshold = ct           # minimum cash the player should have
# self.cash_penalty = cp             # negative applied if money lower than cash threshold
# self.deadly_properties = dp        # negative value applied to the number of deadly spaces
    
s1 = Strategy(0.1, 5, 500, 500, 1, 50)
s2 = Strategy(0.1, 5, 500, 500, 1, 50)

a = Player("Alex", s1)
b = Player("Bop", s1)
c = Player("Alice", s1)
d = Player("Said", s1)

players = [a, b, c, d]
print(test_series(players, 500, 50, output=False))


# players = [a]
# game = Game( players, 500 )

# for x in game.state.board.monopoly_board:
#     if type(x) == Property:
#         a.moveTo(game.state.board.monopoly_board.index(x), game.state)
#         print(f'{x.name:25}: {round(a.strategy.heuristic(a,game.state),4):6} m:{a.money}')

# print()
# players = [b]
# game = Game( players, 500 )
# for x in game.state.board.monopoly_board:
#     if type(x) == Property:
#         b.moveTo(game.state.board.monopoly_board.index(x), game.state)
#         print(f'{x.name:25}: {round(b.strategy.heuristic(b,game.state),4):6} m:{b.money}')
    

