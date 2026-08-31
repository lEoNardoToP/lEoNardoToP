#!/usr/bin/env python3
import argparse,csv,hashlib,json,re,shlex,statistics,subprocess,time,urllib.request
from pathlib import Path
FORBIDDEN=re.compile(r"(?i)(?:^|[;&|\s])(curl|wget|nc|netcat|ssh|scp|sftp|ftp|telnet|nmap|masscan|socat|ping|sudo|su|rm|mkfs|fdisk|parted|dd|shutdown|reboot|poweroff|mount|umount|chmod|chown|kill|pkill|iptables|ufw|apt|apt-get|yum|dnf|pacman|pip|npm|whois)(?:$|\s)")
URLISH=re.compile(r"(?i)(https?://|/dev/tcp|/dev/udp)")
CODE_FENCE=re.compile(r"^```(?:bash|sh)?\s*|\s*```$",re.I)

def tokens(s):
    try:
        lex=shlex.shlex(s,posix=True,punctuation_chars='|&;<>');lex.whitespace_split=True;lex.commenters='';return list(lex)
    except:return []
def norm(s):
    t=tokens(s);return ' '.join(t) if t else ' '.join(str(s).strip().split())
def safe(s):
    if not s or len(s)>1200 or '\n' in s or '\r' in s:return False,'shape'
    if URLISH.search(s) or FORBIDDEN.search(' '+s):return False,'forbidden-capability'
    if re.search(r'(^|\s)>\s*/(?:etc|usr|bin|sbin|root|boot|proc|sys)/',s):return False,'host-write'
    return True,'ok'
def syntax(s):
    p=subprocess.run(['bash','-n','-c',s],capture_output=True,text=True,timeout=5);return p.returncode==0,(p.stderr or '')[:250]
def signature(s):
    t=tokens(s);ops={'|','||','&&',';','&','>','>>','<','<<'};ctrl={'while','do','done','then','fi','if','for','in','case','esac'};u=[];f=[];expect=True
    for x in t:
        if x in ops:expect=True;continue
        if x in ctrl:continue
        if expect and not x.startswith(('-','$')) and '=' not in x:u.append(Path(x).name);expect=False
        elif x.startswith('-'):f.append(x)
    return tuple(u),tuple(sorted(f))
def structural(a,b):
    ua,fa=signature(a);ub,fb=signature(b);return bool(ua) and ua==ub and fa==fb

def clean(x):
    x=CODE_FENCE.sub('',str(x).strip()).strip();lines=[y.strip() for y in x.splitlines() if y.strip()]
    if not lines:return ''
    x=lines[0]
    for p in ('Command:','Bash:','Answer:','Choice:','Fill:','Suffix:'):
        if x.lower().startswith(p.lower()):x=x[len(p):].strip()
    if len(x)>=2 and x[0]==x[-1] and x[0] in ('`','"'):x=x[1:-1].strip()
    return x

def ttype(m):return str(m.get('task_type','nl2bash')).lower()
def choices(m):return m.get('choices') or m.get('options') or m.get('answer_choices') or []
def prompt_baseline(m):
    p=[f"Task: {m.get('nl_description','')}"]
    if m.get('context'):p.append('Context: '+str(m['context']))
    if m.get('previous_command'):p.append('Previous command: '+str(m['previous_command']))
    if 'previous_output' in m:p.append('Previous output: '+str(m.get('previous_output','')))
    if m.get('command_prefix'):p.append('The full answer must start with this prefix: '+str(m['command_prefix']))
    if m.get('template'):p.append('Template with blank: '+str(m['template']))
    if choices(m):p.append('Choices: '+json.dumps(choices(m),ensure_ascii=False))
    return '\n'.join(p)
def prompt_adapter(m):
    typ=ttype(m);p=[f"Task: {m.get('nl_description','')}"]
    if m.get('context'):p.append('Observed context: '+str(m['context']))
    if m.get('previous_command'):p.append('Previous command: '+str(m['previous_command']))
    if 'previous_output' in m:p.append('Previous output: '+str(m.get('previous_output','')))
    if 'mcq' in typ:
        p.append('Choices in order A,B,C,D: '+json.dumps(choices(m),ensure_ascii=False));p.append('Return ONLY the best choice text or its letter.')
    elif 'blank' in typ:
        p.append('Template: '+str(m.get('template','')));p.append('Return ONLY the text that replaces the blank marker ___, not the whole command.')
    elif 'prefix' in typ:
        p.append('Fixed prefix: '+str(m.get('command_prefix','')));p.append('Return ONLY the suffix that comes after the fixed prefix.')
    elif 'multi' in typ:
        p.append('Treat previous output as current state. Return only the next command requested now.')
    elif 'context' in typ:
        p.append('Use the observed context to choose the direct command. Return only that command.')
    else:p.append('Return the simplest standard Linux command that exactly performs the request.')
    return '\n'.join(p)

