<div align="center">

# Leonardo Rosati

### ML infrastructure · Systems engineering · Failure analysis

**Build the mechanism. Break the assumptions. Keep the evidence.**

[Portfolio](https://leonardotop.github.io/) · [LinkedIn](https://www.linkedin.com/in/leonardo-rosati-97b863273/)

Computer Science BSc · University of Bologna · Bologna, Italy

</div>

```text
leo@lab:~$ cat engineering.conf

focus       = ML internals / Linux systems / reliable execution
method      = implement -> test -> inject failures -> document limits
entrypoint  = public source + runnable commands below
```

## Inspect the code

| System | What to inspect | Start here |
|:--|:--|:--|
| **AtlasGuard** · Python / Linux | Host telemetry, PSI drift detection, explainable runtime rules and bounded ingestion | [Source & quick start](https://github.com/lEoNardoToP/lEoNardoToP/tree/main/projects/atlasguard) · [Hands-on lab](https://github.com/lEoNardoToP/lEoNardoToP/blob/main/projects/atlasguard/docs/HANDS_ON_LAB.md) |
| **AI Algorithms Portfolio** · C++ / Java / polyglot | From-scratch autodiff and MLP, a Java DQN, and alpha-beta engines in eight languages | [Source & reviewer route](https://github.com/lEoNardoToP/polyglot-alpha-beta-arena) · [Independent contract checker](https://github.com/lEoNardoToP/polyglot-alpha-beta-arena/blob/main/scripts/verify_contract.py) |

### Run something in one minute

Requires Git and Python 3.10+. No GPU, dependencies or API key for this example.

```bash
git clone https://github.com/lEoNardoToP/polyglot-alpha-beta-arena.git
cd polyglot-alpha-beta-arena
python3 python/main.py XX-OO---- X
```

The engine must choose **move 2**, with **score 9** (cells are numbered 0–8).
Then inspect the [unpruned oracle](https://github.com/lEoNardoToP/polyglot-alpha-beta-arena/blob/main/scripts/verify_contract.py)
that checks the engines independently.

### Follow the failure paths

- **Bad telemetry / capacity pressure:** AtlasGuard rejects nonfinite input and caps service/model identities. [Input and capacity contract](https://github.com/lEoNardoToP/lEoNardoToP/blob/main/projects/atlasguard/docs/DRIFT_INPUT_VALIDATION.md).
- **Rejected deliveries / cancellation:** agent behavior is documented with failure and cleanup checks. [Agent contract](https://github.com/lEoNardoToP/lEoNardoToP/blob/main/projects/atlasguard/docs/AGENT_FAILURE_BEHAVIOR.md).
- **Engines that agree on the wrong answer:** the arena checks against an independent game-tree oracle, including an exhaustive Python route over 4,520 nonterminal positions. [Validation scope and evidence](https://github.com/lEoNardoToP/polyglot-alpha-beta-arena/blob/main/docs/CONTRACT_VALIDATION_2026-10-24.md).

## Behind the lab door

**Leonardo's Lab is currently private.** Its source, runnable demos and evidence
documents require repository access. The four systems explore:

| Project | Engineering focus |
|:--|:--|
| **TensorForge** · C++20 | Tensor IR, automatic differentiation and execution backends |
| **InferMesh** · Python | Batching, admission control, deadlines and supervised workers |
| **NanoExchange** · C++20 | Price-time matching, write-ahead logging and crash recovery |
| **AgentForge** · Python | Task contracts, isolated execution and independent grading |

For immediately inspectable work, use the public projects above.

## Engineering rules

A working reference comes first. Optimizations must reproduce its results.
Failure handling gets exercised on purpose. Performance claims name the workload,
environment and measurement method; unverified behavior stays an explicit limit.

**Tools:** Python · C++20 · Java · PyTorch · Triton · CUDA · FastAPI · Docker · CMake · Linux · SQL · OpenTelemetry · Prometheus · GitHub Actions
