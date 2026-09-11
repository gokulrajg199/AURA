"use client";

import { FormEvent, useEffect, useMemo, useState } from "react";

const API_BASE = process.env.NEXT_PUBLIC_AURA_API_URL || "http://127.0.0.1:8000";

async function auraFetch(input: RequestInfo | URL, init: RequestInit = {}): Promise<Response> {
  const headers = new Headers(init.headers || {});
  if (!headers.has("Authorization")) {
    try {
      const raw = window.localStorage.getItem("aura_session");
      if (raw) {
        const session = JSON.parse(raw) as { token?: string };
        if (session.token) headers.set("Authorization", `Bearer ${session.token}`);
      }
    } catch {
      // Ignore malformed browser session state; the backend will reject protected requests.
    }
  }
  const response = await fetch(input, { ...init, headers });
  if (response.status === 401) throw new Error("Your AURA session is no longer valid. Please sign in again.");
  if (response.status === 403) throw new Error("You do not have access to this AURA project.");
  return response;
}


const STAGES = [
  "understand",
  "investigate",
  "analyze",
  "verdict",
  "innovate",
  "solution",
  "architect",
  "build",
  "experiment",
  "validate",
  "deliver",
];

const LABELS: Record<string, string> = {
  understand: "UNDERSTAND",
  investigate: "INVESTIGATE",
  analyze: "ANALYZE",
  verdict: "AURA VERDICT",
  innovate: "INNOVATE",
  solution: "SOLUTION",
  architect: "ARCHITECT",
  build: "BUILD",
  experiment: "EXPERIMENT",
  validate: "VALIDATE",
  deliver: "DELIVER",
};

const DESCRIPTIONS: Record<string, string> = {
  understand:
    "AURA understands the problem, objectives, requirements, constraints and project context.",
  investigate:
    "AURA investigates existing research, technologies, projects, datasets and solutions.",
  analyze:
    "AURA compares evidence, methods, datasets, experiments, limitations and research trends.",
  verdict:
    "AURA evaluates evidence strength, saturation, opportunity and the recommended research direction.",
  innovate:
    "AURA develops differentiated innovation directions from identified gaps and opportunities.",
  solution:
    "AURA converts the selected direction into a concrete technical solution.",
  architect:
    "AURA designs the system architecture, components, data flow, APIs, AI and deployment structure.",
  build:
    "AURA creates the implementation roadmap, modules, dependencies, code targets and build plan.",
  experiment:
    "AURA designs experiments, hypotheses, baselines, metrics, comparisons and reproducibility plans.",
  validate:
    "AURA evaluates implementation readiness, evidence, experiments, reliability and validation gates.",
  deliver:
    "AURA prepares reports, papers, presentations, demos, viva material and SIH/hackathon outputs.",
};

const STAGE_ICONS: Record<string, string> = {
  understand: "◈",
  investigate: "⌕",
  analyze: "◌",
  verdict: "◆",
  innovate: "✦",
  solution: "◇",
  architect: "⌬",
  build: "⌘",
  experiment: "∿",
  validate: "✓",
  deliver: "▣",
};

type Project = {
  project_id?: string;
  project_name?: string;
  owner_id?: number | null;
  owner_email?: string | null;
  original_idea?: string;
  status?: string;
  current_stage?: string;
  domain?: string[];
  objectives?: string[];
  requirements?: string[];
  constraints?: string[];
  research?: Record<string, unknown>;
  analysis?: Record<string, unknown>;
  innovation?: Record<string, unknown>;
  solution?: Record<string, unknown>;
  architecture?: Record<string, unknown>;
  development?: Record<string, unknown>;
  experiments?: Record<string, unknown>;
  validation?: Record<string, unknown>;
  deliverables?: Record<string, unknown>;
  memory?: unknown[];
  evidence?: unknown[];
  lifecycle?: Lifecycle;
  completion?: Record<string, unknown>;
};

type LifecycleStage = {
  key: string;
  label: string;
  order: number;
  status: string;
  display: string;
  reason: string;
  description: string;
  verified: boolean;
};

type Lifecycle = {
  profile?: string;
  stages?: LifecycleStage[];
  total_stages?: number;
  verified_stages?: number;
  completion_percent?: number;
  completed?: boolean;
  next_blocker?: LifecycleStage | null;
  truth?: string;
};

type Pipeline = {
  stages?: Array<{
    stage?: string;
    label?: string;
    status?: string;
    progress?: number;
  }>;
  progress?: number;
  completed_stages?: number;
  total_stages?: number;
};

type SavedProject = {
  project: Project;
  savedAt: string;
};

type BackendResponse = {
  project?: Project;
  pipeline?: Pipeline;
  project_id?: string;
  project_name?: string;
  owner_id?: number | null;
  owner_email?: string | null;
  original_idea?: string;
  status?: string;
  current_stage?: string;
  data?: {
    project?: Project;
    pipeline?: Pipeline;
    [key: string]: unknown;
  };
  [key: string]: unknown;
};

type Card = {
  label: string;
  value: string;
  tone?: "cyan" | "green" | "violet" | "amber" | "blue";
};

type CleanSection = {
  title: string;
  items: string[];
};

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function safeText(value: unknown): string {
  if (value === null || value === undefined) return "";

  if (
    typeof value === "string" ||
    typeof value === "number" ||
    typeof value === "boolean"
  ) {
    return String(value);
  }

  return "";
}

function humanizeKey(value: string): string {
  return value
    .replace(/([a-z])([A-Z])/g, "$1 $2")
    .replace(/[_-]+/g, " ")
    .replace(/\s+/g, " ")
    .trim()
    .replace(/\b\w/g, (letter) => letter.toUpperCase());
}

function getTruthStatus(project: Project | null): { label: string; detail: string; tone: "good" | "warning" | "neutral" } {
  const validation = isRecord(project?.validation) ? project.validation : {};
  const experiments = isRecord(project?.experiments) ? project.experiments : {};
  const results = isRecord(experiments.results_summary) ? experiments.results_summary : {};
  const verified = validation.scientific_validation === true || validation.results_verified === true || results.scientific_validation === true;
  const resultStatus = safeText(results.status).toUpperCase();
  const executionStatus = safeText(validation.execution_status || experiments.execution_status).toUpperCase();
  const successfulExecution = ["EXECUTED", "RESULTS_AVAILABLE_REVIEW_REQUIRED", "EXPERIMENT_EXECUTED_REVIEW_REQUIRED"].includes(resultStatus) || executionStatus === "EXECUTED";
  const blockedExecution = ["BLOCKED", "BLOCKED_OR_FAILED", "FAILED"].includes(resultStatus) || ["BLOCKED", "BLOCKED_OR_FAILED", "FAILED"].includes(executionStatus);
  if (verified) return { label: "VALIDATED", detail: "Measured execution evidence has been reviewed and scientifically approved.", tone: "good" };
  if (blockedExecution && !successfulExecution) return { label: "EXECUTION BLOCKED", detail: "A controlled execution was attempted but a required project input or prerequisite is missing.", tone: "warning" };
  if (successfulExecution) return { label: "EXECUTION RECORDED", detail: "Controlled execution is recorded; measured evidence still requires scientific review.", tone: "warning" };
  return { label: "DESIGNED • NOT EXECUTED", detail: "Blueprint and workflow are prepared; measured results do not yet exist.", tone: "warning" };
}

function getStageState(stage: string, index: number, pipeline: Pipeline | null, project: Project | null): { status: string; label: string } {
  if (!project) return { status: "pending", label: "PENDING" };
  const truth = getTruthStatus(project);
  const validation = isRecord(project.validation) ? project.validation : {};
  const experiments = isRecord(project.experiments) ? project.experiments : {};
  const results = isRecord(experiments.results_summary) ? experiments.results_summary : {};
  const validated = validation.scientific_validation === true || validation.results_verified === true;
  const experimentExecuted = ["RESULTS_AVAILABLE_REVIEW_REQUIRED", "EXPERIMENT_EXECUTED_REVIEW_REQUIRED"].includes(safeText(results.status).toUpperCase());
  const executionBlocked = truth.label === "EXECUTION BLOCKED";
  if (index <= 2) return { status: "completed", label: "COMPLETED" };
  if (stage === "aura_verdict") return { status: "completed", label: "GENERATED" };
  if (stage === "innovate") return { status: "completed", label: "GENERATED" };
  if (stage === "solution" || stage === "architect") return { status: "completed", label: "DESIGNED" };
  if (stage === "build") return { status: "ready", label: "READY" };
  if (stage === "experiment") {
    if (experimentExecuted) return { status: "completed", label: "EXECUTED" };
    if (executionBlocked) return { status: "blocked", label: "BLOCKED" };
    return { status: "pending", label: "AWAITING EXECUTION" };
  }
  if (stage === "validate") return validated ? { status: "completed", label: "VERIFIED" } : { status: "blocked", label: "REVIEW REQUIRED" };
  if (stage === "deliver") return validated ? { status: "ready", label: "READY" } : { status: "pending", label: "PENDING" };
  return { status: "pending", label: "PENDING" };
}

function BlueprintValue({ value }: { value: unknown }) {
  if (Array.isArray(value)) {
    return <ul className="aura20-blueprint-list">{value.map((item, i) => <li key={i}><span>✦</span><BlueprintValue value={item} /></li>)}</ul>;
  }
  if (isRecord(value)) {
    return <div className="aura20-blueprint-object">{Object.entries(value).map(([key, item]) => <div className="aura20-blueprint-field" key={key}><div className="aura20-blueprint-field-label">{humanizeKey(key)}</div><BlueprintValue value={item} /></div>)}</div>;
  }
  return <span>{String(value ?? "—")}</span>;
}

function cleanText(value: unknown): string {
  if (value === null || value === undefined) return "";

  if (
    typeof value === "string" ||
    typeof value === "number" ||
    typeof value === "boolean"
  ) {
    return String(value);
  }

  return "";
}

function displayValue(value: unknown): string {
  if (value === null || value === undefined) return "";

  if (
    typeof value === "string" ||
    typeof value === "number" ||
    typeof value === "boolean"
  ) {
    return String(value);
  }

  if (Array.isArray(value)) {
    return value
      .map((item) => displayValue(item))
      .filter(Boolean)
      .join(" • ");
  }

  if (isRecord(value)) {
    return Object.entries(value)
      .map(([key, item]) => {
        const text = displayValue(item);
        return text ? `${humanizeKey(key)}: ${text}` : "";
      })
      .filter(Boolean)
      .join(" • ");
  }

  return "";
}

function shortText(value: unknown, max = 220): string {
  const text = displayValue(value);

  if (text.length <= max) return text;

  return text.slice(0, max).trimEnd() + "…";
}

function listFrom(value: unknown): string[] {
  if (!Array.isArray(value)) {
    const text = cleanText(value);
    return text ? [text] : [];
  }

  return value
    .map((item) => {
      if (typeof item === "string") return item;

      if (typeof item === "number" || typeof item === "boolean") {
        return String(item);
      }

      if (isRecord(item)) {
        const preferredKeys = [
          "name",
          "title",
          "label",
          "description",
          "text",
          "claim",
          "objective",
          "requirement",
          "limitation",
          "method",
          "dataset",
          "metric",
          "module",
          "phase",
          "direction",
          "recommendation",
          "finding",
          "component",
          "step",
          "technology",
          "model",
        ];

        for (const key of preferredKeys) {
          const candidate = cleanText(item[key]);

          if (candidate) return candidate;
        }

        return shortText(item, 180);
      }

      return "";
    })
    .map((item) => item.trim())
    .filter(Boolean);
}

function findValue(
  source: Record<string, unknown> | null | undefined,
  keys: string[]
): unknown {
  if (!source) return undefined;

  for (const key of keys) {
    if (source[key] !== undefined && source[key] !== null) {
      return source[key];
    }
  }

  const entries = Object.entries(source);

  for (const wanted of keys) {
    const target = wanted.toLowerCase().replace(/[^a-z0-9]/g, "");

    const found = entries.find(([key]) => {
      const normalized = key.toLowerCase().replace(/[^a-z0-9]/g, "");
      return normalized === target;
    });

    if (found) return found[1];
  }

  return undefined;
}

function collectArray(
  source: Record<string, unknown> | null | undefined,
  keys: string[]
): string[] {
  return listFrom(findValue(source, keys));
}

function firstMeaningfulText(
  source: Record<string, unknown> | null | undefined,
  keys: string[],
  fallback = ""
): string {
  const value = findValue(source, keys);

  if (Array.isArray(value)) {
    return listFrom(value)[0] || fallback;
  }

  const text = cleanText(value);

  return text || fallback;
}

function normalizeProject(payload: unknown): Project | null {
  if (!isRecord(payload)) return null;

  if (isRecord(payload.project)) {
    return payload.project as Project;
  }

  if (
    payload.project_id ||
    payload.original_idea ||
    payload.project_name ||
    payload.research ||
    payload.analysis
  ) {
    return payload as Project;
  }

  if (isRecord(payload.data)) {
    const data = payload.data;

    if (isRecord(data.project)) {
      return data.project as Project;
    }

    if (
      data.project_id ||
      data.original_idea ||
      data.project_name ||
      data.research
    ) {
      return data as Project;
    }
  }

  return null;
}

function normalizePipeline(payload: unknown): Pipeline | null {
  if (!isRecord(payload)) return null;

  if (isRecord(payload.pipeline)) {
    return payload.pipeline as Pipeline;
  }

  if (isRecord(payload.data) && isRecord(payload.data.pipeline)) {
    return payload.data.pipeline as Pipeline;
  }

  if (Array.isArray(payload.stages)) {
    return payload as Pipeline;
  }

  return null;
}

function stageDataFor(
  stage: string,
  project: Project | null
): Record<string, unknown> | null {
  if (!project) return null;

  switch (stage) {
    case "understand":
    case "analyze":
    case "verdict":
      return project.analysis || null;

    case "investigate":
      return project.research || null;

    case "innovate":
      return project.innovation || null;

    case "solution":
      return project.solution || null;

    case "architect":
      return project.architecture || null;

    case "build":
      return project.development || null;

    case "experiment":
      return project.experiments || null;

    case "validate":
      return project.validation || null;

    case "deliver":
      return project.deliverables || null;

    default:
      return null;
  }
}

function getUnderstandingData(
  data: Record<string, unknown> | null
): Record<string, unknown> | null {
  if (!data) return null;

  const nested = findValue(data, [
    "problem_understanding",
    "problemUnderstanding",
    "understanding",
  ]);

  if (isRecord(nested)) {
    return {
      ...data,
      ...nested,
    };
  }

  return data;
}

function getImportantCards(
  stage: string,
  data: Record<string, unknown> | null,
  project: Project | null
): Card[] {
  const viewData =
    stage === "understand"
      ? getUnderstandingData(data)
      : data;

  if (!viewData) {
    if (stage === "understand" && project) {
      return [
        {
          label: "ORIGINAL IDEA",
          value: cleanText(project.original_idea) || "Not provided",
          tone: "cyan",
        },
        {
          label: "NORMALIZED IDEA",
          value: cleanText(project.original_idea) || "Being normalized",
        },
        {
          label: "DOMAIN",
          value:
            project.domain?.join(" • ") || "Domain being identified",
        },
        {
          label: "OBJECTIVES",
          value:
            project.objectives?.join(" • ") ||
            "Objectives being identified",
          tone: "violet",
        },
        {
          label: "REQUIREMENTS",
          value:
            project.requirements?.join(" • ") ||
            "Requirements being identified",
        },
      ];
    }

    return [];
  }

  const mappings: Record<
    string,
    Array<{
      label: string;
      keys: string[];
      tone?: Card["tone"];
    }>
  > = {
    understand: [
      {
        label: "ORIGINAL IDEA",
        keys: ["original_idea", "idea", "user_idea"],
        tone: "cyan",
      },
      {
        label: "NORMALIZED IDEA",
        keys: ["normalized_idea", "normalizedIdea"],
      },
      {
        label: "PROJECT TYPE",
        keys: ["project_type", "type", "project_classification"],
        tone: "violet",
      },
      {
        label: "INTENT",
        keys: ["intent", "detected_intent", "primary_intent"],
        tone: "blue",
      },
      {
        label: "PROBLEM DEFINITION",
        keys: [
          "problem_statement",
          "interpreted_problem",
          "problem",
          "problem_definition",
        ],
        tone: "cyan",
      },
      {
        label: "TARGET CONTEXT",
        keys: ["target_context", "context", "target_users", "users"],
      },
      {
        label: "DOMAINS",
        keys: ["domains", "domain", "detected_domains"],
        tone: "violet",
      },
      {
        label: "CONFIDENCE",
        keys: [
          "understanding_confidence",
          "confidence",
          "confidence_score",
        ],
        tone: "green",
      },
    ],

    investigate: [
      {
        label: "PAPERS FOUND",
        keys: ["paper_count", "papers_found", "total_papers", "count"],
        tone: "cyan",
      },
      {
        label: "RESEARCH SOURCES",
        keys: ["sources", "providers", "source_count"],
      },
      {
        label: "TOP METHODS",
        keys: ["methods", "top_methods"],
      },
      {
        label: "KEY TOPICS",
        keys: ["topics", "keywords", "key_topics"],
        tone: "violet",
      },
    ],

    analyze: [
      {
        label: "RESEARCH TREND",
        keys: ["research_trend", "trend", "trend_summary"],
        tone: "cyan",
      },
      {
        label: "METHODS",
        keys: ["methods", "dominant_methods", "common_methods"],
      },
      {
        label: "LIMITATIONS",
        keys: ["limitations", "common_limitations"],
        tone: "amber",
      },
      {
        label: "EVIDENCE",
        keys: ["evidence_strength", "evidence_score", "confidence"],
        tone: "green",
      },
    ],

    verdict: [
      {
        label: "EVIDENCE STRENGTH",
        keys: ["evidence_strength", "evidence_classification"],
        tone: "cyan",
      },
      {
        label: "SATURATION",
        keys: ["saturation", "research_saturation"],
      },
      {
        label: "OPPORTUNITY",
        keys: [
          "innovation_opportunity",
          "opportunity",
          "opportunity_score",
        ],
        tone: "green",
      },
      {
        label: "AURA RECOMMENDATION",
        keys: [
          "recommended_direction",
          "recommendation",
          "recommended_path",
        ],
        tone: "violet",
      },
    ],

    innovate: [
      {
        label: "INNOVATION DIRECTIONS",
        keys: ["innovation_directions", "directions", "ideas"],
        tone: "violet",
      },
      {
        label: "DIFFERENTIATION",
        keys: ["differentiation_strategies", "differentiation"],
      },
      {
        label: "TECHNICAL CONTRIBUTION",
        keys: [
          "technical_contributions",
          "technical_contribution",
        ],
      },
      {
        label: "FEASIBILITY",
        keys: ["feasibility", "feasibility_score"],
        tone: "green",
      },
    ],

    solution: [
      {
        label: "SOLUTION CONCEPT",
        keys: ["solution_concept", "concept", "solution"],
        tone: "cyan",
      },
      {
        label: "TECHNOLOGY STACK",
        keys: ["technology_stack", "tech_stack", "technologies"],
      },
      {
        label: "DATASET STRATEGY",
        keys: ["dataset_strategy", "datasets", "dataset"],
      },
      {
        label: "READINESS",
        keys: ["readiness", "readiness_score"],
        tone: "green",
      },
    ],

    architect: [
      {
        label: "ARCHITECTURE STYLE",
        keys: ["architecture_style", "style"],
        tone: "cyan",
      },
      {
        label: "COMPONENTS",
        keys: ["components", "architecture_components"],
      },
      {
        label: "DATA FLOW",
        keys: ["data_flow", "flow"],
      },
      {
        label: "ARCHITECTURE SCORE",
        keys: ["architecture_score", "score"],
        tone: "green",
      },
    ],

    build: [
      {
        label: "MODULES",
        keys: ["modules", "implementation_modules"],
        tone: "cyan",
      },
      {
        label: "PHASES",
        keys: ["phases", "development_phases"],
      },
      {
        label: "CODE TARGETS",
        keys: ["code_targets", "code_modules"],
      },
      {
        label: "BUILD READINESS",
        keys: ["readiness", "build_readiness"],
        tone: "green",
      },
    ],

    experiment: [
      {
        label: "HYPOTHESES",
        keys: ["hypotheses", "hypothesis"],
        tone: "violet",
      },
      {
        label: "BASELINES",
        keys: ["baselines", "baseline"],
      },
      {
        label: "METRICS",
        keys: ["metrics", "evaluation_metrics"],
      },
      {
        label: "REPRODUCIBILITY",
        keys: ["reproducibility", "reproducibility_plan"],
        tone: "green",
      },
    ],

    validate: [
      {
        label: "VALIDATION STATUS",
        keys: ["status", "validation_status"],
        tone: "cyan",
      },
      {
        label: "VALIDATION GATES",
        keys: ["gates", "validation_gates"],
      },
      {
        label: "STRENGTHS",
        keys: ["strengths"],
        tone: "green",
      },
      {
        label: "LIMITATIONS",
        keys: ["limitations"],
        tone: "amber",
      },
    ],

    deliver: [
      {
        label: "REPORT",
        keys: ["report", "report_output", "report_plan"],
        tone: "cyan",
      },
      {
        label: "PAPER",
        keys: ["paper", "paper_output", "paper_plan"],
      },
      {
        label: "PRESENTATION",
        keys: ["presentation", "ppt", "presentation_plan"],
      },
      {
        label: "DEMO / SIH",
        keys: ["demo", "sih", "hackathon", "demo_plan"],
        tone: "violet",
      },
    ],
  };

  const cards: Card[] = [];

  for (const item of mappings[stage] || []) {
    const value = findValue(viewData, item.keys);

    if (value === undefined || value === null) continue;

    const maxLength = stage === "understand" ? 950 : 300;
    const text = shortText(value, maxLength);

    if (!text) continue;

    cards.push({
      label: item.label,
      value: text,
      tone: item.tone,
    });
  }

  return cards.slice(0, stage === "understand" ? 8 : 6);
}

function getStageSections(
  stage: string,
  data: Record<string, unknown> | null
): CleanSection[] {
  if (!data) return [];

  const viewData =
    stage === "understand"
      ? getUnderstandingData(data)
      : data;

  if (!viewData) return [];

  const mappings: Record<string, Array<[string, string[]]>> = {
    understand: [
      [
        "Problem Definition",
        [
          "problem_statement",
          "interpreted_problem",
          "problem_definition",
          "problem",
        ],
      ],
      [
        "Target Context",
        ["target_context", "context", "target_users", "users"],
      ],
      [
        "Stakeholders",
        ["stakeholders", "stakeholder_groups"],
      ],
      [
        "Objectives",
        ["objectives", "goals"],
      ],
      [
        "Functional Requirements",
        [
          "functional_requirements",
          "requirements",
        ],
      ],
      [
        "Technical Requirements",
        ["technical_requirements", "technical_needs"],
      ],
      [
        "Constraints",
        ["constraints", "limitations"],
      ],
      [
        "Research Questions",
        ["research_questions", "questions"],
      ],
      [
        "Success Criteria",
        ["success_criteria", "success_metrics", "acceptance_criteria"],
      ],
      [
        "Investigation Focus",
        ["investigation_focus", "research_focus", "focus_areas"],
      ],
      [
        "Uncertainties",
        ["uncertainties", "unknowns", "open_questions"],
      ],
    ],

    investigate: [
      ["Key Findings", ["key_findings", "findings"]],
      ["Research Topics", ["top_topics", "topics", "keywords"]],
      ["Methods Identified", ["methods", "top_methods"]],
      ["Known Limitations", ["limitations", "common_limitations"]],
    ],

    analyze: [
      ["Key Findings", ["key_findings", "findings"]],
      ["Research Gaps", ["research_gaps", "gaps"]],
      ["Research Trends", ["trends", "research_trends"]],
      ["Limitations", ["limitations", "common_limitations"]],
    ],

    verdict: [
      [
        "Recommended Direction",
        ["recommended_direction", "recommendation"],
      ],
      [
        "Innovation Opportunity",
        ["innovation_opportunity", "opportunity"],
      ],
      ["Limitations", ["limitations"]],
      ["Warnings", ["warnings"]],
    ],

    innovate: [
      [
        "Innovation Directions",
        ["innovation_directions", "directions", "ideas"],
      ],
      [
        "Differentiation Strategies",
        ["differentiation_strategies", "differentiation"],
      ],
      [
        "Technical Contributions",
        ["technical_contributions", "contributions"],
      ],
      [
        "Validation Requirements",
        ["validation_requirements"],
      ],
    ],

    solution: [
      ["System Behaviour", ["system_behavior", "behavior"]],
      ["Hardware", ["hardware"]],
      ["Software", ["software"]],
      ["APIs & Data", ["apis", "data_schema"]],
      ["Risks", ["risks"]],
      ["Implementation Strategy", ["implementation_strategy"]],
    ],

    architect: [
      ["Components", ["components"]],
      ["Relationships", ["relationships"]],
      ["Data Flow", ["data_flow"]],
      ["Deployment", ["deployment"]],
      ["Security", ["security"]],
      ["Development Boundaries", ["development_boundaries"]],
    ],

    build: [
      ["Modules", ["modules"]],
      ["Development Phases", ["phases"]],
      ["Implementation Steps", ["implementation_steps", "steps"]],
      ["Dependencies", ["dependencies"]],
      ["Testing Plan", ["testing_plan"]],
      ["Milestones", ["milestones"]],
    ],

    experiment: [
      ["Hypotheses", ["hypotheses"]],
      ["Experiments", ["experiments"]],
      ["Metrics", ["metrics"]],
      ["Ablation & Comparison", ["ablation", "comparison"]],
      ["Failure Analysis", ["failure_analysis"]],
      ["Validation Gates", ["validation_gates"]],
    ],

    validate: [
      ["Validation Gates", ["gates", "validation_gates"]],
      ["Strengths", ["strengths"]],
      ["Limitations", ["limitations"]],
      ["Recommended Actions", ["actions"]],
      ["Warnings", ["warnings"]],
    ],

    deliver: [
      ["Report", ["report", "report_plan"]],
      ["Research Paper", ["paper", "paper_plan"]],
      ["Presentation", ["presentation", "ppt", "presentation_plan"]],
      ["Demo", ["demo", "demo_plan"]],
      ["Viva", ["viva"]],
      ["SIH / Hackathon", ["sih", "hackathon"]],
    ],
  };

  const sections: CleanSection[] = [];

  for (const [title, keys] of mappings[stage] || []) {
    const value = findValue(viewData, keys);

    if (value === undefined || value === null) continue;

    const items = listFrom(value)
      .map((item) => item.trim())
      .filter(Boolean)
      .slice(0, stage === "understand" ? 8 : 5);

    if (items.length > 0) {
      sections.push({
        title,
        items,
      });
    }
  }

  return sections.slice(0, stage === "understand" ? 11 : 6);
}

function getStatusTone(value: string): string {
  const normalized = value.toLowerCase();

  if (
    normalized.includes("validated") ||
    normalized.includes("ready") ||
    normalized.includes("complete") ||
    normalized.includes("strong")
  ) {
    return "good";
  }

  if (
    normalized.includes("not_yet") ||
    normalized.includes("pending") ||
    normalized.includes("incomplete") ||
    normalized.includes("warning")
  ) {
    return "warning";
  }

  return "neutral";
}

function formatStatus(value: string): string {
  return value
    .replace(/_/g, " ")
    .replace(/\b\w/g, (letter) => letter.toUpperCase());
}


function getProjectTruthStatus(project: Project | null): { label: string; detail: string } {
  const validation = isRecord(project?.validation) ? project.validation : {};
  const experiments = isRecord(project?.experiments) ? project.experiments : {};
  const results = isRecord(validation.results) ? validation.results : {};
  const verified = validation.results_verified === true || results.verified === true;
  const executed = safeText(validation.execution_status || experiments.execution_status).toLowerCase().includes("execut");
  if (verified) return { label: "PROJECT VALIDATED", detail: "Execution and results have been recorded and marked for scientific review." };
  if (executed) return { label: "EXECUTION RECORDED", detail: "Controlled execution has been recorded; scientific validation is still pending review." };
  if (project?.status === "completed") return { label: "WORKFLOW COMPLETE", detail: "All AURA reasoning stages are complete; the actual project still requires execution and validation." };
  return { label: "PROJECT IN PROGRESS", detail: "AURA is still building or evaluating the project." };
}

function getStageMessage(
  stage: string,
  data: Record<string, unknown> | null
): string {
  if (!data) {
    return "AURA has connected this stage to the project journey. Detailed intelligence will appear when the engine produces stage results.";
  }

  const messages: Record<string, string[]> = {
    understand: [
      "AURA has converted the initial idea into a structured project problem.",
      "The project context is now connected to objectives, requirements and constraints.",
    ],
    investigate: [
      "AURA has investigated the surrounding research and technology landscape.",
      "Existing work is being used as the evidence foundation for later decisions.",
    ],
    analyze: [
      "AURA has compared the discovered evidence to identify patterns, methods and limitations.",
      "The research landscape is now being transformed into actionable intelligence.",
    ],
    verdict: [
      "AURA has evaluated the evidence and translated it into a project direction.",
      "This verdict separates evidence-supported conclusions from AURA recommendations.",
    ],
    innovate: [
      "AURA has transformed identified opportunities into differentiated innovation paths.",
      "The innovation layer connects research gaps with practical technical contributions.",
    ],
    solution: [
      "AURA has converted the selected direction into a concrete technical solution.",
      "Technology, data, AI, hardware and implementation choices are now connected.",
    ],
    architect: [
      "AURA has designed the internal structure needed to turn the solution into a working system.",
      "Components, relationships, data flow and deployment boundaries are connected.",
    ],
    build: [
      "AURA has transformed the architecture into an executable development roadmap.",
      "Modules, phases, dependencies and testing activities are connected to the project.",
    ],
    experiment: [
      "AURA has designed a validation-oriented experimental strategy.",
      "Hypotheses, baselines, metrics and reproducibility are connected before implementation results are claimed.",
    ],
    validate: [
      "AURA is checking whether the project is supported by implementation and measurable evidence.",
      "Validation status reflects actual evidence rather than assumed performance.",
    ],
    deliver: [
      "AURA has organized the project into final research, presentation and demonstration outputs.",
      "Generated deliverables remain subject to evidence and human review.",
    ],
  };

  return (
    messages[stage]?.[0] ||
    "AURA has processed this stage and connected its intelligence to the project journey."
  );
}

