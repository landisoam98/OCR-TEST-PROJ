# Classic OCR engines + "OCR then small text LLM" pipelines for CPU-only delivery-note key-field extraction (as of Nov 2026)

Scope: Windows server, 8 CPU cores, 32 GB RAM, no GPU; tens to a few hundred scanned A4 pages a day. Target fields: DN date, customer name, DN number, returned as JSON. Languages likely needed: English, Malay, Chinese.

Legend: **[MEASURED]** = a number from a stated benchmark with stated hardware. **[CLAIM]** = a vendor or project claim with no independent check, or a figure whose method isn't given. **[OLD]** = from before 2026.

---

## Q1. What is the fastest accurate CPU OCR on Windows today?

### Takeaway
PaddleOCR's **PP-OCRv6** (released 11 June 2026 with PaddleOCR 3.7.0) is the strongest open CPU OCR found. The **small** tier runs in about 0.6 s per image on a server Xeon through OpenVINO or ONNX Runtime. The easiest Windows route is **RapidOCR ≥3.9.0** (`pip install rapidocr onnxruntime`), which now ships PP-OCRv6 small as its default. Tesseract is a fast fallback but much less accurate downstream. OnnxTR is a credible second option. Surya/Marker and EasyOCR are too slow on CPU or lose on accuracy.

### Cited Findings

