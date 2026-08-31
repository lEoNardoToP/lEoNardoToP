#!/usr/bin/env python3
import argparse, csv, hashlib, json, re, shlex, statistics, subprocess, time, urllib.request
from pathlib import Path

FORBIDDEN = re.compile(r"(?i)(?:^|[;&|\s])(curl|wget|nc|netcat|ssh|scp|sftp|ftp|telnet|nmap|masscan|socat|ping|sudo|su|rm|mkfs|fdisk|parted|dd|shutdown|reboot|poweroff|mount|umount|chmod|chown|kill|pkill|iptables|ufw|apt|apt-get|yum|dnf|pacman|pip|npm|whois)(?:$|\s)")
URLISH = re.compile(r"(?i)(https?://|/dev/tcp|/dev/udp)")
CODE_FENCE = re.compile(r"^```(?:bash|sh)?\s*|\s*```$", re.I)

def shell_tokens(s):
    try:
        lex=shlex.shlex(s,posix=True,punctuation_chars='|&;<>'); lex.whitespace_split=True; lex.commenters=''
        return list(lex)
    except Exception: return []

def normalize(s):
    toks=shell_tokens(s); return ' '.join(toks) if toks else ' '.join(str(s).strip().split())

def safe_command(s):
    if not s or len(s)>1200 or '\n' in s or '\r' in s: return False,'shape'
    if URLISH.search(s) or FORBIDDEN.search(' '+s): return False,'forbidden-capability'
    if re.search(r'(^|\s)>\s*/(?:etc|usr|bin|sbin|root|boot|proc|sys)/',s): return False,'host-write'
    return True,'ok'

def syntax_ok(s):
    p=subprocess.run(['bash','-n','-c',s],capture_output=True,text=True,timeout=5)
    return p.returncode==0,(p.stderr or '').strip()[:250]

def utility_signature(s):
    toks=shell_tokens(s); ops={'|','||','&&',';','&','>','>>','<','<<'}; control={'while','do','done','then','fi','if','for','in','case','esac'}
    utils=[]; flags=[]; expect=True
    for t in toks:
        if t in ops: expect=True; continue
        if t in control: continue
        if expect and not t.startswith(('-','$')) and '=' not in t: utils.append(Path(t).name); expect=False
        elif t.startswith('-'): flags.append(t)
    return tuple(utils),tuple(sorted(flags))
def structural_match(a,b):
    ua,fa=utility_signature(a); ub,fb=utility_signature(b); return bool(ua) and ua==ub and fa==fb

def clean_model_text(text):
    text=CODE_FENCE.sub('',str(text).strip()).strip(); lines=[x.strip() for x in text.splitlines() if x.strip()]
    if not lines:return ''
    line=lines[0]
    for p in ('Command:','Bash:','Answer:','Choice:','Fill:'):
        if line.lower().startswith(p.lower()):line=line[len(p):].strip()
    if len(line)>=2 and line[0]==line[-1] and line[0] in ('`','"'):line=line[1:-1].strip()
    return line

def task_type(meta): return str(meta.get('task_type','nl2bash')).lower()
def options_for(meta): return meta.get('options') or meta.get('choices') or meta.get('answer_choices') or meta.get('mcq_options')

def build_user(meta, mode='adapter'):
    typ=task_type(meta); desc=meta.get('nl_description',''); parts=[f"Task type: {typ}",f"Task: {desc}"]
    if meta.get('context'):parts.append('Context: '+str(meta['context']))
    if meta.get('previous_command'):parts.append('Previous command: '+str(meta['previous_command']))
    if 'previous_output' in meta:parts.append('Previous output: '+str(meta.get('previous_output','')))
    if meta.get('command_prefix'):parts.append('Required prefix: '+str(meta['command_prefix']))
    if meta.get('template'):parts.append('Template: '+str(meta['template']))
    opts=options_for(meta)
    if opts:parts.append('Choices: '+json.dumps(opts,ensure_ascii=False))
    if mode=='adapter':
        if 'mcq' in typ: parts.append('Return exactly one allowed choice, with no explanation.')
        elif 'blanks' in typ or 'blank' in typ: parts.append('Complete the blank(s) in the template. Return the full completed command only.')
        elif 'prefixed' in typ or 'prefix' in typ: parts.append('Return the full command and preserve the required prefix exactly.')
        elif 'multi' in typ: parts.append('Use the previous command/output as state. Return only the next requested command.')
        elif 'context' in typ: parts.append('Use the supplied context as observed state. Return only the requested command.')
        else: parts.append('Translate the request into the most direct standard Linux command.')
    return '\n'.join(parts)

