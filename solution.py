import copy

class Solution:

    def __init__(self, s, fs, cap: None):
        self.s = s  # solution as a list of routes (sub-lists)
        self.fs = fs  # solution objective function cost
        self.cap = cap  # list of used capacities for each route

    def copy(self):
        """"Return a copy of current solution"""
        s = copy.deepcopy(self.s)
        fs = self.fs
        cap = self.cap[:]
        soln = Solution(s, fs, cap)
        return soln

    # neighborhood moves
    def two_opt_eval(self, cvrp, r, i, j):
        """"Eval 2-opt at indexes i and j (reversion of route segment [i...j])"""
        fs = self.fs + cvrp.d[self.s[r][i - 1]][self.s[r][j]] + cvrp.d[self.s[r][i]][self.s[r][j + 1]] \
             - cvrp.d[self.s[r][i - 1]][self.s[r][i]] - cvrp.d[self.s[r][j]][self.s[r][j + 1]]
        return fs

    def two_opt_move(self, cvrp, r, i, j):
        """"Do 2-opt move at indexes i and j (reverse route segment [i...j])"""
        self.fs += cvrp.d[self.s[r][i - 1]][self.s[r][j]] + cvrp.d[self.s[r][i]][self.s[r][j + 1]] \
                   - cvrp.d[self.s[r][i - 1]][self.s[r][i]] - cvrp.d[self.s[r][j]][self.s[r][j + 1]]
        self.s[r] = self.s[r][0:i] + list(reversed(self.s[r][i:j + 1])) + self.s[r][j + 1:]
        return self

    def inter_swap_eval(self, cvrp, r1, r2, i, j):
        """"Do inter-route swap between indexes i and j if possible."""
        if self.cap[r1] - cvrp.dem[self.s[r1][i]] + cvrp.dem[self.s[r2][j]] <= cvrp.cap \
                and self.cap[r2] - cvrp.dem[self.s[r2][j]] + cvrp.dem[self.s[r1][i]] <= cvrp.cap:
            # move is feasible w.r.t. vehicle capacity
            fs = self.fs - cvrp.d[self.s[r1][i - 1]][self.s[r1][i]] - cvrp.d[self.s[r1][i]][self.s[r1][i + 1]] \
                 - cvrp.d[self.s[r2][j - 1]][self.s[r2][j]] - cvrp.d[self.s[r2][j]][self.s[r2][j + 1]] \
                 + cvrp.d[self.s[r1][i - 1]][self.s[r2][j]] + cvrp.d[self.s[r2][j]][self.s[r1][i + 1]] \
                 + cvrp.d[self.s[r2][j - 1]][self.s[r1][i]] + cvrp.d[self.s[r1][i]][self.s[r2][j + 1]]
            return fs
        else:
            return float("inf")

    def inter_swap_move(self, cvrp, r1, r2, i, j):
        """"Do inter-route swap between indexes i and j if possible."""
        if self.cap[r1] - cvrp.dem[self.s[r1][i]] + cvrp.dem[self.s[r2][j]] <= cvrp.cap \
                and self.cap[r2] - cvrp.dem[self.s[r2][j]] + cvrp.dem[self.s[r1][i]] <= cvrp.cap:
            # move is feasible w.r.t. vehicle capacity
            self.fs = self.fs - cvrp.d[self.s[r1][i - 1]][self.s[r1][i]] - cvrp.d[self.s[r1][i]][self.s[r1][i + 1]] \
                      - cvrp.d[self.s[r2][j - 1]][self.s[r2][j]] - cvrp.d[self.s[r2][j]][self.s[r2][j + 1]] \
                      + cvrp.d[self.s[r1][i - 1]][self.s[r2][j]] + cvrp.d[self.s[r2][j]][self.s[r1][i + 1]] \
                      + cvrp.d[self.s[r2][j - 1]][self.s[r1][i]] + cvrp.d[self.s[r1][i]][self.s[r2][j + 1]]
            self.s[r1][i], self.s[r2][j] = self.s[r2][j], self.s[r1][i]
            self.cap[r1] = self.cap[r1] - cvrp.dem[self.s[r1][i]] + cvrp.dem[self.s[r2][j]]
        return self

    def inter_best_swap_eval(self, cvrp, r1, r2, i, j):
        """"Do inter-route swap between indexes i and j if possible."""
        if self.cap[r1] - cvrp.dem[self.s[r1][i]] + cvrp.dem[self.s[r2][j]] <= cvrp.cap \
                and self.cap[r2] - cvrp.dem[self.s[r2][j]] + cvrp.dem[self.s[r1][i]] <= cvrp.cap:
            # save i and j nodes
            node_i, node_j = self.s[r1][i], self.s[r2][j]
            # first, remove i and j from their respective routes (they will be added back later)
            delta = - cvrp.d[self.s[r1][i - 1]][self.s[r1][i]] - cvrp.d[self.s[r1][i]][self.s[r1][i + 1]] + cvrp.d[self.s[r1][i - 1]][self.s[r1][i + 1]] \
                    - cvrp.d[self.s[r2][j - 1]][self.s[r2][j]] - cvrp.d[self.s[r2][j]][self.s[r2][j + 1]] + cvrp.d[self.s[r2][j - 1]][self.s[r2][j + 1]]
            self.s[r1].pop(i)
            self.s[r2].pop(j)

            # find the cheapest insertion for node i
            delta_best_i = float("inf")
            best_idx = None
            for idx in range(1, len(self.s[r2])):
                delta_idx = cvrp.d[self.s[r2][idx - 1]][node_i] + cvrp.d[node_i][self.s[r2][idx]] - cvrp.d[self.s[r2][idx - 1]][self.s[r2][idx]]
                if delta_idx < delta_best_i:
                    delta_best_i = delta_idx
                    best_idx = idx

            # find the cheapest insertion for node j
            delta_best_j = float("inf")
            best_idx = None
            for idx in range(1, len(self.s[r1])):
                delta_idx = cvrp.d[self.s[r1][idx - 1]][node_j] + cvrp.d[node_j][self.s[r1][idx]] - cvrp.d[self.s[r1][idx - 1]][self.s[r1][idx]]
                if delta_idx < delta_best_j:
                    delta_best_j = delta_idx
                    best_idx = idx

            # get updated cost function
            fs = self.fs + delta + delta_best_i + delta_best_j

            # add i and j back to the solution
            self.s[r1].insert(i, node_i)
            self.s[r2].insert(j, node_j)
            return fs
        else:
            return float("inf")

    def inter_best_swap_move(self, cvrp, r1, r2, i, j):
        """"Do inter-route swap between indexes i and j if possible."""
        if self.cap[r1] - cvrp.dem[self.s[r1][i]] + cvrp.dem[self.s[r2][j]] <= cvrp.cap \
                and self.cap[r2] - cvrp.dem[self.s[r2][j]] + cvrp.dem[self.s[r1][i]] <= cvrp.cap:
            # save i and j nodes
            node_i, node_j = self.s[r1][i], self.s[r2][j]
            # first, remove i and j from their respective routes
            delta = - cvrp.d[self.s[r1][i - 1]][self.s[r1][i]] - cvrp.d[self.s[r1][i]][self.s[r1][i + 1]] + cvrp.d[self.s[r1][i - 1]][self.s[r1][i + 1]] \
                    - cvrp.d[self.s[r2][j - 1]][self.s[r2][j]] - cvrp.d[self.s[r2][j]][self.s[r2][j + 1]] + cvrp.d[self.s[r2][j - 1]][self.s[r2][j + 1]]
            self.s[r1].pop(i)
            self.s[r2].pop(j)

            # find and perform the cheapest insertion for node i
            delta_best_i = float("inf")
            best_idx = None
            for idx in range(1, len(self.s[r2])):
                delta_idx = cvrp.d[self.s[r2][idx - 1]][node_i] + cvrp.d[node_i][self.s[r2][idx]] - cvrp.d[self.s[r2][idx - 1]][self.s[r2][idx]]
                if delta_idx < delta_best_i:
                    delta_best_i = delta_idx
                    best_idx = idx
            self.s[r2].insert(best_idx, node_i)

            # find and perform the cheapest insertion for node j
            delta_best_j = float("inf")
            best_idx = None
            for idx in range(1, len(self.s[r1])):
                delta_idx = cvrp.d[self.s[r1][idx - 1]][node_j] + cvrp.d[node_j][self.s[r1][idx]] - cvrp.d[self.s[r1][idx - 1]][self.s[r1][idx]]
                if delta_idx < delta_best_j:
                    delta_best_j = delta_idx
                    best_idx = idx
            self.s[r1].insert(best_idx, node_j)

            # update cost function and capacities
            self.fs += delta + delta_best_i + delta_best_j
            self.cap[r1] = self.cap[r1] - cvrp.dem[self.s[r1][i]] + cvrp.dem[self.s[r2][j]]
        return self

    def move_to_neighbor(self, N, cvrp):
        """"Move to neighbor N (either a 2-opt or inter-route swap)."""
        if len(N) == 4:  # 2-opt neighbor
            self.two_opt_move(cvrp, N[1], N[2], N[3])
        elif len(N) == 5:  # route-swap neighbor
            self.inter_best_swap_move(cvrp, N[1], N[2], N[3], N[4])
        return self

    def obj_eval(self, cvrp):
        """"Full evaluation of objective function"""
        rota_cap = []
        rota_dist = []
        fs = 0
        for rota in range(len(self.s)):
            aux_dist = 0
            aux_cap = 0
            for i in range(len(self.s[rota]) - 1):
                aux_dist += cvrp.d[self.s[rota][i]][self.s[rota][i + 1]]
                aux_cap += cvrp.dem[self.s[rota][i]]
            rota_dist.append(aux_dist)
            rota_cap.append(aux_cap)
            fs += aux_dist
            if aux_cap > cvrp.cap:
                # capacity exceeded! infeasible solution
                fs += 10000000
        return fs