function LoginScreen({
  mode,
  email,
  password,
  name,
  error,
  onModeChange,
  onEmailChange,
  onPasswordChange,
  onNameChange,
  onSubmit,
  onGoogle,
  onGuest,
}: {
  mode: "login" | "create";
  email: string;
  password: string;
  name: string;
  error: string;
  onModeChange: (mode: "login" | "create") => void;
  onEmailChange: (value: string) => void;
  onPasswordChange: (value: string) => void;
  onNameChange: (value: string) => void;
  onSubmit: (event: FormEvent<HTMLFormElement>) => void;
  onGoogle: () => void;
  onGuest: () => void;
}) {
  return (
    <main className="aura-login-page">
      <div className="login-ambient login-ambient-one" />
      <div className="login-ambient login-ambient-two" />
      <div className="login-grid" />
      <div className="login-scanline" />

      <section className="login-shell">
        <div className="login-brand-column">
          <div className="login-logo-wrap" aria-label="AURA logo">
            <div className="aura-login-mark">A</div>
            <div className="aura-login-wordmark">AURA</div>
          </div>
          <div className="login-eyebrow"><span /> AURA INTELLIGENCE CORE</div>
          <h1>Welcome to <span>AURA</span></h1>
          <p className="login-tagline">
            AI Research, Innovation &amp; Development Operating System
          </p>
          <p className="login-description">
            Turn one idea into a connected journey of research, evidence,
            innovation, architecture, development, experimentation,
            validation and final delivery.
          </p>
          <div className="login-capabilities">
            <div><b>01</b><span>INVESTIGATE</span></div>
            <div><b>02</b><span>INNOVATE</span></div>
            <div><b>03</b><span>BUILD</span></div>
            <div><b>04</b><span>VALIDATE</span></div>
          </div>
        </div>

        <div className="login-card">
          <div className="login-card-top">
            <div>
              <div className="login-card-kicker">SECURE RESEARCH WORKSPACE</div>
              <h2>{mode === "login" ? "Sign in to AURA" : "Create your AURA account"}</h2>
            </div>
            <div className="login-live"><span /> CORE READY</div>
          </div>

          <div className="auth-tabs">
            <button className={mode === "login" ? "active" : ""} onClick={() => onModeChange("login")}>LOGIN</button>
            <button className={mode === "create" ? "active" : ""} onClick={() => onModeChange("create")}>CREATE ACCOUNT</button>
          </div>

          <form onSubmit={onSubmit} className="login-form">
            {mode === "create" && (
              <label>
                <span>NAME</span>
                <input value={name} onChange={(e) => onNameChange(e.target.value)} placeholder="Your name" autoComplete="name" />
              </label>
            )}
            <label>
              <span>EMAIL</span>
              <input type="email" value={email} onChange={(e) => onEmailChange(e.target.value)} placeholder="researcher@example.com" autoComplete="email" required />
            </label>
            <label>
              <span>PASSWORD</span>
              <input type="password" value={password} onChange={(e) => onPasswordChange(e.target.value)} placeholder="Minimum 6 characters" autoComplete={mode === "login" ? "current-password" : "new-password"} required />
            </label>

            {error && <div className="login-error">{error}</div>}

            <button className="primary-auth-button" type="submit">
              {mode === "login" ? "LOGIN TO AURA" : "CREATE AURA ACCOUNT"}<span>→</span>
            </button>
          </form>

          <div className="auth-divider"><span /> OR <span /></div>

          <button className="google-auth-button" onClick={onGoogle}>
            <span className="google-mark">G</span>
            CONTINUE WITH GOOGLE
          </button>

          <button className="guest-auth-button" onClick={onGuest}>
            CONTINUE AS GUEST
          </button>

          <div className="login-trust">
            <span>●</span> Guest mode is local-only. Email/password accounts use AURA backend authentication; cloud persistence still requires production storage.
          </div>
        </div>
      </section>
    </main>
  );
}

function ProjectDashboard({
  projects,
  onResume,
  onDelete,
  onNewProject,
}: {
  projects: SavedProject[];
  onResume: (saved: SavedProject) => void;
  onDelete: (projectId: string) => void;
  onNewProject: () => void;
}) {
  return (
    <section className="project-dashboard" aria-label="My AURA projects">
      <div className="project-dashboard-head">
        <div>
          <span className="project-dashboard-kicker">AURA PROJECT VAULT</span>
          <h2>Continue your research journey.</h2>
          <p>Your latest AURA projects are saved in this browser and can be resumed without losing the workspace snapshot.</p>
        </div>
        <button type="button" className="vault-new-button" onClick={onNewProject}>+ NEW PROJECT</button>
      </div>
      {projects.length === 0 ? (
        <div className="vault-empty">
          <div className="vault-empty-orb">A</div>
          <div>
            <strong>NO SAVED PROJECTS YET</strong>
            <p>Create your first AURA project. Once AURA starts processing it, the complete project snapshot will appear here automatically.</p>
          </div>
        </div>
      ) : (
      <div className="saved-project-grid">
        {projects.slice(0, 6).map((saved) => {
          const item = saved.project;
          const stageIndex = Math.max(0, STAGES.indexOf(item.current_stage || "understand"));
          const truth = getTruthStatus(item);
          const scientificallyValidated = truth.label === "VALIDATED";
          const progress = scientificallyValidated ? 100 : Math.round((stageIndex / STAGES.length) * 100);
          return (
            <article className="saved-project-card" key={item.project_id || item.project_name}>
              <div className="saved-project-top">
                <span className="saved-project-icon">A</span>
                <span className={"saved-project-status " + (scientificallyValidated ? "complete" : "active")}>
                  {scientificallyValidated ? "SCIENTIFICALLY VALIDATED" : truth.label}
                </span>
              </div>
              <h3>{item.project_name || "Untitled AURA Project"}</h3>
              <p>{item.original_idea || "Project idea unavailable."}</p>
              <div className="saved-project-progress">
                <div><span>{progress}% JOURNEY</span><span>{LABELS[item.current_stage || "understand"] || "UNDERSTAND"}</span></div>
                <div className="saved-project-track"><i style={{ width: progress + "%" }} /></div>
              </div>
              <div className="saved-project-actions">
                <button type="button" onClick={() => onResume(saved)}>RESUME →</button>
                <button type="button" className="saved-project-delete" onClick={() => item.project_id && onDelete(item.project_id)} aria-label={`Delete ${item.project_name || "project"}`}>DELETE</button>
              </div>
              <small>SAVED {new Date(saved.savedAt).toLocaleString()}</small>
            </article>
          );
        })}
      </div>
      )}
      {projects.length > 6 && <div className="vault-more">+ {projects.length - 6} more saved project{projects.length - 6 === 1 ? "" : "s"}</div>}
    </section>
  );
}

