#!/usr/bin/env python3
"""Resumable translation of public catalog fields. Never runs during site builds.

Requires network access to Google Translate's public translation endpoint.
Outputs drafts, not human-reviewed translations. No API keys or secrets used.
"""
import argparse
import collections
import hashlib
import json
import os
from pathlib import Path
import re
import time
import urllib.parse
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
# Keep product names and common technical terminology in their original spelling.
TERMS = '''1Password|React|Next.js|Vue|Vue.js|Nuxt|Svelte|Astro|Angular|Tailwind CSS|Tailwind|Bootstrap|Figma|Sketch|Canva|Framer|Webflow|WordPress|WooCommerce|Shopify|Stripe|PayPal|Notion|Slack|Discord|Telegram|WhatsApp|Twitter|LinkedIn|YouTube|Instagram|TikTok|Facebook|Reddit|Pinterest|GitHub|GitLab|Bitbucket|Google|Microsoft|Anthropic|OpenAI|Claude|ChatGPT|Gemini|Grok|Codex|Copilot|Cursor|Windsurf|Cline|DeepSeek|Hugging Face|HuggingFace|Huggingface|LangChain|LangGraph|LlamaIndex|Ollama|vLLM|TensorFlow|PyTorch|Keras|scikit-learn|NumPy|Pandas|Polars|Matplotlib|Seaborn|Plotly|SciPy|Jupyter|Python|JavaScript|TypeScript|Node.js|Node|Deno|Bun|Ruby|Rails|Rust|Golang|Java|Kotlin|Swift|SwiftUI|Objective-C|C++|C#|PHP|Laravel|Django|Flask|FastAPI|FastMCP|Express|NestJS|Spring Boot|Spring|.NET|ASP.NET|Elixir|Phoenix|Haskell|Scala|Clojure|Erlang|Julia|Perl|Bash|PowerShell|SQL|PostgreSQL|Postgres|MySQL|SQLite|MongoDB|Redis|Elasticsearch|OpenSearch|ClickHouse|Snowflake|BigQuery|Databricks|Supabase|Firebase|Neon|Prisma|Drizzle|SQLAlchemy|Alembic|Docker|Kubernetes|Terraform|Ansible|Helm|Pulumi|Vagrant|Nix|NixOS|Linux|Ubuntu|Debian|Windows|macOS|iOS|Android|Flutter|Dart|Expo|React Native|Electron|Tauri|Unity|Unreal Engine|Godot|Blender|Three.js|three.js|WebGL|Vulkan|OpenGL|CUDA|NVIDIA|AMD|Intel|Qualcomm|Apple|Playwright|Puppeteer|Selenium|Cypress|Jest|Vitest|Mocha|pytest|unittest|JUnit|TestDino|Sentry|PostHog|Datadog|Grafana|Prometheus|OpenTelemetry|New Relic|Cloudflare|Vercel|Netlify|Heroku|DigitalOcean|Render|Railway|Amazon|Azure|Google Cloud|AWS|GCP|IBM|Oracle|Salesforce|HubSpot|Mailchimp|SendGrid|Resend|Twilio|Deepgram|ElevenLabs|Whisper|AssemblyAI|Firecrawl|Apify|Browserbase|Browserless|Brave|Chrome|Chromium|Firefox|Safari|Edge|Opera|Obsidian|Logseq|Zotero|Linear|Jira|Confluence|Trello|Asana|ClickUp|Airtable|Monday|Basecamp|Zoom|Teams|Fathom|Calendly|Cal.com|Zapier|Make|n8n|Temporal|Airflow|Dagster|Prefect|dbt|DuckDB|Apache|Spark|Kafka|RabbitMQ|Celery|BullMQ|MinIO|S3|Vite|Webpack|Rollup|Parcel|esbuild|Turbopack|Turborepo|Nx|npm|pnpm|yarn|pip|uv|poetry|conda|cargo|composer|bundler|Gradle|Maven|CMake|Makefile|Git|git|GitHub Actions|CI/CD|DevOps|DevSecOps|GraphQL|REST|gRPC|WebSocket|WebRTC|OAuth|OAuth2|OpenID Connect|SAML|JWT|SSH|SSL|TLS|HTTPS|HTTP|TCP|UDP|DNS|CDN|VPN|VPC|IAM|RBAC|ABAC|TOTP|FIDO2|WebAuthn|bcrypt|Argon2|SHA-256|AES|RSA|Markdown|MDX|HTML|CSS|JSON|JSONL|YAML|TOML|XML|CSV|TSV|Parquet|Avro|Protobuf|PDF|DOCX|XLSX|PPTX|SVG|PNG|JPEG|JPG|WebP|GIF|MP4|WAV|MP3|FFmpeg|ImageMagick|OpenCV|Tesseract|OCR|LaTeX|BibTeX|Mermaid|PlantUML|D3|Recharts|Chart.js|ECharts|shadcn/ui|Radix|Chakra|Material UI|MUI|Ant Design|Mantine|Zustand|Redux|MobX|TanStack|SWR|Axios|Zod|Yup|Valibot|Pydantic|tRPC|Hono|Elysia|SolidJS|Qwik|Remix|Gatsby|Docusaurus|Storybook|Lighthouse|axe-core|WCAG|ARIA|GDPR|HIPAA|SOC 2|ISO 27001|OWASP|NIST|CVE|CVSS|CWE|MITRE|ATT&CK|Pentest|Metasploit|Burp Suite|Wireshark|Nmap|Semgrep|CodeQL|SonarQube|Snyk|Trivy|Checkov|ESLint|Prettier|Biome|Ruff|Black|mypy|Pyright|TypeDoc|JSDoc|Sphinx|MkDocs|Doxygen|Docusign|DocuSign|Dropbox|Box|OneDrive|SharePoint|Power BI|Tableau|Looker|Metabase|Redash|Excel|PowerPoint|Word|Outlook|Gmail|Google Sheets|Google Docs|Google Slides|Google Drive|Google Calendar|Google Meet|Google Analytics|Google Ads|Bing|DuckDuckGo|Tavily|Exa|Perplexity|SerpAPI|Serper|Excalidraw|tldraw|inference.sh|Fastify|Superset|Streamlit|Gradio|Dash|NiceGUI|Reflex|Lovable|Replit|Bolt|v0|Framer Motion|GSAP|Lottie|Rive|Remotion|FLUX|Midjourney|DALL-E|Stable Diffusion|ComfyUI|Diffusers|Runway|Kling|Veo|Sora|Seedance|Ideogram|Recraft|fal.ai|Replicate|Modal|RunPod|Vast.ai|Together AI|Groq|Cerebras|Fireworks|OpenRouter|LiteLLM|Portkey|Helicone|Langfuse|LangSmith|Weights & Biases|MLflow|Comet|Neptune|ClearML|DVC|BentoML|Ray|KServe|Seldon|Triton|ONNX|TensorRT|OpenVINO|Core ML|GGUF|GGML|LoRA|QLoRA|PEFT|RLHF|DPO|PPO|SFT|RAG|MCP|LLM|VLM|TTS|STT|ASR|NLP|CV|RL|ML|AI|API|CLI|SDK|IDE|UI|UX|DOM|AST|JIT|AOT|ORM|CRUD|ACID|CAP|CQRS|DDD|TDD|BDD|SOLID|DRY|KISS|YAGNI|SOLIDWORKS|AutoCAD|Fusion 360|FreeCAD|KiCad|Altium|LTspice|SPICE|Verilog|VHDL|SystemVerilog|FPGA|ASIC|RTL|PCB|EDA|ROS|ROS2|Gazebo|MuJoCo|Isaac Sim|Isaac Lab|PhysX|Omniverse|Isaac|cuDNN|cuBLAS|cuFFT|cuSPARSE|NCCL|MPI|OpenMP|OpenACC|Slurm|PBS|LSF|HTCondor|Apptainer|Singularity|Enroot|Pyxis|NVLink|InfiniBand|RDMA|RoCE|DPDK|SPDK|DOCA|BlueField|ConnectX|Spectrum|Cumulus|SONiC|NetQ|NSight|Nsight|Numba|CuPy|JAX|Flax|Optax|Haiku|Equinox|Kornia|MONAI|BioNeMo|NeMo|Megatron|DeepSpeed|FSDP|DDP|DTensor|TorchTitan|TorchTune|Axolotl|Unsloth|LLaMA-Factory|Swift|MS-Swift|frontend|backend|fullstack|full-stack|refactor|refactoring|workflow|workflows|webhook|webhooks|endpoint|endpoints|middleware|runtime|serverless|microservice|microservices|monorepo|polyfill|callback|callbacks|closure|closures|Promise|async|await|asyncio|thread|threads|processId|projectId|taskId|Dockerfile|docker-compose|package.json|tsconfig.json|SKILL.md|README.md|LICENSE.txt'''.split('|')
TERMS += '''Apollo|Apollo Router|Bazel|Route 53|Route53|CloudFront|CoCounsel|Westlaw|Tres Finance|Bitwarden|1password|Paperless|Tailscale|WireGuard|Proxmox|TrueNAS|Synology|Home Assistant|Homebrew|Chocolatey|Scoop|Supabase|PocketBase|Convex|ConvexDB|PlanetScale|CockroachDB|TiDB|Milvus|Qdrant|Weaviate|Pinecone|Chroma|LanceDB|FAISS|Annoy|HNSW|Vespa|Typesense|Meilisearch|Solr|Lucene|Neo4j|ArangoDB|Dgraph|SurrealDB|DynamoDB|DocumentDB|Cosmos DB|CosmosDB|Firestore|Cloud SQL|Bigtable|Redshift|Athena|Glue|Lake Formation|Kinesis|Firehose|EventBridge|Step Functions|CloudWatch|CloudTrail|CloudFormation|CloudFront|Route 53|Route53|Bedrock|SageMaker|Textract|Comprehend|Rekognition|Transcribe|Polly|Lex|Connect|Amplify|AppSync|Cognito|App Runner|AppRunner|Lambda|Fargate|ECS|EKS|EC2|EBS|EFS|FSx|ELB|ALB|NLB|WAF|Shield|GuardDuty|Macie|Inspector|Security Hub|Detective|Control Tower|Cloud Run|Cloud Functions|Cloud Build|Cloud Deploy|Cloud Storage|Cloud Scheduler|Cloud Tasks|Pub/Sub|Vertex AI|Dialogflow|Firebase|App Engine|Cloud Armor|Cloud CDN|Cloud DNS|Cloud NAT|Cloud VPN|Cloud Interconnect|Cloud Spanner|Azure Functions|Azure DevOps|Azure Monitor|Azure Sentinel|Azure OpenAI|AKS|Entra ID|Active Directory|Key Vault|Service Bus|Event Hubs|Logic Apps|Power Automate|Power Apps|Copilot Studio|Semantic Kernel|AutoGen|AutoGPT|CrewAI|Agno|PydanticAI|DSPy|Haystack|Semantic Router|Instructor|Guidance|Outlines|LMQL|SGLang|LM Studio|Jan|GPT4All|llama.cpp|llamafile|KoboldCpp|Tabby|Continue|Aider|OpenHands|SWE-agent|Devin|Roo Code|Kilo Code|Goose|OpenCode|Pi|OpenClaw|ClawHub|Clawdbot|Moltbot|openclaw|Fabric|Obsidian|Beads|Dolt|Jujutsu|Sapling|jj|gh|op|jq|yq|curl|wget|sed|awk|grep|ripgrep|fzf|tmux|zsh|Fish|Nushell|Starship|Zellij|Alacritty|WezTerm|Ghostty|Kitty|iTerm2|Warp|Zed|Neovim|Vim|Emacs|Helix|VS Code|VSCode|VSCodium|IntelliJ|PyCharm|WebStorm|Rider|GoLand|CLion|DataGrip|Fleet|Eclipse|NetBeans|Xcode|Android Studio|RStudio|Posit|MATLAB|Octave|Mathematica|Wolfram|Maple|SageMath|Maxima|SymPy|Statsmodels|XGBoost|LightGBM|CatBoost|Optuna|Hyperopt|Ax|BoTorch|GPyTorch|Pyro|NumPyro|Stan|PyMC|ArviZ|Bambi|Emcee|Dynesty|UltraNest|Nautilus|BlackJAX|TensorFlow Probability|tfp|Turing|Dynamax|Distrax|Chex|Jraph|JAXopt|JAXline|JAX-MD|JAX-FEM|Diffrax|Diffrax|DeepChem|RDKit|Open Babel|ASE|GPAW|PySCF|Psi4|Qiskit|Cirq|PennyLane|QuTiP|Quimb|TeNPy|ITensor|NetKet|QuSpin|QuTiP|Astropy|SunPy|Skyfield|Poliastro|Orbitize|REBOUND|Gala|Galpy|Gammapy|Naima|Sherpa|XSPEC|ROOT|Geant4|Pythia|MadGraph|FastJet|HepMC|HepMC3|Uproot|Awkward|Vector|Hist|Coffea|Scikit-HEP|Scikit-Image|Scikit-Learn|Scikit-Bio|BioPython|Biopython|BioPandas|MDAnalysis|MDTraj|OpenMM|GROMACS|NAMD|Amber|CHARMM|LAMMPS|HOOMD-blue|ESPResSo|QE|Quantum ESPRESSO|VASP|ABINIT|CP2K|ORCA|Gaussian|GAMESS|NWChem|TeraChem|Molpro|MRCC|CFOUR|Q-Chem'''.split('|')
GLOSSARY = re.compile(r'(?<![\w])(?:' + '|'.join(re.escape(t) for t in sorted(set(TERMS), key=len, reverse=True)) + r')(?![\w])', re.I)
TECH = re.compile(r'https?://[^\s<>"\']+|`[^`\n]+(?:`|$)|"[^"\n]+(?:"|$)|\b[A-Z][A-Za-z0-9]*(?:[A-Z][a-z0-9]+)+\b|\b[A-Z][A-Z0-9_]{1,}\b|\b[a-zA-Z_][\w]*(?:[._/:-][\w-]+)+\b|\b\w+\(\)|…|\.{3}')
TOKEN = re.compile(r'\[\[T(\d+)\]\]')
MARKER = re.compile(r'\[\[(\d{5})\]\]')
PERSIAN = re.compile('[\u0600-\u06ff]')


