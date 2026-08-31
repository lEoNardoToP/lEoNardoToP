#!/usr/bin/env python3
import argparse, csv, hashlib, json, re, shlex, statistics, subprocess, time, urllib.request
from pathlib import Path

FORBIDDEN = re.compile(r"(?i)(?:^|[;&|\s])(curl|wget|nc|netcat|ssh|scp|sftp|ftp|telnet|nmap|masscan|socat|ping|sudo|su|rm|mkfs|fdisk|parted|dd|shutdown|reboot|poweroff|mount|umount|chmod|chown|kill|pkill|iptables|ufw|apt|apt-get|yum|dnf|pacman|pip|npm|whois)(?:$|\s)")
URLISH = re.compile(r"(?i)(https?://|/dev/tcp|/dev/udp)")
CODE_FENCE = re.compile(r"^```(?:bash|sh)?\s*|\s*```$", re.I)


def shell_tokens(s):
    try:
        lex = shlex.shlex(s, posix=True, punctuation_chars='|&;<>')
        lex.whitespace_split = True; lex.commenters = ''
        return list(lex)
    except Exception:
        return []


def normalize(s):
    toks = shell_tokens(s)
    return ' '.join(toks) if toks else ' '.join(s.strip().split())


def safe_command(s):
    if not s or len(s) > 1200 or '\n' in s or '\r' in s:
        return False, 'shape'
    if URLISH.search(s) or FORBIDDEN.search(' ' + s):
        return False, 'forbidden-capability'
    if re.search(r'(^|\s)>\s*/(?:etc|usr|bin|sbin|root|boot|proc|sys)/', s):
        return False, 'host-write'
    return True, 'ok'


def syntax_ok(s):
    p = subprocess.run(['bash','-n','-c',s], capture_output=True, text=True, timeout=5)
    return p.returncode == 0, (p.stderr or '').strip()[:300]


def utility_signature(s):
    toks = shell_tokens(s)
    ops = {'|','||','&&',';','&','>','>>','<','<<'}
    control = {'while','do','done','then','fi','if','for','in','case','esac'}
    utils, flags, expect = [], [], True
    for t in toks:
        if t in ops:
            expect = True; continue
        if t in control: continue
        if expect and not t.startswith(('-', '$')) and '=' not in t:
            utils.append(Path(t).name); expect = False
        elif t.startswith('-'):
            flags.append(t)
    return tuple(utils), tuple(sorted(flags))


def structural_match(a,b):
    ua,fa = utility_signature(a); ub,fb = utility_signature(b)
    return bool(ua) and ua == ub and fa == fb


def clean_model_text(text):
    text = CODE_FENCE.sub('', text.strip()).strip()
    lines = [x.strip() for x in text.splitlines() if x.strip()]
    if not lines: return ''
    line = lines[0]
    for p in ('Command:','Bash:','Answer:'):
        if line.lower().startswith(p.lower()): line = line[len(p):].strip()
    if len(line) >= 2 and line[0] == line[-1] and line[0] in ('`','"'):
        line = line[1:-1].strip()
    return line


def task_prompt(meta):
    parts = [f"Task: {meta.get('nl_description','')}"]
    if meta.get('context'):
        parts.append(f"Context: {meta['context']}")
    if meta.get('previous_command'):
        parts.append(f"Previous command: {meta['previous_command']}")
    if 'previous_output' in meta:
        parts.append(f"Previous output: {meta.get('previous_output','')}")
    if meta.get('command_prefix'):
        parts.append(f"The full answer must start with this prefix: {meta['command_prefix']}")
    if meta.get('template'):
        parts.append(f"Template with blank: {meta['template']}. Return the completed full command.")
    opts = meta.get('options') or meta.get('choices')
    if opts:
        parts.append('Allowed choices: ' + json.dumps(opts, ensure_ascii=False))
    return '\n'.join(parts)