export default function Home() {
  const [authenticated, setAuthenticated] = useState(false);
  const [authMode, setAuthMode] = useState<"login" | "create">("login");
  const [authEmail, setAuthEmail] = useState("");
  const [authPassword, setAuthPassword] = useState("");
  const [authName, setAuthName] = useState("");
  const [authError, setAuthError] = useState("");
  const [userName, setUserName] = useState("Researcher");
  const [userEmail, setUserEmail] = useState("");
  const [authToken, setAuthToken] = useState("");
  const [userRole, setUserRole] = useState("researcher");
  const [savedProjects, setSavedProjects] = useState<SavedProject[]>([]);

  const [idea, setIdea] = useState("");
  const [projectName, setProjectName] = useState("");

  const [backendOnline, setBackendOnline] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const [project, setProject] = useState<Project | null>(null);
  const [pipeline, setPipeline] = useState<Pipeline | null>(null);

  const [activeStage, setActiveStage] = useState("understand");
  const [showWorkspace, setShowWorkspace] = useState(false);

  useEffect(() => {
    checkBackend();
    let cancelled = false;
    try {
      const saved = window.localStorage.getItem("aura_session");
      if (saved) {
        const session = JSON.parse(saved) as { authenticated?: boolean; name?: string; email?: string; token?: string; role?: string };
        if (session.authenticated) {
          setAuthenticated(true);
          setUserEmail(session.email || "");
          setUserName(session.name || session.email?.split("@")[0] || "Researcher");
          setAuthToken(session.token || "");
          setUserRole(session.role || "researcher");

          // Revalidate persisted sessions against the backend before trusting
          // an old browser token or its cached project snapshots. Guest mode
          // intentionally has no token and remains local/ownerless.
          if (session.token) {
            auraFetch(API_BASE + "/api/aura/auth/me", { cache: "no-store" })
              .then(async (response) => {
                if (!response.ok) throw new Error("Session validation failed.");
                const payload = await response.json().catch(() => ({}));
                if (cancelled) return;
                const verified = payload.user || {};
                const email = verified.email || session.email || "";
                const name = session.name || email.split("@")[0] || "Researcher";
                const role = verified.role || session.role || "researcher";
                saveSession(name, email, session.token || "", role);
              })
              .catch(() => {
                if (cancelled) return;
                window.localStorage.removeItem("aura_session");
                setAuthenticated(false);
                setUserEmail("");
                setAuthToken("");
                setUserRole("researcher");
                setSavedProjects([]);
              });
          }
        }
      }
    } catch {
      window.localStorage.removeItem("aura_session");
    }
    return () => { cancelled = true; };
  }, []);

  useEffect(() => {
    if (!authenticated || !userEmail) {
      setSavedProjects([]);
      return;
    }

    try {
      const raw = window.localStorage.getItem(`aura_projects_${userEmail.toLowerCase()}`);
      if (!raw) {
        setSavedProjects([]);
        return;
      }
      const parsed = JSON.parse(raw);
      if (Array.isArray(parsed)) {
        setSavedProjects(parsed.filter((entry) => entry && entry.project));
      } else {
        setSavedProjects([]);
      }
    } catch {
      setSavedProjects([]);
    }
  }, [authenticated, userEmail]);

  useEffect(() => {
    if (!authenticated || !userEmail || !project?.project_id) return;

    setSavedProjects((current) => {
      const nextEntry: SavedProject = { project, savedAt: new Date().toISOString() };
      const existing = current.filter((entry) => entry.project?.project_id !== project.project_id);
      const next = [nextEntry, ...existing].slice(0, 20);
      try {
        window.localStorage.setItem(`aura_projects_${userEmail.toLowerCase()}`, JSON.stringify(next));
      } catch {
        // Storage can fail in private/restricted browser contexts; workspace still works.
      }
      return next;
    });
  }, [project, authenticated, userEmail]);

  function resumeSavedProject(saved: SavedProject) {
    const restored = saved.project;
    setProject(restored);
    setIdea(restored.original_idea || "");
    setProjectName(restored.project_name || "");
    setShowWorkspace(true);
    setActiveStage(restored.current_stage && STAGES.includes(restored.current_stage) ? restored.current_stage : "understand");
    setError("");
    const restoredProjectId = restored.project_id;
    if (restoredProjectId && backendOnline) {
      fetchProject(restoredProjectId).catch(() => {
        // Never keep displaying a cached project after the server rejects it.
        // This prevents stale/tampered browser snapshots from bypassing the
        // backend ownership boundary in the UI.
        setProject(null);
        setShowWorkspace(false);
        setError("This project is no longer available to your account.");
        deleteSavedProject(restoredProjectId);
      });
    }
  }

  function deleteSavedProject(projectId: string) {
    setSavedProjects((current) => {
      const next = current.filter((entry) => entry.project?.project_id !== projectId);
      try {
        window.localStorage.setItem(`aura_projects_${userEmail.toLowerCase()}`, JSON.stringify(next));
      } catch {
        // Ignore storage failures.
      }
      return next;
    });
  }

  function saveSession(name: string, email: string, token = "", role = "researcher") {
    const cleanName = name.trim() || email.split("@")[0] || "Researcher";
    setUserName(cleanName);
    setUserEmail(email);
    setAuthToken(token);
    setUserRole(role);
    setAuthenticated(true);
    window.localStorage.setItem(
      "aura_session",
      JSON.stringify({ authenticated: true, name: cleanName, email, token, role })
    );
    setAuthError("");
  }

  async function handleAuthSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const email = authEmail.trim();
    const password = authPassword;
    if (!email || !email.includes("@")) { setAuthError("Enter a valid email address."); return; }
    if (password.length < 8) { setAuthError("Password must contain at least 8 characters."); return; }
    try {
      const endpoint = authMode === "create" ? "/api/aura/auth/register" : "/api/aura/auth/login";
      const response = await auraFetch(API_BASE + endpoint, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ email, password, role: "researcher" }) });
      const data = await response.json().catch(() => ({}));
      if (!response.ok) throw new Error(data.detail || "Authentication failed.");
      if (authMode === "create") {
        setAuthMode("login"); setAuthPassword(""); setAuthError("Account created. Please sign in."); return;
      }
      saveSession(data.user?.email?.split("@")[0] || "Researcher", data.user?.email || email, data.access_token || "", data.user?.role || "researcher");
    } catch (e) { setAuthError(e instanceof Error ? e.message : "Authentication failed."); }
  }

  function continueWithGoogle() {
    setAuthError("Google sign-in is not configured. Use email/password or Guest mode.");
  }

  function continueAsGuest() {
    saveSession("Guest Researcher", "guest@aura.local", "", "researcher");
  }

  function logout() {
    window.localStorage.removeItem("aura_session");
    setAuthenticated(false);
    setUserEmail("");
    setAuthToken("");
    setUserRole("researcher");
    setSavedProjects([]);
    setAuthEmail("");
    setAuthPassword("");
    setAuthName("");
    setAuthError("");
    resetAura();
  }

  async function checkBackend() {
    try {
      const response = await auraFetch(API_BASE + "/health", {
        cache: "no-store",
      });

      setBackendOnline(response.ok);
    } catch {
      setBackendOnline(false);
    }
  }

  async function fetchProject(projectId: string) {
    const response = await fetch(
      API_BASE + "/api/aura/projects/" + projectId,
      {
        cache: "no-store",
      }
    );

    if (!response.ok) {
      throw new Error("Unable to retrieve the AURA project.");
    }

    const payload: BackendResponse = await response.json();

    const normalizedProject = normalizeProject(payload);

    if (normalizedProject) {
      setProject(normalizedProject);

      if (
        normalizedProject.current_stage &&
        STAGES.includes(normalizedProject.current_stage)
      ) {
        setActiveStage(normalizedProject.current_stage);
      }
    }

    const normalizedPipeline = normalizePipeline(payload);

    if (normalizedPipeline) {
      setPipeline(normalizedPipeline);
    }

    return normalizedProject;
  }

  async function fetchPipeline() {
    try {
      const response = await auraFetch(API_BASE + "/api/aura/pipeline", {
        cache: "no-store",
      });

      if (!response.ok) return;

      const payload = await response.json();
      const normalized = normalizePipeline(payload);

      if (normalized) {
        setPipeline(normalized);
      }
    } catch {
      // Keep existing state.
    }
  }

  async function runAura(event: FormEvent) {
    event.preventDefault();

    if (!idea.trim()) {
      setError("Tell AURA your idea, problem or research question first.");
      return;
    }

    setError("");
    setLoading(true);

    try {
      const createResponse = await fetch(
        API_BASE + "/api/aura/projects",
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            idea: idea.trim(),
            project_name: projectName.trim() || undefined,
          }),
        }
      );

      if (!createResponse.ok) {
        const errorText = await createResponse.text();

        throw new Error(
          errorText || "AURA could not create the project."
        );
      }

      const createPayload: BackendResponse =
        await createResponse.json();

      const createdProject = normalizeProject(createPayload);

      const projectId =
        safeText(createPayload.project_id) ||
        safeText(createdProject?.project_id);

      if (!projectId) {
        throw new Error(
          "AURA created the project but no project ID was returned."
        );
      }

      if (createdProject) {
        setProject(createdProject);
      }

      setShowWorkspace(true);
      setActiveStage("understand");

      const runResponse = await fetch(
        API_BASE + "/api/aura/projects/" + projectId + "/run",
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            stop_on_failure: true,
          }),
        }
      );

      if (!runResponse.ok) {
        const errorText = await runResponse.text();

        throw new Error(
          errorText ||
            "AURA could not start the autonomous pipeline."
        );
      }

      const runPayload: BackendResponse =
        await runResponse.json();

      const runProject = normalizeProject(runPayload);

      if (runProject) {
        setProject(runProject);
      }

      const runPipeline = normalizePipeline(runPayload);

      if (runPipeline) {
        setPipeline(runPipeline);
      }

      await fetchProject(projectId);
      await fetchPipeline();
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Something went wrong while running AURA."
      );
    } finally {
      setLoading(false);
    }
  }

  function startExample(example: string) {
    setIdea(example);
    setError("");
  }

  function resetAura() {
    setIdea("");
    setProjectName("");
    setProject(null);
    setPipeline(null);
    setShowWorkspace(false);
    setActiveStage("understand");
    setError("");
  }

  if (!authenticated) {
    return (
      <LoginScreen
        mode={authMode}
        email={authEmail}
        password={authPassword}
        name={authName}
        error={authError}
        onModeChange={(mode) => {
          setAuthMode(mode);
          setAuthError("");
        }}
        onEmailChange={setAuthEmail}
        onPasswordChange={setAuthPassword}
        onNameChange={setAuthName}
        onSubmit={handleAuthSubmit}
        onGoogle={continueWithGoogle}
        onGuest={continueAsGuest}
      />
    );
  }

  const currentStage =
    project?.current_stage &&
    STAGES.includes(project.current_stage)
      ? project.current_stage
      : activeStage;

  const currentStageIndex = Math.max(
    0,
    STAGES.indexOf(currentStage)
  );

  // AURA Journey progress and Project Lifecycle completion are deliberately separate.
  const stageStates = project ? STAGES.map((stage, index) => getStageState(stage, index, pipeline, project)) : [];
  const journeyVerifiedCount = stageStates.filter((item) => ["COMPLETED", "EXECUTED", "VERIFIED"].includes(item.label)).length;
  const progress = project ? Math.round((journeyVerifiedCount / STAGES.length) * 100) : 0;
  const configuredCount = project ? STAGES.length : 0;

  return (
    <main className="aura-app">
      <div className="ambient ambient-one" />
      <div className="ambient ambient-two" />
      <div className="ambient ambient-three" />
      <div className="scanline" />
      <div className="grid-background" />

      <header className="topbar">
        <div className="brand">
          <div className="logo-wrap">
            <img src="/aura-logo.png" alt="AURA" />
          </div>

          <div className="brand-copy">
            <div className="brand-name">AURA</div>
            <div className="brand-subtitle">
              RESEARCH • INNOVATION • DEVELOPMENT
            </div>
          </div>
        </div>

        <div className="top-status">
          <div className="system-status">
            <span
              className={
                backendOnline
                  ? "status-dot online"
                  : "status-dot offline"
              }
            />

            {backendOnline
              ? "AURA CORE ONLINE"
              : "CORE OFFLINE"}
          </div>

          <button
            className="vault-top-button"
            onClick={() => setShowWorkspace(false)}
            title="Open AURA Project Vault"
          >
            PROJECT VAULT
          </button>

          <button
            className="new-project-button"
            onClick={resetAura}
          >
            + NEW PROJECT
          </button>

          <button className="logout-button" onClick={logout} title="Sign out of AURA">
            {userName.toUpperCase()} · SIGN OUT
          </button>
        </div>
      </header>

      {!showWorkspace ? (
        <>
          <ProjectDashboard
            projects={savedProjects}
            onResume={resumeSavedProject}
            onDelete={deleteSavedProject}
            onNewProject={resetAura}
          />
          <section className="landing">
          <div className="hero-left">
            <div className="eyebrow">
              <span />
              AI RESEARCH, INNOVATION & DEVELOPMENT OS
            </div>

            <h1>
              Give AURA
              <br />
              an <span>idea.</span>
            </h1>

            <h2>
              Build the
              <br />
              entire journey.
            </h2>

            <p className="hero-description">
              One input becomes a connected research and development
              journey. AURA investigates the world, analyzes evidence,
              identifies opportunities, designs the solution,
              architects the system, plans the build, experiments,
              validates and prepares the final outputs.
            </p>

            <div className="hero-proof">
              <div>
                <strong>01</strong>
                <span>INVESTIGATE</span>
              </div>

              <div>
                <strong>02</strong>
                <span>INNOVATE</span>
              </div>

              <div>
                <strong>03</strong>
                <span>BUILD</span>
              </div>

              <div>
                <strong>04</strong>
                <span>VALIDATE</span>
              </div>
            </div>
          </div>

          <div className="hero-right">
            <div className="core-orbit">
              <div className="orbit orbit-one" />
              <div className="orbit orbit-two" />
              <div className="orbit orbit-three" />

              <div className="core-glow">
                <div className="core-inner">
                  <span>A</span>
                </div>
              </div>

              <div className="orbit-node node-one" />
              <div className="orbit-node node-two" />
              <div className="orbit-node node-three" />
            </div>

            <form
              className="idea-card"
              onSubmit={runAura}
            >
              <div className="card-top">
                <div>
                  <div className="card-label">
                    START WITH ONE INPUT
                  </div>

                  <div className="card-title">
                    What do you want to build?
                  </div>
                </div>

                <div className="input-counter">
                  {idea.length}/2000
                </div>
              </div>

              <textarea
                value={idea}
                onChange={(event) =>
                  setIdea(event.target.value)
                }
                maxLength={2000}
                placeholder="Describe your idea, problem, research question, project or innovation..."
              />

              <div className="quick-examples">
                <span>TRY:</span>

                <button
                  type="button"
                  onClick={() =>
                    startExample(
                      "AI based early detection of plant diseases using computer vision and IoT"
                    )
                  }
                >
                  Plant disease detection
                </button>

                <button
                  type="button"
                  onClick={() =>
                    startExample(
                      "Smart IoT based hydroponic plant growth monitoring and intelligent nutrition management"
                    )
                  }
                >
                  Smart hydroponics
                </button>

                <button
                  type="button"
                  onClick={() =>
                    startExample(
                      "Agentic AI system for intelligent research and project development"
                    )
                  }
                >
                  Agentic AI
                </button>
              </div>

              <div className="input-bottom">
                <input
                  value={projectName}
                  onChange={(event) =>
                    setProjectName(event.target.value)
                  }
                  placeholder="Project name (optional)"
                />

                <button
                  type="submit"
                  className="run-button"
                  disabled={loading || !backendOnline}
                >
                  <span>
                    {loading
                      ? "AURA IS WORKING..."
                      : "RUN AURA"}
                  </span>

                  <b>→</b>
                </button>
              </div>

              {error && (
                <div className="error-box">
                  {error}
                </div>
              )}

              {!backendOnline && (
                <div className="offline-note">
                  AURA Core is not reachable. Start the backend on
                  port 8000.
                </div>
              )}
            </form>

            <div className="autonomous-note">
              <span className="pulse" />
              AURA AUTONOMOUS PIPELINE
              <span className="line" />
              11 CONNECTED STAGES
            </div>
          </div>
        </section>
        </>
      ) : (
        <section className="workspace">
          <aside className="sidebar">
            <div className="sidebar-heading">
              AURA PROJECT
            </div>

            <div className="project-mini">
              <div className="project-icon">A</div>

              <div>
                <strong>
                  {project?.project_name ||
                    projectName ||
                    "AURA Project"}
                </strong>

                <span className="project-truth-badge">
                  {getTruthStatus(project).label}
                </span>
              </div>
            </div>

            <div className="progress-box">
              <div className="progress-header">
                <span>PROJECT JOURNEY</span>
                <strong>{progress}% VERIFIED PROGRESS</strong>
              </div>
              <div className="progress-track"><div className="progress-fill" style={{ width: progress + "%" }} /></div>
              <small>{journeyVerifiedCount} / {STAGES.length} AURA STAGES VERIFIED · {configuredCount} CONFIGURED</small>
              <div className="truth-status-grid">
                <div><b>WORKFLOW</b><span>{configuredCount} / {STAGES.length} CONFIGURED</span></div>
                <div><b>DESIGN</b><span>COMPLETE</span></div>
                <div><b>RESEARCH</b><span>EVIDENCE REQUIRED</span></div>
                <div><b>IMPLEMENTATION</b><span>READY</span></div>
                <div><b>EXPERIMENT</b><span>{getStageState("experiment", 8, pipeline, project).label}</span></div>
                <div><b>VALIDATION</b><span>{getStageState("validate", 9, pipeline, project).label}</span></div>
                <div><b>DELIVERY</b><span>{getStageState("deliver", 10, pipeline, project).label}</span></div>
              </div>
              <div className="scientific-truth-strip"><span>🛡</span><div><b>SCIENTIFIC TRUTH</b><small>NO FABRICATED RESULTS · DESIGNED ≠ EXECUTED ≠ VALIDATED</small></div></div>
            </div>

            <div className="sidebar-section">
              <div className="sidebar-label">
                AURA JOURNEY
              </div>

              {STAGES.map((stage, index) => {
                const stageState = getStageState(stage, index, pipeline, project);
                const stageStatus = stageState.status;

                return (
                  <button
                    key={stage}
                    className={
                      "stage-nav " +
                      (activeStage === stage
                        ? "active "
                        : "") +
                      stageStatus
                    }
                    onClick={() =>
                      setActiveStage(stage)
                    }
                  >
                    <span className="stage-number">
                      {String(index + 1).padStart(2, "0")}
                    </span>

                    <span className="stage-icon">
                      {STAGE_ICONS[stage]}
                    </span>

                    <span className="stage-name">
                      {LABELS[stage]}
                    </span>

                    <span className="stage-marker">
                      {stageStatus === "completed" ? "✓" : stageStatus === "running" ? "●" : stageStatus === "ready" ? "◐" : stageStatus === "blocked" ? "!" : "○"}
                    </span>
                    <span className="stage-state-label">{stageState.label}</span>
                  </button>
                );
              })}
            </div>

            <div className="sidebar-section system-section">
              <div className="sidebar-label">
                PROJECT INTELLIGENCE
              </div>

              <button
                className={
                  "system-nav " +
                  (activeStage === "evidence"
                    ? "active"
                    : "")
                }
                onClick={() =>
                  setActiveStage("evidence")
                }
              >
                ◉ Evidence & Trust
              </button>

              <button
                className={
                  "system-nav " +
                  (activeStage === "memory"
                    ? "active"
                    : "")
                }
                onClick={() =>
                  setActiveStage("memory")
                }
              >
                ◌ Project Memory
              </button>
              <button
                className={"system-nav " + (activeStage === "aura2" ? "active" : "")}
                onClick={() => setActiveStage("aura2")}
              >
                ✦ AURA 2.0 INTELLIGENCE
              </button>
            </div>
          </aside>

          <div className="workspace-main">
            <div className="workspace-top">
              <div>
                <div className="workspace-eyebrow">
                  AURA AUTONOMOUS WORKSPACE
                </div>

                <h1>
                  {project?.project_name ||
                    projectName ||
                    "AURA Project"}
                </h1>

                <p>
                  {project?.original_idea ||
                    idea ||
                    "Project context loading..."}
                </p>
              </div>

              <button
                className="back-button"
                onClick={resetAura}
              >
                ← NEW IDEA
              </button>
            </div>

            <div className="neural-pipeline">
        <div className="np-header">
          <div><span className="np-kicker">AURA NEURAL PIPELINE</span><span className="np-caption">Autonomous research-to-delivery execution map</span></div>
          <div className="np-live"><span className="np-live-dot" /> LIVE INTELLIGENCE</div>
        </div>
        <div className="np-track">
          {STAGES.map((item, index) => {
            const stageState = getStageState(item, index, pipeline, project);
            const active = item === activeStage;
            const done = stageState.status === "completed";
            return <button type="button" className={`np-node ${active ? "active" : ""} ${done ? "done" : ""}`} key={item} onClick={() => setActiveStage(item)} aria-label={`Open ${LABELS[item]} stage`}>
              <div className="np-orb"><span>{String(index + 1).padStart(2,"0")}</span></div>
              <div className="np-label">{LABELS[item]}</div>
              {index < STAGES.length - 1 && <div className="np-link"><i /></div>}
            </button>;
          })}
        </div>
      </div>

      <div className="pipeline-strip">
              {STAGES.map((stage, index) => {
                const status =
                  index < currentStageIndex
                    ? "completed"
                    : index === currentStageIndex
                      ? "active"
                      : "pending";

                return (
                  <button
                    key={stage}
                    className={
                      "pipeline-stage " + status
                    }
                    onClick={() =>
                      setActiveStage(stage)
                    }
                  >
                    <span>
                      {String(index + 1).padStart(2, "0")}
                    </span>

                    <b>{LABELS[stage]}</b>
                  </button>
                );
              })}
            </div>

            <ProjectLifecycle project={project} />
            <AuraProjectStatusLayer project={project} pipeline={pipeline} />
            <PlatformCompletionPanel />
            <ProjectHealthPanel project={project} />

            {activeStage === "evidence" ? (
              <EvidencePanel project={project} />
            ) : activeStage === "memory" ? (
              <MemoryPanel project={project} />
            ) : activeStage === "aura2" ? (
              <AuraTwoPointZero project={project} idea={idea} projectName={projectName} />
            ) : (
              <StagePanel
                stage={activeStage}
                project={project}
                index={STAGES.indexOf(activeStage)}
              />
            )}
          </div>
        </section>
      )}

      <footer className="footer">
        <span>AURA</span>
        <span>
          AI RESEARCH • INNOVATION • DEVELOPMENT OS
        </span>
        <span>CORE v6.1 • AURA 1.0 + INTELLIGENCE 2.0</span>
      </footer>

      <style jsx global>{`
        * {
          box-sizing: border-box;
        }

        html,
        body {
          margin: 0;
          padding: 0;
          background: #030509;
          color: #eef7ff;
          font-family:
            Inter,
            ui-sans-serif,
            system-ui,
            -apple-system,
            BlinkMacSystemFont,
            "Segoe UI",
            sans-serif;
        }

        body {
          min-height: 100vh;
        }

        button,
        input,
        textarea {
          font: inherit;
        }

        button {
          cursor: pointer;
        }

        .aura-app {
          min-height: 100vh;
          position: relative;
          overflow: hidden;
          background:
            radial-gradient(
              circle at 75% 20%,
              rgba(0, 213, 255, 0.09),
              transparent 28%
            ),
            radial-gradient(
              circle at 20% 80%,
              rgba(100, 75, 255, 0.08),
              transparent 30%
            ),
            #030509;
        }

        .grid-background {
          position: fixed;
          inset: 0;
          pointer-events: none;
          opacity: 0.14;
          background-image:
            linear-gradient(
              rgba(255, 255, 255, 0.035) 1px,
              transparent 1px
            ),
            linear-gradient(
              90deg,
              rgba(255, 255, 255, 0.035) 1px,
              transparent 1px
            );
          background-size: 42px 42px;
          mask-image: linear-gradient(
            to bottom,
            black,
            transparent 92%
          );
        }

        .scanline {
          position: fixed;
          inset: 0;
          pointer-events: none;
          z-index: 20;
          opacity: 0.018;
          background: repeating-linear-gradient(
            to bottom,
            transparent 0,
            transparent 3px,
            rgba(255, 255, 255, 0.08) 4px
          );
        }

        .ambient {
          position: fixed;
          width: 500px;
          height: 500px;
          border-radius: 50%;
          filter: blur(100px);
          pointer-events: none;
          opacity: 0.08;
          animation: ambientFloat 12s ease-in-out infinite;
        }

        .ambient-one {
          top: -200px;
          right: 5%;
          background: #00d9ff;
        }

        .ambient-two {
          bottom: -260px;
          left: 15%;
          background: #685cff;
          animation-delay: -4s;
        }

        .ambient-three {
          top: 35%;
          right: -300px;
          background: #006cff;
          animation-delay: -8s;
        }

        .topbar {
          position: relative;
          z-index: 30;
          height: 84px;
          padding: 0 44px;
          border-bottom: 1px solid
            rgba(255, 255, 255, 0.07);
          display: flex;
          align-items: center;
          justify-content: space-between;
          backdrop-filter: blur(18px);
          background: rgba(3, 5, 9, 0.74);
        }

        .brand {
          display: flex;
          align-items: center;
          gap: 13px;
        }

        .logo-wrap {
          width: 42px;
          height: 42px;
          border-radius: 12px;
          border: 1px solid
            rgba(0, 216, 255, 0.35);
          display: grid;
          place-items: center;
          background: rgba(0, 216, 255, 0.05);
          box-shadow:
            0 0 28px rgba(0, 216, 255, 0.1);
          overflow: hidden;
        }

        .logo-wrap img {
          width: 34px;
          height: 34px;
          object-fit: contain;
        }

        .brand-name {
          font-size: 19px;
          font-weight: 900;
          letter-spacing: 0.12em;
        }

        .brand-subtitle {
          margin-top: 2px;
          color: #667386;
          font-size: 8px;
          font-weight: 800;
          letter-spacing: 0.2em;
        }

        .top-status {
          display: flex;
          align-items: center;
          gap: 20px;
        }

        .system-status {
          color: #778598;
          font-size: 9px;
          font-weight: 800;
          letter-spacing: 0.13em;
          display: flex;
          align-items: center;
          gap: 8px;
        }

        .status-dot {
          width: 7px;
          height: 7px;
          border-radius: 50%;
          display: inline-block;
        }

        .status-dot.online {
          background: #1ce5a0;
          box-shadow: 0 0 12px #1ce5a0;
        }

        .status-dot.offline {
          background: #ff6575;
          box-shadow: 0 0 12px #ff6575;
        }

        .new-project-button,
        .back-button {
          border: 1px solid
            rgba(255, 255, 255, 0.1);
          background: rgba(255, 255, 255, 0.035);
          color: #aeb9c9;
          border-radius: 10px;
          padding: 10px 15px;
          font-size: 9px;
          font-weight: 900;
          letter-spacing: 0.12em;
          transition: 0.25s ease;
        }

        .new-project-button:hover,
        .back-button:hover {
          border-color: rgba(
            0,
            214,
            255,
            0.4
          );
          color: #fff;
          transform: translateY(-1px);
        }

        .landing {
          position: relative;
          z-index: 2;
          min-height: calc(100vh - 84px);
          display: grid;
          grid-template-columns: 1fr 1fr;
          gap: 30px;
          align-items: center;
          padding: 55px 7vw 85px;
        }

        .hero-left {
          max-width: 690px;
          padding-left: 3vw;
        }

        .eyebrow {
          display: flex;
          align-items: center;
          gap: 10px;
          color: #00d7ff;
          font-size: 9px;
          font-weight: 900;
          letter-spacing: 0.22em;
          margin-bottom: 30px;
        }

        .eyebrow span {
          width: 26px;
          height: 1px;
          background: #00d7ff;
          box-shadow: 0 0 12px #00d7ff;
        }

        .hero-left h1,
        .hero-left h2 {
          margin: 0;
          font-size: clamp(
            64px,
            7.2vw,
            115px
          );
          line-height: 0.88;
          letter-spacing: -0.065em;
          font-weight: 900;
        }

        .hero-left h1 span {
          background: linear-gradient(
            110deg,
            #ffffff 10%,
            #a8edff 45%,
            #5d74ff 95%
          );
          -webkit-background-clip: text;
          background-clip: text;
          color: transparent;
        }

        .hero-left h2 {
          margin-top: 8px;
          color: #8fa0b6;
        }

        .hero-description {
          max-width: 620px;
          margin: 35px 0 0;
          color: #7f8da1;
          font-size: 14px;
          line-height: 1.85;
        }

        .hero-proof {
          display: flex;
          gap: 30px;
          margin-top: 40px;
        }

        .hero-proof div {
          display: flex;
          flex-direction: column;
          gap: 5px;
        }

        .hero-proof strong {
          color: #00d9ff;
          font-size: 10px;
          letter-spacing: 0.15em;
        }

        .hero-proof span {
          color: #596678;
          font-size: 8px;
          font-weight: 900;
          letter-spacing: 0.16em;
        }

        .hero-right {
          position: relative;
          min-height: 690px;
          display: flex;
          align-items: center;
          justify-content: center;
        }

        .core-orbit {
          position: absolute;
          width: 620px;
          height: 620px;
          left: 50%;
          top: 50%;
          transform: translate(-50%, -53%);
          pointer-events: none;
        }

        .orbit {
          position: absolute;
          inset: 50%;
          border: 1px solid
            rgba(0, 218, 255, 0.13);
          border-radius: 50%;
          transform: translate(-50%, -50%);
        }

        .orbit-one {
          width: 330px;
          height: 330px;
          animation: rotate 22s linear infinite;
        }

        .orbit-two {
          width: 470px;
          height: 470px;
          border-style: dashed;
          animation: rotateReverse 34s linear infinite;
        }

        .orbit-three {
          width: 600px;
          height: 600px;
          opacity: 0.45;
          animation: rotate 50s linear infinite;
        }

        .core-glow {
          position: absolute;
          width: 190px;
          height: 190px;
          left: 50%;
          top: 43%;
          transform: translate(-50%, -50%);
          border-radius: 50%;
          background: radial-gradient(
            circle,
            rgba(0, 224, 255, 0.24),
            rgba(0, 140, 255, 0.08) 45%,
            transparent 70%
          );
          filter: blur(3px);
          animation: corePulse 4s ease-in-out infinite;
        }

        .core-inner {
          position: absolute;
          width: 90px;
          height: 90px;
          left: 50%;
          top: 50%;
          transform: translate(-50%, -50%);
          border-radius: 50%;
          display: grid;
          place-items: center;
          border: 1px solid
            rgba(0, 224, 255, 0.65);
          background:
            radial-gradient(
              circle at 35% 30%,
              #eaffff,
              #72dfff 20%,
              #172a40 75%
            );
          box-shadow:
            0 0 35px rgba(0, 214, 255, 0.45),
            inset 0 0 25px
              rgba(255, 255, 255, 0.2);
        }

        .core-inner span {
          color: #021018;
          font-size: 33px;
          font-weight: 950;
        }

        .orbit-node {
          position: absolute;
          width: 7px;
          height: 7px;
          border-radius: 50%;
          background: #00dcff;
          box-shadow: 0 0 16px #00dcff;
        }

        .node-one {
          top: 23%;
          left: 23%;
        }

        .node-two {
          right: 15%;
          top: 47%;
        }

        .node-three {
          left: 31%;
          bottom: 9%;
        }

        .idea-card {
          position: relative;
          z-index: 4;
          width: min(570px, 90%);
          margin-top: 100px;
          padding: 25px;
          border: 1px solid
            rgba(0, 215, 255, 0.24);
          border-radius: 20px;
          background:
            linear-gradient(
              145deg,
              rgba(13, 19, 29, 0.92),
              rgba(5, 9, 15, 0.82)
            );
          backdrop-filter: blur(24px);
          box-shadow:
            0 30px 100px
              rgba(0, 0, 0, 0.55),
            0 0 80px
              rgba(0, 193, 255, 0.06);
        }

        .card-top {
          display: flex;
          justify-content: space-between;
          gap: 15px;
          margin-bottom: 17px;
        }

        .card-label,
        .panel-label {
          color: #00d8ff;
          font-size: 8px;
          font-weight: 900;
          letter-spacing: 0.18em;
        }

        .card-label {
          margin-bottom: 7px;
        }

        .card-title {
          color: #dce8f5;
          font-size: 17px;
          font-weight: 800;
        }

        .input-counter {
          color: #56667a;
          font-size: 9px;
          padding-top: 3px;
        }

        .idea-card textarea {
          width: 100%;
          min-height: 165px;
          resize: vertical;
          outline: none;
          border-radius: 13px;
          border: 1px solid
            rgba(255, 255, 255, 0.08);
          background: rgba(1, 5, 10, 0.65);
          color: #eaf8ff;
          padding: 18px;
          font-size: 14px;
          line-height: 1.65;
        }

        .idea-card textarea:focus {
          border-color: rgba(
            0,
            216,
            255,
            0.4
          );
          box-shadow:
            0 0 25px
              rgba(0, 216, 255, 0.06);
        }

        .idea-card textarea::placeholder {
          color: #4d5b6e;
        }

        .quick-examples {
          display: flex;
          flex-wrap: wrap;
          align-items: center;
          gap: 7px;
          margin: 12px 0 18px;
        }

        .quick-examples span {
          color: #4e5b6c;
          font-size: 8px;
          font-weight: 900;
          letter-spacing: 0.1em;
        }

        .quick-examples button {
          border: 1px solid
            rgba(255, 255, 255, 0.07);
          border-radius: 20px;
          background: rgba(
            255,
            255,
            255,
            0.025
          );
          color: #78879a;
          padding: 6px 9px;
          font-size: 8px;
          transition: 0.2s ease;
        }

        .quick-examples button:hover {
          color: #bcefff;
          border-color: rgba(
            0,
            216,
            255,
            0.25
          );
          transform: translateY(-1px);
        }

        .input-bottom {
          display: grid;
          grid-template-columns: 1fr auto;
          gap: 10px;
        }

        .input-bottom input {
          min-width: 0;
          border: 1px solid
            rgba(255, 255, 255, 0.08);
          border-radius: 11px;
          outline: none;
          background: rgba(
            255,
            255,
            255,
            0.025
          );
          color: #dce9f7;
          padding: 14px;
          font-size: 12px;
        }

        .run-button {
          min-width: 155px;
          border: 0;
          border-radius: 11px;
          padding: 0 20px;
          display: flex;
          align-items: center;
          justify-content: center;
          gap: 14px;
          color: white;
          font-size: 9px;
          font-weight: 950;
          letter-spacing: 0.12em;
          background: linear-gradient(
            100deg,
            #00c9ef,
            #6672ff
          );
          box-shadow:
            0 10px 35px
              rgba(0, 170, 255, 0.17);
          transition: 0.25s ease;
        }

        .run-button:hover:not(:disabled) {
          transform: translateY(-2px);
          box-shadow:
            0 14px 40px
              rgba(0, 170, 255, 0.3);
        }

        .run-button:disabled {
          cursor: not-allowed;
          opacity: 0.45;
        }

        .run-button b {
          font-size: 17px;
        }

        .error-box,
        .offline-note {
          margin-top: 12px;
          padding: 10px 12px;
          border-radius: 9px;
          font-size: 10px;
          line-height: 1.5;
        }

        .error-box {
          color: #ffabb4;
          background: rgba(
            255,
            60,
            90,
            0.08
          );
          border: 1px solid
            rgba(255, 60, 90, 0.15);
        }

        .offline-note {
          color: #8997aa;
          background: rgba(
            255,
            255,
            255,
            0.03
          );
        }

        .autonomous-note {
          position: absolute;
          bottom: 22px;
          left: 50%;
          transform: translateX(-50%);
          display: flex;
          align-items: center;
          gap: 9px;
          color: #536174;
          white-space: nowrap;
          font-size: 7px;
          font-weight: 900;
          letter-spacing: 0.17em;
        }

        .autonomous-note .pulse {
          width: 5px;
          height: 5px;
          border-radius: 50%;
          background: #00e4ff;
          box-shadow: 0 0 10px #00e4ff;
          animation: pulse 1.8s ease-in-out infinite;
        }

        .autonomous-note .line {
          width: 32px;
          height: 1px;
          background: #253447;
        }

        .footer {
          position: fixed;
          z-index: 25;
          bottom: 0;
          left: 0;
          right: 0;
          height: 30px;
          padding: 0 25px;
          display: flex;
          align-items: center;
          justify-content: space-between;
          border-top: 1px solid
            rgba(255, 255, 255, 0.045);
          background: rgba(3, 5, 9, 0.82);
          color: #364253;
          font-size: 7px;
          font-weight: 800;
          letter-spacing: 0.15em;
        }

        .footer span:first-child {
          color: #00cfee;
        }

        .workspace {
          position: relative;
          z-index: 3;
          min-height: calc(100vh - 114px);
          display: grid;
          grid-template-columns: 250px 1fr;
        }

        .sidebar {
          border-right: 1px solid
            rgba(255, 255, 255, 0.065);
          background: rgba(
            3,
            6,
            11,
            0.78
          );
          padding: 26px 15px 50px;
          overflow-y: auto;
        }

        .sidebar-heading,
        .sidebar-label {
          color: #445266;
          font-size: 8px;
          font-weight: 900;
          letter-spacing: 0.2em;
        }

        .sidebar-heading {
          padding: 0 10px;
          margin-bottom: 15px;
        }

        .project-mini {
          display: flex;
          align-items: center;
          gap: 10px;
          padding: 11px;
          border-radius: 11px;
          background: rgba(
            255,
            255,
            255,
            0.025
          );
          border: 1px solid
            rgba(255, 255, 255, 0.06);
        }

        .project-icon {
          width: 34px;
          height: 34px;
          display: grid;
          place-items: center;
          border-radius: 9px;
          background: linear-gradient(
            135deg,
            #00cfff,
            #5666ff
          );
          color: white;
          font-weight: 950;
        }

        .project-mini strong {
          display: block;
          max-width: 150px;
          overflow: hidden;
          white-space: nowrap;
          text-overflow: ellipsis;
          color: #dce7f4;
          font-size: 10px;
        }

        .project-mini span {
          display: block;
          margin-top: 3px;
          color: #00d8ff;
          font-size: 7px;
          text-transform: uppercase;
          letter-spacing: 0.12em;
        }

        .truth-status-grid { display:grid; grid-template-columns:1fr 1fr; gap:5px; margin-top:10px; }
        .truth-status-grid > div { padding:7px 8px; border:1px solid rgba(119,224,255,.08); border-radius:8px; background:rgba(119,224,255,.025); }
        .truth-status-grid b, .truth-status-grid span { display:block; }
        .truth-status-grid b { color:#68798c; font-size:6px; letter-spacing:.12em; }
        .truth-status-grid span { color:#b7d8e7; font-size:6.5px; margin-top:3px; line-height:1.35; }
        .scientific-truth-strip { display:flex; gap:8px; align-items:center; margin-top:8px; padding:8px; border:1px solid rgba(255,185,80,.14); border-radius:9px; background:rgba(255,185,80,.035); }
        .scientific-truth-strip > span { font-size:12px; }
        .scientific-truth-strip b, .scientific-truth-strip small { display:block; }
        .scientific-truth-strip b { color:#ffd38a; font-size:6.5px; letter-spacing:.1em; }
        .scientific-truth-strip small { color:#8f7c62; font-size:5.5px; margin-top:2px; line-height:1.4; }

        .progress-box {
          margin: 18px 4px 24px;
          padding: 13px;
          border: 1px solid
            rgba(255, 255, 255, 0.05);
          border-radius: 11px;
          background: rgba(
            255,
            255,
            255,
            0.018
          );
        }

        .progress-header {
          display: flex;
          justify-content: space-between;
          color: #58677a;
          font-size: 8px;
          font-weight: 900;
          letter-spacing: 0.12em;
        }

        .progress-header strong {
          color: #9eeeff;
        }

        .progress-track {
          height: 3px;
          margin: 10px 0 8px;
          border-radius: 20px;
          background: #18212d;
          overflow: hidden;
        }

        .progress-fill {
          height: 100%;
          background: linear-gradient(
            90deg,
            #00d7ff,
            #6570ff
          );
          box-shadow:
            0 0 12px
              rgba(0, 216, 255, 0.45);
          transition: width 0.5s ease;
        }

        .progress-box small {
          color: #465467;
          font-size: 7px;
        }

        .sidebar-section {
          margin-top: 20px;
        }

        .sidebar-label {
          padding: 0 10px;
          margin-bottom: 8px;
        }

        .stage-nav {
          width: 100%;
          min-height: 38px;
          display: grid;
          grid-template-columns: 24px 20px 1fr 17px;
          align-items: center;
          border: 0;
          border-left: 2px solid transparent;
          border-radius: 7px;
          padding: 0 8px;
          background: transparent;
          color: #617084;
          text-align: left;
          transition:
            background 0.2s ease,
            color 0.2s ease,
            transform 0.2s ease;
        }

        .stage-nav:hover {
          color: #d9e7f5;
          background: rgba(
            255,
            255,
            255,
            0.025
          );
          transform: translateX(2px);
        }

        .stage-nav.active {
          color: #eaffff;
          border-left-color: #00d8ff;
          background: linear-gradient(
            90deg,
            rgba(0, 216, 255, 0.11),
            transparent
          );
        }

        .stage-number {
          font-size: 7px;
          color: #3e4b5d;
        }

        .stage-icon {
          color: #4e5e72;
          font-size: 10px;
        }

        .stage-nav.active .stage-icon {
          color: #00d8ff;
          text-shadow: 0 0 12px #00d8ff;
        }

        .stage-name {
          font-size: 8px;
          font-weight: 800;
          letter-spacing: 0.05em;
        }

        .stage-marker {
          text-align: right;
          font-size: 8px;
        }

        .stage-state-label { color:#53667a; font-size:5.5px; letter-spacing:.08em; text-align:right; min-width:38px; }
        .stage-nav.ready .stage-marker { color:#d7b56b; }
        .stage-nav.blocked .stage-marker { color:#ff8f8f; }
        .stage-nav.ready .stage-state-label { color:#c8a866; }
        .stage-nav.blocked .stage-state-label { color:#d88484; }

        .stage-nav.completed .stage-marker {
          color: #27e4ad;
        }

        .stage-nav.running .stage-marker {
          color: #00d8ff;
          text-shadow: 0 0 10px #00d8ff;
        }

        .system-section {
          border-top: 1px solid
            rgba(255, 255, 255, 0.05);
          padding-top: 20px;
        }

        .system-nav {
          width: 100%;
          border: 0;
          background: transparent;
          color: #667489;
          text-align: left;
          padding: 10px;
          border-radius: 7px;
          font-size: 9px;
          transition: 0.2s ease;
        }

        .system-nav:hover,
        .system-nav.active {
          color: #d7e8f7;
          background: rgba(
            255,
            255,
            255,
            0.025
          );
        }

        .workspace-main {
          min-width: 0;
          padding: 42px 48px 70px;
          overflow-y: auto;
        }

        .workspace-top {
          display: flex;
          justify-content: space-between;
          gap: 25px;
          align-items: flex-start;
        }

        .workspace-eyebrow {
          color: #00d8ff;
          font-size: 8px;
          font-weight: 900;
          letter-spacing: 0.2em;
          margin-bottom: 10px;
        }

        .workspace-top h1 {
          margin: 0;
          font-size: clamp(
            28px,
            4vw,
            48px
          );
          line-height: 1;
          letter-spacing: -0.04em;
        }

        .workspace-top p {
          max-width: 850px;
          margin: 13px 0 0;
          color: #718095;
          line-height: 1.6;
          font-size: 12px;
        }

        .pipeline-strip {
          display: flex;
          gap: 5px;
          margin-top: 34px;
          padding: 8px;
          border: 1px solid
            rgba(255, 255, 255, 0.06);
          border-radius: 12px;
          background: rgba(
            255,
            255,
            255,
            0.018
          );
          overflow-x: auto;
        }

        .pipeline-stage {
          flex: 1 0 90px;
          border: 1px solid transparent;
          border-radius: 7px;
          background: transparent;
          padding: 10px 8px;
          text-align: left;
          color: #526073;
          transition: 0.2s ease;
        }

        .pipeline-stage:hover {
          background: rgba(
            255,
            255,
            255,
            0.025
          );
        }

        .pipeline-stage span {
          display: block;
          font-size: 7px;
          margin-bottom: 5px;
        }

        .pipeline-stage b {
          display: block;
          font-size: 7px;
          white-space: nowrap;
          letter-spacing: 0.05em;
        }

        .pipeline-stage.completed {
          color: #27dba8;
        }

        .pipeline-stage.active {
          color: #dffbff;
          border-color: rgba(
            0,
            216,
            255,
            0.24
          );
          background: rgba(
            0,
            216,
            255,
            0.07
          );
        }

        .pipeline-stage.active span {
          color: #00d8ff;
        }

        .stage-panel {
          margin-top: 25px;
          display: grid;
          grid-template-columns:
            minmax(0, 1.55fr)
            minmax(250px, 0.45fr);
          gap: 18px;
          animation: panelIn 0.45s ease both;
        }

        .main-panel,
        .side-panel,
        .generic-panel {
          border: 1px solid
            rgba(255, 255, 255, 0.065);
          border-radius: 17px;
          background:
            linear-gradient(
              145deg,
              rgba(10, 16, 25, 0.88),
              rgba(5, 9, 15, 0.75)
            );
          box-shadow:
            0 20px 70px
              rgba(0, 0, 0, 0.2);
          backdrop-filter: blur(18px);
        }

        .main-panel {
          min-height: 520px;
          padding: 28px;
        }

        .side-panel {
          padding: 20px;
          align-self: start;
        }

        .main-panel h2,
        .generic-panel h2 {
          margin: 10px 0 8px;
          font-size: 30px;
          letter-spacing: -0.035em;
        }

        .stage-description {
          max-width: 850px;
          color: #718095;
          font-size: 12px;
          line-height: 1.7;
          margin-bottom: 22px;
        }

        .idea-context {
          padding: 15px;
          border-radius: 12px;
          border: 1px solid
            rgba(0, 216, 255, 0.08);
          background:
            linear-gradient(
              120deg,
              rgba(0, 216, 255, 0.035),
              rgba(255, 255, 255, 0.015)
            );
          color: #b8c6d7;
          font-size: 12px;
          line-height: 1.65;
        }

        .idea-context strong {
          color: #00d8ff;
          font-size: 8px;
          letter-spacing: 0.13em;
        }

        .insight-header {
          display: flex;
          align-items: flex-end;
          justify-content: space-between;
          gap: 15px;
          margin-top: 28px;
          margin-bottom: 14px;
        }

        .insight-header > div:first-child {
          display: flex;
          flex-direction: column;
          gap: 5px;
        }

        .intelligence-badge {
          display: inline-flex;
          align-items: center;
          gap: 7px;
          padding: 7px 9px;
          border: 1px solid rgba(118, 94, 255, 0.18);
          border-radius: 999px;
          background: rgba(118, 94, 255, 0.05);
          color: #9184ff;
          font-size: 7px;
          font-weight: 900;
          letter-spacing: 0.12em;
          white-space: nowrap;
        }

        .intelligence-badge i {
          width: 5px;
          height: 5px;
          border-radius: 50%;
          background: #9184ff;
          box-shadow: 0 0 10px #9184ff;
        }

        .understand-banner {
          position: relative;
          display: flex;
          align-items: flex-start;
          gap: 14px;
          margin-bottom: 12px;
          padding: 14px 15px;
          border: 1px solid rgba(0, 216, 255, 0.11);
          border-radius: 13px;
          background:
            radial-gradient(
              circle at 0% 50%,
              rgba(0, 216, 255, 0.08),
              transparent 38%
            ),
            rgba(0, 216, 255, 0.018);
          overflow: hidden;
        }

        .understand-banner::after {
          content: "";
          position: absolute;
          top: 0;
          left: -30%;
          width: 30%;
          height: 1px;
          background: linear-gradient(
            90deg,
            transparent,
            #00d8ff,
            transparent
          );
          animation: intelligenceSweep 4.5s ease-in-out infinite;
        }

        .understand-banner-mark {
          flex: 0 0 auto;
          width: 34px;
          height: 34px;
          display: grid;
          place-items: center;
          border-radius: 10px;
          border: 1px solid rgba(0, 216, 255, 0.22);
          background: radial-gradient(
            circle at 35% 30%,
            #eaffff,
            #63ddff 22%,
            #12253a 78%
          );
          color: #041017;
          font-size: 13px;
          font-weight: 950;
          box-shadow: 0 0 24px rgba(0, 216, 255, 0.14);
        }

        .understand-banner strong {
          display: block;
          color: #d9f7ff;
          font-size: 11px;
          line-height: 1.4;
        }

        .understand-banner p {
          margin: 4px 0 0;
          color: #6e7e92;
          font-size: 9px;
          line-height: 1.65;
        }

        .understand-grid {
          grid-template-columns:
            repeat(
              2,
              minmax(0, 1fr)
            );
        }

        .understand-card {
          min-height: 108px;
        }

        .understand-card strong {
          font-size: 11px;
          line-height: 1.7;
        }

        .understand-card:first-child,
        .understand-card:nth-child(5) {
          min-height: 132px;
        }

        .understand-footnote {
          margin-top: 18px;
          padding: 13px 15px;
          border: 1px dashed rgba(255, 184, 76, 0.16);
          border-radius: 11px;
          background: rgba(255, 184, 76, 0.018);
        }

        .understand-footnote span {
          display: block;
          color: #c7964a;
          font-size: 7px;
          font-weight: 900;
          letter-spacing: 0.15em;
          margin-bottom: 5px;
        }

        .understand-footnote p {
          margin: 0;
          color: #68778a;
          font-size: 9px;
          line-height: 1.65;
        }

        @keyframes intelligenceSweep {
          0% {
            left: -30%;
            opacity: 0;
          }
          15% {
            opacity: 1;
          }
          65% {
            left: 100%;
            opacity: 1;
          }
          100% {
            left: 100%;
            opacity: 0;
          }
        }

        .insight-header span {
          color: #506074;
          font-size: 8px;
          font-weight: 900;
          letter-spacing: 0.16em;
        }

        .insight-header b {
          color: #dbeaf7;
          font-size: 12px;
        }

        .data-grid {
          display: grid;
          grid-template-columns:
            repeat(
              2,
              minmax(0, 1fr)
            );
          gap: 11px;
        }

        .data-card {
          position: relative;
          overflow: hidden;
          min-height: 125px;
          padding: 16px;
          border: 1px solid
            rgba(255, 255, 255, 0.055);
          border-radius: 12px;
          background: rgba(
            255,
            255,
            255,
            0.018
          );
          transition:
            transform 0.25s ease,
            border-color 0.25s ease,
            background 0.25s ease;
        }

        .data-card::after {
          content: "";
          position: absolute;
          width: 100px;
          height: 100px;
          right: -50px;
          bottom: -50px;
          border-radius: 50%;
          background: rgba(0, 216, 255, 0.08);
          filter: blur(25px);
        }

        .data-card:hover {
          transform: translateY(-3px);
          border-color: rgba(
            0,
            216,
            255,
            0.18
          );
          background: rgba(
            0,
            216,
            255,
            0.025
          );
        }

        .data-card span {
          display: block;
          color: #506074;
          font-size: 7px;
          font-weight: 900;
          letter-spacing: 0.12em;
          margin-bottom: 9px;
        }

        .data-card strong {
          display: block;
          position: relative;
          z-index: 2;
          color: #cbd8e7;
          font-size: 11px;
          line-height: 1.55;
          white-space: pre-wrap;
          word-break: break-word;
        }

        .data-card.tone-cyan {
          border-color: rgba(
            0,
            216,
            255,
            0.14
          );
        }

        .data-card.tone-cyan span {
          color: #00d8ff;
        }

        .data-card.tone-green {
          border-color: rgba(
            39,
            228,
            173,
            0.14
          );
        }

        .data-card.tone-green span {
          color: #27dba8;
        }

        .data-card.tone-violet {
          border-color: rgba(
            118,
            94,
            255,
            0.16
          );
        }

        .data-card.tone-violet span {
          color: #8c7bff;
        }

        .data-card.tone-amber {
          border-color: rgba(
            255,
            184,
            76,
            0.16
          );
        }

        .data-card.tone-amber span {
          color: #e4ae58;
        }

        .data-card.tone-blue {
          border-color: rgba(
            76,
            126,
            255,
            0.16
          );
        }

        .data-card.tone-blue span {
          color: #7397ff;
        }

        .section-grid {
          display: grid;
          grid-template-columns:
            repeat(
              2,
              minmax(0, 1fr)
            );
          gap: 12px;
          margin-top: 24px;
        }

        .clean-section {
          border: 1px solid
            rgba(255, 255, 255, 0.055);
          border-radius: 12px;
          padding: 16px;
          background: rgba(
            255,
            255,
            255,
            0.015
          );
          transition: 0.25s ease;
        }

        .clean-section:hover {
          border-color: rgba(
            0,
            216,
            255,
            0.13
          );
          transform: translateY(-2px);
        }

        .clean-section-title {
          color: #718096;
          font-size: 8px;
          font-weight: 900;
          letter-spacing: 0.14em;
          margin-bottom: 12px;
        }

        .clean-section-list {
          display: grid;
          gap: 8px;
        }

        .clean-section-item {
          display: flex;
          align-items: flex-start;
          gap: 9px;
          color: #9aa9bc;
          font-size: 10px;
          line-height: 1.6;
        }

        .clean-section-item::before {
          content: "";
          flex: 0 0 auto;
          width: 4px;
          height: 4px;
          margin-top: 6px;
          border-radius: 50%;
          background: #00d8ff;
          box-shadow: 0 0 8px
            rgba(0, 216, 255, 0.7);
        }

        .stage-message {
          margin-top: 22px;
          padding: 15px 17px;
          border-left: 2px solid #00d8ff;
          border-radius: 0 10px 10px 0;
          background: linear-gradient(
            90deg,
            rgba(0, 216, 255, 0.055),
            transparent
          );
          color: #77879b;
          font-size: 10px;
          line-height: 1.65;
        }

        .stage-list {
          display: flex;
          flex-direction: column;
          gap: 5px;
        }

        .stage-list-item {
          display: flex;
          align-items: center;
          gap: 10px;
          padding: 9px;
          border-radius: 8px;
          background: rgba(
            255,
            255,
            255,
            0.014
          );
        }

        .stage-list-item i {
          width: 6px;
          height: 6px;
          border-radius: 50%;
          background: #273444;
        }

        .stage-list-item.current {
          background: rgba(
            0,
            216,
            255,
            0.05
          );
        }

        .stage-list-item.current i {
          background: #00d8ff;
          box-shadow: 0 0 12px #00d8ff;
        }

        .stage-list-item.done i {
          background: #27dba8;
        }

        .stage-list-item span {
          color: #69788c;
          font-size: 8px;
          font-weight: 800;
        }

        .stage-list-item.current span {
          color: #c9f8ff;
        }

        .connected-count {
          margin-top: 18px;
          padding: 13px;
          border-radius: 10px;
          border: 1px solid
            rgba(255, 255, 255, 0.05);
          background: rgba(
            255,
            255,
            255,
            0.018
          );
        }

        .connected-count strong {
          display: block;
          color: #d9e9f7;
          font-size: 20px;
          letter-spacing: -0.04em;
        }

        .connected-count span {
          display: block;
          color: #4f6075;
          margin-top: 3px;
          font-size: 7px;
          letter-spacing: 0.12em;
          font-weight: 900;
        }

        .system-panel {
          margin-top: 18px;
          padding: 15px;
          border: 1px solid
            rgba(0, 216, 255, 0.1);
          border-radius: 10px;
          background: rgba(
            0,
            216,
            255,
            0.025
          );
        }

        .system-panel strong {
          display: block;
          color: #9eeeff;
          font-size: 8px;
          letter-spacing: 0.1em;
          margin-bottom: 7px;
        }

        .system-panel span {
          color: #61748a;
          font-size: 9px;
          line-height: 1.5;
        }

        .generic-panel {
          margin-top: 25px;
          padding: 28px;
          animation: panelIn 0.45s ease both;
        }

        .generic-panel > p {
          max-width: 900px;
          color: #748398;
          font-size: 12px;
          line-height: 1.7;
        }

        .trust-summary {
          display: grid;
          grid-template-columns:
            repeat(
              3,
              minmax(0, 1fr)
            );
          gap: 11px;
          margin-top: 24px;
        }

        .trust-card {
          padding: 16px;
          border-radius: 12px;
          border: 1px solid
            rgba(255, 255, 255, 0.055);
          background: rgba(
            255,
            255,
            255,
            0.018
          );
        }

        .trust-card span {
          display: block;
          color: #526176;
          font-size: 7px;
          font-weight: 900;
          letter-spacing: 0.13em;
          margin-bottom: 7px;
        }

        .trust-card strong {
          color: #dceaf7;
          font-size: 18px;
        }

        .evidence-list,
        .memory-list {
          display: flex;
          flex-direction: column;
          gap: 10px;
          margin-top: 20px;
        }

        .evidence-item,
        .memory-item {
          padding: 16px;
          border: 1px solid
            rgba(255, 255, 255, 0.055);
          border-radius: 11px;
          background: rgba(
            255,
            255,
            255,
            0.018
          );
          transition: 0.2s ease;
        }

        .evidence-item:hover,
        .memory-item:hover {
          border-color: rgba(
            0,
            216,
            255,
            0.13
          );
          transform: translateY(-1px);
        }

        .record-top {
          display: flex;
          justify-content: space-between;
          gap: 15px;
          align-items: flex-start;
        }

        .record-badge {
          flex: 0 0 auto;
          padding: 5px 7px;
          border-radius: 20px;
          background: rgba(
            0,
            216,
            255,
            0.07
          );
          color: #75eaff;
          font-size: 7px;
          font-weight: 900;
          letter-spacing: 0.1em;
        }

        .evidence-item strong,
        .memory-item strong {
          display: block;
          color: #c8d7e8;
          font-size: 11px;
          line-height: 1.5;
        }

        .evidence-item > span,
        .memory-item > span {
          display: block;
          color: #637388;
          margin-top: 7px;
          font-size: 9px;
          line-height: 1.6;
        }

        .record-source {
          color: #4c6077 !important;
          font-size: 8px !important;
          margin-top: 10px !important;
        }

        .record-detail {
          margin-top: 10px;
          padding: 10px 12px;
          border-radius: 8px;
          background: rgba(
            0,
            216,
            255,
            0.025
          );
          color: #718398;
          font-size: 9px;
          line-height: 1.6;
        }

        .empty-state {
          margin-top: 20px;
          padding: 25px;
          border: 1px dashed
            rgba(255, 255, 255, 0.08);
          border-radius: 12px;
          text-align: center;
          color: #5c6c80;
          font-size: 10px;
          line-height: 1.7;
        }

        .loading-overlay {
          position: fixed;
          inset: 0;
          z-index: 100;
          display: grid;
          place-items: center;
          background: rgba(
            2,
            5,
            9,
            0.82
          );
          backdrop-filter: blur(12px);
        }

        .loading-card {
          width: min(430px, 90vw);
          padding: 30px;
          border: 1px solid
            rgba(0, 216, 255, 0.2);
          border-radius: 20px;
          background:
            linear-gradient(
              145deg,
              rgba(12, 19, 30, 0.96),
              rgba(4, 8, 14, 0.96)
            );
          box-shadow:
            0 30px 100px
              rgba(0, 0, 0, 0.5),
            0 0 60px
              rgba(0, 216, 255, 0.08);
          text-align: center;
        }

        .loading-orb {
          width: 74px;
          height: 74px;
          margin: 0 auto 22px;
          border-radius: 50%;
          border: 1px solid
            rgba(0, 216, 255, 0.5);
          display: grid;
          place-items: center;
          box-shadow:
            0 0 35px
              rgba(0, 216, 255, 0.2);
          animation: loadingPulse 1.5s ease-in-out infinite;
        }

        .loading-orb span {
          color: #00d8ff;
          font-size: 24px;
          font-weight: 950;
        }

        .loading-card h3 {
          margin: 0;
          color: #e8f8ff;
          font-size: 18px;
        }

        .loading-card p {
          margin: 9px 0 0;
          color: #68798e;
          font-size: 10px;
          line-height: 1.6;
        }

        @keyframes rotate {
          from {
            transform:
              translate(-50%, -50%)
              rotate(0deg);
          }

          to {
            transform:
              translate(-50%, -50%)
              rotate(360deg);
          }
        }

        @keyframes rotateReverse {
          from {
            transform:
              translate(-50%, -50%)
              rotate(360deg);
          }

          to {
            transform:
              translate(-50%, -50%)
              rotate(0deg);
          }
        }

        @keyframes pulse {
          0%,
          100% {
            opacity: 0.45;
            transform: scale(0.8);
          }

          50% {
            opacity: 1;
            transform: scale(1.25);
          }
        }

        @keyframes corePulse {
          0%,
          100% {
            transform:
              translate(-50%, -50%)
              scale(0.9);
            opacity: 0.75;
          }

          50% {
            transform:
              translate(-50%, -50%)
              scale(1.08);
            opacity: 1;
          }
        }

        @keyframes loadingPulse {
          0%,
          100% {
            transform: scale(0.92);
            box-shadow:
              0 0 25px
                rgba(0, 216, 255, 0.12);
          }

          50% {
            transform: scale(1.06);
            box-shadow:
              0 0 45px
                rgba(0, 216, 255, 0.28);
          }
        }

        @keyframes ambientFloat {
          0%,
          100% {
            transform: translate3d(0, 0, 0);
          }

          50% {
            transform: translate3d(25px, -20px, 0);
          }
        }

        @keyframes panelIn {
          from {
            opacity: 0;
            transform: translateY(10px);
          }

          to {
            opacity: 1;
            transform: translateY(0);
          }
        }

        @media (max-width: 900px) { .aura20-status-flow { grid-template-columns:repeat(2,minmax(0,1fr)); } .aura20-truth-heading { align-items:flex-start; flex-direction:column; } .aura20-blueprint-meta { grid-template-columns:1fr; } }

        @media (prefers-reduced-motion: reduce) {
          *,
          *::before,
          *::after {
            animation-duration: 0.01ms !important;
            animation-iteration-count: 1 !important;
            scroll-behavior: auto !important;
            transition-duration: 0.01ms !important;
          }
        }

        @media (max-width: 1100px) {
          .landing {
            grid-template-columns: 1fr;
            padding-top: 45px;
          }

          .hero-left {
            padding-left: 0;
            max-width: 850px;
          }

          .hero-right {
            min-height: 650px;
          }

          .stage-panel {
            grid-template-columns: 1fr;
          }
        }

        @media (max-width: 760px) {
          .topbar {
            height: 72px;
            padding: 0 18px;
          }

          .brand-subtitle,
          .system-status {
            display: none;
          }

          .new-project-button {
            padding: 8px 10px;
          }

          .landing {
            padding: 45px 18px 70px;
            min-height: auto;
          }

          .hero-left h1,
          .hero-left h2 {
            font-size: clamp(
              54px,
              16vw,
              85px
            );
          }

          .hero-description {
            font-size: 12px;
          }

          .hero-proof {
            gap: 17px;
            flex-wrap: wrap;
          }

          .hero-right {
            min-height: 570px;
          }

          .core-orbit {
            width: 430px;
            height: 430px;
          }

          .orbit-one {
            width: 250px;
            height: 250px;
          }

          .orbit-two {
            width: 350px;
            height: 350px;
          }

          .orbit-three {
            width: 425px;
            height: 425px;
          }

          .idea-card {
            width: 100%;
            margin-top: 75px;
            padding: 18px;
          }

          .idea-card textarea {
            min-height: 150px;
          }

          .input-bottom {
            grid-template-columns: 1fr;
          }

          .run-button {
            min-height: 48px;
          }

          .autonomous-note {
            font-size: 6px;
          }

          .footer {
            display: none;
          }

          .workspace {
            grid-template-columns: 1fr;
          }

          .sidebar {
            position: relative;
            border-right: 0;
            border-bottom: 1px solid
              rgba(255, 255, 255, 0.06);
            padding: 15px;
          }

          .sidebar-section {
            overflow-x: auto;
          }

          .sidebar-section:not(
              .system-section
            ) {
            display: flex;
            gap: 5px;
          }

          .stage-nav {
            min-width: 145px;
          }

          .system-section {
            display: flex;
            gap: 5px;
          }

          .workspace-main {
            padding: 25px 15px 60px;
          }

          .workspace-top {
            flex-direction: column;
          }

          .pipeline-strip {
            margin-top: 20px;
          }

          .data-grid,
          .section-grid,
          .trust-summary,
          .understand-grid {
            grid-template-columns: 1fr;
          }

          .insight-header {
            align-items: flex-start;
            flex-direction: column;
          }

          .intelligence-badge {
            align-self: flex-start;
          }

          .understand-banner {
            padding: 13px;
          }

          .main-panel {
            padding: 20px;
          }

          .generic-panel {
            padding: 20px;
          }

          .main-panel h2,
          .generic-panel h2 {
            font-size: 25px;
          }

          .record-top {
            flex-direction: column;
          }
        }

/* =========================================================
   AURA COMMAND CENTER — FINAL INTELLIGENCE LAYER
   ========================================================= */
.aura-command-insights {
  position: relative;
  margin: 24px 0 28px;
  padding: 22px;
  border: 1px solid rgba(119, 224, 255, .18);
  border-radius: 22px;
  background:
    linear-gradient(145deg, rgba(9, 21, 31, .96), rgba(7, 13, 22, .92)),
    radial-gradient(circle at 85% 10%, rgba(79, 221, 255, .12), transparent 35%);
  box-shadow: 0 20px 70px rgba(0,0,0,.28), inset 0 1px 0 rgba(255,255,255,.04);
  overflow: hidden;
}
.aura-command-insights::before {
  content: "";
  position: absolute;
  inset: 0;
  pointer-events: none;
  background: linear-gradient(90deg, transparent, rgba(120,220,255,.035), transparent);
  transform: translateX(-100%);
  animation: auraCommandSweep 7s linear infinite;
}
@keyframes auraCommandSweep { to { transform: translateX(100%); } }
.aci-head, .aci-verdict-grid, .aci-flow-row, .aci-delivery { position: relative; z-index: 1; }
.aci-head { display:flex; justify-content:space-between; gap:18px; align-items:flex-start; }
.aci-kicker, .aci-section-title { display:block; font-size:10px; letter-spacing:.2em; font-weight:800; opacity:.58; }
.aci-head h3 { margin:7px 0 5px; font-size:20px; letter-spacing:-.02em; }
.aci-head p { margin:0; max-width:760px; color:rgba(232,245,250,.62); line-height:1.55; font-size:13px; }
.aci-state { white-space:nowrap; display:flex; align-items:center; gap:8px; padding:8px 11px; border:1px solid rgba(118,227,255,.18); border-radius:999px; font-size:9px; letter-spacing:.14em; font-weight:800; color:rgba(210,245,255,.78); }
.aci-state i { width:7px; height:7px; border-radius:50%; background:#75f0bd; box-shadow:0 0 14px rgba(117,240,189,.7); }
.aci-metrics { position:relative; z-index:1; display:grid; grid-template-columns:repeat(5,1fr); gap:9px; margin-top:18px; }
.aci-metric { padding:13px 14px; border:1px solid rgba(255,255,255,.07); border-radius:14px; background:rgba(255,255,255,.025); }
.aci-metric span { display:block; font-size:9px; letter-spacing:.14em; opacity:.5; }
.aci-metric strong { display:block; margin-top:5px; font-size:22px; letter-spacing:-.04em; }
.aci-verdict, .aci-research, .aci-flow, .aci-truth, .aci-delivery { position:relative; z-index:1; margin-top:18px; padding-top:18px; border-top:1px solid rgba(255,255,255,.07); }
.aci-verdict-grid { display:grid; grid-template-columns:1fr 190px; gap:18px; margin-top:14px; }
.aci-score-list { display:grid; gap:10px; }
.aci-score > div:first-child { display:flex; justify-content:space-between; gap:12px; font-size:11px; }
.aci-score b { font-size:11px; opacity:.82; }
.aci-track { height:6px; margin-top:6px; border-radius:99px; background:rgba(255,255,255,.07); overflow:hidden; }
.aci-track i { display:block; height:100%; border-radius:inherit; background:linear-gradient(90deg, rgba(96,218,255,.45), rgba(126,244,198,.9)); box-shadow:0 0 16px rgba(88,216,255,.2); }
.aci-verdict-core { min-height:150px; display:flex; flex-direction:column; justify-content:center; align-items:center; border:1px solid rgba(112,229,255,.16); border-radius:18px; background:radial-gradient(circle, rgba(70,206,255,.11), transparent 68%); text-align:center; }
.aci-verdict-core span { font-size:9px; letter-spacing:.18em; opacity:.55; }
.aci-verdict-core strong { font-size:52px; line-height:1; margin:7px 0; }
.aci-verdict-core small { opacity:.48; font-size:9px; }
.aci-source-bars { display:grid; grid-template-columns:repeat(2,1fr); gap:12px 20px; margin-top:14px; }
.aci-source div:first-child { display:flex; justify-content:space-between; font-size:11px; }
.aci-source b { opacity:.7; }
.aci-note { margin-top:13px; font-size:10px; line-height:1.5; opacity:.45; }
.aci-flow-row { display:grid; grid-template-columns:repeat(4,1fr); gap:10px; margin-top:14px; }
.aci-flow-node { position:relative; min-height:105px; padding:13px; border:1px solid rgba(255,255,255,.07); border-radius:15px; background:rgba(255,255,255,.025); }
.aci-flow-node span { display:block; font-size:9px; opacity:.4; }
.aci-flow-node b { display:block; margin-top:9px; font-size:9px; letter-spacing:.12em; opacity:.62; }
.aci-flow-node strong { display:block; margin-top:7px; font-size:17px; }
.aci-flow-node i { position:absolute; right:-8px; top:50%; transform:translateY(-50%); font-style:normal; opacity:.45; }
.aci-truth { display:flex; gap:13px; align-items:flex-start; padding:14px 15px; border:1px solid rgba(255,190,90,.2); border-radius:15px; background:rgba(255,174,64,.045); }
.aci-truth.truth-executed { border-color:rgba(117,240,189,.2); background:rgba(117,240,189,.045); }
.aci-truth-icon { width:28px; height:28px; flex:0 0 28px; display:grid; place-items:center; border-radius:50%; background:rgba(255,190,90,.12); font-weight:900; }
.truth-executed .aci-truth-icon { background:rgba(117,240,189,.12); }
.aci-truth strong { display:block; font-size:10px; letter-spacing:.12em; }
.aci-truth p { margin:5px 0 0; font-size:11px; line-height:1.5; opacity:.58; }
.aci-delivery { display:flex; justify-content:space-between; gap:20px; align-items:center; }
.aci-delivery h4 { margin:6px 0 4px; font-size:17px; }
.aci-delivery p { margin:0; max-width:700px; font-size:11px; line-height:1.55; opacity:.55; }
.aci-delivery-stats { display:flex; gap:8px; }
.aci-delivery-stats div { min-width:86px; padding:11px; border:1px solid rgba(255,255,255,.07); border-radius:13px; text-align:center; }
.aci-delivery-stats b { display:block; font-size:19px; }
.aci-delivery-stats span { display:block; margin-top:4px; font-size:7px; letter-spacing:.12em; opacity:.5; }
@media (max-width: 900px) {
  .aci-metrics { grid-template-columns:repeat(3,1fr); }
  .aci-verdict-grid { grid-template-columns:1fr; }
  .aci-flow-row { grid-template-columns:repeat(2,1fr); }
  .aci-delivery { flex-direction:column; align-items:flex-start; }
}
@media (max-width: 600px) {
  .aura-command-insights { padding:16px; border-radius:17px; }
  .aci-head { flex-direction:column; }
  .aci-state { align-self:flex-start; }
  .aci-metrics { grid-template-columns:repeat(2,1fr); }
  .aci-source-bars { grid-template-columns:1fr; }
  .aci-flow-row { grid-template-columns:1fr; }
  .aci-flow-node i { display:none; }
  .aci-delivery-stats { width:100%; }
  .aci-delivery-stats div { flex:1; min-width:0; }
}
@media (prefers-reduced-motion: reduce) {
  .aura-command-insights::before { animation:none; }
}

.neural-pipeline{position:relative;margin:0 0 22px;padding:18px 20px 20px;border:1px solid rgba(119,224,255,.16);border-radius:20px;background:linear-gradient(135deg,rgba(7,18,31,.94),rgba(10,15,30,.82));box-shadow:inset 0 1px rgba(255,255,255,.04),0 18px 55px rgba(0,0,0,.22);overflow:hidden}
.neural-pipeline:before{content:"";position:absolute;inset:0;background-image:linear-gradient(rgba(119,224,255,.035) 1px,transparent 1px),linear-gradient(90deg,rgba(119,224,255,.035) 1px,transparent 1px);background-size:28px 28px;mask-image:linear-gradient(90deg,transparent,#000 18%,#000 82%,transparent)}
.np-header{position:relative;z-index:2;display:flex;align-items:center;justify-content:space-between;gap:16px;margin-bottom:18px}.np-kicker{font-size:11px;letter-spacing:.18em;font-weight:800;color:#77e0ff}.np-caption{margin-left:12px;font-size:12px;color:rgba(220,240,255,.48)}.np-live{font-size:10px;letter-spacing:.13em;color:#9dffcb;display:flex;align-items:center;gap:7px}.np-live-dot{width:7px;height:7px;border-radius:50%;background:#8dffc0;box-shadow:0 0 12px #8dffc0;animation:npPulse 1.4s infinite}
.np-track{position:relative;z-index:2;display:grid;grid-template-columns:repeat(11,1fr);align-items:start;min-width:900px}.np-node{appearance:none;font:inherit;text-align:left;cursor:pointer;position:relative;text-align:center;cursor:pointer;transition:transform .25s ease}.np-node:hover{transform:translateY(-3px)}.np-orb{margin:auto;width:40px;height:40px;border:1px solid rgba(119,224,255,.22);border-radius:50%;display:grid;place-items:center;background:rgba(8,25,40,.9);box-shadow:0 0 0 5px rgba(119,224,255,.025),inset 0 0 18px rgba(119,224,255,.06)}.np-orb span{font-size:10px;color:rgba(220,240,255,.48);font-weight:800}.np-label{margin-top:9px;font-size:8px;letter-spacing:.08em;color:rgba(220,240,255,.4);white-space:nowrap}.np-link{position:absolute;left:50%;top:20px;width:100%;height:1px;background:linear-gradient(90deg,rgba(119,224,255,.16),rgba(119,224,255,.05));z-index:-1}.np-link i{display:block;width:22%;height:2px;background:#77e0ff;box-shadow:0 0 10px #77e0ff;animation:npFlow 2.2s linear infinite}.np-node.done .np-orb{border-color:rgba(141,255,192,.55);box-shadow:0 0 18px rgba(141,255,192,.12),inset 0 0 18px rgba(141,255,192,.08)}.np-node.done .np-orb span{color:#9dffcb}.np-node.active .np-orb{border-color:#77e0ff;box-shadow:0 0 0 7px rgba(119,224,255,.055),0 0 30px rgba(119,224,255,.24),inset 0 0 22px rgba(119,224,255,.13);animation:npCore 1.8s ease-in-out infinite}.np-node.active .np-orb span,.np-node.active .np-label{color:#77e0ff}.np-node.active .np-label{font-weight:800}.np-node.active:after{content:"";position:absolute;left:50%;top:-5px;width:52px;height:52px;transform:translateX(-50%);border:1px solid rgba(119,224,255,.18);border-radius:50%;animation:npSpin 6s linear infinite}
@keyframes npPulse{50%{opacity:.35;transform:scale(.72)}}@keyframes npCore{50%{transform:scale(1.08)}}@keyframes npFlow{from{transform:translateX(-130%)}to{transform:translateX(500%)}}@keyframes npSpin{to{transform:translateX(-50%) rotate(360deg)}}
@media(max-width:900px){.np-caption{display:none}.np-track{overflow-x:auto;display:flex;gap:38px;padding:4px 8px 10px}.np-node{min-width:72px}.np-link{width:38px;left:calc(50% + 20px)}}
@media(prefers-reduced-motion:reduce){.np-live-dot,.np-link i,.np-node.active .np-orb,.np-node.active:after{animation:none}}


        /* FINAL DELIVERY + SCROLL EXPERIENCE */
        .bec-notice{margin:10px 0;padding:12px 14px;border:1px solid rgba(0,216,255,.22);background:rgba(0,216,255,.06);border-radius:12px;color:#bdefff;font-size:12px;letter-spacing:.04em}
        .bec-workspace-modal{position:fixed;inset:0;z-index:1000;background:rgba(3,7,18,.82);backdrop-filter:blur(14px);display:flex;align-items:center;justify-content:center;padding:24px}
        .bec-workspace-modal-inner{width:min(1100px,96vw);height:min(760px,90vh);background:linear-gradient(145deg,rgba(10,18,35,.98),rgba(7,12,25,.98));border:1px solid rgba(0,216,255,.25);border-radius:20px;box-shadow:0 30px 100px rgba(0,0,0,.55);overflow:hidden}
        .bec-workspace-modal-head{display:flex;align-items:center;justify-content:space-between;padding:18px 20px;border-bottom:1px solid rgba(255,255,255,.08)}
        .bec-workspace-modal-head h4{margin:6px 0 0;font-size:14px;word-break:break-all;color:#eafaff}
        .bec-workspace-modal-head button{border:1px solid rgba(255,255,255,.12);background:rgba(255,255,255,.04);color:#d8efff;border-radius:10px;padding:9px 13px;cursor:pointer}
        .bec-workspace-browser{display:grid;grid-template-columns:280px 1fr;height:calc(100% - 82px)}
        .bec-file-list{overflow:auto;border-right:1px solid rgba(255,255,255,.08);padding:10px}
        .bec-file-list button{display:block;width:100%;text-align:left;border:0;background:transparent;color:#9db4c8;padding:9px 10px;border-radius:8px;cursor:pointer;font:inherit;font-size:12px;word-break:break-all}
        .bec-file-list button:hover,.bec-file-list button.active{background:rgba(0,216,255,.09);color:#dff9ff}
        .bec-file-content{margin:0;overflow:auto;padding:20px;color:#c8d8e7;font:12px/1.65 ui-monospace,SFMono-Regular,Menlo,monospace;white-space:pre-wrap}
        @media (max-width:760px){.bec-workspace-browser{grid-template-columns:1fr}.bec-file-list{max-height:220px;border-right:0;border-bottom:1px solid rgba(255,255,255,.08)}.bec-workspace-modal{padding:10px}.bec-workspace-modal-inner{height:94vh}}
        .workspace-main { scroll-behavior:smooth; scrollbar-width:thin; scrollbar-color:rgba(0,216,255,.22) transparent; }
        .workspace-main::-webkit-scrollbar{width:7px}.workspace-main::-webkit-scrollbar-track{background:transparent}.workspace-main::-webkit-scrollbar-thumb{background:linear-gradient(to bottom,rgba(0,216,255,.42),rgba(104,92,255,.34));border-radius:999px}
        .stage-panel{align-items:start}.main-panel{overflow:clip}.side-panel{position:sticky;top:24px}
        .clean-section,.data-card,.aura-command-insights{content-visibility:auto;contain-intrinsic-size:180px}
        .delivery-studio{position:relative;margin-top:26px;padding:24px;border:1px solid rgba(0,216,255,.14);border-radius:20px;background:radial-gradient(circle at 88% 8%,rgba(104,92,255,.11),transparent 28%),linear-gradient(145deg,rgba(9,17,28,.94),rgba(3,8,14,.9));box-shadow:0 30px 90px rgba(0,0,0,.24),inset 0 1px 0 rgba(255,255,255,.035);overflow:hidden}.delivery-studio::before{content:"";position:absolute;inset:0;pointer-events:none;background:linear-gradient(90deg,transparent,rgba(0,216,255,.035),transparent);transform:translateX(-100%);animation:deliverySweep 8s linear infinite}
        .delivery-studio-top{position:relative;z-index:1;display:flex;justify-content:space-between;align-items:flex-start;gap:20px}.delivery-kicker{color:#00d8ff;font-size:8px;font-weight:900;letter-spacing:.22em}.delivery-studio h3{margin:7px 0;font-size:25px;letter-spacing:-.035em}.delivery-studio-top p{max-width:800px;margin:0;color:#738196;font-size:11px;line-height:1.7}.delivery-live{display:flex;align-items:center;gap:7px;padding:8px 10px;border:1px solid rgba(0,216,255,.13);border-radius:999px;color:#8edff1;font-size:8px;font-weight:900;letter-spacing:.13em;white-space:nowrap}.delivery-live span{width:6px;height:6px;border-radius:50%;background:#00d8ff;box-shadow:0 0 12px rgba(0,216,255,.8);animation:livePulse 1.8s ease-in-out infinite}
        .delivery-tabs{position:relative;z-index:2;display:flex;gap:6px;margin:20px 0;padding:5px;border:1px solid rgba(255,255,255,.055);border-radius:11px;background:rgba(255,255,255,.018);overflow-x:auto}.delivery-tabs button{cursor:pointer;pointer-events:auto;position:relative;z-index:5;border:0;background:transparent;color:#58667a;padding:9px 13px;border-radius:8px;font-size:8px;font-weight:900;letter-spacing:.12em;white-space:nowrap}.delivery-tabs button.active{color:#dffaff;background:rgba(0,216,255,.09);box-shadow:inset 0 0 0 1px rgba(0,216,255,.11)}
        .delivery-overview{position:relative;z-index:1;display:grid;gap:12px}.delivery-hero-card{display:flex;align-items:center;gap:18px;padding:20px;border:1px solid rgba(255,255,255,.055);border-radius:15px;background:rgba(255,255,255,.018)}.delivery-orbit{position:relative;width:80px;height:80px;flex:0 0 80px;display:grid;place-items:center}.delivery-orbit:before,.delivery-orbit:after{content:"";position:absolute;border:1px solid rgba(0,216,255,.2);border-radius:50%}.delivery-orbit:before{inset:4px;animation:spinSlow 8s linear infinite}.delivery-orbit:after{inset:16px;border-color:rgba(104,92,255,.28);animation:spinSlow 5s linear infinite reverse}.delivery-orbit-core{width:32px;height:32px;display:grid;place-items:center;border-radius:50%;background:radial-gradient(circle,#dffaff 0,#00d8ff 22%,#1d6f94 70%,transparent 72%);color:#031018;font-size:13px;font-weight:1000;box-shadow:0 0 30px rgba(0,216,255,.35)}.delivery-orbit i{position:absolute;width:4px;height:4px;border-radius:50%;background:#00d8ff;box-shadow:0 0 9px #00d8ff}.delivery-orbit i:nth-child(2){top:7px;left:35px}.delivery-orbit i:nth-child(3){right:5px;bottom:23px;background:#8a7cff}.delivery-orbit i:nth-child(4){left:10px;bottom:14px}.delivery-mini-label{display:block;color:#526176;font-size:7px;font-weight:900;letter-spacing:.18em;margin-bottom:5px}.delivery-hero-card strong{display:block;font-size:22px;letter-spacing:-.03em}.delivery-hero-card p{margin:5px 0 0;color:#718095;font-size:10px}
        .delivery-metric-grid{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:8px}.delivery-metric-grid>div{padding:14px;border:1px solid rgba(255,255,255,.05);border-radius:12px;background:rgba(255,255,255,.014)}.delivery-metric-grid span,.delivery-metric-grid small{display:block;color:#59677b;font-size:7px;font-weight:900;letter-spacing:.12em}.delivery-metric-grid strong{display:inline-block;margin:7px 5px 2px 0;font-size:21px}.delivery-output-grid{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:9px}.delivery-output-card{cursor:pointer;pointer-events:auto;position:relative;z-index:3;text-align:left;display:flex;flex-direction:column;min-height:150px;padding:15px;border:1px solid rgba(255,255,255,.055);border-radius:13px;background:rgba(255,255,255,.015);color:inherit;transition:transform .25s ease,border-color .25s ease,background .25s ease}.delivery-output-card:hover{transform:translateY(-4px);border-color:rgba(0,216,255,.18);background:rgba(0,216,255,.025)}.delivery-output-icon{width:30px;height:30px;display:grid;place-items:center;margin-bottom:12px;border-radius:9px;background:rgba(0,216,255,.07);color:#00d8ff;font-weight:900}.delivery-output-title{color:#e8f5ff;font-size:10px;font-weight:900;letter-spacing:.05em}.delivery-output-subtitle{margin-top:5px;color:#657389;font-size:9px;line-height:1.5}.delivery-output-state{margin-top:auto;color:#71d9ec;font-size:7px;font-weight:900;letter-spacing:.12em}.delivery-section-heading{display:flex;justify-content:space-between;align-items:center;gap:12px;margin-bottom:12px}.delivery-section-heading span{color:#00d8ff;font-size:8px;font-weight:900;letter-spacing:.16em}.delivery-section-heading strong{color:#8d9bae;font-size:9px}.delivery-detail-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:10px}.delivery-detail-card{padding:16px;border:1px solid rgba(255,255,255,.055);border-radius:13px;background:rgba(255,255,255,.014)}.delivery-detail-head{display:grid;grid-template-columns:auto 1fr auto;gap:10px;align-items:center}.delivery-detail-head .delivery-output-icon{margin:0}.delivery-detail-head strong,.delivery-detail-head span{display:block}.delivery-detail-head strong{font-size:10px}.delivery-detail-head div span{margin-top:3px;color:#657389;font-size:8px}.delivery-detail-head em{font-style:normal;color:#7de2f2;font-size:7px;font-weight:900;letter-spacing:.1em}.delivery-detail-card p{margin:13px 0;color:#8390a2;font-size:10px;line-height:1.65}.delivery-detail-foot{display:flex;justify-content:space-between;color:#465368;font-size:7px;font-weight:900;letter-spacing:.1em}.delivery-file-strip{display:flex;flex-wrap:wrap;gap:7px;align-items:center;margin-top:12px;padding:12px;border:1px dashed rgba(255,255,255,.07);border-radius:11px}.delivery-file-strip>div{margin-right:auto}.delivery-file-strip>div span,.delivery-file-strip>div strong{display:block}.delivery-file-strip>div span{color:#566477;font-size:7px;letter-spacing:.12em;font-weight:900}.delivery-file-strip>div strong{margin-top:3px;font-size:13px}.delivery-file-strip>span{padding:7px 8px;border-radius:7px;background:rgba(255,255,255,.02);color:#566477;font-size:7px;font-weight:900}.delivery-file-strip>span.ready{color:#72e2c4;background:rgba(80,220,175,.05)}.delivery-file-strip>span.not-ready{color:#68758a}
        .delivery-trust-flow{display:grid;grid-template-columns:1fr auto 1fr auto 1fr auto 1fr auto 1fr;gap:7px;align-items:center}.delivery-trust-flow>div{min-height:105px;padding:13px;border:1px solid rgba(255,255,255,.055);border-radius:11px;background:rgba(255,255,255,.014)}.delivery-trust-flow b,.delivery-trust-flow strong,.delivery-trust-flow span{display:block}.delivery-trust-flow b{color:#00d8ff;font-size:7px}.delivery-trust-flow strong{margin-top:8px;font-size:9px}.delivery-trust-flow span{margin-top:5px;color:#657389;font-size:8px;line-height:1.45}.delivery-trust-flow>i{color:#415166;font-style:normal;text-align:center}.delivery-warning-box{margin-top:12px;padding:15px;border-left:2px solid #00d8ff;border-radius:10px;background:rgba(0,216,255,.035)}.delivery-warning-box span{color:#00d8ff;font-size:7px;font-weight:900;letter-spacing:.15em}.delivery-warning-box strong{display:block;margin-top:5px;font-size:11px}.delivery-warning-box p{margin:5px 0 0;color:#718095;font-size:9px;line-height:1.6}
        .delivery-execution-view{display:grid;gap:12px}.execution-banner{display:flex;gap:12px;align-items:flex-start;padding:16px;border:1px solid rgba(255,183,77,.13);border-radius:12px;background:rgba(255,183,77,.035)}.execution-pulse{width:8px;height:8px;flex:0 0 8px;margin-top:4px;border-radius:50%;background:#ffb74d;box-shadow:0 0 14px rgba(255,183,77,.45)}.execution-banner strong{font-size:9px;letter-spacing:.12em}.execution-banner p{margin:5px 0 0;color:#8c8b80;font-size:9px;line-height:1.6}.execution-grid{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:9px}.execution-grid>div{padding:15px;border:1px solid rgba(255,255,255,.05);border-radius:12px;background:rgba(255,255,255,.014)}.execution-grid span,.execution-grid small{display:block;color:#58667a;font-size:7px;font-weight:900;letter-spacing:.1em}.execution-grid strong{display:block;margin:8px 0 5px;font-size:10px;color:#f0c486}.execution-grid small{line-height:1.55;letter-spacing:0;font-weight:600;color:#68758a}
        @keyframes deliverySweep{to{transform:translateX(100%)}}@keyframes livePulse{50%{opacity:.35;transform:scale(.72)}}@keyframes spinSlow{to{transform:rotate(360deg)}}
        @media (max-width:1100px){.delivery-output-grid{grid-template-columns:repeat(2,minmax(0,1fr))}.delivery-metric-grid{grid-template-columns:repeat(2,minmax(0,1fr))}.execution-grid{grid-template-columns:repeat(2,minmax(0,1fr))}.delivery-trust-flow{grid-template-columns:1fr}.delivery-trust-flow>i{transform:rotate(90deg)}}
        @media (max-width:760px){.side-panel{position:relative;top:auto}.delivery-studio{padding:16px;border-radius:15px}.delivery-studio-top{flex-direction:column}.delivery-live{align-self:flex-start}.delivery-hero-card{align-items:flex-start}.delivery-orbit{width:62px;height:62px;flex-basis:62px}.delivery-orbit-core{width:27px;height:27px;font-size:11px}.delivery-output-grid,.delivery-detail-grid,.execution-grid{grid-template-columns:1fr}.delivery-metric-grid{grid-template-columns:repeat(2,minmax(0,1fr))}.delivery-detail-head{grid-template-columns:auto 1fr}.delivery-detail-head em{grid-column:2}.delivery-file-strip{align-items:flex-start;flex-direction:column}}
        @media (prefers-reduced-motion:reduce){.delivery-studio:before,.delivery-orbit:before,.delivery-orbit:after,.delivery-live span{animation:none!important}}

      /* =========================================================
         AURA AUTHENTICATION EXPERIENCE
         ========================================================= */
      .aura-login-page {
        min-height: 100vh;
        position: relative;
        overflow: hidden;
        display: grid;
        place-items: center;
        padding: 34px;
        background: #03050b;
        color: #eef5ff;
      }
      .login-grid {
        position: absolute;
        inset: 0;
        background-image: linear-gradient(rgba(95, 143, 190, .07) 1px, transparent 1px), linear-gradient(90deg, rgba(95, 143, 190, .07) 1px, transparent 1px);
        background-size: 54px 54px;
        mask-image: radial-gradient(circle at center, black 20%, transparent 82%);
      }
      .login-scanline {
        position: absolute;
        inset: 0;
        pointer-events: none;
        opacity: .14;
        background: repeating-linear-gradient(to bottom, transparent 0, transparent 3px, rgba(255,255,255,.035) 4px);
      }
      .login-ambient {
        position: absolute;
        width: 480px;
        height: 480px;
        border-radius: 50%;
        filter: blur(90px);
        opacity: .18;
        pointer-events: none;
        animation: loginFloat 9s ease-in-out infinite;
      }
      .login-ambient-one { left: -160px; top: -130px; background: #2368ff; }
      .login-ambient-two { right: -160px; bottom: -160px; background: #16d5c5; animation-delay: -3s; }
      .login-shell {
        position: relative;
        z-index: 2;
        width: min(1180px, 100%);
        display: grid;
        grid-template-columns: 1.05fr .95fr;
        gap: 70px;
        align-items: center;
      }
      .login-brand-column { padding: 20px 0; }
      .login-logo-wrap {
        width: 82px;
        height: 82px;
        display: grid;
        place-items: center;
        margin-bottom: 26px;
        border: 1px solid rgba(124, 190, 255, .3);
        border-radius: 22px;
        background: rgba(10, 18, 33, .72);
        box-shadow: 0 0 45px rgba(54, 137, 255, .2), inset 0 0 30px rgba(82, 164, 255, .06);
      }
      .login-logo-wrap img { width: 62px; height: 62px; object-fit: contain; }
      .login-eyebrow {
        display: flex;
        align-items: center;
        gap: 10px;
        color: #8eb8e8;
        font-size: 11px;
        font-weight: 800;
        letter-spacing: .18em;
        margin-bottom: 18px;
      }
      .login-eyebrow span { width: 28px; height: 1px; background: #62b4ff; box-shadow: 0 0 12px #62b4ff; }
      .login-brand-column h1 { font-size: clamp(48px, 6vw, 84px); line-height: .95; letter-spacing: -.055em; margin: 0; font-weight: 800; }
      .login-brand-column h1 span { color: #71c8ff; text-shadow: 0 0 35px rgba(70, 174, 255, .35); }
      .login-tagline { max-width: 610px; margin: 22px 0 0; color: #d9e8fa; font-size: 21px; line-height: 1.35; font-weight: 600; }
      .login-description { max-width: 620px; margin: 18px 0 0; color: #8195ae; font-size: 15px; line-height: 1.8; }
      .login-capabilities { display: grid; grid-template-columns: repeat(4, 1fr); gap: 10px; max-width: 620px; margin-top: 34px; }
      .login-capabilities div { border-left: 1px solid rgba(105, 170, 225, .22); padding: 10px 12px; background: rgba(9, 17, 29, .38); }
      .login-capabilities b { display: block; color: #6ebaff; font-size: 11px; margin-bottom: 8px; }
      .login-capabilities span { color: #8298b2; font-size: 9px; font-weight: 800; letter-spacing: .13em; }
      .login-card {
        border: 1px solid rgba(116, 172, 222, .2);
        background: linear-gradient(145deg, rgba(13, 22, 37, .94), rgba(5, 10, 18, .96));
        border-radius: 26px;
        padding: 28px;
        box-shadow: 0 35px 100px rgba(0,0,0,.5), inset 0 1px 0 rgba(255,255,255,.04), 0 0 60px rgba(46, 127, 218, .08);
        backdrop-filter: blur(22px);
      }
      .login-card-top { display: flex; justify-content: space-between; gap: 16px; align-items: flex-start; }
      .login-card-kicker { color: #6287ad; font-size: 9px; letter-spacing: .17em; font-weight: 800; margin-bottom: 8px; }
      .login-card h2 { margin: 0; font-size: 25px; letter-spacing: -.02em; }
      .login-live { white-space: nowrap; color: #7de4c8; font-size: 9px; font-weight: 800; letter-spacing: .12em; padding-top: 4px; }
      .login-live span { display: inline-block; width: 6px; height: 6px; margin-right: 7px; border-radius: 50%; background: #59dfb9; box-shadow: 0 0 12px #59dfb9; }
      .auth-tabs { display: grid; grid-template-columns: 1fr 1fr; margin: 24px 0 22px; border-bottom: 1px solid rgba(120, 164, 204, .15); }
      .auth-tabs button { border: 0; background: transparent; color: #6e849c; padding: 11px 6px; font-size: 10px; font-weight: 800; letter-spacing: .11em; cursor: pointer; border-bottom: 2px solid transparent; }
      .auth-tabs button.active { color: #dff3ff; border-bottom-color: #63baff; }
      .login-form { display: grid; gap: 14px; }
      .login-form label { display: grid; gap: 7px; }
      .login-form label > span { color: #7188a2; font-size: 9px; font-weight: 800; letter-spacing: .13em; }
      .login-form input { width: 100%; box-sizing: border-box; border: 1px solid rgba(111, 156, 197, .16); border-radius: 11px; padding: 13px 14px; background: rgba(2, 7, 14, .72); color: #eaf5ff; outline: none; font: inherit; }
      .login-form input:focus { border-color: rgba(98, 187, 255, .65); box-shadow: 0 0 0 3px rgba(72, 160, 232, .08); }
      .login-form input::placeholder { color: #46596f; }
      .login-error { border: 1px solid rgba(255, 100, 100, .25); background: rgba(120, 24, 24, .14); color: #ff9d9d; padding: 10px 12px; border-radius: 9px; font-size: 11px; }
      .primary-auth-button, .google-auth-button, .guest-auth-button { width: 100%; border-radius: 11px; padding: 13px 15px; cursor: pointer; font: inherit; font-weight: 800; letter-spacing: .1em; font-size: 10px; transition: transform .2s ease, border-color .2s ease, background .2s ease; }
      .primary-auth-button { display: flex; justify-content: space-between; align-items: center; border: 1px solid rgba(107, 196, 255, .42); background: linear-gradient(135deg, rgba(44, 127, 202, .85), rgba(30, 78, 145, .72)); color: white; box-shadow: 0 10px 30px rgba(35, 121, 209, .16); }
      .primary-auth-button:hover, .google-auth-button:hover, .guest-auth-button:hover { transform: translateY(-1px); }
      .auth-divider { display: flex; align-items: center; gap: 10px; margin: 20px 0 14px; color: #53677e; font-size: 8px; font-weight: 800; letter-spacing: .12em; }
      .auth-divider span { flex: 1; height: 1px; background: rgba(105, 146, 184, .13); }
      .google-auth-button { display: flex; align-items: center; justify-content: center; gap: 10px; border: 1px solid rgba(126, 164, 201, .2); background: rgba(13, 23, 37, .8); color: #dbe8f5; }
      .google-mark { display: grid; place-items: center; width: 19px; height: 19px; border-radius: 50%; background: white; color: #4285f4; font-size: 12px; font-weight: 900; }
      .guest-auth-button { margin-top: 9px; border: 1px solid rgba(115, 154, 190, .12); background: transparent; color: #7890a9; }
      .login-trust { margin-top: 18px; color: #50647b; font-size: 9px; line-height: 1.55; text-align: center; }
      .login-trust span { color: #65c8ae; margin-right: 5px; }
      .logout-button { border: 1px solid rgba(117, 151, 182, .14); background: rgba(9, 16, 27, .65); color: #71869d; border-radius: 9px; padding: 9px 11px; cursor: pointer; font-size: 8px; font-weight: 800; letter-spacing: .08em; }
      .logout-button:hover { color: #d7e8f7; border-color: rgba(117, 181, 229, .35); }
      @keyframes loginFloat { 0%,100% { transform: translate3d(0,0,0) scale(1); } 50% { transform: translate3d(20px,-18px,0) scale(1.05); } }
      @media (max-width: 900px) {
        .aura-login-page { padding: 20px; overflow-y: auto; }
        .login-shell { grid-template-columns: 1fr; gap: 30px; max-width: 620px; }
        .login-brand-column { text-align: center; padding-top: 8px; }
        .login-logo-wrap { margin: 0 auto 20px; }
        .login-eyebrow { justify-content: center; }
        .login-description { margin-left: auto; margin-right: auto; }
        .login-capabilities { margin-left: auto; margin-right: auto; }
      }
      @media (max-width: 520px) {
        .aura-login-page { padding: 14px; }
        .login-card { padding: 21px; border-radius: 20px; }
        .login-brand-column h1 { font-size: 50px; }
        .login-tagline { font-size: 17px; }
        .login-capabilities { grid-template-columns: 1fr 1fr; }
        .login-card-top { display: block; }
        .login-live { margin-top: 10px; }
      }
      @media (prefers-reduced-motion: reduce) {
        .login-ambient { animation: none; }
        .primary-auth-button, .google-auth-button, .guest-auth-button { transition: none; }
      }

        .delivery-output-card{position:relative;text-align:left;cursor:pointer}
        .delivery-open-hint{display:block;margin-top:12px;color:#00d8ff;font-size:8px;font-weight:900;letter-spacing:.12em}
        .delivery-card-clickarea{display:block;width:100%;border:0;background:transparent;color:inherit;text-align:left;cursor:pointer;padding:0}
        .delivery-card-clickarea:focus-visible,.delivery-detail-foot button:focus-visible,.output-close-button:focus-visible,.selected-output-actions button:focus-visible{outline:1px solid #00d8ff;outline-offset:3px;border-radius:8px}
        .selected-output-panel{position:relative;margin-top:14px;border:1px solid rgba(0,216,255,.18);border-radius:16px;background:rgba(4,11,19,.92);overflow:hidden;box-shadow:0 24px 70px rgba(0,0,0,.24)}
        .selected-output-header{display:flex;justify-content:space-between;gap:18px;align-items:center;padding:18px 20px;border-bottom:1px solid rgba(255,255,255,.06);background:linear-gradient(90deg,rgba(0,216,255,.055),rgba(104,92,255,.05))}
        .selected-output-header>div{display:flex;gap:12px;align-items:center}
        .selected-output-header small{display:block;color:#00d8ff;font-size:7px;font-weight:900;letter-spacing:.18em}
        .selected-output-header h4{margin:3px 0;font-size:17px;letter-spacing:-.02em}
        .selected-output-header p{margin:0;color:#718097;font-size:10px}
        .output-close-button{border:1px solid rgba(0,216,255,.2);background:rgba(0,216,255,.05);color:#9deafa;border-radius:8px;padding:8px 10px;font-size:8px;font-weight:900;letter-spacing:.1em;cursor:pointer;white-space:nowrap}
        .selected-output-notice{display:flex;gap:10px;flex-wrap:wrap;padding:10px 20px;border-bottom:1px solid rgba(255,255,255,.05)}
        .selected-output-notice span,.selected-output-notice strong{font-size:7px;font-weight:900;letter-spacing:.12em;padding:5px 7px;border-radius:5px;background:rgba(255,255,255,.035);color:#8290a4}
        .selected-output-notice strong{color:#00d8ff}
        .selected-output-content{display:grid;grid-template-columns:1fr 1fr;gap:10px;padding:16px}
        .selected-output-content article{min-width:0;border:1px solid rgba(255,255,255,.055);border-radius:10px;background:rgba(255,255,255,.018);padding:13px}
        .selected-output-content article>div{color:#8edff1;font-size:8px;font-weight:900;letter-spacing:.13em;margin-bottom:8px}
        .selected-output-content pre{margin:0;white-space:pre-wrap;overflow-wrap:anywhere;color:#aab5c5;font:10px/1.65 ui-monospace,SFMono-Regular,Consolas,monospace;max-height:260px;overflow:auto}
        .selected-output-actions{display:flex;align-items:center;gap:12px;flex-wrap:wrap;padding:14px 16px;border-top:1px solid rgba(255,255,255,.06)}
        .selected-output-actions button{border:1px solid rgba(0,216,255,.24);background:linear-gradient(135deg,rgba(0,216,255,.12),rgba(104,92,255,.1));color:#c8f8ff;border-radius:8px;padding:9px 12px;font-size:8px;font-weight:900;letter-spacing:.1em;cursor:pointer}
        .selected-output-actions span{color:#657287;font-size:8px;line-height:1.5}
        @media(max-width:760px){.selected-output-content{grid-template-columns:1fr}.selected-output-header{align-items:flex-start;flex-direction:column}.output-close-button{width:100%}}

.aura20-graph-canvas{position:relative;height:430px;margin-top:16px;border:1px solid rgba(255,255,255,.06);border-radius:18px;overflow:hidden;background:radial-gradient(circle at center,rgba(0,216,255,.08),transparent 42%),rgba(255,255,255,.012)}.aura20-graph-canvas:before{content:"";position:absolute;inset:14%;border:1px dashed rgba(0,216,255,.12);border-radius:50%}.aura20-graph-node{position:absolute;transform:translate(-50%,-50%);z-index:2;min-width:90px;max-width:150px;padding:9px 11px;border:1px solid rgba(0,216,255,.2);border-radius:12px;background:rgba(5,13,27,.94);color:#eafaff;cursor:pointer;box-shadow:0 8px 28px rgba(0,0,0,.25)}.aura20-graph-node b,.aura20-graph-node span{display:block}.aura20-graph-node b{font-size:9px}.aura20-graph-node span{margin-top:3px;color:#657389;font-size:7px;text-transform:uppercase;letter-spacing:.08em}.aura20-graph-node.project{border-color:rgba(0,216,255,.5);box-shadow:0 0 30px rgba(0,216,255,.18)}.aura20-edge{position:absolute;left:50%;top:50%;width:37%;height:1px;background:linear-gradient(90deg,rgba(0,216,255,.02),rgba(0,216,255,.22),rgba(104,92,255,.02));transform-origin:left center}.aura20-graph-legend{display:flex;flex-wrap:wrap;gap:7px;margin-top:10px}.aura20-graph-legend span{padding:5px 8px;border-radius:999px;background:rgba(255,255,255,.03);color:#718095;font-size:7px;font-weight:900;text-transform:uppercase}
.validation-gate-panel{margin-top:20px;padding:18px;border:1px solid rgba(0,216,255,.12);border-radius:16px;background:linear-gradient(145deg,rgba(0,216,255,.035),rgba(104,92,255,.02))}.validation-gate-head{display:flex;justify-content:space-between;gap:16px;align-items:flex-start}.validation-gate-head h3{margin:7px 0 4px;font-size:18px}.validation-gate-head p{margin:0;color:#718095;font-size:10px;line-height:1.65;max-width:760px}.validation-gate-head button,.validation-gate-actions button{border:1px solid rgba(0,216,255,.2);background:rgba(0,216,255,.06);color:#bcefff;border-radius:9px;padding:9px 11px;font-size:8px;font-weight:900;letter-spacing:.1em;cursor:pointer}.validation-gate-grid{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:8px;margin-top:15px}.validation-gate-grid>div{padding:11px;border:1px solid rgba(255,255,255,.05);border-radius:10px;background:rgba(255,255,255,.015)}.validation-gate-grid>div span{font-size:13px}.validation-gate-grid>div b,.validation-gate-grid>div small{display:block}.validation-gate-grid>div b{margin-top:5px;font-size:8px}.validation-gate-grid>div small{margin-top:3px;color:#657389;font-size:7px}.validation-gate-grid .passed{border-color:rgba(80,220,175,.18)}.validation-gate-grid .passed span{color:#72e2c4}.validation-gate-grid .blocked span{color:#68758a}.validation-gate-actions{display:flex;justify-content:space-between;gap:10px;align-items:center;margin-top:14px}.validation-gate-actions strong{color:#8d9bae;font-size:8px;letter-spacing:.12em}.validation-gate-actions button:disabled{opacity:.45;cursor:not-allowed}.validation-gate-message{margin-top:10px;padding:9px;border-radius:8px;background:rgba(255,255,255,.025);color:#8edff1;font-size:8px}@media(max-width:760px){.validation-gate-head,.validation-gate-actions{flex-direction:column}.validation-gate-grid{grid-template-columns:repeat(2,minmax(0,1fr))}}
      `}

</style>

      {loading && (
        <div className="loading-overlay">
          <div className="loading-card">
            <div className="loading-orb">
              <span>A</span>
            </div>

            <h3>AURA is thinking beyond the idea.</h3>

            <p>
              Investigating research, analyzing evidence,
              designing the solution and connecting the complete
              project journey.
            </p>
          </div>
        </div>
      )}
    </main>
  );
}


