import random
import copy
from fractions import Fraction
import time
import math
import csv

global propertiesLanding
propertiesLanding = [0]*40

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
        self.opponents = []
        
    # money management
    # get paid
    def moneyIn(self, amount):
        self.money += amount
        game_output(str(amount) + " added to " + self.name + " money become " + str(self.money))

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
        global propertiesLanding
        self.position = position
        propertiesLanding[self.position] += 1
        state.board.action(state, self)

    def makeAMove(self, state):
        global propertiesLanding
        # player must be alive to play
        if not self.alive:
            return False

        ## check if there is a property to un mortgage
        while self.unMortgage(state):
            pass

        # buy property (based on gain player get)
        self.buyProperty(state)

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

        propertiesLanding[self.position] += 1

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
            possibleStatesOfMortgage, propertiesToMortgage = [], []
            for prop in playerProperties:
                if not prop.isMortgaged:
                    Mortgage = self.stateOfMortgage(state, prop)
                    if Mortgage != None:
                        possibleStatesOfMortgage.append(Mortgage)
                        propertiesToMortgage.append(prop)

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

            maxValueState = resultsOfMortgage.index(max(resultsOfMortgage))

            chosenProperty = propertiesToMortgage[maxValueState]
            ## sell houses
            if chosenProperty.houses > 0:
                game_output(f'{self.name} sold house from {chosenProperty.name}')
                self.moneyIn(int(chosenProperty.house_price/2))
                chosenProperty.houses -= 1
            else:
                chosenProperty.isMortgaged = True
                game_output(f'{self.name} mortgage {chosenProperty.name}')
                self.moneyIn(int(chosenProperty.price/2))

            state.board.recalculateChanges()

    def stateOfMortgage(self, state, space):
        global GAME_OUTPUT
        current = GAME_OUTPUT
        GAME_OUTPUT = False
        newState = state.newState()
        prop = newState.board.monopoly_board[state.board.monopoly_board.index(space)]
       
        if prop.houses > 0:
            ## sell houses
            newState.players[state.players.index(self)].moneyIn(int(prop.house_price/2))
            prop.houses -= 1
        else:
            for n in prop.neighbors:
                if n.houses > 0:
                    return
            # Mortgage property
            prop.isMortgaged = True
            newState.players[state.players.index(self)].moneyIn(int(prop.price/2))
        newState.board.recalculateChanges()
        GAME_OUTPUT = current
        return newState

    def unMortgage(self, state):
        # find all possible state of UnMortgage
        possibleStatesOfUnMortgage, propertiesToUnMortgage = [], []
        for prop in state.board.monopoly_board:
            if prop.type in ["property", "util", "station"]\
                and prop.owner == self\
                and prop.isMortgaged\
                and prop.price/2 <= self.money-self.strategy.cash_threshold:
                possibleStatesOfUnMortgage.append(self.stateOfUnMortgage(state, prop))
                propertiesToUnMortgage.append(prop)

        if len(possibleStatesOfUnMortgage) == 0:
            return False
        
        resultsOfUnMortgage = [
            self.strategy.heuristic(stateOfUnMortgage.players[state.players.index(self)], stateOfUnMortgage)
            for stateOfUnMortgage in possibleStatesOfUnMortgage]
        
        maxValueState = resultsOfUnMortgage.index(max(resultsOfUnMortgage))
        chosenProperty = propertiesToUnMortgage[maxValueState]

        chosenProperty.isMortgaged = False
        game_output(f'{self.name} unmortgage {chosenProperty.name}')
        self.moneyOut(int(chosenProperty.price/2), state)
        state.board.recalculateChanges()
    
        return True

    def stateOfUnMortgage(self, state, space):
        global GAME_OUTPUT
        current = GAME_OUTPUT
        GAME_OUTPUT = False
        newState = state.newState()
        # set property to not Mortgaged
        prop = newState.board.monopoly_board[state.board.monopoly_board.index(space)]
        prop.isMortgaged = False
        # take money from player
        newState.players[state.players.index(self)].moneyOut(int(prop.price/2), newState)
        newState.board.recalculateChanges()
        GAME_OUTPUT = current
        return newState
    
    ## this functions allow player in his turn to check if he  
    ## wants to buy any available properties (owned by others)
    ## player can buy if the buy gain higher than buy margin
    def buyProperty(self, state):
        buyingPropAndPrice = []
        PlayerCur = self.strategy.heuristic(self, state)
        for prop in state.board.monopoly_board:
            if prop.type == "property" and prop.owner != '' and prop.owner != self and prop.houses == 0:
                price = self.buyingPriceWithinMargin(state, prop.owner, prop, PlayerCur + self.strategy.buy_margin)
                if price != None and price > 0:
                    buyingPropAndPrice.append([prop, price])
                    
        if buyingPropAndPrice == []:
            game_output("No buying offers made by ", self.name)
            return
        
        for property, price in buyingPropAndPrice:
            game_output(f'{self.name:6} offers {price} for {property.name}.')


        acceptedOffers = []
        for property, price in buyingPropAndPrice:
            before = property.owner.strategy.heuristic(property.owner, state)
            after = property.owner.sellStateResult(state, self, property, price)
            opponentsGain = after - before
            if opponentsGain > property.owner.strategy.sell_margin:
                playerBefore = self.strategy.heuristic(property.owner, state)
                playerAfter = self.sellStateResult(state, self, property, price)
                playerGain = playerAfter - playerBefore
                acceptedOffers.append([property, price, playerGain])
            
        
        if acceptedOffers == []:
            game_output(self.name + "'s offers have been declined")
            return
        
        acceptedOffers.sort(key=lambda playerGain: playerGain[2], reverse=True)
        property, price, playerGain = acceptedOffers[0]
        game_output(f'DEAL: {property.owner.name:6} sold {property.name:21} to {self.name:6} for {price}')
        paid = self.moneyOut(price, state)
        property.owner.moneyIn(paid)
        property.owner = self
        state.board.recalculateChanges()


    def buyingPriceWithinMargin(self, state, op, wantProp, targetValue):
        # If player pay nothing, is the property useful for him
        # to make sure getting this property meet the margin
        halfPricePropHeuristicValue = self.buyStateResult(state, op, wantProp, wantProp.price/2)
        if halfPricePropHeuristicValue >= targetValue:
            low = wantProp.price/2
            high = self.money 
            while low + 1 < high:
                mid = (low + high) // 2
                resultMid = self.buyStateResult(state, op, wantProp, mid)
                
                if resultMid <= targetValue:
                    high = mid
                else:
                    low = mid
            return low
        
        return None

    ## some issues occur when create a new state
    # that's why it is missy and I just modify current state
    def buyStateResult(self, state, seller, buyProp, cost):
        global GAME_OUTPUT
        current = GAME_OUTPUT
        GAME_OUTPUT = False
        
        buyProp.owner = self
        self.moneyOut(cost, state)
        seller.moneyIn(cost)
        state.board.recalculateChanges()
        result = self.strategy.heuristic(self, state)
        # return everything
        buyProp.owner = seller
        self.moneyIn(cost)
        seller.moneyOut(cost, state)
        state.board.recalculateChanges()
        GAME_OUTPUT = current
        return result
    
    def sellStateResult(self, state, buyer, sellProp, cost):
        global GAME_OUTPUT
        current = GAME_OUTPUT
        GAME_OUTPUT = False
        
        sellProp.owner = buyer
        buyer.moneyOut(cost, state)
        self.moneyIn(cost)
        state.board.recalculateChanges()
        result = self.strategy.heuristic(self, state)
        # return everything
        sellProp.owner = self
        buyer.moneyIn(cost)
        self.moneyOut(cost, state)
        state.board.recalculateChanges()
        GAME_OUTPUT = current
        return result


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

        # actions
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

        # actions
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
        self.groupShare = 0
        self.isMortgaged = False
        self.houses = 0
        self.owner = ""
        self.neighbors = []

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
                state.board.recalculateChanges()
            else:
                game_output(player.name + " does not have money to buy " + self.name)
                # to avoid biding of stations and utilities
                # deferent mechanism is required for stations and utilities
                if self.type == "property":
                    game_output("start auction")
                    state.output_state()
                    playersBidOrder = state.players[state.players.index(player):] + state.players[:state.players.index(player)]
                    playersBidOrder = [player for player in playersBidOrder if player.alive]
                    bidder, bid = self.auction(state, self.price/2, playersBidOrder)
                    bidder.moneyOut(bid, state)
                    self.owner = bidder
                    game_output(f'{bidder.name} wins the auction of {self.name}, paid {bid}')
                    state.board.recalculateChanges()

        # pay rent
        else:
            if self.isMortgaged:
                game_output(f'{self.name} is mortgaged, no rent for {self.owner.name}')
            else:
                money_taken = player.moneyOut(rent, state)
                self.owner.moneyIn(money_taken)
                game_output(player.name + " pays " + str(money_taken) + " to " + self.owner.name + " for " + self.name)

    def auction(self, state, bid, players):
        while len(players) > 1:
            player = players[0]
            if player.money <= bid:
                game_output(player.name, " does not have enough money to bid")
                players.pop(0)
                continue
            # player current and auction heuristic value
            playerCurrentStateResult = player.strategy.heuristic(player, state)
            playerAuctionStateResult = self.stateOfAuction(state, player, bid)
            playerGain = playerAuctionStateResult - playerCurrentStateResult
            
            # opponents current and auction heuristic value
            opCurrentStateResults = [player.strategy.heuristic(op, state) for op in players[1:]]
            opNewStateResults = [self.stateOfAuction(state, op, bid) for op in players[1:]]
            opponentsGains = [opNewStateResults[i] - opCurrentStateResults[i] for i in range(len(opCurrentStateResults))]
            worstOpNewStateResult = min(opponentsGains)

            # make sure current bidder gain is higher than worst op
            # based on player strategy
            if playerGain > worstOpNewStateResult:
                # next player bidding
                game_output(f'{player.name} bids {(bid+1)} for {self.name}.')
                players.append(players.pop(0))
                bid += 1
            else:
                game_output(player.name, " passes.")
                players.pop(0)

        return (players[0], bid)

    # some issues occur when create a new state
    # that's why it is missy and I just modify current state
    def stateOfAuction(self, state, player, bid):
        global GAME_OUTPUT
        current = GAME_OUTPUT
        GAME_OUTPUT = False

        self.owner = player
        player.moneyOut(bid, state)
        state.board.recalculateChanges()
        result = player.strategy.heuristic(player, state)
        self.owner = ""
        player.moneyIn(bid)
        state.board.recalculateChanges()

        GAME_OUTPUT = current
        return result


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
        # update neighbors for properties in the same group
        for prop in self.monopoly_board:
            if type(prop) == Property:
                for other_prop in self.monopoly_board:
                    if type(other_prop) == Property and prop.group == other_prop.group and prop != other_prop:
                        prop.neighbors.append(other_prop)
            

        # Community Chest
        self.communityCards = list(range(0, 14))
        random.shuffle(self.communityCards)
        # Chance
        self.chanceCards = list(range(0, 15))
        random.shuffle(self.chanceCards)

    ## used to check if property sets, utils, or stations owned by the same player
    # it update 'groupShare' for each
    def isSets(self):
        for prop in self.monopoly_board:
            if type(prop) == Property:
                prop.groupShare = 0

        for prop in self.monopoly_board:
            if type(prop) == Property and prop.owner != "" and not prop.isMortgaged:
                prop.groupShare += Fraction(1,(len(prop.neighbors)+1))
                for neighbor in prop.neighbors:
                    if neighbor.owner != "" and prop.owner.name == neighbor.owner.name:
                        neighbor.groupShare += Fraction(1,(len(prop.neighbors)+1))

    ## return the number of stations
    def calculateStations(self, station):
        stationsCount = 0
        for prop in self.monopoly_board:
            if type(prop) == Property and prop.type == "station" and prop.owner != ""\
                and station.owner != "" and station.owner.name == prop.owner.name and not prop.isMortgaged:
                stationsCount += 1
        return stationsCount

    ## return the rent amount of stations
    def calculateRent(self, property):
        if type(property) == Property and not property.isMortgaged:
            ## normal property rent (count houses if there some)
            if property.type == "property":
                if property.houses == 0 and property.groupShare == 1:
                    return property.rent_price[0]*2
                else:
                    return property.rent_price[property.houses]

            ## utility rent (if have 1 or 2) 
            elif property.type == "util":
                if property.groupShare == 1:
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
    
    # this function do build in properties
    def build(self, player, state):
        
        # find all possible state of building
        possibleStatesOfBuilding, propertiesToBuild = [], []
        for prop in state.board.monopoly_board:
            if prop.type == "property" \
                and prop.groupShare == 1 \
                and prop.owner == player \
                and prop.houses < 5 \
                and prop.house_price <= player.money-player.strategy.cash_threshold:
                
                # make sure there is one house difference in any set
                housesInSet = prop.houses
                housesInSet += sum([housesInSet.houses for housesInSet in prop.neighbors])
                maxInProp = min((math.ceil(housesInSet / (len(prop.neighbors)+1) + 0.1)), 5)
                if prop.houses < maxInProp:
                    propertiesToBuild.append(prop)
                    possibleStatesOfBuilding.append(self.stateOfBuilding(state, player, prop))
        
        #there is no property to build
        if len(possibleStatesOfBuilding) == 0:
            game_output(f'There is nothing to build')
            return False
        
        # resultOfCurrentState = player.strategy.heuristic(player, state)
        resultsOfBuilding = [
            player.strategy.heuristic(stateOfBuilding.players[state.players.index(player)], stateOfBuilding)
            for stateOfBuilding in possibleStatesOfBuilding]
        
        # get the index of hights value state
        maxValueState = resultsOfBuilding.index(max(resultsOfBuilding))
        
        targetProp = propertiesToBuild[maxValueState]
        targetProp.houses += 1

        # Reduce the player's money by the cost of building a house on the property
        player.moneyOut(targetProp.house_price, state)
        state.board.recalculateChanges()

        return True
        
    def stateOfBuilding(self, state, player, space):
        global GAME_OUTPUT
        current = GAME_OUTPUT
        GAME_OUTPUT = False
        # Create a new state
        newState = state.newState()

        # Increment the number of houses on the specified property
        targetProp = newState.board.monopoly_board[state.board.monopoly_board.index(space)]
        targetProp.houses += 1

        # Reduce the player's money by the cost of building a house on the property
        targetPlayer = newState.players[state.players.index(player)]
        targetPlayer.moneyOut(targetProp.house_price, newState)

        newState.board.recalculateChanges()
        GAME_OUTPUT = current
        return newState
    
    ## return all properties to the game (if player lost)
    def sellAll(self, player):
        for prop in self.monopoly_board:
            if type(prop) == Property and prop.owner == player:
                prop.owner = ""
                prop.houses = 0
                prop.isMortgaged = False
                prop.groupShare = 0

    # calculate the number of deadly properties
    def dangerousProperties(self, player):
        deadly = 0
        propCount = 0
        for prop in self.monopoly_board:
            if prop.type in ["property"]:
                if prop.owner != ""\
                and prop.owner.name != player.name\
                and self.calculateRent(prop) > player.money:
                    deadly += 1
                propCount += 1
        
        return deadly / propCount
    
    # this calculate total cost to improve and total rent return
    # it calculate these values for the whole set not individual properties
    def propertiesEvaluation(self, player):
        tPropEvaluation = 0
        for prop in self.monopoly_board:
            propEvaluation = 0
            if prop.type == "property" and prop.owner != "" and prop.owner == player:
                for n in prop.neighbors:
                    propEvaluation += n.rent_price[5] / (n.house_price*5)
                setSize = len(prop.neighbors)+1
                propEvaluation += prop.rent_price[5] / (prop.house_price*5)
                if prop.groupShare == 1:
                    tPropEvaluation += round(propEvaluation/setSize*6,3)
                else:
                    tPropEvaluation += round((propEvaluation/setSize)*(prop.groupShare*3\
                                        if prop.group not in ["brown","dark blue"]\
                                            else prop.groupShare*2),2)
            tPropEvaluation += propEvaluation
        return tPropEvaluation
    
    def landingOnLikelihood(self, player):
        likelihoodDict = {"Old Kent Road"        : 4.95,
                          "Whitechapel Road"     : 3.57,
                          "The Angel Islington"  : 4.17,
                          "Euston Road"          : 4.35,
                          "Pentonville Road"     : 4.18,
                          "Pall Mall"            : 5.69,
                          "Whitehall"            : 4.29,
                          "Northumberland Avenue": 4.2,
                          "Bow Street"           : 4.94,
                          "Marlborough Street"   : 5.15,
                          "Vine Street"          : 5.56,
                          "The Strand"           : 4.7,
                          "Fleet Street"         : 4.41,
                          "Trafalgar Square"     : 6.22,
                          "Leicester Square"     : 4.46,
                          "Coventry Street"      : 4.49,
                          "Piccadilly"           : 4.26,
                          "Regent Street"        : 4.25,
                          "Oxford Street"        : 4.11,
                          "Bond Street"          : 3.86,
                          "Park Lane"            : 3.34,
                          "Mayfair"              : 5.03}
        totalLikelihood = 0
        for prop in self.monopoly_board:
            if prop.type == "property" and prop.owner != "" and prop.owner == player:
                totalLikelihood += likelihoodDict[prop.name]
        return totalLikelihood
    
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
        starting.board = Board()
        starting.players = copy.deepcopy(players)
        starting.round = 0

        return starting
    
    def newState(self):
        newState = GameState()
        newState.board = copy.deepcopy(self.board)
        newState.players = copy.deepcopy(self.players)
        newState.round = copy.deepcopy(self.round)
        
        return newState
       
    def output_state(self):
        game_output(f'name |money  |position')
        for player in self.players:
            game_output(f'{player.name:5}|{player.money:7}|{player.position:2}|{player.alive}')
        
        game_output(f'property name            | rent | houses | owner | isMortgaged |groupShare ')
        for prop in self.board.monopoly_board:
            if prop.type in ["property", "station"]:
                if prop.owner != "":
                    game_output(f'{prop.name:24} | {self.board.calculateRent(prop):^4} | {prop.houses:^6} | {prop.owner.name:^5} | {prop.isMortgaged:^11} | {round(float(prop.groupShare),2):2}')
                else:
                    game_output(f'{prop.name:24} | {self.board.calculateRent(prop):^4} | {prop.houses:^6} | {prop.owner:^5} | {prop.isMortgaged:^11} | {round(float(prop.groupShare),2):2}')