def source_hash(row):
    what, use = row.get('what', ''), row.get('use_when', '')
    payload = what + '\n' + use
    if not what:
        payload += '\n' + row.get('description', '')
    return hashlib.sha256(payload.encode()).hexdigest()


def protect(text):
    spans = [(m.start(), m.end()) for pattern in (GLOSSARY, TECH) for m in pattern.finditer(text)]
    spans.sort(key=lambda x: (x[0], -(x[1]-x[0])))
    selected, end = [], 0
    for start, stop in spans:
        if start >= end:
            selected.append((start, stop)); end = stop
    output, tokens, end = [], [], 0
    for start, stop in selected:
        output.append(text[end:start]); output.append(f'[[T{len(tokens)}]]')
        tokens.append(text[start:stop]); end = stop
    output.append(text[end:])
    return ''.join(output), tokens


def restore(text, tokens, original):
    text = re.sub(r'\[\s*\[\s*T\s*(\d+)\s*\]\s*\]', r'[[T\1]]', text)
    found = [int(m.group(1)) for m in TOKEN.finditer(text)]
    if collections.Counter(found) != collections.Counter(range(len(tokens))):
        raise ValueError('Technical placeholder lost or duplicated')
    result = TOKEN.sub(lambda m: tokens[int(m.group(1))], text).strip()
    # Persian word order can move the truncation marker inside the sentence.
    # Preserve each marker rather than forcing English word order onto Persian.
    for marker in ('…', '...'):
        if original.count(marker) != result.count(marker):
            raise ValueError('Truncation marker lost or invented')
    if re.search(r'\[\[T\d+\]\]', result):
        raise ValueError('Unresolved placeholder')
    # Prose must actually have been translated. Pure tool/code lists may stay English.
    unprotected = TOKEN.sub('', protect(original)[0])
    if len(re.findall('[A-Za-z]{2,}', unprotected)) >= 3 and not PERSIAN.search(result):
        raise ValueError('English prose was not translated')
    return result


