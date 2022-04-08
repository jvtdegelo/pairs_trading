from copy import deepcopy
from future.utils import iteritems
from datetime import date, datetime
import pandas as pd
import numpy as np
import bt

class ChecaSeNaoFechouPar(bt.Algo):
    def __init__(self):
        super(ChecaSeNaoFechouPar, self).__init__()
    
    def __call__(self, target):
        return not target.perm["fechou_par"]

class ConfiguracaoInicial(bt.Algo):
    def __init__(self):
        super(ConfiguracaoInicial, self).__init__()
    
    def __call__(self, target):
        target.perm["data_inicial"] = target.now
        target.perm["estado"] = 0
        target.perm["fechou_par"] = False
        target.perm["std_spread"]=target.get_data("std_spread")
        return True

class Normaliza(bt.Algo):
    def __init__(self):
        super(Normaliza, self).__init__()

    def __call__(self, target):
        pair_1 = target.get_data("pair_1")
        pair_2 = target.get_data("pair_2")
        now = target.now
        price_1 = target.universe[pair_1][now]
        price_2 = target.universe[pair_2][now]
        max_1   = target.get_data("max_1")
        min_1   = target.get_data("min_1")
        max_2   = target.get_data("max_2")
        min_2   = target.get_data("min_2")
        
        target.temp["norm_1"] = (price_1 - min_1)/(max_1 - min_1)
        target.temp["norm_2"] = (price_2 - min_2)/(max_2 - min_2)
        
        target.temp["spread"] = target.temp["norm_1"] - target.temp["norm_2"]
        return True 
        
class ChecaSeAbre(bt.Algo):
    def __init__(self, limite):
        super(ChecaSeAbre, self).__init__()
        self.limite=limite

    def __call__(self, target):
        if target.perm["estado"] == 0 and target.temp["spread"]>2*target.perm["std_spread"]:
            target.perm["estado"] = 1
            return True

        if target.perm["estado"] == 0 and target.temp["spread"]<-2*target.perm["std_spread"]:
            target.perm["estado"] = -1
            return True

class ChecaSeFecha(bt.Algo):
    def __init__(self, limite):
        super(ChecaSeFecha, self).__init__()
        self.limite=limite

    def __call__(self, target):
        if target.perm["estado"] == 1 and target.temp["spread"]<0:
            target.perm["estado"] = 0
            return True

        if target.perm["estado"] == -1 and target.temp["spread"]>0:
            target.perm["estado"] = 0
            return True

        return False


class ChecaSeAberto(bt.Algo):
    def __init__(self):
        super(ChecaSeAberto, self).__init__()

    def __call__(self, target):
        if target.perm["estado"] != 0 :
            return True

        return False

class Abre(bt.Algo):
    def __init__(self, weight):
        super(Abre, self).__init__()
        self.weight = weight

    def __call__(self, target):
        if target.perm["estado"] == 1:
            target.temp["weights"] = {  target.get_data("pair_1") : -self.weight,
                                        target.get_data("pair_2") : self.weight}
        
        if target.perm["estado"] == -1:
            target.temp["weights"] = {  target.get_data("pair_1") : self.weight,
                                        target.get_data("pair_2") : -self.weight}
        
        return True


class Fecha(bt.Algo):
    def __init__(self):
        super(Fecha, self).__init__()

    def __call__(self, target):
        target.temp["weights"] = {  target.get_data("pair_1") : 0.,
                                    target.get_data("pair_2") : 0.}
        
        return True


class ChecaSeAcabouPeriodoDeTrocas(bt.Algo):
    def __init__(self, meses):
        super(ChecaSeAcabouPeriodoDeTrocas, self).__init__()
        self.meses = meses

    def __call__(self, target):
        if target.perm["data_inicial"] + pd.DateOffset(months=self.meses) <= target.now:
            return True

        return False

class ChecaSeFechado(bt.Algo):
    def __init__(self):
        super(ChecaSeFechado, self).__init__()

    def __call__(self, target):
        if target.perm["estado"] == 0:
            return True
        
        return False

class EncerraPar(bt.Algo):
    def __init__(self):
        super(EncerraPar, self).__init__()

    def __call__(self, target):
        if target.children and not target.bankrupt:
            target.flatten()
            target.update( target.now ) 

            if target.parent != target:
                capital = target.capital
                target.adjust(-capital, update=False, flow=True)
                target.parent.adjust(capital, update=True, flow=False)
                target.perm["fechou_par"] = True
        return False 