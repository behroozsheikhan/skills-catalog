import test from "node:test";
import fs from "node:fs";
import assert from "node:assert/strict";
import { skills } from "../src/lib/catalog.mjs";
import { translationSourceHash } from "../src/lib/translations.mjs";
test("direct rewrites have distinct provenance without claiming human review", () => {
  const editorial = skills.filter((s) => s.fa?.method === "editorial");
  assert.equal(editorial.length, skills.length);
  const report = JSON.parse(
    fs.readFileSync("data/translation-report.json", "utf8"),
  );
  assert.equal(report.editorialSkills, editorial.length);
  assert.equal(
    report.editorialSourcePairs,
    new Set(editorial.map((s) => s.fa.sourceHash)).size,
  );
  assert.equal(report.editorialPending, skills.length - editorial.length);
  for (const s of editorial) {
    assert.equal(s.fa.editorialVersion, 1);
    assert.equal(s.fa.status, "draft");
    assert.equal(s.fa.sourceHash, translationSourceHash(s));
    assert.equal(
      s.fa.provider,
      "Arena assistant — direct translation from source",
    );
  }
  assert.equal(report.editorialPending, 0);
  assert.equal(report.machineTranslationRecords, 0);
  assert.equal(report.humanReviewed, false);
});
test("developer terminology and missing source fields survive rewriting", () => {
  const find = (k) => skills.find((s) => s.key === k).fa;
  assert.ok(find("microsoft/ensure-pipelines-host").what.includes("tenant"));
  assert.ok(!find("microsoft/ensure-pipelines-host").what.includes("مستاجر"));
  assert.ok(find("microsoft/pytest").what.includes("parametrize"));
  assert.equal(find("anthropic/frontend-design").use_when, "");
  assert.ok(
    find("vercel/web-design-guidelines").use_when.includes('"review my UI"'),
  );
});

test("continued rewrites preserve named APIs, arguments and original restrictions", () => {
  const find = (key) => skills.find((s) => s.key === key).fa;
  assert.equal(find("vercel/ask-next").method, "editorial");
  assert.ok(find("vercel/ask-next").what.includes("$ARGUMENTS"));
  assert.ok(
    find("cloudflare/building-mcp-server-on-cloudflare").use_when.includes(
      '"OAuth to MCP"',
    ),
  );
  assert.ok(
    find("microsoft/add-workiq").what.includes("shared_a365copilotchatmcp"),
  );
  assert.ok(find("nvidia/clinical-delegation").what.includes("agentId"));
  assert.ok(find("nvidia/clinical-delegation").what.includes("نه ACP"));
  assert.ok(
    find("nvidia/clinical-delegation").what.includes("web_fetch مجاز نیست"),
  );
  assert.equal(find("github/ai-ready").use_when, "");
});

