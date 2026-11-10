<div align="center">

# Leonardo Rosati
### ML infrastructure · Systems engineering · Reliable software

**I build the mechanisms underneath ML systems, and I test them until their failure boundaries are written down.**

[Portfolio](https://leonardotop.github.io/) · [Leonardo's Lab](https://github.com/lEoNardoToP/Leonardo-sLab) · [LinkedIn](https://www.linkedin.com/in/leonardo-rosati-97b863273/)

Computer Science BSc · University of Bologna · Bologna, Italy

</div>

---

### Leonardo's Lab: four systems, one engineering standard

[**Leonardo's Lab**](https://github.com/lEoNardoToP/Leonardo-sLab) is my main body of work: four projects that go from tensor expressions to reliable execution. Each has a runnable example, explicit contracts, regression tests and dated, source-linked evidence.

| Project | The question it answers | Look at |
|:--|:--|:--|
| [**TensorForge**](https://github.com/lEoNardoToP/Leonardo-sLab/tree/main/projects/tensorforge) · C++20 | How does a tensor graph generate its own gradients and run with safe memory reuse? | Typed IR → generated backward graph → native C++ loops, LibTorch and Triton backends, checked on a real T4 |
| [**InferMesh**](https://github.com/lEoNardoToP/Leonardo-sLab/tree/main/projects/infermesh) · Python | How do concurrent requests share finite workers without losing deadlines or fairness? | Batching, per-tenant admission, supervised worker processes, streaming HTTP/SSE, OpenTelemetry tracing |
| [**NanoExchange**](https://github.com/lEoNardoToP/Leonardo-sLab/tree/main/projects/nanoexchange) · C++20 | How does a matching engine survive crashes and client retries without losing order? | Price-time book, fsynced WAL, fenced compaction, 1,852 injected POSIX fault scenarios |
| [**AgentForge**](https://github.com/lEoNardoToP/Leonardo-sLab/tree/main/projects/agentforge) · Python | How do you tell a bad AI-agent submission from a broken evaluator? | Calibrated task contracts, Docker isolation, independent grading, forged-output rejection |

Plus [six from-scratch experiments](https://github.com/lEoNardoToP/Leonardo-sLab/blob/main/docs/EXPERIMENT_GUIDE.md): tensors and convolution, autograd, a tiny Transformer, an attention explorer, Triton GPU kernels and evidence-aware retrieval.

**Two-minute check, no GPU or API key needed:**

```bash
git clone https://github.com/lEoNardoToP/Leonardo-sLab && cd Leonardo-sLab
PYTHONPATH=projects/infermesh/src python3 -m infermesh.demo
```

[Five-minute reviewer route](https://github.com/lEoNardoToP/Leonardo-sLab/blob/main/docs/REVIEWER_GUIDE.md) · [Current evidence](https://github.com/lEoNardoToP/Leonardo-sLab/blob/main/docs/CURRENT_EVIDENCE.md) · [Roadmap and open limits](https://github.com/lEoNardoToP/Leonardo-sLab/blob/main/ROADMAP.md)

### Smaller public projects

| Project | What it is |
|:--|:--|
| [**AtlasGuard**](projects/atlasguard) · Python / Linux | Linux telemetry agent and control plane: PSI drift detection, explainable runtime findings, Prometheus metrics, hardened Docker and systemd deployment, CI on Python 3.11 and 3.12 |
| [**AI Algorithms Portfolio**](https://github.com/lEoNardoToP/polyglot-alpha-beta-arena) · C++ / Java / polyglot | C++ autodiff and MLP, a Java DQN, and alpha-beta engines in eight languages, each checked in CI against an independent unpruned game-tree oracle |
| [**Deep Vault: Risk & Loot**](https://github.com/lEoNardoToP/DeepVault) · game | 2D roguelite for Android and web, in development |

### How I work

A working reference comes first. Optimizations must reproduce its results, failure handling is exercised on purpose, and every performance claim names its workload and hardware. Where something is not verified (physical power loss, multi-host serving, GPU speedups), the docs say so.

**Tools:** Python · C++20 · Java · PyTorch · Triton · CUDA · FastAPI · Docker · CMake · Linux · SQL · OpenTelemetry · Prometheus · GitHub Actions
