from cvrp import CVRP
import numpy as np
from mip import Var, Model, BINARY, INTEGER, CONTINUOUS, xsum, OptimizationStatus
from itertools import permutations

class CVRPModel:
    __slots__ = ['inst', 'params', 'soln', 'model', 'x', 'u']

    def __init__(self, inst: CVRP, params, soln):
        self.inst = inst
        self.params = params
        self.soln = soln

        # model-related variables
        self.model = None
        self.x = self.u = None

        # creating and solving model
        self.create_model()
        self.solve_model()

    def create_model(self):
        self.model = model = Model("CVRP")
        # https://how-to.aimms.com/Articles/332/332-Formulation-CVRP.html#:~:text=A%20CVRP%20can%20be%20formulated,and%20is%20driven%20by%20vehicle%20.

        # aliases and shortcuts to make code easier to read
        inst, n, v, d, q, dem = self.inst, self.inst.n, self.inst.v, self.inst.d, self.inst.cap, self.inst.dem

        # creating variables *x*
        self.x = x = np.empty((n, n, v), dtype=Var)
        for i, j in permutations(range(n), r=2):
            for k in range(v):
                x[i, j, k] = model.add_var(f"x({i},{j},{k})", obj=inst.d[i][j], var_type=BINARY)

        # creating variables *u*
        self.u = u = np.empty((n), dtype=Var)
        for i in range(1, n):
            u[i] = model.add_var(f"u({i})", lb=dem[i], ub=q, var_type=CONTINUOUS)

        # creating constraints (1) Vehicle leaves node that it enters
        for j in range(n):
            for k in range(v):
                model.add_constr(xsum(x[i, j, k] for i in range(n) if i != j) == xsum(x[j, i, k] for i in range(n) if i != j), name=f"cons1_{j}_{k}")

        # creating constraints (2) Ensure that every node is entered once
        for j in range(1, n):
            model.add_constr(xsum(x[i, j, k] for i in range(n) for k in range(v) if i != j) == 1, name=f"cons2_{j}")

        # creating constraints (3) Every vehicle leaves the depot
        for k in range(v):
            model.add_constr(xsum(x[0, j, k] for j in range(1, n)) == 1, name=f"cons3_{k}")

        # creating constraints (4) Capacity constraint
        for k in range(v):
            model.add_constr(xsum(x[i, j, k] * dem[j] for i in range(n) for j in range(1, n) if i != j) <= q, name=f"cons4_{k}")

        # creating constraints (5) MTZ sub-tour elimination
        for i in range(1, n):
            for j in range(1, n):
                for k in range(v):
                    if i != j:
                        model.add_constr(u[j] - u[i] >= dem[j] - (q * (1 - x[i, j, k])), name=f"cons5_{i}_{j}_{k}")


        model.write('model.lp')

    def solve_model(self):
        self.load_soln()
        self.model.optimize(max_seconds=self.params.time_limit)
        self.model.write('model.lp')
        self.print_vars()

    def load_soln(self):
        if len(self.soln.s) == self.inst.v:
            start = []
            for k in range(len(self.soln.s)):
                for i in range(len(self.soln.s[k]) - 1):
                    # self.x[self.soln.s[k][i], self.soln.s[k][i+1]].start = 1.0
                    start.append((self.x[self.soln.s[k][i], self.soln.s[k][i+1], k], 1.0))
                    # self.x[self.soln.s[k][i], self.soln.s[k][i+1]].lb = self.x[self.soln.s[k][i], self.soln.s[k][i+1]].ub = 1
                    # self.u[self.soln.s[k][i]].lb = self.u[self.soln.s[k][i]].ub = load
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
                    for k in range(self.inst.v):
                        if self.x[i, j, k].x >= 0.00001:
                            print("%s \t %.3f" % (self.x[i, j, k].name, self.x[i, j, k].x))
        # for i in range(self.inst.n):
        #     for k in range(self.inst.v):
        #         if self.t[i, k].x >= 0.00001:
        #             print("%s \t %.3f" % (self.t[i, k].name, self.t[i, k].x))
        for i in range(1, self.inst.n):
            if self.u[i].x >= 0.00001:
                print(self.u[i].name, self.u[i].x)

    def optimize(self, max_seconds: int = 0):
        if max_seconds:
            self.model.optimize(max_seconds=max_seconds)
        else:
            self.model.optimize()
