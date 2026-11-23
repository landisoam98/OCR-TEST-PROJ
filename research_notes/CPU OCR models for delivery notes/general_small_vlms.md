# General-purpose small VLMs (1-9B) for CPU-only key-field extraction from scanned delivery notes (state as of Nov 2026)

Scope: extract DN date, customer name, DN number as JSON from scanned printed delivery notes (varied layouts, faint/skewed), on Windows, 8 x86 cores, 32 GB RAM, no GPU, tens to a few hundred pages/day, 30-90 s/page acceptable.

Research budget note: ~22 tool calls. Several items (exact Qwen3-VL small-model DocVQA table, InternVL3.5 benchmark numbers, MiniCPM-V 4.5 OCRBench, Phi-4-mm / Florence-2 / Moondream status) could not be pulled as text and are listed under Gaps. Measured CPU numbers for document VLMs are scarce; every one found is listed and labelled.

---

## Q1. Model-family fact sheet: latest versions, sizes, license, document benchmarks

### Takeaway
As of Nov 2026 the strongest small general VLM families for document key-field work are Qwen3.5 (0.8B/2B/4B/9B, Feb-Mar 2026, Apache-2.0, native multimodal), Qwen3-VL (2B/4B/8B, late 2025, Apache-2.0) and Gemma 4 (E2B/E4B, mid-2026, Apache-2.0). InternVL's latest is still 3.5 (Aug 2025); no InternVL 4 was found. A Qwen3-4B-based OCR specialist, Qianfan-OCR (Mar 2026, Apache-2.0, GGUF available), slightly beats Qwen3-VL-4B on KIE benchmarks.

### Cited Findings

