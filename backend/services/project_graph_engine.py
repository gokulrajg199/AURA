from __future__ import annotations
from typing import Any

def build_graph(project: dict[str,Any], lifecycle: dict[str,Any], executions: list[dict[str,Any]]) -> dict[str,Any]:
    nodes=[]; edges=[]
    def add(kind, key, label, status='context'):
        nodes.append({'id':key,'type':kind,'label':label,'status':status})
    add('project','project',project.get('project_name','AURA Project'),'active')
    for s in lifecycle.get('stages',[]):
        sid='stage:'+str(s['key']); add('lifecycle',sid,s['label'],s.get('status','pending'))
    for i,s in enumerate(lifecycle.get('stages',[])):
        sid='stage:'+str(s['key']); edges.append({'source':'project' if i==0 else 'stage:'+str(lifecycle['stages'][i-1]['key']),'target':sid,'relation':'lifecycle'})
    for i,e in enumerate(project.get('evidence') or []):
        eid='evidence:'+str(e.get('evidence_id') or i); add('evidence',eid,e.get('title') or e.get('source') or f'Evidence {i+1}',str(e.get('status','UNREVIEWED')).lower())
        edges.append({'source':eid,'target':'stage:research','relation':'supports'})
    for i,e in enumerate(executions):
        xid='execution:'+str(e.get('execution_id') or i); add('execution',xid,e.get('task','execution'),str(e.get('status','unknown')).lower())
        edges.append({'source':'stage:experiment','target':xid,'relation':'executed'})
    return {'nodes':nodes,'edges':edges,'node_count':len(nodes),'edge_count':len(edges),
            'provenance':True,'truth_status':'GRAPH_DERIVED_FROM_PROJECT_STATE_AND_EXECUTION_RECORDS'}