**PaddleOCR 3.x / PP-OCRv5 / PP-OCRv6**
- PP-OCRv6 was released on 11 June 2026 alongside PaddleOCR 3.7.0. It has three tiers, tiny (1.5M), small (7.7M) and medium (34.5M) parameters, for edge, mobile and server use. — [arXiv 2606.13108 (PP-OCRv6)](https://arxiv.org/html/2606.13108); [PaddleOCR 3.7.0 PP-OCRv6 docs](https://www.paddleocr.ai/v3.7.0/en/version3.x/algorithm/PP-OCRv6/PP-OCRv6.html)
- **[MEASURED, project's own benchmark]** CPU end-to-end seconds per image on an **Intel Xeon 8350C** over 200 images, including image I/O and pre/post-processing. The thread count isn't stated.
  - PaddlePaddle: v6 medium 2.05, v6 small 0.79, v6 tiny 0.32, v5 server 2.04, v5 mobile 0.80
  - OpenVINO: v6 medium **1.40**, v6 small **0.59**, v6 tiny 0.20, v5 server 7.30, v5 mobile 0.78
  - ONNX Runtime: v6 medium 3.31, v6 small **0.61**, v6 tiny 0.22, v5 server 6.36, v5 mobile 0.61

  Source: [PP-OCRv6 docs](https://www.paddleocr.ai/v3.7.0/en/version3.x/algorithm/PP-OCRv6/PP-OCRv6.html)
- **[CLAIM]** PP-OCRv6 medium beats PP-OCRv5 server by +5.1% recognition accuracy and +4.6% detection Hmean. The project also cites a "5.2× end-to-end CPU speedup". — [PP-OCRv6 docs](https://www.paddleocr.ai/v3.7.0/en/version3.x/algorithm/PP-OCRv6/PP-OCRv6.html); [search summary of PaddleOCR announcements / hyper.ai](https://hyper.ai/en/stories/d3ee689571cc134a197942095f45b44d)
- **[MEASURED, project's own benchmark]** Detection average Hmean: PP-OCRv6 medium 86.2, PP-OCRv5 server 81.6, Qwen3-VL-235B 38.3, GPT-5.5 45.6, Gemini-3.1-Pro 46.8. Recognition weighted average: v6 medium 83.2, v5 server 78.1, Qwen3-VL-235B 74.9, Gemini-3.1-Pro 71.4, GPT-5.5 64.2. These are the vendor's own test sets, and the VLM detection scores mostly measure box-localization ability, not reading. — [PP-OCRv6 docs](https://www.paddleocr.ai/v3.7.0/en/version3.x/algorithm/PP-OCRv6/PP-OCRv6.html)
- Languages: the v6 medium and small tiers cover **50 languages in one model**: Simplified and Traditional Chinese, English, Japanese, plus "46 Latin-script languages". Tiny covers 49 (no Japanese). The page names neither Malay nor the full list, but Malay uses the Latin alphabet. — [PP-OCRv6 docs](https://www.paddleocr.ai/v3.7.0/en/version3.x/algorithm/PP-OCRv6/PP-OCRv6.html)
- The PP-OCRv6 docs say it runs on Windows, Linux and Mac. ONNX Runtime is available as a high-performance backend through `enable_hpi=True`, which needs extra installs. — [PP-OCRv6 docs](https://www.paddleocr.ai/v3.7.0/en/version3.x/algorithm/PP-OCRv6/PP-OCRv6.html)
- **[MEASURED, project, older doc]** PP-OCRv5 on an Intel Xeon Gold 6271C over 200 general and document images: v5 mobile 1.75 s, v4 mobile 1.37 s, v5 server 4.34 s, v4 server 5.42 s per image. Peak RAM was about 2.2 GB for mobile and about 4.0 GB for server. v5 is slower than v4 on CPU because of its larger dictionary. — [PP-OCRv5 docs](https://www.paddleocr.ai/latest/en/version3.x/algorithm/PP-OCRv5/PP-OCRv5.html)
- **[MEASURED, project]** PP-OCRv5 server/mobile recognition accuracy: printed Chinese 0.901/0.861, printed English 0.868/0.875, handwritten English 0.581/0.494. The PP-OCRv5 page lists only Chinese (Simplified, Traditional, Pinyin), English and Japanese. Latin-script multilingual coverage arrives in v6. — [PP-OCRv5 docs](https://www.paddleocr.ai/latest/en/version3.x/algorithm/PP-OCRv5/PP-OCRv5.html)

**RapidOCR**
- RapidOCR **v3.9.0 made the PP-OCRv6 small detection and recognition models the defaults**. That release runs only on ONNX Runtime and OpenVINO, with other engines planned for later versions. v3.9.1 appears on AUR. v3.9.2 appears in a Hugging Face mirror dated 2026-08, but I couldn't confirm it on the GitHub releases page. — [newreleases.io: RapidOCR v3.9.0](https://newreleases.io/project/github/RapidAI/RapidOCR/release/v3.9.0); [AUR python-rapidocr 3.9.1](https://aur.archlinux.org/packages/python-rapidocr?O=0); [CSDN post on v3.9.x engine rollout](https://aicoding.csdn.net/6a68817510ee7a33f2937d77.html)
- License is Apache-2.0, and the converted models are redistributed under their original licenses. Install with `pip install rapidocr onnxruntime`. A badge in the page's markup indicates Linux, Windows and Mac support. The README gives no speed numbers ("extreme speed" is a claim only). — [RapidOCR GitHub](https://github.com/RapidAI/RapidOCR)
- A May 2026 benchmark ran RapidOCR 3.8.1 with OpenVINO 2026.1.0 on CPU. I found it only as a search snippet and didn't fetch its numbers. — [search result referencing RapidOCR + OpenVINO CPU test](https://redirect.github.com/RapidAI/RapidOCR/releases)

**Tesseract 5.x**
- **[MEASURED, 2026 paper]** In the WebPII paper, Tesseract took about 453 ms per image on CPU, while PaddleOCR took 2,143 ms. In that test, EasyOCR and PaddleOCR ran with GPU acceleration and were still 1.6–4.7× slower. These were web screenshots, not scans. — [WebPII, arXiv 2603.17357](https://arxiv.org/pdf/2603.17357)
- **[MEASURED, Sept 2026 paper]** OCR quality on business documents, as mean CER/WER against gold text:

  | Dataset | PaddleOCR | EasyOCR | Tesseract |
  |---|---|---|---|
  | SROIE receipts | **0.31 / 0.46** | 0.41 / 0.71 | 0.43 / 0.66 |
  | CORD receipts | **0.48 / 0.62** | 0.50 / 0.85 | 0.80 / 0.98 |
  | FUNSD forms | **0.42 / 0.57** | 0.50 / 0.73 | 0.55 / 0.72 |

  These are sequence-level rates, so they include reading-order and line-grouping differences, not only glyph errors. — [From Pixels to Pairs, arXiv 2609.17538](https://arxiv.org/pdf/2609.17538)
- **[CLAIM / unclear method]** A 2026 guide puts Tesseract 5.5 at about 0.5 s/page, PaddleOCR v5 at about 1 s/page and EasyOCR at about 2 s/page on CPU. — [slavadubrov OCR guide, Mar 2026](https://slavadubrov.github.io/blog/2026/03/04/ocr-guide/)
- **[MEASURED, GPU box, vendor-run]** On SROIE, CPU Tesseract had a median of about 671 ms/page. docTR on an RTX 4090 had about 109 ms. — [imagetotable.ai OCR latency benchmark 2026](https://imagetotable.ai/references/ocr-latency-benchmark)

**docTR / OnnxTR**
- **[MEASURED, project README, OLD v0.1.x era]** On an i7-14700K CPU:
  - FUNSD: docTR 0.8.1 about 1.29 s/page, OnnxTR about 0.57 s/page, OnnxTR 8-bit about 0.38 s/page.
  - CORD: docTR about 0.60 s/page, OnnxTR about 0.25 s/page, OnnxTR 8-bit about 0.14 s/page.
  - The lightest mobilenet combination ran at about 0.12–0.17 s/page, though the README doesn't clearly say whether that was on CPU.

  Sources: [OnnxTR PyPI 0.1.2](https://pypi.org/project/onnxtr/0.1.2); [OnnxTR PyPI 0.3.0](https://pypi.org/project/onnxtr/0.3.0); [OnnxTR GitHub](https://github.com/felixdittrich92/OnnxTR)
- **[MEASURED, blog]** Idle memory: PaddleOCR about 450 MB, EasyOCR about 800 MB, docTR about 320 MB. — [dev.to memory/latency test](https://dev.to/tildalice/paddleocr-vs-easyocr-vs-doctr-memory-latency-test-id0)

**Surya / Marker**
- **[MEASURED, project README, OLD]** The OnnxTR README's CPU comparison table puts Surya at roughly 35–49 s/page on CPU. — [OnnxTR PyPI 0.2.0](https://pypi.org/project/onnxtr/0.2.0)
- Marker v2 adds full CPU support and defaults to "fast" mode on CPU. In that mode it uses the PDF text layer and calls the VLM only where needed, which doesn't help image-only scans. — [Marker releases](https://github.com/datalab-to/marker/releases)
- **[MEASURED, unclear unit]** On an Intel N100 (4 cores), Surya OCR 2 took 137.84 s on CPU versus 7.93 s for PaddleOCR. The post doesn't say whether that is per page or per test set. — [wikidocs.net](https://wikidocs.net/441138)

**EasyOCR**
- **[MEASURED, OLD]** In an assistive-technology test, EasyOCR took 0.82 s/image on CPU versus 0.3 s for Tesseract. — [arXiv 2308.00801](https://arxiv.org/pdf/2308.00801)
- EasyOCR gives the worst downstream extraction scores of the three engines in the 2026 "Pixels to Pairs" benchmark (see Q3). — [arXiv 2609.17538](https://arxiv.org/pdf/2609.17538)

**Windows built-in OCR (Windows.Media.Ocr)**
- It ships free with Windows 10 and 11. A vendor-written comparison says it supports 25+ languages versus Tesseract's 100+. — [HackerNoon .NET OCR comparison 2026](https://hackernoon.com/c-ocr-libraries-the-definitive-net-comparison-for-2026)
- Microsoft's docs say the APIs only work in desktop apps with package identity, which complicates use from a plain server service. — [Microsoft Learn: Windows.Media.Ocr](https://learn.microsoft.com/uwp/api/windows.media.ocr)
- I found no independent accuracy or speed benchmark of Windows.Media.Ocr against PaddleOCR or Tesseract. Search results were dominated by IronOCR vendor pages.

### Inferences
- **The Xeon 8350C is a 32-core server part**, and the docs don't state the thread count. On an 8-core Windows server, expect PP-OCRv6 small to take roughly 0.8–2 s per A4 page at 200–300 DPI, and medium roughly 2–4 s. Doc-scene test images are likely smaller than a full 300-DPI A4, so the real per-page time is probably at the higher end. This needs a local measurement.
- **Recommended default:** RapidOCR 3.9.x with PP-OCRv6 small on ONNX Runtime or OpenVINO. It installs with pip on Windows, needs no Paddle framework, and returns boxes plus text. Use PP-OCRv6 medium through OpenVINO if accuracy on faint scans requires it (1.40 s vs 0.59 s on the Xeon).
- Turn on PaddleOCR's document orientation and unwarping modules, or deskew with OpenCV, for skewed scans. The PP-OCRv5 docs note these modules add time and can affect accuracy.
- Tesseract is the fastest simple baseline, but its error rate on receipts (CORD WER 0.98) makes it a poor fit for faint or varied delivery notes.
- Malay is a Latin-script language and should read correctly with a Latin or multilingual model. For DN numbers, dates and names, the character set matters more than the language. Mixed Chinese and Latin text favours PP-OCRv6's unified model.

### Gaps
- No independent (non-PaddlePaddle) CPU benchmark of PP-OCRv6 was found, and none on an 8-core desktop or server CPU or on Windows specifically.
- RapidOCR's latest version (3.9.2?) and release notes weren't confirmed from GitHub directly.
- Tesseract's latest version: the 2026 guide calls it "Tesseract 5.5". I didn't verify a 2026 release.
- No Windows.Media.Ocr benchmarks, and no reliable data on its Malay or Chinese mixed-text quality.
- No reliable 2026 CPU per-page numbers for Surya or current OnnxTR.
- I found no new non-Paddle classic OCR engine from 2026 that competes on CPU.
- The PP-OCRv6 docs don't list the 46 Latin languages, so Malay support is inferred, not confirmed.

---

## Q2. How long does OCR plus a 4B text LLM take end to end per page on 8 cores?

### Takeaway
Expect roughly **10–25 s per page** for PP-OCRv6 OCR plus a Qwen3/Qwen3.5-4B Q4 model run through llama.cpp on 8 x86 cores, with thinking off and a short JSON output. Decoding the roughly 50–100 output tokens dominates. At a few hundred pages a day that is about 1–2 hours of CPU time, well within budget. A 1.7–2B model roughly halves the LLM time. These are estimates built from measured component numbers, not a measured end-to-end figure.

### Cited Findings
- **[MEASURED]** CPU-only (AMD EPYC-Rome, 16 cores/32 threads at 2.0 GHz; 8 threads for generation, 16 for prefill; llama.cpp via igllama; Q4_K_XL; `--no-think`), generation speed:

  | Model | Gen tok/s |
  |---|---|
  | Qwen3.5-0.8B | 23.0 |
  | Qwen3.5-2B | 18.4 |
  | **Qwen3.5-4B** | **8.5** |
  | Qwen3.5-9B | 6.5 |
  | Qwen3.5-35B-A3B MoE | 5.6 |

  Prefill speed wasn't reported. — [igllama Qwen 3.5 small showcase](https://bkataru.github.io/igllama/showcase/qwen35-small/)
- **[MEASURED]** Qwen3-4B CPU-only (16-core x86 with AVX-512 and VNNI, `-t 16`, llama.cpp build 10516, llama-bench pp512 and tg128): **Q4_K_M gave pp512 2064.8 t/s and tg128 6.50 t/s**. Q8_0 gave 1355.9 / 5.04 and Q3_K_M gave 2142.5 / 6.56. The prefill figure is unusually high and the decode figure unusually low, which suggests a memory-bandwidth-limited machine. Treat both with care. — [b4ph/qwen3-4b-lowram-bench](https://huggingface.co/b4ph/qwen3-4b-lowram-bench)
- **[CLAIM / secondary]** Qwen3-8B Q4_K_M, CPU-only, 16 threads: about 210 t/s pp512 and about 26 t/s tg128. The CPU isn't identified in what I saw. — search snippet attributed to [markaicode llama.cpp benchmark](https://markaicode.com/benchmarks/llamacpp-tokens-per-second-benchmark/)
- **[MEASURED, other CPU]** On a 6-core/12-thread i7-8700, llama.cpp throughput peaked at 8 threads. Using all 12 logical threads was slower, so on 8 physical cores use `-t 8`. — [InventiveHQ CPU thread scaling](https://inventivehq.com/blog/cpu-thread-scaling-llm-inference)
- OCR stage: PP-OCRv6 small takes 0.59–0.61 s/image and medium 1.40 s/image (OpenVINO) on a Xeon 8350C. — [PP-OCRv6 docs](https://www.paddleocr.ai/v3.7.0/en/version3.x/algorithm/PP-OCRv6/PP-OCRv6.html)

### Inferences
- **Token budget per delivery note** (my estimate): about 300–800 OCR tokens, plus about 200–400 for instructions and schema, so roughly 600–1,200 prompt tokens. Output JSON for three fields is about 40–80 tokens with thinking disabled.
- **Prefill:** at 100–400 t/s on an 8-core AVX2 Xeon or Ryzen with a 4B Q4_K_M model, 1,000 tokens take about 2.5–10 s. AVX-512 or AMX parts are much faster. The prompt prefix can be cached with llama.cpp's `--cache-reuse` or slot reuse, so only the OCR text needs prefilling each time.
- **Decode:** at about 6–10 t/s (measured 6.5–8.5 for 4B on 8–16 threads), 60 tokens take about 6–10 s.
- **Total:** about 1–3 s OCR + 3–10 s prefill + 6–10 s decode ≈ **10–23 s/page** for 4B. A 1.7–2B model decodes at about 18 t/s, for an estimated **5–10 s/page**. An 8B model would take about 20–40 s/page.
- Use llama.cpp's GBNF / `--json-schema` (or Ollama's `format` with a JSON schema) so the output is always valid JSON. Keep keys short so the decode stage has fewer tokens to produce.
- Disable Qwen3/3.5 "thinking". Reasoning tokens would multiply decode time 5–20×.

### Gaps
- No measured end-to-end (OCR + LLM) per-page time on an 8-core Windows server was found. The figure above is composed from separate measurements.
- No reliable prefill (pp) number exists for an 8-core AVX2 desktop or server with a 4B Q4_K_M model. The figures found are 16-thread or bandwidth-skewed. Whether Windows builds are slower than Linux wasn't covered.
- No measured CPU tokens/s for Gemma 3/4 small, Phi-4-mini or SmolLM3 on 8 cores were found in this pass.

---

## Q3. How does OCR + text LLM compare with a small VLM on varied-layout forms? (Plus non-LLM KIE)

### Takeaway
Evidence is mixed and comes mostly from large or cloud models. For strong MLLMs, image-only input matches or beats OCR-text input on real business documents, delivery notes included. With small open text models (2B–8B), **OCR quality dominates**: PaddleOCR text keeps key recall near clean-text levels on receipts, but exact-value accuracy drops a lot. For three simple header fields (date, customer, DN number), OCR plus a small LLM is a reasonable and auditable CPU choice. Exact-value errors from OCR are the main risk, so add validation rules and a low-confidence route to human review. Layout-preserving input (line text plus coordinates) helps, based on LMDX, at the cost of more tokens.

### Cited Findings
- **[MEASURED, SAP, Mar 2026]** "OCR or Not?" tested about 1,000 real supply-chain (C1) and finance (C2) documents, with a **delivery note** used as the prompt example. Languages were English, Spanish, German, French and Italian; pages are dense (150–400 words) and multi-page. Mean F1 by input mode (image-only / OCR-only / image+OCR):

  | Model | Image-only | OCR-only | Image+OCR |
  |---|---|---|---|
  | GPT-4o mini | 66.6 | 68.3 | 71.1 |
  | GPT-4o | 70.1 | 72.8 | 73.0 |
  | Llama 4 Scout | 68.4 | 68.9 | 68.6 |
  | Pixtral Large | 63.1 | 73.3 | 70.4 |
  | Claude 3.5 Sonnet | 67.2 | 72.8 | 71.6 |
  | Gemini 1.5 Pro | 76.8 | 74.1 | 75.6 |
  | Gemini 2.5 Flash | 72.6 | 72.1 | 72.2 |

  The authors conclude that OCR "may not be necessary" for powerful MLLMs. OCR-only scores fall in a narrower 66–74% band. OCR-only errors are dominated by schema ambiguity, and image-only inputs produced fewer total errors. Some of the paper's reported means don't match the average of their C1/C2 values. — [arXiv 2603.02789 (HTML)](https://arxiv.org/html/2603.02789); [abstract](https://arxiv.org/abs/2603.02789)
- Also from that study: OCR-only scores rise from 57% to 74% as model size grows, while image-only and multimodal scores stay comparable across sizes. For Gemini 2.0 Flash-Lite, the smallest Gemini, image-only beat multimodal by nearly 3%. — [arXiv 2603.02789](https://arxiv.org/html/2603.02789)
- **[MEASURED, Sept 2026]** "From Pixels to Pairs" tested five open 2B–8B text LLMs (Gemma 2B/7B, Mistral-7B, Qwen2.5-7B, Llama-3-8B) zero-shot on OCR text from Tesseract, EasyOCR and PaddleOCR 3.x, scoring key recall (KR), exact match (EM) and value F1 (VF1).
  - **SROIE** (4 receipt header fields, the closest analog to the DN task), Qwen2.5-7B: Gold text KR 0.995 / EM 0.687 / VF1 0.893; **PaddleOCR 0.994 / 0.574 / 0.837**; EasyOCR and Tesseract lower (Tesseract and EasyOCR rows were truncated in my extraction).
  - **SROIE with PaddleOCR, 3-shot:** Qwen2.5-7B reached EM 0.672 and VF1 0.856. Llama-3-8B went from KR 0.68 zero-shot to 0.99 with one example.
  - **SROIE, Gemma 2B with PaddleOCR:** KR 0.862, EM 0.385, VF1 0.574. 2B-class models lose a lot on exact values.
  - **CORD** (dense receipts), Qwen2.5-7B: VF1 fell from 0.875 on gold text to 0.491 with PaddleOCR, 0.277 with EasyOCR and 0.149 with Tesseract.
  - **FUNSD** (forms, layout-dependent), Qwen2.5-7B: VF1 0.552 on gold text vs 0.353 with PaddleOCR.
  - PaddleOCR gave "substantially stronger downstream results" than EasyOCR and Tesseract. Model rankings flip between clean and OCR text, and few-shot gains are not monotonic. The paper deliberately did **not** test VLMs and did not supply boxes or layout coordinates.

  Source: [arXiv 2609.17538](https://arxiv.org/pdf/2609.17538) (code: github.com/zanvari/pixels-to-pairs)
- **[MEASURED, 2025, OLD]** A Fraunhofer benchmark of eight multimodal models on invoices found that native image processing generally beats structured text-parsing approaches. — [arXiv 2509.04469](https://arxiv.org/html/2509.04469v1)
- **[CLAIM, anecdote]** One practitioner reports 99.1% accuracy for OCR plus a small LLM versus 95.2% for Gemini 2.5 Flash on 93 invoices, and a VLM hallucinating a VAT ID. No methodology is given. — [LinkedIn post](https://cy.linkedin.com/in/christoph-schillmeier)
- **Layout trick (LMDX, Google, ACL Findings 2024, OLD):** each OCR line is passed with quantized box coordinates, and the model returns values with line or segment IDs. A decoding step grounds every value in the OCR text, which discards hallucinations. It reached state of the art on VRDU and CORD, including zero-shot on new document types. Its drawbacks: coordinate tokens take up a large share of the prompt, and localization is only line-level. — [LMDX, arXiv 2309.10952](https://arxiv.org/abs/2309.10952); [ACL Anthology](https://aclanthology.org/2024.findings-acl.899)
- The "Pixels to Pairs" paper attributes much of FUNSD's text-only difficulty to question–answer relationships that depend on 2-D layout. Flattening forms to plain text removes those cues. — [arXiv 2609.17538](https://arxiv.org/pdf/2609.17538)
- **Small VLM alternative datapoint [CLAIM, model card]:** a Qwen3-VL-2B fine-tuned on CORD-v2 self-reports field F1 0.886 and exact match 0.430. The card warns of worse results on other layouts and document types. — [HF: qwen3vl-2b-receipt-extraction](https://huggingface.co/ratlinghitman/qwen3vl-2b-receipt-extraction)
- **[MEASURED, June 2026, different task]** On a merchant-extraction task, Qwen 3.5 4B came within 0.35 points of the 8B baseline. That is text classification and extraction from transactions, not OCR. — [arXiv 2606.08051](https://arxiv.org/html/2606.08051)

**Non-LLM KIE (LayoutLMv3, Donut, rules)**
- LayoutLM-family and other layout-aware encoders (DocFormer, FormNet, StructuralLM) jointly model text and layout but need task-specific fine-tuning. The "Pixels to Pairs" paper frames instruction-tuned LLMs as the alternative that needs no fine-tuning. — [arXiv 2609.17538](https://arxiv.org/pdf/2609.17538)
- SROIE has only 973 receipts (626 train, 347 test) and CORD has 1,000 (800/100/100). Fine-tuned KIE models trained on such small, single-domain sets are known to transfer poorly to new layouts. The Qwen3-VL-2B model card makes the same caveat for its CORD fine-tune. — [KIEval arXiv 2503.05488 / search summary](https://arxiv.org/pdf/2503.05488); [HF model card](https://huggingface.co/ratlinghitman/qwen3vl-2b-receipt-extraction)

### Inferences
- **For this task, plain-text OCR plus a 4B LLM should get the field right (key recall) about 99% of the time.** Exact-value accuracy is bounded by OCR quality on faint scans: on SROIE, EM fell from 0.69 to 0.57 when going from gold to PaddleOCR text. Mitigations:
  1. Validate outputs with regex and parsers: DN-number pattern per customer or supplier, a date parser with DD/MM/YYYY preference for Malaysia, and fuzzy matching of customer names against the master customer list.
  2. **Require each returned value to appear verbatim (or fuzzily) in the OCR text**, the LMDX-style grounding. Otherwise mark it for review.
  3. Pass OCR lines in reading order with compact coordinates, e.g. `[y,x] text`, or a whitespace-preserving layout-text render, so that "label: value" pairs stay together.
  4. Use 1–3 few-shot examples, choosing them carefully since gains are not monotonic.
- Three header fields on a delivery note are much closer to SROIE (compact header fields: very high KR, EM limited by OCR) than to CORD line items or FUNSD forms. Results should land near the SROIE numbers if the OCR is good.
- **Compared with a small VLM:** the SAP evidence that image-only matches OCR applies to large cloud MLLMs. For CPU-sized VLMs (about 2–4B), I found no head-to-head on varied-layout business documents. A small VLM on CPU also has to encode a full-page image, which takes thousands of visual tokens at 300 DPI. On CPU that likely makes it slower than OCR plus a text LLM, but this is unmeasured here and covered by other research threads.
- **LayoutLMv3 / Donut** need labelled training data per field set and generalize weakly to unseen layouts. For many supplier layouts with three fields, an LLM plus rules is likely more robust with no training. LayoutLMv3's base weights are, to my knowledge, under a non-commercial CC BY-NC-SA license; verify this before any commercial use (not verified in this session).
- **A pure-rules approach** (anchor keywords such as "D/O No", "DN No", "Delivery Order", "Date", "Tarikh", "Customer", "Bill To", plus nearby-box search) is fast and deterministic for known layouts. It is a good first pass, with the LLM as fallback for unseen layouts.

### Gaps
- I found no published head-to-head of OCR plus a ≤8B text LLM versus a ≤4B VLM on CPU for varied-layout delivery notes or invoices, covering both accuracy and latency.
- No numbers were found for Qwen3/Qwen3.5 1.7B–4B on SROIE or CORD from OCR text. The closest data is Qwen2.5-7B and Gemma 2B/7B in "Pixels to Pairs".
- I found no controlled ablation quantifying how much bounding-box or layout-text input helps small open LLMs versus plain text. LMDX shows the method works with PaLM 2-S, not with small open models on CPU.
- No 2026 measured generalization numbers for LayoutLMv3 or Donut on unseen layouts were found in this pass. The license status of LayoutLMv3 is unverified here.
- No data on Malay- or Chinese-language delivery notes for any pipeline.