def ask(base_url, model, prompt, repair=''):
    system = (
        'Translate the benign local Linux administration request into exactly one Bash command. '
        'Return only the command. No markdown or explanation. Do not use networking, privilege escalation, '
        'package installation, destructive commands, or external hosts.'
    )
    user = prompt
    if repair:
        user += '\nYour previous answer was rejected only for this syntax/safety reason: ' + repair + '\nReturn one corrected command.'
    body = json.dumps({'model':model,'messages':[{'role':'system','content':system},{'role':'user','content':user}],
                       'temperature':0,'max_tokens':180,'stream':False}).encode()
    req = urllib.request.Request(base_url.rstrip('/')+'/v1/chat/completions', data=body,
                                 headers={'Content-Type':'application/json'})
    with urllib.request.urlopen(req, timeout=180) as r:
        obj = json.load(r)
    return clean_model_text(obj['choices'][0]['message']['content'])


def load_jsonl(path):
    out = {}
    for line in path.read_text().splitlines():
        if line.strip():
            row = json.loads(line); out[row['task_id']] = row
    return out


def load_all_tasks(root):
    tasks = {}
    for rel in ('data/tasks/nl2bash/nl2bash_tasks.jsonl','data/tasks/cybashbench/cybashbench_tasks.jsonl'):
        p = root/rel
        if p.exists(): tasks.update(load_jsonl(p))
    return tasks


def load_humans(root):
    rows=[]
    with (root/'data/human/completions.csv').open(newline='') as f:
        for r in csv.DictReader(f):
            if r.get('benchmark') in ('nl2bash','cybashbench'): rows.append(r)
    return rows


def bootstrap_delta(per_task, seed=740100, n=5000):
    import random
    if not per_task: return [None,None]
    rng=random.Random(seed); vals=[]
    for _ in range(n):
        sm=[per_task[rng.randrange(len(per_task))] for _ in range(len(per_task))]
        vals.append(statistics.mean(x['agent']-x['human'] for x in sm))
    vals.sort(); return [vals[int(.025*(n-1))], vals[int(.975*(n-1))]]


def human_stats(rows):
    attempts=len(rows); passes=sum(str(r.get('passed','')).lower()=='true' for r in rows)
    times=[]
    for r in rows:
        if str(r.get('passed','')).lower()=='true' and str(r.get('censored','')).lower()!='true':
            try:
                v=float(r.get('elapsed_minutes','0'))
                if v>0: times.append(v)
            except Exception: pass
    return attempts, (passes/attempts if attempts else 0.0), (statistics.median(times) if times else None)


