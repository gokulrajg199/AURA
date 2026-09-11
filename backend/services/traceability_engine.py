from __future__ import annotations
from typing import Any
from hashlib import sha256


def _items(project: dict[str, Any], key: str) -> list[dict[str, Any]]:
    v = project.get(key)
    if isinstance(v, list): return [x if isinstance(x, dict) else {'text': str(x)} for x in v]
    for section in ('analysis','research','innovation','solution','architecture','development','experiments','validation','deliverables'):
        d = project.get(section)
        if isinstance(d, dict) and isinstance(d.get(key), list):
            return [x if isinstance(x, dict) else {'text': str(x)} for x in d[key]]
    return []


def _id(prefix: str, obj: dict[str, Any], i: int) -> str:
    raw = str(obj.get('id') or obj.get(f'{prefix}_id') or obj.get('evidence_id') or obj.get('claim_id') or obj.get('finding_id') or obj.get('decision_id') or i)
    return f'{prefix}:{raw}'


def _text(obj: dict[str, Any]) -> str:
    for k in ('text','claim','finding','title','name','decision','description'):
        if obj.get(k): return str(obj[k])
    return ''


def build_traceability(project: dict[str, Any], executions: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    executions = executions or []
    evidence = _items(project, 'evidence')
    research = _items(project, 'papers')
    analysis = project.get('analysis') if isinstance(project.get('analysis'), dict) else {}
    claims = analysis.get('claim_register') or (project.get('research') or {}).get('claim_register') or (project.get('research') or {}).get('canonical_claims') or []
    findings = analysis.get('findings') or analysis.get('canonical_findings') or (project.get('research') or {}).get('canonical_findings') or (project.get('research') or {}).get('findings') or []
    decisions = analysis.get('decisions') or (project.get('research') or {}).get('decisions') or []
    innovation = _items(project, 'innovation')
    requirements = project.get('requirements') or []
    results = []
    for e in executions:
        if isinstance(e, dict) and (e.get('metrics') or e.get('results') or e.get('artifact_hashes')): results.append(e)
    nodes=[]; edges=[]
    def add(prefix, obj, i, status='UNKNOWN'):
        nid=_id(prefix,obj,i); nodes.append({'id':nid,'type':prefix,'label':_text(obj)[:180] or nid,'status':status,'provenance_hash':sha256(_text(obj).encode()).hexdigest() if _text(obj) else None}); return nid
    source_ids=[add('source',p,i,'SOURCE_RECORDED') for i,p in enumerate(research)]
    evidence_ids=[add('evidence',e,i,str(e.get('status','UNREVIEWED'))) for i,e in enumerate(evidence)]
    claim_ids=[add('claim',c,i,str(c.get('verification') or c.get('status') or 'REVIEW_REQUIRED')) for i,c in enumerate(claims if isinstance(claims,list) else [])]
    finding_ids=[add('finding',f,i,str(f.get('status','REVIEW_REQUIRED'))) for i,f in enumerate(findings if isinstance(findings,list) else [])]
    decision_ids=[add('decision',d,i,str(d.get('status','REVIEW_REQUIRED'))) for i,d in enumerate(decisions if isinstance(decisions,list) else [])]
    innovation_ids=[add('innovation',x,i,str(x.get('status','DEFINED'))) for i,x in enumerate(innovation)]
    req_ids=[add('requirement',{'text':r} if not isinstance(r,dict) else r,i,'DEFINED') for i,r in enumerate(requirements)]
    result_ids=[add('result',r,i,str(r.get('status','MEASURED'))) for i,r in enumerate(results)]
    # Explicit links supplied by records are preferred; otherwise only conservative structural links are asserted.
    all_nodes=nodes
    def explicit_links(obj, target_ids, source_id):
        for k in ('evidence_ids','evidence_id','source_ids','source_id','claim_ids','claim_id','finding_ids','finding_id','decision_ids','decision_id','requirement_ids','requirement_id','result_ids','result_id'):
            v=obj.get(k) if isinstance(obj,dict) else None
            vals=v if isinstance(v,list) else [v] if v else []
            for val in vals:
                s=str(val)
                for tid in target_ids:
                    if s in tid: edges.append({'source':source_id,'target':tid,'relationship':k})
    for i,c in enumerate(claims if isinstance(claims,list) else []): explicit_links(c,evidence_ids,claim_ids[i])
    for i,f in enumerate(findings if isinstance(findings,list) else []): explicit_links(f,claim_ids,finding_ids[i])
    for i,d in enumerate(decisions if isinstance(decisions,list) else []): explicit_links(d,finding_ids,decision_ids[i]); explicit_links(d,evidence_ids,decision_ids[i])
    for i,x in enumerate(innovation): explicit_links(x,decision_ids,innovation_ids[i]); explicit_links(x,finding_ids,innovation_ids[i])
    for i,r in enumerate(requirements):
        obj=r if isinstance(r,dict) else {'text':r}; explicit_links(obj,innovation_ids,req_ids[i]); explicit_links(obj,decision_ids,req_ids[i])
    for i,r in enumerate(results): explicit_links(r,req_ids,result_ids[i]); explicit_links(r,claim_ids,result_ids[i])
    # Source -> evidence is only asserted when the evidence explicitly names/references the source.
    for i,e in enumerate(evidence): explicit_links(e,source_ids,evidence_ids[i])
    types=['source','evidence','claim','finding','decision','innovation','requirement','result']
    counts={t:sum(1 for n in nodes if n['type']==t) for t in types}
    linked=set();
    for edge in edges: linked.add(edge['target']); linked.add(edge['source'])
    coverage=round((len(linked)/len(nodes))*100,1) if nodes else 0.0
    return {'schema':'6.1-traceability-1','nodes':nodes,'edges':edges,'counts':counts,'coverage_percent':coverage,'orphan_nodes':[n['id'] for n in nodes if n['id'] not in linked],'truth_status':'TRACEABILITY_RECORDS_ASSERTED_LINKS_ONLY; MISSING_LINKS ARE NOT INFERRED AS SCIENTIFIC FACTS.','review_required':True}
