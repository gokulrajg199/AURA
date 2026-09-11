from __future__ import annotations
import json, subprocess, sys, time, uuid
from datetime import datetime, timezone
from pathlib import Path
import os
from typing import Any
from services.database import save_execution, load_executions

BASE_DIR = Path(os.getenv("AURA_DATA_DIR", str(Path(__file__).resolve().parents[1] / "data"))) / "project_workspaces"

def now() -> str: return datetime.now(timezone.utc).isoformat()

def infer_profile(project: dict[str, Any]) -> str:
    text = " ".join(map(str, [project.get("original_idea", ""), project.get("analysis", {}), project.get("solution", {}), project.get("architecture", {})])).lower()
    # Resolve the dominant execution modality from the idea first. This prevents
    # broad architecture text (for example IoT modules in a plant system) from
    # incorrectly overriding an explicitly computer-vision project.
    idea = str(project.get("original_idea", "")).lower()
    if any(x in idea for x in ["computer vision", "plant disease", "object detection", "image classification", "image recognition"]): return "computer_vision"
    if any(x in idea for x in ["hydroponic", "nutrient prediction", "sensor data", "iot", "ph sensor", "ec sensor", "tds sensor", "smart agriculture"]): return "iot"
    if any(x in text for x in ["computer vision", "plant disease", "object detection", "image classification", "image recognition"]): return "computer_vision"
    if any(x in text for x in ["hydroponic", "nutrient prediction", "sensor data", "iot", "ph sensor", "ec sensor", "tds sensor", "smart agriculture"]): return "iot"
    if any(x in text for x in ["nlp", "language model", "text classification"]): return "nlp"
    return "general_ai"

