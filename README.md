# 🧬 NeuroCross — BBB Nanocarrier Triage & Literature Gap Map
<p align="right"><sub><code>Version 2.0 Binary</code></sub></p>

![Python](https://img.shields.io/badge/Python-3.10%2B-blue?style=flat-square&logo=python)
![Status](https://img.shields.io/badge/Status-In_Development-orange?style=flat-square)
[![License](https://img.shields.io/badge/License-View--Only-red?style=flat-square)](./LICENSE)

## 📌 Description
 
NeuroCross is a personal research project, forked from the SENACYT blood-brain barrier (BBB) simulator and now developed independently. It models the adhesion of **functionalized nanocarriers** (currently liposomes only) to the luminal surface of the BBB, using DLVO/PMF physics and Boltzmann statistics, in the context of therapies for **Multiple Sclerosis**.
 
NeuroCross is not a validated quantitative predictor of drug delivery or therapeutic efficacy — no published literature currently anchors adhesion or permeation outputs end-to-end against real measurements, and no confirmed passive transcytosis mechanism exists for unligated liposomes. Given this, the project's goal is deliberately scoped as a **physical triage tool and literature gap map**: it screens out candidates that are physically unviable in adhesion or circulation survival, and documents — gate by gate — what is backed by real experimental contrast, what is borrowed by analogy, and what has no physics implemented at all. A gate without real contrast never returns FAIL, only UNKNOWN.
 
## 🚀 How to Run
 
The route to access the simulator is `/triage/index.html`. Then open the file in your browser.
 
> ⚠️ **Disclaimer**  
> This project is a work in progress. It does not predict therapeutic efficacy or final parenchymal delivery — that is explicitly out of scope. The underlying models, simulations, and parameters have not been fully validated or benchmarked against experimental data. As such, this software **should not be cited or relied upon as a definitive scientific reference** for clinical or academic publications at this stage.  
>  
> *Note: Currently, the simulator interface only supports Spanish.*
 
---
