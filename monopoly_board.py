import random
import copy
from fractions import Fraction
import time

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
        self.position = position
        state.board.action(state, self)

    def makeAMove(self, state):
        # player must be alive to play
        if not self.alive:
            return False

        # state.board.recalculateChanges()

        ## check if there is a property to un mortgage
        while self.unMortgage(state):
            pass

        # check all possible states of trading
        # self.tradeProperty(state)

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
                    possibleStatesOfMortgage.append(self.stateOfMortgage(state, prop))
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
                self.moneyIn(int(chosenProperty.house_price/2))
                chosenProperty.houses -= 1
            else:
                chosenProperty.isMortgaged = True
                self.moneyIn(int(chosenProperty.price/2))

            state.board.recalculateChanges()

    def stateOfMortgage(self, state, space):
        newState = state.newState()
        prop = newState.board.monopoly_board[state.board.monopoly_board.index(space)]
        ## sell houses
        if prop.houses > 0:
            newState.players[state.players.index(self)].moneyIn(int(prop.house_price/2))
            prop.houses -= 1
        else:
            prop.isMortgaged = True
            newState.players[state.players.index(self)].moneyIn(int(prop.price/2))
        newState.board.recalculateChanges()
        return newState

    def unMortgage(self, state):
        # find all possible state of UnMortgage
        possibleStatesOfUnMortgage, propertiesToUnMortgage = [], []
        for prop in state.board.monopoly_board:
            if prop.type in ["property", "util", "station"] and prop.owner == self and prop.isMortgaged and prop.price/2 <= self.money:
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
        self.moneyOut(int(chosenProperty.price/2), state)
        state.board.recalculateChanges()
    
        return True

    def stateOfUnMortgage(self, state, space):
        newState = state.newState()
        prop = newState.board.monopoly_board[state.board.monopoly_board.index(space)]
        prop.isMortgaged = False
        newState.players[state.players.index(self)].moneyOut(int(prop.price/2), newState)
        newState.board.recalculateChanges()
        return newState
    
    ## this functions allow player in his turn to check if he  
    ## wants to buy any available properties (owned buy others)
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
            game_output(f'{self.name:6}:{self.money:6} offers £{price} for {property.name}:{property.owner.name}.')


        acceptedOffers = []
        for property, price in buyingPropAndPrice:
            before = property.owner.strategy.heuristic(property.owner, state)
            after = property.owner.sellStateResult(state, self, property, price)
            gain = after - before
            if gain > property.owner.strategy.sell_margin:
                acceptedOffers.append([property, price, gain])
                before = property.owner.strategy.heuristic(property.owner, state)
                after = property.owner.sellStateResult(state, self, property, price)
            
        
        
        if acceptedOffers == []:
            game_output(self.name + "'s offers have been declined")
            return
        
        acceptedOffers.sort(key=lambda gain: gain[2], reverse=True)
        property, price, gain = acceptedOffers[0]
        game_output(f'DEAL: {property.owner.name:6} sold {property.name:21} to {self.name:6} for {price} of value {round(gain,2):5}')
        paid = self.moneyOut(price, state)
        property.owner.moneyIn(paid)
        property.owner = self
        state.board.recalculateChanges()


    def buyingPriceWithinMargin(self, state, op, wantProp, targetValue):
        # If player pay nothing, is the property useful for him
        # to make sure getting this property meet the margin
        BuyResultWithZero = self.buyStateResult(state, op, wantProp, wantProp.price/2)
        if BuyResultWithZero >= targetValue:
            low = 0
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

    def buyStateResult(self, state, seller, buyProp, cost):
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
        return result
    
    def sellStateResult(self, state, buyer, sellProp, cost):
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
        return result



    def tradeProperty(self, state):
        state.output_state()
        possibleStatesOfTrade, resultsOfTrade = [], []
        give, get = [], []
        for plyerProperty in filter(lambda prop: prop.type == "property" and prop.owner == self and prop.houses == 0, state.board.monopoly_board):
            for targetProperty in filter(lambda prop: prop.type == "property" and prop.owner != "" and prop.owner != self and prop.houses == 0, state.board.monopoly_board):
                # current state value for opponent (based on player strategy, who makes the offer)
                playerPropCur = self.strategy.propertyHeuristic(plyerProperty)
                # current state value for opponent (based on target player strategy)
                opPropCur = targetProperty.owner.strategy.propertyHeuristic(targetProperty)

                tradingState = self.stateOfTrade(state, plyerProperty, targetProperty)
                # trading state value for player and opponent (based on player strategy, who makes the offer)
                playerPropTrade = self.strategy.propertyHeuristic(tradingState.board.monopoly_board[state.board.monopoly_board.index(plyerProperty)])
                # trading state value for opponent (based on target player strategy)
                opPropTrade = targetProperty.owner.strategy.propertyHeuristic(tradingState.board.monopoly_board[state.board.monopoly_board.index(targetProperty)])

                # check if there is a gain on trading
                # this gain must be more than opponent gain
                # opponent have a gain value as well
                print(f'{plyerProperty.owner.name:6}|{plyerProperty.name:21}|{round(playerPropCur,2):^8}|{round(playerPropTrade,2):^8}|{playerPropTrade > playerPropCur}')
                print(f'{targetProperty.owner.name:6}|{targetProperty.name:21}|{round(opPropCur,2):8}|{round(opPropTrade,2):^8}|{opPropTrade > opPropCur}')
                print("-------------------------------------------")
                if playerPropTrade > playerPropCur\
                    and opPropTrade > opPropCur:
                    resultsOfTrade.append((playerPropTrade-playerPropCur)\
                                          -(opPropTrade-opPropCur))
                    give.append(plyerProperty)
                    get.append(targetProperty)
        
        if len(resultsOfTrade) == 0:
            return False
        
        maxValueState = resultsOfTrade.index(max(resultsOfTrade))

        haveProp = give[maxValueState]
        wantProp =  get[maxValueState]
        haveProp.owner, wantProp.owner = wantProp.owner, haveProp.owner
        state.board.recalculateChanges()
    
    def stateOfTrade(self, state, have, want):
        newState = state.newState()
        haveProp = newState.board.monopoly_board[state.board.monopoly_board.index(have)]
        wantProp = newState.board.monopoly_board[state.board.monopoly_board.index(want)]
        haveProp.owner, wantProp.owner = wantProp.owner, haveProp.owner
        newState.board.recalculateChanges()
        return newState
    

    def tradeProperty(self, state):
        # state.output_state()
        possibleStatesOfTrade, resultsOfTrade = [], []
        resultOfCurrentStateForPlayer = self.strategy.heuristic(self, state)
        give, get = [], []
        for plyerProperty in filter(lambda prop: prop.type == "property" and prop.owner == self and prop.houses == 0, state.board.monopoly_board):
            for targetProperty in filter(lambda prop: prop.type == "property" and prop.owner != "" and prop.owner != self and prop.houses == 0, state.board.monopoly_board):
                # current state value for opponent (based on player strategy, who makes the offer)
                playerResultOfCurrentStateForOpponent = self.strategy.heuristic(state.players[state.players.index(targetProperty.owner)], state)
                # current state value for opponent (based on target player strategy)
                resultOfCurrentStateForOpponent = targetProperty.owner.strategy.heuristic(state.players[state.players.index(targetProperty.owner)], state)

                tradingState = self.stateOfTrade(state, plyerProperty, targetProperty)
                # trading state value for player and opponent (based on player strategy, who makes the offer)
                resultForPlayer = self.strategy.heuristic(tradingState.players[state.players.index(plyerProperty.owner)], tradingState)
                PlayerResultForOpponent = self.strategy.heuristic(tradingState.players[state.players.index(targetProperty.owner)], tradingState)
                # trading state value for opponent (based on target player strategy)
                resultForOpponent = targetProperty.owner.strategy.heuristic(tradingState.players[state.players.index(targetProperty.owner)], tradingState)

                # check if there is a gain on trading
                # this gain must be more than opponent gain
                # opponent have a gain value as well
                # print(f'{plyerProperty.owner.name:6}|{plyerProperty.name:21}|{round(resultOfCurrentStateForPlayer,2):^8}|{round(resultForPlayer,2):^8}|{resultForPlayer > resultOfCurrentStateForPlayer}')
                # print(f'{targetProperty.owner.name:6}|{targetProperty.name:21}|{round(resultOfCurrentStateForOpponent,2):8}|{round(resultForOpponent,2):^8}|{resultForOpponent > resultOfCurrentStateForOpponent}')
                # print("-------------------------------------------")
                if resultForPlayer > resultOfCurrentStateForPlayer\
                    and resultForOpponent > resultOfCurrentStateForOpponent:
                    possibleStatesOfTrade.append(tradingState)
                    resultsOfTrade.append((resultOfCurrentStateForPlayer-resultForPlayer)\
                                          -(resultOfCurrentStateForOpponent-resultForOpponent))
                    give.append(plyerProperty)
                    get.append(targetProperty)
        
        if len(possibleStatesOfTrade) == 0:
            return False
        
        maxValueState = resultsOfTrade.index(max(resultsOfTrade))
        # state.output_state()
        haveProp = give[maxValueState]
        wantProp =  get[maxValueState]
        haveProp.owner, wantProp.owner = wantProp.owner, haveProp.owner
        state.board.recalculateChanges()
    
    def stateOfTrade(self, state, have, want):
        newState = state.newState()
        haveProp = newState.board.monopoly_board[state.board.monopoly_board.index(have)]
        wantProp = newState.board.monopoly_board[state.board.monopoly_board.index(want)]
        haveProp.owner, wantProp.owner = wantProp.owner, haveProp.owner
        newState.board.recalculateChanges()
        return newState





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
                    # state.output_state()
                    # playersBidOrder = state.players[state.players.index(player):] + state.players[:state.players.index(player)]
                    # bidder, bid = self.auction(state, self.price/2, playersBidOrder)
                    # bidder.moneyOut(bid, state)
                    # self.owner = bidder
                    # game_output(bidder.name + " wins the auction of " + self.name)
                    # state.board.recalculateChanges()



        # pay rent
        else:
            if self.isMortgaged:
                game_output(f'{self.name} is mortgaged, no rent for {self.owner.name}')
            else:
                money_taken = player.moneyOut(rent, state)
                self.owner.moneyIn(money_taken)
                game_output(player.name + " pays " + str(money_taken) + " to " + self.owner.name + " for " + self.name)

    def auction(self, state, bid, players):
        player = players[0]
        if len(players) == 1:
            return (player, bid)
        if player.money <= bid:
            game_output(player.name, " does not have enough money to bid")
            return self.auction(state, bid, players[1:])
        # player current state and result
        playerCurrentStateResult = player.strategy.heuristic(player, state)
        # player auction state and result
        playerAuctionStateResult = self.stateOfAuction(state, player, bid)
        # playerAuctionState, bidder = self.stateOfAuction(state, player, bid)
        # playerAuctionState.output_state()
        # playerAuctionStateResult = player.strategy.heuristic(bidder, playerAuctionState)
        
        playerGain = playerAuctionStateResult - playerCurrentStateResult
        ################# op
        # opponents current states and results
        opCurrentStateResults = [player.strategy.heuristic(op, state) for op in players[1:]]
        # opponents auction states and results
        opNewStateResults = [self.stateOfAuction(state, op, bid) for op in players[1:]] # return state and bidder
        # for ss in opAuctionState[0]:
        #     ss.output_state()
        # opNewStateResults = [player.strategy.heuristic(opStates[1], opStates[0]) for opStates in opAuctionState]

        opponentsGains = [opNewStateResults[i] - opCurrentStateResults[i] for i in range(len(opCurrentStateResults))]
        worstOpNewStateResult = min( opNewStateResults )
        playersList = players[1:]
        playersList.append(player)
        # print(str(playerGain) + " " + str(opponentsGains))
        ## make sure current bidder gain is higher than others
        if playerAuctionStateResult > worstOpNewStateResult:
            game_output( f'{playersList[0].name} bids {bid+1} for {self.name}.')
            return self.auction( state, bid+1, playersList)
        else:
            game_output( player.name, " passes.")
            return self.auction( state, bid+1, playersList[:-1])

    def stateOfAuction(self, state, player, bid):
        self.owner = player
        # player.moneyOut(bid, state)
        state.board.recalculateChanges()
        result = player.strategy.heuristic(player, state)
        self.owner = ""
        player.moneyIn(bid)
        state.board.recalculateChanges()
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
                    if neighbor.owner != "" and prop.owner == neighbor.owner:
                        neighbor.groupShare += Fraction(1,(len(prop.neighbors)+1))

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
                and prop.house_price <= player.money:
                
                propertiesToBuild.append(prop)
                possibleStatesOfBuilding.append(self.stateOfBuilding(state, player, prop))
        
        #there is no property to build
        if len(possibleStatesOfBuilding) == 0:
            game_output(f'There is nothing to build')
            return False
        
        resultOfCurrentState = player.strategy.heuristic(player, state)
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
        # Create a new state
        new_state = state.newState()

        # Increment the number of houses on the specified property
        targetProp = new_state.board.monopoly_board[state.board.monopoly_board.index(space)]
        targetProp.houses += 1

        # Reduce the player's money by the cost of building a house on the property
        targetPlayer = new_state.players[state.players.index(player)]
        targetPlayer.moneyOut(targetProp.house_price, new_state)

        new_state.board.recalculateChanges()
        return new_state
    
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
                if prop.owner != "" and prop.owner.name != player.name and self.calculateRent(prop) > player.money:
                    deadly += 1
                propCount += 1
        
        return deadly / propCount
    
    def propertyShareInGroup(self, group, player):
        propertiesCount = 0
        ownedProperties = 0
        for prop in self.monopoly_board:
            if prop.type == "property" and prop.group == group:
                propertiesCount += 1
                if prop.owner == player:
                    ownedProperties += 1
        
        return ownedProperties / propertiesCount
    
    def totalShares(self, player):
        totalCount = Fraction(0)
        for prop in self.monopoly_board:
            if prop.type == "property" and prop.owner != "" and prop.owner.name == player.name:
                totalCount += prop.groupShare
        
        return totalCount
    
    # this calculate total cost and total rent return
    # it has been created for the whole set not individual properties
    def propertiesRentReturn(self, player):
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
                    tPropEvaluation += round((propEvaluation/setSize)*(prop.groupShare*3 if prop.group not in ["brown","dark blue"] else prop.groupShare*2),2)
            tPropEvaluation += propEvaluation
        return tPropEvaluation
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
        print(f'name |money|po')
        for player in self.players:
            print(f'{player.name:5}|{player.money:5}|{player.position:2}')
        
        print(f'property:                |owner|groupShare')
        for prop in self.board.monopoly_board:
            if prop.type == "property":
                if prop.owner != "":
                    print(f'{prop.name:25}|{prop.owner.name:5}|{round(float(prop.groupShare),3):2}')
                else:
                    print(f'{prop.name:25}|{prop.owner:5}|{round(float(prop.groupShare),3):2}')

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
            for player in self.state.players:
                # player.strategy.heuristic(player, self.state)
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
                return False
            self.state.round += 1

