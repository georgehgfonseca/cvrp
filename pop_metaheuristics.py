import local_search as ls
import time
import random
import math
from solution import Solution


def mutation_swap(cvrp, individual, mutation_rate):
    if random.random() <= mutation_rate:
        N = ls.get_random_neighbor(cvrp, individual)
        individual.move_to_neighbor(N, cvrp)


def crossover_ox(cvrp, parent_one, parent_two):
    parent_one = parent_one.s
    parent_two = parent_two.s
    # create a giant tours
    parent_one_tour = []
    parent_two_tour = []
    for r in range(len(parent_one)):
        for i in range(1, len(parent_one[r]) - 1):
            parent_one_tour.append(parent_one[r][i])
    for r in range(len(parent_two)):
        for i in range(1, len(parent_two[r]) - 1):
            parent_two_tour.append(parent_two[r][i])

    # print(parent_one_tour, parent_two_tour)
    # two cut points
    cut = random.sample(range(1, len(parent_one_tour) - 1), 2)
    cut.sort()

    # create empty children
    child_one = [0] * len(parent_one_tour)
    child_two = [0] * len(parent_two_tour)

    # copy sequence between cut[0] and cut [1] from parent one to child one
    c1, c2 = cut[0], cut[1] + 1
    child_one[c1:c2] = parent_one_tour[c1:c2]
    # The same for second child with parent two
    child_two[c1:c2] = parent_two_tour[c1:c2]

    # Starting from c2 until check all elements from parent two, insert on child one.
    visit_order_p2 = parent_two_tour[c2:len(parent_two_tour)] + parent_two_tour[0:c2]
    # Position to insert on child one - starting from c2
    position = c2
    for customer in visit_order_p2:
        # If customer does not exist in child one:
        if customer not in child_one:
            child_one[position] = customer
            position += 1

            if position == len(child_one):
                position = 0

    # The same process for the child two
    # This code will be rewrite as a function
    visit_order_p1 = parent_one_tour[c2:len(parent_one_tour)] + parent_one_tour[0:c2]
    # Position to insert on child one - starting from c2
    position = c2
    # print(f"Starting from: {position}")
    # print(visit_order_p1)

    for customer in visit_order_p1:
        # If customer does not exist in child one:
        if customer not in child_two:
            # print(position)
            child_two[position] = customer
            position += 1

            if position == len(child_two):
                position = 0

    # print(child_one, child_two)

    # split (into routes) child individuals
    child_one_cap = [0]
    child_one_fs = 0
    child_one_split = [[0]]
    for n in child_one:
        if child_one_cap[-1] + cvrp.dem[n] <= cvrp.cap:
            child_one_split[-1].append(n)
            child_one_cap[-1] += cvrp.dem[n]
            child_one_fs += cvrp.d[child_one_split[-1][-2]][child_one_split[-1][-1]]
        else:
            # close and start a new route
            child_one_split[-1].append(0)
            child_one_fs += cvrp.d[child_one_split[-1][-2]][child_one_split[-1][-1]]
            child_one_split.append([0])
            child_one_split[-1].append(n)
            child_one_fs += cvrp.d[child_one_split[-1][-2]][child_one_split[-1][-1]]
            child_one_cap.append(cvrp.dem[n])
    # close last route
    child_one_split[-1].append(0)
    child_one_fs += cvrp.d[child_one_split[-1][-2]][child_one_split[-1][-1]]

    child_two_cap = [0]
    child_two_fs = 0
    child_two_split = [[0]]
    for n in child_two:
        if child_two_cap[-1] + cvrp.dem[n] <= cvrp.cap:
            child_two_split[-1].append(n)
            child_two_cap[-1] += cvrp.dem[n]
            child_two_fs += cvrp.d[child_two_split[-1][-2]][child_two_split[-1][-1]]
        else:
            # close and start a new route
            child_two_split[-1].append(0)
            child_two_fs += cvrp.d[child_two_split[-1][-2]][child_two_split[-1][-1]]
            child_two_split.append([0])
            child_two_split[-1].append(n)
            child_two_fs += cvrp.d[child_two_split[-1][-2]][child_two_split[-1][-1]]
            child_two_cap.append(cvrp.dem[n])
    # close last route
    child_two_split[-1].append(0)
    child_two_fs += cvrp.d[child_two_split[-1][-2]][child_two_split[-1][-1]]

    child_one_split = Solution(child_one_split, child_one_fs, child_one_cap)
    child_two_split = Solution(child_two_split, child_two_fs, child_two_cap)

    return child_one_split, child_two_split


