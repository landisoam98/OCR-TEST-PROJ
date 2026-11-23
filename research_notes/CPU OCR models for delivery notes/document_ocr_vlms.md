# Document-specialist OCR VLMs (as of Nov 2026): CPU-only on Windows for delivery-note field extraction

Scope: target = Windows server, 8 CPU cores, 32 GB RAM, no GPU; tens to a few hundred printed delivery-note pages/day; need DN date, customer name, DN number; 30-90 s/page acceptable.

Labels used below: **[MEASURED]** = a third party or user timed it; **[VENDOR]** = model author claim; **[2025]** = older info, flagged.

## Which models realistically run on an 8-core CPU without a GPU, and how fast?

### Takeaway
Only the ~0.3B to ~1.2B models are realistic on CPU: PaddleOCR-VL-1.5/1.6 (0.9B), GLM-OCR (0.9B), Granite-Docling (258M), LightOnOCR-2 (1B), and MinerU's non-VLM "pipeline" backend. Nobody has published a clean x86 8-core CPU seconds-per-page figure for any of the OCR VLMs. The few measured CPU numbers are on an Apple M4 or on old pipelines, and they suggest roughly 10x slower than GPU. In practice that is tens of seconds to a few minutes per page, so a pilot benchmark on the actual server is mandatory. The 3B+ models (dots.mocr, DeepSeek-OCR-2, Nanonets-OCR2-3B, olmOCR-2-8B, Chandra-2 ~9B) are not realistic on CPU. Chandra OCR 2 ran out of memory on CPU in one test.

### Cited Findings

