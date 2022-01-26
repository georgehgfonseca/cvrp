import random
import time

EPS = 0.0001  # to avoid numerical issues when comparing float values
MAX_K = 2  # number of neighborhood structures


# =================================== Getting same route 2-opt neighbors ===============================================
def get_two_opt_neighbors(cvrp, soln):
    """Get all neighbors regarding same route 2-opt neighborhood. A neighbor represented as: [fs, r, i, j]"""
    N = []
    for r in range(len(soln.s)):
        for i in range(1, len(soln.s[r]) - 1):
            for j in range(i + 1, len(soln.s[r]) - 1):
                fs_ = soln.two_opt_eval(cvrp, r, i, j)
                if fs_ + EPS < soln.fs:
                    # add improvement neighbor
                    N.append((fs_, r, i, j))
    return N


def get_two_opt_first_neighbor(cvrp, soln):
    """Get first neighbor regarding same route 2-opt neighborhood. A neighbor represented as: [fs, r, i, j]"""
    N = []
    for r in range(len(soln.s)):
        for i in range(1, len(soln.s[r]) - 1):
            for j in range(i + 1, len(soln.s[r]) - 1):
                fs_ = soln.two_opt_eval(cvrp, r, i, j)
                if fs_ + EPS < soln.fs:
                    # return improvement neighbor
                    N.append((fs_, r, i, j))
                    return N
    return N


def get_two_opt_random_neighbor(cvrp, soln):
    """Get a random same route 2-opt neighbor represented as: [fs, r, i, j]"""
    N = []
    r = random.choice(range(len(soln.s)))
    i = random.choice(range(1, len(soln.s[r]) - 1))
    j = random.choice(range(1, len(soln.s[r]) - 1))
    while i == j:  # ensure different values for i and j
        r = random.choice(range(len(soln.s)))
        i = random.choice(range(1, len(soln.s[r]) - 1))
        j = random.choice(range(1, len(soln.s[r]) - 1))
    if i > j:  # ensure i and j are ordered
        i, j = j, i
    fs_ = soln.two_opt_eval(cvrp, r, i, j)
    N.append((fs_, r, i, j))
    return N


# =================================== Getting inter-route swap neighbors ===============================================
def get_inter_best_swap_neighbors(cvrp, soln):
    """Get all neighbors regarding inter-route swap neighborhood. A neighbor represented as: [fs, r1, r2, i, j]"""
    N = []
    for r1 in range(len(soln.s)):
        for i in range(1, len(soln.s[r1]) - 1):
            for r2 in range(r1 + 1, len(soln.s)):
                for j in range(1, len(soln.s[r2]) - 1):
                    fs_ = soln.inter_best_swap_eval(cvrp, r1, r2, i, j)
                    if fs_ + EPS < soln.fs:
                        # add improvement neighbor
                        N.append((fs_, r1, r2, i, j))
    return N


def get_inter_best_swap_first_neighbor(cvrp, soln):
    """Get first neighbor regarding inter-route swap neighborhood. A neighbor represented as: [fs, r1, r2, i, j]"""
    N = []
    for r1 in range(len(soln.s)):
        for i in range(1, len(soln.s[r1]) - 1):
            for r2 in range(r1 + 1, len(soln.s)):
                for j in range(1, len(soln.s[r2]) - 1):
                    fs_ = soln.inter_best_swap_eval(cvrp, r1, r2, i, j)
                    if fs_ + EPS < soln.fs:
                        # return improvement neighbor
                        N.append((fs_, r1, r2, i, j))
                        return N
    return N


def get_inter_best_swap_random_neighbor(cvrp, soln):
    """Get a random inter-swap neighbor represented as: [fs, r1, r2, i, j]"""
    N = []
    r1 = random.choice(range(len(soln.s)))
    r2 = random.choice(range(len(soln.s)))
    while r1 == r2:  # ensure different values for r1 and r2
        r2 = random.choice(range(len(soln.s)))
    if r1 > r2:  # ensure r1 and r2 are ordered
        r1, r2 = r2, r1
    i = random.choice(range(1, len(soln.s[r1]) - 1))
    j = random.choice(range(1, len(soln.s[r2]) - 1))
    fs_ = soln.inter_best_swap_eval(cvrp, r1, r2, i, j)
    N.append((fs_, r1, r2, i, j))
    return N