class Game:
    def __init__(self, players, max_rounds):
        self.max_rounds = max_rounds
        self.state = GameState.startState(players)
        self.rounds = 0

    def play(self):
        for player in self.state.players:
            for op in self.state.players:
                if player != op:
                    player.opponents.append(op)
        global GAME_OUTPUT
        playing = True
        while playing:
            game_output(f'Round {self.state.round}:')
            for player in self.state.players:
                game_output(f'{player.name:} turn:')
                player.makeAMove(self.state)
                game_output(f'')
                if self.state.board.gameOver(self.state.players):
                    playing = False
                    for player in self.state.players:
                        if player.alive:
                            game_output(f'Number of rounds is {self.state.round}')
                            game_output(player.name + " is the winner.\n")
                            return player.name
                    break
            if self.state.round > self.max_rounds:
                playing = False
                game_output("number of rounds exceeded\n")
                return False
            self.state.output_state()
            self.state.round += 1      

class Strategy:
    def __init__(self, rr, opm, oprr, ct, cp, dp, pe, lp, bm, sm):
        self.rent_return = rr            # positive multiplier of total rent return
        self.op_money = opm              # negative multiplier of total opponents' money
        self.op_rent_return = oprr       # negative multiplier of total opponents' rent return
        self.cash_threshold = ct         # minimum cash the player should have
        self.cash_penalty = cp           # negative applied if money lower than cash threshold
        self.deadly_properties = dp      # negative value applied to the number of deadly spaces
        self.property_evaluation = pe    # positive multiplier for total properties evaluation
        self.landing_property = lp       # positive multiplier for total likelihood of landing on player's properties
        self.buy_margin = bm           # heuristic gain to buy property
        self.sell_margin = sm         # heuristic gain to sell property
          
    def heuristic(self, player, state):
        value =  player.money
        value += state.board.totalRent(player) * self.rent_return

        value -= sum( [opponent.money for opponent in player.opponents] ) * self.op_money
        value -= sum( [state.board.totalRent(opponent) for opponent in player.opponents] ) * self.op_rent_return

        if (player.money < self.cash_threshold):
            value -= self.cash_penalty * (1-(player.money/self.cash_threshold))

        value -= state.board.dangerousProperties(player) * self.deadly_properties
        value += state.board.propertiesEvaluation(player) * self.property_evaluation
        value += state.board.landingOnLikelihood(player) * self.landing_property

        return value



