"""SQuAD-style exact match and token F1 (maximum over reference answers)."""
import re
import string
from collections import Counter

def normalize(text):
    text = ''.join(c for c in (text or '').lower() if c not in string.punctuation)
    return ' '.join(re.sub(r'\b(a|an|the)\b', ' ', text).split())

def score_answer(prediction, references):
    p = normalize(prediction)
    refs = references or ['']
    em, f1 = 0., 0.
    for reference in refs:
        r = normalize(reference)
        em = max(em, float(p == r))
        pt, rt = p.split(), r.split()
        common = sum((Counter(pt) & Counter(rt)).values())
        value = float(pt == rt) if not pt or not rt else 2*common/(len(pt)+len(rt))
        f1 = max(f1, value)
    return em, f1

def summarize(rows):
    def group(items):
        return {'count':len(items), 'exact_match':100*sum(r['em'] for r in items)/max(1,len(items)),
                'f1':100*sum(r['f1'] for r in items)/max(1,len(items))}
    return {'overall':group(rows), 'answerable':group([r for r in rows if r['references']]),
            'unanswerable':group([r for r in rows if not r['references']])}
