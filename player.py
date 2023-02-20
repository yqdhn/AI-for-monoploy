import random

class Player:
    def __init__(self, name, buildTechnique, cashLimit):
        self.name = name
        self.position = 0
        self.money = 1500  # start 1500
        self.buildTechnique = buildTechnique
        self.cashLimit = cashLimit
        self.toBuild = []
        self.wanted = {}
        self.inJail = False
        self.roundsInJail = 0
        self.dicesDoubleCount = 0
        self.alive = True

    # money management
    # get paid
    def moneyIn(self, amount):
        print(str(amount) + " added to " + self.name)
        self.money += amount
        print(self.name + " money become " + str(self.money))

    # pay someone or buy
    def moneyOut(self, amount, board):
        print(self.name + " money was " + str(self.money))
        money_taken = 0
        self.bankruptPlayer(amount, board)
        if self.money >= amount:
            self.money -= amount
            money_taken = amount
        else:
            money_taken = self.money
            self.money -= money_taken
        
        print("become " + str(self.money) + " paid " + str(money_taken))
        return money_taken

    # positions
    def moveTo(self, position):
        self.position = position

    def makeAMove(self, board):

        playAgain = False

        if not self.alive:
            return False

        board.recalculateChanges()

        while self.unMortgage(board):
            board.recalculateAfterPropertyChange()

        while board.build(self, self.money - self.cashLimit):
            pass

        dice1 = random.randint(1, 6)
        dice2 = random.randint(1, 6)

        if not self.inJail and dice1 == dice2:
            playAgain = True
            self.dicesDoubleCount += 1
            # go to jail if 3 dices doubles
            if self.dicesDoubleCount == 3:
                self.inJail = True
                playAgain = False
                self.moveTo(10)
                self.dicesDoubleCount = 0
                print(f'{self.name} went to jail after 3 doubles')
                return False
        else:
            self.dicesDoubleCount = 0

        if self.inJail:
            if dice1 != dice2:
                self.roundsInJail += 1
                if self.roundsInJail > 3:
                    print(f'{self.name} get out of jail after 3 rounds')
                    pass
                elif self.money >= 50:
                    jailFine = self.moneyOut(50, board)
                    print(f'{self.name} pays {jailFine} to get out of jail')
                    self.roundsInJail = 0
                else:
                    return False
            else:
                playAgain = False
        self.roundsInJail = 0
        self.inJail = False

        # move the piece
        print(f'{self.name} position is {self.position} and dices total is {dice1+dice2}')
        self.position += dice1+dice2
        # calculate correct cell
        # and get salary for passing GO (200)
        if self.position >= 40:
            self.position = self.position - 40
            self.moneyIn(200)

        print(f'{self.name} new position is {board.monopoly_board[self.position].name}({self.position})')
        board.action(self, self.position)

        if playAgain:
            print(f'{self.name} plays again {dice1}={dice2}')
            self.makeAMove(board)
    
    # take an action if player doesn't have money
    def bankruptPlayer(self, amount, board):
        while self.money - amount < 0:
            propertyToMortgage = None
            for prop in board.monopoly_board:
                if prop.type in ["property", "util", "station"] and prop.owner == self and not prop.isMortgaged:
                    if propertyToMortgage == None:
                        propertyToMortgage = prop
                    elif propertyToMortgage.valueToOwner > prop.valueToOwner:
                        propertyToMortgage = prop
            
            if propertyToMortgage == None: #there is no property To Mortgage
                self.alive = False
                board.sellAll(self)
                print(f'{self.name} is out no (money to pay rent)')
                return
            if propertyToMortgage.houses > 0:
                self.moneyIn(int(propertyToMortgage.house_price/2))
                propertyToMortgage.houses -= 1
                print(f'{self.name} sold one house from {propertyToMortgage.name}')
            else:
                houseSold = False
                if propertyToMortgage.type == "property" and propertyToMortgage.isFullSet:
                    houseSold = False
                    for prop in board.monopoly_board:
                        if prop.type == "property" and prop.group == propertyToMortgage.group:
                            if prop.houses > 0 and prop != propertyToMortgage:
                                self.moneyIn(int(propertyToMortgage.house_price/2))
                                prop.houses -= 1
                                print(f'{self.name} sold one house from {propertyToMortgage.name} group')
                                houseSold = True
                                break
                if not houseSold: 
                    propertyToMortgage.isMortgaged = True
                    self.moneyIn(int(propertyToMortgage.price/2))
                    print(f'{self.name} mortgage {propertyToMortgage.name}')
            
            board.recalculateChanges()

    def unMortgage(self, board):
        propertyToUnMortgage = None
        for prop in board.monopoly_board:
            if prop.type in ["property", "util", "station"] and prop.owner == self and prop.isMortgaged and prop.price/2 <= self.money:
                if propertyToUnMortgage == None:
                    propertyToUnMortgage = prop
                elif propertyToUnMortgage.valueToOwner < prop.valueToOwner:
                    propertyToUnMortgage = prop

        if propertyToUnMortgage != None:
            propertyToUnMortgage.isMortgaged = False
            self.moneyOut(int(propertyToUnMortgage.price/2), board)
            print(f'{self.name} UnMortgage {propertyToUnMortgage.name}')





    # def tradeProperty(self, board):