def ask(base_url, model, meta, mode='adapter', repair=''):
    typ=task_type(meta)
    if mode=='baseline':
        system=('Translate the benign local Linux administration request into exactly one Bash command. Return only the command. No markdown or explanation. Do not use networking, privilege escalation, package installation, destructive commands, or external hosts.')
    else:
        if 'mcq' in typ:
            system=('You are a precise cybersecurity/Linux benchmark answerer. For multiple-choice tasks, output exactly one answer choice and nothing else. Never invent a shell command when the task is a question.')
        else:
            system=('You are the command-grounding adapter for an authorized local benchmark. Produce exactly one minimal Linux/Bash command matching the requested action. Respect task state, templates and prefixes literally. Prefer standard utilities and the simplest semantics. Return only the answer, no markdown/explanation. Do not use networking, privilege escalation, package installation, destructive commands, or external hosts.')
    user=build_user(meta,mode)
    if repair:user+='\nPrevious answer failed only this validation: '+repair+'\nReturn one corrected answer.'
    body=json.dumps({'model':model,'messages':[{'role':'system','content':system},{'role':'user','content':user}],'temperature':0,'max_tokens':220,'stream':False}).encode()
    req=urllib.request.Request(base_url.rstrip('/')+'/v1/chat/completions',data=body,headers={'Content-Type':'application/json'})
    with urllib.request.urlopen(req,timeout=180) as r:obj=json.load(r)
    return clean_model_text(obj['choices'][0]['message']['content'])

def load_jsonl(path):
    out={}
    for line in path.read_text().splitlines():
        if line.strip():
            row=json.loads(line);out[row['task_id']]=row
    return out

def load_tasks(root):
    tasks={}
    for rel in ('data/tasks/nl2bash/nl2bash_tasks.jsonl','data/tasks/cybashbench/cybashbench_tasks.jsonl'):
        p=root/rel
        if p.exists():tasks.update(load_jsonl(p))
    return tasks

def human_ids(root):
    ids=set();p=root/'data/human/completions.csv'
    if not p.exists():return ids
    with p.open(newline='') as f:
        for r in csv.DictReader(f):
            if r.get('benchmark') in ('nl2bash','cybashbench'):ids.add(r['task_id'])
    return ids

def stable_bucket(tid):return int(hashlib.sha256(tid.encode()).hexdigest()[:8],16)%100

def eligible(meta):
    ref=meta.get('bash_command',''); typ=task_type(meta)
    if 'mcq' in typ:return True,'ok'
    return safe_command(ref)

def ref_answer(meta):
    typ=task_type(meta)
    if 'mcq' in typ:
        for k in ('correct_answer','answer','bash_command'):
            if meta.get(k) not in (None,''):return str(meta[k])
    return str(meta.get('bash_command',''))

def score_answer(meta,cand):
    ref=ref_answer(meta); typ=task_type(meta)
    exact=' '.join(cand.strip().split())==' '.join(ref.strip().split()) if 'mcq' in typ else normalize(cand)==normalize(ref)
    struct=False if 'mcq' in typ else structural_match(cand,ref)
    return exact,struct,ref

def run_one(base_url,model,meta,mode):
    t0=time.perf_counter(); cand=''; status='ok';retry=0
    try:
        cand=ask(base_url,model,meta,mode)
        if 'mcq' not in task_type(meta):
            ok,note=safe_command(cand); syn,snote=syntax_ok(cand) if ok else (False,note)
            if not ok or not syn:
                retry=1;cand=ask(base_url,model,meta,mode,note if not ok else snote)
                ok,note=safe_command(cand);syn,snote=syntax_ok(cand) if ok else (False,note)
            if not ok:status='rejected-safety'
            elif not syn:status='rejected-syntax'
    except Exception as e:status='model-error:'+type(e).__name__
    exact,struct,ref=score_answer(meta,cand) if status=='ok' else (False,False,ref_answer(meta))
    return {'candidate':cand,'exact':exact,'structural':struct,'status':status,'retry':retry,'elapsed_minutes':(time.perf_counter()-t0)/60.0,'ref_sha256':hashlib.sha256(ref.encode()).hexdigest()}

