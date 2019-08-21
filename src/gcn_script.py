''' Trying on gcn algorithm git repo retrieved from https://github.com/tkipf/gcn '''

from scipy.sparse import csr_matrix
from mtx_processor import MtxProcessor
from collections import defaultdict
from gcn import train
import numpy as np

def get_data_for_gcn(adj_dict, ft_mtx, y, n, d):
    graph = defaultdict(int, adj_dict)
    ally = np.zeros((n, 2))
    for i, yi in enumerate(y, start=0):
        if yi ==  0: ally[i][1] = 1
        elif yi ==  1: ally[i][0] = 1
        # elif yi == -1: ally[i][2] = 1
        
    allx = csr_matrix(np.array(ft_mtx))
    # x, y, tx, ty, allx, ally, graph
    return allx[80:100], ally[80:100], allx[:40], ally[:40], allx[40:], ally[40:], graph


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
