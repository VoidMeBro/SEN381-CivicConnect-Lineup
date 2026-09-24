"""CivicConnect NFR-06 evidence integrity checks; never certifies human approval."""
import argparse
import html
import json
from pathlib import Path

FIELDS = {'id','wording','source','priority','acceptance_criteria','asr','architecture',
          'data','design','technology','implementation','verification','status','references',
          'approval','acceptance_status'}
STATUSES = {'Approved','In Development','Implemented','Changed','Deferred','Planned','Not Yet Implemented'}

def validate(root):
    root = Path(root).resolve()
    rows = json.loads((root/'rtm.json').read_text(encoding='utf-8'))
    baseline = json.loads((root/'baseline_m1.json').read_text(encoding='utf-8'))
    errors = []
    if not isinstance(rows,list) or not all(isinstance(r,dict) for r in rows):
        return ['RTM must be a list of records']
    expected = {r['id']:r for r in baseline}
    ids = [r.get('id') for r in rows]
    if any(not isinstance(i,str) for i in ids): return ['Every record needs a string ID']
    if len(set(ids)) != len(ids): errors.append('Duplicate requirement IDs')
    if set(ids) != set(expected): errors.append('Requirement coverage differs from preserved M1')
    for r in rows:
        rid = r['id']
        missing = FIELDS-set(r)
        if missing:
            errors.append(f'{rid}: missing fields {sorted(missing)}')
            continue
        for k in FIELDS-{'implementation','verification','references'}:
            if not isinstance(r[k],str) or not r[k].strip(): errors.append(f'{rid}: empty or invalid {k}')
        if r['status'] not in STATUSES: errors.append(f'{rid}: uncontrolled status')
        if not all(isinstance(r[k],list) and all(isinstance(v,str) for v in r[k]) for k in ('implementation','verification','references')):
            errors.append(f'{rid}: evidence and references must be string lists')
            continue
        for kind in ('implementation','verification'):
            for link in r[kind]:
                target = (root/link).resolve()
                if not target.is_relative_to(root) or Path(link).is_absolute():
                    errors.append(f'{rid}: evidence path escapes pack: {link}')
                elif not target.is_file(): errors.append(f'{rid}: missing evidence {link}')
        if r['status']=='Implemented' and (not r['implementation'] or not r['verification']):
            errors.append(f'{rid}: Implemented needs implementation and verification evidence')
        if rid in expected:
            changed = any(r.get(k)!=v for k,v in expected[rid].items())
            if changed and not any(v.startswith('CR-') for v in r['references']):
                errors.append(f'{rid}: baseline change needs a CR reference')
        if r['status']=='Changed' and not any(v.startswith('CR-') for v in r['references']):
            errors.append(f'{rid}: Changed needs a CR reference')
    return errors

def render(root):
    root=Path(root)
    rows=json.loads((root/'rtm.json').read_text(encoding='utf-8'))
    cards=[]
    for r in rows:
        fields=''.join('<dt>'+html.escape(k.replace('_',' ').title())+'</dt><dd>'+html.escape('; '.join(v) if isinstance(v,list) and v else ('Planned - no evidence' if isinstance(v,list) else str(v)))+'</dd>' for k,v in r.items())
        cards.append('<article><h2>'+html.escape(r['id'])+'</h2><dl>'+fields+'</dl></article>')
    page='''<!doctype html><html lang="en"><meta charset="utf-8"><title>CivicConnect RTM</title>
    <style>body{font:16px/1.5 system-ui;margin:32px auto;max-width:1000px;padding:0 20px;background:#f4f6f8;color:#182535}input{padding:12px;width:90%;font:inherit}article{background:white;padding:24px;margin:20px 0;border:1px solid #ccd4db}dl{display:grid;grid-template-columns:190px 1fr;gap:12px}dt{font-weight:bold}dd{margin:0;overflow-wrap:anywhere}h1{font-size:30px}@media(max-width:650px){dl{display:block}dt{margin-top:15px}}@media print{input{display:none}article{break-inside:avoid}}</style>
    <h1>CivicConnect requirements traceability</h1><p>M1 v0.11 sign-off confirmed by the user on 24 September 2026. M2 allocations remain proposed; product implementation evidence is pending. Tool checks do not certify acceptance.</p>
    <label for="q">Find a requirement or evidence reference</label><p><input id="q" type="search" placeholder="Try FR-13 or NFR-06"></p><p id="count" aria-live="polite"></p>'''+''.join(cards)+'''<script>const q=document.querySelector('#q');function filter(){let n=0;document.querySelectorAll('article').forEach(a=>{a.hidden=!a.textContent.toLowerCase().includes(q.value.toLowerCase());if(!a.hidden)n++});document.querySelector('#count').textContent=n+' requirements shown'}q.addEventListener('input',filter);filter()</script></html>'''
    (root/'RTM.html').write_text(page,encoding='utf-8')

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command',choices=['validate','render'])
    parser.add_argument('--root',type=Path,default=Path(__file__).parent)
    args=parser.parse_args()
    try:
        if args.command=='render': render(args.root)
        else:
            errors=validate(args.root)
            print('\n'.join(errors) if errors else 'PASS: 20-record M1 coverage and RTM structure/evidence checks. Human approval and product acceptance are not certified.')
            raise SystemExit(bool(errors))
    except (OSError,ValueError,KeyError,TypeError) as exc:
        parser.exit(1,f'Invalid traceability input: {exc}\n')