# ================================================ Local search methods ================================================
def descent_two_opt(cvrp, soln):
    """Descent local search method (same route 2-opt) for CVRP"""
    t_init = time.time()
    N = get_two_opt_neighbors(cvrp, soln)
    while N:
        # select best neighbor
        best_n = -1
        min = float("inf")
        for n in N:
            if n[0] < min:
                min = n[0]
                best_n = n
        # move to next neighbor
        soln.two_opt_move(cvrp, best_n[1], best_n[2], best_n[3])
        # print(round(soln.fs, 2))
        N = get_two_opt_neighbors(cvrp, soln)
    return soln, time.time() - t_init


def first_improvement_two_opt(cvrp, soln):
    """First improvement local search method (same route 2-opt) for CVRP"""
    t_init = time.time()
    N = get_two_opt_first_neighbor(cvrp, soln)
    while N:
        # move to next neighbor
        soln.two_opt_move(cvrp, N[0][1], N[0][2], N[0][3])
        # print(round(soln.fs, 2))
        N = get_two_opt_first_neighbor(cvrp, soln)
    return soln, time.time() - t_init


# def first_improvement_three_opt(d, s, fs):
#     """First improvement local search method (3-opt) for TSP"""
#     t_init = time.time()
#     N = get_three_opt_first_neighbor_sample(d, s, fs)
#     while N:
#         # move to next neighbor
#         s, fs = tsp.three_opt_move(d, s, fs, N[0][1], N[0][2], N[0][3])
#         # print(round(s_dist, 2))
#         N = get_three_opt_first_neighbor_sample(d, s, fs)
#     return s, fs, time.time() - t_init


def random_descent_two_opt(cvrp, soln, max_it):
    """Random descent local search method (same route 2-opt) for CVRP"""
    t_init = time.time()
    it = 0
    while it < max_it:
        it += 1
        N = get_two_opt_random_neighbor(cvrp, soln)
        if N[0][0] + EPS < soln.fs:
            it = 0
            # apply and accept move
            soln.two_opt_move(cvrp, N[0][1], N[0][2], N[0][3])
    return soln, time.time() - t_init


def descent_inter_best_swap(cvrp, soln):
    """Descent local search method (inter-route swap) for CVRP"""
    t_init = time.time()
    N = get_inter_best_swap_neighbors(cvrp, soln)
    while N:
        # select best neighbor
        best_n = -1
        min = float("inf")
        for n in N:
            if n[0] < min:
                min = n[0]
                best_n = n
        # move to next neighbor
        soln.inter_best_swap_move(cvrp, best_n[1], best_n[2], best_n[3], best_n[4])
        # print(round(soln.fs, 2))
        N = get_inter_best_swap_neighbors(cvrp, soln)
    return soln, time.time() - t_init


def first_improvement_inter_best_swap(cvrp, soln):
    """First improvement local search method (inter-route swap) for CVRP"""
    t_init = time.time()
    N = get_inter_best_swap_first_neighbor(cvrp, soln)
    while N:
        # move to next neighbor
        soln.inter_best_swap_move(cvrp, N[0][1], N[0][2], N[0][3], N[0][4])
        # print(round(soln.fs, 2))
        N = get_inter_best_swap_first_neighbor(cvrp, soln)
    return soln, time.time() - t_init


def random_descent_inter_best_swap(cvrp, soln, max_it):
    """Random descent local search method (inter-route swap) for CVRP"""
    t_init = time.time()
    it = 0
    while it < max_it:
        it += 1
        N = get_inter_best_swap_random_neighbor(cvrp, soln)
        if N[0][0] + EPS < soln.fs:
            it = 0
            # apply and accept move
            soln.inter_best_swap_move(cvrp, N[0][1], N[0][2], N[0][3], N[0][4])
    return soln, time.time() - t_init


def get_random_neighbor(cvrp, soln):
    """Get either a 2-opt (50% odd) or a inter-route swap neighbor (50% odd)"""
    r = random.random()
    if r < 0.5:
        return get_two_opt_random_neighbor(cvrp, soln)
    else:
        return get_inter_best_swap_random_neighbor(cvrp, soln)


