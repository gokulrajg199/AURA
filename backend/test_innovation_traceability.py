from services.innovation_traceability import build_innovation_traceability

def test_innovation_to_validation_chain():
    p={
      'innovation': {'items':[{'id':'i1','text':'Adaptive model'}]},
      'requirements': [{'id':'r1','text':'Improve F1','innovation_id':'i1'}],
      'architecture': {'components':[{'id':'a1','text':'Inference service','requirement_id':'r1'}]},
      'development': {'components':[{'id':'d1','text':'Model implementation','architecture_id':'a1'}]},
      'dataset': {'items':[{'id':'ds1','text':'Training dataset','component_ids':['d1']}]},
      'experiments': {'plans':[{'id':'e1','text':'Ablation experiment','dataset_id':'ds1'}]},
      'validation': {'criteria':[{'id':'v1','text':'Validation review','result_id':'result:0'}]}
    }
    t=build_innovation_traceability(p,[{'id':'run1','metrics':{'f1':.9},'result_id':'r1'}])
    assert t['schema']=='6.1-innovation-traceability-1'
    assert t['counts']['innovation']==1
    assert any(e['source']=='innovation:i1' and e['target']=='requirement:r1' for e in t['edges'])
    assert t['review_required'] is True