def _apply_iot_files(files: dict[str, str]) -> None:
    files["requirements.txt"] = "numpy>=1.26\npandas>=2.2\nscikit-learn>=1.4\njoblib>=1.3\n"
    files["src/sensors.py"] = '''from dataclasses import dataclass, asdict\nfrom typing import Any\n\n@dataclass\nclass SensorReading:\n    timestamp: str\n    ph: float\n    ec: float\n    tds: float\n    temperature: float\n    humidity: float\n    def to_dict(self) -> dict[str, Any]: return asdict(self)\n\ndef validate_reading(r: SensorReading) -> None:\n    if not 0 <= r.ph <= 14: raise ValueError("pH must be between 0 and 14")\n    if r.ec < 0 or r.tds < 0: raise ValueError("EC/TDS cannot be negative")\n    if not -20 <= r.temperature <= 80: raise ValueError("temperature outside supported range")\n    if not 0 <= r.humidity <= 100: raise ValueError("humidity must be 0..100")\n'''
    files["src/prediction.py"] = '''from pathlib import Path
import os\nFEATURES=["ph","ec","tds","temperature","humidity"]\nTARGET="nutrient_target"\n\ndef load_dataset(path):\n    import pandas as pd\n    df=pd.read_csv(path); missing=[c for c in FEATURES+[TARGET] if c not in df.columns]\n    if missing: raise ValueError(f"Missing required columns: {missing}")\n    df=df[FEATURES+[TARGET]].dropna()\n    if df.empty: raise ValueError("No usable rows after cleaning")\n    return df\n\ndef train_models(csv_path,out_dir):\n    from sklearn.ensemble import RandomForestRegressor, HistGradientBoostingRegressor\n    from sklearn.model_selection import train_test_split\n    import joblib,json\n    df=load_dataset(csv_path); X=df[FEATURES]; y=df[TARGET]\n    Xtr,Xte,ytr,yte=train_test_split(X,y,test_size=.2,random_state=42)\n    baseline=RandomForestRegressor(n_estimators=100,random_state=42,n_jobs=-1)\n    proposed=HistGradientBoostingRegressor(random_state=42)\n    baseline.fit(Xtr,ytr); proposed.fit(Xtr,ytr)\n    out=Path(out_dir); out.mkdir(parents=True,exist_ok=True)\n    joblib.dump(baseline,out/"baseline.joblib"); joblib.dump(proposed,out/"proposed.joblib")\n    (out/"training_metadata.json").write_text(json.dumps({"rows":len(df),"features":FEATURES,"target":TARGET,"test_rows":len(Xte),"scientific_result":False,"review_required":True},indent=2),encoding="utf-8")\n'''
    files["src/evaluation.py"] = '''import numpy as np\nfrom sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score\ndef regression_metrics(y_true,y_pred):\n    return {"mae":float(mean_absolute_error(y_true,y_pred)),"rmse":float(np.sqrt(mean_squared_error(y_true,y_pred))),"r2":float(r2_score(y_true,y_pred))}\n'''
    files["src/pipeline.py"] = '''from pathlib import Path
import os\ndef run_pipeline(input_value): return {"input":input_value,"status":"ready","stages":["sensor_ingest","validate","preprocess","predict","evaluate"]}\ndef validate_project_layout(root:Path):\n    required=[root/"src",root/"tests",root/"scripts",root/"data",root/"models",root/"artifacts"]\n    return {"valid":all(p.exists() for p in required),"checked":[str(p.relative_to(root)) for p in required]}\n'''
    files["tests/test_pipeline.py"] = '''import unittest\nfrom pathlib import Path
import os\nfrom src.pipeline import run_pipeline,validate_project_layout\nfrom src.sensors import SensorReading,validate_reading\nclass TestHydroponicPipeline(unittest.TestCase):\n    def test_pipeline_smoke(self): self.assertEqual(run_pipeline("AURA_SMOKE_SENSOR")["status"],"ready")\n    def test_sensor_validation(self): validate_reading(SensorReading("SMOKE",6.2,1.4,700,24,65))\n    def test_project_layout(self): self.assertTrue(validate_project_layout(Path(__file__).resolve().parents[1])["valid"])\nif __name__ == "__main__": unittest.main()\n'''
    files["scripts/smoke_test.py"] = '''import json,sys\nfrom pathlib import Path
import os\nROOT=Path(__file__).resolve().parents[1]; sys.path.insert(0,str(ROOT)); (ROOT/"artifacts").mkdir(exist_ok=True)\nfrom src.pipeline import run_pipeline,validate_project_layout\nfrom src.sensors import SensorReading,validate_reading\nr=SensorReading("AURA_SMOKE_ONLY",6.2,1.4,700,24,65); validate_reading(r)\nout={"status":"EXECUTED","mode":"CONTROLLED_SMOKE_TEST","sensor_schema":r.to_dict(),"pipeline":run_pipeline(r.to_dict()),"workspace_layout":validate_project_layout(ROOT),"scientific_result":False,"review_required":True,"truth_note":"Synthetic smoke input only; not scientific hydroponic evidence."}\n(ROOT/"artifacts"/"smoke_test.json").write_text(json.dumps(out,indent=2),encoding="utf-8"); print(json.dumps(out,indent=2))\n'''
    files["scripts/project_test.py"] = '''import json,subprocess,sys\nfrom pathlib import Path
import os\nROOT=Path(__file__).resolve().parents[1]; ART=ROOT/"artifacts"; ART.mkdir(exist_ok=True)\np=subprocess.run([sys.executable,"-m","unittest","discover","-s","tests","-p","test_*.py"],cwd=ROOT,capture_output=True,text=True,shell=False)\nout={"status":"EXECUTED" if p.returncode==0 else "FAILED","exit_code":p.returncode,"stdout":p.stdout[-8000:],"stderr":p.stderr[-8000:],"scientific_result":False,"review_required":True,"truth_note":"Automated code tests verify implementation behavior only; they are not scientific model validation."}\n(ART/"project_test.json").write_text(json.dumps(out,indent=2),encoding="utf-8"); print(json.dumps(out,indent=2)); sys.exit(p.returncode)\n'''
    files["scripts/dataset_prepare.py"] = '''from pathlib import Path
import os\nimport json,sys\nROOT=Path(__file__).resolve().parents[1]; ART=ROOT/"artifacts"; ART.mkdir(exist_ok=True); DATA=ROOT/"data"/"sensor_data.csv"\nrequired=["timestamp","ph","ec","tds","temperature","humidity","nutrient_target"]\nif not DATA.exists(): result={"status":"BLOCKED","reason":"Place an approved data/sensor_data.csv with columns: "+", ".join(required),"scientific_result":False}\nelse:\n import pandas as pd\n df=pd.read_csv(DATA); missing=[c for c in required if c not in df.columns]\n result={"status":"READY" if len(df)>0 and not missing else "BLOCKED","rows":len(df),"missing_columns":missing,"scientific_result":False}\n(ART/"dataset_status.json").write_text(json.dumps(result,indent=2),encoding="utf-8"); print(json.dumps(result,indent=2)); sys.exit(0 if result["status"]=="READY" else 2)\n'''
    files["scripts/train_model.py"] = '''from pathlib import Path
import os\nimport json,sys\nROOT=Path(__file__).resolve().parents[1]; DATA=ROOT/"data"/"sensor_data.csv"; ART=ROOT/"artifacts"; ART.mkdir(exist_ok=True)\nif not DATA.exists(): result={"status":"BLOCKED","trained":False,"reason":"Approved data/sensor_data.csv is required.","scientific_result":False}\nelse:\n try:\n  from src.prediction import train_models\n  train_models(DATA,ROOT/"models"); result={"status":"EXECUTED","trained":True,"scientific_result":False,"review_required":True}\n except Exception as exc: result={"status":"FAILED","trained":False,"error":str(exc),"scientific_result":False}\n(ART/"training_status.json").write_text(json.dumps(result,indent=2),encoding="utf-8"); print(json.dumps(result,indent=2)); sys.exit(0 if result["status"]=="EXECUTED" else 2)\n'''
    files["scripts/baseline_evaluate.py"] = '''from pathlib import Path
import os\nimport json,sys\nROOT=Path(__file__).resolve().parents[1]; ART=ROOT/"artifacts"; DATA=ROOT/"data"/"sensor_data.csv"; MODEL=ROOT/"models"/"baseline.joblib"; ART.mkdir(exist_ok=True)\nif not DATA.exists() or not MODEL.exists(): result={"status":"BLOCKED","metrics_available":False,"metrics":{},"reason":"Approved sensor_data.csv and executed baseline.joblib are required.","scientific_result":False}\nelse:\n try:\n  import joblib\n  from src.prediction import load_dataset,FEATURES,TARGET\n  from src.evaluation import regression_metrics\n  df=load_dataset(DATA); m=joblib.load(MODEL); result={"status":"EXECUTED","metrics_available":True,"metrics":regression_metrics(df[TARGET],m.predict(df[FEATURES])),"scientific_result":True,"review_required":True}\n except Exception as exc: result={"status":"FAILED","metrics_available":False,"metrics":{},"error":str(exc),"scientific_result":False}\n(ART/"baseline_evaluation.json").write_text(json.dumps(result,indent=2),encoding="utf-8"); print(json.dumps(result,indent=2)); sys.exit(0 if result["status"]=="EXECUTED" else 2)\n'''
    files["scripts/evaluate_model.py"] = files["scripts/baseline_evaluate.py"].replace("baseline.joblib","proposed.joblib").replace("baseline_evaluation.json","evaluation.json")
    files["data/README.md"] = "# Approved Hydroponic Sensor Dataset\n\nPlace approved sensor_data.csv here with: timestamp, ph, ec, tds, temperature, humidity, nutrient_target.\n\nAURA never fabricates scientific data.\n"
    files["models/README.md"] = "Models are created only from an approved sensor dataset. No fabricated weights or metrics.\n"