class Strategy:
    def __init__(self, rr, opmv, oprr, ct, cp, dp, pe, buym, sellm):
        self.rent_return = rr              # positive multiplier of total rent return
        self.opponent_money_value = opmv   # negative multiplier of total opponents' money
        self.opponent_rent_return = oprr   # negative multiplier of total opponents' rent return
        self.cash_threshold = ct           # minimum cash the player should have
        self.cash_penalty = cp             # negative applied if money lower than cash threshold
        self.deadly_properties = dp        # negative value applied to the number of deadly spaces
        self.properties_evaluation = pe    # positive multiplier for total properties evaluation
        self.buy_margin = buym             # heuristic gain to buy property
        self.sell_margin = sellm           # heuristic gain to sell property
          
    def heuristic(self, player, state):
        value =  player.money
        value += state.board.totalRent(player) * self.rent_return

        value -= sum( [opponent.money for opponent in player.opponents] ) * self.opponent_money_value
        value -= sum( [state.board.totalRent(opponent) for opponent in player.opponents] ) * self.opponent_rent_return

        if (player.money < self.cash_threshold):
            value -= self.cash_penalty * (1-(player.money/self.cash_threshold))

        value -= state.board.dangerousProperties(player) * self.deadly_properties

        value += state.board.propertiesRentReturn(player) * self.properties_evaluation

        return value