def ask(url,model,m,mode,repair=''):
    if mode=='baseline':
        sys='Translate the benign local Linux administration request into exactly one Bash command. Return only the command. No markdown or explanation. Do not use networking, privilege escalation, package installation, destructive commands, or external hosts.';user=prompt_baseline(m)
    else:
        sys=('You are IncidentLens command-grounding interface compiler for an authorized local benchmark. Separate task semantics from output format. '
             'Honor templates/prefixes/choices literally; prefer minimal standard Linux semantics. Return only the requested payload with no explanation. '
             'Never use networking, privilege escalation, package installation, destructive commands, or external hosts.');user=prompt_adapter(m)
    if repair:user+='\nPrevious output failed only this validation: '+repair+'\nReturn a corrected payload.'
    body=json.dumps({'model':model,'messages':[{'role':'system','content':sys},{'role':'user','content':user}],'temperature':0,'max_tokens':220,'stream':False}).encode()
    req=urllib.request.Request(url.rstrip('/')+'/v1/chat/completions',data=body,headers={'Content-Type':'application/json'})
    with urllib.request.urlopen(req,timeout=180) as r:o=json.load(r)
    return clean(o['choices'][0]['message']['content'])

def compile_answer(m,payload,mode):
    if mode=='baseline':return payload
    typ=ttype(m)
    if 'mcq' in typ:
        cs=choices(m);x=payload.strip();mm=re.fullmatch(r'(?i)(?:choice\s*)?([A-D])(?:[\).:]?)',x)
        if mm and cs:
            i=ord(mm.group(1).upper())-65
            if 0<=i<len(cs):return str(cs[i])
        for c in cs:
            if x.lower()==str(c).strip().lower():return str(c)
        return x
    if 'blank' in typ:
        tmpl=str(m.get('template',''));x=payload.strip()
        if '___' in tmpl:
            first=tmpl.split()[0] if tmpl.split() else ''
            if first and x.startswith(first+' '):return x
            return tmpl.replace('___',x,1)
        return x
    if 'prefix' in typ:
        pref=str(m.get('command_prefix',''));x=payload.strip()
        if x.startswith(pref):return x
        if not x:return pref
        return pref.rstrip()+('' if pref.endswith(' ') else ' ')+x.lstrip()
    return payload

def load_jsonl(p):
    o={}
    for l in p.read_text().splitlines():
        if l.strip():r=json.loads(l);o[r['task_id']]=r
    return o
def load_tasks(root):
    o={}
    for rel in ('data/tasks/nl2bash/nl2bash_tasks.jsonl','data/tasks/cybashbench/cybashbench_tasks.jsonl'):
        p=root/rel
        if p.exists():o.update(load_jsonl(p))
    return o
def human_ids(root):
    ids=set()
    with (root/'data/human/completions.csv').open(newline='') as f:
        for r in csv.DictReader(f):
            if r.get('benchmark') in ('nl2bash','cybashbench'):ids.add(r['task_id'])
    return ids
def eligible(m):
    if 'mcq' in ttype(m):return True,'ok'
    return safe(str(m.get('bash_command','')))
def bucket(s,tid):return int(hashlib.sha256((s+tid).encode()).hexdigest()[:8],16)%100
def order(s,tid):return hashlib.sha256((s+tid).encode()).hexdigest()
def consumed_v1(pool,limit=60):
    p=sorted(pool,key=lambda x:order('freeze-v1:',x[0]));d=[x for x in p if bucket('',x[0])<60][:limit];h=[x for x in p if bucket('',x[0])>=60][:limit];return {x[0] for x in d+h}
def score(m,c):
    ref=str(m.get('bash_command',''));e=' '.join(c.strip().split())==' '.join(ref.strip().split()) if 'mcq' in ttype(m) else norm(c)==norm(ref);s=False if 'mcq' in ttype(m) else structural(c,ref);return e,s,ref
