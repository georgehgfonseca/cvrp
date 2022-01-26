import local_search as ls
import time
import random
import math


def simulated_annealing(cvrp, soln, params):
    """Simulated Annealing https://www.science.org/doi/10.1126/science.220.4598.671"""
    t_init = time.time()
    chart_data = []
    soln_star = soln.copy()
    while time.time() - t_init < params.time_limit:
        iter_t = 0    # iterations at temperature t
        t = params.sa_t_0       # current temperature
        soln = soln_star.copy()
        while t > 0.001:
            if params.verbose:
                print(f'| temp: {t:10.3f}  |  s: {soln.fs:10.3f}  |  s*: {soln_star.fs:10.3f}  |  time: {time.time() - t_init:10.2f} |')
            while iter_t < params.sa_max * len(cvrp.d):
                iter_t += 1
                N = ls.get_random_neighbor(cvrp, soln)
                delta = N[0][0] - soln.fs
                if delta < 0:
                    soln.move_to_neighbor(N[0], cvrp)
                    if soln.fs < soln_star.fs:
                        soln_star = soln.copy()
                else:
                    x = random.random()  # generates a random float number between 0 and 1
                    if x < math.exp(-delta/t):  # move to a worsening neighbor
                        soln.move_to_neighbor(N[0], cvrp)
            chart_data.append([time.time() - t_init, soln.fs, soln_star.fs])
            t = params.sa_alpha * t
            iter_t = 0
    return soln_star, time.time() - t_init, chart_data


def set_initial_temperature_simulation(d, s, fs, sa_max, t_0=100, beta=1.15, gama=0.90):
    """Defines initial temperature by simulation"""
    t = t_0       # current temperature
    flag = True
    while flag:
        accepted = 0
        for iter_t in range(sa_max):
            N = ls.get_random_neighbor(d, fs, s)
            delta = N[0][0] - fs
            if delta < 0:
                accepted += 1
            else:
                x = random.random()
                if x < math.exp(-delta/t):
                    accepted += 1
        if accepted >= gama * sa_max:
            flag = False
        else:
            t = beta * t
    return t


def set_initial_temperature_sampling(d, s, fs, n_neighbors=100):
    """Defines initial temperature by sampling"""
    t = 0
    for i in range(n_neighbors):
        N = ls.get_random_neighbor(d, fs, s)
        delta = fs - N[0][0]
        if math.fabs(delta) > t:
            t = math.fabs(delta)
    return t


def ils(cvrp, soln, params):
    """Iterated Local Search https://doi.org/10.1007/BF01096763"""
    t_init = time.time()
    chart_data = []
    chart_data.append([time.time() - t_init, soln.fs, soln.fs])
    soln, t = ls.local_search(cvrp, soln, params)
    chart_data.append([time.time() - t_init, soln.fs, soln.fs])
    it = 0
    while time.time() - t_init < params.time_limit:
        it += 1
        soln_ = soln.copy()
        # perturbation
        for _ in range(params.ils_p_level):  # perturbation: apply p_level inter-route best swap random moves to s_
            N = ls.get_inter_best_swap_random_neighbor(cvrp, soln_)
            soln_.inter_best_swap_move(cvrp, N[0][1], N[0][2], N[0][3], N[0][4])
        chart_data.append([time.time() - t_init, soln_.fs, soln.fs])
        # local search
        soln__, t = ls.local_search(cvrp, soln_, params)
        # acceptance condition
        if soln__.fs < soln.fs:
            soln = soln__.copy()
        if params.verbose:
            print(f'| it: {it:6d}  |  s_: {soln_.fs:10.2f}  |  s__: {soln__.fs:10.2f}  |  s*: {soln.fs:10.2f}  |  time: {time.time() - t_init:10.2f} |')
        chart_data.append([time.time() - t_init, soln__.fs, soln.fs])
    return soln, time.time() - t_init, chart_data