def build_workspace(project: dict[str, Any]) -> dict[str, Any]:
    project_id = str(project["project_id"]); root = BASE_DIR / project_id; root.mkdir(parents=True, exist_ok=True)
    profile = infer_profile(project)
    from services.universal_execution import build_contract as _build_contract
    contract = _build_contract(project)
    files = {
      "README.md": f"# {project.get('project_name','AURA Project')}\n\nGenerated by AURA Build & Execution Core.\n\nIdea: {project.get('original_idea','')}\nProfile: {profile}\n\nScientific claims are never fabricated. Training/evaluation require approved data and an approved runtime.\n",
      "aura_project.json": json.dumps(project, indent=2, ensure_ascii=False),
      "requirements.txt": "ultralytics>=8.3.0\npyyaml>=6.0\nPillow>=10.0\nnumpy>=1.26\nopencv-python-headless>=4.9\nscikit-learn>=1.4\n",
      "src/__init__.py": "",
      "src/config.py": f"PROJECT_ID = {project_id!r}\nPROFILE = {profile!r}\n",
      "src/vision.py": """from pathlib import Path
import os\nfrom typing import Any\n\ndef inspect_image(image_path: str | Path) -> dict[str, Any]:\n    # Real image loading/preprocessing path. Model inference is intentionally\n    # gated until an approved trained model is supplied.\n    try:\n        from PIL import Image\n    except ImportError as exc:\n        raise RuntimeError('Pillow is required for image inspection.') from exc\n    path = Path(image_path)\n    if not path.exists():\n        raise FileNotFoundError(path)\n    with Image.open(path) as image:\n        rgb = image.convert('RGB')\n        return {\n            'path': str(path),\n            'width': rgb.width,\n            'height': rgb.height,\n            'mode': rgb.mode,\n        }\n\ndef predict_image(image_path: str | Path, weights: str | Path = 'models/base.pt') -> dict[str, Any]:\n    weights_path = Path(weights)\n    if not weights_path.exists():\n        return {\n            'status': 'BLOCKED',\n            'prediction_available': False,\n            'reason': 'Approved model weights are required before inference.',\n            'scientific_result': False,\n            'image': inspect_image(image_path),\n        }\n    try:\n        from ultralytics import YOLO\n    except ImportError as exc:\n        raise RuntimeError('Ultralytics is required for YOLO inference.') from exc\n    model = YOLO(str(weights_path))\n    results = model.predict(source=str(image_path), verbose=False)\n    return {\n        'status': 'EXECUTED',\n        'prediction_available': True,\n        'detections': int(sum(len(r.boxes) if r.boxes is not None else 0 for r in results)),\n        'scientific_result': False,\n        'review_required': True,\n    }\n""",
      "src/pipeline.py": """from pathlib import Path
import os\n\ndef run_pipeline(input_value):\n    return {\n        'input': input_value,\n        'status': 'ready',\n        'stages': ['load', 'preprocess', 'infer', 'postprocess'],\n    }\n\ndef validate_project_layout(root: Path):\n    required = [root/'src', root/'tests', root/'scripts', root/'data', root/'models', root/'artifacts']\n    return {'valid': all(p.exists() for p in required), 'checked': [str(p.relative_to(root)) for p in required]}\n""",
      "tests/__init__.py": "",
      "tests/test_pipeline.py": """import unittest\nfrom pathlib import Path
import os\nfrom src.pipeline import run_pipeline, validate_project_layout\n\nclass TestAURAPipeline(unittest.TestCase):\n    def test_pipeline_smoke(self): self.assertEqual(run_pipeline('AURA_SMOKE_INPUT')['status'], 'ready')\n    def test_project_layout(self): self.assertTrue(validate_project_layout(Path(__file__).resolve().parents[1])['valid'])\n\nif __name__ == '__main__': unittest.main()\n""",
      "scripts/smoke_test.py": """import json, sys\nfrom pathlib import Path
import os\nROOT=Path(__file__).resolve().parents[1]\n(ROOT/'artifacts').mkdir(exist_ok=True)\nsys.path.insert(0, str(ROOT))\nfrom src.pipeline import run_pipeline, validate_project_layout\n\nresult = {\n    'status': 'EXECUTED',\n    'mode': 'CONTROLLED_SMOKE_TEST',\n    'project_pipeline': run_pipeline('AURA_SMOKE_INPUT'),\n    'workspace_layout': validate_project_layout(ROOT),\n    'scientific_result': False,\n    'review_required': True,\n    'truth_note': 'Smoke execution verifies generated code and workspace wiring only; it is not plant-disease model validation.'\n}\n(ROOT/'artifacts').mkdir(exist_ok=True)\n(ROOT/'artifacts'/'smoke_test.json').write_text(json.dumps(result, indent=2), encoding='utf-8')\nprint(json.dumps(result, indent=2))\n""",
      "scripts/project_test.py": """import json, subprocess, sys
from pathlib import Path
import os
ROOT=Path(__file__).resolve().parents[1]; ART=ROOT/"artifacts"; ART.mkdir(exist_ok=True)
p=subprocess.run([sys.executable, "-m", "unittest", "discover", "-s", "tests", "-p", "test_*.py"], cwd=ROOT, capture_output=True, text=True, shell=False)
out={"status":"EXECUTED" if p.returncode==0 else "FAILED","exit_code":p.returncode,"stdout":p.stdout[-8000:],"stderr":p.stderr[-8000:],"scientific_result":False,"review_required":True,"truth_note":"Automated implementation tests are not scientific validation."}
(ART/"project_test.json").write_text(json.dumps(out,indent=2),encoding="utf-8"); print(json.dumps(out,indent=2)); sys.exit(p.returncode)
""",
      "scripts/dataset_prepare.py": '''from pathlib import Path
import os\nimport json, sys\nROOT=Path(__file__).resolve().parents[1]; DATA=ROOT/'data'; ART=ROOT/'artifacts'; ART.mkdir(exist_ok=True)\nconfig=DATA/'dataset.yaml'\nimages=[p for p in DATA.rglob('*') if p.suffix.lower() in {'.jpg','.jpeg','.png','.bmp','.webp'}]\nresult={'status':'READY' if config.exists() else 'BLOCKED','dataset_yaml':str(config),'image_files_found':len(images),'approved_dataset':config.exists(),'scientific_result':False}\nif not config.exists(): result['reason']='Place an approved YOLO dataset configuration at data/dataset.yaml. AURA will not invent a dataset.'\n(ART/'dataset_status.json').write_text(json.dumps(result,indent=2),encoding='utf-8'); print(json.dumps(result,indent=2)); sys.exit(0 if config.exists() else 2)\n''',
      "scripts/train_model.py": '''from pathlib import Path
import os\nimport json, sys\nROOT=Path(__file__).resolve().parents[1]; DATA=ROOT/'data'/'dataset.yaml'; MODEL=ROOT/'models'/'base.pt'; ART=ROOT/'artifacts'; ART.mkdir(exist_ok=True)\nif not DATA.exists(): result={'status':'BLOCKED','trained':False,'reason':'Approved data/dataset.yaml is required.','scientific_result':False}; (ART/'training_status.json').write_text(json.dumps(result,indent=2)); print(json.dumps(result,indent=2)); sys.exit(2)\ntry: from ultralytics import YOLO\nexcept Exception as exc: result={'status':'BLOCKED','trained':False,'reason':'Ultralytics is not installed in the approved environment.','error':str(exc),'scientific_result':False}; (ART/'training_status.json').write_text(json.dumps(result,indent=2)); print(json.dumps(result,indent=2)); sys.exit(2)\nif not MODEL.exists(): result={'status':'BLOCKED','trained':False,'reason':'Approved base weights are required at models/base.pt.','scientific_result':False}; (ART/'training_status.json').write_text(json.dumps(result,indent=2)); print(json.dumps(result,indent=2)); sys.exit(2)\ntry:\n model=YOLO(str(MODEL)); run=model.train(data=str(DATA),epochs=10,imgsz=640,project=str(ART),name='aura_plant_disease',exist_ok=True); result={'status':'EXECUTED','trained':True,'run':str(getattr(run,'save_dir','')),'scientific_result':False,'review_required':True}\nexcept Exception as exc: result={'status':'FAILED','trained':False,'reason':'Training failed.','error':str(exc),'scientific_result':False}\n(ART/'training_status.json').write_text(json.dumps(result,indent=2)); print(json.dumps(result,indent=2)); sys.exit(0 if result['status']=='EXECUTED' else 2)\n''',
      "scripts/evaluate_model.py": '''from pathlib import Path
import os\nimport json, sys\nROOT=Path(__file__).resolve().parents[1]; DATA=ROOT/'data'/'dataset.yaml'; WEIGHTS=ROOT/'artifacts'/'aura_plant_disease'/'weights'/'best.pt'; ART=ROOT/'artifacts'; ART.mkdir(exist_ok=True)\nif not DATA.exists() or not WEIGHTS.exists(): result={'status':'BLOCKED','metrics_available':False,'metrics':{},'reason':'Evaluation requires dataset.yaml and executed best.pt weights.','scientific_result':False}; (ART/'evaluation.json').write_text(json.dumps(result,indent=2)); print(json.dumps(result,indent=2)); sys.exit(2)\ntry:\n from ultralytics import YOLO\n model=YOLO(str(WEIGHTS)); m=model.val(data=str(DATA),split='test'); result={'status':'EXECUTED','metrics_available':True,'metrics':{'map50':float(m.box.map50),'map50_95':float(m.box.map),'precision':float(m.box.mp),'recall':float(m.box.mr)},'scientific_result':True,'review_required':True}\nexcept Exception as exc: result={'status':'FAILED','metrics_available':False,'metrics':{},'reason':'Evaluation failed.','error':str(exc),'scientific_result':False}\n(ART/'evaluation.json').write_text(json.dumps(result,indent=2)); print(json.dumps(result,indent=2)); sys.exit(0 if result['status']=='EXECUTED' else 2)\n''',
      "scripts/baseline_evaluate.py": '''from pathlib import Path
import os
import json, sys
ROOT=Path(__file__).resolve().parents[1]; DATA=ROOT/'data'/'dataset.yaml'; WEIGHTS=ROOT/'models'/'baseline.pt'; ART=ROOT/'artifacts'; ART.mkdir(exist_ok=True)
if not DATA.exists() or not WEIGHTS.exists():
 result={'status':'BLOCKED','metrics_available':False,'metrics':{},'reason':'Baseline evaluation requires approved data/dataset.yaml and models/baseline.pt. AURA will not invent a baseline.','scientific_result':False}
else:
 try:
  from ultralytics import YOLO
  model=YOLO(str(WEIGHTS)); m=model.val(data=str(DATA),split='test')
  result={'status':'EXECUTED','metrics_available':True,'metrics':{'map50':float(m.box.map50),'map50_95':float(m.box.map),'precision':float(m.box.mp),'recall':float(m.box.mr)},'scientific_result':True,'review_required':True}
 except Exception as exc:
  result={'status':'FAILED','metrics_available':False,'metrics':{},'reason':'Baseline evaluation failed.','error':str(exc),'scientific_result':False}
(ART/'baseline_evaluation.json').write_text(json.dumps(result,indent=2)); print(json.dumps(result,indent=2)); sys.exit(0 if result['status']=='EXECUTED' else 2)
''',
      "scripts/experiment_runner.py": '''import json, subprocess, sys\nfrom pathlib import Path
import os\nROOT=Path(__file__).resolve().parents[1]; ART=ROOT/'artifacts'; ART.mkdir(exist_ok=True)\nrecords=[]\nfor name in ['dataset_prepare.py','baseline_evaluate.py','train_model.py','evaluate_model.py']:\n p=subprocess.run([sys.executable,str(ROOT/'scripts'/name)],cwd=ROOT,capture_output=True,text=True,shell=False); records.append({'task':name,'exit_code':p.returncode,'stdout':p.stdout[-8000:],'stderr':p.stderr[-8000:]})\n if p.returncode: break\nresult={'status':'EXECUTED' if records and all(x['exit_code']==0 for x in records) else 'BLOCKED_OR_FAILED','steps':records,'scientific_validation':False,'review_required':True}\n(ART/'experiment_run.json').write_text(json.dumps(result,indent=2),encoding='utf-8'); print(json.dumps(result,indent=2)); sys.exit(0 if result['status']=='EXECUTED' else 2)\n''',
      "execution_manifest.json": json.dumps({"allowed_tasks":["smoke_test","project_test","dataset_prepare","train_model","evaluate_model","baseline_evaluate","experiment_run"],"shell":False,"timeout_seconds":300},indent=2)
    }
    if profile == 'computer_vision':
        # Explicit development-only path: verifies the CV workflow without
        # turning synthetic values into scientific evidence.
        files["scripts/dataset_prepare.py"] = '''from pathlib import Path
import os
import json, os, sys
ROOT=Path(__file__).resolve().parents[1]; ART=ROOT/'artifacts'; ART.mkdir(exist_ok=True)
fixture=os.getenv('AURA_DEVELOPMENT_FIXTURE')=='1'; config=ROOT/'data'/'dataset.yaml'
images=[p for p in (ROOT/'data').rglob('*') if p.suffix.lower() in {'.jpg','.jpeg','.png','.bmp','.webp'}]
if fixture: result={'status':'READY','dataset_yaml':str(config),'image_files_found':0,'approved_dataset':False,'scientific_result':False,'development_fixture':True,'reason':'Development verification fixture; no scientific CV dataset supplied.'}
elif config.exists(): result={'status':'READY','dataset_yaml':str(config),'image_files_found':len(images),'approved_dataset':True,'scientific_result':False,'review_required':True}
else: result={'status':'BLOCKED','dataset_yaml':str(config),'image_files_found':len(images),'approved_dataset':False,'scientific_result':False,'reason':'Place an approved YOLO dataset configuration at data/dataset.yaml. AURA will not invent a dataset.'}
(ART/'dataset_status.json').write_text(json.dumps(result,indent=2),encoding='utf-8'); print(json.dumps(result,indent=2)); sys.exit(0 if result['status']=='READY' else 2)
'''
        files["scripts/train_model.py"] = '''from pathlib import Path
import os
import json, os, sys
ROOT=Path(__file__).resolve().parents[1]; ART=ROOT/'artifacts'; ART.mkdir(exist_ok=True)
if os.getenv('AURA_DEVELOPMENT_FIXTURE')=='1': result={'status':'EXECUTED','trained':True,'development_fixture':True,'scientific_result':False,'review_required':True,'model_artifact':'DEVELOPMENT_FIXTURE_ONLY','reason':'Controlled engineering fixture; no real weights or scientific training result.'}
else:
 DATA=ROOT/'data'/'dataset.yaml'; MODEL=ROOT/'models'/'base.pt'
 if not DATA.exists(): result={'status':'BLOCKED','trained':False,'reason':'Approved data/dataset.yaml is required.','scientific_result':False}
 elif not MODEL.exists(): result={'status':'BLOCKED','trained':False,'reason':'Approved base weights are required at models/base.pt.','scientific_result':False}
 else:
  try:
   from ultralytics import YOLO
   model=YOLO(str(MODEL)); run=model.train(data=str(DATA),epochs=10,imgsz=640,project=str(ART),name='aura_plant_disease',exist_ok=True); result={'status':'EXECUTED','trained':True,'run':str(getattr(run,'save_dir','')),'scientific_result':False,'review_required':True}
  except Exception as exc: result={'status':'FAILED','trained':False,'reason':'Training failed.','error':str(exc),'scientific_result':False}
(ART/'training_status.json').write_text(json.dumps(result,indent=2),encoding='utf-8'); print(json.dumps(result,indent=2)); sys.exit(0 if result['status']=='EXECUTED' else 2)
'''
        files["scripts/baseline_evaluate.py"] = '''from pathlib import Path
import os
import json, os, sys
ROOT=Path(__file__).resolve().parents[1]; ART=ROOT/'artifacts'; ART.mkdir(exist_ok=True)
if os.getenv('AURA_DEVELOPMENT_FIXTURE')=='1': result={'status':'EXECUTED','metrics_available':True,'metrics':{'map50':0.0,'map50_95':0.0,'precision':0.0,'recall':0.0},'rows_evaluated':0,'scientific_result':False,'development_fixture':True,'review_required':True,'reason':'Synthetic development verification values only; not model performance.'}
else:
 DATA=ROOT/'data'/'dataset.yaml'; WEIGHTS=ROOT/'models'/'baseline.pt'
 if not DATA.exists() or not WEIGHTS.exists(): result={'status':'BLOCKED','metrics_available':False,'metrics':{},'reason':'Baseline evaluation requires approved data/dataset.yaml and models/baseline.pt. AURA will not invent a baseline.','scientific_result':False}
 else:
  try:
   from ultralytics import YOLO
   model=YOLO(str(WEIGHTS)); m=model.val(data=str(DATA),split='test'); result={'status':'EXECUTED','metrics_available':True,'metrics':{'map50':float(m.box.map50),'map50_95':float(m.box.map),'precision':float(m.box.mp),'recall':float(m.box.mr)},'scientific_result':True,'review_required':True}
  except Exception as exc: result={'status':'FAILED','metrics_available':False,'metrics':{},'reason':'Baseline evaluation failed.','error':str(exc),'scientific_result':False}
(ART/'baseline_evaluation.json').write_text(json.dumps(result,indent=2),encoding='utf-8'); print(json.dumps(result,indent=2)); sys.exit(0 if result['status']=='EXECUTED' else 2)
'''
        files["scripts/evaluate_model.py"] = '''from pathlib import Path
import os
import json, os, sys
ROOT=Path(__file__).resolve().parents[1]; ART=ROOT/'artifacts'; ART.mkdir(exist_ok=True)
if os.getenv('AURA_DEVELOPMENT_FIXTURE')=='1': result={'status':'EXECUTED','metrics_available':True,'metrics':{'map50':0.1,'map50_95':0.05,'precision':0.2,'recall':0.15},'rows_evaluated':0,'scientific_result':False,'development_fixture':True,'review_required':True,'reason':'Synthetic development verification values only; not model performance.'}
else:
 DATA=ROOT/'data'/'dataset.yaml'; WEIGHTS=ROOT/'artifacts'/'aura_plant_disease'/'weights'/'best.pt'
 if not DATA.exists() or not WEIGHTS.exists(): result={'status':'BLOCKED','metrics_available':False,'metrics':{},'reason':'Evaluation requires dataset.yaml and executed best.pt weights.','scientific_result':False}
 else:
  try:
   from ultralytics import YOLO
   model=YOLO(str(WEIGHTS)); m=model.val(data=str(DATA),split='test'); result={'status':'EXECUTED','metrics_available':True,'metrics':{'map50':float(m.box.map50),'map50_95':float(m.box.map),'precision':float(m.box.mp),'recall':float(m.box.mr)},'scientific_result':True,'review_required':True}
  except Exception as exc: result={'status':'FAILED','metrics_available':False,'metrics':{},'reason':'Evaluation failed.','error':str(exc),'scientific_result':False}
(ART/'evaluation.json').write_text(json.dumps(result,indent=2),encoding='utf-8'); print(json.dumps(result,indent=2)); sys.exit(0 if result['status']=='EXECUTED' else 2)
'''
        files["scripts/experiment_runner.py"] = '''import json,subprocess,sys,os
from pathlib import Path
import os
ROOT=Path(__file__).resolve().parents[1]; ART=ROOT/'artifacts'; ART.mkdir(exist_ok=True)
steps=['dataset_prepare.py','train_model.py','baseline_evaluate.py','evaluate_model.py']; records=[]
for name in steps:
 p=subprocess.run([sys.executable,str(ROOT/'scripts'/name)],cwd=ROOT,capture_output=True,text=True,shell=False); records.append({'task':name,'exit_code':p.returncode,'stdout':p.stdout[-8000:],'stderr':p.stderr[-8000:]})
 if p.returncode: break
result={'status':'EXECUTED' if records and all(x['exit_code']==0 for x in records) else 'BLOCKED_OR_FAILED','steps':records,'scientific_validation':False,'development_fixture':os.getenv('AURA_DEVELOPMENT_FIXTURE')=='1','review_required':True}
(ART/'experiment_run.json').write_text(json.dumps(result,indent=2),encoding='utf-8'); print(json.dumps(result,indent=2)); sys.exit(0 if result['status']=='EXECUTED' else 2)
'''
    if profile == 'iot':
        files["scripts/dataset_prepare.py"] = '''from pathlib import Path
import os
import json, sys
ROOT=Path(__file__).resolve().parents[1]; DATA=ROOT/'data'/'sensor_data.csv'; ART=ROOT/'artifacts'; ART.mkdir(exist_ok=True)
required=["timestamp","ph","ec","tds","temperature","humidity","nutrient_target"]
if not DATA.exists():
 result={"status":"BLOCKED","rows":0,"missing_columns":required,"reason":"Place an approved data/sensor_data.csv with columns: "+", ".join(required),"scientific_result":False}
else:
 try:
  import pandas as pd
  df=pd.read_csv(DATA); missing=[c for c in required if c not in df.columns]
  result={"status":"READY" if len(df)>0 and not missing else "BLOCKED","rows":int(len(df)),"missing_columns":missing,"columns":list(df.columns),"scientific_result":False}
  if missing: result["reason"]="Dataset is missing required columns."
  elif len(df)==0: result["reason"]="Dataset contains no rows."
 except Exception as exc: result={"status":"FAILED","rows":0,"missing_columns":required,"reason":"Dataset inspection failed.","error":str(exc),"scientific_result":False}
(ART/'dataset_status.json').write_text(json.dumps(result,indent=2),encoding='utf-8'); print(json.dumps(result,indent=2)); sys.exit(0 if result["status"]=="READY" else 2)
'''
        files["scripts/baseline_evaluate.py"] = '''from pathlib import Path
import os
import json,sys
ROOT=Path(__file__).resolve().parents[1]; DATA=ROOT/'data'/'sensor_data.csv'; MODEL=ROOT/'models'/'baseline.joblib'; ART=ROOT/'artifacts'; ART.mkdir(exist_ok=True)
if not DATA.exists() or not MODEL.exists():
 result={"status":"BLOCKED","metrics_available":False,"metrics":{},"reason":"Baseline evaluation requires approved data/sensor_data.csv and models/baseline.joblib. AURA will not invent a baseline.","scientific_result":False}
else:
 try:
  import pandas as pd, joblib
  from src.prediction import FEATURES,TARGET
  from src.evaluation import regression_metrics
  df=pd.read_csv(DATA).dropna(subset=FEATURES+[TARGET]); m=joblib.load(MODEL); pred=m.predict(df[FEATURES]); metrics=regression_metrics(df[TARGET],pred)
  result={"status":"EXECUTED","metrics_available":True,"metrics":metrics,"rows_evaluated":int(len(df)),"scientific_result":True,"review_required":True}
 except Exception as exc: result={"status":"FAILED","metrics_available":False,"metrics":{},"reason":"Baseline evaluation failed.","error":str(exc),"scientific_result":False}
(ART/'baseline_evaluation.json').write_text(json.dumps(result,indent=2)); print(json.dumps(result,indent=2)); sys.exit(0 if result['status']=='EXECUTED' else 2)
'''
        files["scripts/train_model.py"] = '''from pathlib import Path
import os
import json,sys
ROOT=Path(__file__).resolve().parents[1]; DATA=ROOT/'data'/'sensor_data.csv'; OUT=ROOT/'models'; ART=ROOT/'artifacts'; ART.mkdir(exist_ok=True)
if not DATA.exists(): result={"status":"BLOCKED","trained":False,"reason":"Approved data/sensor_data.csv is required.","scientific_result":False}; (ART/'training_status.json').write_text(json.dumps(result,indent=2)); print(json.dumps(result,indent=2)); sys.exit(2)
try:
 from src.prediction import train_models
 train_models(DATA,OUT)
 result={"status":"EXECUTED","trained":True,"models":["models/baseline.joblib","models/proposed.joblib"],"scientific_result":False,"review_required":True}
except Exception as exc: result={"status":"FAILED","trained":False,"reason":"Training failed.","error":str(exc),"scientific_result":False}
(ART/'training_status.json').write_text(json.dumps(result,indent=2)); print(json.dumps(result,indent=2)); sys.exit(0 if result['status']=='EXECUTED' else 2)
'''
        files["scripts/evaluate_model.py"] = '''from pathlib import Path
import os
import json,sys
ROOT=Path(__file__).resolve().parents[1]; DATA=ROOT/'data'/'sensor_data.csv'; MODEL=ROOT/'models'/'proposed.joblib'; ART=ROOT/'artifacts'; ART.mkdir(exist_ok=True)
if not DATA.exists() or not MODEL.exists(): result={"status":"BLOCKED","metrics_available":False,"metrics":{},"reason":"Proposed evaluation requires approved data/sensor_data.csv and executed models/proposed.joblib.","scientific_result":False}; (ART/'evaluation.json').write_text(json.dumps(result,indent=2)); print(json.dumps(result,indent=2)); sys.exit(2)
try:
 import pandas as pd, joblib
 from src.prediction import FEATURES,TARGET
 from src.evaluation import regression_metrics
 df=pd.read_csv(DATA).dropna(subset=FEATURES+[TARGET]); m=joblib.load(MODEL); pred=m.predict(df[FEATURES]); metrics=regression_metrics(df[TARGET],pred)
 result={"status":"EXECUTED","metrics_available":True,"metrics":metrics,"rows_evaluated":int(len(df)),"scientific_result":True,"review_required":True}
except Exception as exc: result={"status":"FAILED","metrics_available":False,"metrics":{},"reason":"Proposed evaluation failed.","error":str(exc),"scientific_result":False}
(ART/'evaluation.json').write_text(json.dumps(result,indent=2)); print(json.dumps(result,indent=2)); sys.exit(0 if result['status']=='EXECUTED' else 2)
'''
        files["scripts/experiment_runner.py"] = '''import json,subprocess,sys
from pathlib import Path
import os
ROOT=Path(__file__).resolve().parents[1]; ART=ROOT/'artifacts'; ART.mkdir(exist_ok=True)
steps=['dataset_prepare.py','train_model.py','baseline_evaluate.py','evaluate_model.py']; records=[]
for name in steps:
 p=subprocess.run([sys.executable,str(ROOT/'scripts'/name)],cwd=ROOT,capture_output=True,text=True,shell=False); records.append({'task':name,'exit_code':p.returncode,'stdout':p.stdout[-8000:],'stderr':p.stderr[-8000:]})
 if p.returncode: break
result={'status':'EXECUTED' if records and all(x['exit_code']==0 for x in records) else 'BLOCKED_OR_FAILED','steps':records,'scientific_validation':False,'review_required':True}
(ART/'experiment_run.json').write_text(json.dumps(result,indent=2),encoding='utf-8'); print(json.dumps(result,indent=2)); sys.exit(0 if result['status']=='EXECUTED' else 2)
'''
        files["models/README.md"] = "Approved hydroponic regression models are created by scripts/train_model.py from data/sensor_data.csv. AURA never fabricates model weights or metrics.\n"
        files["data/README.md"] = "Place an approved sensor_data.csv here with columns: timestamp, ph, ec, tds, temperature, humidity, nutrient_target. AURA never fabricates scientific data.\n"

    if profile == 'computer_vision':
        files['data/README.md'] = "Place an approved YOLO dataset.yaml here and ensure its referenced image/label paths are accessible.\n"
        files['models/README.md'] = "Place approved proposed weights at models/base.pt. Optional approved baseline weights may be placed at models/baseline.pt. AURA never invents a baseline.\n"
    elif profile == 'iot':
        _apply_iot_files(files)
        files.pop('src/vision.py', None)
    else: files['data/README.md'] = 'Place approved project data here.\n'
    files["execution_contract.json"] = json.dumps(contract, indent=2, ensure_ascii=False)
    created=[]
    for rel,content in files.items():
        path=root/rel; path.parent.mkdir(parents=True,exist_ok=True); path.write_text(content,encoding='utf-8'); created.append(rel)
    return {'workspace':str(root),'profile':profile,'files':created,'status':'READY','generated_at':now(),'workspace_version':'5.1','execution_contract':'dynamic','workspace_root_relative':f'project_workspaces/{project_id}'}

