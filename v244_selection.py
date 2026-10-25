"""V24.4 bounded, evidence-grounded hypothesis recommendation (not proof)."""
from v24_discovery import analyze


def recommend(root):
    evidence = analyze(root)
    runs = evidence.get('runs', [])
    usable = [r for r in runs if r.get('record_count', 0) > 0]
    if not usable:
        return {'status': 'NO_EVIDENCE', 'recommendation': None,
                'message': 'Save a native playback trace before requesting a recommendation.',
                'rankings': []}
    # Prefer hypotheses with contradictory/insufficient evidence over those already
    # consistent on held-out data. Scores are priorities, NOT probabilities.
    priorities = {'CONTRADICTED': 4, 'NOT_PROPOSED': 3,
                  'INSUFFICIENT_VALIDATION': 2, 'CONSISTENT_WITH_OBSERVATIONS': 1,
                  'INSUFFICIENT_DISCOVERY': 0}
    ranked = []
    for h in evidence.get('hypotheses', []):
        key = h.get('key')
        if key not in ('unchanged_cell','zero_output','low_byte_preserved','parity_preserved'):
            continue
        status = h.get('status', 'INSUFFICIENT_DISCOVERY')
        ranked.append({'hypothesis': key, 'description': h.get('description',''),
                       'discovery_status': status, 'validation_records': h.get('validation_records',0),
                       'counterexamples': h.get('counterexamples',0),
                       'priority': priorities.get(status,0),
                       'reason': ('Observed counterexamples warrant an independent follow-up.' if status=='CONTRADICTED'
                                  else 'Not supported in discovery; test whether it holds under different conditions.' if status=='NOT_PROPOSED'
                                  else 'Independent validation is needed.' if status=='INSUFFICIENT_VALIDATION'
                                  else 'Additional independent evidence can stress-test the observed agreement.')})
    ranked.sort(key=lambda x:(-x['priority'], x['hypothesis']))
    return {'status':'RECOMMENDATION_AVAILABLE', 'recommendation':ranked[0] if ranked else None,
            'rankings':ranked, 'evidence_runs':len(usable),
            'message':'Heuristic follow-up priority based on saved recordings; not a statistical confidence score or proof.'}
