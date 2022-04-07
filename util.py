import matplotlib.pyplot as plt
import numpy as np
from bokeh.plotting import figure, show, save, output_file
import solution
import cvrp

def read_cvrp(file_path):
    """"Read a CVRP instance in TSPLIB95 format
    http://comopt.ifi.uni-heidelberg.de/software/TSPLIB95/tsp95.pdf"""
    file = open(file_path, "r")
    cap = None
    d = []
    dem = []
    coord = []
    mode = "NODE_COORD"
    for line in file:
        if line.find("EDGE_WEIGHT_SECTION") != -1:
            mode = "EDGE_WEIGHT"
            break
        if line.find("NODE_COORD_SECTION") != -1:
            break
        if line.find("CAPACITY") != -1:
            line = line.strip().replace("\t", " ").split(" ")
            cap = float(line[-1])
    for line in file:
        if line.find("DEMAND_SECTION") != -1:
            break
        line = line.strip().replace("\t", " ").split(" ")
        i = int(line[0])
        x = float(line[1])
        y = float(line[2])
        coord.append((i, x, y))
    for line in file:
        if line.find("DEPOT_SECTION") != -1:
            break
        line = line.strip().replace("\t", " ").split(" ")
        dem.append(float(line[-1]))
    n = len(coord)
    d = [[0 for _ in range(n)] for _ in range(n)]
    for (i, xi, yi) in coord:
        for (j, xj, yj) in coord:
            if i != j:
                d[i - 1][j - 1] = ((xi - xj) ** 2 + (yi - yj) ** 2) ** (1 / 2)
    return d, dem, cap, coord

def read_soln(file_path, inst):
    """"Read a CVRP instance in TSPLIB95 .sol format
    http://comopt.ifi.uni-heidelberg.de/software/TSPLIB95/tsp95.pdf"""
    try:
        file = open(file_path, "r")
        cap = None
        s = []
        fs = 0
        for line in file:
            if line[0] == "R":
                line = line.split(": ")[1].strip()
                route = [int(x) for x in line.split(" ")]
                route.insert(0, 0)
                route.append(0)
                s.append(route)
            elif line[0] == "C":
                fs = float(line.split(" ")[1].strip())
        soln = solution.Solution(s, fs, None)
    except IOError:
        print("Solution file could not be read.\nAborting execution...")
        exit(0)
    return soln

def write_soln(file_path, soln):
    """"Write a CVRP solution in TSPLIB95 .sol format"""
    file = open(file_path, "w")
    content = ""
    for k in range(len(soln.s)):
        content += f"Route {k+1}:"
        for i in range(1, len(soln.s[k]) - 1):
            content += f" {i}"
        content += "\n"
    content += f"Cost {soln.fs}"
    file.write(content)

def plot_chart(chart_data, file, title, ub=None):
    fig, ax = plt.subplots()
    chart_data = np.array(chart_data)
    plt.plot(chart_data[:, 0], chart_data[:, 1], 'b--', chart_data[:, 0], chart_data[:, 2], 'r-')
    # plt.ylim([0, chart_data[0, 1]])
    if ub:  # print optimal solution cost base line
        plt.axhline(y=ub, color='k', linestyle='--')
    plt.legend(('Current', 'Best', 'BKS'),
               loc='upper right', shadow=True)
    ax.set(xlabel='time (s)', ylabel='f(s)',
           title=title)
    ax.grid()
    fig.savefig(file)
    # plt.show()


def plot_overall_chart(chart_data, methods, file, title, ub=None):
    fig, ax = plt.subplots()
    styles = ['o-b', '^--g', ',-.r', 'v:c', 's-m', 'vk:', 'v-g', 'o-r', '^--y', ',-.b']
    for i in range(len(chart_data)):
        preprocess_data(chart_data[i])
        data = np.array(chart_data[i])
        plt.plot(data[:, 0], data[:, 2], styles[i])
    if ub is not None:  # print optimal solution cost base line
        plt.axhline(y=ub, color='k', linestyle='--')
        methods.append('BKS')
    plt.legend(methods,
               loc='upper right', shadow=True)
    ax.set(xlabel='time (s)', ylabel='f(s)',
           title=title)
    ax.grid()
    fig.savefig(file)
    # plt.show()


def preprocess_data(data):
    """"Remove duplicated best solution records"""
    i  = 0
    while i + 1 < len(data):
        if data[i][2] == data[i+1][2]:
            data.pop(i+1)
        else:
            i += 1


def plot_sol(s, coord, file_name, title="", path=False):
    """"Print a TSP solution"""
    fig = figure(title=title)
    i, x, y = zip(*coord)
    fig.circle(x, y, size=8)
    for r in range(len(s)):
        ptseq = [coord[k] for k in s[r]]
        if not path:
            ptseq.append(ptseq[0])
        i, x, y = zip(*ptseq)
        fig.line(x, y)

    #show(fig)
    output_file(file_name)
    save(fig)
    #export_png(fig, filename=file_name)
    # fig.outpsavefig(file_name)