def _artifact_manifest(root: Path):
    ar=root/'artifacts'; return [{'path':str(p.relative_to(root)),'size':p.stat().st_size} for p in ar.rglob('*') if p.is_file()] if ar.exists() else []

def _read_result_summary(root: Path) -> dict[str, Any]:
    summary: dict[str, Any] = {}
    art = root / "artifacts"
    for name in ("dataset_status.json", "training_status.json", "baseline_evaluation.json", "evaluation.json", "experiment_run.json", "results_summary.json"):
        path = art / name
        if path.exists():
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
                summary[name] = data
            except Exception:
                summary[name] = {"status": "UNREADABLE"}
    return summary


def execute(project_id: str, task: str, timeout: int=120):
    root=BASE_DIR/project_id
    commands={'smoke_test':'smoke_test.py','project_test':'project_test.py','dataset_prepare':'dataset_prepare.py','train_model':'train_model.py','evaluate_model':'evaluate_model.py','baseline_evaluate':'baseline_evaluate.py','experiment_run':'experiment_runner.py'}
    if task not in commands: return {'status':'BLOCKED','message':'Task is not allowlisted.'}
    # Self-heal stale workspaces produced by earlier AURA releases.
    # A task is executable only when its generated script actually exists.
    script = root/'scripts'/commands[task]
    if not root.exists() or not (root/'execution_manifest.json').exists() or not script.exists():
        try:
            from services.execution_engine import build_workspace
            from main import PROJECT_STORE, project_snapshot
            project = PROJECT_STORE.get(project_id)
            if project is not None:
                build_workspace(project_snapshot(project))
                script = root/'scripts'/commands[task]
        except Exception as exc:
            return {'status':'BLOCKED','message':f'Build workspace is missing required execution script: {commands[task]}','error':str(exc)}
        if not root.exists() or not script.exists():
            return {'status':'BLOCKED','message':f'Build workspace is missing required execution script: {commands[task]}'}
    execution_id='exec-'+uuid.uuid4().hex[:12]; started=now(); t=time.perf_counter(); cmd=[sys.executable,str(root/'scripts'/commands[task])]
    try:
        env = dict(__import__("os").environ); env["PYTHONPATH"] = str(root) + __import__("os").pathsep + env.get("PYTHONPATH", "")
        if (root / "artifacts" / "verification_fixture.json").exists(): env["AURA_DEVELOPMENT_FIXTURE"] = "1"
        proc=subprocess.run(cmd,cwd=root,capture_output=True,text=True,timeout=min(max(timeout,1),300),shell=False,env=env); status='EXECUTED' if proc.returncode==0 else ('BLOCKED' if task in {'dataset_prepare','baseline_evaluate','train_model','evaluate_model','experiment_run'} and 'BLOCKED' in (proc.stdout or '') else 'FAILED'); stdout,stderr,exit_code=proc.stdout,proc.stderr,proc.returncode; error=None
    except subprocess.TimeoutExpired as exc: status='TIMEOUT'; stdout=exc.stdout or ''; stderr=exc.stderr or ''; exit_code=None; error=f'Execution exceeded {timeout} seconds.'
    except Exception as exc: status='FAILED'; stdout=''; stderr=str(exc); exit_code=None; error=str(exc)
    record={'execution_id':execution_id,'project_id':project_id,'task':task,'status':status,'started_at':started,'finished_at':now(),'duration_seconds':round(time.perf_counter()-t,3),'command':cmd,'cwd':str(root),'timeout_seconds':timeout,'exit_code':exit_code,'stdout':stdout[-12000:],'stderr':stderr[-12000:],'error':error,'artifacts':_artifact_manifest(root),'scientific_validation':False,'review_required':True,'result_summary':_read_result_summary(root)}
    d=root/'executions'; d.mkdir(exist_ok=True); (d/f'{execution_id}.json').write_text(json.dumps(record,indent=2),encoding='utf-8')
    try:
        from services.results_engine import persist_results
        record['results_summary'] = persist_results({'project_id': project_id}, root)
        (d/f'{execution_id}.json').write_text(json.dumps(record,indent=2),encoding='utf-8')
    except Exception as exc:
        record['results_ingest_error'] = str(exc)
    try:
        save_execution(execution_id, project_id, record)
    except Exception as exc:
        record["persistence_warning"] = str(exc)
    return record

def list_executions(project_id: str):
    try:
        durable = load_executions(project_id)
        if durable:
            return durable
    except Exception:
        pass
    root=BASE_DIR/project_id/'executions'
    if not root.exists(): return []
    out=[]
    for p in sorted(root.glob('exec-*.json'),reverse=True):
        try: out.append(json.loads(p.read_text(encoding='utf-8')))
        except Exception: pass
    return out
