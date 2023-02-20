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
    def moneyOut(self, amount):
        print(self.name + " money was " + str(self.money))
        money_taken = 0
        if amount <= self.money:
            self.money -= amount
            money_taken = amount
        else:
            money_taken = self.money
            self.money -= self.money
            self.alive = False ## does not have enough money
        
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
                    jailFine = self.moneyOut(50)
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
    def bankruptPlayer(self, board, amount):
        while self.money - amount < 0:
            tomorgent



    # def tradeProperty(self, board):