def request_translation(text):
    query = urllib.parse.urlencode({'client': 'gtx', 'sl': 'en', 'tl': 'fa', 'dt': 't', 'q': text})
    request = urllib.request.Request('https://translate.googleapis.com/translate_a/single?' + query,
                                     headers={'User-Agent': 'Mozilla/5.0', 'Accept': 'application/json'})
    with urllib.request.urlopen(request, timeout=60) as response:
        data = json.load(response)
    return ''.join(segment[0] or '' for segment in data[0])


def atomic_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix('.tmp')
    temp.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    temp.replace(path)


class FieldFailures(ValueError):
    def __init__(self, successes, failures):
        self.successes, self.failures = successes, failures


def valid_cached(text, translated):
    return all(token in translated for token in protect(text)[1])


def translate_batch(batch):
    prepared = [protect(text) for text in batch]
    payload = '\n'.join(f'[[{i:05d}]] {masked}' for i, (masked, _) in enumerate(prepared))
    result = request_translation(payload)
    matches = list(MARKER.finditer(result))
    if [int(m.group(1)) for m in matches] != list(range(len(batch))):
        raise ValueError('Translation segment boundaries changed')
    translated, failures = [], []
    for i, match in enumerate(matches):
        segment = result[match.end():matches[i+1].start() if i+1 < len(matches) else len(result)].strip()
        try:
            translated.append(restore(segment, prepared[i][1], batch[i]))
        except ValueError as error:
            translated.append(None)
            failures.append({'source':batch[i],'reason':str(error)})
    if failures:
        raise FieldFailures({text:value for text,value in zip(batch,translated) if value is not None}, failures)
    return translated


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', default='translation-output')
    parser.add_argument('--limit', type=int, default=0)
    parser.add_argument('--delay', type=float, default=2.0)
    parser.add_argument('--shard-index', type=int, default=0)
    parser.add_argument('--shard-count', type=int, default=1)
    parser.add_argument('--assemble-only', action='store_true')
    args = parser.parse_args()
    out = ROOT / args.output
    out.mkdir(parents=True, exist_ok=True)
    rows = [json.loads(line) for line in (ROOT / 'skills-catalog/skills-index-flat.jsonl').read_text().splitlines()]
    existing = json.loads((ROOT / 'data/fa.json').read_text())
    cache_path = out / 'field-cache.json'
    cache = json.loads(cache_path.read_text()) if cache_path.exists() else {}
    cache = {text:value for text,value in cache.items() if valid_cached(text,value)}
    # Existing authored translations seed the cache only where their source matches.
    by_key = {r['author']+'/'+r['name']: r for r in rows}
    for key, translation in existing.items():
        row = by_key.get(key)
        if row and translation['sourceHash'] == source_hash(row):
            for field in ('what', 'use_when'):
                if row.get(field) and translation.get(field) and (translation.get('method') != 'machine' or valid_cached(row[field],translation[field])): cache[row[field]] = translation[field]
    unique = dict.fromkeys(text for row in rows for text in [row.get('what',''),row.get('use_when',''),row.get('description','') if not row.get('what') else ''] if text)
    pending = [text for text in unique if text not in cache and int(hashlib.sha256(text.encode()).hexdigest(),16) % args.shard_count == args.shard_index]
    if args.assemble_only: pending = []
    if args.limit: pending = pending[:args.limit]
    print(f'{len(rows)} skills; {len(unique)} distinct fields; {len(pending)} fields to translate', flush=True)
    batches, batch, size = [], [], 0
    for text in pending:
        length = len(protect(text)[0]) + 12
        if batch and (size+length > 3400 or len(batch) >= 24):
            batches.append(batch); batch=[]; size=0
        batch.append(text); size += length
    if batch: batches.append(batch)
    failures = []
    consecutive_network_errors = 0
    last_request = 0.0
    def run_batch(items):
        nonlocal consecutive_network_errors, last_request
        for attempt in range(3):
            try:
                time.sleep(max(0, args.delay - (time.monotonic()-last_request)))
                last_request = time.monotonic()
                translated = translate_batch(items)
                consecutive_network_errors = 0
                cache.update(zip(items, translated))
                return
            except FieldFailures as error:
                cache.update(error.successes)
                failures.extend(error.failures)
                return
            except ValueError as error:
                if len(items)>1:
                    middle=len(items)//2
                    run_batch(items[:middle]); run_batch(items[middle:]); return
                failures.append({'source': items[0], 'reason': str(error)}); return
            except Exception as error:
                print(f'Network retry {attempt+1}: {type(error).__name__} {getattr(error, "code", "")}', flush=True)
                time.sleep(min(120, 15*(2**attempt)))
        consecutive_network_errors += 1
        failures.extend({'source':text, 'reason':'Network request failed'} for text in items)
        if consecutive_network_errors >= 4:
            raise RuntimeError('Translation service unavailable; saved progress can be resumed')
    try:
        for i, batch in enumerate(batches):
            run_batch(batch)
            atomic_json(cache_path, cache)
            print(f'Batch {i+1}/{len(batches)}: {len(cache)} cached; {len(failures)} failed', flush=True)
    finally:
        # Only complete pairs are published; failed fields never get fabricated fallbacks.
        translations = {key:value for key,value in existing.items() if value.get('method') != 'machine'}
        completed_hashes = {t['sourceHash'] for t in translations.values()}
        for row in rows:
            key = row['author']+'/'+row['name']; digest = source_hash(row)
            if digest in completed_hashes: continue
            sources = {'what':row.get('what',''), 'use_when':row.get('use_when','')}
            if not sources['what']: sources['description'] = row.get('description','')
            if not all(not text or text in cache for text in sources.values()): continue
            entry = {'title':'', **{field:cache[text] if text else '' for field,text in sources.items()},
                     'sourceHash':digest,'status':'draft','method':'machine','provider':'Google Translate'}
            translations[key]=entry;completed_hashes.add(digest)
        covered = sum(source_hash(row) in completed_hashes for row in rows)
        atomic_json(out/'fa.json', translations)
        atomic_json(out/'failures.json', failures)
        atomic_json(out/'report.json', {'total':len(rows),'covered':covered,'pending':len(rows)-covered,'records':len(translations),'cachedFields':len(cache),'failedFields':len(failures),'status':'draft'})
        print(f'Coverage: {covered}/{len(rows)}; output: {out}', flush=True)
    if failures: raise SystemExit(2)

if __name__ == '__main__': main()