def testSeries(players, max_rounds, game_num, output):
    global GAME_OUTPUT
    wins = {}
    game_played = 0
    while game_played < game_num:
        game_output(f'\n\nGame {game_played+1}:')
        GAME_OUTPUT = output
        random.shuffle(players)
        game = Game( players, max_rounds )
        winner = game.play()
        if winner != False:
            if winner not in wins:
                wins[winner] = 0
            wins[winner] = wins.get(winner) + 1
            game_played += 1

        for player in game.state.players:
            game_output(f'{player.name:6} have {player.money}')

        for x in game.state.board.monopoly_board:
            if x.type == "property":
                if x.owner != "":
                    game_output(f'{x.name:21} | {x.houses} | {x.owner.name:5} | {round(float(x.groupShare),2):2}')
                else:
                    game_output(f'{x.name:21} | {x.houses} | {x.owner:5} | {round(float(x.groupShare),2):2}')
    
    
    print("PLAYER     WINS  PERCENT  |   RM  OPM  OPR   BM  SM   RES  RPEN   JEPAV")
    for player in players:
        games_won = wins[player.name]
        percentage = round((games_won/game_num)*100,2)
        strategy = player.strategy
        print(f'{player.name:<6} {games_won:<4} {percentage:<5}%')

global GAME_OUTPUT
GAME_OUTPUT = True
def game_output(*args, end="\n"):
    if GAME_OUTPUT:
       print(*args, end=end)