def roulette_wheel_selection(population, nind_to_select):

    index_individuals = []

    ind = 0

    while ind < nind_to_select:
        prob = random.random()

        # Select distinct indexes
        for i in range(len(population)):
            if prob <= population[i].probability and i not in index_individuals:
                index_individuals.append(i)
                ind += 1
                break

    return index_individuals


def linear_ranking(population, sp):

    nind = len(population)
    population.sort(reverse = True, key = lambda i: i.fs)

    # Calculate fitness
    for i in range(1, nind + 1):
        population[i - 1].fitness = 2 - sp + 2 * (sp - 1) * \
                                    (( i - 1 ) / (nind - 1))

    min_value = population[0].fitness
    max_value = population[len(population) - 1].fitness

    # Normalize values - probabilities [0, 1]
    # Scaling: x' = [x - min()] / [ max() - min() ]
    for i in range(0, nind):
        population[i].probability = (population[i].fitness - min_value) / ( max_value - min_value )


def genetic_algorithm(cvrp, soln, params):
    # fitness - linear ranking
    selective_pressure = 1.1
    t_init = time.time()
    chart_data = []

    population = []
    ind_star = Solution(None, float("inf"), None)

    individual, t = cvrp.greedy_build()
    population.append(individual)

    # generate initial population through partially greedy build method
    for _ in range(params.ga_pop_size - len(population)):
        individual, t = cvrp.part_greedy_build(params.alpha)
        # individual, _ = ls.local_search(cvrp, individual, params)
        population.append(individual)

    # sort population using objective cost of linear ranking
    # population.sort(reverse = True, key = lambda i: i.fs)
    linear_ranking(population, selective_pressure)

    index_best = len(population) - 1 # It is the last
    ind_star = population[index_best].copy()

    for it in range(1, params.ga_generation_max + 1):
        # imposing a time limit
        if time.time() - t_init >= params.time_limit:
            break

        descendants = []

        # for each individual
        for _ in range(params.ga_pop_size):
            if random.random() <= params.ga_crossover_rate:
                # select parents
                [pi, pj] = roulette_wheel_selection(population, 2)

                # perform crossover
                child_one, child_two = crossover_ox(cvrp, population[pi], population[pj])

                # perform mutation
                mutation_swap(cvrp, child_one, params.ga_mutation_rate)
                mutation_swap(cvrp, child_two, params.ga_mutation_rate)

                # perform local search
                fs = child_one.obj_eval(cvrp)
                child_one.fs = fs
                if random.random() < params.ga_local_search_rate:
                    child_one, _ = ls.local_search(cvrp, child_one, params)

                fs = child_two.obj_eval(cvrp)
                child_two.fs = fs
                if random.random() < params.ga_local_search_rate:
                    child_two, _ = ls.local_search(cvrp, child_two, params)

                # add children to descendants population
                descendants.append(child_one)
                descendants.append(child_two)

        # merge: current population and descendants
        merge = population + descendants

        # evaluate and rank population
        linear_ranking(merge, selective_pressure)

        # select the survivors
        survivors = roulette_wheel_selection(merge, params.ga_pop_size)

        # update population for the next generation
        population = []

        # elitism
        last = len(merge) - 1
        population.append(merge[last].copy())

        for index in survivors:
            population.append(merge[index].copy())
            if len(population) == params.ga_pop_size:
                break

        linear_ranking(population, selective_pressure)

        index_best = len(population) - 1 # it is the last individual
        chart_data.append([time.time() - t_init, population[index_best].fs, ind_star.fs])

        if population[index_best].fs < ind_star.fs + ls.EPS:
            ind_star = population[index_best].copy()

        if params.verbose:
            print(f'| it: {it:6d}  |  s_: {population[index_best].fs:10.2f}  |  s*: {ind_star.fs:10.2f}  |  time: {time.time() - t_init:10.2f} |  pop: ', end="")
            for ind in population:
                print(round(ind.fs, 2), end=" ")
            print()

    return ind_star, time.time() - t_init, chart_data