def run(url,model,m,mode):
    t0=time.perf_counter();status='ok';retry=0;payload='';cand=''
    try:
        payload=ask(url,model,m,mode);cand=compile_answer(m,payload,mode)
        if 'mcq' not in ttype(m):
            ok,note=safe(cand);sy,se=syntax(cand) if ok else (False,note)
            if not ok or not sy:
                retry=1;payload=ask(url,model,m,mode,note if not ok else se);cand=compile_answer(m,payload,mode);ok,note=safe(cand);sy,se=syntax(cand) if ok else (False,note)
            if not ok:status='rejected-safety'
            elif not sy:status='rejected-syntax'
    except Exception as e:status='model-error:'+type(e).__name__
    ex,st,ref=score(m,cand) if status=='ok' else (False,False,str(m.get('bash_command','')))
    return {'payload':payload,'candidate':cand,'exact':ex,'structural':st,'status':status,'retry':retry,'elapsed_minutes':(time.perf_counter()-t0)/60,'ref_sha256':hashlib.sha256(ref.encode()).hexdigest()}
def agg(rows,mode):
    x=[r for r in rows if r['mode']==mode];return {'n':len(x),'exact':statistics.mean(1.0 if r['exact'] else 0.0 for r in x),'structural':statistics.mean(1.0 if r['structural'] else 0.0 for r in x),'errors':sum(str(r['status']).startswith('model-error') for r in x),'safety_rejections':sum(r['status']=='rejected-safety' for r in x)}

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--data-root',required=True);ap.add_argument('--out-dir',required=True);ap.add_argument('--base-url',default='http://127.0.0.1:8080');ap.add_argument('--model',default='local-qwen-coder');ap.add_argument('--limit',type=int,default=50);a=ap.parse_args();root=Path(a.data_root);out=Path(a.out_dir);out.mkdir(parents=True,exist_ok=True)
    tasks=load_tasks(root);hum=human_ids(root);pool=[]
    for tid,row in tasks.items():
        if tid in hum:continue
        ok,_=eligible(row['dataset_task_metadata'])
        if ok:pool.append((tid,row))
    old=consumed_v1(pool,60);remain=[x for x in pool if x[0] not in old];remain=sorted(remain,key=lambda x:order('freeze-v2:',x[0]));dev=[x for x in remain if bucket('split-v2:',x[0])<60][:a.limit];hold=[x for x in remain if bucket('split-v2:',x[0])>=60][:a.limit]
    rows=[]
    for split,items in [('DEV2',dev),('INTERNAL_HOLDOUT2',hold)]:
        for i,(tid,row) in enumerate(items,1):
            m=row['dataset_task_metadata']
            for mode in ('baseline','adapter-v2'):
                r=run(a.base_url,a.model,m,mode);r.update({'task_id':tid,'split':split,'mode':mode,'task_type':ttype(m),'category':m.get('security_category','')});rows.append(r);print(f'{split} {i}/{len(items)} {mode} {tid} exact={r["exact"]} struct={r["structural"]}',flush=True)
    with (out/'v2_results.csv').open('w',newline='') as f:w=csv.DictWriter(f,fieldnames=list(rows[0].keys()));w.writeheader();w.writerows(rows)
    def sm(split):
        x=[r for r in rows if r['split']==split];b=agg(x,'baseline');v=agg(x,'adapter-v2');return {'baseline':b,'adapter_v2':v,'exact_gain_pp':100*(v['exact']-b['exact']),'structural_gain_pp':100*(v['structural']-b['structural'])}
    man='\n'.join(t for t,_ in dev+hold)+'\n';hs=sm('INTERNAL_HOLDOUT2');promote=hs['adapter_v2']['exact']>=hs['baseline']['exact'] and hs['exact_gain_pp']>=5 and hs['adapter_v2']['exact']>=0.25 and hs['adapter_v2']['errors']==0
    summary={'protocol':'IncidentLens command grounding DEV v2','model':'Qwen2.5-Coder-1.5B-Instruct-GGUF:Q4_K_M','human_task_ids_excluded':len(hum),'v1_consumed_nonhuman_ids_excluded':len(old),'dev2_tasks':len(dev),'internal_holdout2_tasks':len(hold),'manifest_sha256':hashlib.sha256(man.encode()).hexdigest(),'selection':'fresh deterministic v2 split/order after excluding all v1 task IDs','DEV2':sm('DEV2'),'INTERNAL_HOLDOUT2':hs,'promotion_gate':{'holdout_exact_not_below_baseline':True,'gain_pp_min':5,'absolute_exact_min':0.25,'model_errors_required':0},'promote_to_new_human_family':promote,'notes':['Task-aware output compiler uses only prompt-visible metadata, never gold.','MCQ letter mapping, blank reconstruction and prefix reconstruction are deterministic interface normalization.','Generated commands are not executed.']}
    (out/'v2_summary.json').write_text(json.dumps(summary,indent=2));(out/'v2_manifest.txt').write_text(man);print(json.dumps(summary,indent=2),flush=True)
if __name__=='__main__':main()