def random_descent(cvrp, soln, max_it):
    """Random descent local search method (2-opt or inter-route swap) for CVRP"""
    t_init = time.time()
    it = 0
    while it < max_it:
        it += 1
        k = random.random()
        if k < 0.5:
            N = get_two_opt_random_neighbor(cvrp, soln)
            if N[0][0] + EPS < soln.fs:
                it = 0
                # apply and accept move
                soln.two_opt_move(cvrp, N[0][1], N[0][2], N[0][3])
        elif k < 1.0:
            N = get_inter_best_swap_random_neighbor(cvrp, soln)
            if N[0][0] + EPS < soln.fs:
                it = 0
                # apply and accept move
                soln.inter_best_swap_move(cvrp, N[0][1], N[0][2], N[0][3], N[0][4])
    return soln, time.time() - t_init


def vnd(cvrp, soln, max_k):
    """Variable neighborhood descent method for TSP (k=1: 2-opt k=2: inter-route swap)"""
    t_init = time.time()
    k = 1
    while k <= max_k:
        if k == 1:
            soln_, t = descent_two_opt(cvrp, soln)
        elif k == 2:
            soln_, t = descent_inter_best_swap(cvrp, soln)
        if soln_.fs < soln.fs:
            soln_ = soln.copy()
            k = 1
        else:
            k += 1
    return soln, time.time() - t_init


def vnd_first_improvement(cvrp, soln, max_k):
    """Variable neighborhood descent (using first improvement) method for TSP (k=1: 2-opt k=2: inter-route swap)"""
    t_init = time.time()
    k = 1
    while k <= max_k:
        if k == 1:
            soln_, t = first_improvement_two_opt(cvrp, soln)
        elif k == 2:
            soln_, t = first_improvement_inter_best_swap(cvrp, soln)
        if soln_.fs < soln.fs:
            soln_ = soln.copy()
            k = 1
        else:
            k += 1
    return soln, time.time() - t_init

# def vnd_first_improvement(d, s, fs, max_k):
#     """Variable neighborhood descent method for TSP (k=1: 2-opt k=2: 3-opt)"""
#     t_init = time.time()
#     k = 1
#     while k <= max_k:
#         if k == 1:
#             s_line, fs_line, t = first_improvement_two_opt(d, s, fs)
#         elif k == 2:
#             s_line, fs_line, t = first_improvement_three_opt(d, s, fs)
#         if fs_line < fs:
#             s = s_line[:]
#             fs = fs_line
#             k = 1
#         else:
#             k += 1
#     return s, fs, time.time() - t_init


def local_search(cvrp, soln, params):
    if params.local_search == "DESCENT2OPT":
        soln, t = descent_two_opt(cvrp, soln)
    elif params.local_search == "DESCENTINTER":
        soln, t = random_descent_inter_best_swap(cvrp, soln)
    elif params.local_search == "FIRSTIMP2OPT":
        soln, t = first_improvement_two_opt(cvrp, soln)
    elif params.local_search == "FIRSTIMPINTER":
        soln, t = first_improvement_inter_best_swap(cvrp, soln)
    elif params.local_search == "RANDOM*":
        soln, t = random_descent(cvrp, soln, params.ls_max * len(cvrp.d))
    elif params.local_search == "RANDOM2OPT":
        soln, t = random_descent_two_opt(cvrp, soln, params.ls_max * len(cvrp.d))
    elif params.local_search == "RANDOMINTER":
        soln, t = random_descent_inter_best_swap(cvrp, soln, params.ls_max * len(cvrp.d))
    elif params.local_search == "VND":
        soln, t = vnd(cvrp, soln, params.neigh_types)
    elif params.local_search == "VNDFIRSTIMPROV":
        soln, t = vnd_first_improvement(cvrp, soln, params.neigh_types)
    return soln, t