def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--data-root',required=True); ap.add_argument('--out-dir',required=True)
    ap.add_argument('--base-url',default='http://127.0.0.1:8080'); ap.add_argument('--model',default='local-qwen-coder')
    args=ap.parse_args(); root=Path(args.data_root); out=Path(args.out_dir); out.mkdir(parents=True,exist_ok=True)
    tasks=load_all_tasks(root); humans=load_humans(root)
    by={}
    for r in humans:
        if r['task_id'] in tasks: by.setdefault(r['task_id'],[]).append(r)

    selected=[]; skipped=[]
    for tid in sorted(by):
        ref=tasks[tid]['dataset_task_metadata']['bash_command']
        ok,why=safe_command(ref)
        if ok: selected.append(tid)
        else: skipped.append({'task_id':tid,'benchmark':by[tid][0]['benchmark'],'reason':'unsafe-reference:'+why})
    manifest='\n'.join(selected)+'\n'; manifest_hash=hashlib.sha256(manifest.encode()).hexdigest()

    results=[]; per=[]
    for i,tid in enumerate(selected,1):
        meta=tasks[tid]['dataset_task_metadata']; ref=meta['bash_command']; prompt=task_prompt(meta)
        candidate=''; status='ok'; retry=0; t0=time.perf_counter()
        try:
            candidate=ask(args.base_url,args.model,prompt)
            ok,note=safe_command(candidate); syn,snote=syntax_ok(candidate) if ok else (False,note)
            if not ok or not syn:
                retry=1; candidate=ask(args.base_url,args.model,prompt,note if not ok else snote)
                ok,note=safe_command(candidate); syn,snote=syntax_ok(candidate) if ok else (False,note)
            if not ok: status='rejected-safety'
            elif not syn: status='rejected-syntax'
        except Exception as e:
            status='model-error:'+type(e).__name__
        elapsed=(time.perf_counter()-t0)/60.0
        exact=status=='ok' and normalize(candidate)==normalize(ref)
        struct=status=='ok' and structural_match(candidate,ref)
        attempts,hfrac,hmed=human_stats(by[tid]); bench=by[tid][0]['benchmark']
        results.append({'task_id':tid,'benchmark':bench,'passed':bool(exact),'elapsed_minutes':elapsed,'status':status,
                        'retry':retry,'exact_match':bool(exact),'structural_match':bool(struct),'human_attempts':attempts,
                        'human_solve_fraction':hfrac,'human_median_minutes':hmed,'candidate':candidate,
                        'candidate_sha256':hashlib.sha256(candidate.encode()).hexdigest()})
        per.append({'agent':1.0 if exact else 0.0,'human':hfrac,'benchmark':bench})
        print(f'[{i}/{len(selected)}] {tid} exact={exact} structural={struct} status={status} human={hfrac:.2f}',flush=True)

    fields=list(results[0].keys()) if results else ['task_id','benchmark','passed','elapsed_minutes']
    with (out/'incidentlens_run.csv').open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=fields); w.writeheader(); w.writerows(results)
    bybench={}
    for bench in ('cybashbench','nl2bash'):
        rr=[r for r in results if r['benchmark']==bench]; pp=[x for x in per if x['benchmark']==bench]
        if rr:
            bybench[bench]={'tasks':len(rr),'agent_exact':statistics.mean(1.0 if r['exact_match'] else 0.0 for r in rr),
                            'agent_structural':statistics.mean(1.0 if r['structural_match'] else 0.0 for r in rr),
                            'human_mean_task_solve_fraction':statistics.mean(x['human'] for x in pp)}
    ar=statistics.mean(x['agent'] for x in per) if per else 0.0; hr=statistics.mean(x['human'] for x in per) if per else 0.0
    summary={'protocol':'IncidentLens zero-cost same-task command benchmark v0.2','selected_tasks':len(selected),
             'skipped_unsafe_reference_tasks':len(skipped),'manifest_sha256':manifest_hash,
             'primary_metric':'strict canonical exact match (conservative lower bound; no paid judge)',
             'secondary_metric':'utility+flag structural match (diagnostic only)',
             'agent_exact_solve_rate':ar,'agent_structural_rate':statistics.mean(1.0 if r['structural_match'] else 0.0 for r in results) if results else 0.0,
             'human_mean_task_solve_fraction':hr,'delta_agent_minus_human':ar-hr,'bootstrap95_delta':bootstrap_delta(per),
             'by_benchmark':bybench,'mean_agent_minutes':statistics.mean(r['elapsed_minutes'] for r in results) if results else None,
             'safety_rejections':sum(r['status']=='rejected-safety' for r in results),'syntax_rejections':sum(r['status']=='rejected-syntax' for r in results),
             'model_errors':sum(str(r['status']).startswith('model-error') for r in results),
             'notes':['Same public task IDs as human attempts; no synthetic IncidentLens scores are substituted.',
                      'Exact matching is stricter than the original AI functional-equivalence grader, so agent success is a conservative lower bound.',
                      'Unsafe/network/privileged reference tasks are excluded before model prompting.',
                      'Generated commands are never executed; only bash -n syntax parsing is performed.',
                      'This measures a zero-cost external adapter using local Qwen plus IncidentLens-style safety/one-retry discipline, not frozen v0.73 alone.']}
    (out/'summary.json').write_text(json.dumps(summary,indent=2)); (out/'skipped.json').write_text(json.dumps(skipped,indent=2)); (out/'task_manifest.txt').write_text(manifest)
    print(json.dumps(summary,indent=2),flush=True)

if __name__=='__main__': main()