def vns(cvrp, soln, params):
    """Variable Neighborhood Search (uses 1st improvement VND local search) https://doi.org/10.1007/BF01096763"""
    t_init = time.time()
    chart_data = []
    it = 0
    while time.time() - t_init < params.time_limit:
        it += 1
        k = 1
        while k <= params.vns_k_max:
            soln_ = soln.copy()
            if k == 1:  # move to random 2-opt neighbor
                for _ in range(params.vns_p_level):  # perturbation: apply p_level 2-opt random moves to s_
                    N = ls.get_two_opt_random_neighbor(cvrp, soln)
                    soln_.two_opt_move(cvrp, N[0][1], N[0][2], N[0][3])
            elif k == 2:  # move to random inter-route best swap neighbor
                for _ in range(params.vns_p_level):  # perturbation: apply p_level inter-route swap random moves to s_
                    N = ls.get_inter_best_swap_random_neighbor(cvrp, soln)
                    soln_.inter_best_swap_move(cvrp, N[0][1], N[0][2], N[0][3], N[0][4])
            chart_data.append([time.time() - t_init, soln_.fs, soln.fs])
            # local search
            soln__, t = ls.local_search(cvrp, soln_, params)
            if soln__.fs + ls.EPS < soln.fs:
                soln = soln__.copy()
                k = 1
            else:
                k = k + 1
            if params.verbose:
                print(f'| it: {it:6d}  |  k: {k:3d}  |  s_: {soln_.fs:10.2f}  |  s__: {soln__.fs:10.2f}  |  s*: {soln.fs:10.2f}  |  time: {time.time() - t_init:10.2f} |')
            chart_data.append([time.time() - t_init, soln__.fs, soln.fs])
    return soln, time.time() - t_init, chart_data


def tabu_search(cvrp, soln, params):
    """Tabu Search https://link.springer.com/chapter/10.1007/978-1-4613-0303-9_33"""
    t_init = time.time()
    chart_data = []
    soln_star = soln.copy()
    T = []  # tabu list
    it = 0
    while time.time() - t_init < params.time_limit:
        it += 1
        soln, m = tabu_neighbor(cvrp, soln, soln_star.fs, T)
        T.append(m)
        if len(T) > params.tabu_max:
            T.pop(0)
        if soln.fs < soln_star.fs:
            soln_star = soln.copy()
        if params.verbose:
            print(f'| it: {it:6d}  |  s: {soln.fs:10.2f}  |  s*: {soln_star.fs:10.2f}  |  time: {time.time() - t_init:10.2f} |')
        chart_data.append([time.time() - t_init, soln.fs, soln_star.fs])
    return soln_star, time.time() - t_init, chart_data


def tabu_neighbor(cvrp, soln, fs_star, T):
    """Move to the best non Tabu neighbor"""
    V = []
    best_fs = float("inf")
    # 2-opt neighbors
    for r in range(len(soln.s)):
        for i in range(1, len(soln.s[r]) - 1):
            for j in range(i + 1, len(soln.s[r]) - 1):
                m = (r, i, j)
                fs_ = soln.two_opt_eval(cvrp, r, i, j)
                if fs_ < best_fs and (m not in T or fs_ < fs_star):
                    best_fs = fs_
                    V.append([fs_, r, i, j])
    # inter-route best swap neighbors
    for r1 in range(len(soln.s)):
        for i in range(1, len(soln.s[r1]) - 1):
            for r2 in range(r1 + 1, len(soln.s)):
                for j in range(1, len(soln.s[r2]) - 1):
                    m = (r1, r2, i, j)
                    fs_ = soln.inter_best_swap_eval(cvrp, r1, r2, i, j)
                    if fs_ < best_fs and (m not in T or fs_ < fs_star):
                        best_fs = fs_
                        V.append([fs_, r1, r2, i, j])
    if V:
        if len(V[-1]) == 4:  # move to 2-opt best neighbor
            r, i, j = V[-1][1], V[-1][2], V[-1][3]
            m = (r, i, j)
            soln.two_opt_move(cvrp, r, i, j)
        elif len(V[-1]) == 5:  # move to inter-route best swap best neighbor
            r1, r2, i, j = V[-1][1], V[-1][2], V[-1][3], V[-1][4]
            m = (r1, r2, i, j)
            soln.inter_best_swap_move(cvrp, r1, r2, i, j)
    return soln, m


def grasp(cvrp, soln, params):
    """Greedy Randomized Adaptive Search Procedure https://doi.org/10.1007/BF01096763"""
    t_init = time.time()
    soln_star = soln.copy()
    it = 0
    chart_data = []
    while time.time() - t_init < params.time_limit:
        it += 1
        soln, t = cvrp.part_greedy_build(params.grasp_alpha)
        if soln.fs < soln_star.fs:
            fs_star = soln.fs
        chart_data.append([time.time() - t_init, soln.fs, soln_star.fs])
        soln_ = soln.copy()
        soln__, t = ls.local_search(cvrp, soln_, params)
        if params.verbose:
            print(f'| it: {it:6d}  |  s_ini: {soln_.fs:10.2f}  |  s: {soln__.fs:10.2f}  |  s*: {soln_star.fs:10.2f}  |  time: {time.time() - t_init:10.2f} |')
        if soln__.fs < soln_star.fs:
            fs_star = soln__.fs
            soln_star = soln__.copy()
        chart_data.append([time.time() - t_init, soln__.fs, soln_star.fs])

    return soln_star, time.time() - t_init, chart_data