def aggregate(rows,prefix):
    rr=[r for r in rows if r['mode']==prefix]
    return {'n':len(rr),'exact':statistics.mean([1.0 if r['exact'] else 0.0 for r in rr]) if rr else 0,'structural':statistics.mean([1.0 if r['structural'] else 0.0 for r in rr]) if rr else 0,'errors':sum(str(r['status']).startswith('model-error') for r in rr),'safety_rejections':sum(r['status']=='rejected-safety' for r in rr)}

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--data-root',required=True);ap.add_argument('--out-dir',required=True);ap.add_argument('--base-url',default='http://127.0.0.1:8080');ap.add_argument('--model',default='local-qwen-coder');ap.add_argument('--limit',type=int,default=60)
    args=ap.parse_args();root=Path(args.data_root);out=Path(args.out_dir);out.mkdir(parents=True,exist_ok=True)
    tasks=load_tasks(root);consumed=human_ids(root);pool=[];skipped=[]
    for tid,row in tasks.items():
        if tid in consumed:continue
        meta=row['dataset_task_metadata'];ok,why=eligible(meta)
        if not ok:skipped.append({'task_id':tid,'reason':why});continue
        split='DEV' if stable_bucket(tid)<60 else 'INTERNAL_HOLDOUT';pool.append((tid,split,row))
    pool.sort(key=lambda x: hashlib.sha256(('freeze-v1:'+x[0]).encode()).hexdigest())
    dev=[x for x in pool if x[1]=='DEV'][:args.limit];hold=[x for x in pool if x[1]=='INTERNAL_HOLDOUT'][:args.limit];rows=[]
    for split,items in [('DEV',dev),('INTERNAL_HOLDOUT',hold)]:
        for i,(tid,_,row) in enumerate(items,1):
            meta=row['dataset_task_metadata']
            for mode in ('baseline','adapter'):
                r=run_one(args.base_url,args.model,meta,mode);r.update({'task_id':tid,'split':split,'mode':mode,'task_type':task_type(meta),'category':meta.get('security_category',''),'gold_hidden_from_model':True});rows.append(r)
                print(f'{split} {i}/{len(items)} {mode} {tid} exact={r["exact"]} structural={r["structural"]} status={r["status"]}',flush=True)
    with (out/'dev_results.csv').open('w',newline='') as f:
        fields=list(rows[0].keys());w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(rows)
    def split_summary(split):
        s=[r for r in rows if r['split']==split];b=aggregate(s,'baseline');a=aggregate(s,'adapter')
        return {'baseline':b,'adapter':a,'exact_gain_pp':100*(a['exact']-b['exact']),'structural_gain_pp':100*(a['structural']-b['structural'])}
    manifest='\n'.join(tid for tid,_,_ in dev+hold)+'\n'
    summary={'protocol':'IncidentLens command grounding DEV v1','consumed_human_task_ids_excluded':len(consumed),'dev_tasks':len(dev),'internal_holdout_tasks':len(hold),'manifest_sha256':hashlib.sha256(manifest.encode()).hexdigest(),'selection':'deterministic SHA-256 split and order; no gold-dependent selection','DEV':split_summary('DEV'),'INTERNAL_HOLDOUT':split_summary('INTERNAL_HOLDOUT'),'freeze_rule':'After this run, adapter prompt/type routing is frozen before opening any new human family.','notes':['Gold answers used only by scorer, never in model prompt.','All task IDs with published human completion attempts are excluded from DEV and internal holdout.','No generated command is executed.']}
    (out/'dev_summary.json').write_text(json.dumps(summary,indent=2));(out/'dev_manifest.txt').write_text(manifest);(out/'dev_skipped.json').write_text(json.dumps(skipped,indent=2));print(json.dumps(summary,indent=2),flush=True)
if __name__=='__main__':main()
