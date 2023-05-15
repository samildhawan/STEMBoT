# All libraries go here
import numpy as np
import pandas as pd
from matplotlib import pyplot as plt
from sympy import Symbol, Eq, solve
from tqdm import tqdm


def compute_percent_error(Y, Y_true):
    Y, Y_true = np.asarray(Y, dtype=np.float32), np.asarray(Y_true, dtype=np.float32)
    return np.around(np.abs(Y - Y_true) / Y_true, 5)


def plot_figure(X, Y, Y_true):
    plt.plot(X, Y, label='h from autonomous framework')
    plt.plot(X, Y_true, label='h from paper')
    plt.legend()
    # plt.scatter(X, Y, marker='x')
    plt.xlabel('Contact Pressure (MPa)')
    plt.ylabel('IHTC (kW/m²K)')
    # plt.title('The IHTC Evolutions with Contact Pressure (Cast Iron)')
    plt.title('The IHTC Evolutions with Contact Pressure (P20)')
    plt.show()


def plot_error_analysis(X, Y, Y_true):
    percent_error = compute_percent_error(Y, Y_true) * 100
    plt.plot(X, percent_error)
    plt.xlabel('Contact Pressure (MPa)')
    plt.ylabel('Percentage Error (%)')
    # plt.title('Error Analysis (Cast Iron)')
    plt.title('Error Analysis (P20)')
    plt.show()


# All equation parameters go here
# delta = 1.5e-5

colomn_name = ['P', 'h']
# df = pd.read_csv('figures\\cast_iron.csv', header=None, names=colomn_name)
df = pd.read_csv('figures\\p20.csv', header=None, names=colomn_name)
P_list = pd.to_numeric(df['P']).tolist()
h_list_paper = pd.to_numeric(df['h']).tolist()
h_list = []

for P in tqdm(P_list, desc='Generating Curve'):
    # All equations go here

    # print(P)
    # print(solve(exprs)[0])
    sol = solve(exprs)[0]

    # for key, val in sol.items():
    #     exec("{} = {}".format(key, val))

    # print(sol)
    h_list.append(round(sol[h], 5))


print('X: {}'.format(P_list))
print('Y: {}'.format(h_list))
print('Y_true: {}'.format(h_list_paper))

plot_figure(P_list, h_list, h_list_paper)
plot_error_analysis(P_list, h_list, h_list_paper)