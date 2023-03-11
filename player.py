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
    
    check ability to build
    return average number of houses can build according to money have
    def financialStatus(self, player, property):
        numberOfHousesCanBuild = (player.money - player.cashLimit) / property.house_price
        average =  min(numberOfHousesCanBuild / (2 if  property.group in ["dark blue", "brown"] else 3), 5)
        return average


    def propertyEvaluation(self, player, property):
        share = self.propertyShareInGroup(property.group, player) * 10 # just scaling (to be out of 10)
        rentReturn = property.rent_price[0] / property.price
        probabilityOfLanding = 0 ########### to do next
        rentAmount = self.calculateRent(property) / 2000 * 10

    	# check rent return according to the financial status
        # financial = self.financialStatus(player, property)
        # idx = int(financial)
        # rentFinancial = 0
        # if financial < 5:
        #     rentFinancial = (rentReturn[idx] * (idx + 1 - financial)) + (rentReturn[idx + 1] * (financial - idx))
        # else:
        #     rentFinancial = rentReturn[idx]
        # rentFinancial = rentFinancial * 10/1.622 # just scaling (to be out of 10)

        value = round(share  + probabilityOfLanding + rentAmount, 3)
        return value

    def wantedProperties(self, player):
        for prop in self.monopoly_board:
            if prop.type == "property" and prop.owner != player and prop.owner != "" and prop.houses == 0:
                player.wanted[prop] = self.propertyEvaluation(player, prop)


    The value of all properties the player own (add in the board)
    def valuePlayersProperties(self, player):
        for prop in self.monopoly_board:
            if prop.type == "property" and prop.owner == player:
                prop.valueToOwner = self.propertyEvaluation(player, prop)
            elif prop.type in ["util", "station"]:
                prop.valueToOwner == 1.




    ## check the if the set have houses (can't mortgage property in a set that have houses)
    houseSold = False
    if propertyToMortgage.type == "property" and propertyToMortgage.isFullSet:
        houseSold = False
        for prop in state.board.monopoly_board:
            if prop.type == "property" and prop.group == propertyToMortgage.group:
                if prop.houses > 0 and prop != propertyToMortgage:
                    self.moneyIn(int(propertyToMortgage.house_price/2))
                    prop.houses -= 1
                    game_output(f'{self.name} sold one house from {propertyToMortgage.name} group')
                    houseSold = True
                    break
    ## can't find houses in the set, mortgage the property