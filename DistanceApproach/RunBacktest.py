import pandas as pd
import numpy as np
import bt
from AlgosPeriodoDeTrocas import *
from AlgosPeriodoDeFormacaoDosPares import *

def run_backtest(data): 
    ConfiguraPar        = bt.AlgoStack(bt.algos.RunOnce(), ConfiguracaoInicial())
    NormalizaPar        = bt.AlgoStack(ChecaSeNaoFechouPar(), Normaliza())
    AbrePosicao         = bt.AlgoStack(ChecaSeAbre(5.), Abre(1.), bt.algos.Rebalance())
    FechaPosicao        = bt.AlgoStack(ChecaSeFecha(5.), Fecha(), bt.algos.Rebalance())
    FechaPosicaoFim     = bt.AlgoStack(ChecaSeAberto(), Fecha(), bt.algos.Rebalance())
    FimPeriodoDeTrocas  = bt.AlgoStack(ChecaSeAcabouPeriodoDeTrocas(6), bt.algos.Or([ChecaSeFechado(), FechaPosicaoFim]), EncerraPar())
    
    PeriodoDeTrocasPar  = [
        bt.algos.Or([ConfiguraPar, NormalizaPar]),
        bt.algos.Or([AbrePosicao, FechaPosicao, FimPeriodoDeTrocas])
    ]
    
    ChecaSelecionaPares = bt.algos.Or([bt.AlgoStack(bt.algos.RunOnce(), ConfiguracaoInicialEstrategia()), ChecaSeEscolhePares()])
    PeriodoSelecaoPares = [
        ChecaSelecionaPares, 
        SelecionaPares(10),
        CriaPares(PeriodoDeTrocasPar),
        AlocaPesosPares(0.1)
    ]
    
    strategy = bt.Strategy("PairsTradingDistanceApproach", PeriodoSelecaoPares)
    test = bt.Backtest(strategy, data)
    out = bt.run(test)
    print(out.stats)
    return out