# self.rent_return = rr              # positive multiplier of total rent return
# self.opponent_money_value = opmv   # negative multiplier of total opponents' money
# self.opponent_rent_return = oprr   # negative multiplier of total opponents' rent return
# self.cash_threshold = ct           # minimum cash the player should have
# self.cash_penalty = cp             # negative applied if money lower than cash threshold
# self.deadly_properties = dp        # negative value applied to the number of deadly spaces
# self.buy_margin = buym
# self.sell_margin = sellm

s1 = Strategy(3, 0, 0.5, 0, 500, 2000, 3, 200, 200)
s2 = Strategy(8, 0, 0.5, 0, 500, 2000, 0, 200, 200)
s3 = Strategy(7, 0.3, 0.3, 100, 5000, 20000, 8, 80, 80)
s4 = Strategy(9, 0.2, 0.2, 0, 5000, 20000, 10, 150, 150)

a = Player("Alex", s1)
b = Player("Bop", s2)
c = Player("Alice", s1)
d = Player("Said", s1)

players = [a, b]
start = time.time()
print(testSeries(players, 200, 200, output=False))
end = time.time()
print(end-start)


# game = Board()
# z = True
# for x in game.monopoly_board:
#     if x.type == "property":
#         # if z:
#         x.owner = a
#         #     z = False
#         # else:
#         #     z = True
# game.isSets()
# playerCashScore = a.money * 0.01
# tPropEvaluation = 0
# for prop in game.monopoly_board:
#     propEvaluation = 0
#     if prop.type == "property" and prop.owner != "" and prop.owner == a:
#         for n in prop.neighbors:
#             propEvaluation += n.rent_price[5] / (n.house_price*5)
#         setSize = len(prop.neighbors)+1
#         propEvaluation += prop.rent_price[5] / (prop.house_price*5)
#         # if prop.groupShare == 1:
#         #     tPropEvaluation = round(propEvaluation/setSize*6,3)
#         #     print(f'{prop.name:21} value {tPropEvaluation}')
#         # else:
#         # tPropEvaluation = round((propEvaluation/setSize)*(prop.groupShare*3 if prop.group not in ["brown","dark blue"] else prop.groupShare*2),2)
#         one =  round((propEvaluation/setSize)*(1 if prop.group not in ["brown","dark blue"] else 1),2)
#         two =  round((propEvaluation/setSize)*(2 if prop.group not in ["brown","dark blue"] else 6),2)
#         three =  round((propEvaluation/setSize)*(6 if prop.group not in ["brown","dark blue"] else 0),2)
#         print(f'{prop.name:21}| {one:5} | {two:5} | {three:5}')

