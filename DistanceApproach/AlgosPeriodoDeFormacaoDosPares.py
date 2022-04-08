from copy import deepcopy
from scipy.spatial import distance
from future.utils import iteritems
from datetime import date, datetime
import pandas as pd
import numpy as np
import bt

class ConfiguracaoInicialEstrategia(bt.Algo):
    def __init__(self):
        super(ConfiguracaoInicialEstrategia, self).__init__()

    def __call__(self, target):
        target.perm["ultima_data_inicio"] = target.now+pd.DateOffset(months = 6)
        target.perm["ativos"] = target.universe.columns 
        return False 

class ChecaSeEscolhePares(bt.Algo):
    def __init__(self):
        super(ChecaSeEscolhePares, self).__init__()

    def __call__(self, target):
        if target.now>target.perm["ultima_data_inicio"]+pd.DateOffset(months=6):
            target.perm["ultima_data_inicio"] = target.now
            
            return True
        return False

class SelecionaPares(bt.Algo):
    def __init__(self, n_pares):
        super(SelecionaPares, self).__init__()
        self.n_pares = n_pares

    def __call__(self, target):
        ativos = target.perm["ativos"]
        matriz_precos_pfp = target.universe[target.now-pd.DateOffset(months=12):target.now][ativos]
        matriz_norm = self._normaliza_precos(matriz_precos_pfp)  
        matriz_distancia = self._encontra_distancia(matriz_norm)
        indices = self._encontra_menores_distancias(matriz_distancia)
        self._adiciona_pares(target, matriz_norm, matriz_precos_pfp, indices)
        return True 

    def _normaliza_precos(self, matriz):
        maximos = matriz.max(axis = 0)
        minimos = matriz.min(axis = 0)
        matriz_norm = (matriz-minimos)/(maximos-minimos)
        return matriz_norm
    
    def _encontra_distancia(self, matriz_norm):
        matriz_distancia = distance.cdist(matriz_norm.T, matriz_norm.T, 'euclidean') 
        sem_repeticao = np.triu(matriz_distancia)
        sem_repeticao[sem_repeticao == 0.] = np.nan
        return sem_repeticao
    
    def _encontra_menores_distancias(self, matriz):
        indices_tupla = np.unravel_index(np.argsort(matriz, axis=None), matriz.shape)
        indices_np = np.array(indices_tupla)
        return indices_np[:, :self.n_pares]

    def _adiciona_pares(self, target, matriz_norm, matriz_precos_pfp, indices):
        lista_pares = []
        for indice_par in indices.T:
            idx_par_1 = indice_par[0]
            idx_par_2 = indice_par[1]

            name_par_1 = target.universe.columns[idx_par_1]
            name_par_2 = target.universe.columns[idx_par_2]
            
            preco_par_1 = matriz_precos_pfp[name_par_1]
            preco_par_2 = matriz_precos_pfp[name_par_2]
            
            norm_par_1 = matriz_norm[name_par_1]
            norm_par_2 = matriz_norm[name_par_2]


            maximo_par_1 = preco_par_1.max(axis = 0)
            minimo_par_1 = preco_par_1.min(axis = 0)
            maximo_par_2 = preco_par_2.max(axis = 0)
            minimo_par_2 = preco_par_2.min(axis = 0)
            spread = norm_par_1 - norm_par_2
            std_spread = spread.std()
            par = (name_par_1, name_par_2,maximo_par_1, minimo_par_1, maximo_par_2, minimo_par_2, std_spread)
            lista_pares.append(par)
        
        target.temp["pares"] = lista_pares
        return 

class CriaPares(bt.Algo):
    def __init__(self, periodo_de_trocas_par_algos):
        super(CriaPares, self).__init__()
        self.pt_algos = periodo_de_trocas_par_algos

    def __call__(self, target):
        lista_pares = target.temp["pares"]
        target.temp["weights"] = {}
        for n1, n2, max1, min1, max2, min2, std_spread in lista_pares:
            pair_name = "%s_%s_%s" % (n1, n2, target.now.strftime("%m/%Y"))
            trade = bt.Strategy(pair_name, deepcopy(self.pt_algos), children = [n1, n2], parent = target)
            trade.setup_from_parent(pair_1 = n1, pair_2 = n2, max_1 = max1, min_1 = min1, max_2 = max2, min_2 = min2, std_spread = std_spread)
            target.temp["weights"][pair_name] = 0
        return True 

class AlocaPesosPares(bt.Algo):
    def __init__(self, pct_capital):
        super(AlocaPesosPares, self).__init__()
        self.pct_capital = pct_capital

    def __call__(self, target):
        weights = target.temp.get("weights")
        pair_capital = target.capital * self.pct_capital
        for pair_name in weights:
            target.allocate(pair_capital, child = pair_name, update = False) 
        
        target.update(target.now)     
        return True 