#
# def get_three_opt_first_neighbor(d, s, fs):
#     """Get first neighbor regarding 3-opt neighborhood. A neighbor represented as: [fs, i, j, k]"""
#     N = []
#     for i_idx in range(1, len(s) - 1):
#         for j_idx in range(i_idx + 1, len(s) - 1):
#             for k_idx in range(j_idx + 1, len(s) - 1):
#                 s_new_dist = tsp.three_opt(d, s, fs, i_idx, j_idx, k_idx)
#                 if s_new_dist + EPS < fs:
#                     # add neighbor
#                     N.append((s_new_dist, i_idx, j_idx, k_idx))
#                     return N
#     return N
#
#
# def get_three_opt_first_neighbor_sample(d, s, fs):
#     """Get first neighbor regarding 3-opt neighborhood. A neighbor represented as: [fs, i, j, k]"""
#     N = []
#     l = range(1, len(s) - 1)
#     l = random.sample(l, len(l))
#     for i in range(len(l)):
#         for j in range(i + 1, len(l)):
#             for k in range(j + 1, len(l)):
#                 i_idx = l[i]
#                 j_idx = l[j]
#                 k_idx = l[k]
#                 # ensure i, j and k are ordered
#                 sum_val = i_idx + j_idx + k_idx
#                 max_val = max(i_idx, j_idx, k_idx)
#                 min_val = min(i_idx, j_idx, k_idx)
#                 i_idx = min_val
#                 j_idx = sum_val - max_val - min_val
#                 k_idx = max_val
#                 s_new_dist = tsp.three_opt(d, s, fs, i_idx, j_idx, k_idx)
#                 if s_new_dist + EPS < fs:
#                     # add neighbor
#                     N.append((s_new_dist, i_idx, j_idx, k_idx))
#                     return N
#     return N
#
#
# def get_three_opt_neighbors(d, s, fs):
#     """Get all neighbors regarding 3-opt neighborhood. A neighbor represented as: [fs, i, j, k]"""
#     N = []
#     for i_idx in range(1, len(s) - 1):
#         for j_idx in range(i_idx + 1, len(s) - 1):
#             for k_idx in range(j_idx + 1, len(s) - 1):
#                 fs_line = tsp.three_opt(d, s, fs, i_idx, j_idx, k_idx)
#                 if fs_line + EPS < fs:
#                     # add neighbor
#                     N.append((fs_line, i_idx, j_idx, k_idx))
#     return N
#
#
# def get_three_opt_random_neighbor(d, s, fs):
#     """Get a random 3-opt neighbor represented as: [fs, i, j, k]"""
#     N = []
#     i = random.choice(range(1, len(s) - 1))
#     j = random.choice(range(1, len(s) - 1))
#     k = random.choice(range(1, len(s) - 1))
#     while i == j or i == k or j == k:
#         i = random.choice(range(1, len(s) - 1))
#         j = random.choice(range(1, len(s) - 1))
#         k = random.choice(range(1, len(s) - 1))
#     # ensure i, j and k are ordered
#     sum_val = i + j + k
#     max_val = max(i, j, k)
#     min_val = min(i, j, k)
#     i = min_val
#     j = sum_val - max_val - min_val
#     k = max_val
#     s_new_dist = tsp.three_opt(d, s, fs, i, j, k)
#     N.append((s_new_dist, i, j, k))
#     return N
# def descent_three_opt(d, s, fs):
#     """Descent local search method (3-opt) for TSP"""
#     t_init = time.time()
#     N = get_three_opt_neighbors(d, s, fs)
#     while N:
#         # select best neighbor
#         best_n = -1
#         min = float("inf")
#         for n in N:
#             if n[0] < min:
#                 min = n[0]
#                 best_n = n
#         # move to next neighbor
#         (s, fs) = tsp.three_opt_move(d, s, fs, best_n[1], best_n[2], best_n[3])
#         N = get_three_opt_neighbors(d, s, fs)
#     return s, fs, time.time() - t_init

# def random_descent_three_opt(d, s, fs, max_it):
#     """Random descent local search method (3-opt) for TSP"""
#     t_init = time.time()
#     it = 0
#     while it < max_it:
#         it += 1
#         N = get_three_opt_random_neighbor(d, s, fs)
#         if N[0][0] + EPS < fs:
#             it = 0
#             # apply and accept move
#             s, fs = tsp.three_opt_move(d, s, fs, N[0][1], N[0][2], N[0][3])
#     return s, fs, time.time() - t_init