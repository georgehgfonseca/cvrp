import solution
from cvrp import CVRP
import numpy as np
from mip import Var, Model, BINARY, INTEGER, CONTINUOUS, xsum, OptimizationStatus, InterfacingError, CBC, GRB
from itertools import permutations
import math
import time
import random

class CVRPModel:
    __slots__ = ['inst', 'params', 'soln', 'model', 'x', 't', 'u', 'b', 'lbs', 'ubs']

    def __init__(self, inst: CVRP, params, soln):
        self.inst = inst
        self.params = params
        self.soln = soln

        # model-related variables
        self.model = None
        self.x = self.t = self.u = self.b = None
        self.lbs = self.ubs = None

        # creating and configuring model
        self.create_model()
        self.model.seed = self.params.seed
        if self.params.threads != 0:
            self.model.threads = self.params.threads

    def export_model_soln(self):
        """"Build solution object from variable values in MIP model"""
        if self.model.num_solutions == 0:
            return
        s = [[0, 0] for _ in range(self.inst.v)]
        for i in range(self.inst.n):
            for k in range(self.inst.v):
                if self.t[i, k].x >= 0.00001:
                    if i not in s[k]:
                        s[k].insert(-2, i)
                    pos_i = s[k].index(i)
                    for j in range(self.inst.n):
                        if i != j:
                            if self.x[i, j].x >= 0.00001 and j not in s[k]:
                                # insert j after i
                                s[k].insert(pos_i, j)
                            if self.x[j, i].x >= 0.00001 and j not in s[k]:
                                # insert j before i
                                s[k].insert(pos_i - 1, j)
                    break
        fs = self.model.objective_value
        return solution.Solution(s, fs)

    def convert_aux_soln(self, s):
        s_aux = [[0 for _ in range(self.inst.n)] for _ in range(self.inst.n)]
        for k in range(len(s)):
            for i in range(len(s[k]) - 1):
                s_aux[s[k][i]][s[k][i+1]] = 1
        return s_aux

    def fix_opt(self):
        chart_data = [[0, self.soln.fs, self.soln.fs]]
        t_init = time.time()
        self.load_soln()
        self.model.emphasis = 1
        n_routes = self.params.fix_opt_n
        it = 0
        fs_best = self.soln.fs
        s_aux = self.convert_aux_soln(self.soln.s)
        # idea: optimize the variables of a certain range box
        # fix a number of vehicles and optimize the others
        while time.time() - t_init < self.params.time_limit:
            it += 1
            # fix all vars
            for i in range(self.inst.n):
                for k in range(self.inst.v):
                    if it == 1:
                        if i in self.soln.s[k]:
                            self.t[i, k].ub = self.t[i, k].lb = 1.0
                        else:
                            self.t[i, k].ub = self.t[i, k].lb = 0.0
                    else:
                        if self.t[i, k].x >= 0.999:
                            self.t[i, k].ub = self.t[i, k].lb = 1.0
                        else:
                            self.t[i, k].ub = self.t[i, k].lb = 0.0
                for j in range(self.inst.n):
                    if i != j:
                        if it == 1:
                            if s_aux[i][j]:
                                self.x[i, j].ub = self.x[i, j].lb = 1.0
                            else:
                                self.x[i, j].ub = self.x[i, j].lb = 0.0
                        else:
                            if self.x[i, j].x >= 0.999:
                                self.x[i, j].ub = self.x[i, j].lb = 1.0
                            else:
                                self.x[i, j].ub = self.x[i, j].lb = 0.0

            # # randomly choose a center point to unfix: approach B
            # unfixed_c = [random.choice(list(range(1, self.inst.n)))]
            # for _ in range(n_routes * 30):
            #     min_dist = float("inf")
            #     min_i = -1
            #     for i in range(self.inst.n):
            #         if self.inst.d[unfixed_c[0]][i] < min_dist and i not in unfixed_c:
            #             min_dist = self.inst.d[unfixed_c[0]][i]
            #             min_i = i
            #     if i == -1:
            #         break
            #     unfixed_c.append(min_i)
            # print(len(unfixed_c), unfixed_c)
            #
            # # unfix selected t vars and their x related vars
            # for i in unfixed_c:
            #     for j in range(self.inst.n):
            #         if i != j:
            #             self.x[i, j].lb = self.x[j, i].lb = 0
            #             self.x[i, j].ub = self.x[j, i].ub = 1
            #     for k in range(self.inst.v):
            #         self.t[i, k].lb = 0
            #         self.t[i, k].ub = 1

            # randomly choose routes to unfix: approach A
            unfixed_routes = random.sample(list(range(self.inst.v)), n_routes)
            print(unfixed_routes, self.inst.v)

            # unfix selected t vars and their x related vars
            for i in range(self.inst.n):
                for k in unfixed_routes:
                    self.t[i, k].lb = 0
                    self.t[i, k].ub = 1
                    if (it == 1 and i in self.soln.s[k]) or (it != 1 and self.t[i, k].x > 0.999):
                        for j in range(self.inst.n):
                            if i != j:
                                self.x[i, j].lb = self.x[j, i].lb = 0
                                self.x[i, j].ub = self.x[j, i].ub = 1

            self.model.write('model.lp')

            self.model.optimize(max_seconds=self.params.fix_opt_it_tl)
            chart_data.append([time.time() - t_init, self.model.objective_value, self.model.objective_value])

            if self.params.verbose:
                print(f'| it: {it:6d}  |  n_routes: {n_routes:6d}  |  lb: {self.model.objective_bound:10.2f}  |  ub (s): {self.model.objective_value:10.2f}  |  time: {time.time() - t_init:10.2f} |')

            # check for global optimality
            if self.model.status == OptimizationStatus.OPTIMAL and n_routes >= self.inst.v:
                print("=" * 18, "Solution is optimal (sub-problem size equals problem size) ", "=" * 18)
                break

            # adjust sub-problem size
            if self.model.objective_value < fs_best:
                fs_best = self.model.objective_value
            else:
                if self.model.status == OptimizationStatus.OPTIMAL:
                    n_routes += 1#= math.ceil(n_routes * 1.20)
                else:
                    n_routes -= 1#= math.ceil(n_routes * 0.80)

        soln = self.export_model_soln()
        return soln, self.model.objective_value, time.time() - t_init, chart_data

    def create_model(self):
        # setting up solver
        try:
            model = Model("Timetabling", solver_name=GRB)
        except (InterfacingError, FileNotFoundError):
            print("Gurobi commercial solver is not licenced! Using open source CBC instead.")
            model = Model("Timetabling", solver_name=CBC)

        # aliases and shortcuts to make code easier to read
        inst, n, v, d, q, dem = self.inst, self.inst.n, self.inst.v, self.inst.d, self.inst.cap, self.inst.dem

        # creating variables *x*
        self.x = x = np.empty((n, n), dtype=Var)
        for i, j in permutations(range(n), r=2):
            x[i, j] = model.add_var(f"x({i},{j})", lb=0, ub=1, obj=inst.d[i][j], var_type=BINARY)

        # creating variables *t*
        self.t = t = np.empty((n, v), dtype=Var)
        for i in range(n):
            for k in range(v):
                t[i, k] = model.add_var(f"t({i},{k})", lb=0, ub=1, obj=0, var_type=BINARY)

        # creating variables *u*
        self.u = u = np.empty((n), dtype=Var)
        for i in range(n):
            u[i] = model.add_var(f"u({i})", obj=0, lb=dem[i], ub=q, var_type=CONTINUOUS)

        # creating constraints (14) and (15) Ensure that every node is entered and left once
        for i in range(1, n):
            model.add_constr(xsum(x[i, j] for j in range(n) if j != i) == 1, name=f"cons14_{i}")
            model.add_constr(xsum(x[j, i] for j in range(n) if j != i) == 1, name=f"cons15_{i}")

        # creating constraints (12) and (13) Exactly v outgoing and ingoing edges to depot
        model.add_constr(xsum(x[0, i] for i in range(1, n)) == v, name=f"cons12_{i}")
        model.add_constr(xsum(x[i, 0] for i in range(1, n)) == v, name=f"cons13_{i}")

        # creating constraints (6) Link between variables x and t
        for i in range(1, n):
            for j in range(i + 1, n):
                for k in range(v):
                    model.add_constr(x[i, j] + x[j, i] <= t[i, k] + 1 - t[j, k], name=f"cons6_{i}_{j}_{k}")

        # creating constraints (7) Capacity of each vehicle is respected
        for k in range(v):
            model.add_constr(xsum(t[i, k] * dem[i] for i in range(1, n)) <= q, name=f"cons7_{k}")

        # creating constraints (8) Exactly one vehicle attends each customer
        for i in range(1, n):
            model.add_constr(xsum(t[i, k] for k in range(v)) == 1, name=f"cons8_{i}")

        # creating constraints (9) MTZ sub-tour elimination constraints
        for i in range(1, n):
            for j in range(1, n):
                if i != j:
                    model.add_constr(u[i] - u[j] + ((n - 1) * x[i, j]) + ((n - 3) * x[j, i]) <= n - 2,
                                     name=f"cons9_{i}_{j}")

        # creating constraints (10) and (11) Strengthening constraints
        # for i in range(1, n):
        #     model.add_constr(u[i] >= 3 - x[0, i], name=f"cons10_{i}")
        #     model.add_constr(u[i] <= 1 + n - v, name=f"cons11_{i}")

        model.write('model.lp')

    def solve_model(self):
        self.load_soln()
        self.model.optimize(max_seconds=self.params.time_limit)
        self.print_vars()

    def load_soln(self):
        if len(self.soln.s) == self.inst.v:
            start = []
            for k in range(len(self.soln.s)):
                for i in range(len(self.soln.s[k]) - 1):
                    start.append((self.x[self.soln.s[k][i], self.soln.s[k][i+1]], 1.0))
                    start.append((self.t[self.soln.s[k][i], k], 1.0))
            self.model.start = start
            print("Initial solution loaded!")
        else:
            print("Initial solution uses more vehicles than allowed! Skipping it...")

    def print_vars(self):
        if self.model.num_solutions == 0:
            return
        # Print active variables (for debug)
        for i in range(self.inst.n):
            for j in range(self.inst.n):
                if i != j:
                    if self.x[i, j].x >= 0.00001:
                        print("%s \t %.3f" % (self.x[i, j].name, self.x[i, j].x))
        for i in range(self.inst.n):
            for k in range(self.inst.v):
                if self.t[i, k].x >= 0.00001:
                    print("%s \t %.3f" % (self.t[i, k].name, self.t[i, k].x))
        for i in range(self.inst.n):
            print(self.u[i].name, self.u[i].x)

    # def optimize(self, max_seconds: int = 0):
    #     if max_seconds:
    #         self.model.optimize(max_seconds=max_seconds)
    #     else:
    #         self.model.optimize()