#     tPropEvaluation += propEvaluation

# print(tPropEvaluation)

# for x in game.monopoly_board:
#     if type(x) == Property:
#         for y in x.neighbors:
#             print(y.name+",", end='')
#         print("")

# y = False
# for x in game.monopoly_board:
#     if type(x) == Property and y:
#         x.owner = a
#         y = False
#     else:
#         x.owner = b
#         y = True

# game.isSets()
# print(game.totalShares(b))

# for x in game.monopoly_board:
#     if type(x) == Property:
#         print(x.name + ": " + str(x.groupShare) + " "+  x.owner.name )

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

# {'Bop': 56, 'Alex': 12, None: 5, 'Alice': 13, 'Said': 14}
# {'Said': 26, 'Bop': 46, 'Alex': 11, 'Alice': 17}
# {'Bop': 45, 'Alice': 17, 'Said': 16, 'Alex': 22}
# {'Said': 36, 'Bop': 15, 'Alice': 37, 'Alex': 12}
# {'Alice': 31, 'Said': 36, 'Bop': 18, 'Alex': 15}
# {'Alex': 66, 'Alice': 191, 'Said': 174, 'Bop': 69}
# ({'Said': 32, 'Bop': 22, 'Alice': 22, 'Alex': 24}, 47.46)
# ({'Alex': 22, 'Alice': 21, 'Said': 34, 'Bop': 23}, 57.5)


# s1 = Strategy(3, 0, 0.5, 0, 500, 2000, 5, 200, 200) 40%
# s2 = Strategy(8, 0, 0.5, 0, 500, 2000, 1, 200, 200) 60%