test("editorial drafts retain empty fields, truncation markers and inline identifiers", () => {
  for (const s of skills.filter((s) => s.fa?.method === "editorial")) {
    const fields = ["what", "use_when", ...(!s.what ? ["description"] : [])];
    for (const field of fields) {
      const source = s[field] || "";
      const target = s.fa[field] || "";
      assert.equal(
        Boolean(target),
        Boolean(source),
        `${s.key}/${field}: empty field`,
      );
      for (const marker of ["…", "..."]) {
        assert.equal(
          target.split(marker).length,
          source.split(marker).length,
          `${s.key}/${field}: truncation ${marker}`,
        );
      }
      for (const match of source.matchAll(/`([^`]+)`/g)) {
        assert.ok(target.includes(match[1]), `${s.key}/${field}: ${match[1]}`);
      }
    }
  }
});

test("large continuation retains authentication and orchestration restrictions", () => {
  const find = (key) => skills.find((s) => s.key === key).fa;
  const auth = find("microsoft/auth");
  assert.equal(auth.method, "editorial");
  for (const term of ["AuthResolver", "os.getenv()", "ممنوع"])
    assert.ok(auth.what.includes(term));
  const setup = find("launchdarkly/apply").what;
  assert.ok(setup.includes("با رضایت کاربر"));
  const triage = find("microsoft/apm-triage-panel").what;
  assert.ok(triage.includes("هیچ subagentی فراخوانی نمی‌شود"));
  const projects = find("microsoft/azure-ai-projects-py").use_when;
  assert.ok(projects.includes("سطح پایین"));
  assert.ok(projects.includes("azure-ai-agents-python"));
  const legacy = find("microsoft/azure-communication-callingserver-java");
  assert.ok(legacy.what.includes("منسوخ"));
  assert.ok(legacy.what.includes("azure-communication-callautomation"));
  assert.ok(legacy.use_when.includes("کد قدیمی"));
});

test("Azure rewrites preserve management-plane exclusions, deprecations and consent", () => {
  const find = (key) => {
    const fa = skills.find((s) => s.key === `microsoft/${key}`).fa;
    assert.equal(fa.method, "editorial");
    return fa;
  };
  for (const [key, sdk] of [
    ["azure-resource-manager-cosmosdb-dotnet", "Microsoft.Azure.Cosmos"],
    ["azure-resource-manager-sql-dotnet", "Microsoft.Data.SqlClient"],
    ["azure-resource-manager-redis-dotnet", "StackExchange.Redis"],
  ]) {
    const text = find(key).use_when;
    for (const term of ["management plane", "data plane", "نیست", sdk])
      assert.ok(text.includes(term), `${key}: ${term}`);
  }
  const playwright = find("azure-resource-manager-playwright-dotnet").use_when;
  assert.ok(playwright.includes("برای اجرای تست Playwright نیست"));
  assert.ok(
    playwright.includes("Azure.Developer.MicrosoftPlaywrightTesting.NUnit"),
  );
  const atlas = find("azure-mgmt-mongodbatlas-dotnet").use_when;
  assert.ok(atlas.includes("نه مستقیماً کلاسترها یا دیتابیس‌های Atlas"));
  for (const [key, replacements] of [
    [
      "azure-monitor-query-java",
      ["azure-monitor-query-logs", "azure-monitor-query-metrics"],
    ],
    [
      "azure-monitor-opentelemetry-exporter-java",
      ["azure-monitor-opentelemetry-autoconfigure"],
    ],
  ]) {
    const text = find(key).use_when;
    assert.ok(text.includes("منسوخ"));
    for (const sdk of replacements) assert.ok(text.includes(sdk));
  }
  const speech = find("azure-speech-to-text-rest-py").use_when;
  for (const term of [
    "60",
    "streaming",
    "استفاده نشود",
    "Speech SDK",
    "Batch Transcription API",
  ])
    assert.ok(speech.includes(term));
  assert.ok(find("azure-reliability").what.includes("با تأیید کاربر"));
});

test("Chinese-source rewrites preserve commands, consent and routing boundaries", () => {
  const find = (name) => {
    const skill = skills.find((s) => s.key === `modelstudioai/${name}`);
    assert.equal(skill.fa.method, "editorial");
    assert.match(skill.what, /[\u3400-\u9fff]/u);
    assert.doesNotMatch(skill.fa.what, /[\u3400-\u9fff]/u);
    return skill.fa.what;
  };
  const managed = find("bailian-managed-agent");
  for (const term of [
    "agents.yaml",
    "bl managed-agent",
    "apply / destroy",
    "--yes",
    "plan",
    "تأیید",
    "bailian-app-call",
  ])
    assert.ok(managed.includes(term), term);
  const fine = find("bailian-finetune");
  for (const term of [
    "SFT-LoRA",
    "DPO-LoRA",
    "CPT",
    "--dry-run",
    "API key",
    "file-id",
    "bailian-model-recommend",
  ])
    assert.ok(fine.includes(term), term);
  const gen = find("bailian-gen");
  for (const term of [
    "bl omni",
    "--download",
    "polling",
    "موارد خارج از دامنه",
    "bailian-finetune",
  ])
    assert.ok(gen.includes(term), term);
  assert.ok(find("bailian-protocol").includes("خودکار دریافت نمی‌کنند"));
});

test("continuation preserves production approval, literal-only sources and design exclusions", () => {
  const find = (key) => skills.find((s) => s.key === key).fa;
  const audit = find("github/bigquery-pipeline-audit");
  assert.equal(audit.method, "editorial");
  for (const term of [
    "maximum_bytes_billed",
    "تأیید صریح",
    "dry-run",
    "MERGE",
    "append",
  ])
    assert.ok(audit.use_when.includes(term), term);
  assert.equal(
    find("bitwarden/bitwarden-workflow-linter-rules").what,
    "job_environment_prefix",
  );
  const landing = find("wshobson/brand-landingpage").use_when;
  assert.ok(landing.includes("از این اسکیل استفاده نشود"));
  assert.ok(landing.includes("mockup"));
});

test("500-source batch preserves prerequisites, offline limits and literal commands", () => {
  const find = (key) => {
    const fa = skills.find((s) => s.key === key).fa;
    assert.equal(fa.method, "editorial");
    return fa;
  };
  assert.equal(
    find("prisma/prisma-cli-migrate-reset").what,
    "prisma migrate reset",
  );
  assert.equal(
    find("prisma/prisma-cli-migrate-deploy").what,
    "prisma migrate deploy",
  );
  assert.ok(
    find("deepgram/core-mcp").what.includes(
      "پیش از هر عملیات ترمینال wsh الزامی",
    ),
  );
  assert.ok(
    find("nvidia/compileiq-booster-pack").what.includes(
      "پیش از اجرای جست‌وجوی کامل",
    ),
  );
  assert.ok(find("deepgram/openai-whisper").what.includes("بدون API key"));
  assert.ok(
    find("deepgram/sherpa-onnx-tts").what.includes("آفلاین و بدون cloud"),
  );
  assert.ok(find("anthropic/form-generation").what.includes("منسوخ"));
  assert.ok(find("anthropic/form-generation").what.includes("`/draft`"));
  assert.equal(find("tldraw/dotcom-release-crew").what, "ارسال به");
  assert.ok(
    find("github/mkdocs-translations").what.includes(
      "متن کافی در صفحه وجود ندارد",
    ),
  );
  const chineseCommands = find("dontbesilent2025/dbs-chatroom").what;
  assert.ok(chineseCommands.includes("/dbs-chatroom"));
  assert.ok(chineseCommands.includes("/定向聊天室"));
  assert.ok(chineseCommands.includes("«定向聊天室»"));
  const translated = find("tencent/weread-skills").what;
  assert.doesNotMatch(translated, /[\u3400-\u9fff]/u);
  for (const term of ["جست‌وجوی کتاب", "یادداشت", "آمار مطالعه"])
    assert.ok(translated.includes(term));
});

test("second 500-source batch preserves approval gates and narrow execution scope", () => {
  const find = (key) => {
    const fa = skills.find((s) => s.key === key).fa;
    assert.equal(fa.method, "editorial");
    return fa;
  };
  assert.ok(
    find("langfuse/incident-alert-tickets").what.includes("پس از تأیید انسان"),
  );
  assert.ok(
    find("nvidia/text-summarizer").what.includes(
      "بدون هیچ دسترسی شبکه یا فراخوانی API بیرونی",
    ),
  );
  assert.ok(find("nvidia/cuopt-lp-milp-api-c").what.includes("فقط C API"));
  assert.ok(find("nvidia/cuopt-lp-milp-api-c").use_when.includes("C/C++"));
  assert.ok(
    find("deepgram/core").what.includes(
      "ابزارهای MCP با نام wsh_* در دسترس نیستند",
    ),
  );
  assert.ok(
    find("openai/figma-generate-diagram").what.includes(
      "پیش از هر فراخوانی ابزار `generate_diagram`",
    ),
  );
  assert.ok(
    find("anthropic/fhir-developer-skill").what.includes(
      'cardinality آن‌ها با "1"',
    ),
  );
  assert.ok(find("redis/pull-requests").what.includes('"AI-Made"'));
  assert.ok(
    find("caffeinelabs/extension-http-outcalls").what.includes(
      "نه در frontend",
    ),
  );
  const local = find("nvidia/compileiq-validate-result").what;
  for (const term of ["پس از تکمیل Search", "پیش از ادعای", "ACF"])
    assert.ok(local.includes(term));
  const fallback = find("langchain-ai/competitor-analysis");
  assert.equal(fallback.what, "");
  assert.equal(fallback.description, "هنگام درخواست تحلیل رقبا:");
  const chinese = find("larksuite/lark-workflow-standup-report").what;
  assert.ok(chinese.includes("calendar +agenda"));
  assert.ok(chinese.includes("task +get-my-tasks"));
  assert.doesNotMatch(chinese, /[\u3400-\u9fff]/u);
});

test("third 500-source batch preserves review gates, API scope and incomplete source", () => {
  const find = (key) => {
    const fa = skills.find((s) => s.key === key).fa;
    assert.equal(fa.method, "editorial");
    return fa;
  };
  assert.ok(
    find("langchain-ai/deep-agents-orchestration").what.includes(
      "الزام به تأیید انسان",
    ),
  );
  const readonly = find("posthog/querying-local-postgres").what;
  for (const term of ["فقط‌خواندنی", "SELECT", "EXPLAIN ANALYZE روی SELECT"])
    assert.ok(readonly.includes(term));
  const cuopt = find("nvidia/cuopt-numerical-optimization-api-c");
  assert.ok(cuopt.what.includes("QP در مرحلهٔ beta"));
  assert.ok(cuopt.what.includes("فقط C API"));
  assert.ok(cuopt.use_when.includes("C/C++"));
  assert.ok(
    find("nvidia/cuopt-server-common").what.includes(
      "بدون کد استقرار یا کلاینت",
    ),
  );
  assert.ok(
    find("openai/figma-use").what.includes(
      "پیش از هر فراخوانی ابزار `use_figma`",
    ),
  );
  assert.ok(
    find("openshift/code-formatting").what.includes("'When...it should...'"),
  );
  assert.ok(
    find("mastra-ai/e2e-tests-studio").what.includes("نه فقط رندرشدن عناصر UI"),
  );
  assert.ok(
    find("shopify/shopify-dev").what.includes("فقط وقتی هیچ اسکیل مخصوص API"),
  );
  assert.ok(find("dagster-io/erk-planning").what.includes("حذف شده است"));
  assert.ok(
    find("langchain-ai/deep-agents-memory-&amp;-filesystem").what.includes(
      "دیگر در دسترس نباشد",
    ),
  );
  assert.equal(find("microsoft/pr-description-skill").what, "");
  assert.equal(
    find("microsoft/pr-description-skill").description,
    "این اسکیل را برای هر یک از مقصودهای زیر فعال کنید:",
  );
});

test("fourth 500-source batch preserves payment gates, command flags and fallback", () => {
  const find = (key) => {
    const fa = skills.find((s) => s.key === key).fa;
    assert.equal(fa.method, "editorial");
    return fa;
  };
  const payment = find("nvidia/release-packet").what;
  assert.ok(payment.includes("وجه را آزاد نمی‌کند"));
  assert.ok(payment.includes("بازبین انسانی"));
  assert.ok(
    find("nvidia/rail-boundary-test").what.includes(
      "هرگز آزادسازی پرداخت نیست",
    ),
  );
  const cli = find("planetscale/planetscale-pscale-cli-automation").what;
  for (const term of ["--format json", "pscale sql", "--force"])
    assert.ok(cli.includes(term));
  assert.ok(
    find(
      "planetscale/planetscale-traffic-control-recommendations",
    ).what.includes("بدون اعمال"),
  );
  assert.ok(
    find("nvidia/jetson-customize-uphy").what.includes("استفاده نکنید"),
  );
  assert.ok(find("nvidia/jetson-customize-uphy").use_when.includes("pinmux"));
  assert.ok(
    find("nvidia/nv-segment-ctmr").what.includes("نه برای تفسیر بالینی"),
  );
  assert.ok(find("rivet-dev/driver-test-runner").what.endsWith("در…"));
  const fallback = find("signoz/signoz-clickhouse-query");
  assert.equal(fallback.what, "");
  assert.equal(fallback.description, fallback.use_when);
  assert.ok(fallback.description.endsWith(":"));
});

test("1000-source batch retains consent, read-only limits, clinical exclusions and truncation", () => {
  const find = (key) => {
    const fa = skills.find((s) => s.key === key).fa;
    assert.equal(fa.method, "editorial");
    return fa;
  };
  const autonomous = find(
    "planetscale/planetscale-autonomous-execution-mode",
  ).what;
  assert.ok(autonomous.includes("تغییر تأییدشده"));
  assert.ok(autonomous.includes("صریحاً پذیرش ریسک"));
  assert.ok(
    find("planetscale/planetscale-mcp-agent-operating-model").what.includes(
      "بدون تغییر خودمختار production",
    ),
  );
  assert.ok(
    find("planetscale/planetscale-readonly-inventory").what.includes(
      "فقط‌خواندنی",
    ),
  );
  assert.ok(
    find("mongodb/mongodb-natural-language-querying").what.includes(
      "فقط‌خواندنی",
    ),
  );
  assert.ok(
    find("nvidia/dicom-metadata-extract").what.includes(
      "نه برای ناشناس‌سازی یا کاربرد بالینی",
    ),
  );
  assert.ok(
    find("nvidia/dicom-series-to-volume").what.includes(
      "نه برای DICOM چندفریمی یا کاربرد بالینی",
    ),
  );
  const cli = find("nvidia/cuopt-numerical-optimization-api-cli");
  assert.ok(cli.what.includes("beta"));
  assert.ok(cli.what.includes("فقط CLI"));
  const finalReview = find("openai/implementation-final-review");
  assert.ok(finalReview.what.includes("فقط استفاده شود"));
  assert.ok(finalReview.use_when.includes("صریحاً"));
  assert.ok(finalReview.use_when.endsWith("…"));
  assert.ok(find("microsoft/conductor").what.includes("فقط با درخواست صریح"));
  const triton = find("nvidia/kernel-triton-writing");
  assert.ok(triton.what.includes("هرگز استفاده نشود"));
  for (const term of ["CUDA C++", "TileIR", "ncu", "nsys"])
    assert.ok(triton.use_when.includes(term));
  const asr = find("nvidia/digital-health-clinical-asr-finetune").use_when;
  for (const term of ["۰٫۳", "Parakeet TDT v2", "N+1", "نه برای…"])
    assert.ok(asr.includes(term));
  const outline = find("anthropic/outline-builder").what;
  assert.ok(outline.includes("به‌جای شما نمی‌نویسد"));
  const calendar = find("larksuite/lark-calendar").what;
  for (const term of ["lark-vc", "lark-task", "نه این اسکیل"])
    assert.ok(calendar.includes(term));
  const note = find("larksuite/lark-note").what;
  for (const term of [
    "note_id",
    "vc-node-id",
    "unified",
    "Docx",
    "در حیطهٔ آن نیست",
  ])
    assert.ok(note.includes(term));
  for (const key of [
    "microsoft/rust",
    "mattpocock/resolving-merge-conflicts",
    "langfuse/frontend-browser-review",
    "openai/security-scan",
  ]) {
    const fa = find(key);
    assert.equal(fa.what, "");
    assert.equal(fa.description, fa.use_when);
  }
});

test("second 1000-source batch preserves explicit approvals and narrow execution scope", () => {
  const find = (key) => {
    const fa = skills.find((s) => s.key === key).fa;
    assert.equal(fa.method, "editorial");
    return fa;
  };
  assert.ok(find("sentry/linear-project-update").what.includes("تأیید صریح"));
  assert.ok(
    find("wix/rp-execute-import").use_when.includes(
      "کاربر برنامهٔ اجرا را تأیید کرده",
    ),
  );
  const deployment = find("get-convex/convex-deploy-guard").what;
  for (const term of ["پیش از هر دستور", "رضایت صریح تازه", "فقط‌خواندنی"])
    assert.ok(deployment.includes(term));
  assert.ok(
    find("bitwarden/exploring-bitwarden-data").what.includes("فقط‌خواندنی"),
  );
  const merge = find("deepgram/merge-pr");
  assert.ok(merge.what.includes("/preparepr"));
  for (const term of ["به main push نکنید", "کد را تغییر ندهید", "MERGED"])
    assert.ok(merge.use_when.includes(term));
  assert.ok(merge.use_when.endsWith("…"));
  assert.ok(
    find("langfuse/langfuse-previews").what.includes("فقط دادهٔ مصنوعی"),
  );
  for (const key of [
    "nvidia/earth2studio-deterministic-forecast",
    "nvidia/earth2studio-discover",
    "nvidia/earth2studio-data-fetch",
  ]) {
    assert.ok(find(key).what.includes("استفاده نکنید"));
    assert.ok(find(key).use_when.includes("نصب"));
  }
  const convert = find("nvidia/tao-convert-dataset-format");
  assert.ok(convert.what.includes("`tao-daft convert`"));
  assert.ok(convert.what.includes("استفاده نکنید"));
  assert.ok(convert.use_when.includes("غیر DAFT"));
  assert.ok(
    find("nvidia/jetson-validate-image").what.includes(
      "نه برای build یا flash",
    ),
  );
  const handoff = find("pulumi/pulumi-neo-handoff");
  assert.ok(handoff.what.includes("انتقال یک‌طرفه"));
  assert.ok(handoff.use_when.includes("صریحاً"));
  assert.ok(find("microsoft/html2pptx").what.includes("نه PNG داخل اسلاید"));
  const whiteboard = find("larksuite/lark-whiteboard").what;
  for (const term of ["lark-doc", "lark-sheets / lark-base", "نه این اسکیل"])
    assert.ok(whiteboard.includes(term));
});

test("third 1000-source batch preserves safety limits, routing and source fallbacks", () => {
  const fa = (key) => {
    const value = skills.find((s) => s.key === key)?.fa;
    assert.equal(value?.method, "editorial", key);
    return value;
  };
  assert.match(fa("redis/git-safety").what, /هرگز مستقیم.*main.*force-push/);
  assert.match(
    fa("nvidia/doca-flow-grpc-server").what,
    /هیچ گزینهٔ TLS \/ mTLS \/ token-auth ندارد/,
  );
  assert.match(
    fa("nvidia/tao-validate-dataset-format").use_when,
    /قالب غیر DAFT/,
  );
  assert.match(
    fa("wix/wix-cli-backend-api").use_when,
    /صریحاً backend endpoint/,
  );
  assert.match(
    fa("nvidia/nim-operator-uninstall").what,
    /تأیید صریح اقدام مخرب/,
  );
  assert.match(fa("nvidia/doca-bf4-deployment").what, /برگشت‌ناپذیر/);
  assert.match(fa("sentry/fix-issue").what, /اگر اصلاح ساده نیست، انصراف/);
  assert.match(
    fa("planetscale/planetscale-schema-recommendations-agent-loop").what,
    /بدون اعمال تغییر production/,
  );
  assert.match(
    fa("nvidia/tao-setup-nvidia-gpu-host").what,
    /نصب پس از تأیید کاربر/,
  );
  assert.match(
    fa("wind-information-co-ltd/wind-find-finance-skill").what,
    /پس از تأیید کاربر AI خودش نصب/,
  );
  assert.match(
    fa("larksuite/lark-minutes").what,
    /بر رونویسی محلی ffmpeg\/whisper اولویت/,
  );
  assert.match(fa("larksuite/lark-sheets").what, /docs \+search در lark-doc/);
  assert.match(
    fa("wind-information-co-ltd/wind-mcp-skill").what,
    /برای سهام اروپا\/ژاپن.*رمزارز.*نیست/,
  );
  for (const key of [
    "google-gemini/github-issue-creator",
    "contentstack/javascript-node",
    "flutter/test-driven-development",
    "mongodb/mongo-tools-js-to-go",
    "contentstack/testing",
  ]) {
    assert.equal(fa(key).what, "");
    assert.equal(fa(key).description, fa(key).use_when);
  }
});

test("continued direct rewrites retain consent, platform limits and expanded fallback descriptions", () => {
  const fa = (key) => {
    const value = skills.find((s) => s.key === key)?.fa;
    assert.equal(value?.method, "editorial", key);
    return value;
  };
  assert.match(fa("okx/okx-agentic-wallet").what, /فقط Solana و بدون EIP-7702/);
  assert.match(fa("get-convex/convex-verify").what, /رد کاربر نادرست/);
  assert.match(
    fa("neondatabase/claimable-postgres").what,
    /۷۲ ساعت.*مگر.*Neon/,
  );
  assert.match(
    fa("get-convex/convex-cost").what,
    /confirm-cost برای اقدام پولی/,
  );
  assert.match(
    fa("get-convex/convex-self-heal").what,
    /هرگز auto-merge نمی‌کند/,
  );
  assert.match(fa("get-convex/convex-explain-app").what, /فقط‌خواندنی/);
  assert.match(fa("apify/feature-spec").what, /هیچ فایلی ویرایش نشود/);
  assert.match(
    fa("langfuse/react-component-cleaner").use_when,
    /فقط با دستور کاربر/,
  );
  assert.match(
    fa("posthog/exploring-autocapture-events").what,
    /با opt-in کاربر/,
  );
  assert.match(
    fa("momentic-ai/momentic-mobile-test").what,
    /فقط.*اطمینان بالا/,
  );
  assert.match(fa("warpdotdev/implement-specs").what, /پس از تأیید/);
  assert.match(
    fa("heygen-com/captions-overlay").what,
    /نه نوار رزروشدهٔ پایین/,
  );
  assert.match(fa("larksuite/lark-contact").what, /در حیطهٔ آن نیست.*OpenAPI/);
  const fallback = fa("openai/supabase");
  assert.equal(fallback.what, "");
  assert.notEqual(fallback.description, fallback.use_when);
  assert.match(fallback.description, /Edge Functions.*client…/);
});

test("700-source continuation preserves safety gates and expanded fallback text", () => {
  const fa = (key) => {
    const value = skills.find((s) => s.key === key)?.fa;
    assert.equal(value?.method, "editorial", key);
    return value;
  };
  assert.match(
    fa("posthog/query-clickhouse-via-metabase").what,
    /API key تنها کافی نیست/,
  );
  assert.match(fa("openai/model-audit-tieout").use_when, /نه ساخت مدل از صفر/);
  assert.match(fa("nvidia/jetson-flash-image").description, /نه شخصی‌سازی BSP/);
  assert.match(
    fa("posthog/diagnosing-failed-warehouse-syncs").what,
    /مستقیم resync از صفر نروید/,
  );
  assert.match(fa("firecrawl/yeet").use_when, /فقط با درخواست صریح/);
  assert.match(fa("get-convex/convex-suggest").use_when, /هرگز نصب بدون رضایت/);
  assert.match(
    fa("nvidia/vss-summarize-video").use_when,
    /مشروط به HITL.*نه گزارش/,
  );
  assert.match(fa("nvidia/doca-caps").use_when, /فقط‌خواندنی/);
  assert.match(fa("juliusbrussee/caveman-manage").use_when, /بدون mutation/);
  assert.match(
    fa("larksuite/lark-vc").what,
    /lark-calendar.*vc meeting get --with-participants.*lark-vc-agent/,
  );
  const fallback = fa("cloudflare/git-commit");
  assert.equal(fallback.what, "");
  assert.notEqual(fallback.use_when, fallback.description);
  assert.match(fallback.description, /۷ قاعده.*…/);
});

test("300-source completion retains integration restrictions and truncated sources", () => {
  const fa = (key) => {
    const value = skills.find((s) => s.key === key)?.fa;
    assert.equal(value?.method, "editorial", key);
    return value;
  };
  assert.match(
    fa("caffeinelabs/extension-posting-to-x").what,
    /تنها مسیر.*`x-client`.*OAuth 2.0 PKCE/,
  );
  assert.match(
    fa("caffeinelabs/extension-posting-to-x").what,
    /`icBooking.http_request`.*ممنوع/,
  );
  assert.match(
    fa("caffeinelabs/extension-openai").what,
    /`api.openai.com\/v1\/\.\.\.`.*ممنوع/,
  );
  assert.match(fa("caffeinelabs/extension-openai").what, /۱۳برابر/);
  assert.match(
    fa("signoz/signoz-modifying-dashboards").what,
    /توقف.*https:\/\/signoz.io/,
  );
  assert.match(
    fa("signoz/signoz-modifying-dashboards").what,
    /بدون ابزار MCP.*روی نیاورید/,
  );
  assert.match(fa("shadcn/improve").what, /فقط‌خواندنی.*هیچ پیاده‌سازی/);
  assert.match(
    fa("lllllllama/minimal-run-and-audit").use_when,
    /`repro_outputs\/`.*نه برای اجرای training/,
  );
  assert.ok(fa("apollographql/skill-creator").what.endsWith("شماره‌گذاریِ"));
  assert.match(fa("juliusbrussee/cavecrew").what, /`Explore`/);
  assert.match(fa("dontbesilent2025/dbs-decision").what, /……/);
});

test("final rewrites preserve routing exclusions, workflow prerequisites and fallback tails", () => {
  const fa = (key) => {
    const value = skills.find((s) => s.key === key)?.fa;
    assert.equal(value?.method, "editorial", key);
    return value;
  };
  assert.match(
    fa("okx/okx-defi-invest").what,
    /okx-dapp-discovery.*نه این اسکیل/,
  );
  assert.match(fa("okx/okx-dex-market").use_when, /ممنوعیت قطعی.*هرگز/);
  assert.match(fa("okx/okx-dex-market").use_when, /نه K-line/);
  assert.match(fa("okx/okx-audit-log").use_when, /نه برای موجودی wallet/);
  assert.match(
    fa("posthog/setting-up-a-data-warehouse-source").use_when,
    /wizard → db-schema → create/,
  );
  assert.match(
    fa("posthog/diagnosing-sdk-health").use_when,
    /به‌جای استدلال مستقل.*SDK Doctor/,
  );
  assert.match(
    fa("heygen-com/hyperframes-audio").use_when,
    /نه برای.*`\/media-use`.*نه برای.*`\/hyperframes-core`/,
  );
  assert.match(
    fa("heygen-com/remotion-to-hyperframes").use_when,
    /صریحاً.*نه برای ساخت composition جدید/,
  );
  assert.match(
    fa("lllllllama/explore-code").use_when,
    /صریحاً.*مجزا.*`explore_outputs\/`/,
  );
  assert.match(
    fa("vercel/vercel-optimize").use_when,
    /فقط کاندید دارای پشتوانهٔ metric/,
  );
  assert.match(
    fa("prisma/prisma-compute").use_when,
    /`PRISMA_SERVICE_TOKEN`.*`0\.0\.0\.0`/,
  );
  const copy = fa("coreyhaines31/copywriting");
  assert.equal(copy.what, "");
  assert.ok(copy.use_when.includes("improve this copy,"));
  assert.notEqual(copy.description, copy.use_when);
  assert.ok(copy.description.endsWith("..."));
  assert.match(
    fa("coreyhaines31/product-marketing").description,
    /`\.agents\/product-marketing\.md`/,
  );
  const payments = fa("okx/okx-agent-payments-protocol");
  assert.ok(payments.use_when.endsWith("…"));
  assert.ok(payments.description.endsWith("..."));
  assert.ok(fa("figma/figma-generate-design").what.endsWith("استفاده شود"));
  assert.match(fa("xixu-me/xdrop").use_when, /`\/t\/:transferId#k=\.\.\.`/);
});
