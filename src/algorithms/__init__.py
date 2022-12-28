from algorithms.cpop import CPOP, CPOPDelay, CPOPReserve, CPOPSBAC
from algorithms.heft import HEFT, HEFTDelay, HEFTReserve, HEFTSBAC
from algorithms.ippts import IPPTS, IPPTSDelay, IPPTSReserve, IPPTSSBAC

def get_scheduling_algorithm(algo, strategy=None):
    if strategy is not None and strategy not in ('delay', 'reserve', 'sbac'):
        raise ValueError('Not supported decorator')
    if strategy:
        algo = f'{algo}_{strategy}'
    if isinstance(algo, str):
        algo = {
            'heft': HEFT(),
            'heft_delay': HEFTDelay(),
            'heft_reserve': HEFTReserve(),
            'heft_sbac': HEFTSBAC(),
            'cpop': CPOP(),
            'cpop_delay': CPOPDelay(),
            'cpop_reserve': CPOPReserve(),
            'cpop_sbac': CPOPSBAC(),
            'ippts': IPPTS(),
            'ippts_delay': IPPTSDelay(),
            'ippts_reserve': IPPTSReserve(),
            # 'mem_first': MemFirst(),
        }[algo.lower()]
    return algo