function List({ value }: { value: unknown[] }) {
  return (
    <ul className="aura20-capability-list">
      {value.map((item, index) => {
        const text = typeof item === "string" ? item :
          (item && typeof item === "object" && "title" in item && typeof (item as { title?: unknown }).title === "string")
            ? (item as { title: string }).title
            : JSON.stringify(item);
        return (
          <li key={`${index}-${text}`}>
            <span className="aura20-list-dot">✦</span>
            <span>{text}</span>
          </li>
        );
      })}
    </ul>
  );
}

function AuraTwoPointZero({ project, idea, projectName }: { project: Project | null; idea: string; projectName: string }) {
  const [tab, setTab] = useState("detail");
  const [blueprint, setBlueprint] = useState<any>(null);
  const [graph, setGraph] = useState<any>(null);
  const [recs, setRecs] = useState<any[]>([]);
  const [viva, setViva] = useState<any>(null);
  const [docText, setDocText] = useState("");
  const [docAnalysis, setDocAnalysis] = useState<any>(null);
  const [claims, setClaims] = useState("");
  const [evidence, setEvidence] = useState("");
  const [claimAnalysis, setClaimAnalysis] = useState<any>(null);
  const [researchQuery, setResearchQuery] = useState(idea || "");
  const [research, setResearch] = useState<any>(null);
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState("");

  async function call(path: string, init?: RequestInit) {
    const response = await auraFetch(API_BASE + path, {
      ...init,
      headers: { "Content-Type": "application/json", ...(init?.headers || {}) },
    });
    const data = await response.json().catch(() => ({}));
    if (!response.ok) throw new Error(data.detail || "AURA 2.0 request failed.");
    return data;
  }

  async function runDetail() {
    setBusy(true); setMessage("");
    try {
      const data = await call("/api/aura/blueprint", {
        method: "POST",
        body: JSON.stringify({ idea: idea || "AURA research project", project_name: projectName || undefined }),
      });
      setBlueprint(data.blueprint);
      setTab("detail");
    } catch (e) { setMessage(e instanceof Error ? e.message : "Unable to generate blueprint."); }
    finally { setBusy(false); }
  }

  async function loadProjectTools() {
    if (!project?.project_id) {
      setMessage("Run or open an AURA project first to use project-linked intelligence.");
      return;
    }
    setBusy(true); setMessage("");
    try {
      const [g, r, v] = await Promise.all([
        call(`/api/aura/projects/${project.project_id}/graph`),
        call(`/api/aura/projects/${project.project_id}/recommendations`),
        call(`/api/aura/projects/${project.project_id}/viva`),
      ]);
      setGraph(g.graph); setRecs(r.recommendations || []); setViva(v.viva);
    } catch (e) { setMessage(e instanceof Error ? e.message : "Unable to load project intelligence."); }
    finally { setBusy(false); }
  }

  async function analyzeDoc() {
    if (!docText.trim()) return;
    setBusy(true);
    try {
      const data = await call("/api/aura/document/analyze", {
        method: "POST", body: JSON.stringify({ text: docText, filename: "AURA document" }),
      });
      setDocAnalysis(data.analysis); setTab("documents");
    } catch (e) { setMessage(e instanceof Error ? e.message : "Document analysis failed."); }
    finally { setBusy(false); }
  }

  async function analyzeClaims() {
    setBusy(true);
    try {
      const data = await call("/api/aura/claims/analyze", {
        method: "POST", body: JSON.stringify({
          claims: claims.split("\n").map(x => x.trim()).filter(Boolean),
          evidence: evidence.split("\n").map(x => x.trim()).filter(Boolean),
        }),
      });
      setClaimAnalysis(data.analysis); setTab("evidence");
    } catch (e) { setMessage(e instanceof Error ? e.message : "Claim analysis failed."); }
    finally { setBusy(false); }
  }

  async function runResearch() {
    if (!researchQuery.trim()) return;
    setBusy(true);
    try {
      const data = await call("/api/aura/research/web", {
        method: "POST", body: JSON.stringify({ query: researchQuery, limit: 8 }),
      });
      setResearch(data); setTab("research");
    } catch (e) { setMessage(e instanceof Error ? e.message : "Research search failed."); }
    finally { setBusy(false); }
  }

  const sections = blueprint ? Object.entries(blueprint).filter(([k]) => k !== "domains" && k !== "keywords" && k !== "completion_gates") : [];
  return (
    <div className="aura20-shell">
      <div className="aura20-head">
        <div>
          <div className="aura20-kicker">AURA 2.0 / INTELLIGENCE LAYER</div>
          <h2>✦ AURA DETAIL</h2>
          <p>Extend the original AURA journey with project definition, evidence intelligence, graph reasoning, research discovery and delivery intelligence.</p>
        </div>
        <button className="aura20-primary" onClick={runDetail} disabled={busy}>✦ {busy ? "PROCESSING..." : "GENERATE DETAIL"}</button>
      </div>
      <div className="aura20-tabs">
        {[
          ["detail","✦ AURA DETAIL"],["research","⌕ RESEARCH"],["evidence","◉ EVIDENCE"],["graph","⌬ GRAPH"],["execution","∿ EXPERIMENT / VALIDATE"],["delivery","▣ DELIVERY / VIVA"],["team","◈ TEAM / ROLES"]
        ].map(([key,label]) => <button key={key} className={tab === key ? "active" : ""} onClick={() => { setTab(key); if (key === "graph" || key === "delivery") loadProjectTools(); }}>{label}</button>)}
      </div>
      {message && <div className="aura20-message">{message}</div>}

      {tab === "detail" && (
        <>
        <DependencyImpactPanel project={project} />
        <InnovationImplementationTraceability project={project} />
        <div className="aura20-truth-dashboard">
          <div className="aura20-truth-heading"><div><span>TRUTH-AWARE PROJECT CONTROL</span><h3>AURA PROJECT STATUS</h3></div><div className="aura20-truth-badge">🛡 NO FABRICATED RESULTS</div></div>
          <div className="aura20-status-flow">
            {[
              ["DESIGNED", "COMPLETE", "done"],
              ["RESEARCHED", "EVIDENCE REQUIRED", "warn"],
              ["IMPLEMENTED", "READY", "ready"],
              ["EXECUTED", "NOT EXECUTED", "blocked"],
              ["MEASURED", "PENDING", "blocked"],
              ["VALIDATED", "PENDING", "blocked"],
              ["DELIVERED", "PENDING", "blocked"],
            ].map(([title, state, tone]) => <div className={`aura20-status-step ${tone}`} key={title}><span>{title}</span><b>{state}</b></div>)}
          </div>
          <p className="aura20-truth-note"><b>Workflow completion ≠ scientific validation ≠ project execution.</b> AURA separates generated design decisions from real-world evidence.</p>
        </div>
        <div className="aura20-grid">
          <div className="aura20-card wide">
            <div className="aura20-label">PROJECT BLUEPRINT</div>
            {!blueprint ? <p>Enter an idea in the original AURA input and use <b>GENERATE DETAIL</b>. The result expands it into an 11-area project specification.</p> :
              <>
              <div className="aura20-blueprint-meta"><div><span>AGENT</span><b>AURA Project Definition Agent · Intelligence Engine</b></div><div><span>TRUTH STATUS</span><b>DESIGNED — NOT EXECUTED</b></div></div>
              <div className="aura20-blueprint">{sections.map(([key,value]) =>
                <div className="aura20-section" key={key}><h3>{humanizeKey(key)}</h3><BlueprintValue value={value} /></div>
              )}</div></>}
          </div>
          <div className="aura20-card">
            <div className="aura20-label">TRUTH BOUNDARY</div>
            <h3>Scientific truth protection</h3>
            <p>Plans, generated architectures and proposed experiments are not execution results. AURA must not fabricate metrics, datasets, screenshots or validation claims.</p>
          </div>
          <div className="aura20-card">
            <div className="aura20-label">V2 CAPABILITIES</div>
            <List value={["Project Definition Agent","Literature / Crossref discovery","Evidence & claim scoring","Research graph","Multi-agent role model","Experiment & validation gates","Document analysis","Gap / innovation recommendations","Viva generation","Authentication & persistent local memory"]} />
          </div>
        </div>
        </>
      )}

      {tab === "research" && <div className="aura20-card">
        <div className="aura20-label">RESEARCH INTELLIGENCE</div>
        <div className="aura20-form"><input value={researchQuery} onChange={e=>setResearchQuery(e.target.value)} placeholder="Research topic or question"/><button onClick={runResearch} disabled={busy}>SEARCH</button></div>
        <p className="aura20-note">Source discovery uses the public Crossref API. Discovered sources are evidence candidates, not automatically verified truth.</p>
        {research?.results?.map((r:any,i:number)=><div className="aura20-result" key={i}><b>{r.title || "Untitled"}</b><span>{r.DOI || "No DOI"}</span><p>{r.container_title || ""} {r.published ? "• "+JSON.stringify(r.published) : ""}</p></div>)}
      </div>}

      {tab === "evidence" && <div className="aura20-grid">
        <div className="aura20-card"><div className="aura20-label">CLAIMS</div><textarea value={claims} onChange={e=>setClaims(e.target.value)} placeholder="One claim per line"/><textarea value={evidence} onChange={e=>setEvidence(e.target.value)} placeholder="Evidence statements, one per line"/><button className="aura20-primary" onClick={analyzeClaims} disabled={busy}>ANALYZE SUPPORT</button></div>
        <div className="aura20-card"><div className="aura20-label">ANALYSIS</div>{claimAnalysis ? <pre>{JSON.stringify(claimAnalysis,null,2)}</pre> : <p>Support scores are heuristic lexical signals, not scientific verification.</p>}</div>
      </div>}

      {tab === "graph" && <div className="aura20-card"><div className="aura20-label">PROJECT RESEARCH GRAPH</div><button className="aura20-primary" onClick={loadProjectTools} disabled={busy}>REFRESH GRAPH</button>{graph ? <><div className="aura20-graph-canvas">{(graph.edges||[]).map((e:any,i:number)=><div className="aura20-edge" key={`edge-${i}`} />)}{(graph.nodes||[]).map((n:any,i:number)=>{ const total=Math.max(1,(graph.nodes||[]).length); const angle=(i/total)*Math.PI*2; const x=50+37*Math.cos(angle); const y=50+37*Math.sin(angle); return <button type="button" className={`aura20-graph-node ${n.type||""}`} key={n.id} style={{left:`${x}%`,top:`${y}%`}} title={`${n.label} · ${n.type}`}><b>{n.label}</b><span>{n.type}{n.count ? ` · ${n.count}` : ""}</span></button>})}</div><div className="aura20-graph-legend">{(graph.filters||[]).map((f:string)=><span key={f}>{f}</span>)}</div></> : <p>Open a project and refresh to build the graph from its actual state.</p>}</div>}

      {tab === "execution" && <div className="aura20-grid"><div className="aura20-card"><div className="aura20-label">EXPERIMENT GATES</div><List value={["Define hypothesis","Declare baseline","Define metrics","Execute experiment","Record raw results","Compare baseline vs proposed","Review reproducibility","Human scientific validation"]}/></div><div className="aura20-card"><div className="aura20-label">VALIDATION STATUS</div><h3>NOT CLAIMED</h3><p>Designed experiments are not presented as completed experiments. Measured results enter AURA only after real execution.</p></div></div>}

      {tab === "delivery" && <div className="aura20-grid"><div className="aura20-card"><div className="aura20-label">DOCUMENT ANALYSIS</div><textarea value={docText} onChange={e=>setDocText(e.target.value)} placeholder="Paste paper/report text here..."/><button className="aura20-primary" onClick={analyzeDoc} disabled={busy}>ANALYZE DOCUMENT</button>{docAnalysis&&<pre>{JSON.stringify(docAnalysis,null,2)}</pre>}</div><div className="aura20-card"><div className="aura20-label">VIVA / RECOMMENDATIONS</div><button className="aura20-primary" onClick={loadProjectTools} disabled={busy}>GENERATE PROJECT PACK</button>{recs.length>0&&<List value={recs}/>} {viva&&<pre>{JSON.stringify(viva,null,2)}</pre>}</div></div>}

      {tab === "team" && <div className="aura20-grid"><div className="aura20-card"><div className="aura20-label">MULTI-AGENT COUNCIL</div><List value={["Research Agent","Evidence Agent","Claim Analyst","Innovation Agent","Architect Agent","Experiment Agent","Validation Agent","Delivery Agent"]}/></div><div className="aura20-card"><div className="aura20-label">COLLABORATION ROLES</div><List value={["researcher","project_manager","developer","admin"]}/><p>Role-based collaboration architecture is available in the AURA 2.0 backend.</p></div></div>}
    </div>
  );
}

