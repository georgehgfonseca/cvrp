from cvrp import CVRP
import util
import random
import ls_metaheuristics
import pop_metaheuristics
import model as m
import sys
import local_search as ls
from params import Params


def main(args):
    params = Params(args)         # read command line parameters
    d, dem, cap, coord = util.read_cvrp(params.instance)
    cvrp = CVRP(d, dem, cap, coord)
    if params.seed:
        random.seed(params.seed)  # change/remove to allow new random behavior (and solutions)
    if params.time_limit is None:
        params.time_limit = 2 * len(d)
        print("Unspecified run time limit set to (twice the num. cities)", params.time_limit, "\n")
    if params.initial_soln:
        soln = util.read_soln(params.initial_soln, cvrp)
    else:
        # build initial solution
        if params.constructive == "PARTGREEDY":
            soln, t = cvrp.part_greedy_build(params.alpha)
        elif params.constructive == "GREEDY":
            soln, t = cvrp.greedy_build()
        elif params.constructive == "SAVINGS":
            soln, t = cvrp.greedy_build_savings()
    print("Initial solution of cost: ", round(soln.fs, 2))
    print(soln.s)
    print(soln.cap)
    print(soln.obj_eval(cvrp))
    print()

    # run selected algorithm
    print("Running", params.algorithm)
    if params.algorithm == "GRASP":
        soln, t, data = ls_metaheuristics.grasp(cvrp, soln, params)
    elif params.algorithm == "TS":
        soln, t, data = ls_metaheuristics.tabu_search(cvrp, soln, params)
    elif params.algorithm == "SA":
        soln, t, data = ls_metaheuristics.simulated_annealing(cvrp, soln, params)
    elif params.algorithm == "VNS":
        soln, t, data = ls_metaheuristics.vns(cvrp, soln, params)
    elif params.algorithm == "ILS":
        soln, t, data = ls_metaheuristics.ils(cvrp, soln, params)
    elif params.algorithm == "GA":
        soln, t, data = pop_metaheuristics.genetic_algorithm(cvrp, soln, params)
    elif params.algorithm == "FIXOPT":
        model = m.CVRPModel(cvrp, params, soln)
        soln, t, data = model.fix_opt()
    elif params.algorithm == "MIP":
        model = m.CVRPModel(cvrp, params, soln)
        soln, t, data = model.solve_model()

    # write outputs (if allowed)
    if params.chart:
        util.plot_chart(data, f'output/{params.instance} {params.algorithm} {params.seed}.png', f'{params.algorithm} convergence chart', params.lb)
    if params.output:
        util.plot_sol(soln.s, cvrp.coord, f'output/{params.instance} {params.algorithm} {params.seed}.html', title=f'{params.instance} {params.algorithm} {params.seed} Cost `{round(soln.fs, 2)}')
    if params.output_soln:
        util.write_soln(params.output_soln)

    # needed to iRace
    print(round(soln.fs, 2), end="")


if __name__ == "__main__":
    main(sys.argv)


# old code for baby-steps lecturing, just ignore it!
# ==================================== lecture test problem data and solution ==========================================
# dataset = "test_6_nodes"
# d = [[0, 9, 1, 4, 9, 1],
#      [9, 0, 5, 9, 7, 8],
#      [1, 5, 0, 3, 8, 6],
#      [4, 9, 3, 0, 2, 6],
#      [9, 7, 8, 2, 0, 2],
#      [1, 8, 6, 6, 2, 0]]
#
# s_ini = [0, 2, 3, 4, 5, 1, 0]
# fs_ini = 25