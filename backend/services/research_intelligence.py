from __future__ import annotations
import hashlib, re
from typing import Any

STOP=set('the a an and or of to in for on with by from is are was were this that using based system method model study research'.split())

def _terms(text: str) -> list[str]:
    words=re.findall(r'[A-Za-z][A-Za-z0-9-]{2,}', text.lower())
    counts={}
    for w in words:
        if w not in STOP: counts[w]=counts.get(w,0)+1
    return [w for w,_ in sorted(counts.items(), key=lambda x:(-x[1],x[0]))[:20]]

def synthesize(question: str, papers: list[dict[str,Any]]) -> dict[str,Any]:
    records=[]
    for i,p in enumerate(papers):
        title=str(p.get('title') or p.get('name') or f'Source {i+1}')
        abstract=str(p.get('abstract') or p.get('summary') or '')
        text=title+' '+abstract
        records.append({'source_id':'src-'+hashlib.sha256(text.encode()).hexdigest()[:12], 'title':title,
                        'year':p.get('year'), 'doi':p.get('doi',''), 'url':p.get('url') or p.get('source_url',''),
                        'terms':_terms(text), 'has_abstract':bool(abstract),
                        'evidence_status':'SOURCE_METADATA_ONLY'})
    alltext=' '.join(x['title']+' '+' '.join(x['terms']) for x in records)
    qterms=set(_terms(question))
    covered=[r for r in records if qterms.intersection(r['terms'])]
    gaps=[t for t in sorted(qterms) if not any(t in r['terms'] for r in records)]
    return {'question':question,'source_count':len(records),'relevant_source_count':len(covered),
            'sources':records,'dominant_terms':_terms(alltext),'coverage':round(len(covered)/max(1,len(records))*100,1),
            'uncovered_question_terms':gaps,'research_gaps':[
                {'type':'coverage_gap','term':g,'severity':'medium','action':'retrieve targeted literature'} for g in gaps],
            'truth_status':'LITERATURE_SYNTHESIS_REQUIRES_SOURCE_REVIEW'}