function UnifiedProjectIntelligence({ project }: { project: Project | null }) {
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(false);

  const load = async () => {
    if (!project?.project_id) return;
    setLoading(true);
    try {
      const r = await auraFetch(`${API_BASE}/api/aura/projects/${project.project_id}/intelligence/unified`, { cache: "no-store" });
      if (!r.ok) throw new Error("Unified intelligence unavailable");
      setData(await r.json());
    } catch { setData(null); }
    finally { setLoading(false); }
  };

  useEffect(() => { load(); }, [project?.project_id]);
  if (!project) return null;

  const truth = data?.truth || {};
  const completion = data?.completion || {};
  const gate = data?.validation_gate || {};
  const impact = data?.dependency_impact || {};
  const obs = data?.results_observatory || {};
  const dimensions = data?.intelligence?.dimensions || {};

  return (
    <section className="aura20-card wide" style={{ marginBottom: 18 }}>
      <div className="aura20-label">AURA 6.1 / UNIFIED PROJECT INTELLIGENCE</div>
      <div style={{ display: "flex", justifyContent: "space-between", gap: 16, alignItems: "center" }}>
        <div><h3>One truth pipeline across the project</h3><p>Project Twin → dependency impact → results → validation → completion. Each layer remains evidence-aware.</p></div>
        <button className="aura20-primary" onClick={load} disabled={loading}>{loading ? "SYNCING..." : "SYNC INTELLIGENCE"}</button>
      </div>
      {!data ? <p className="aura20-note">Unified state will appear when the project is available.</p> : <>
        <div className="aci-metrics" style={{ marginTop: 14 }}>
          <div className="aci-metric"><span>WORKFLOW</span><strong>{Number(truth.workflow || 0).toFixed(0)}%</strong></div>
          <div className="aci-metric"><span>RESULTS</span><strong>{obs.measured_results ? "MEASURED" : "PENDING"}</strong></div>
          <div className="aci-metric"><span>VALIDATION</span><strong>{gate.ready ? "READY" : "BLOCKED"}</strong></div>
          <div className="aci-metric"><span>COMPLETION</span><strong>{completion.completed ? "COMPLETE" : "IN PROGRESS"}</strong></div>
        </div>
        <div className="aura20-grid" style={{ marginTop: 14 }}>
          <div className="aura20-card"><div className="aura20-label">PROJECT HEALTH</div>{Object.entries(dimensions).map(([k,v]) => <div key={k} className="aura20-result"><b>{humanizeKey(k)}</b><span>{Number(v || 0).toFixed(0)}%</span></div>)}</div>
          <div className="aura20-card"><div className="aura20-label">VALIDATION GATE</div><h3>{gate.status || "BLOCKED"}</h3><p>{gate.required_passed || 0} / {gate.required_total || 0} required criteria passed.</p><p className="aura20-note">Scientific validation: {truth.scientific_validation ? "RECORDED" : "NOT RECORDED"} · Human approval: {truth.human_approval ? "RECORDED" : "NOT RECORDED"}</p></div>
          <div className="aura20-card"><div className="aura20-label">DEPENDENCY IMPACT</div><h3>{impact.requires_reexecution ? "RE-EXECUTION REQUIRED" : "NO RE-EXECUTION FLAG"}</h3><p>{Array.isArray(impact.impacted_nodes) ? impact.impacted_nodes.length : 0} downstream nodes impacted.</p><p className="aura20-note">{impact.requires_revalidation ? "Re-validation is required." : "No re-validation flag."}</p></div>
          <div className="aura20-card"><div className="aura20-label">TRUTH BOUNDARY</div><p><b>{completion.status || "IN_PROGRESS"}</b></p><p>{truth.boundary}</p></div>
        </div>
      </>}
    </section>
  );
}

