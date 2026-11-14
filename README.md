<div align="center">

# Leonardo Rosati
### ML infrastructure · Systems engineering · Reliable software

**Build the mechanism. Break it on purpose. Make the result reproducible.**

[Portfolio](https://leonardotop.github.io/) · [Public code](https://github.com/lEoNardoToP?tab=repositories&type=public) · [LinkedIn](https://www.linkedin.com/in/leonardo-rosati-97b863273/)

Computer Science BSc · University of Bologna · Bologna, Italy

</div>

---

### Start here: public code you can inspect

| Project | Engineering focus | First thing to inspect |
|:--|:--|:--|
| [**AtlasGuard**](projects/atlasguard) · Python / Linux | Host telemetry, ML distribution drift and explainable runtime findings in one control-plane prototype | [Input and capacity contracts](projects/atlasguard/docs/DRIFT_INPUT_VALIDATION.md), [agent failure handling](projects/atlasguard/docs/AGENT_FAILURE_BEHAVIOR.md), [Docker acceptance evidence](projects/atlasguard/docs/DOCKER_RUNTIME_ACCEPTANCE.md) |
| [**AI Algorithms Portfolio**](https://github.com/lEoNardoToP/polyglot-alpha-beta-arena) · C++ / Java / eight languages | Reverse-mode autodiff, MLP training, a Java DQN and consistent alpha-beta engines | [Independent oracle validation](https://github.com/lEoNardoToP/polyglot-alpha-beta-arena/blob/main/docs/CONTRACT_VALIDATION_2026-10-24.md) and [technical notes](https://github.com/lEoNardoToP/polyglot-alpha-beta-arena/blob/main/TECHNICAL_INTERVIEW_NOTES.md) |

**AtlasGuard:** bounded admission, isolated drift baselines, explicit delivery failures, Prometheus metrics and least-privilege deployment. A prototype with documented limits and a path to reproduce its checks.

**AI Algorithms Portfolio:** the learning and search mechanics are implemented directly. Alpha-beta results are checked against an independent unpruned game-tree oracle; the Python check can cover all **4,520 reachable nonterminal positions**.

### Try the algorithms

Requires Python 3 and Git. No GPU or API key needed.

```bash
git clone https://github.com/lEoNardoToP/polyglot-alpha-beta-arena.git
cd polyglot-alpha-beta-arena
python3 python/main.py XX-OO---- X
```

Then inspect [the shared CLI contract and verification commands](https://github.com/lEoNardoToP/polyglot-alpha-beta-arena#independent-contract-verification).

### More work

**Leonardo's Lab** is my private systems workspace. Its source and evidence are not currently available to public visitors; start with the public projects above to evaluate my work.

[**Deep Vault: Risk & Loot**](https://github.com/lEoNardoToP/DeepVault) is a 2D roguelite for Android and web, in development. Its public repository is currently a placeholder.

### How I work

A working reference comes first. Optimizations must reproduce its results, failure handling is exercised on purpose, and every performance claim names its workload and hardware. Unverified behavior and unfinished capabilities belong in the documented limits.

**Tools:** Python · C++20 · Java · PyTorch · Triton · CUDA · FastAPI · Docker · CMake · Linux · SQL · OpenTelemetry · Prometheus · GitHub Actions
