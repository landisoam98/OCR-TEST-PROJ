# Community & practitioner reports: local CPU-only OCR and key-field extraction (as of 23 Nov 2026)

**Method note (read first):** reddit.com could not be fetched directly ("unable to fetch from www.reddit.com"), and `site:reddit.com` / "r/LocalLLaMA" searches returned no Reddit threads. So **this file has no first-hand Reddit quotes**. The community evidence comes from GitHub issues and discussions (PaddleOCR, Qwen3-VL, paperless-gpt, llama.cpp), Hacker News, the Level1Techs forum, personal dev blogs, and a small public benchmark repo. Each item is tagged **[MEASURED]** (numbers from a stated run), **[ANECDOTE]** (one person's impression), **[VENDOR]** (a project's own claim) or **[GUIDE]** (a secondary blog or roundup).

---

## Q1. What do practitioner communities recommend in 2026 for CPU-only document OCR and extraction?

### Takeaway
Sources from late 2026 agree that on a machine with no GPU you should use a classic or light OCR engine (Tesseract, or PP-OCRv5/v6 through RapidOCR/ONNX) as the base layer. Rules or a small LLM pull the fields out of that text, and a VLM is optional for hard pages. The 0.9B–3B "OCR VLMs" (PaddleOCR-VL, GLM-OCR, dots.ocr, MinerU VLM) are described as GPU-first and slow on CPU. 7–8B general VLMs (Qwen-VL, InternVL) are the most-used choice for paperless-style OCR, but the users reporting them nearly all ran GPUs.