function AuraRequirementsAudit() {
  const [audit, setAudit] = useState<Record<string, unknown> | null>(null);
  const [loading, setLoading] = useState(false);
  const [open, setOpen] = useState(false);

  const load = () => {
    setLoading(true);
    auraFetch(`${API_BASE}/api/aura/requirements/audit`, { cache: "no-store" })
      .then((r) => r.ok ? r.json() : Promise.reject(new Error("Audit unavailable")))
      .then((data) => setAudit(isRecord(data.audit) ? data.audit : null))
      .catch(() => setAudit(null))
      .finally(() => setLoading(false));
  };

  useEffect(() => { load(); }, []);

  const summary = isRecord(audit?.summary) ? audit.summary : {};
  const atomic = isRecord(audit?.atomic_649) ? audit.atomic_649 : {};
  const areas = Array.isArray(audit?.areas) ? audit.areas : [];
  const implemented = Number(summary.implemented) || 0;
  const partial = Number(summary.partial) || 0;
  const missing = Number(summary.missing) || 0;
  const total = Number(audit?.area_count) || areas.length || 0;

  return (
    <section className="aura-requirements-audit">
      <div className="ara-head">
        <div>
          <span>REQUIREMENTS CONTROL</span>
          <h3>Implementation Audit</h3>
          <p>Repository evidence is tracked separately from atomic requirement verification.</p>
        </div>
        <div className="ara-actions">
          <button type="button" onClick={load} disabled={loading}>{loading ? "SYNCING…" : "REFRESH AUDIT"}</button>
          <button type="button" onClick={() => setOpen(v => !v)}>{open ? "HIDE DETAIL" : "VIEW DETAIL"}</button>
        </div>
      </div>
      <div className="ara-summary">
        <div><b>{implemented}</b><span>IMPLEMENTED AREAS</span></div>
        <div><b>{partial}</b><span>PARTIAL</span></div>
        <div><b>{missing}</b><span>MISSING</span></div>
        <div><b>{total}</b><span>TOTAL AREAS</span></div>
        <div className={atomic.available === true ? "ara-atomic ready" : "ara-atomic"}><b>{atomic.available === true ? "READY" : "SOURCE REQUIRED"}</b><span>649-ITEM ATOMIC AUDIT</span></div>
      </div>
      {open && (
        <div className="ara-detail">
          {areas.map((item, i) => {
            const row = isRecord(item) ? item : {};
            const status = safeText(row.status) || "UNKNOWN";
            return <div key={`${safeText(row.area)}-${i}`} className={`ara-row ${status.toLowerCase()}`}><span>{safeText(row.area)}</span><b>{status}</b></div>;
          })}
          <small>{safeText(atomic.message) || "Atomic requirement source status unavailable."}</small>
        </div>
      )}
    </section>
  );
}

function AuraProjectIntelligenceOverview({ project }: { project: Project | null }) {
  const [overview, setOverview] = useState<Record<string, unknown> | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!project?.project_id) return;
    let cancelled = false;
    setLoading(true);
    auraFetch(`${API_BASE}/api/aura/projects/${project.project_id}/overview`, { cache: "no-store" })
      .then((r) => r.ok ? r.json() : Promise.reject(new Error("Overview unavailable")))
      .then((data) => { if (!cancelled) setOverview(isRecord(data.overview) ? data.overview : null); })
      .catch(() => { if (!cancelled) setOverview(null); })
      .finally(() => { if (!cancelled) setLoading(false); });
    return () => { cancelled = true; };
  }, [project?.project_id, project?.status, project?.current_stage]);

  if (!project?.project_id) return null;
  const dimensions = isRecord(overview?.dimensions) ? overview!.dimensions : {};
  const truth = isRecord(overview?.truth) ? overview!.truth : {};
  const next = isRecord(overview?.next_best_action) ? overview!.next_best_action : {};
  const blockers = Array.isArray(overview?.blockers) ? overview!.blockers : [];
  const pairs: Array<[string, unknown]> = [
    ["Research", dimensions.research], ["Development", dimensions.development],
    ["Data", dimensions.data], ["Experiment", dimensions.experimentation],
    ["Validation", dimensions.validation], ["Delivery", dimensions.delivery],
  ];

  return (
    <section className="project-intelligence-overview">
      <div className="pio-head">
        <div>
          <span className="pio-kicker">AURA PROJECT INTELLIGENCE</span>
          <h3>How to complete this project</h3>
          <p>Live guidance derived from the current project state, lifecycle dependencies and truth boundary.</p>
        </div>
        <div className="pio-truth">{safeText(truth.status) || (loading ? "SYNCING" : "LIVE")}</div>
      </div>
      <div className="pio-grid">
        {pairs.map(([label, value]) => (
          <div className="pio-dimension" key={String(label)}>
            <div><span>{label}</span><b>{typeof value === "number" ? `${Math.round(value)}%` : "—"}</b></div>
            <div className="pio-track"><i style={{ width: `${Math.max(0, Math.min(100, Number(value) || 0))}%` }} /></div>
          </div>
        ))}
      </div>
      <div className="pio-action">
        <div><span>NEXT BEST ACTION</span><strong>{safeText(next.title) || "Syncing project intelligence…"}</strong><p>{safeText(next.action)}</p></div>
        <div className="pio-action-meta"><b>{safeText(next.where)}</b><small>{Array.isArray(next.blocks) && next.blocks.length ? `Blocks: ${next.blocks.join(" → ")}` : "No downstream blockers identified"}</small></div>
      </div>
      {blockers.length > 0 && (
        <div className="pio-blockers">
          <span>ACTIVE BLOCKERS</span>
          {blockers.slice(0, 4).map((item, i) => {
            const b = isRecord(item) ? item : {};
            return <div key={`${safeText(b.stage)}-${i}`}><b>{safeText(b.title)}</b><small>{safeText(b.reason)}</small></div>;
          })}
        </div>
      )}
    </section>
  );
}

function DecisionIntelligencePanel({ project }: { project: Project | null }) {
  const [data, setData] = useState<Record<string, any> | null>(null);
  const [busy, setBusy] = useState(false);
  const load = async () => {
    if (!project?.project_id) return;
    setBusy(true);
    try {
      const r = await auraFetch(`${API_BASE}/api/aura/projects/${project.project_id}/decision-intelligence`, { cache: "no-store" });
      if (r.ok) {
        const d = await r.json();
        setData(isRecord(d.decision_intelligence) ? d.decision_intelligence : null);
      }
    } finally { setBusy(false); }
  };
  useEffect(() => { load(); }, [project?.project_id, project?.status, project?.current_stage]);
  if (!project?.project_id) return null;
  const risks = Array.isArray(data?.risks) ? data!.risks : [];
  const blockers = Array.isArray(data?.blockers) ? data!.blockers : [];
  const actions = Array.isArray(data?.next_best_actions) ? data!.next_best_actions : [];
  const basis = isRecord(data?.evidence_basis) ? data!.evidence_basis : {};
  return <section className="decision-intelligence-panel">
    <div className="dip2-head">
      <div><span>DECISION INTELLIGENCE · AURA 6.1</span><h3>What should happen next?</h3><p>Deterministic decisions from the current project state, evidence basis, dependencies, risks and blockers.</p></div>
      <button onClick={load} disabled={busy}>{busy ? "SYNCING…" : "REFRESH"}</button>
    </div>
    <div className="dip2-stats">
      <div><b>{safeText(data?.risk_level) || "—"}</b><span>RISK LEVEL</span></div>
      <div><b>{safeText(data?.decision_confidence) || "—"}</b><span>DECISION CONFIDENCE</span></div>
      <div><b>{blockers.length}</b><span>ACTIVE BLOCKERS</span></div>
      <div><b>{actions.length}</b><span>RANKED ACTIONS</span></div>
    </div>
    <div className="dip2-grid">
      <div className="dip2-card"><span>RECOMMENDED ACTION</span><h4>{safeText(data?.recommended_action?.title) || "Syncing decision intelligence…"}</h4><p>{safeText(data?.recommended_action?.action)}</p><small>{safeText(data?.recommended_action?.why_now)}</small></div>
      <div className="dip2-card"><span>EVIDENCE BASIS</span><h4>{Number(basis.approved) || 0} approved · {Number(basis.reviewed) || 0} reviewed</h4><p>{Number(basis.total) || 0} evidence records · {Number(basis.sourced) || 0} sourced/provenanced</p><small>Evidence quality affects decision confidence; it does not create scientific truth.</small></div>
    </div>
    {risks.length > 0 && <div className="dip2-list"><span>RISK REGISTER</span>{risks.slice(0, 5).map((r: any) => <div key={safeText(r.id)}><b>{safeText(r.severity)} · {safeText(r.source)}</b><small>{safeText(r.reason)}</small><em>Mitigation: {safeText(r.mitigation)}</em></div>)}</div>}
    {blockers.length > 0 && <div className="dip2-list"><span>BLOCKERS</span>{blockers.slice(0, 5).map((b: any) => <div key={safeText(b.stage)}><b>{safeText(b.severity)} · {safeText(b.title)}</b><small>{safeText(b.reason)}</small></div>)}</div>}
    <div className="dip2-actions"><span>NEXT BEST ACTION QUEUE</span>{actions.slice(0, 5).map((a: any, i: number) => <div key={safeText(a.id)}><strong>{i + 1}. {safeText(a.title)}</strong><small>{safeText(a.why_now)}</small></div>)}</div>
    <small className="dip2-truth">{safeText(data?.truth) || "Decision Intelligence does not certify scientific validity or project completion."}</small>
  </section>;
}

function InnovationImplementationTraceability({ project }: { project: Project | null }) {
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const load = async () => {
    if (!project?.project_id) return;
    setLoading(true);
    try {
      const r = await auraFetch(`${API_BASE}/api/aura/projects/${project.project_id}/innovation-traceability`, { cache: "no-store" });
      if (!r.ok) throw new Error("Innovation traceability unavailable");
      const j = await r.json(); setData(j.traceability || null);
    } catch { setData(null); } finally { setLoading(false); }
  };
  useEffect(() => { load(); }, [project?.project_id]);
  if (!project) return null;
  const chain = ["innovation","requirement","architecture","implementation","dataset","experiment","result","validation"];
  const counts = data?.counts || {};
  return <section className="aura20-card wide" style={{ marginBottom: 18 }}>
    <div className="aura20-label">INNOVATION → IMPLEMENTATION TRACEABILITY</div>
    <div style={{display:"flex",justifyContent:"space-between",gap:16,alignItems:"center"}}>
      <div><h3>Does the innovation become a real project component?</h3><p>Explicit links connect the innovation to requirements, architecture, implementation, experiments, results and validation.</p></div>
      <button className="aura20-primary" onClick={load} disabled={loading}>{loading ? "CHECKING..." : "REFRESH TRACE"}</button>
    </div>
    {!data ? <p className="aura20-note">Traceability will appear when the project state is available.</p> : <>
      <div className="aci-metrics" style={{marginTop:14}}>
        <div className="aci-metric"><span>COVERAGE</span><strong>{Number(data.coverage_percent || 0).toFixed(0)}%</strong></div>
        <div className="aci-metric"><span>ORPHAN / MISSING</span><strong>{(data.missing_links || []).length}</strong></div>
        <div className="aci-metric"><span>RESULTS</span><strong>{counts.result || 0}</strong></div>
        <div className="aci-metric"><span>VALIDATION</span><strong>{counts.validation || 0}</strong></div>
      </div>
      <div style={{display:"grid",gridTemplateColumns:"repeat(4,minmax(0,1fr))",gap:8,marginTop:14}}>
        {chain.map((key, i) => <div key={key} className="aura20-result"><b>{i+1}. {humanizeKey(key)}</b><span>{counts[key] || 0}</span></div>)}
      </div>
      <p className="aura20-note" style={{marginTop:12}}><b>TRUTH:</b> traceability proves recorded relationships only. It does not prove that implementation was executed, results are scientifically valid, or validation is approved.</p>
    </>}
  </section>;
}

function AuraCommandCenter({
  stage,
  project,
}: {
  stage: string;
  project: Project | null;
}) {
  const evidence = Array.isArray(project?.evidence) ? project.evidence : [];
  const memory = Array.isArray(project?.memory) ? project.memory : [];
  const research = isRecord(project?.research) ? project.research : {};
  const analysis = isRecord(project?.analysis) ? project.analysis : {};
  const innovation = isRecord(project?.innovation) ? project.innovation : {};
  const validation = isRecord(project?.validation) ? project.validation : {};
  const experiments = isRecord(project?.experiments) ? project.experiments : {};
  const verdict = isRecord(analysis.verdict)
    ? analysis.verdict
    : isRecord(project?.analysis?.verdict)
      ? project!.analysis.verdict
      : {};

  const researchClaims = Array.isArray(research.claim_register)
    ? research.claim_register
    : Array.isArray(research.canonical_claims)
      ? research.canonical_claims
      : Array.isArray(research.claims)
        ? research.claims
        : [];

  const claims = Array.isArray(analysis.claim_register) && analysis.claim_register.length
    ? analysis.claim_register
    : Array.isArray(analysis.claims) && analysis.claims.length
      ? analysis.claims
      : researchClaims;

  const researchFindings = Array.isArray(research.canonical_findings)
    ? research.canonical_findings
    : Array.isArray(research.findings)
      ? research.findings
      : [];

  const findings = Array.isArray(analysis.findings) && analysis.findings.length
    ? analysis.findings
    : Array.isArray(analysis.canonical_findings) && analysis.canonical_findings.length
      ? analysis.canonical_findings
      : isRecord(analysis.research_intelligence) && Array.isArray(analysis.research_intelligence.findings) && analysis.research_intelligence.findings.length
        ? analysis.research_intelligence.findings
        : researchFindings;

  const directions = Array.isArray(innovation.directions)
    ? innovation.directions
    : Array.isArray(innovation.candidate_directions)
      ? innovation.candidate_directions
      : [];

  const coverage = Number(
    findValue(analysis, [
      "claim_evidence_coverage_percent",
      "claim_coverage_percent",
      "evidence_coverage_percent",
      "coverage_percent",
    ]) ??
    findValue(isRecord(analysis.claim_analysis) ? analysis.claim_analysis : {}, [
      "coverage_percent",
      "claim_evidence_coverage_percent",
    ]) ??
    findValue(isRecord(analysis.evidence_synthesis) && isRecord(analysis.evidence_synthesis.evidence_base) ? analysis.evidence_synthesis.evidence_base : {}, [
      "coverage_percent",
    ]) ??
    findValue(research, [
      "claim_evidence_coverage_percent",
      "claim_coverage_percent",
      "evidence_coverage_percent",
    ]) ?? 0
  );

  const opportunity = Number(findValue(verdict, ["opportunity_score"]) ?? 0);
  const evidenceScore = Number(findValue(verdict, ["evidence_strength"]) ?? 0);
  const gapScore = Number(findValue(verdict, ["research_gap_strength"]) ?? 0);
  const feasibility = Number(findValue(verdict, ["technical_feasibility"]) ?? 0);
  const novelty = Number(findValue(verdict, ["novelty_confidence"]) ?? 0);

  const sourceNames = ["OpenAlex", "Crossref", "Semantic Scholar", "PubMed", "arXiv", "IEEE Xplore"];
  const sourceCounts = sourceNames.map((name) => {
    const count = evidence.filter((item) => {
      if (!isRecord(item)) return false;
      const source = safeText(item.source || item.provider || item.source_name).toLowerCase();
      return source.includes(name.toLowerCase().split(" ")[0]);
    }).length;
    return { name, count };
  });
  const maxSource = Math.max(...sourceCounts.map((item) => item.count), 1);

  const planned =
    stage === "build" || stage === "experiment" || stage === "validate";
  const executed =
    safeText(validation.execution_status || validation.status).toLowerCase().includes("execut") ||
    safeText(experiments.execution_status).toLowerCase().includes("execut");

  const metricItems = [
    { label: "RESEARCH", value: Array.isArray(research.papers) ? research.papers.length : Math.max(evidence.length, 0) },
    { label: "EVIDENCE", value: evidence.length },
    { label: "CLAIMS", value: claims.length },
    { label: "FINDINGS", value: findings.length },
    { label: "COVERAGE", value: `${Number.isFinite(coverage) ? coverage.toFixed(0) : 0}%` },
  ];

  return (
    <>
    <AuraProjectIntelligenceOverview project={project} />
    <UnifiedProjectIntelligence project={project} />
    <AuraRequirementsAudit />
    <ResultsObservatoryPanel project={project} />
    <ReproducibilityLineagePanel project={project} />
    <DecisionIntelligencePanel project={project} />
    <section className="aura-command-insights">
      <div className="aci-head">
        <div>
          <span className="aci-kicker">AURA COMMAND CENTER</span>
          <h3>Evidence-driven project intelligence</h3>
          <p>
            AURA connects research, evidence, decisions, innovation and execution truth into one project intelligence layer.
          </p>
        </div>
        <div className="aci-state"><i /> LIVE PROJECT GRAPH</div>
      </div>

      <div className="aci-metrics">
        {metricItems.map((item) => (
          <div className="aci-metric" key={item.label}>
            <span>{item.label}</span>
            <strong>{item.value}</strong>
          </div>
        ))}
      </div>

      {stage === "verdict" && (
        <div className="aci-verdict">
          <div className="aci-section-title">AURA VERDICT SIGNALS</div>
          <div className="aci-verdict-grid">
            <div className="aci-score-list">
              {[
                ["Evidence strength", evidenceScore],
                ["Research-gap strength", gapScore],
                ["Technical feasibility", feasibility],
                ["Novelty confidence", novelty],
                ["Opportunity score", opportunity],
              ].map(([label, value]) => (
                <div className="aci-score" key={String(label)}>
                  <div><span>{label}</span><b>{Number(value)}%</b></div>
                  <div className="aci-track"><i style={{ width: `${Math.max(0, Math.min(100, Number(value)))}%` }} /></div>
                </div>
              ))}
            </div>
            <div className="aci-verdict-core">
              <span>OPPORTUNITY</span>
              <strong>{Number.isFinite(opportunity) ? opportunity : 0}</strong>
              <small>AURA ranking signal</small>
            </div>
          </div>
        </div>
      )}

      {stage === "investigate" && (
        <div className="aci-research">
          <div className="aci-section-title">RESEARCH SOURCE SIGNALS</div>
          <div className="aci-source-bars">
            {sourceCounts.map((item) => (
              <div className="aci-source" key={item.name}>
                <div><span>{item.name}</span><b>{item.count}</b></div>
                <div className="aci-track"><i style={{ width: `${(item.count / maxSource) * 100}%` }} /></div>
              </div>
            ))}
          </div>
          <div className="aci-note">Source availability is shown from the current investigation corpus. Retrieval is not the same as scientific verification.</div>
        </div>
      )}

      {stage === "innovate" && (
        <div className="aci-flow">
          <div className="aci-section-title">RESEARCH → INNOVATION CHAIN</div>
          <div className="aci-flow-row">
            {[
              ["RESEARCH GAP", gapScore || "—"],
              ["OPPORTUNITY", opportunity || "—"],
              ["DIRECTIONS", directions.length || "—"],
              ["VALIDATION", "REQUIRED"],
            ].map(([title, value], index) => (
              <div className="aci-flow-node" key={String(title)}>
                <span>0{index + 1}</span>
                <b>{title}</b>
                <strong>{value}</strong>
                {index < 3 && <i>→</i>}
              </div>
            ))}
          </div>
        </div>
      )}

      {planned && (
        <div className={`aci-truth ${executed ? "truth-executed" : "truth-planned"}`}>
          <div className="aci-truth-icon">{executed ? "✓" : "!"}</div>
          <div>
            <strong>{executed ? "EXECUTION RECORDED — REVIEW REQUIRED" : "DESIGNED BUT NOT EXECUTED"}</strong>
            <p>
              {executed
                ? "AURA has an execution record, but results still require review and evidence validation."
                : "AURA has prepared the development/experiment/validation path. No execution result is being fabricated or presented as verified."}
            </p>
          </div>
        </div>
      )}

      {stage === "deliver" && (
        <div className="aci-delivery">
          <div>
            <span className="aci-section-title">DELIVERY INTELLIGENCE</span>
            <h4>One project graph. Multiple outputs.</h4>
            <p>Reports, papers, presentations, demos, viva material and SIH outputs should all derive from the same evidence-backed project context.</p>
          </div>
          <div className="aci-delivery-stats">
            <div><b>{memory.length}</b><span>MEMORY EVENTS</span></div>
            <div><b>{evidence.length}</b><span>EVIDENCE RECORDS</span></div>
            <div><b>{findings.length}</b><span>FINDINGS</span></div>
          </div>
        </div>
      )}
    </section>
    </>
  );
}


