''' Trying on gcn algorithm git repo retrieved from https://github.com/tkipf/gcn '''

from scipy.sparse import csr_matrix
from mtx_processor import MtxProcessor
from collections import defaultdict
from gcn import train
import numpy as np
import math

def get_data_for_gcn(adj_dict, ft_mtx, y, n, d):
    print('n is')
    print(n)
    
    graph = defaultdict(int, adj_dict)
    ally = np.zeros((n, 3))
    print('n is :', n)
    # a = 0
    # j = 0
    # k = 0
    for i, yi in enumerate(y, start=0):
        print(yi)
        if yi == 0: 
            # k += 1
            ally[i][1] = 1
        elif yi == 1:
            # j += 1 
            ally[i][0] = 1
        elif yi == -1: 
            # a += 1
            ally[i][2] = 1
    # print('labeled real : ', j)
    # print('labeled fake : ', k)
    # print('unlabeled : ', a)
    allx = np.array(ft_mtx)

    indices = np.arange(allx.shape[0])
    np.random.shuffle(indices)
    allx = allx[indices]
    ally = ally[indices]
    allx = csr_matrix(allx)

    n_1 = math.floor(n/20)
    n_2 = math.floor(n/18)

    x    = allx[n_1:n_2]
    y    = ally[n_1:n_2]
    tx   = allx[:n_1]
    ty   = ally[:n_1]
    allx = allx[n_1:]
    ally = ally[n_1:]

    return x, y, tx, ty, allx, ally, graph


mp = MtxProcessor()

''' Try gcn with different feature matrix.
    Do not run trains in a row. Run them separately.
'''
# Try with every feature
# x, y, tx, ty, allx, ally, graph = get_data_for_gcn(mp.adj_dict, mp.bin_ft_mtx, mp.y, mp.n, mp.d)
# train.train(x, y, tx, ty, allx, ally, graph)

# Try with bin features
x, y, tx, ty, allx, ally, graph = get_data_for_gcn(mp.adj_dict, mp.bin_ft_mtx, mp.y, mp.n, mp.d)
train.train(x, y, tx, ty, allx, ally, graph)

mp.show_adj_graph()