**Measured CPU numbers (the only ones found)**
- OCR Workbench (2026 repo; CPU/MPS = MacBook Air M4, GPU = RTX 5090). The times are **per whole document in seconds, not per page**, and page counts are not stated. [MEASURED] — [joneswack/ocr-workbench](https://github.com/joneswack/ocr-workbench)
  - NIST handwriting sample, CPU: Docling+Tesseract 3 s, Docling+RapidOCR 18 s, MinerU 25 s, marker 31 s, Docling-Granite 164 s, LightOnOCR-2-1B 170 s (vs 23 s on GPU).
  - World Food Bank report, CPU: MinerU 263 s, Docling-Granite 838 s, LightOnOCR-2-1B 2440 s (vs 191 s on GPU).
  - RKI German bulletin, CPU: MinerU 544 s, Docling-Granite 153 s, LightOnOCR-2-1B 4187 s (vs 416 s on GPU).
  - Chandra OCR 2: "OOM" on CPU and MPS (M4 Air); GPU only.
  - Inference: LightOnOCR-2 on CPU is roughly 7-13x slower than on an RTX 5090. MinerU's default CPU path is 1.5-6x slower than its GPU path.
- PaddleOCR 3.2.0 (classic `PaddleOCR` OCR pipeline, **not** the VL model) on Windows 11, CPU-only, Intel i7-10850H, 16 GB RAM: "~60s per single-page image" for a 2550x3300 TIFF scaled to 50%. No replies offered fixes. [MEASURED] [2025, Sept 30] — [PaddleOCR Discussion #16610](https://github.com/PaddlePaddle/PaddleOCR/discussions/16610)
- PaddleOCR-VL on CPU: about 531 s/page (vs about 114 s/page on GPU). The author says most of that is model load, and calls vLLM "the production answer" (single-run blog, unoptimized path). [MEASURED, secondhand via search snippet] — [Medium: I Just Wanted to Parse One Invoice. PaddleOCR-VL Had Other Plans](https://adityamangal98.medium.com/i-just-wanted-to-parse-one-invoice-paddleocr-vl-had-other-plans-3acc18055906)
- One author found that a 273 s/page result was an artifact of the unoptimized transformers runtime. Runtime choice dominates speed. [MEASURED, secondhand] — [Medium: dots.ocr vs PaddleOCR-VL on an 8GB Laptop](https://adityamangal98.medium.com/the-hidden-cost-of-local-ocr-dots-ocr-vs-paddleocr-vl-on-an-8gb-laptop-ac16af46c513)
- Docling standard (non-VLM) pipeline: "3.1 sec/page (x86 CPU)" and 1.27 sec/page on an M3 Max. [VENDOR paper] [2025, Jan] — [Docling paper arXiv 2501.17887](https://arxiv.org/pdf/2501.17887)
- GLM-OCR: a Hacker News commenter claims 1-2 s/page on a single core and ran 20 instances in parallel. It is an unverified anecdote with no hardware given, implausibly fast for a 0.9B VLM, and treated here as suspect. — [HN thread](https://news.ycombinator.com/item?id=46924075)
- Surya OCR 2.5 (non-VLM-class, not in scope but a CPU reference): "a few seconds to roughly 15 seconds per page" on CPU, from a blog guide. [MEASURED, informal] — [goremy.ai](https://goremy.ai/blog/articles/run-surya-ocr-2-5-locally)
- Tesseract reference: 0.27 s/page on CPU (2026 blog). — [joshua8.ai](https://joshua8.ai/ocr-models-vs-vision-llms-vs-tesseract/)

**Per-page times with unknown hardware (probably GPU, do not use for CPU sizing)**
- Instavar "full-50" run: GLM-OCR 1.252 s/page, FireRed-OCR 3.328 s/page, HunyuanOCR 6.884 s/page, DeepSeek-OCR-2 17.591 s/page. Hardware not stated. — [Instavar OCR leaderboard (Feb 2026, updated Sept 2026)](https://instavar.com/research/ocr/open-document-ocr-models)

**Vendor statements on CPU**
- PaddleOCR-VL docs: on x64 CPU, the PaddlePaddle, Transformers, PaddlePaddle+llama.cpp and Transformers+llama.cpp backends are supported. vLLM, SGLang and FastDeploy are not supported on CPU. The docs warn CPU speed "may not meet the requirements of a production environment." No CPU numbers are given. [VENDOR] — [PaddleOCR-VL usage tutorial](https://www.paddleocr.ai/latest/en/version3.x/pipeline_usage/PaddleOCR-VL.html)
- PaddleOCR v3.4.1 (14 Apr 2026) added a `llama-cpp-server` backend for PaddleOCR-VL. v3.7.0 (11 Jun 2026) released PP-OCRv6 (1.5M/7.7M/34.5M params), with a claimed "5.2x CPU speedup with OpenVINO" for the medium tier. [VENDOR] — [PaddleOCR releases](https://github.com/PaddlePaddle/PaddleOCR/releases)
- PaddleOCR-VL-1.5 community ONNX export: "specifically optimized for CPU inference", with FP32/Q8/Q4 vision encoder and decoder variants (NNCF / Intel Neural Compressor), any ONNX Runtime EP, and a Colab demo on OpenVINO. Apache-2.0. No timings. — [onnx-community/PaddleOCR-VL-1.5-ONNX](https://huggingface.co/onnx-community/PaddleOCR-VL-1.5-ONNX)
- llama.cpp OCR guide (10 Apr 2026): supported models are LightOnOCR, Qianfan-OCR, PaddleOCR-VL ("may have degraded performance"), GLM-OCR, DeepSeek-OCR, dots.ocr and HunyuanOCR. It says some "can even run on CPU with decent performance" but gives no figures. Q8_0 is the default quant. — [ngxson blog](https://blog.ngxson.com/using-ocr-models-with-llama-cpp)
- A llama.cpp issue reports PaddleOCR-VL-1.5 GGUF at about 529 tokens/s in an OCR task. Hardware is not given in the snippet, so it cannot be attributed to CPU. — [llama.cpp #20072](https://github.com/ggml-org/llama.cpp/issues/20072)
- MinerU 4.1.0: the default install "supports CPU inference on Windows, Linux, and macOS", and GPU is about 2-3x CPU speed on core workloads. 4.2.0 recommends the Basic tier on CPUs with 4+ logical cores and Standard with 12+. MinerU publishes no absolute pages/s figure. [VENDOR] — [MinerU changelog](https://opendatalab.github.io/MinerU/reference/changelog/)
- MinerU pipeline backend: 16 GB RAM minimum, 32 GB recommended, CLI `mineru -p input.pdf -o output/ -b pipeline` (secondary source). — [explainx.ai MinerU 3.4 guide](https://explainx.ai/blog/mineru-3-4-document-parsing-rag-agents-2026)
- PaddleOCR-VL-1.5 paper: throughput is reported only on H800/A100/H20 GPUs (best about 2.43 pages/s on H800 with FastDeploy). There is no CPU data. — [arXiv 2601.21957](https://arxiv.org/html/2601.21957v1)
- LightOnOCR-2-1B: 5.71 pages/s on one H100 (GPU only). — [LightOnOCR paper arXiv 2601.14251](https://arxiv.org/html/2601.14251v1)
- GLM-OCR official throughput: 1.86 pages/s for PDFs and 0.67 images/s for images, single replica, hardware unclear (GPU). — [localaimaster summary](https://localaimaster.com/models/glm-ocr)

### Inferences
- A 0.9B VLM through llama.cpp with Q8_0 on 8 x86 cores is the most promising CPU path (PaddleOCR-VL-1.5/1.6 or GLM-OCR). The LightOnOCR-2 M4 numbers (about 10x GPU) and the GLM-OCR GPU figure (about 0.5-1.3 s/page) together suggest something like 10-60 s/page on 8 cores. That is an **estimate, not a measurement**. It fits the 30-90 s/page budget, but only a pilot will confirm it.
- Delivery notes are short, sparse pages. Decode time scales with output tokens, so a prompt for just 3 fields (JSON) instead of full-page markdown should be much faster than the full-document timings above.
- Throughput maths: 300 pages/day at 60 s/page = 5 h of compute, which is feasible overnight or in a background queue even at the pessimistic end.
- 32 GB RAM is plenty for any 0.3-1.2B model (GGUF Q8 GLM-OCR is about 1 GB). RAM is not the binding constraint; CPU decode speed is.
- Parallelism: 2-4 llama.cpp worker processes with 2-4 threads each may beat one 8-thread process on batch throughput. This is unverified and should be tested.

### Gaps
- No x86 8-core CPU seconds-per-page benchmark was found for PaddleOCR-VL-1.5/1.6, GLM-OCR, MinerU2.5-Pro VLM, Granite-Docling, DeepSeek-OCR-2, HunyuanOCR or dots.mocr. All CPU sizing above is extrapolated.
- The OCR Workbench timings are per document with unknown page counts, and come from an ARM M4 rather than a Windows x86 server.
- The PP-OCRv6 OpenVINO "5.2x" claim has no baseline or absolute latency in the release notes.

## Which run natively on Windows (vs WSL/Docker)?

### Takeaway
The llama.cpp route is the cleanest native-Windows path: `winget install llama.cpp`, then `llama-server` with GGUF plus mmproj. It covers GLM-OCR, PaddleOCR-VL-1.5/1.6, LightOnOCR, DeepSeek-OCR, dots.ocr and HunyuanOCR, and Ollama also runs GLM-OCR natively. MinerU 4.x and Docling are pip-installable and claim Windows CPU support. Anything that needs vLLM, SGLang or FastDeploy (the default fast paths for PaddleOCR-VL, dots.mocr, olmOCR, Chandra and Nanonets) is Linux/Docker-only and usually NVIDIA-only, so it is irrelevant here.

### Cited Findings
- PaddleOCR-VL docs: "vLLM, SGLang, and FastDeploy cannot run natively on Windows. Please use our Docker images." The official Docker image is "NVIDIA GPU only." The docs do not say whether the PaddlePaddle or Transformers CPU paths work natively on Windows. — [PaddleOCR-VL usage tutorial](https://www.paddleocr.ai/latest/en/version3.x/pipeline_usage/PaddleOCR-VL.html)
- PaddleOCR-VL-1.5-GGUF (official, Apache-2.0): llama.cpp can be installed with `winget install llama.cpp`. Run `llama-server -m ...gguf --mmproj ...mmproj.gguf --temp 0`, then point PaddleOCR at it with `--vl_rec_backend llama-cpp-server`. Task prompts are `OCR:`, `Table Recognition:`, `Formula Recognition:`, `Chart Recognition:`, `Seal Recognition:` and `Spotting:`. The mmproj filename is inconsistent across the card's examples. — [PaddlePaddle/PaddleOCR-VL-1.5-GGUF](https://huggingface.co/PaddlePaddle/PaddleOCR-VL-1.5-GGUF)
- llama.cpp gained PaddleOCR-VL architecture support in February 2026 (PR #18825). — [Ollama issue #12685](https://github.com/ollama/ollama/issues/12685)
- Windows bugs: PaddleOCR + llama-cpp-server on Windows 11 crashes with HTTP 500 on images that contain curly quotes (a llama.cpp server token-decoding bug, closed "not planned"). — [PaddleOCR #18170](https://github.com/PaddlePaddle/PaddleOCR/issues/18170). PaddleOCR-VL produced zero output on a Windows AMD GPU, and a later llama.cpp build (b8986) reportedly fixed it. — [llama.cpp #22551](https://github.com/ggml-org/llama.cpp/issues/22551)
- Community "paddleocr-vl-cpu" OpenAI-compatible server (pure PyTorch/Transformers, MIT): "Ubuntu/Linux (Windows users please use WSL)". It recommends 16 GB+ RAM and gives no timings. — [Think-Core/paddleocr-vl-cpu](https://github.com/Think-Core/paddleocr-vl-cpu)
- GLM-OCR GGUF: ggml-org Q8_0 (0.9B, glm4 arch) plus mmproj. Community quants: Q4_K_M about 0.5 GB, Q8_0 about 1.0 GB. — [ggml-org/GLM-OCR-GGUF](https://huggingface.co/ggml-org/GLM-OCR-GGUF), [mradermacher/GLM-OCR-GGUF](https://huggingface.co/mradermacher/GLM-OCR-GGUF)
- GLM-OCR on CPU-only Ollama: the output repeats endlessly unless a stop sequence is configured, and even then it still repeats on some images. — [zai-org/GLM-OCR #220](https://github.com/zai-org/GLM-OCR/issues/220)
- MinerU: 4.1.0 claims CPU inference on Windows. 4.2.1 fixed managed-port probing on Windows, and 4.2.3 improved Windows process-tree cleanup. — [MinerU changelog](https://opendatalab.github.io/MinerU/reference/changelog/)
- dots.ocr / dots.mocr: vLLM is recommended (Docker `vllm/vllm-openai:v0.11.0`). Transformers works but is slower. There is a "Hugging Face inference with CPU" pointer to an issue comment, and no Windows notes. — [rednote-hilab/dots.ocr](https://github.com/rednote-hilab/dots.ocr)
- Granite-Docling: runs on Transformers (falls back to CPU with SDPA), vLLM (`revision="untied"`), SGLang, MLX and Docker Model Runner. GGUF quants are linked for llama.cpp, Ollama and LM Studio, and ONNX is mentioned. GPUs without bf16 output only "!!!", fixed by using float32. — [ibm-granite/granite-docling-258M](https://huggingface.co/ibm-granite/granite-docling-258M)

### Inferences
- Recommended Windows stack for a pilot: native llama.cpp (winget) with GLM-OCR Q8_0 or PaddleOCR-VL-1.6 GGUF, driven by a Python service that rasterizes the PDF (e.g. pypdfium2), deskews and crops the image, calls `/v1/chat/completions`, validates the result and files the PDF. No WSL or Docker is needed.
- The PaddleOCR Python package plus a llama.cpp backend adds PP-DocLayout layout detection. That helps accuracy but adds Windows dependency risk (PaddlePaddle CPU wheels). Calling the GGUF directly with a cropped header region is simpler.

### Gaps
- No source confirms that the PaddlePaddle-native or Transformers CPU backends of PaddleOCR-VL install cleanly on Windows Server specifically.
- No Windows-specific timing for any VLM was found.

## Which are good at key-information extraction (forms/invoices/delivery notes) vs full-page markdown?

### Takeaway
GLM-OCR is the only small (0.9B) model whose official card documents **prompted JSON-schema key-field extraction** (it has an "Information Extraction" mode and claims SOTA there without a number). That makes it the best fit for "give me date, customer, DN number" on CPU. PaddleOCR-VL-1.5/1.6 has fixed task prompts (OCR, table, formula, chart, seal, spotting) and no documented KIE prompt, so with it you OCR first and then extract with regex or rules (or a small LLM). Granite-Docling, LightOnOCR, olmOCR and MinerU are markdown/structure converters. dots.mocr can return JSON layout+text but is 3B. Research shows zero-shot field extraction on unusual layouts can be poor, and fine-tuning on few samples fixes it.

### Cited Findings
- GLM-OCR: MIT license (the bundled PP-DocLayoutV3 is Apache-2.0). OmniDocBench v1.5 94.62 (#1 claimed), olmOCR-bench 75.2 (excl. headers/footers, via ZAI API), ParseBench mean 29.6. Runtimes: vLLM, SGLang, Ollama, Transformers. Information extraction prompts "must follow a strict JSON schema". The example is an ID card template (id_number, names, date_of_birth, address, dates, sex). The KIE claim is "state-of-the-art" with no number. Tech report arXiv 2603.10910 (Mar 2026). [VENDOR] — [zai-org/GLM-OCR](https://huggingface.co/zai-org/GLM-OCR)
- PaddleOCR-VL: official prompts are OCR/Table/Formula/Chart/Seal/Spotting. The docs do not mention KIE. `prompt_label` only applies when `use_layout_detection=False`. — [PaddleOCR-VL-1.5-GGUF](https://huggingface.co/PaddlePaddle/PaddleOCR-VL-1.5-GGUF), [PaddleOCR-VL tutorial](https://www.paddleocr.ai/latest/en/version3.x/pipeline_usage/PaddleOCR-VL.html). The 2026 release notes don't mention PP-ChatOCR/KIE. — [PaddleOCR releases](https://github.com/PaddlePaddle/PaddleOCR/releases)
- PaddleOCR-VL-1.5 paper title: "Towards a Multi-Task 0.9B VLM for Robust In-the-Wild Document Parsing" (Jan 2026), targeting skew, warping and scanning artifacts, which is relevant to faint or skewed delivery notes. — [arXiv 2601.21957](https://arxiv.org/html/2601.21957v1)
- PaddleOCR-VL-1.6: released 28 May 2026, 96.3 on OmniDocBench v1.6, same architecture as 1.5 ("migration at zero cost"). — [PaddleOCR-VL tutorial](https://www.paddleocr.ai/latest/en/version3.x/pipeline_usage/PaddleOCR-VL.html)
- Granite-Docling-258M: Apache-2.0, released 17 Sep 2025 [2025], Idefics3 + SigLIP2 + Granite 165M. Output is DocTags, then Markdown/HTML. OCRBench 500 (vs SmolDocling 338), full-page OCR edit distance 0.45, table TEDS 0.97. Key-value extraction is not mentioned, and it is "not intended for general image understanding." — [granite-docling-258M](https://huggingface.co/ibm-granite/granite-docling-258M)
- dots.ocr-1.5 was rebranded **dots.mocr** (19 Mar 2026). It is listed as 3B, olmOCR-Bench 83.9 (vs 79.1 for dots.ocr), OmniDocBench v1.5 TextEdit 0.031. It has prompt modes (layout-all, OCR-only, etc.) and can return JSON with bboxes, categories and text. The license is MIT plus a separate "dots.ocr LICENSE AGREEMENT". — [rednote-hilab/dots.ocr](https://github.com/rednote-hilab/dots.ocr)
- CENTURIA field-extraction study (31 Aug 2026): zero-shot OCR models hit 15-32% transcription error and recovered domain-specific fields in <3% of cases. After LoRA fine-tuning on 57 samples, error dropped below 1.5% and field accuracy rose above 87%. The domain is archaeological forms, not delivery notes. — [arXiv 2608.30616](https://arxiv.org/abs/2608.30616)

### Inferences
- For printed delivery notes, a two-stage design is safer than trusting the VLM alone. Stage 1: VLM OCR of the page, or of the header crop, to text/markdown. Stage 2: deterministic rules (DN-number regex, date parsing, customer-name lookup against the company's customer master list) plus a confidence gate that routes failures to a human review folder. GLM-OCR's JSON mode can serve as a direct stage-1+2 alternative to A/B test.
- The CENTURIA result suggests that if zero-shot accuracy is poor on the company's layouts, a small LoRA on about 50-100 labelled DNs can close the gap. Fine-tuning would happen on a GPU elsewhere, and the result is then run on CPU via GGUF.

### Gaps
- No public KIE/form benchmark scores (e.g. FUNSD, SROIE, CORD, DocVQA-KIE) were found for GLM-OCR, PaddleOCR-VL-1.6 or the other small OCR VLMs in 2026 sources.
- No OCRBench (v1/v2) scores were found for GLM-OCR or PaddleOCR-VL-1.5/1.6 in the sources fetched.

## Licensing gotchas for commercial use (plus fact-sheet roll-up)

### Takeaway
The commercially clean options are GLM-OCR (MIT), the PaddleOCR-VL family and its GGUF/ONNX (Apache-2.0), Granite-Docling (Apache-2.0), DeepSeek-OCR-2 (reportedly Apache-2.0) and Docling (open). The models to watch are: Chandra OCR 2 (modified OpenRAIL-M, revenue cap, no competing with Datalab's API); HunyuanOCR (custom community license with territory and usage limits; the HunyuanOCR-1.5 paper page shows CC BY-NC-SA 4.0 and the weights are not yet released); Jina-OCR-v1 and GutenOCR (CC-BY-NC); dots.mocr (MIT plus an extra agreement); Nanonets-OCR2 (license unclear); and MinerU, which moved to a custom "MinerU Open Source License" in April 2026.

### Cited Findings
- Chandra OCR 2: code is Apache-2.0, weights are modified OpenRAIL-M. Free commercial use is limited to small organizations (one source cites a $2M revenue/funding threshold), and use competing with Datalab's API is barred. — [aimadetools 2026 comparison](https://www.aimadetools.com/blog/best-open-source-ocr-models-2026/), [vdf.ai](https://vdf.ai/blog/best-local-ocr-models/) (secondary; verify on model card)
- DeepSeek-OCR-2: reportedly 3B under Apache-2.0 (the original DeepSeek-OCR was MIT). Instavar lists it as 3B MoE (~500M active) plus an 80M compressor, OmniDocBench 91.09. — [andrew.ooo](https://andrew.ooo/answers/best-open-source-ocr-models-2026-ranked/), [Instavar](https://instavar.com/research/ocr/open-document-ocr-models)
- Nanonets-OCR2-3B: sources conflict, with one saying the model card states no license and another saying Apache-2.0. — [docsumo](https://www.docsumo.com/blog/best-ocr-models), [aitechmodel](https://aitechmodel.com/best-open-source-ocr-models/)
- HunyuanOCR (1B): "custom community license with territory and usage limits; legal review advised"; OmniDocBench 94.10 reported. — [Instavar](https://instavar.com/research/ocr/open-document-ocr-models). HunyuanOCR-1.5 (arXiv 6 Jul 2026, v3 17 Sep 2026): the paper says weights "will release"; claims 6.37x Transformers / 2.14x vLLM speedup via DFlash decoding; the arXiv page shows CC BY-NC-SA 4.0 (this may be the paper license, not the weights). — [arXiv 2607.04884](https://arxiv.org/abs/2607.04884)
- Jina-OCR-v1: CC-BY-NC-4.0. GutenOCR 3B/7B: CC-BY-NC weights. — [Instavar](https://instavar.com/research/ocr/open-document-ocr-models)
- MinerU 3.1.0 (18 Apr 2026): license moved to the "MinerU Open Source License", a custom license based on Apache-2.0. The VLM is MinerU2.5-Pro-2604-1.2B, later 2605-1.2B (3.3, 11 Jun 2026). 3.4 (18 Jun 2026) switched the pipeline OCR to PP-OCRv6 (about +11% on OmniDocBench v1.6, about 2x OCR speed). The pipeline scored 86.2 on OmniDocBench v1.5 at 3.0.0. The latest listed version is 4.2.3 (undated). — [MinerU changelog](https://opendatalab.github.io/MinerU/reference/changelog/)
- dots.mocr: MIT sidebar plus a separate "dots.ocr LICENSE AGREEMENT" file. — [rednote-hilab/dots.ocr](https://github.com/rednote-hilab/dots.ocr)

### Fact-sheet roll-up (Nov 2026)
| Model (latest) | Params | License | Key scores | CPU realistic? | Native Windows path | KIE/JSON prompt |
|---|---|---|---|---|---|---|
| PaddleOCR-VL-1.6 (28 May 2026; 1.5 Jan 2026) | 0.9B | Apache-2.0 | OmniDocBench v1.6 96.3 (1.6); 94.50 (1.5) | Yes, slow; official CPU backends = Paddle/Transformers/llama.cpp | llama.cpp GGUF (winget); ONNX/OpenVINO community export | No documented KIE; fixed task prompts |
| GLM-OCR (Mar 2026 report) | 0.9B | MIT (+Apache layout) | OmniDocBench v1.5 94.62; olmOCR-bench 75.2 | Yes (GGUF Q8 ~1 GB) | llama.cpp / Ollama (repetition bug, needs stop seq) | **Yes, JSON-schema prompts** |
| MinerU 4.2.x (pipeline / hybrid; VLM MinerU2.5-Pro-2605-1.2B) | 1.2B VLM; pipeline = small models | MinerU Open Source License (Apache-based, custom) | pipeline 86.2 OmniDocBench v1.5 | Yes, pipeline + CPU officially supported | pip, Windows CPU claimed | No (markdown/JSON layout) |
| Granite-Docling-258M (Sep 2025) | 258M | Apache-2.0 | OCRBench 500 | Yes, but measured 153-1564 s/doc on M4 CPU | Transformers / GGUF / Docling | No (DocTags/markdown) |
| Docling (standard pipeline) | n/a | MIT (toolkit) | n/a | Yes, 3.1 s/page x86 [2025 vendor] | pip | No (structure only) |
| LightOnOCR-2-1B | 1B | not confirmed in sources | olmOCR-Bench 83.2 | Possible but slowest measured on CPU (170-4187 s/doc, M4) | llama.cpp | No |
| DeepSeek-OCR-2 | 3B MoE (~0.5B active) | Apache-2.0 (reported) | OmniDocBench 91.09 | Doubtful | llama.cpp (DeepSeek-OCR listed) | Limited |
| dots.mocr (ex dots.ocr-1.5, Mar 2026) | 3B | MIT + extra agreement | olmOCR-Bench 83.9 | Not practical | vLLM/Docker; Transformers slow | JSON layout output |
| HunyuanOCR 1.0 / 1.5 (Jul 2026, weights pending) | 1B | Restrictive community / NC | OmniDocBench 94.10 (1.0) | Unknown | llama.cpp (HunyuanOCR listed) | IE listed as task, no scores |
| olmOCR-2-8B | 8B | not confirmed | olmOCR-Bench 80.4 | No | vLLM/GPU | No |
| Chandra OCR 2 | ~9B | OpenRAIL-M modified, revenue cap | olmOCR-Bench 81.7 | No (OOM on CPU) | GPU only | No |
| Nanonets-OCR2-3B | 3B | unclear | — | Not practical | — | Some |
| Newer 2026 entrants: OvisOCR2 (0.8B, OmniDocBench 96.58 reported), FireRed-OCR (2B, Mar 2026), Qianfan-OCR, OCRia-1 (4B, Oct/Nov 2026, ParseBench 0.87) | — | mostly not stated | see cells | Unknown / no CPU data | Qianfan-OCR in llama.cpp | not stated |

Sources for the roll-up rows are in the findings above. OvisOCR2, FireRed-OCR and Qianfan-OCR: [Instavar](https://instavar.com/research/ocr/open-document-ocr-models). OCRia-1: [arXiv 2611.00092](https://arxiv.org/abs/2611.00092). Qianfan-OCR in llama.cpp: [ngxson blog](https://blog.ngxson.com/using-ocr-models-with-llama-cpp).

### Inferences
- Shortlist for this project: (1) GLM-OCR GGUF via llama.cpp, with JSON key-field prompts; (2) PaddleOCR-VL-1.6 GGUF via llama.cpp, with `OCR:` plus regex/rules extraction; (3) a non-VLM fallback such as the MinerU pipeline or PP-OCRv6 (OpenVINO) plus rules, which is fastest on CPU, though classic OCR may struggle more on faint scans. All three are commercially usable (MinerU needs its custom license reviewed).
- Avoid Chandra, HunyuanOCR, Jina-OCR and GutenOCR for a commercial deployment unless legal signs off.

### Gaps
- License texts for LightOnOCR-2, olmOCR-2, Nanonets-OCR2 and SmolDocling were not verified from primary model cards in this pass.
- No DeepSeek-OCR-2 CPU data or KIE capability details were found.
- No benchmark covers faint, skewed scanned delivery notes specifically. OmniDocBench and olmOCR-bench are general parsing benchmarks, so a 20-50 page in-house test set is needed.