function BuildExecutionCenter({ project }: { project: Project | null }) {
  const [build, setBuild] = useState<any>(null);
  const [executions, setExecutions] = useState<any[]>([]);
  const [results, setResults] = useState<any>(null);
  const [busy, setBusy] = useState<string | null>(null);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [workspaceFiles, setWorkspaceFiles] = useState<string[]>([]);
  const [workspaceOpen, setWorkspaceOpen] = useState(false);
  const [workspaceFile, setWorkspaceFile] = useState<string | null>(null);
  const [workspaceContent, setWorkspaceContent] = useState("");

  const projectId = project?.project_id || "";

  async function loadBuild() {
    if (!projectId) return;
    try {
      const r = await auraFetch(`${API_BASE}/api/aura/projects/${projectId}/build`, { cache: "no-store" });
      const d = await r.json().catch(() => ({}));
      if (r.ok) {
        setBuild(d.build || null);
        return;
      }
      // Recover browser-only projects automatically instead of showing
      // "project not found" when the backend has restarted.
      if (r.status === 404 && project) {
        await syncProjectToBackend();
        const retry = await auraFetch(`${API_BASE}/api/aura/projects/${projectId}/build`, { cache: "no-store" });
        const retryData = await retry.json().catch(() => ({}));
        if (retry.ok) setBuild(retryData.build || null);
      }
    } catch {}
  }

  async function loadResults() {
    try {
      const r = await auraFetch(`${API_BASE}/api/aura/projects/${projectId}/results`);
      const d = await r.json();
      if (r.ok) setResults(d.results || null);
    } catch {}
  }
  useEffect(() => {
    if (!projectId) {
      setBuild(null);
      setExecutions([]);
      setResults(null);
      return;
    }
    void Promise.all([loadBuild(), loadExecutions(), loadResults()]);
  }, [projectId]);

  async function loadExecutions() {
    try {
      const r = await auraFetch(`${API_BASE}/api/aura/projects/${projectId}/executions`);
      const d = await r.json();
      setExecutions(Array.isArray(d.executions) ? d.executions : []);
    } catch {}
  }
  async function syncProjectToBackend() {
    if (!projectId || !project) return false;
    const r = await auraFetch(`${API_BASE}/api/aura/projects/${projectId}/snapshot`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(project),
    });
    if (!r.ok) {
      const d = await r.json().catch(() => ({}));
      throw new Error(d.detail || "AURA could not synchronize the project workspace.");
    }
    return true;
  }

  async function callBuild() {
    setBusy("build"); setError("");
    try {
      // Browser-saved projects can outlive the backend process. Restore the exact
      // project snapshot first so BUILD never runs against a phantom project ID.
      await syncProjectToBackend();
      const r = await auraFetch(`${API_BASE}/api/aura/projects/${projectId}/build`, { method: "POST" });
      const d = await r.json(); if (!r.ok) throw new Error(d.detail || "Build failed");
      setBuild(d.build);
      await Promise.all([loadExecutions(), loadResults(), loadBuild()]);
      setNotice("WORKSPACE GENERATED → STARTING CONTROLLED SMOKE TEST…");
      const smoke = await auraFetch(`${API_BASE}/api/aura/projects/${projectId}/executions`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ task: "smoke_test", timeout_seconds: 300 }) });
      const smokeData = await smoke.json().catch(() => ({}));
      if (!smoke.ok) throw new Error(smokeData.detail || "Smoke test failed to start");
      setNotice(`SMOKE TEST → ${smokeData.execution?.status || "EXECUTED"}`);
      await Promise.all([loadExecutions(), loadResults(), loadBuild()]);
    } catch (e) { setError(e instanceof Error ? e.message : "Build failed"); }
    finally { setBusy(null); }
  }
  async function runTask(task: string) {
    setBusy(task); setError(""); setNotice("");
    try {
      if (!build?.workspace) throw new Error("Generate the real project workspace before running this task.");
      const r = await auraFetch(`${API_BASE}/api/aura/projects/${projectId}/executions`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ task, timeout_seconds: 300 }) });
      const d = await r.json().catch(() => ({}));
      if (!r.ok) throw new Error(d.detail || "Execution failed");
      const execution = d.execution || {};
      setNotice(`${String(execution.task || task).split("_").join(" ").toUpperCase()} → ${execution.status || "COMPLETED"}${execution.exit_code !== undefined && execution.exit_code !== null ? ` · exit ${execution.exit_code}` : ""}`);
      await Promise.all([loadExecutions(), loadResults(), loadBuild()]);
    } catch (e) { setError(e instanceof Error ? e.message : "Execution failed"); }
    finally { setBusy(null); }
  }

  async function runCompleteVerification() {
    setError(""); setNotice(""); setBusy("verification");
    try {
      const r = await auraFetch(`${API_BASE}/api/aura/projects/${projectId}/verification/run`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ use_development_fixture: true }) });
      const d = await r.json().catch(() => ({}));
      if (!r.ok) throw new Error(d.detail || "Complete verification failed.");
      setNotice(d.verification?.passed ? "COMPLETE ENGINEERING VERIFICATION PASSED — synthetic fixture only; not scientific evidence." : "Verification stopped; inspect the execution record.");
      await Promise.all([loadExecutions(), loadResults(), loadBuild()]);
    } catch (e) { setError(e instanceof Error ? e.message : "Complete verification failed"); }
    finally { setBusy(null); }
  }

  async function openWorkspace() {
    setError("");
    try {
      const r = await auraFetch(`${API_BASE}/api/aura/projects/${projectId}/workspace`);
      const d = await r.json().catch(() => ({}));
      if (!r.ok) throw new Error(d.detail || "Workspace could not be opened.");
      setWorkspaceFiles(Array.isArray(d.files) ? d.files : []);
      setWorkspaceOpen(true);
    } catch (e) { setError(e instanceof Error ? e.message : "Workspace could not be opened."); }
  }

  async function openWorkspaceFile(file: string) {
    try {
      const r = await auraFetch(`${API_BASE}/api/aura/projects/${projectId}/workspace/file?path=${encodeURIComponent(file)}`);
      const d = await r.json().catch(() => ({}));
      if (!r.ok) throw new Error(d.detail || "File could not be opened.");
      setWorkspaceFile(file); setWorkspaceContent(String(d.content || ""));
    } catch (e) { setError(e instanceof Error ? e.message : "File could not be opened."); }
  }

  if (!projectId) return null;

  const latest = executions[0];
  const comparison: Record<string, any> =
    results?.comparison && typeof results.comparison === "object" && !Array.isArray(results.comparison)
      ? results.comparison as Record<string, any>
      : {};
  const metricRows: string[] =
    Array.isArray(results?.evaluation_metrics) && results.evaluation_metrics.length
      ? results.evaluation_metrics.filter((metric: unknown): metric is string => typeof metric === "string")
      : Object.keys(comparison);
  const proposed = results?.proposed?.metrics || {};
  const baseline = results?.baseline?.metrics || {};
  const status = String(results?.status || "NOT_EXECUTED");
  const hasMeasured = Boolean(results?.proposed_executed);

  return <section className="build-execution-center">
    <div className="bec-head"><div><span className="aci-section-title">AURA BUILD & EXECUTION CORE</span><h3>Build the actual project — then execute it.</h3><p>AURA separates generated documentation from the real project workspace, controlled execution, measured results and validation evidence.</p></div><div className="bec-state">{build?.status === "READY" || build?.workspace ? "WORKSPACE READY" : "BUILD REQUIRED"}</div></div>
    <div className="bec-flow"><span>WORKSPACE</span><b>→</b><span>CODE</span><b>→</b><span>TEST</span><b>→</b><span>EXPERIMENT</span><b>→</b><span>RESULTS</span><b>→</b><span>VALIDATION</span><b>→</b><span>DELIVERY</span></div>
    <div className="bec-actions">
      <button type="button" onClick={callBuild} disabled={busy !== null}>{busy === "build" ? "GENERATING…" : "GENERATE REAL PROJECT WORKSPACE"}</button>
      {(build?.status === "READY" || Boolean(build?.workspace)) && <>
        <button type="button" onClick={openWorkspace} disabled={busy !== null}>OPEN WORKSPACE</button>
        <button type="button" onClick={() => runTask("smoke_test")} disabled={busy !== null}>{busy === "smoke_test" ? "RUNNING…" : "RUN SMOKE TEST"}</button>
        <button type="button" onClick={() => runTask("project_test")} disabled={busy !== null}>{busy === "project_test" ? "RUNNING…" : "RUN PROJECT TESTS"}</button>
        <button type="button" className="bec-primary-action" onClick={runCompleteVerification} disabled={busy !== null}>{busy === "verification" ? "VERIFYING…" : "RUN COMPLETE ENGINEERING VERIFICATION"}</button>
        <button type="button" onClick={() => runTask("dataset_prepare")} disabled={busy !== null}>{busy === "dataset_prepare" ? "CHECKING…" : "PREPARE DATASET"}</button>
        <button type="button" onClick={() => runTask("baseline_evaluate")} disabled={busy !== null || results?.dataset?.status !== "READY"}>EVALUATE BASELINE</button>
        <button type="button" onClick={() => runTask("train_model")} disabled={busy !== null || results?.dataset?.status !== "READY"}>RUN PROPOSED TRAINING</button>
        <button type="button" onClick={() => runTask("evaluate_model")} disabled={busy !== null || results?.training?.status !== "EXECUTED"}>EVALUATE PROPOSED</button>
        <button type="button" onClick={() => runTask("experiment_run")} disabled={busy !== null || results?.dataset?.status !== "READY"}>{busy === "experiment_run" ? "RUNNING…" : "RUN FULL EXPERIMENT"}</button>
      </>}
    </div>
    {error && <div className="bec-error">{error}</div>}
    {notice && <div className="bec-notice">{notice}</div>}
    {build && <div className="bec-workspace"><div><strong>PROJECT PROFILE</strong><span>{humanizeKey(String(build.profile || "general_ai"))}</span></div><div><strong>FILES GENERATED</strong><span>{build.files?.length || 0}</span></div><div><strong>WORKSPACE</strong><span>{build.workspace}</span></div></div>}

    {workspaceOpen && <div className="bec-workspace-modal" role="dialog" aria-modal="true" aria-label="AURA project workspace">
      <div className="bec-workspace-modal-inner">
        <div className="bec-workspace-modal-head"><div><span className="aci-section-title">REAL PROJECT WORKSPACE</span><h4>{build?.workspace || "AURA workspace"}</h4></div><button type="button" onClick={() => { setWorkspaceOpen(false); setWorkspaceFile(null); }}>CLOSE</button></div>
        <div className="bec-workspace-browser">
          <div className="bec-file-list">{workspaceFiles.map((file) => <button type="button" key={file} className={workspaceFile === file ? "active" : ""} onClick={() => openWorkspaceFile(file)}>{file}</button>)}</div>
          <pre className="bec-file-content">{workspaceFile ? workspaceContent : "Select a generated workspace file to inspect it."}</pre>
        </div>
      </div>
    </div>}

    <div className="bec-results-panel">
      <div className="bec-results-head"><div><span className="aci-section-title">AURA RESULTS OBSERVATORY</span><h4>Measured project results — never inferred.</h4></div><span className={`bec-results-status ${status.toLowerCase()}`}>{status.split("_").join(" ")}</span></div>
      <div className="bec-results-truth">{hasMeasured ? "REAL METRICS CAPTURED FROM CONTROLLED EVALUATION — REVIEW REQUIRED" : "NO MEASURED PERFORMANCE RESULT YET — AURA WILL NOT FABRICATE ONE"}</div>
      <div className="bec-result-grid">
        <div className="bec-result-card"><span>DATASET</span><strong>{results?.dataset?.status || "NOT AVAILABLE"}</strong><small>{results?.dataset?.rows !== undefined ? `${results?.dataset?.rows ?? 0} rows detected` : `${results?.dataset?.files_found ?? 0} files detected`}</small></div>
        <div className="bec-result-card"><span>BASELINE</span><strong>{results?.baseline_executed ? "EXECUTED" : "NOT EXECUTED"}</strong><small>{results?.baseline_executed ? "Measured baseline available" : "Run the project-approved baseline evaluation"}</small></div>
        <div className="bec-result-card"><span>PROPOSED</span><strong>{results?.proposed_executed ? "EVALUATED" : "NOT EVALUATED"}</strong><small>{results?.proposed_executed ? "Measured proposed metrics available" : "Run the project-approved proposed evaluation"}</small></div>
        <div className="bec-result-card"><span>VALIDATION</span><strong>REVIEW REQUIRED</strong><small>AURA does not self-certify scientific validity</small></div>
      </div>
      <div className="bec-metric-table">
        <div className="bec-metric-row bec-metric-header"><span>METRIC</span><span>BASELINE</span><span>PROPOSED</span><span>Δ</span></div>
        {metricRows.map((metric) => {
          const row = comparison[metric];
          const b = row?.baseline ?? baseline?.[metric];
          const pr = row?.proposed ?? proposed?.[metric];
          const delta = row?.delta;
          return <div className="bec-metric-row" key={metric}><span>{metric.split("_").join(" ").toUpperCase()}</span><span>{typeof b === "number" ? b.toFixed(4) : "—"}</span><span>{typeof pr === "number" ? pr.toFixed(4) : "—"}</span><span>{typeof delta === "number" ? `${delta >= 0 ? "+" : ""}${delta.toFixed(4)}` : "—"}</span></div>;
        })}
      </div>
    </div>

    {latest && <div className="bec-result"><div className="bec-result-head"><strong>EXECUTION {latest.execution_id}</strong><span className={`bec-status ${String(latest.status).toLowerCase()}`}>{latest.status}</span></div><div className="bec-metrics"><span>Task <b>{latest.task}</b></span><span>Exit <b>{latest.exit_code ?? "—"}</b></span><span>Duration <b>{latest.duration_seconds}s</b></span><span>Scientific validation <b>NO</b></span></div><pre>{latest.stdout || latest.stderr || latest.error || "No output."}</pre></div>}
    <div className="bec-truth"><strong>EXECUTION TRUTH</strong><p>Training and evaluation results are displayed only when produced by controlled execution. A missing baseline is not replaced with an estimate. Measured metrics are evidence, not automatic scientific validation.</p></div>
  </section>;
}

function DeliveryStudio({ project }: { project: Project | null }) {
  const [view, setView] = useState("overview");
  const [selectedOutput, setSelectedOutput] = useState<string | null>(null);
  const [generatedFiles, setGeneratedFiles] = useState<Record<string, boolean>>(() =>
    isRecord(project?.deliverables?.actual_file_generation)
      ? Object.fromEntries(Object.entries(project?.deliverables?.actual_file_generation as Record<string, unknown>).map(([k, v]) => [k, v === true]))
      : {}
  );
  const [generatingFile, setGeneratingFile] = useState<string | null>(null);
  const [generationError, setGenerationError] = useState("");
  const [completeReport, setCompleteReport] = useState<any>(null);

  useEffect(() => {
    if (!project?.project_id) { setCompleteReport(null); return; }
    auraFetch(`${API_BASE}/api/aura/projects/${project.project_id}/report/complete`)
      .then((r) => r.ok ? r.json() : null)
      .then((d) => setCompleteReport(d?.report || null))
      .catch(() => setCompleteReport(null));
  }, [project?.project_id]);

  const delivery = isRecord(project?.deliverables) ? project.deliverables : {};
  const evidence = Array.isArray(project?.evidence) ? project.evidence : [];
  const memory = Array.isArray(project?.memory) ? project.memory : [];
  const analysis = isRecord(project?.analysis) ? project.analysis : {};
  const validation = isRecord(project?.validation) ? project.validation : {};

  const research = isRecord(project?.research) ? project.research : {};
  const claimCoverage = Number(
    findValue(analysis, [
      "claim_evidence_coverage_percent",
      "claim_coverage_percent",
      "evidence_coverage_percent",
    ]) ?? findValue(research, [
      "claim_evidence_coverage_percent",
      "claim_coverage_percent",
      "evidence_coverage_percent",
    ]) ?? 0
  );

  const researchRecords = Number(
    findValue(delivery, ["research_records", "research_count", "references"]) ?? 0
  );

  const actualFiles = isRecord(delivery.actual_file_generation)
    ? delivery.actual_file_generation
    : {};
  const truthStatus = getProjectTruthStatus(project);

  type OutputSection = [string, unknown];
  type OutputCard = {
    id: string;
    title: string;
    subtitle: string;
    state: string;
    icon: string;
    sections: OutputSection[];
  };

  const outputCards: OutputCard[] = [
    {
      id: "report",
      title: "COMPLETE PROJECT REPORT",
      subtitle: "14-chapter end-to-end technical report",
      state: completeReport?.truth_status === "SCIENTIFICALLY_COMPLETE" ? "SCIENTIFICALLY COMPLETE" : "GATED / PROJECT IN PROGRESS",
      icon: "▤",
      sections: completeReport?.chapters?.length
        ? completeReport.chapters.map((chapter: any) => [`CHAPTER ${chapter.number}: ${chapter.title}`, chapter.sections || []])
        : [
            ["PROJECT", project?.original_idea || "Project idea"],
            ["PROBLEM UNDERSTANDING", project?.analysis?.problem_understanding || project?.analysis || {}],
            ["RESEARCH", project?.research || {}],
            ["SOLUTION", project?.solution || {}],
            ["ARCHITECTURE", project?.architecture || {}],
            ["DEVELOPMENT", project?.development || {}],
            ["EXPERIMENTS", project?.experiments || {}],
            ["VALIDATION", project?.validation || {}],
          ],
    },
    {
      id: "paper",
      title: "RESEARCH PAPER",
      subtitle: "Evidence-aware manuscript draft",
      state: "REVIEW REQUIRED",
      icon: "◈",
      sections: [
        ["TITLE", project?.project_name || project?.original_idea || "AURA Research Project"],
        ["ABSTRACT / CONTEXT", project?.original_idea || ""],
        ["RESEARCH EVIDENCE", project?.research || {}],
        ["RESEARCH ANALYSIS", project?.analysis || {}],
        ["INNOVATION", project?.innovation || {}],
        ["LIMITATIONS & VERIFICATION", project?.validation || {}],
      ],
    },
    {
      id: "presentation",
      title: "PRESENTATION",
      subtitle: "Research-to-demo narrative",
      state: "CONTENT READY",
      icon: "▥",
      sections: [
        ["SLIDE 01 — PROJECT", project?.project_name || project?.original_idea || ""],
        ["SLIDE 02 — PROBLEM", project?.analysis?.problem_understanding || {}],
        ["SLIDE 03 — EXISTING WORK", project?.research || {}],
        ["SLIDE 04 — AURA VERDICT", project?.analysis || {}],
        ["SLIDE 05 — INNOVATION", project?.innovation || {}],
        ["SLIDE 06 — SOLUTION", project?.solution || {}],
        ["SLIDE 07 — ARCHITECTURE", project?.architecture || {}],
        ["SLIDE 08 — BUILD & EXPERIMENT", { development: project?.development, experiments: project?.experiments }],
        ["SLIDE 09 — VALIDATION", project?.validation || {}],
        ["SLIDE 10 — DEMO / CONCLUSION", { deliverables: project?.deliverables }],
      ],
    },
    {
      id: "sih",
      title: "SIH / HACKATHON",
      subtitle: "Pitch and judging narrative",
      state: "CONTENT READY",
      icon: "✦",
      sections: [
        ["PROBLEM", project?.original_idea || ""],
        ["WHY IT MATTERS", project?.analysis || {}],
        ["PROPOSED SOLUTION", project?.solution || {}],
        ["INNOVATION", project?.innovation || {}],
        ["TECHNICAL ARCHITECTURE", project?.architecture || {}],
        ["FEASIBILITY & BUILD", project?.development || {}],
        ["VALIDATION PLAN", project?.validation || {}],
        ["DEMO BOUNDARY", "AURA has prepared the demonstration plan. No unexecuted performance result is presented as verified."],
      ],
    },
    {
      id: "demo",
      title: "DEMO SCRIPT",
      subtitle: "Controlled demonstration sequence",
      state: "PLANNED",
      icon: "▶",
      sections: [
        ["DEMO OBJECTIVE", project?.original_idea || ""],
        ["STEP 01 — INPUT", "Provide representative real or controlled input."],
        ["STEP 02 — PROCESSING", project?.architecture || project?.solution || {}],
        ["STEP 03 — AI / INTELLIGENCE", project?.innovation || {}],
        ["STEP 04 — OUTPUT", "Display the system output produced by an actual implementation."],
        ["STEP 05 — VALIDATION", project?.experiments || project?.validation || {}],
        ["IMPORTANT", "A live demonstration is not scientific proof. Quantitative claims require executed experiments."],
      ],
    },
    {
      id: "dataset_report",
      title: "DATASET REPORT",
      subtitle: "Dataset inventory, quality and provenance",
      state: "GATED BY REAL DATA",
      icon: "◫",
      sections: [["DATASET", completeReport?.datasets || "Upload the real project dataset to populate this report."], ["TRUTH", "Dataset profiling is not scientific validation."]],
    },
    {
      id: "results_report",
      title: "RESULTS REPORT",
      subtitle: "Measured baseline vs proposed results",
      state: completeReport?.results?.proposed_executed ? "MEASURED / REVIEW REQUIRED" : "NOT EXECUTED",
      icon: "▥",
      sections: [["RESULTS", completeReport?.results || "No measured results yet."], ["TRUTH", "Metrics are included only when produced by controlled execution."]],
    },
    {
      id: "experiment_report",
      title: "EXPERIMENT REPORT",
      subtitle: "Hypothesis, baseline, proposed model and reproducibility",
      state: "EXECUTION DEPENDENT",
      icon: "∿",
      sections: [["EXPERIMENT", completeReport?.results?.experiment || project?.experiments || {}]],
    },
    {
      id: "traceability_report",
      title: "TRACEABILITY REPORT",
      subtitle: "Evidence → claims → execution → validation",
      state: "PROVENANCE",
      icon: "⌬",
      sections: [["LIFECYCLE", completeReport?.lifecycle || {}], ["EVIDENCE", project?.evidence || []], ["COMPLETION", completeReport?.completion || {}]],
    },
    {
      id: "completion_report",
      title: "COMPLETION REPORT",
      subtitle: "Final gates and scientific completion certificate",
      state: completeReport?.scientific_completion ? "COMPLETE" : "GATES REMAIN",
      icon: "✓",
      sections: [["COMPLETION", completeReport?.completion || project?.completion || {}], ["TRUTH STATUS", completeReport?.truth_status || "DESIGNED_OR_IN_PROGRESS"]],
    },
    {
      id: "viva",
      title: "VIVA PREPARATION",
      subtitle: "Evidence-grounded questions",
      state: "CONTENT READY",
      icon: "?",
      sections: [
        ["Q1 — WHAT IS THE PROBLEM?", project?.original_idea || ""],
        ["Q2 — WHAT DID AURA FIND?", project?.research || {}],
        ["Q3 — WHAT IS THE RESEARCH GAP?", project?.analysis || {}],
        ["Q4 — WHAT IS YOUR INNOVATION?", project?.innovation || {}],
        ["Q5 — HOW DOES THE SYSTEM WORK?", project?.architecture || project?.solution || {}],
        ["Q6 — HOW WILL YOU VALIDATE IT?", project?.experiments || project?.validation || {}],
        ["Q7 — WHAT HAS ACTUALLY BEEN VERIFIED?", validation || "Execution boundaries remain explicit."],
      ],
    },
  ];

  const selected = outputCards.find((card) => card.id === selectedOutput) || null;

  const executionTruth =
    safeText(findValue(validation, ["important_note", "execution_warning", "final_statement"])) ||
    "Actual implementation, experiments, quantitative results and deployment remain execution-dependent.";

  function valueToText(value: unknown, depth = 0): string {
    if (value === null || value === undefined) return "Not available.";
    if (typeof value === "string" || typeof value === "number" || typeof value === "boolean") return String(value);
    if (Array.isArray(value)) {
      if (!value.length) return "No records.";
      return value.slice(0, 12).map((item, i) => `${i + 1}. ${valueToText(item, depth + 1)}`).join("\n");
    }
    if (isRecord(value)) {
      const entries = Object.entries(value).slice(0, 18);
      if (!entries.length) return "No structured data.";
      return entries.map(([key, item]) => {
        const rendered = valueToText(item, depth + 1);
        return `${humanizeKey(key)}: ${rendered}`;
      }).join("\n");
    }
    return String(value);
  }

  function openOutput(id: string) {
    setSelectedOutput(id);
    setView("outputs");
    window.setTimeout(() => document.getElementById("aura-output-detail")?.scrollIntoView({ behavior: "smooth", block: "start" }), 50);
  }

  async function downloadOutput(id: string) {
    const card = outputCards.find((item) => item.id === id);
    if (!card) return;
    const content = [
      `AURA — ${card.title}`,
      `Project: ${project?.project_name || project?.original_idea || "AURA Project"}`,
      `Generated from current AURA project state.`,
      `Execution truth: prepared content is not proof of execution.`,
      "",
      ...card.sections.map(([title, value]) => `## ${title}\n${valueToText(value)}`),
    ].join("\n\n");
    const blob = new Blob([content], { type: "text/plain;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const anchor = document.createElement("a");
    anchor.href = url; anchor.download = `AURA_${card.id}_draft.txt`; anchor.click();
    URL.revokeObjectURL(url);
  }

  async function generateFile(kind: string) {
    if (!project?.project_id) { setGenerationError("No active AURA project is available."); return; }
    setGeneratingFile(kind); setGenerationError("");
    try {
      // The backend persists projects, but this sync also restores a browser-saved
      // project after a backend restart before any file is generated.
      const syncResponse = await auraFetch(`${API_BASE}/api/aura/projects/${project.project_id}/snapshot`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(project),
      });
      if (!syncResponse.ok) {
        const syncDetail = await syncResponse.text();
        throw new Error(syncDetail || "AURA project synchronization failed.");
      }

      const endpointKind = kind === "docx" ? "report" : kind === "pptx" ? "presentation" : kind;
      const endpoint = kind === "zip"
        ? `${API_BASE}/api/aura/projects/${project.project_id}/package`
        : `${API_BASE}/api/aura/projects/${project.project_id}/deliverables/${endpointKind}`;
      const response = await fetch(endpoint);
      if (!response.ok) {
        const detail = await response.text();
        throw new Error(detail || "AURA file generation failed.");
      }
      const blob = await response.blob();
      const disposition = response.headers.get("content-disposition") || "";
      const match = disposition.match(/filename="?([^";]+)"?/i);
      const filename = match?.[1] || `AURA_${kind}`;
      const url = URL.createObjectURL(blob);
      const anchor = document.createElement("a");
      anchor.href = url; anchor.download = filename; anchor.click();
      URL.revokeObjectURL(url);
      setGeneratedFiles((current) => ({ ...current, [kind]: true }));
    } catch (error) {
      setGenerationError(error instanceof Error ? error.message : "AURA file generation failed.");
    } finally {
      setGeneratingFile(null);
    }
  }

  const fileStates = [
    { key: "docx", label: "COMPLETE REPORT · DOCX", icon: "▤" },
    { key: "pdf", label: "COMPLETE REPORT · PDF", icon: "▧" },
    { key: "pptx", label: "PRESENTATION · PPTX", icon: "▥" },
    { key: "dataset_report", label: "DATASET REPORT", icon: "◫" },
    { key: "results_report", label: "RESULTS REPORT", icon: "▥" },
    { key: "experiment_report", label: "EXPERIMENT REPORT", icon: "∿" },
    { key: "traceability_report", label: "TRACEABILITY REPORT", icon: "⌬" },
    { key: "completion_report", label: "COMPLETION REPORT", icon: "✓" },
    { key: "zip", label: "COMPLETE PROJECT PACKAGE", icon: "◈" },
  ];

  const fileReadyCount = fileStates.filter((item) => generatedFiles[item.key] === true || actualFiles[item.key] === true).length;

  return (
    <section className="delivery-studio" aria-label="AURA Delivery Studio">
      <div className="delivery-studio-top">
        <div>
          <div className="delivery-kicker">AURA DELIVERY STUDIO</div>
          <h3>Turn the project knowledge graph into a delivery package.</h3>
          <p>Every output below is generated from the current project context. Open an output to inspect its actual content before generation.</p>
        </div>
        <div className="delivery-live"><span /> DELIVERY CONTROL</div>
      </div>

      <div className="delivery-tabs" role="tablist" aria-label="Delivery views">
        {[["overview", "OVERVIEW"], ["outputs", "OUTPUTS"], ["evidence", "EVIDENCE"], ["execution", "EXECUTION TRUTH"]].map(([id, label]) => (
          <button key={id} type="button" role="tab" aria-selected={view === id} className={view === id ? "active" : ""} onClick={() => setView(id)}>
            {label}
          </button>
        ))}
      </div>

      {view === "overview" && (
        <div className="delivery-overview">
          <div className="delivery-hero-card">
            <div className="delivery-orbit"><span className="delivery-orbit-core">A</span><i /><i /><i /></div>
            <div>
              <span className="delivery-mini-label">PROJECT DELIVERY STATE</span>
              <strong>{truthStatus.label}</strong>
              <p>{truthStatus.detail} One project context. Multiple outputs. One provenance chain.</p>
            </div>
          </div>
          <div className="delivery-metric-grid">
            <div><span>RESEARCH</span><strong>{researchRecords || evidence.length || "—"}</strong><small>records</small></div>
            <div><span>EVIDENCE</span><strong>{evidence.length}</strong><small>records</small></div>
            <div><span>TRACEABILITY</span><strong>{claimCoverage ? `${claimCoverage.toFixed(1)}%` : "—"}</strong><small>claim coverage</small></div>
            <div><span>MEMORY</span><strong>{memory.length}</strong><small>events</small></div>
          </div>
          <div className="delivery-output-grid">
            {outputCards.slice(0, 6).map((card) => (
              <button key={card.id} type="button" className="delivery-output-card" onClick={() => openOutput(card.id)}>
                <span className="delivery-output-icon">{card.icon}</span>
                <span className="delivery-output-title">{card.title}</span>
                <span className="delivery-output-subtitle">{card.subtitle}</span>
                <span className="delivery-output-state">{card.state}</span>
                <span className="delivery-open-hint">OPEN CONTENT →</span>
              </button>
            ))}
          </div>
        </div>
      )}

      {view === "outputs" && (
        <div className="delivery-output-detail" id="aura-output-detail">
          <div className="delivery-section-heading"><span>OUTPUT MATRIX</span><strong>{outputCards.length} delivery targets</strong></div>

          {selected ? (
            <div className="selected-output-panel">
              <div className="selected-output-header">
                <div>
                  <span className="delivery-output-icon">{selected.icon}</span>
                  <div>
                    <small>AURA OUTPUT</small>
                    <h4>{selected.title}</h4>
                    <p>{selected.subtitle}</p>
                  </div>
                </div>
                <button type="button" className="output-close-button" onClick={() => setSelectedOutput(null)}>← ALL OUTPUTS</button>
              </div>

              <div className="selected-output-notice">
                <strong>{selected.state}</strong>
                <span>PROVENANCE PRESERVED</span>
                <span>HUMAN REVIEW REQUIRED</span>
              </div>

              <div className="selected-output-content">
                {selected.sections.map(([title, value]) => (
                  <article key={title}>
                    <div>{title}</div>
                    <pre>{valueToText(value)}</pre>
                  </article>
                ))}
              </div>

              <div className="selected-output-actions">
                <button type="button" onClick={() => downloadOutput(selected.id)}>DOWNLOAD DRAFT (.TXT)</button>
                {selected.id === "report" && <button type="button" onClick={() => generateFile("docx")} disabled={generatingFile !== null}>{generatingFile === "docx" ? "GENERATING…" : "GENERATE DOCX"}</button>}
                {selected.id === "report" && <button type="button" onClick={() => generateFile("pdf")} disabled={generatingFile !== null}>{generatingFile === "pdf" ? "GENERATING…" : "GENERATE PDF"}</button>}
                {selected.id === "presentation" && <button type="button" onClick={() => generateFile("pptx")} disabled={generatingFile !== null}>{generatingFile === "pptx" ? "GENERATING…" : "GENERATE PPTX"}</button>}
                {["dataset_report","results_report","experiment_report","traceability_report","completion_report"].includes(selected.id) && <button type="button" onClick={() => generateFile(selected.id)} disabled={generatingFile !== null}>{generatingFile === selected.id ? "GENERATING…" : "GENERATE REPORT FILE"}</button>}
                <button type="button" onClick={() => generateFile("zip")} disabled={generatingFile !== null}>{generatingFile === "zip" ? "PACKAGING…" : "GENERATE COMPLETE PROJECT ZIP"}</button>
                <span>Files are generated from the current AURA project state. Generated files are not scientific verification of unexecuted experiments.</span>
              </div>
            </div>
          ) : (
            <div className="delivery-detail-grid">
              {outputCards.map((card) => (
                <article key={card.id} className="delivery-detail-card">
                  <button type="button" className="delivery-card-clickarea" onClick={() => openOutput(card.id)}>
                    <div className="delivery-detail-head">
                      <span className="delivery-output-icon">{card.icon}</span>
                      <div><strong>{card.title}</strong><span>{card.subtitle}</span></div>
                      <em>{card.state}</em>
                    </div>
                    <p>Open this output to inspect the project-derived content.</p>
                  </button>
                  <div className="delivery-detail-foot">
                    <span>PROVENANCE PRESERVED</span>
                    <span>HUMAN REVIEW</span>
                    <button type="button" onClick={() => openOutput(card.id)}>OPEN OUTPUT →</button>
                  </div>
                </article>
              ))}
            </div>
          )}

          <div className="delivery-file-strip">
            <div><span>ACTUAL FILE GENERATION</span><strong>{fileReadyCount} / {fileStates.length}</strong></div>
            {fileStates.map((item) => {
              const ready = generatedFiles[item.key] === true || actualFiles[item.key] === true;
              return (
                <button key={item.key} type="button" className={ready ? "ready" : "not-ready"} onClick={() => generateFile(item.key)} disabled={generatingFile !== null}>
                  {item.icon} {item.label} · {ready ? "DOWNLOAD AGAIN" : "GENERATE"}
                </button>
              );
            })}
          </div>
          {generationError && <div className="delivery-generation-error">{generationError}</div>}
        </div>
      )}

      {view === "evidence" && (
        <div className="delivery-evidence-view">
          <div className="delivery-section-heading"><span>DELIVERY TRUST LAYER</span><strong>Claims stay connected to evidence.</strong></div>
          <div className="delivery-trust-flow">
            <div><b>01</b><strong>PROJECT</strong><span>Original idea + requirements</span></div><i>→</i>
            <div><b>02</b><strong>RESEARCH</strong><span>{researchRecords || evidence.length} source records</span></div><i>→</i>
            <div><b>03</b><strong>EVIDENCE</strong><span>{evidence.length} evidence records</span></div><i>→</i>
            <div><b>04</b><strong>CLAIMS</strong><span>{claimCoverage ? `${claimCoverage.toFixed(1)}% covered` : "coverage pending"}</span></div><i>→</i>
            <div><b>05</b><strong>DELIVERY</strong><span>Traceable outputs</span></div>
          </div>
          <div className="delivery-warning-box"><span>TRUST RULE</span><strong>Metadata is not the same as verified scientific evidence.</strong><p>AURA preserves source identifiers and verification boundaries so a polished document never becomes a substitute for evidence.</p></div>
        </div>
      )}

      {view === "execution" && (
        <div className="delivery-execution-view">
          <div className="execution-banner"><span className="execution-pulse" /><div><strong>EXECUTION BOUNDARY</strong><p>{executionTruth}</p></div></div>
          <div className="execution-grid">
            <div><span>CODE EXECUTED</span><strong>NOT CLAIMED</strong><small>AURA generated the development path, not an observed runtime result.</small></div>
            <div><span>EXPERIMENTS RUN</span><strong>NOT CLAIMED</strong><small>Experiment designs are preserved as plans until real runs produce results.</small></div>
            <div><span>RESULTS VERIFIED</span><strong>NOT CLAIMED</strong><small>Only executed and reviewed measurements should enter a Results section.</small></div>
            <div><span>HUMAN REVIEW</span><strong>REQUIRED</strong><small>Final technical, scientific and submission decisions remain human-reviewed.</small></div>
          </div>
        </div>
      )}
    </section>
  );
}


