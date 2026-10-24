# Leonardo Rosati

**Software engineer focused on AI infrastructure, backend systems and inspectable reliability.**

BSc Computer Science at the **University of Bologna — in progress**.

I build systems whose behavior I can explain and test: how requests are scheduled, how
state survives a crash, how gradients flow, and how an evaluator distinguishes a bad
submission from its own failure. My work spans Python, C++ and Java, with runnable
examples and explicit engineering tradeoffs.

## Start here — a five-minute technical review

| Interest | Project to open | Concrete mechanism to inspect |
|---|---|---|
| ML platforms / observability | [AtlasGuard](projects/atlasguard) · public | Linux telemetry → PSI distribution-shift detection → explainable runtime findings |
| AI algorithms / fundamentals | [AI Algorithms Portfolio](https://github.com/lEoNardoToP/polyglot-alpha-beta-arena) · public | C++ autodiff/Adam, Java DQN and a shared alpha-beta contract across eight languages |
| Compilers / reliable runtimes | [Leonardo's Lab](https://github.com/lEoNardoToP/Leonardo-sLab) · private source | Tensor graphs, fair inference scheduling, durable matching and calibrated software evaluation |

For public source, begin with **AtlasGuard** or **AI Algorithms Portfolio**. Leonardo's Lab
and the R&D projects below require repository access; their source is not published here.

### AtlasGuard · observability and runtime signals

A Linux-oriented control-plane prototype combining host telemetry, inference observations,
Population Stability Index drift monitoring, deterministic security rules and Prometheus
metrics. The source separates collection, API contracts, numerical detection and findings,
with Docker/systemd deployment material and a documented threat model.

**Review:** [architecture and quick start](projects/atlasguard) →
[drift implementation](projects/atlasguard/src/atlasguard/drift.py) →
[tests](projects/atlasguard/tests).

**Engineering discussion:** how monitoring itself stays bounded, how a reference distribution
is established, and which findings come from explicit rules rather than opaque model scores.
This is a prototype; production acceptance needs the deployment and failure evidence appropriate
to the target environment.

### AI Algorithms Portfolio · learn the mechanism by running it

[NeuroForge C++](https://github.com/lEoNardoToP/polyglot-alpha-beta-arena/tree/main/neuroforge-cpp)
implements reverse-mode autodiff, MLP training, binary cross-entropy, Adam and gradient checking.
[DeepGrid Java](https://github.com/lEoNardoToP/polyglot-alpha-beta-arena/tree/main/deepgrid-java)
implements a compact DQN with manual backpropagation, replay and a target network.
The same repository includes minimax/alpha-beta engines with one JSON contract in eight languages.

```bash
./run_ai_mechanics.sh
```

**Engineering discussion:** how a local derivative becomes a training loop, why target networks
stabilize value-based learning, and how independent expected results differ from engines merely
agreeing with each other. [Technical interview notes](https://github.com/lEoNardoToP/polyglot-alpha-beta-arena/blob/main/TECHNICAL_INTERVIEW_NOTES.md).

### Leonardo's Lab · four systems from expression to execution

- **TensorForge:** C++20 typed tensor IR, graph optimization and liveness-aware workspace reuse.
- **InferMesh:** bounded inference scheduling, compatible batching, fair spawned workers and deadlines.
- **NanoExchange:** price-time matching, indexed cancellation, persisted request identities and WAL recovery.
- **AgentForge:** six calibrated software tasks, local/Docker evaluation and provenance-bearing reports.

The CPU baselines are merged, with source-linked local/native/Docker verification. GPU code
generation, multi-machine serving and production durability remain separate milestones.
[Reviewer route — requires access](https://github.com/lEoNardoToP/Leonardo-sLab/blob/main/docs/REVIEWER_GUIDE.md).

## Private R&D

**HypoWeb** — scientific evidence orchestration: source retrieval, claim extraction, hypothesis
construction/challenge and provenance across research runs. Focus: scientific AI, evaluation,
research workflow reliability and evidence quality.

**IncidentLens** — controlled security-analysis workflows in lab environments, with structured
findings, repeatable evaluation and defensive reporting. Focus: C++/Python, CodeQL, Docker
and analysis automation.

Private project descriptions are areas of work, not public benchmark or production-adoption claims.

## Roles and stack

I'm interested in **ML platform / AI infrastructure**, **backend and systems engineering**,
**observability/reliability**, **developer tools** and **defensive security tooling**.

- **Daily engineering:** Python, C++, Java, SQL, Git, CMake, shell and GitHub Actions.
- **Backend and operations:** FastAPI, Django, REST APIs, Docker, Linux/macOS and Prometheus.
- **AI mechanics and evaluation:** NumPy, PyTorch, scikit-learn, from-scratch ML/RL and reproducible task evaluation.
- **Additional languages:** JavaScript/TypeScript, C, PHP, C# and Swift.

## Earlier application work

[Lernify](https://github.com/lEoNardoToP/Lernify_WEBAPP),
[Logics](https://github.com/lEoNardoToP/Logics) and
[AVIATIONTEST](https://github.com/lEoNardoToP/AVIATIONTEST) show my development history in web
applications, frontend/backend integration and Django/PHP. Their current scope and setup are
explained in their own repositories.

## Contact

[GitHub · @lEoNardoToP](https://github.com/lEoNardoToP) ·
[LinkedIn · Leonardo Rosati](https://www.linkedin.com/in/leonardo-rosati-97b863273/)
