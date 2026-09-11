from services.traceability_engine import build_traceability

def test_traceability_conservative_links():
    p = {
        'project_name':'x',
        'requirements':['r1'],
        'evidence':[{'evidence_id':'ev1','title':'E','status':'APPROVED'}],
        'analysis': {
            'claim_register':[{'claim_id':'c1','text':'claim','evidence_ids':['ev1']}],
            'findings':[{'finding_id':'f1','text':'finding','claim_ids':['c1']}],
            'decisions':[{'decision_id':'d1','decision':'use approach','finding_ids':['f1']}]
        },
        'innovation':[{'id':'i1','title':'innovation','decision_ids':['d1']}]
    }
    t = build_traceability(p, [])
    assert any(e['source']=='claim:c1' and e['target']=='evidence:ev1' for e in t['edges'])
    assert any(e['source']=='finding:f1' and e['target']=='claim:c1' for e in t['edges'])
    assert any(e['source']=='decision:d1' and e['target']=='finding:f1' for e in t['edges'])
    assert t['review_required'] is True