function ProjectLifecycle({ project }: { project: Project | null }) {
  const lifecycle = project?.lifecycle;
  const stages = Array.isArray(lifecycle?.stages) ? lifecycle.stages : [];
  if (!project || stages.length === 0) return null;
  const percent = Number(lifecycle?.completion_percent || 0);
  const verified = Number(lifecycle?.verified_stages || 0);
  const total = Number(lifecycle?.total_stages || stages.length);
  const blocker = lifecycle?.next_blocker;
  return (
    <div className="project-lifecycle-panel">
      <div className="project-lifecycle-head">
        <div>
          <span className="project-lifecycle-kicker">PROJECT DEVELOPMENT LIFECYCLE</span>
          <h3>{lifecycle?.completed ? "PROJECT COMPLETED" : "LIVE PROJECT COMPLETION"}</h3>
          <p>Project-specific development stages generated from the detected project profile. Design, execution, measurement and scientific validation remain separate states.</p>
        </div>
        <div className="lifecycle-score"><strong>{percent}%</strong><span>VERIFIED</span></div>
      </div>
      <div className="lifecycle-progress"><i style={{ width: `${percent}%` }} /></div>
      <div className="lifecycle-summary"><b>{verified} / {total} VERIFIED STAGES</b><span>PROFILE · {(lifecycle?.profile || "general").replaceAll("_", " ").toUpperCase()}</span></div>
      <div className="lifecycle-track" role="list" aria-label="Project development lifecycle">
        {stages.map((stage) => (
          <div key={stage.key} className={`lifecycle-node lifecycle-${stage.status}`} role="listitem" title={stage.reason}>
            <div className="lifecycle-dot">{stage.verified ? "✓" : stage.status === "review" ? "!" : stage.status === "blocked" ? "×" : stage.status === "na" ? "–" : "○"}</div>
            <span>{stage.label}</span>
            <small>{stage.display}</small>
          </div>
        ))}
      </div>
      <div className={`lifecycle-blocker ${blocker ? "has-blocker" : "clear"}`}>
        <span>{blocker ? "NEXT REQUIRED ACTION" : "LIFECYCLE CLEAR"}</span>
        <strong>{blocker ? `${blocker.label}: ${blocker.display}` : "All project lifecycle stages are verified."}</strong>
        <small>{blocker?.reason || lifecycle?.truth}</small>
      </div>
    </div>
  );
}


function AuraProjectStatusLayer({ project, pipeline }: { project: Project | null; pipeline: Pipeline | null }) {
  if (!project) return null;
  const truth = getTruthStatus(project);
  const validation = isRecord(project.validation) ? project.validation : {};
  const experiments = isRecord(project.experiments) ? project.experiments : {};
  const results = isRecord(experiments.results_summary) ? experiments.results_summary : {};
  const evidence = Array.isArray(project.evidence) ? project.evidence : [];
  const research = isRecord(project.research) ? project.research : {};
  const researchRecords = Array.isArray(research.sources) ? research.sources.length : Array.isArray(research.papers) ? research.papers.length : 0;
  const executed = ["RESULTS_AVAILABLE_REVIEW_REQUIRED", "EXPERIMENT_EXECUTED_REVIEW_REQUIRED", "EXECUTED"].includes(safeText(results.status).toUpperCase()) || safeText(validation.execution_status).toUpperCase() === "EXECUTED";
  const measured = Boolean(results && Object.keys(results).some((k) => ["precision","recall","accuracy","f1","map50","map50_95","mae","rmse","r2"].includes(k.toLowerCase()) && results[k] !== null && results[k] !== undefined));
  const validated = truth.label === "VALIDATED";
  const workflow = pipeline ? "CONFIGURED" : "READY";
  const steps = [
    ["DESIGNED", "COMPLETE", "good"],
    ["RESEARCH", researchRecords ? `${researchRecords} RECORDS` : "EVIDENCE REQUIRED", researchRecords ? "good" : "warn"],
    ["IMPLEMENTATION", "READY", "ready"],
    ["EXECUTION", executed ? "RECORDED" : "NOT EXECUTED", executed ? "good" : "blocked"],
    ["MEASUREMENT", measured ? "MEASURED" : "PENDING", measured ? "good" : "blocked"],
    ["VALIDATION", validated ? "VERIFIED" : "PENDING REVIEW", validated ? "good" : "warn"],
    ["DELIVERY", validated ? "READY" : "PENDING", validated ? "good" : "blocked"],
  ];
  return <section className="aura-project-status-layer" aria-label="AURA project status and truth">
    <div className="aps-head">
      <div><span>AURA PROJECT STATUS</span><h3>One truth layer for the entire project</h3><p>Workflow configuration, evidence, execution, measurement and scientific validation are tracked separately.</p></div>
      <div className={`aps-truth ${truth.tone}`}>{truth.label}</div>
    </div>
    <div className="aps-grid">
      {steps.map(([name, state, tone]) => <div className={`aps-card ${tone}`} key={name}><span>{name}</span><strong>{state}</strong></div>)}
    </div>
    <div className="aps-footer"><div><b>WORKFLOW</b><span>{workflow} · {STAGES.length}/{STAGES.length} stages available</span></div><div><b>EVIDENCE</b><span>{evidence.length} records · reviewed separately</span></div><div><b>SCIENTIFIC TRUTH</b><span>{truth.detail}</span></div></div>
  </section>;
}

function PlatformCompletionPanel() {
  const [cert, setCert] = useState<any>(null);
  useEffect(() => {
    auraFetch(`${API_BASE}/api/aura/platform/certification`, { cache: "no-store" })
      .then((r) => r.json()).then((d) => setCert(d?.certification || null)).catch(() => undefined);
  }, []);
  if (!cert) return null;
  const checks = isRecord(cert.checks) ? Object.entries(cert.checks) : [];
  return <section className="platform-completion-panel">
    <div className="platform-completion-head">
      <div><span>AURA PLATFORM CERTIFICATION</span><h3>{cert.certification === "PLATFORM_COMPLETE" ? "100% PLATFORM COMPLETE" : "PLATFORM VERIFICATION REQUIRED"}</h3><p>All core AURA software capabilities are represented in the release. Scientific project completion remains governed by real evidence and human validation.</p></div>
      <div className="platform-completion-score"><strong>{cert.percent}%</strong><small>{cert.passed}/{cert.total} CHECKS</small></div>
    </div>
    <div className="platform-completion-bar"><i style={{width:`${cert.percent}%`}} /></div>
    <div className="platform-check-grid">{checks.map(([key,value]) => <div key={key} className={value ? "platform-check pass" : "platform-check fail"}><b>{value ? "✓" : "×"}</b><span>{key.replaceAll("_"," ").toUpperCase()}</span></div>)}</div>
  </section>;
}

function ProjectHealthPanel({ project }: { project: Project | null }) {
  const [health, setHealth] = useState<any>(null);
  useEffect(() => {
    if (!project?.project_id) return;
    auraFetch(`${API_BASE}/api/aura/projects/${project.project_id}/health-score`, { cache: "no-store" })
      .then((r) => r.json()).then((d) => { if (d?.health) setHealth(d.health); }).catch(() => undefined);
  }, [project?.project_id, project?.lifecycle?.completion_percent]);
  if (!project || !health) return null;
  const components = isRecord(health.components) ? health.components : {};
  return (
    <div className="project-health-panel">
      <div className="project-health-head">
        <div><span className="project-health-kicker">AURA PROJECT HEALTH</span><h3>{health.grade} · {health.score}/100</h3><p>Engineering readiness signal across lifecycle, execution, research, evidence, testing and review. This is not a scientific validity score.</p></div>
        <div className="project-health-score"><strong>{health.score}</strong><span>HEALTH</span></div>
      </div>
      <div className="project-health-bars">
        {Object.entries(components).map(([key, value]) => <div className="project-health-row" key={key}><span>{humanizeKey(key)}</span><i><b style={{ width: `${Math.min(100, Number(value) * 2)}%` }} /></i><strong>{String(value)}</strong></div>)}
      </div>
      <div className="project-health-foot"><span>{health.executions} successful executions</span><span>{health.failures} failures / blocks</span><span>{health.scientific_validation ? "SCIENTIFIC REVIEWED" : "SCIENTIFIC REVIEW PENDING"}</span></div>
    </div>
  );
}

function DependencyImpactPanel({ project }: { project: Project | null }) {
  const [impact, setImpact] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  async function refresh() {
    if (!project?.project_id) return;
    setLoading(true);
    try {
      const r = await auraFetch(`${API_BASE}/api/aura/projects/${project.project_id}/dependency-impact`, { cache: "no-store" });
      const d = await r.json().catch(() => ({}));
      if (r.ok) setImpact(d.impact || null);
    } finally { setLoading(false); }
  }
  useEffect(() => { void refresh(); }, [project?.project_id]);
  if (!project) return null;
  const changed = Array.isArray(impact?.changed_nodes) ? impact.changed_nodes : [];
  const affected = Array.isArray(impact?.impacted_nodes) ? impact.impacted_nodes : [];
  return <section className="dependency-impact-panel">
    <div className="dip-head">
      <div><span>DEPENDENCY & IMPACT INTELLIGENCE</span><h3>{changed.length ? "DOWNSTREAM IMPACT DETECTED" : "PROJECT DEPENDENCIES STABLE"}</h3><p>AURA tracks upstream changes and identifies downstream work that may require re-checking, re-execution or re-validation.</p></div>
      <button type="button" onClick={refresh} disabled={loading}>{loading ? "SCANNING…" : "SCAN IMPACT"}</button>
    </div>
    <div className="dip-stats"><div><b>{changed.length}</b><span>CHANGED NODES</span></div><div><b>{affected.length}</b><span>IMPACTED NODES</span></div><div><b>{impact?.requires_reexecution ? "YES" : "NO"}</b><span>RE-EXECUTION</span></div><div><b>{impact?.requires_revalidation ? "YES" : "NO"}</b><span>RE-VALIDATION</span></div></div>
    {changed.length > 0 ? <div className="dip-flow">{changed.map((node:string) => <div key={node}><strong>{node.replaceAll("_", " ").toUpperCase()}</strong><span>CHANGED</span></div>)}<i>→</i><div className="dip-affected"><strong>{affected.length} DOWNSTREAM</strong><span>{affected.slice(0, 7).map((node:string) => node.replaceAll("_", " ")).join(" · ")}{affected.length > 7 ? " · …" : ""}</span></div></div> : <div className="dip-clear">No persisted upstream change is currently propagating through the project dependency graph.</div>}
    <small className="dip-truth">{impact?.truth || "Impact propagation identifies stale downstream work; it does not itself prove scientific invalidity."}</small>
  </section>;
}


function ResultsObservatoryPanel({ project }: { project: Project | null }) {
  const [data, setData] = useState<any>(null); const [loading, setLoading] = useState(false);
  async function refresh(){ if(!project?.project_id)return; setLoading(true); try{const r=await auraFetch(`${API_BASE}/api/aura/projects/${project.project_id}/results/observatory`,{cache:"no-store"}); const d=await r.json().catch(()=>({})); if(r.ok)setData(d.observatory||null);}finally{setLoading(false);} }
  useEffect(()=>{void refresh();},[project?.project_id]); if(!project)return null;
  const metrics=Array.isArray(data?.metrics)?data.metrics:[], artifacts=Array.isArray(data?.artifacts)?data.artifacts:[], lineage=Array.isArray(data?.execution_lineage)?data.execution_lineage:[];
  const repro=isRecord(data?.reproducibility)?data.reproducibility:{};
  return <section className="results-observatory-panel"><div className="rop-head"><div><span>RESULTS OBSERVATORY</span><h3>Measured results, provenance & reproducibility</h3><p>Every metric is tied to persisted execution artifacts. Measurement remains separate from scientific validation.</p></div><button type="button" onClick={refresh} disabled={loading}>{loading?"REFRESHING…":"REFRESH RESULTS"}</button></div>
    <div className="rop-stats"><div><b>{metrics.filter((m:any)=>m.measured).length}</b><span>MEASURED METRICS</span></div><div><b>{artifacts.length}</b><span>HASHED ARTIFACTS</span></div><div><b>{lineage.length}</b><span>EXECUTED RUNS</span></div><div><b>{repro.reproducible_ready?"READY":"PENDING"}</b><span>REPRODUCIBILITY</span></div></div>
    {metrics.length?<div className="rop-metrics">{metrics.map((m:any)=><div className="rop-metric" key={m.metric}><b>{String(m.metric).replaceAll("_"," ").toUpperCase()}</b><small>{m.source}</small><strong>{m.proposed??"—"}</strong><span>{m.baseline!=null?`BASELINE ${m.baseline} · Δ ${m.delta??"—"}`:"NO BASELINE RECORDED"}</span></div>)}</div>:<div className="rop-empty">No measured metrics are currently available from persisted execution artifacts.</div>}
    <div className="rop-lineage"><div><b>EXECUTION LINEAGE</b><span>{lineage.length?lineage.slice(0,4).map((e:any)=>`${e.task||"run"} · ${e.execution_id||"unknown"}`).join(" | "):"No successful execution lineage recorded."}</span></div><div><b>RESULT STATUS</b><span>{data?.review_status||"REVIEW_REQUIRED"}</span></div></div><small className="rop-truth">{data?.truth||"Measured results require the validation gate and authorized human review before scientific validation."}</small>
  </section>;
}

function ReproducibilityLineagePanel({ project }: { project: Project | null }) {
  const [data,setData]=useState<any>(null); const [loading,setLoading]=useState(false);
  async function refresh(){ if(!project?.project_id)return; setLoading(true); try{const r=await auraFetch(`${API_BASE}/api/aura/projects/${project.project_id}/reproducibility/lineage`,{cache:"no-store"}); const d=await r.json().catch(()=>({})); if(r.ok)setData(d.lineage||null);}finally{setLoading(false);} }
  useEffect(()=>{void refresh();},[project?.project_id]); if(!project)return null;
  const files=Array.isArray(data?.tracked_files)?data.tracked_files:[], runs=Array.isArray(data?.executions)?data.executions:[];
  return <section className="repro-lineage-panel"><div className="rlp-head"><div><span>REPRODUCIBILITY & EXPERIMENT LINEAGE</span><h3>Can the recorded result be reproduced?</h3><p>Configuration, execution order, environment and artifact hashes are kept together as a reproducibility record.</p></div><button type="button" onClick={refresh} disabled={loading}>{loading?"CHECKING…":"CHECK REPRODUCIBILITY"}</button></div>
    <div className="rlp-stats"><div><b>{data?.reproducible_ready?"READY":"INCOMPLETE"}</b><span>REPRODUCTION STATE</span></div><div><b>{runs.length}</b><span>EXECUTION STEPS</span></div><div><b>{files.length}</b><span>TRACKED ARTIFACTS</span></div><div><b>{data?.requirements?.seed??"—"}</b><span>RECORDED SEED</span></div></div>
    <div className="rlp-flow">{runs.slice(0,6).map((r:any,i:number)=><div key={r.execution_id||i}><strong>{i+1}. {String(r.task||"execution").replaceAll("_"," ")}</strong><span>{r.execution_id||"NO ID"} · {r.artifact_count||0} artifacts</span></div>)}</div>
    <small className="rlp-truth">{data?.truth_boundary||"Reproducibility documentation does not establish scientific validity; validation still requires the AURA validation gate and authorized human review."}</small>
  </section>;
}

function ValidationGate({ project }: { project: Project | null }) {
  const [completion, setCompletion] = useState<any>(null);
  const [gate, setGate] = useState<any>(null);
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState("");
  async function refresh() {
    if (!project?.project_id) return;
    const [completionResponse, gateResponse] = await Promise.all([
      auraFetch(`${API_BASE}/api/aura/projects/${project.project_id}/completion`, { cache: "no-store" }),
      auraFetch(`${API_BASE}/api/aura/projects/${project.project_id}/validation/gate`, { cache: "no-store" }),
    ]);
    const d = await completionResponse.json().catch(() => ({}));
    const g = await gateResponse.json().catch(() => ({}));
    if (completionResponse.ok) setCompletion(d.completion);
    if (gateResponse.ok) setGate(g.gate);
  }
  useEffect(() => { void refresh(); }, [project?.project_id]);
  async function approve() {
    if (!project?.project_id) return;
    setBusy(true); setMessage("");
    try {
      const session = JSON.parse(window.localStorage.getItem("aura_session") || "{}");
      if (!session.token) throw new Error("Sign in with an AURA account before approving validation.");
      const r = await auraFetch(`${API_BASE}/api/aura/projects/${project.project_id}/validation/review`, { method:"POST", headers:{"Content-Type":"application/json","Authorization":`Bearer ${session.token}`}, body:JSON.stringify({approved:true, reviewer_note:"Human review completed in AURA."}) });
      const d = await r.json().catch(() => ({}));
      if (!r.ok) throw new Error(d.detail || "Validation approval was blocked.");
      setCompletion(d.completion);
      await refresh();
      setMessage("VALIDATION APPROVED — completion state recalculated.");
    } catch (e) { setMessage(e instanceof Error ? e.message : "Validation review failed."); } finally { setBusy(false); }
  }
  const gates = Array.isArray(completion?.gates) ? completion.gates : [];
  return <section className="validation-gate-panel">
    <div className="validation-gate-head"><div><span className="aci-section-title">COMPLETION & VALIDATION GATE</span><h3>{completion?.status || "CHECKING…"}</h3><p>AURA cannot self-certify scientific validity. Every required gate must pass, measured evidence must exist, and a human reviewer must approve validation.</p></div><button type="button" onClick={refresh}>REFRESH</button></div>
    <div className="validation-gate-grid">{gates.map((g:any)=><div key={g.gate} className={g.passed ? "passed" : "blocked"}><span>{g.passed ? "✓" : "○"}</span><b>{String(g.gate).replaceAll("_"," ").toUpperCase()}</b><small>{g.passed ? "PASSED" : "REQUIRED"}</small></div>)}</div>
    {Array.isArray(gate?.criteria) && <div className="validation-gate-criteria">{gate.criteria.map((c:any)=><div key={c.id} className={c.passed ? "passed" : "blocked"}><span>{c.passed ? "✓" : "!"}</span><div><b>{c.label}</b><small>{c.reason}</small></div></div>)}</div>}
    <div className="validation-gate-actions"><strong>{gate ? `${gate.required_passed}/${gate.required_total} REQUIRED CRITERIA` : `${completion?.completion_percent ?? 0}% GATES PASSED`}</strong><button type="button" disabled={busy || completion?.completed || !gate?.ready} onClick={approve}>{busy ? "REVIEWING…" : "APPROVE SCIENTIFIC VALIDATION"}</button></div>
    {message && <div className="validation-gate-message">{message}</div>}
  </section>;
}

function StagePanel({
  stage,
  project,
  index,
}: {
  stage: string;
  project: Project | null;
  index: number;
}) {
  const stageData = stageDataFor(stage, project);

  const importantCards = useMemo(
    () => getImportantCards(stage, stageData, project),
    [stage, stageData, project]
  );

  const sections = useMemo(
    () => getStageSections(stage, stageData),
    [stage, stageData]
  );

  const projectIdea =
    project?.original_idea ||
    "AURA project context is loading.";

  const connectedBefore = Math.max(index, 0);
  const remainingGates = Math.max(STAGES.length - STAGES.map((item, itemIndex) => getStageState(item, itemIndex, null, project)).filter((item) => ["COMPLETED", "EXECUTED", "VERIFIED"].includes(item.label)).length, 0);

  const status =
    project?.status ||
    "processing";

  return (
    <div className="stage-panel">
      <div className="main-panel">
        <div className="panel-label">
          STAGE {String(index + 1).padStart(2, "0")} /{" "}
          {STAGES.length}
        </div>

        <h2>
          {LABELS[stage] || stage}
        </h2>

        <div className="stage-description">
          {DESCRIPTIONS[stage] ||
            "AURA is processing this part of your project journey."}
        </div>

        <div className="idea-context">
          <strong>PROJECT CONTEXT</strong>
          <br />
          {projectIdea}
        </div>

        <div className="stage-message">
          {getStageMessage(stage, stageData)}
        </div>

        <AuraCommandCenter stage={stage} project={project} />

        {stage === "build" && <BuildExecutionCenter project={project} />}
        {stage === "validate" && <ValidationGate project={project} />}

        {stage === "deliver" && <BuildExecutionCenter project={project} />}
        {stage === "deliver" && <DeliveryStudio project={project} />}

        {importantCards.length > 0 ? (
          <>
            <div className="insight-header">
              <div>
                <span>AURA INTELLIGENCE</span>
                <b>
                  {stage === "understand"
                    ? "Structured project understanding"
                    : "Executive view"}
                </b>
              </div>

              {stage === "understand" && (
                <div className="intelligence-badge">
                  <i />
                  AURA REASONING LAYER
                </div>
              )}
            </div>

            {stage === "understand" && (
              <div className="understand-banner">
                <div className="understand-banner-mark">A</div>

                <div>
                  <strong>AURA has interpreted your starting idea</strong>
                  <p>
                    This is an AI-generated working interpretation. It
                    becomes the context AURA carries into investigation,
                    evidence analysis, innovation and development.
                  </p>
                </div>
              </div>
            )}

            <div className={
              "data-grid " +
              (stage === "understand" ? "understand-grid" : "")
            }>
              {importantCards.map((card, cardIndex) => (
                <div
                  className={
                    "data-card " +
                    (card.tone
                      ? "tone-" + card.tone
                      : "") +
                    (stage === "understand"
                      ? " understand-card"
                      : "")
                  }
                  key={cardIndex}
                >
                  <span>{card.label}</span>
                  <strong>{card.value}</strong>
                </div>
              ))}
            </div>
          </>
        ) : (
          <div className="empty-state">
            AURA has connected this stage to the project pipeline,
            but detailed intelligence is not available yet.
          </div>
        )}

        {sections.length > 0 && (
          <div className="section-grid">
            {sections.map((section) => (
              <div
                className="clean-section"
                key={section.title}
              >
                <div className="clean-section-title">
                  {section.title.toUpperCase()}
                </div>

                <div className="clean-section-list">
                  {section.items.map((item, itemIndex) => (
                    <div
                      className="clean-section-item"
                      key={itemIndex}
                    >
                      <span>{item}</span>
                    </div>
                  ))}
                </div>
              </div>
            ))}
          </div>
        )}

        {stage === "understand" && (
          <div className="understand-footnote">
            <span>WORKING INTERPRETATION</span>
            <p>
              AURA should treat this stage as a hypothesis about the
              project, not as verified research. Later stages must
              investigate the real-world evidence and refine or challenge
              these assumptions.
            </p>
          </div>
        )}
      </div>

      <div className="side-panel">
        <div className="panel-label">
          CONNECTED JOURNEY
        </div>

        <h3>AURA Pipeline</h3>

        <div className="stage-list">
          {STAGES.map((item, itemIndex) => {
            const done = itemIndex < index;
            const current = itemIndex === index;

            return (
              <div
                key={item}
                className={
                  "stage-list-item " +
                  (done ? "done " : "") +
                  (current ? "current" : "")
                }
              >
                <i />
                <span>
                  {LABELS[item]}
                </span>
              </div>
            );
          })}
        </div>

        <div className="connected-count">
          <strong>
            {connectedBefore}
          </strong>

          <span>
            PIPELINE STAGES CONNECTED
          </span>
        </div>

        <div className="connected-count">
          <strong>
            {remainingGates}
          </strong>

          <span>
            VERIFICATION GATES REMAINING
          </span>
        </div>

        <div className="system-panel">
          <strong>
            PROJECT STATUS
          </strong>

          <span>
            {getProjectTruthStatus(project).label} — {getProjectTruthStatus(project).detail}
          </span>
        </div>

        <div className="system-panel">
          <strong>
            AURA PROJECT MEMORY
          </strong>

          <span>
            This stage does not exist alone. Its intelligence becomes
            context for every stage that follows.
          </span>
        </div>
      </div>
    </div>
  );
}

function EvidencePanel({
  project,
}: {
  project: Project | null;
}) {
  const evidence = Array.isArray(project?.evidence)
    ? project.evidence
    : [];

  const verified = evidence.filter((item) => {
    if (!isRecord(item)) return false;

    const type =
      safeText(item.evidence_type).toLowerCase();

    return (
      type.includes("verified") ||
      type.includes("evidence")
    );
  }).length;

  const sourceCount = new Set(
    evidence
      .map((item) =>
        isRecord(item)
          ? safeText(item.source)
          : ""
      )
      .filter(Boolean)
  ).size;

  return (
    <div className="generic-panel">
      <div className="panel-label">
        PROJECT INTELLIGENCE / EVIDENCE
      </div>

      <h2>Evidence & Trust</h2>

      <p>
        AURA keeps evidence connected to claims,
        recommendations and project decisions instead of presenting
        generated information as unquestioned fact.
      </p>

      <div className="trust-summary">
        <div className="trust-card">
          <span>EVIDENCE RECORDS</span>
          <strong>{evidence.length}</strong>
        </div>

        <div className="trust-card">
          <span>IDENTIFIED SOURCES</span>
          <strong>{sourceCount}</strong>
        </div>

        <div className="trust-card">
          <span>SUPPORTED RECORDS</span>
          <strong>{verified}</strong>
        </div>
      </div>

      {evidence.length > 0 ? (
        <div className="evidence-list">
          {evidence.slice(0, 12).map((item, index) => {
            const record = isRecord(item)
              ? item
              : null;

            const claim =
              safeText(record?.claim) ||
              "Evidence record";

            const type =
              safeText(record?.evidence_type) ||
              "AURA EVIDENCE";

            const source =
              safeText(record?.source);

            const data =
              record?.data;

            const readableData =
              data !== undefined
                ? shortText(data, 320)
                : "";

            return (
              <div
                className="evidence-item"
                key={index}
              >
                <div className="record-top">
                  <strong>{claim}</strong>

                  <span className="record-badge">
                    {type.toUpperCase()}
                  </span>
                </div>

                {source && (
                  <span className="record-source">
                    SOURCE • {source}
                  </span>
                )}

                {readableData && (
                  <div className="record-detail">
                    {readableData}
                  </div>
                )}
              </div>
            );
          })}
        </div>
      ) : (
        <div className="empty-state">
          No evidence records are available yet.
        </div>
      )}
    </div>
  );
}

function MemoryPanel({
  project,
}: {
  project: Project | null;
}) {
  const memory = Array.isArray(project?.memory)
    ? project.memory
    : [];

  const stageCounts = memory.reduce<Record<string, number>>(
    (acc, item) => {
      if (!isRecord(item)) return acc;

      const stage =
        safeText(item.stage) || "system";

      acc[stage] = (acc[stage] || 0) + 1;

      return acc;
    },
    {} as Record<string, number>
  );

  const latestStages = Object.entries(stageCounts)
    .sort((a, b) => b[1] - a[1])
    .slice(0, 4);

  return (
    <div className="generic-panel">
      <div className="panel-label">
        PROJECT INTELLIGENCE / MEMORY
      </div>

      <h2>Project Memory</h2>

      <p>
        AURA continuously connects important decisions, discoveries
        and stage events so later reasoning can build on earlier
        project context.
      </p>

      <div className="trust-summary">
        <div className="trust-card">
          <span>MEMORY EVENTS</span>
          <strong>{memory.length}</strong>
        </div>

        <div className="trust-card">
          <span>CONNECTED STAGES</span>
          <strong>
            {Object.keys(stageCounts).length}
          </strong>
        </div>

        <div className="trust-card">
          <span>PROJECT STATE</span>
          <strong>
            {project?.status
              ? formatStatus(project.status)
              : "Active"}
          </strong>
        </div>
      </div>

      {latestStages.length > 0 && (
        <div className="section-grid">
          {latestStages.map(([stage, count]) => (
            <div
              className="clean-section"
              key={stage}
            >
              <div className="clean-section-title">
                {stage === "system"
                  ? "SYSTEM"
                  : LABELS[stage] || stage.toUpperCase()}
              </div>

              <div className="clean-section-item">
                <span>
                  {count} connected project event
                  {count === 1 ? "" : "s"}
                </span>
              </div>
            </div>
          ))}
        </div>
      )}

      {memory.length > 0 ? (
        <div className="memory-list">
          {memory
            .slice()
            .reverse()
            .slice(0, 15)
            .map((item, index) => {
              const record = isRecord(item)
                ? item
                : null;

              const event =
                safeText(record?.event) ||
                "Project event";

              const stage =
                safeText(record?.stage);

              const data =
                record?.data;

              const timestamp =
                safeText(record?.timestamp);

              const readableData =
                data !== undefined
                  ? shortText(data, 300)
                  : "";

              return (
                <div
                  className="memory-item"
                  key={index}
                >
                  <div className="record-top">
                    <strong>{event}</strong>

                    <span className="record-badge">
                      {stage
                        ? (
                            LABELS[stage] ||
                            stage
                          ).toUpperCase()
                        : "AURA MEMORY"}
                    </span>
                  </div>

                  {timestamp && (
                    <span className="record-source">
                      {timestamp}
                    </span>
                  )}

                  {readableData && (
                    <div className="record-detail">
                      {readableData}
                    </div>
                  )}
                </div>
              );
            })}
        </div>
      ) : (
        <div className="empty-state">
          Project memory is ready. It will accumulate as AURA
          executes the autonomous journey.
        </div>
      )}
    </div>
  );
}