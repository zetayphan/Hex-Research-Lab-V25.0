"""Observational metrics. No proof of full-engine conservation or reversibility."""
def summarize_state(s):
    values=s.get('values',[])
    n=len(values)
    rgb=[sum((v>>shift)&255 for v in values) for shift in (16,8,0)]
    distinct=len(set(values))
    transitions=sum(a!=b for a,b in zip(values,values[1:]))
    # Observable proxies only: not Jacobian rank or topological dimension.
    adjacent_gradient=sum(sum(abs(((a>>k)&255)-((b>>k)&255)) for k in (16,8,0)) for a,b in zip(values,values[1:]))
    return {'tick':s.get('tick',0),'cells':n,'rgb_totals':rgb,'total_rgb':sum(rgb),
        'distinct_hex_values':distinct,'adjacent_value_transitions':transitions,
        'adjacent_rgb_gradient':adjacent_gradient,
        'checksum':s.get('checksum'), 'dimension':s.get('dimension'),
        'metrics_note':'Observational proxies. RGB totals may change during full engine steps; no Jacobian rank, inverse, or PDE validation is claimed.'}