**Qwen3.5 small (newest Qwen multimodal; 2026)**
- Qwen3.5 small series = 0.8B, 2B, 4B, 9B dense models, released ~2 March 2026, all natively multimodal (text/image/video in one unified architecture, not a bolted-on module) — [NYU Shanghai RITS](https://rits.shanghai.nyu.edu/ai/qwen-3-5-small-models-9b-parameters-that-beat-120b/); [Qwen3.5-2B card](https://huggingface.co/Qwen/Qwen3.5-2B)
- Qwen3.5-4B: Apache-2.0; hybrid Gated DeltaNet (linear attention) + Gated Attention in 3:1 pattern, 32 layers, hidden 2560; 262K native context; citation dated Feb 2026 — [Qwen3.5-4B card](https://huggingface.co/Qwen/Qwen3.5-4B)
- Qwen3.5-4B document benchmarks (vendor-reported): OmniDocBench1.5 86.2, OCRBench 85.0 (i.e. ~850/1000), CC-OCR 76.7, CharXiv(RQ) 70.8, MMLongBench-Doc 54.2, AI2D 89.6. DocVQA/InfoVQA not reported on the card — [Qwen3.5-4B card](https://huggingface.co/Qwen/Qwen3.5-4B)
- DeepLearning.AI notes the two smallest Qwen3.5 variants lack comparative metrics — [The Batch](https://www.deeplearning.ai/the-batch/alibabas-latest-flagship-models-are-open-weights-moe-performers-in-sizes-from-less-than-1b-parameters)
- Card names Transformers, vLLM, SGLang, KTransformers as runtimes; says quantized versions usable in llama.cpp/Ollama/LM Studio — [Qwen3.5-4B card](https://huggingface.co/Qwen/Qwen3.5-4B)

**Qwen3-VL (Oct-Nov 2025; flag: pre-2026)**
- Dense family 2B/4B/8B/32B (+MoE 30B-A3B, 235B-A22B); 2B and 4B use SigLIP2-Large (300M) vision encoder, larger use SigLIP2-SO-400M; merger compresses 2x2 encoder features into one visual token — [Qwen3-VL Technical Report, arXiv 2511.21631](https://arxiv.org/html/2511.21631)
- License Apache-2.0 — [Qwen3-VL-4B-Instruct card](https://huggingface.co/Qwen/Qwen3-VL-4B-Instruct)
- Qwen3-VL-4B: DocVQA 94.9, OCRBench 873, OCRBenchv2 en/zh 60.68/59.13, CC-OCR overall 76.5, ChartQA 83.3, TextVQA 81.8. Qwen3-VL-2B: DocVQA 92.7, ChartQA 78.3, TextVQA 79.9 (as reproduced by Baidu in a competitor's table) — [Qianfan-OCR GGUF card](https://huggingface.co/Mungert/Qianfan-OCR-GGUF)
- KIE (key information extraction) for Qwen3-VL-4B: overall 83.5; OCRBench-KIE 89.0; OCRBenchv2-KIE en 82.1; CC-OCR KIE 91.6; Nanonets KIE F1 83.3 — [Qianfan-OCR GGUF card](https://huggingface.co/Mungert/Qianfan-OCR-GGUF)
- Flagship Qwen3-VL-235B: DocVQA 96.5, OCRBench 875 (shows 4B is within ~1.5 pts DocVQA of the flagship) — [arXiv 2511.21631](https://arxiv.org/pdf/2511.21631)

**Qianfan-OCR (Baidu, Mar 2026) — OCR-specialised but prompt-driven, Qwen3-4B LLM + Qianfan-ViT**
- 4B, Apache-2.0, tech report arXiv 2603.13398 (Mar 2026) — [Qianfan-OCR GGUF card](https://huggingface.co/Mungert/Qianfan-OCR-GGUF)
- OCRBench 880, DocVQA 92.8, KIE overall 87.9 (OCRBench-KIE 95.0, CC-OCR KIE 92.8, Nanonets KIE F1 86.5) vs Qwen3-VL-4B 83.5 overall — vendor-reported — [same](https://huggingface.co/Mungert/Qianfan-OCR-GGUF)
- GGUF Q4_K_M 3.06 GB; runs via llama.cpp / Ollama (`ollama run hf.co/Mungert/Qianfan-OCR-GGUF:Q4_K_M`); card does not explain mmproj/thinking-mode handling for the GGUF — [same](https://huggingface.co/Mungert/Qianfan-OCR-GGUF)

**InternVL (user's prior model)**
- Latest found: InternVL3.5 (paper arXiv 2508.18265, 25 Aug 2025; flag: pre-2026). Sizes 1B (1.1B), 2B (2.3B), 4B (4.7B), 8B (8.5B), 14B, 38B, MoE 20B-A4B / 30B-A3B / 241B-A28B. Flash variants with a Visual Resolution Router (ViR) announced "as soon as possible" — [InternVL3.5-4B card](https://huggingface.co/OpenGVLab/InternVL3_5-4B)
- License Apache-2.0 (Qwen3-based LLM components also Apache-2.0) — [same](https://huggingface.co/OpenGVLab/InternVL3_5-4B)
- Vision: InternViT-300M; Dynamic High Resolution with 448 px tiles; each tile = 1024 ViT tokens, pixel-shuffled to 256 LLM tokens; example code uses max_num=12 tiles — [same](https://huggingface.co/OpenGVLab/InternVL3_5-4B)
- Two checkpoint formats: GitHub/custom format and "-HF" Transformers-native format, with conversion scripts — [same](https://huggingface.co/OpenGVLab/InternVL3_5-4B)
- No evidence of an InternVL 4 release in search results; GitHub README's newest report is InternVL3.5 — [OpenGVLab/InternVL GitHub](https://github.com/OpenGVLab/InternVL)

**Gemma 4 (2026)**
- llama.cpp lists Gemma 4 E2B, E4B, 26B-A4B, 31B — [llama.cpp multimodal.md](https://github.com/ggml-org/llama.cpp/blob/master/docs/multimodal.md)
- Gemma 4 E4B: 4.5B effective params (8B with embeddings), Apache-2.0, ~150M vision encoder, variable aspect ratio; tech report arXiv 2607.02770 (Jul 2026) — [gemma-4-E4B-it card](https://huggingface.co/google/gemma-4-E4B-it)
- Configurable image token budget: 70/140/280/560/1120; Google recommends 280-1120 for OCR/document parsing/small text; image before text prompt — [same](https://huggingface.co/google/gemma-4-E4B-it)
- Doc benchmarks: OmniDocBench1.5 edit distance 0.181 (lower better); DocVQA/OCRBench not reported; ParseBench-2 overall 42.32 (third-party) — [same](https://huggingface.co/google/gemma-4-E4B-it)

**MiniCPM-V 4.5 (OpenBMB; flag: 2025)**
- Card claims "leading performance on OCRBench, surpassing GPT-4o-latest and Gemini 2.5"; no numeric score found in text; claims int4/GGUF/AWQ quants in 16 sizes — [MiniCPM-V-4_5 card](https://huggingface.co/openbmb/MiniCPM-V-4_5)
- Ollama library entry `minicpm-v4.5`, Q4_K_M ~6.1 GB — [Ollama library](https://ollama.com/library/minicpm-v4.5)
- An OCRBench 876 figure appears for the sibling MiniCPM-o 4.5, not V 4.5 — [search result, MiniCPM-o 4.5](https://huggingface.co/yxxpp/minicpm-o-4_5) (unverified attribution)

**SmolVLM2 / Moondream / Phi-4-multimodal / Florence-2**
- SmolVLM / SmolVLM2 (incl. 256M/500M) and Moondream2 (20250414) are on llama.cpp's supported list; Phi-4-multimodal and Florence-2 are not listed — [llama.cpp multimodal.md](https://github.com/ggml-org/llama.cpp/blob/master/docs/multimodal.md)

### Inferences
- For three printed key fields, the 4B tier (Qwen3-VL-4B, Qwen3.5-4B, Qianfan-OCR, Gemma 4 E4B, InternVL3.5-4B) is likely sufficient; the KIE gap between Qwen3-VL-4B (83.5) and the 235B flagship (84.2) on Baidu's table is under 1 point, suggesting little gain from 8-9B for KIE.
- Qwen3.5-4B's OCRBench (850) is slightly below Qwen3-VL-4B's 873 on the vendor numbers; Qwen3.5's advantage is newer architecture/runtime momentum, not clearly better OCR. Both deserve a bake-off on real DNs.
- InternVL3.5 is ~15 months old and has been overtaken in tooling momentum by Qwen3-VL/Qwen3.5/Gemma 4.

### Gaps
- InternVL3.5 1B/2B/4B/8B DocVQA/OCRBench/InfoVQA numbers are only in images on the HF card; not extracted. (Report-writer: InternVL3.5 tech report arXiv 2508.18265 has them.)
- Qwen3-VL Table 3 (2B/4B/8B InfoVQA, OmniDocBench) not extracted from arXiv text.
- No FUNSD/CORD/SROIE numbers found for any of these general models in sources read.
- No confirmed newer "Nov 2026" small-VLM newcomer beyond Qwen3.5 / Gemma 4 / Qianfan-OCR was found; Phi-4-multimodal, Florence-2, Moondream 3 status not researched in depth.
- MiniCPM-V 4.5 numeric OCRBench/DocVQA not found.

---

## Q2. Is InternVL well supported in llama.cpp / Ollama / OpenVINO on Windows CPU today, versus Qwen-VL?

### Takeaway
No for InternVL3.5 in first-party terms: llama.cpp officially documents InternVL 2.5 and 3 only (via PR #13422); InternVL3.5 GGUFs exist only as third-party conversions without confirmed official mmproj support. Qwen3-VL (llama.cpp since 30 Oct 2025), Qwen3.5 (all sizes in the Ollama library with image input) and Gemma 4 (listed in llama.cpp docs) are the better-supported path. OpenVINO has official Qwen3-VL INT4 IR models and documents InternVL2 via the model server.

### Cited Findings
- llama.cpp multimodal docs list vision families: Gemma 3, SmolVLM/SmolVLM2, Pixtral, Qwen2-VL, Qwen2.5-VL, Mistral Small 3.1, InternVL 2.5 and InternVL3 (1B-14B), Llama 4 Scout, Moondream2, Gemma 4. Doc page itself does not list Qwen3-VL, Qwen3.5, MiniCPM-V, Phi-4, Florence — [llama.cpp multimodal.md](https://github.com/ggml-org/llama.cpp/blob/master/docs/multimodal.md)
- InternVL support was added by commit "mtmd : support InternVL 2.5 and 3 (#13422)" — [commit mirror](https://cdn04132025.gitlink.org.cn/replica/llama.cpp/commit/053367d149f778cdabc356ee3024494e0dd53223)
- An older version of the docs stated mmproj conversion is supported "only for the non-HF version of InternVL3" — [search summary of multimodal.md / Debian mirror](https://sources.debian.org/src/llama.cpp/7593%2Bdfsg-3/docs/multimodal.md); current page did not repeat that caveat per fetch — [llama.cpp multimodal.md](https://github.com/ggml-org/llama.cpp/blob/master/docs/multimodal.md) (conflicting/ambiguous)
- Third-party InternVL3.5 GGUFs exist (QuantStack 1B/2B "test" conversions, author said it "seemed to run"; bartowski 14B; Luigi 1B Q4_0) — [QuantStack 2B](https://huggingface.co/QuantStack/InternVL3_5-2B-gguf/blob/main/README.md); [bartowski 14B](https://huggingface.co/bartowski/OpenGVLab_InternVL3_5-14B-GGUF); [Luigi 1B](https://huggingface.co/Luigi/InternVL3_5-1B-Q4_0-GGUF)
- InternVL3.5 card names LMDeploy, vLLM, SGLang, Transformers (trust_remote_code); no GGUF or OpenVINO mention — [InternVL3.5-4B card](https://huggingface.co/OpenGVLab/InternVL3_5-4B)
- Qwen3-VL GGUF supported in llama.cpp since 30 Oct 2025; official Qwen GGUF repos (e.g. Qwen/Qwen3-VL-4B-Instruct-GGUF) plus bartowski, unsloth, lmstudio-community — [Unsloth Qwen3-VL guide](https://unsloth.ai/docs/models/tutorials/qwen3-how-to-run-and-fine-tune/qwen3-vl-how-to-run-and-fine-tune); [Qwen official GGUF](https://huggingface.co/Qwen/Qwen3-VL-4B-Instruct-GGUF); [LM Studio community GGUF](https://huggingface.co/lmstudio-community/Qwen3-VL-4B-Instruct-GGUF)
- bartowski flags Q4_0 / IQ4_NL as the quants with online repacking for ARM/AVX CPU inference — [bartowski Qwen3-VL-4B GGUF](https://huggingface.co/bartowski/Qwen_Qwen3-VL-4B-Instruct-GGUF)
- Qwen3.5 in Ollama library: 0.8b (1.2-1.3 GB), 2b (2.7-3.1 GB), 4b (3.3-4.0 GB), 9b (6.6-7.6 GB), all "Text, Image" input, 256K context — [Ollama qwen3.5](https://ollama.com/library/qwen3.5)
- Qwen3.5-9B Q4_K_M + mmproj-BF16 runs in llama-server (llama.cpp build 8994, May 2026) — [llama.cpp issue #22582](https://github.com/ggml-org/llama.cpp/issues/22582)
- Known accuracy issue: Qwen2.5-VL-3B OCR output in llama.cpp reported noticeably worse than Transformers reference — [llama.cpp issue search result #17801/#19345](https://github.com/ggml-org/llama.cpp/issues/17801) (exact issue number not verified)
- OpenVINO: official `OpenVINO/Qwen3-VL-8B-Instruct-int4-ov` IR on HF (no perf figures); OVMS docs show InternVL2-2B int4 VLM serving on CPU — [OpenVINO Qwen3-VL-8B int4](https://huggingface.co/OpenVINO/Qwen3-VL-8B-Instruct-int4-ov); [OVMS VLM demo 2026 docs](https://docs.openvino.ai/2026/model-server/ovms_demos_continuous_batching_vlm.html)
- OpenVINO GenAI has a VLMPipeline image-processing use case — [OpenVINO GenAI docs](https://openvinotoolkit.github.io/openvino.genai/docs/use-cases/image-processing/)

### Inferences
- If staying on InternVL on Windows CPU, the safest route is InternVL3 (not 3.5) GGUF in llama.cpp, or InternVL via OpenVINO/Optimum-Intel; InternVL3.5 in llama.cpp is "may work, unofficial".
- Ollama on Windows is the lowest-friction path for Qwen3.5 (image support out of the box) and MiniCPM-V 4.5; Ollama supports JSON-schema `format` structured outputs (from general knowledge, not verified in this session), and llama.cpp supports GBNF grammars / `--json-schema` (general knowledge, not verified here).
- LM Studio likely runs the lmstudio-community Qwen3-VL GGUFs (repo exists), but no LM Studio statement was read directly.

### Gaps
- Could not confirm whether current llama.cpp master's `convert_hf_to_gguf.py` handles InternVL3.5 mmproj; no dedicated issue/PR found.
- Gemma 3n and Phi-4-multimodal llama.cpp/Ollama status not verified.
- ONNX Runtime GenAI support for Qwen3-VL/Qwen3.5/InternVL not researched (no source found).
- JSON/grammar-constrained decoding support was not explicitly verified from docs in this session.

---

## Q3. Image-token cost of an A4 page (dominant CPU cost)

### Takeaway
Image tokens per page range from ~280-1120 (Gemma 4, fixed budget), ~1,000-2,500 (Qwen3-VL/Qwen3.5 at ~1000-1600 px long edge; dynamic pixels), up to 3,328 (InternVL with 12 tiles + thumbnail). One measured data point: a ~4K image into Qwen3.5-9B produced ~4,056 LLM image tokens in llama.cpp.

### Cited Findings
- InternVL3.5: 256 LLM tokens per 448x448 tile; example max_num=12 tiles — [InternVL3.5-4B card](https://huggingface.co/OpenGVLab/InternVL3_5-4B)
- Qwen3-VL: 2x2 encoder features merged per visual token — [arXiv 2511.21631](https://arxiv.org/html/2511.21631)
- Gemma 4: image budgets 70/140/280/560/1120 tokens; 280-1120 for documents — [gemma-4-E4B-it](https://huggingface.co/google/gemma-4-E4B-it)
- Measured: Qwen3.5-9B, ~4K-resolution 7.44 MB image -> image decoded in two batches of 2048 + 2008 = 4,056 tokens — [llama.cpp issue #22582](https://github.com/ggml-org/llama.cpp/issues/22582)
- Measured: Qwen3-VL-2B on a 640x320 px invoice -> 232 input tokens total (prompt + image) — [issoh.co.jp](https://www.issoh.co.jp/md/tech/10073)

### Inferences
- InternVL at default dynamic tiling: an A4 portrait page (aspect ~1:1.41) typically maps to a 2x3 or 3x4 tile grid + 1 thumbnail = 7-13 tiles = ~1,800-3,300 tokens; capping max_num at 4-6 gives ~1,280-1,800 tokens. (Derived from 256 tokens/tile.)
- Qwen3-VL/Qwen3.5 (assumes patch 16 x 2x2 merge = 32x32 px per token — patch size NOT confirmed in sources read; Qwen2.5-VL used 14 px patches = 28x28 px/token): A4 at 1240x1754 (150 dpi) ≈ 39x55 ≈ 2,100 tokens; at ~900x1270 ≈ 28x40 ≈ 1,100 tokens. Setting max_pixels (or llama.cpp image max-token options) to ~1 MP is the main CPU-time lever. The 232-token / 640x320 measurement (~0.2 MP) is consistent with ~32x32 px per token.
- For three header fields, a downscaled page (~1000 px long edge) or a crop of the top third is likely enough for printed text; faint scans may need more pixels — test.

### Gaps
- Exact Qwen3-VL / Qwen3.5 patch size and default min/max_pixels not confirmed from a primary text source in this session.
- llama.cpp flags for capping image tokens (e.g. `--image-max-tokens`) not confirmed in the docs page fetched.

---

## Q4. Realistic seconds-per-page on an 8-core x86 CPU; is OpenVINO a meaningful speedup?

### Takeaway
Measured CPU numbers for document VLMs are very sparse. The only hard data points: FP32 Transformers on CPU is unusable (Qwen3-VL-2B, 166 s for a tiny 640x320 invoice at 0.4 tok/s); OpenVINO gives large speedups over PyTorch (12x TTFT / 65x decode on SmolVLM2-256M; 8.49x end-to-end on Qwen2.5-VL-7B INT4 on a 48-core Xeon 6). For llama.cpp, the vision encoder on CPU is the bottleneck (82 s to encode a 4K image for Qwen3.5-9B with BF16 mmproj on a 16-core Ryzen 9 7950X in one disputed report). Inference: a 2-4B model at Q4/INT4 with a ~1 MP page on 8 cores plausibly lands in the 20-90 s/page window, but this must be benchmarked.

### Cited Findings (measured, with hardware)
- Qwen3-VL-2B-Instruct, FP32, transformers 4.57.1, Intel Core i9-9880H (8-core laptop, Intel Mac), 16 GB RAM, 640x320 synthetic invoice, 232 in / 66 out tokens: load 30.1 s, generation 166.1 s, 0.4 tok/s; extracted invoice no./date/total correctly. Measured 13 Oct 2026 — [issoh.co.jp](https://www.issoh.co.jp/md/tech/10073)
- SmolVLM2-256M, Intel Core Ultra 7 265K (20 cores, HT/turbo off), 64 GB DDR5: PyTorch TTFT 5.15 s / 0.72 tok/s / E2E 25.9 s; OpenVINO TTFT 0.42 s / 47.2 tok/s / E2E 0.74 s; OpenVINO 8-bit WOQ TTFT 0.25 s / 63.9 tok/s / E2E 0.48 s (image size unstated; Oct 2025) — [HF blog openvino-vlm](https://huggingface.co/blog/openvino-vlm)
- Qwen2.5-VL-7B-Instruct on Intel Xeon 6740P (48C): OpenVINO FP32 7.28x faster than HF FP32; OpenVINO INT4 a further 1.17x = 8.49x vs HF baseline; 128 output tokens; absolute latencies only in a plot (Oct 2025) — [Lenovo Press LP2305](https://lenovopress.lenovo.com/lp2305-accelerating-multimodal-llms-on-intel-xeon-6-processors-using-openvino)
- llama.cpp llama-server, Qwen3.5-9B Q4_K_M + mmproj BF16, AMD Ryzen 9 7950X (GPU present), ~4K image: image slice encode 82,047 ms; LLM image-token decode 945 ms + 821 ms for 4,056 tokens; total 83.8 s. Maintainer closed as "not planned", disputing the server-vs-CLI claim; root cause (BF16 encoder on CPU) unconfirmed (May 2026) — [llama.cpp issue #22582](https://github.com/ggml-org/llama.cpp/issues/22582)
- Older data point (flag: 2024): Qwen2-VL vision encoder on CPU in llama.cpp ~30 s per image, ~24 ms/patch; GPU expected ~3 s — [zenn.dev/syoyo](https://zenn.dev/syoyo/articles/ced4c9bfeefeb2)
- Qwen3-VL vision encoder SYCL fallback to CPU -> ~23 s image encoding (Intel GPU context) — [llama.cpp issue search result](https://github.com/ggml-org/llama.cpp/issues/16334) (exact issue number not verified)
- Secondary (unverified) claim: Qwen3-VL-4B Q4_K_M (~3.3 GB) recommended for CPU-only; "8B is too slow on CPU" — [Codersera](https://codersera.com/blog/qwen3-vl-4b-vs-qwen3-vl-8b-benchmarks-vram-guide/)
- Memory at 4-bit: Qwen3-VL 2B ~1.9 GB, 4B ~3.3 GB, 8B ~6.1 GB — [issoh.co.jp](https://www.issoh.co.jp/md/tech/10073)
- Reader comment on HF OpenVINO blog says Qwen3-VL 8B ran fastest of models tried on Core Ultra 7 265K with OpenVINO; OpenVINO sped up Mistral 7B but Llama 3.1 8B ran slower (anecdotal) — [HF blog openvino-vlm](https://huggingface.co/blog/openvino-vlm)

### Inferences
- Time per page = vision-encoder time (scales with pixels; often runs in BF16/F16 on CPU in llama.cpp, so quantizing the LLM to Q4 does not speed it up) + LLM prefill of image tokens + decode of ~30-60 JSON tokens. For a 4B LLM at Q4 on 8 modern cores, decode of ~50 tokens is likely 5-15 s; prefill of 1-2k image tokens tens of seconds; encoder 10-40 s at ~1 MP. Total roughly 30-90 s/page for 2-4B at ~1 MP, longer for 8-9B — an estimate, not measured.
- The 4,056 tokens decoded in ~1.8 s in #22582 was likely GPU-accelerated (7900 XTX present), so it does not represent CPU prefill.
- OpenVINO speedups are large mainly relative to PyTorch eager FP32; versus llama.cpp Q4 the gap is unknown. OpenVINO helps most on Intel CPUs (AVX-512/AMX on Xeon); on AMD or older Intel the gain is uncertain.
- The volume (a few hundred pages/day) fits within 24 h even at 90 s/page single-stream (~960 pages/day), so a 4B model is feasible; 2B leaves headroom.

### Gaps
- No measured llama.cpp CPU-only seconds-per-page for Qwen3-VL-4B, Qwen3.5-4B, Gemma 4 E4B, or InternVL3.5 on an 8-core x86 was found.
- No head-to-head OpenVINO vs llama.cpp GGUF CPU benchmark for any VLM found.
- No measured per-page accuracy on real (faint/skewed) delivery notes for any model found; the only extraction test was one synthetic 640x320 invoice.
- Which small VLM gives best "accuracy per CPU-second" cannot be answered from published data; it requires a local bake-off (suggested candidates: Qwen3.5-2B/4B, Qwen3-VL-2B/4B, Qianfan-OCR, Gemma 4 E2B/E4B at 560-1120 budget, InternVL3-2B as baseline).
