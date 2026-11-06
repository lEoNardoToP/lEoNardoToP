<div align="center">

# Leonardo Rosati
### AI infrastructure · Systems engineering · Reliable software

**I build systems whose correctness can be inspected—not just demonstrated.**

[Portfolio](https://leonardotop.github.io/) · [Public code](https://github.com/lEoNardoToP?tab=repositories) · [LinkedIn](https://www.linkedin.com/in/leonardo-rosati-97b863273/)

</div>

---

### Start here — a 90-second technical review

| Project | What makes it interesting | Review |
|:--|:--|:--|
| **AtlasGuard** · Python / Linux | Explainable telemetry, PSI drift detection, runtime findings, Prometheus metrics | [Architecture & source](projects/atlasguard) · [Tests](projects/atlasguard/tests) |
| **AI Algorithms Portfolio** · C++ / Java / polyglot | Autodiff, a DQN, and independently checked alpha-beta contracts | [Source](https://github.com/lEoNardoToP/polyglot-alpha-beta-arena) · [CI](https://github.com/lEoNardoToP/polyglot-alpha-beta-arena/actions) |

### Deeper systems work — currently private

These are substantive engineering projects, **not public source releases**. Their descriptions are not substitutes for independent source review.

| System | Core engineering problem | Current disclosure |
|:--|:--|:--|
| **AgentForge** | Reproducible AI coding-agent evaluation; grader isolation and evidence integrity | Private; release validation in progress |
| **InferMesh** | Bounded inference admission, cancellation ownership and fair worker dispatch | Private; stress and lifecycle acceptance pending |
| **TensorForge** | C++ tensor graphs, reverse-mode autodiff, memory planning and native backends | Private; performance claims require reproduced benchmarks |
| **NanoExchange** | Price-time matching, write-ahead logging and crash recovery | Private; power-loss durability not certified |

> **How I work:** explicit invariants → adversarial tests → failure evidence → reproducible release gates. I distinguish simulated faults from physical failures and mock workloads from real model throughput.

### Read the implementation, not just the pitch

- **Observability:** [PSI drift implementation](projects/atlasguard/src/atlasguard/drift.py) and [regression suite](projects/atlasguard/tests).
- **ML fundamentals:** [C++ autodiff](https://github.com/lEoNardoToP/polyglot-alpha-beta-arena/tree/main/neuroforge-cpp), [Java DQN](https://github.com/lEoNardoToP/polyglot-alpha-beta-arena/tree/main/deepgrid-java).
- **Independent verification:** [algorithm contracts](https://github.com/lEoNardoToP/polyglot-alpha-beta-arena/blob/main/docs/CONTRACT_VALIDATION_2026-10-24.md) and [GitHub Actions](https://github.com/lEoNardoToP/polyglot-alpha-beta-arena/actions).

### About

Computer Science BSc student at the **University of Bologna**. Interested in **AI/ML infrastructure**, **backend & systems**, **reliability**, **developer tooling**, and **observability**.

**Tools:** Python · C++20 · Java · Linux · Docker · CMake · FastAPI · SQL · GitHub Actions · PyTorch

<sub>Engineering claims should be tied to a source revision, a runnable command, and observed evidence. No inflated badges, fabricated benchmarks, or simulated demo videos.</sub>
