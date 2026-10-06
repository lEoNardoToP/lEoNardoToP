# AtlasGuard application portfolio

This directory contains a reproducible candidate portfolio built around AtlasGuard for:

- **Canonical** - Linux, resilient Python software, systemd, container hardening and CI.
- **SurveyMonkey** - ML platform telemetry, distribution drift detection and Prometheus observability.
- **Sysdig** - explainable runtime findings, Linux/container concepts and a hands-on lab path toward Falco/eBPF.

## Generated application materials

After the GitHub Actions build completes, the complete package is under [generated/](generated/):

- [PowerPoint presentation](generated/AtlasGuard_Candidate_Portfolio_Canonical_SurveyMonkey_Sysdig.pptx)
- [Presentation PDF](generated/AtlasGuard_Candidate_Portfolio_Canonical_SurveyMonkey_Sysdig.pdf)
- [Complete ZIP package](generated/AtlasGuard_Candidate_Portfolio_Package.zip)
- [Canonical demo video](generated/videos/AtlasGuard_Canonical_Demo.mp4)
- [SurveyMonkey demo video](generated/videos/AtlasGuard_SurveyMonkey_Demo.mp4)
- [Sysdig demo video](generated/videos/AtlasGuard_Sysdig_Demo.mp4)
- [Canonical brief - DOCX](generated/docs/AtlasGuard_Canonical_Technical_Brief.docx)
- [Canonical brief - PDF](generated/docs/AtlasGuard_Canonical_Technical_Brief.pdf)
- [SurveyMonkey brief - DOCX](generated/docs/AtlasGuard_SurveyMonkey_Technical_Brief.docx)
- [SurveyMonkey brief - PDF](generated/docs/AtlasGuard_SurveyMonkey_Technical_Brief.pdf)
- [Sysdig brief - DOCX](generated/docs/AtlasGuard_Sysdig_Technical_Brief.docx)
- [Sysdig brief - PDF](generated/docs/AtlasGuard_Sysdig_Technical_Brief.pdf)

## Reproducible build

```bash
python -m pip install pillow python-pptx python-docx reportlab
# ffmpeg must also be installed
python build_portfolio.py
```

The workflow `.github/workflows/atlasguard-portfolio-build.yml` builds all binary assets inside GitHub Actions and commits them back into this repository. This keeps the application material reviewable and reproducible instead of relying on external file-hosting links.

## Scope

The materials deliberately distinguish implemented functionality from roadmap items. AtlasGuard does not claim production eBPF collection, distributed durability, or cloud-scale ML tenure that has not been demonstrated.