### Cited Findings
- **[GUIDE, 19 Oct 2026]** One roundup says that without a graphics card, Tesseract plus OCRmyPDF "still holds up". It names MinerU's basic tier (ONNX, about 0.8 GB of models, 2 GB RAM) as a CPU option. It says PaddleOCR-VL has a CPU path on x64 but is slow on CPU, and that PaddleOCR's own guide advises against direct local inference in production. — [Pillitteri, "best local OCR for PC and server 2026"](https://pasqualepillitteri.it/en/news/25568/best-local-ocr-pc-server-2026)
- **[GUIDE, 22 Oct 2026]** Another roundup picks Tesseract 5.5 and PP-OCRv6 (tiny/small/medium, ONNX builds) for CPU-only use. It advises keeping a classic engine on every page even when a VLM is used, because the classic engine fails visibly instead of inventing text. Its pick for forms/JSON-schema filling is GLM-OCR (runs in Ollama, vLLM and llama.cpp). — [vdf.ai, Best Local OCR Model 2026](https://vdf.ai/blog/best-local-ocr-models/)
- **[GUIDE, 10 Apr 2026]** llama.cpp supports OCR models: LightOnOCR, Qianfan-OCR, PaddleOCR-VL ("may have degraded performance"), GLM-OCR, DeepSeek-OCR, dots.ocr and HunyuanOCR. General VLMs that can do OCR include Qwen3-VL-2B and Gemma-4-E2B/E4B. The post says some run on CPU "with decent performance" but gives no numbers. — [Hugging Face/ggml blog: Using OCR models with llama.cpp](https://huggingface.co/blog/ggml-org/using-ocr-models-with-llama-cpp)
- **[ANECDOTE, HN, roughly Feb 2026]** In the GLM-OCR thread, commenters named GLM-OCR, LightOnOCR-2-1B, PaddleOCR-VL-1.5, dots.ocr (works best in layout mode, but slow) and Chandra (restrictive licence) as favourites. One user ran Chrome's built-in OCR library on CPU at "1 to 2 seconds per page on a single core", with 20 instances in parallel. — [HN: GLM-OCR](https://news.ycombinator.com/item?id=46924075)
- **[ANECDOTE, HN]** In the Ocrbase thread, one commenter said dots.ocr needs "a considerable amount" of compute. Another pointed to a pipeline of small specialised models that runs on CPU only (RapidOCR). — [HN: Show HN Ocrbase](https://news.ycombinator.com/item?id=46691454) (via search summary; thread not fetched in full)
- **[ANECDOTE, 2025]** paperless-gpt users: qwen2.5vl:7b is the accepted "best vision model" answer (RTX 4070 Super). granite3.2-vision was "unsatisfactory". Mistral-small3.1 was more accurate, but "only on CPU, which was too slow for multiple documents". No comments from 2026. — [paperless-gpt Discussion #214](https://github.com/icereed/paperless-gpt/discussions/214)
- **[ANECDOTE, Apr–May 2026]** In a Level1Techs paperless-ngx thread, people tried minicpm-v, llama3.2-vision:11b, qwen2.5vl:7b and qwen3-vl:8b. Others suggested Qwen3.6-27B and DeepSeek-OCR. The thread reached no verdict. The advice was to raise the context length, test single pages, and build a labelled benchmark from known-good pages. — [Level1Techs: Need help with AI OCR for paperless-ngx](https://forum.level1techs.com/t/need-help-with-ai-ocr-for-paperless-ngx/249465)
- **[GUIDE/VENDOR, 2026]** For CPU, MinerU only runs with its `pipeline` backend. Unofficial docs say it is "5–20x slower than GPU", at about 0.5–2 pages/s, and the RAM minimums quoted disagree (2 GB / 4 GB / 16 GB). — [DeepWiki MinerU hardware](https://deepwiki.com/chukonu-team/MinerU_2.5/12.2-hardware-compatibility); [Pillitteri 2026](https://pasqualepillitteri.it/en/news/25568/best-local-ocr-pc-server-2026)

### Inferences
- For a server with 8 cores, 32 GB RAM and no GPU, what the community does points to a hybrid design. Run RapidOCR/PP-OCR (ONNX) or Tesseract on every page, extract the three fields from the text with rules or a small LLM, and send only low-confidence pages to a VLM. That VLM could be a small one (Qwen3-VL-2B/4B, GLM-OCR) through llama.cpp, or InternVL, which the client already knows.
- InternVL rarely appears in practitioner recommendations for this job. Qwen-VL (2.5/3) dominates the anecdotes.

### Gaps
- No Reddit (r/LocalLLaMA, r/selfhosted, r/paperless) threads could be retrieved, so the "Reddit consensus" for late 2026 is not directly evidenced here.
- No practitioner report specifically about **delivery notes** was found. The closest workloads are invoices and receipts.

---

## Q2. What CPU seconds-per-page numbers have people actually posted?

### Takeaway
Measured CPU numbers are scarce. Classic and tiny OCR runs at about 2–9 s/page on weak or limited CPUs. A 7B LLM step takes about 30 s on a laptop-class CPU. 7B OCR VLMs are reported at 30–120 s/page on CPU, and PaddleOCR-VL with cold starts has been reported at about 530 s/page. CPU thread scaling in PaddleOCR is a known problem.

### Cited Findings
- **[MEASURED, Nov 2026, dev.to]** Celeron N4100 (4 cores, no AVX), 7.6 GB RAM, Linux, 4 threads. Indra OCR (Datalab, about 1M-parameter recogniser) took 2.29 s on an invoice (56 lines) and 3.86–4.73 s on a dense 138-line scan. In another run on a busy machine, PP-OCRv6-small via RapidOCR took 26.9 s on the invoice and 31.6–87.6 s on scans, so Indra was 4–10x faster (the author says to trust the ratios, not the absolute times). Native PaddleOCR crashed with "Illegal instruction" on this no-AVX CPU. Accuracy: Indra got 16/16 invoice fields and RapidOCR 15/16. On one dense scan RapidOCR got 12/12 and Indra 10/12. — [dev.to: tiny OCR model without a GPU](https://dev.to/ganesh-kumar/how-a-tiny-ocr-model-finds-reads-and-orders-text-on-a-page-without-a-gpu-kk9)
- **[VENDOR]** Datalab claims a 212 ms median per page for Indra on 4 cores, and about 44 pages/s on 32 cores. — same dev.to post; [Pillitteri 2026](https://pasqualepillitteri.it/en/news/25568/best-local-ocr-pc-server-2026)
- **[MEASURED, 20 Aug 2026, GitHub]** PP-OCRv6 small on an AWS c6i.xlarge (4 vCPU, 8 GiB), PaddleOCR 3.7.0, MKL-DNN on, invoice workload: OCR inference took **6.98–8.87 s per request**. Going from 2 to 4 vCPU gained only about 0.2 s, and CPU use stayed around 1–1.5 vCPU of the 3.5 allocated. A commenter says PaddleOCR-VL with `cpu_threads=11` also stays on about 1 core (unverified). Another suggests OpenVINO (16 Nov 2026, no results). There are no maintainer replies. — [PaddleOCR issue #18320](https://github.com/PaddlePaddle/PaddleOCR/issues/18320)
- **[MEASURED, older PaddleOCR]** About 30 s/page in Docker versus about 6 s in conda. MKL-DNN helped. — [Paddle issue #54482](https://github.com/PaddlePaddle/Paddle/issues/54482) (via search summary)
- **[MEASURED-ish, Medium, date unclear]** PaddleOCR-VL on one invoice: about 531 s/page on CPU and about 114 s/page on GPU. The author says model loading dominates both numbers, warm batches are much faster, and recommends the vLLM backend for production. — [Medium: "I just wanted to parse one invoice"](https://adityamangal98.medium.com/i-just-wanted-to-parse-one-invoice-paddleocr-vl-had-other-plans-3acc18055906) (403 on fetch; figures from search snippet)
- **[MEASURED, GPU reference, 2026]** PaddleOCR-VL locally on an RTX 4060 Ti took about 20 s/page on light pages and about 32 s/page on dense pages (38 s for a single cold page). Even with a GPU, local PaddleOCR-VL can be slow without vLLM. — [PaddleOCR issue #18164](https://github.com/PaddlePaddle/PaddleOCR/issues/18164) (via search summary)
- **[MEASURED, Aug–Nov 2026]** Ryzen 7 5825U mini PC: qwen2.5:7b (text LLM step) took **about 30 s per inference on CPU**, against about 8 s on the iGPU. The iGPU path crashed 451 times in one day, so the author moved to CPU-only for stability. — [woitzik.dev: When your LLM hallucinated your OCR](https://woitzik.dev/blog/llm-hallucinated-ocr-paperless/)
- **[GUIDE/ANECDOTE]** HF Spaces running olmOCR (7B VLM) on CPU list **30–90 s/page**, and a quantized variant warns of **60–120 s/page**. — [HF Space coderprabhat/olmOCR](https://huggingface.co/spaces/coderprabhat/olmOCR/commit/55a0a6c6faa878063e63268f4f960b53c44adff2)
- **[MEASURED, Mac not CPU]** GLM-OCR through llama.cpp on Metal took about 7 s/page on a 16 GB M1 Pro. A llama.cpp-fork PR confirmed GLM-OCR read an invoice correctly ("Invoice #12345") on CPU with 4 threads, with no timing given. GLM-OCR support was merged upstream in llama.cpp on 18 Feb 2026. — [pocketweb.tools GLM-OCR](https://pocketweb.tools/mac/models/glm-ocr); [ik_llama.cpp PR #2814](https://github.com/ikawrakow/ik_llama.cpp/pull/2814); [llama.cpp issue #19335](https://github.com/ggml-org/llama.cpp/issues/19335)
- **[GUIDE]** Generic estimates for Ollama on CPU are 3–6 tok/s, and 1–5 tok/s for Qwen3-VL. A text-only qwen3:4b measured 16.5 tok/s on an Intel Core Ultra 5. No measured qwen3-vl CPU per-image figure was found. — search summary of [agenticwire Ollama Qwen 2026](https://www.agenticwire.news/article/ollama-qwen), [apidog Qwen3-VL guide](https://apidog.com/blog/how-to-run-qwen-3-vl-locally-with-ollama/)
- **[GUIDE]** One practitioner sets a planning target of about 1 minute per invoice on CPU and about 10 s on GPU. This is a target, not a measurement. — [dev.to mrzaizai2k: Key Information Extraction](https://dev.to/mrzaizai2k/real-life-key-information-extraction-p1-dont-over-complicate-things-39o9) (via search summary)

### Inferences
- With 8 modern cores, a reasonable expectation is single-digit seconds per page for RapidOCR/PP-OCR, and tens of seconds per page for a 2–4B VLM at Q4/Q8 through llama.cpp. Image prompt processing dominates the VLM time. These are extrapolations, not measurements.
- With PaddleOCR on CPU, extra cores barely help each request, so throughput comes from running several worker processes in parallel. This matches the HN "20 instances" approach.

### Gaps
- No posted measurement found for Qwen3-VL, InternVL3.5, PaddleOCR-VL (warm), GLM-OCR, DeepSeek-OCR or dots.ocr on an x86 server CPU with seconds per page and hardware stated.
- **OpenVINO:** OpenVINO 2025.2 added Qwen2.5-VL-3B on CPU, 2025.4 added CPU optimisations for Qwen2/2.5-VL, and GenAI supports MiniCPM-V 2.6/4.5/4.6 ([OpenVINO 2025.4 release notes](https://www.intel.com/content/www/us/en/developer/articles/release-notes/openvino/2025-4.html); [OpenVINO GenAI supported models](https://openvinotoolkit.github.io/openvino.genai/docs/supported-models/)). An HF/Intel post shows a small VLM with 0.48 s end-to-end latency at 8-bit on an Intel CPU, but for a tiny model and image, not documents ([HF: VLM on Intel CPUs](https://huggingface.co/blog/openvino-vlm)). **No community-posted OpenVINO document-OCR seconds/page was found.**

---

## Q3. Known accuracy and hallucination problems, and mitigations

### Takeaway
The failure modes reported most often are: (1) the VLM invents plausible text, including invoice numbers, amounts and company names; (2) infinite repetition loops, especially in Qwen-VL during OCR; (3) missing or omitted fields; (4) day/month swaps in parsing. Communities mitigate these with a classic OCR cross-check, one page per request, temperature 0, sanity rules on dates, and human review of flagged fields.

### Cited Findings
- **[ANECDOTE, Aug 2026, updated Nov 2026]** A paperless-gpt setup had a text-only model mistakenly configured as the vision model. For weeks it produced **completely fabricated** German OCR for scanned receipts: "Rechnung Nr. 2024-0847", "Betrag: €1.247,83", "Firma: Mustermann GmbH". The author noticed only from an unfamiliar company name in a title. Lessons: check that the model has vision capability, test with known inputs, and remember that hosted APIs return HTTP 400 for image input to a non-vision model while local runtimes fail silently. — [woitzik.dev](https://woitzik.dev/blog/llm-hallucinated-ocr-paperless/)
- **[ANECDOTE, Oct 2025 – Jan 2026; still open]** Qwen3-VL (2B/4B/8B/30B-A3B/32B) and Qwen2.5-VL go into **infinite repetition** on OCR in transformers, llama.cpp, MLX, Ollama and LM Studio. Triggers include tables with near-identical rows, greedy decoding and 4-bit quants. A higher repetition penalty breaks text that really does repeat, and bf16/fp32 did not fix it. The only reported fix was switching to GLM-4.6V-Flash: 0 loops in 500 tests at Q5_K_M in llama.cpp. There is no Qwen maintainer reply. — [QwenLM/Qwen3-VL issue #1611](https://github.com/QwenLM/Qwen3-VL/issues/1611)
- **[ANECDOTE]** Qwen3-VL-2B "goes on infinite loop when asked to perform OCR". A repeat penalty of 1.05 helped one user. Qwen's own docs suggest a presence penalty of up to 2.0. — [llama.cpp issue #16207](https://github.com/ggml-org/llama.cpp/issues/16207?timeline_page=1); [Qwen llama.cpp docs](https://qwen.readthedocs.io/en/latest/run_locally/llama.cpp.html)
- **[ANECDOTE, Apr 2026]** paperless-ngx users get "gibberish repeating the same paragraph or symbols over and over". qwen3-vl:8b sometimes answered that it did not understand the task. The suspected cause is Ollama's default 4096 context truncating image tokens. — [Level1Techs thread](https://forum.level1techs.com/t/need-help-with-ai-ocr-for-paperless-ngx/249465)
- **[ANECDOTE, 2026]** In paperless-gpt, thinking-capable vision models return **empty OCR** because `OLLAMA_THINK` is ignored. A single global context of 131,072 tokens was forced onto the OCR model and spilled it from VRAM to CPU. — [paperless-gpt issue #1201](https://github.com/icereed/paperless-gpt/issues/1201); [issue #1192](https://github.com/icereed/paperless-gpt/issues/1192) (via search summary)
- **[ANECDOTE, HN]** Some newer OCR models hallucinate "incredibly aggressively" and can loop. LLMs tend to "correct" text, and longer multi-page inputs make that worse, so one page per request is better. About 95% accuracy on messy inputs means several errors per page, so critical fields need human review. — [HN: GLM-OCR](https://news.ycombinator.com/item?id=46924075)
- **[MEASURED, Oct 2026, small benchmark on an RTX 4060]** On 100 clean invoices with unseen layouts (FATURA, synthetic), field F1 was: RapidOCR + qwen2.5:7b **0.922**, qwen2.5vl:7b zero-shot 0.943, qwen3-vl:8b two-shot **0.964** (58% of documents fully correct), Gemini Flash 0.987 (79% fully correct). On 100 **photographed receipts** (CORD v2), OCR + LLM collapsed to **0.336** against 0.680 for qwen3-vl:8b. qwen3.5:4b wrapped 55% of values in braces until given examples. Review flags caught only a third to half of wrong invoices, so the author concludes "a person still checks". — [Tajaddin/vlm-document-extraction](https://github.com/Tajaddin/vlm-document-extraction)
- **[MEASURED, academic, 2026]** On a receipt benchmark, a fine-tuned Qwen3-VL-4B failed mostly by **omitting** fields, not inventing them. Gemini tended to make up a plausible invoice number when the ID was absent, and invoice_number was among the hardest fields. — [arXiv 2605.22413](https://arxiv.org/pdf/2605.22413) (via search summary)
- **[GUIDE, 2026]** Generative OCR "can produce a clean sentence that is not on the page". Treat disagreement between the classic engine and the VLM as a trigger for human review. Tesseract fails visibly and returns word positions. — [vdf.ai](https://vdf.ai/blog/best-local-ocr-models/); IBM warns that small Granite-Docling models "can produce invented content" — [Pillitteri 2026](https://pasqualepillitteri.it/en/news/25568/best-local-ocr-pc-server-2026)
- **[ANECDOTE, GitHub, 2026]** Day/month problems in a real Odoo OCR-AI module: slash dates were hard-parsed as dd/mm, so US 09/04/2026 became 2026-04-09 silently. Any day value above 12 aborted the whole pre-fill. "Datum" matched delivery, due and order dates. An unvalidated LLM date (e.g. 30 Feb) raised an error that discarded the whole OCR result. — [odoo-ocr-ai issue #16](https://github.com/molnkontakt/odoo-ocr-ai/issues/16); [issue #30](https://github.com/molnkontakt/odoo-ocr-ai/issues/30)
- **[GUIDE]** Date mitigations: state the expected format (DD/MM/YYYY) in the prompt, return the raw string as well as an ISO value, reject future or too-old dates, and retry with day and month swapped when a parse is implausible. — [pdfvector: validate extracted invoice data](https://www.pdfvector.com/blog/validate-extracted-data-from-invoices); [theneuralbase receipt OCR](https://theneuralbase.com/ocr-for-ai/learn/intermediate/receipt-ocr-merchant-amount-date/)
- **[GUIDE, Apr 2026]** llama.cpp OCR advice: use low temperature (`--temperature 0.1` or `--top-k 1`) against hallucination. Q8_0 is the default quant, F16 gives better quality, and some models expect the image *after* the prompt. — [HF/ggml blog](https://huggingface.co/blog/ggml-org/using-ocr-models-with-llama-cpp)

### Inferences
- For delivery notes, the DN number is the riskiest field. A VLM may invent or "complete" an ID that is faint, so the value should be found verbatim in the classic OCR text (fuzzy match) before it is accepted.
- Ambiguous dates (both parts ≤ 12) need a fixed locale rule per customer or supplier, plus a plausibility window (for example, within ±N days of the scan date).
- Repetition loops call for a hard `max_tokens` cap, and asking for short JSON output (3 fields) instead of a full-page transcription greatly reduces exposure to loops.

### Gaps
- No community report quantifies **day/month swap rates** for VLMs specifically.
- No head-to-head practitioner thread comparing **InternVL vs Qwen-VL** on documents was found. Only vendor and paper benchmarks exist, e.g. OCRBench 881 for InternVL3-8B vs 883 for Qwen2.5-VL-7B, essentially tied ([Qianfan-VL paper](https://arxiv.org/pdf/2509.18189), via search summary), and InternVL3's own blog claims it beats Qwen2.5 on text tasks ([InternVL3 blog](https://internvl.github.io/blog/2025-04-11-InternVL-3.0/)).

---

## Q4. Windows install pain (supporting notes)

### Takeaway
On Windows, PaddleOCR-VL's fast path (vLLM) and MinerU's GPU/Docker paths are poorly supported. ONNX-based tools (RapidOCR, Tesseract, llama.cpp/Ollama) are the low-friction route.

### Cited Findings
- **[GUIDE, Oct 2026]** PaddleOCR-VL guide: "on Windows vLLM does not run natively", and Docker is recommended. MinerU Docker for non-NVIDIA devices is "pending an update". — [Pillitteri 2026](https://pasqualepillitteri.it/en/news/25568/best-local-ocr-pc-server-2026)
- **[ANECDOTE, 2026]** MinerU on Windows: long PDF names hit the 260-character MAX_PATH limit (FileNotFoundError) because of nested temp paths. It needs Python 3.10–3.12, since 3.13 is unsupported through the ray dependency. The default PyPI torch wheel is CPU-only, which suits a no-GPU server. — [gaoyuindeu/mineru-windows-setup-guide](https://github.com/gaoyuindeu/mineru-windows-setup-guide); [DeepWiki MinerU install](https://deepwiki.com/opendatalab/MinerU/3-installation-and-setup)
- **[MEASURED, Nov 2026]** Native PaddleOCR crashes with "Illegal instruction" on CPUs without AVX, while RapidOCR (ONNX) worked on the same machine. — [dev.to tiny OCR](https://dev.to/ganesh-kumar/how-a-tiny-ocr-model-finds-reads-and-orders-text-on-a-page-without-a-gpu-kk9)
- **[GUIDE, 2026]** RapidOCR (current release reported as 3.9.2, July 2026) installs with `pip install rapidocr onnxruntime` and supports Windows, Linux and macOS. — [invoicedataextraction.com Python OCR comparison](https://invoicedataextraction.com/blog/python-ocr-library-comparison-invoices) (via search summary; verify the version on PyPI)
- **[ANECDOTE]** Ollama GGUFs exported with a `glmocr` architecture string do not load in stock llama.cpp. — [llama.cpp issue #19335](https://github.com/ggml-org/llama.cpp/issues/19335)

### Inferences
- On a Windows server, the easiest stack to support is a single Python environment with RapidOCR (onnxruntime) and a llama.cpp/Ollama binary for the optional VLM. Avoid anything that depends on vLLM or WSL/Docker GPU paths.

### Gaps
- No first-hand Windows Server (as opposed to Windows desktop) deployment reports were found for any of the candidate VLMs.