def testSeries(players, max_rounds, game_num, output, data=[]):
    global GAME_OUTPUT
    wins = {}
    for player in players:
        wins[player.name] = 0
    game_played, progress = 0, 1
    # print("test started\nprogress:")
    while game_played < game_num:
        GAME_OUTPUT = output
        # game_output(f'\n\nGame {game_played+1}:')
        random.shuffle(players)
        game = Game( players, max_rounds )
        winner = game.play()
        if winner != False:
            wins[winner] = wins.get(winner) + 1
            game_played += 1
            if game_played == game_num/10*progress and output == False:
                per = game_played/game_num*100
                print(f'{int(per)}%', end='\r')
                progress += 1

        # GAME_OUTPUT = True
        # game.state.output_state()
        # GAME_OUTPUT = output
    
    print('\n')
    print("PLAYER   | WINS | PERCENT       rr  | opmv | oprr |  ct   |  cp   |  dp   | pe   |  lp  | bm   | sm   ")
    data.append(["game:", game_played, "------", "------"])
    data.append(["PLAYER","WINS","PERCENT", "rr", "opmv", "oprr","ct", "cp ", "dp", "pe", "lp", "bm", "sm"])
    for player in players:
        games_won = wins[player.name]
        percentage = round((games_won/game_num)*100,2)
        s = player.strategy
        print(f'{player.name:<8} | {games_won:^4} | {percentage:^5}%        '\
              f'{s.rent_return:^3} | {s.op_money:^4} | {s.op_rent_return:^4} | '\
              f'{s.cash_threshold:^5} | {s.cash_penalty:^5} | {s.deadly_properties:^5} | '\
              f'{s.property_evaluation:^4} | {s.landing_property:^4} | {s.buy_margin:^4} | {s.sell_margin:^4} ')
        data.append([player.name, games_won, percentage,
              s.rent_return, s.op_money, s.op_rent_return,
              s.cash_threshold, s.cash_penalty, s.deadly_properties,
              s.property_evaluation, s.landing_property, s.buy_margin, s.sell_margin])
    with open("output.csv", "w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerows(data)

    return wins

global GAME_OUTPUT
GAME_OUTPUT = True
def game_output(*args, end="\n"):
    if GAME_OUTPUT:
       print(*args, end=end)


## testSeries
s1 = Strategy(15, 0, 0, 0, 0, 9000, 0, 0, 50, 250)
s2 = Strategy(15, 0, 0, 0, 0, 9000, 9, 0, 50, 250)
s3 = Strategy(15, 0, 0, 0, 0, 9000, 0, 10, 50, 250)
s4 = Strategy(15, 0, 0, 0, 0, 9000, 9, 10, 50, 250) # the most optimal

a = Player("Player1", s1)
b = Player("Player2", s2)
c = Player("Player3", s3)
d = Player("Test", s4)
players = [a, b, c, d]

start = time.time()
# testSeries(players, 200, 2000, output=False)
end = time.time()
print(round((end-start)/60,2))

################## random generated strategies
s1 = Strategy(13, 0.2, 00.8, 44, 915, 4563, 0, 0, 168, 284)
s2 = Strategy(7, 0.2, 1, 29, 605, 6123, 0, 0, 158, 187)
s3 = Strategy(5, 0, 0.3, 16, 395, 1292, 0, 0, 242, 231)
s4 = Strategy(0, 8, 5, 2, 6, 500, 0, 0, 50, 250)

a = Player("Player1", s1)
b = Player("Player2", s2)
c = Player("Player3", s3)
d = Player("Player4", s4)

players = [a, b, c, d]

def evaluate_strategy(players, max_rounds, game_num):
    wins = testSeries(players, max_rounds, game_num, False)
    # highest = max(wins, key=lambda key: wins[key])
    lowest = min(wins, key=lambda key: wins[key])
    lowestPlayer = None
    for person in players:
        if getattr(person, "name") == lowest:
            lowestPlayer = person
            break
    return lowestPlayer
        
def generate_new_strategy():
    rr = random.randint(5,15)
    opm = round(random.uniform(0,1),1)
    oprr = round(random.uniform(0,1),1)
    ct = random.randint(0,500)
    cp = random.randint(0,1000)
    dp = random.randint(0,10000)
    pe = random.randint(0,0)
    pl = random.randint(0,0)
    bm = random.randint(0,300)
    sm = random.randint(0,300)
    return Strategy(rr, opm, oprr, ct, cp, dp, pe, pl, bm, sm)

def random_strategies(players, max_rounds, game_num, iterations):
    newLowestPlayer = evaluate_strategy(players, max_rounds, game_num)
    for _ in range(iterations):
        new_strategy = generate_new_strategy()
        setattr(newLowestPlayer, "strategy", new_strategy)
        newLowestPlayer = evaluate_strategy(players, max_rounds, game_num)

start = time.time()
iterations = 100
random_strategies(players, 150, 1000, iterations)
end = time.time()
print(round((end-start)/60,2))


################## hill_climbing
s1 = Strategy(13, 0.2, 00.8, 44, 915, 4563, 0, 0, 168, 284)
s2 = Strategy(14, 0.2, 1, 29, 605, 6123, 0, 0, 158, 187)
s3 = Strategy(12, 0, 0.3, 16, 395, 1292, 0, 0, 242, 231)
s4 = Strategy(15, 0, 0, 0, 0, 9000, 0, 0, 50, 250)

a = Player("Player1", s1)
b = Player("Player2", s2)
c = Player("Player3", s3)
d = Player("Test", s4)

players = [a, b, c, d]

def evaluate_strategy(players, max_rounds, game_num):
    testSeries(players, max_rounds, game_num, False)
    for player in players:
        if getattr(player, "name") == "Test":
            return player

def generate_new_strategy(changing_val):
    return Strategy(15, 0, 0, 0, 0, 9000, changing_val, 0, 50, 250)

def hill_climbing(players, max_rounds, game_num):
    newLowestPlayer = evaluate_strategy(players, max_rounds, game_num)
    changing_val = 0
    while changing_val < 10:
        changing_val += 1
        new_strategy = generate_new_strategy(changing_val)
        setattr(newLowestPlayer, "strategy", new_strategy)
        newLowestPlayer = evaluate_strategy(players, max_rounds, game_num)

start = time.time()
# hill_climbing(players, 150, 1000)
end = time.time()
print(round((end-start)/60,2))
