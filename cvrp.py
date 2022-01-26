import random
from solution import Solution
import time
import numpy as np
import math

class CVRP:
    def __init__(self, d, dem, cap, coord):
        self.n = len(d)  # problem size (number of nodes)
        self.d = d  # distance matrix
        self.dem = dem  # demand list for each node
        self.cap = cap  # capacity of the vehicle (homogeneous fleet)
        self.coord = coord  # coordinates for each node
        self.v = math.ceil(np.sum(self.dem) / self.cap)

    # Constructive methods
    def greedy_build(self):
        """"Greedy initial solution build by nearest neighbor heuristic"""
        t_init = time.time()
        s = [[0]]
        fs = 0
        cap = [0]
        C = [i for i in range(1, self.n)]
        while len(C) != 0:
            # select c_min (nearest neighbor within capacity)
            val_min = float("inf")
            c_min = -1
            for c in C:
                if self.d[s[-1][-1]][c] < val_min and cap[-1] + self.dem[c] <= self.cap:
                    val_min = self.d[s[-1][-1]][c]
                    c_min = c
            # insert c_min into s
            if c_min != -1:
                s[-1].append(c_min)
                fs += val_min
                cap[-1] += self.dem[c_min]
                C.remove(c_min)
            else:
                s[-1].append(0)
                fs += self.d[s[-1][-2]][s[-1][-1]]
                s.append([0])
                cap.append(0)
        # add first node to close the cycle
        fs += self.d[s[-1][-1]][s[-1][0]]
        s[-1].append(s[-1][0])
        return Solution(s, fs, cap), time.time() - t_init

    def can_merge(self, i, j, s):
        """Auxiliary function to determine whether routes of i and j can be merged"""
        res_dem = 0
        for route_idx in range(len(s)):
            i_in_idx = i in s[route_idx]
            j_in_idx = j in s[route_idx]
            if i_in_idx and j_in_idx:
                # belong to the same route
                return False
            elif i_in_idx and s[route_idx].index(i) not in [1, len(s[route_idx]) - 2]:
                # i is interior on its route
                return False
            elif j_in_idx and s[route_idx].index(j) not in [1, len(s[route_idx]) - 2]:
                # j is interior on its route
                return False
            if i_in_idx:
                for x in s[route_idx]:
                    res_dem += self.dem[x]
            if j_in_idx:
                for x in s[route_idx]:
                    res_dem += self.dem[x]
        if res_dem > self.cap:
            return False
        return True

    def greedy_build_savings(self):
        """"Greedy initial solution build by Savings heuristic"""
        t_init = time.time()
        s = []
        fs = 0
        cap = []
        for i in range(1, len(self.d)):
            s.append([])
            s[-1].append(0)
            s[-1].append(i)
            s[-1].append(0)
            fs += 2 * self.d[0][i]
            cap.append(self.dem[i])
        # calculate savings
        saving_options = []
        for i in range(1, len(self.d)):
            for j in range(i + 1, len(self.d)):
                sav = self.d[i][0] + self.d[0][j] - self.d[i][j]
                saving_options.append((i, j, sav))
        saving_options.sort(key=lambda elem: elem[2], reverse=True)
        while saving_options:
            # chooses the max feasible savings
            (max_i, max_j, max_sav) = saving_options.pop(0)
            if self.can_merge(max_i, max_j, s):
                # merge routes from max_i and max_j
                rem_dem = -1
                for idx in range(len(s)):
                    if max_j in s[idx]:
                        sub_j = s[idx][1:-1]
                        s.pop(idx)
                        rem_dem = cap[idx]
                        cap.pop(idx)
                        break
                for idx in range(len(s)):
                    if max_i == s[idx][1] and sub_j[-1] == max_j:
                        s[idx] = [0] + sub_j[:] + s[idx][1:-1] + [0]
                        cap[idx] += rem_dem
                        break
                    elif max_i == s[idx][1] and sub_j[0] == max_j:
                        s[idx] = [0] + list(reversed(sub_j)) + s[idx][1:-1] + [0]
                        cap[idx] += rem_dem
                        break
                    elif max_i == s[idx][-2] and sub_j[-1] == max_j:
                        s[idx] = [0] + s[idx][1:-1] + list(reversed(sub_j)) + [0]
                        cap[idx] += rem_dem
                        break
                    elif max_i == s[idx][-2] and sub_j[0] == max_j:
                        s[idx] = [0] + s[idx][1:-1] + sub_j + [0]
                        cap[idx] += rem_dem
                        break
                fs -= max_sav
        return Solution(s, fs, cap), time.time() - t_init

    def part_greedy_build(self, alpha):
        """Partially greedy initial solution based on nearest neighbor heuristic"""
        t_init = time.time()
        s = [[0]]
        fs = 0
        cap = [0]
        C = [i for i in range(1, self.n)]
        while len(C) != 0:
            # calculate g_min and g_max
            g_max = float("-inf")
            g_min = float("inf")
            for c in C:
                if self.d[s[-1][-1]][c] < g_min and cap[-1] + self.dem[c] <= self.cap:
                    g_min = self.d[s[-1][-1]][c]
                if self.d[s[-1][-1]][c] > g_max and cap[-1] + self.dem[c] <= self.cap:
                    g_max = self.d[s[-1][-1]][c]
            # create restricted list of candidates (LCR)
            LCR = []
            for c in C:
                if self.d[s[-1][-1]][c] <= g_min + alpha * (g_max - g_min) and cap[-1] + self.dem[c] <= self.cap:
                    LCR.append(c)
            if LCR:
                # randomly select c among the alpha best candidates and insert into s
                c = random.choice(LCR)
                s[-1].append(c)
                fs += self.d[s[-1][-2]][s[-1][-1]]
                cap[-1] += self.dem[c]
                C.remove(c)
            else:
                # close current route and start a new one
                s[-1].append(0)
                fs += self.d[s[-1][-2]][s[-1][-1]]
                s.append([0])
                cap.append(0)
        # add first node to close the cycle
        fs += self.d[s[-1][-1]][s[-1][0]]
        s[-1].append(s[-1][0])
        return Solution(s, fs, cap), time.time() - t_init
