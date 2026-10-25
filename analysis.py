"""Pure, deterministic experiment comparison; baseline snapshots are not mutated."""
from collections import Counter
from math import log2, sqrt

def metrics(state):
    values=state.get('cells',[])
    n=len(values)
    if not n:return {'count':0,'mean':0,'entropy_bits':0,'unique_values':0,'channels':[0,0,0]}
    freq=Counter(values)
    return {'count':n,'mean':sum(values)/n,'entropy_bits':-sum((c/n)*log2(c/n) for c in freq.values()),'unique_values':len(freq),'channels':[sum((v>>shift)&255 for v in values)/n for shift in (16,8,0)]}

def compare(a,b,ma=None,mb=None):
    x,y=a.get('cells',[]),b.get('cells',[])
    n=min(len(x),len(y)); changes=[(i,x[i],y[i]) for i in range(n) if x[i]!=y[i]]
    differences=len(changes)+abs(len(x)-len(y))
    actions_a=(ma or {}).get('actions',[]);actions_b=(mb or {}).get('actions',[])
    ops=lambda actions:dict(sorted(Counter(str(z.get('operation','unknown')) for z in actions).items()))
    h=lambda state:[{'tick':r.get('tick'),'checksum':r.get('value'),'mean':r.get('mean')} for r in state.get('history',[]) if isinstance(r,dict)]
    return {'different_cells':differences,'cell_counts':[len(x),len(y)],'change_percent':round(100*differences/max(len(x),len(y),1),3),'ticks':[a.get('tick'),b.get('tick')], 'metrics':[metrics(a),metrics(b)],'mean_absolute_difference':sum(abs(u-v) for _,u,v in changes)/n if n else 0,'root_mean_square_difference':sqrt(sum((u-v)**2 for _,u,v in changes)/n) if n else 0,'changed_cell_samples':[{'index':i,'first':f'{u:06X}','second':f'{v:06X}'} for i,u,v in changes[:100]],'operations':[{'total':len(actions_a),'by_type':ops(actions_a)},{'total':len(actions_b),'by_type':ops(actions_b)}],'operation_sequences_equal':actions_a==actions_b,'histories':[h(a),h(b)],'history_note':'Historical curves require recorded history in the saved snapshot; absent history is not reconstructed.'}
