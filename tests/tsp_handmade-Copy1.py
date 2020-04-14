import numpy as np
import random
import math
import operator
import re
import pandas as pd
import matplotlib.pyplot as plt
from numba import jit


# TSPLIB file reader

def read_tsplib_file(filename):
    if filename is None:
        raise FileNotFoundError('Filename can not be None')
    with open(filename) as file:
        lines = file.readlines()
        data = [line.lstrip() for line in lines if line != ""]
        dimension = re.compile(r'[^\d]+')
        for item in data:
            if item.startswith('DIMENSION'):
                dimension = int(dimension.sub('', item))
                break
        c = [-1.0] * (2 * dimension)
        cities_coord = []
        for item in data:
            if item[0].isdigit():
                j, coordX, coordY = [float(x.strip()) for x in item.split(' ')]
                c[2 * (int(j) - 1)] = coordX
                c[2 * (int(j) - 1) + 1] = coordY
                cities_coord.append([coordX, coordY])
        cities = pd.DataFrame(cities_coord)
        #         cities = cities_coord
        matrix = [[-1] * dimension for _ in range(dimension)]
        for k in range(dimension):
            matrix[k][k] = 0
            for j in range(k + 1, dimension):
                dist = math.sqrt((c[k * 2] - c[j * 2]) ** 2 + (c[k * 2 + 1] - c[j * 2 + 1]) ** 2)
                dist = round(dist)
                matrix[k][j] = dist
                matrix[j][k] = dist
        return matrix, dimension, cities


# class City:
#     def __init__(self, x, y):
#         self.x = x
#         self.y = y
#
#     def distance(self, city):
#         xDis = abs(self.x - city.x)
#         yDis = abs(self.y - city.y)
#         distance = np.sqrt((xDis ** 2) + (yDis ** 2))
#         return distance
#
#     def __repr__(self):
#         return "(" + str(self.x) + "," + str(self.y) + ")"


# class Fitness:
#     def __init__(self, route):
#         self.route = route
#         self.distance = 0
#         self.fitness= 0.0
#
#     def routeDistance(self):
#         if self.distance ==0:
#             pathDistance = 0
#             for i in range(0, len(self.route)):
#                 fromCity = self.route[i]
#                 toCity = None
#                 if i + 1 < len(self.route):
#                     toCity = self.route[i + 1]
#                 else:
#                     toCity = self.route[0]
#                 pathDistance += fromCity.distance(toCity)
#             self.distance = pathDistance
#         return self.distance
#
#     def routeFitness(self):
#         if self.fitness == 0:
#             self.fitness = 1 / float(self.routeDistance())
#         return self.fitness


# mod


def routeFitness(pop):
    fitness = 0
    for i in range(len(pop) - 1):
        x = pop[i]
        y = pop[i + 1]
        fitness += dist_matrix[x][y]
    first_city, last_city = pop[0], pop[-1]
    fitness += dist_matrix[first_city][last_city]
    return fitness

@jit(nopython=True)
def createRoute(cityList):
    route = np.random.permutation(cityList)
    return route

@jit(nopython=True)
def initialPopulation(popSize, cityList):
    population = []
    for i in range(0, popSize):
        population.append(createRoute(cityList))  # create route ?
    return population


def rankRoutes(population):
    fitnessResults = {}
    for i in range(len(population)):
        # fitnessResults[i] = Fitness(population[i]).routeFitness()
        fitnessResults[i] = routeFitness(population[i])
    return sorted(fitnessResults.items(), key=operator.itemgetter(1), reverse=False)


def selection(popRanked, eliteSize):
    selectionResults = []
    df = pd.DataFrame(np.array(popRanked), columns=["Index", "Fitness"])
    df['cum_sum'] = df.Fitness.cumsum()
    df['cum_perc'] = 100 * df.cum_sum / df.Fitness.sum()

    for i in range(0, eliteSize):
        selectionResults.append(popRanked[i][0])
    for i in range(0, len(popRanked) - eliteSize):
        pick = 100 * random.random()
        for i in range(0, len(popRanked)):
            if pick <= df.iat[i, 3]:
                selectionResults.append(popRanked[i][0])
                break
    return selectionResults


def matingPool(population, selectionResults):
    matingpool = []
    for i in range(0, len(selectionResults)):
        index = selectionResults[i]
        matingpool.append(population[index])
    return matingpool

@jit(nopython=True)
def breed(parent1, parent2):
    child = []
    childP1 = []
    childP2 = []

    geneA = int(random.random() * len(parent1))
    geneB = int(random.random() * len(parent1))

    startGene = min(geneA, geneB)
    endGene = max(geneA, geneB)

    for i in range(startGene, endGene):
        childP1.append(parent1[i])

    childP2 = [item for item in parent2 if item not in childP1]

    child = childP1 + childP2
    return child


def breedPopulation(matingpool, eliteSize):
    children = []
    length = len(matingpool) - eliteSize
    pool = random.sample(matingpool, len(matingpool))

    for i in range(0, eliteSize):
        children.append(matingpool[i])

    for i in range(0, length):
        child = breed(pool[i], pool[len(matingpool) - i - 1])
        children.append(child)
    return children


def mutate(individual, mutationRate):
    for swapped in range(len(individual)):
        if (random.random() < mutationRate):
            swapWith = int(random.random() * len(individual))

            city1 = individual[swapped]
            city2 = individual[swapWith]

            individual[swapped] = city2
            individual[swapWith] = city1
    return individual


def mutatePopulation(population, mutationRate):
    mutatedPop = []

    for ind in range(0, len(population)):
        mutatedInd = mutate(population[ind], mutationRate)
        mutatedPop.append(mutatedInd)
    return mutatedPop


def nextGeneration(currentGen, eliteSize, mutationRate):
    popRanked = rankRoutes(currentGen)
    selectionResults = selection(popRanked, eliteSize)  # todo here: check how seelction works
    matingpool = matingPool(currentGen, selectionResults)
    children = breedPopulation(matingpool, eliteSize)
    nextGeneration = mutatePopulation(children, mutationRate)
    return nextGeneration


def geneticAlgorithm(population, popSize, eliteSize, mutationRate, generations):
    pop = initialPopulation(popSize, population)  # ongoing
    print("Initial distance: " + str(rankRoutes(pop)[0][1]))

    for i in range(0, generations):
        pop = nextGeneration(pop, eliteSize, mutationRate)

    print("Final distance: " + str(rankRoutes(pop)[0][1]))
    bestRouteIndex = rankRoutes(pop)[0][0]
    bestRoute = pop[bestRouteIndex]
    return bestRoute


# instantiate problem to solve
problem_name = 'Qatar 194 TSP'
optimal_fitness = 9352
dist_matrix, nb_cities, cities_coord = read_tsplib_file('./dj38.tsp')
cityList = cities_coord.index.values

geneticAlgorithm(population=cityList, popSize=100, eliteSize=20, mutationRate=0.01, generations=50)
