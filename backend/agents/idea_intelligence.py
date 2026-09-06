from __future__ import annotations

import re
from typing import Any

from models.project import AURAProject
from orchestration.contract import AURAStageResult
from orchestration.stages import AURAStage


class IdeaIntelligenceAgent:
    """
    Stage 01 — UNDERSTAND

    Evidence-aware project understanding layer.

    Important trust rule:
    Stage 01 does NOT claim that a research fact, novelty claim, gap,
    technology choice, dataset choice, or solution has already been
    externally verified. Instead, it creates:
      1. a structured interpretation of the user's idea,
      2. explicit assumptions and uncertainties,
      3. evidence targets that later AURA research agents must verify,
      4. source/provider requirements,
      5. claim-verification rules and an investigation plan.

    This keeps the pipeline honest while making Stage 01 directly
    useful to the Investigation stage.
    """

    stage = AURAStage.UNDERSTAND

    # =============================================================
    # MAIN EXECUTION
    # =============================================================

    def run(self, project: AURAProject) -> AURAStageResult:
        raw_idea = project.original_idea or ""
        idea = self._clean_idea(raw_idea)

        if not idea:
            return AURAStageResult(
                stage=self.stage,
                success=False,
                message="No project idea was provided.",
                data={"error": "empty_project_idea"},
                next_stage=AURAStage.INVESTIGATE,
            )

        keywords = self._extract_keywords(idea)
        domains = self._detect_domains(idea, keywords)
        intent = self._detect_intent(idea)
        project_type = self._classify_project_type(idea, domains)

        problem = self._build_problem_definition(
            idea, domains, project_type
        )
        target_context = self._identify_target_context(idea, domains)
        stakeholders = self._identify_stakeholders(
            idea, target_context, domains
        )

        objectives = self._generate_objectives(
            idea, domains, project_type, target_context
        )
        functional_requirements = self._generate_functional_requirements(
            idea, domains, project_type
        )
        technical_requirements = self._generate_technical_requirements(
            idea, domains
        )
        constraints = self._identify_constraints(
            idea, domains, project_type
        )
        research_questions = self._generate_research_questions(
            idea, domains, problem
        )
        success_criteria = self._generate_success_criteria(
            project_type, domains
        )
        investigation_focus = self._generate_investigation_focus(
            idea, domains, problem
        )
        uncertainties = self._identify_uncertainties(
            idea, domains, project_type
        )

        normalized_title = self._normalize_title(idea)
        understanding_confidence = self._calculate_understanding_confidence(
            idea=idea,
            domains=domains,
            keywords=keywords,
            target_context=target_context,
        )

        evidence_requirements = self._build_evidence_requirements(
            idea=idea,
            domains=domains,
            keywords=keywords,
            research_questions=research_questions,
            investigation_focus=investigation_focus,
        )

        verification_plan = self._build_verification_plan(
            idea=idea,
            domains=domains,
            project_type=project_type,
        )

        claim_register = self._build_initial_claim_register(
            idea=idea,
            problem=problem,
            target_context=target_context,
            domains=domains,
        )

        source_registry = self._build_source_registry(domains)
        search_strategy = self._build_search_strategy(
            idea=idea,
            normalized_title=normalized_title,
            keywords=keywords,
            domains=domains,
            research_questions=research_questions,
        )

        evidence_summary = {
            "status": "PRE_INVESTIGATION",
            "verified_claims": 0,
            "unverified_claims": len(claim_register),
            "verification_required": True,
            "external_sources_consulted": 0,
            "message": (
                "Stage 01 creates evidence targets and verification "
                "requirements. External research verification begins "
                "in Stage 02."
            ),
        }

        problem_understanding = {
            "original_idea": idea,
            "normalized_idea": normalized_title,
            "intent": intent,
            "project_type": project_type,
            "interpreted_problem": problem,
            "target_context": target_context,
            "stakeholders": stakeholders,
            "keywords": keywords,
            "detected_domains": domains,
            "functional_requirements": functional_requirements,
            "technical_requirements": technical_requirements,
            "constraints": constraints,
            "research_questions": research_questions,
            "success_criteria": success_criteria,
            "investigation_focus": investigation_focus,
            "uncertainties": uncertainties,
            "understanding_confidence": understanding_confidence,
            "evidence_summary": evidence_summary,
            "claim_register": claim_register,
            "evidence_requirements": evidence_requirements,
            "verification_plan": verification_plan,
            "source_registry": source_registry,
            "search_strategy": search_strategy,
            "evidence_policy": self._evidence_policy(),
        }

        project.domain = domains
        project.objectives = objectives
        project.requirements = list(
            dict.fromkeys(
                functional_requirements + technical_requirements
            )
        )
        project.constraints = constraints

        project.analysis = {
            "problem_understanding": problem_understanding
        }

        project.memory.append(
            {
                "stage": self.stage.value,
                "type": "problem_understanding",
                "summary": (
                    f"AURA structured '{normalized_title}' and created "
                    "an explicit evidence-verification plan."
                ),
                "evidence_status": "PRE_INVESTIGATION",
            }
        )

        project.evidence.append(
            {
                "stage": self.stage.value,
                "type": "understanding_framework",
                "status": "aura_synthesis",
                "source": "User-provided project idea",
                "claim": (
                    "AURA generated an initial structured interpretation "
                    "and a verification plan."
                ),
                "verification_scope": (
                    "Interpretation only. Research facts, novelty, gaps, "
                    "and technology choices require external verification."
                ),
            }
        )

        return AURAStageResult(
            stage=self.stage,
            success=True,
            message=(
                "AURA transformed the idea into an evidence-aware "
                "project definition and verification plan."
            ),
            data={
                "original_idea": idea,
                "normalized_idea": normalized_title,
                "intent": intent,
                "project_type": project_type,
                "interpreted_problem": problem,
                "target_context": target_context,
                "stakeholders": stakeholders,
                "domains": domains,
                "keywords": keywords,
                "objectives": objectives,
                "functional_requirements": functional_requirements,
                "technical_requirements": technical_requirements,
                "constraints": constraints,
                "research_questions": research_questions,
                "success_criteria": success_criteria,
                "investigation_focus": investigation_focus,
                "uncertainties": uncertainties,
                "understanding_confidence": understanding_confidence,
                "evidence_summary": evidence_summary,
                "claim_register": claim_register,
                "evidence_requirements": evidence_requirements,
                "verification_plan": verification_plan,
                "source_registry": source_registry,
                "search_strategy": search_strategy,
                "evidence_policy": self._evidence_policy(),
                "next_action": (
                    "Investigate the evidence targets across scholarly, "
                    "technical, project, dataset, standards and official "
                    "sources before making research claims."
                ),
            },
            next_stage=AURAStage.INVESTIGATE,
        )

    # =============================================================
    # EVIDENCE LAYER
    # =============================================================

    def _build_evidence_requirements(
        self,
        idea: str,
        domains: list[str],
        keywords: list[str],
        research_questions: list[str],
        investigation_focus: list[str],
    ) -> dict[str, Any]:
        return {
            "must_verify": [
                "Problem context and real-world need",
                "Existing research and prior approaches",
                "Existing products and implementations",
                "Reported limitations and unresolved challenges",
                "Research gaps supported by multiple relevant sources",
                "Relevant technologies and methods",
                "Available datasets and their provenance",
                "Evaluation methods and benchmark practices",
                "Relevant standards, official guidance or domain constraints",
            ],
            "claim_types": [
                "problem_claim",
                "existing_work_claim",
                "technology_claim",
                "dataset_claim",
                "limitation_claim",
                "gap_claim",
                "trend_claim",
                "performance_claim",
                "novelty_claim",
            ],
            "minimum_source_policy": {
                "research_claims": [
                    "peer-reviewed scholarly source where available",
                    "preprint/repository source when appropriate",
                ],
                "technology_claims": [
                    "official documentation",
                    "reputable technical source",
                ],
                "dataset_claims": [
                    "official dataset/repository",
                    "dataset paper when available",
                ],
                "standards_claims": [
                    "official standards body",
                    "government or institutional source",
                ],
                "project_claims": [
                    "official project repository",
                    "official product/documentation source",
                ],
            },
            "required_metadata": [
                "title",
                "authors_or_organization",
                "publication_or_release_year",
                "source/provider",
                "persistent_identifier_or_url",
                "abstract_or_description",
                "evidence_excerpt_or_supporting_metadata",
            ],
            "search_context": {
                "idea": idea,
                "domains": domains,
                "keywords": keywords,
                "research_questions": research_questions,
                "investigation_focus": investigation_focus,
            },
        }

    def _build_verification_plan(
        self,
        idea: str,
        domains: list[str],
        project_type: str,
    ) -> dict[str, Any]:
        providers = [
            "OpenAlex",
            "Crossref",
            "Semantic Scholar",
            "PubMed where relevant",
            "arXiv where relevant",
            "IEEE Xplore where authorized/configured",
            "ACM Digital Library where authorized/configured",
            "GitHub",
            "official documentation",
            "official datasets/repositories",
            "government/standards sources where relevant",
            "patent databases where accessible and relevant",
        ]

        return {
            "verification_required": True,
            "default_research_window": {
                "from_year": 2022,
                "to_year": 2026,
            },
            "providers_to_check": providers,
            "verification_sequence": [
                "Discover candidate sources.",
                "Normalize metadata.",
                "Remove duplicates and near-duplicates where possible.",
                "Rank relevance to the user's idea.",
                "Extract supporting evidence.",
                "Compare conflicting findings instead of merging them.",
                "Separate published facts from AURA synthesis.",
                "Identify limitations supported by sources.",
                "Construct gap candidates from evidence.",
                "Avoid global novelty claims from sparse retrieval.",
            ],
            "verification_rules": [
                "No external fact is treated as verified without source provenance.",
                "AURA synthesis must remain distinguishable from published claims.",
                "Conflicting sources must remain visible.",
                "Performance numbers must retain their source context.",
                "Novelty is opportunity-oriented unless a comprehensive search supports a narrower claim.",
                "Missing or weak evidence must be marked explicitly.",
            ],
            "project_type": project_type,
            "domains": domains,
        }

    def _build_initial_claim_register(
        self,
        idea: str,
        problem: str,
        target_context: str,
        domains: list[str],
    ) -> list[dict[str, Any]]:
        return [
            {
                "claim_id": "C01",
                "type": "problem_claim",
                "claim": problem,
                "status": "AURA_INTERPRETATION",
                "verification_required": True,
                "source_count": 0,
                "note": "Requires external evidence about the real-world problem.",
            },
            {
                "claim_id": "C02",
                "type": "target_claim",
                "claim": (
                    f"Likely target context: {target_context}"
                ),
                "status": "AURA_INFERENCE",
                "verification_required": True,
                "source_count": 0,
                "note": "Target context is inferred from the user's wording.",
            },
            {
                "claim_id": "C03",
                "type": "domain_claim",
                "claim": (
                    f"Detected domains: {', '.join(domains)}"
                ),
                "status": "AURA_CLASSIFICATION",
                "verification_required": False,
                "source_count": 0,
                "note": "Classification generated from the user input.",
            },
            {
                "claim_id": "C04",
                "type": "research_scope",
                "claim": (
                    f"Investigation scope derived from '{idea}'."
                ),
                "status": "AURA_SYNTHESIS",
                "verification_required": True,
                "source_count": 0,
                "note": "Scope will be refined after source retrieval.",
            },
        ]

    def _build_source_registry(
        self,
        domains: list[str],
    ) -> list[dict[str, Any]]:
        registry = [
            {
                "provider": "OpenAlex",
                "type": "scholarly_metadata",
                "priority": "high",
                "status": "configured_in_literature_engine",
                "purpose": "Broad scholarly discovery and metadata.",
            },
            {
                "provider": "Crossref",
                "type": "scholarly_metadata",
                "priority": "high",
                "status": "configured_in_literature_engine",
                "purpose": "Publication metadata and identifiers.",
            },
            {
                "provider": "Semantic Scholar",
                "type": "scholarly_metadata",
                "priority": "high",
                "status": "configured_with_rate_limits",
                "purpose": "Scholarly discovery and citation/context metadata.",
            },
            {
                "provider": "PubMed",
                "type": "biomedical_literature",
                "priority": "conditional",
                "status": "configured_in_literature_engine",
                "purpose": "Biomedical/health literature where relevant.",
            },
            {
                "provider": "arXiv",
                "type": "preprint_repository",
                "priority": "conditional",
                "status": "configured_in_literature_engine",
                "purpose": "Recent technical research and preprints.",
            },
            {
                "provider": "IEEE Xplore",
                "type": "scholarly_metadata",
                "priority": "conditional",
                "status": "requires_authorized_api_configuration",
                "purpose": "Engineering and computing literature.",
            },
            {
                "provider": "GitHub",
                "type": "software_project",
                "priority": "conditional",
                "status": "future_project_discovery_source",
                "purpose": "Existing implementations and project evidence.",
            },
            {
                "provider": "Official documentation/datasets",
                "type": "primary_technical_source",
                "priority": "high",
                "status": "required_where_relevant",
                "purpose": "Technology, dataset and implementation verification.",
            },
        ]

        if "Healthcare" not in domains:
            registry = [
                item
                for item in registry
                if item["provider"] != "PubMed"
                or item["priority"] != "conditional"
            ]

        return registry

    def _build_search_strategy(
        self,
        idea: str,
        normalized_title: str,
        keywords: list[str],
        domains: list[str],
        research_questions: list[str],
    ) -> dict[str, Any]:
        primary = normalized_title

        queries = [
            primary,
            idea,
            " ".join(keywords[:8]),
        ]

        if domains:
            queries.append(
                f"{primary} {' '.join(domains[:3])}"
            )

        return {
            "primary_query": primary,
            "query_variants": list(
                dict.fromkeys(
                    query.strip()
                    for query in queries
                    if query.strip()
                )
            ),
            "research_question_queries": research_questions[:8],
            "default_year_window": "2022-2026",
            "search_modes": [
                "keyword",
                "semantic where provider supports it",
                "metadata expansion",
                "source-specific query refinement",
            ],
            "ranking_priority": [
                "semantic relevance",
                "publication/source quality",
                "recency",
                "citation/context signal",
                "metadata completeness",
            ],
            "deduplication": [
                "DOI/identifier",
                "normalized title",
                "provider identifiers",
            ],
        }

    def _evidence_policy(self) -> dict[str, Any]:
        return {
            "verified_evidence": (
                "Directly supported by an identified external source."
            ),
            "ai_synthesis": (
                "AURA synthesis across multiple identified sources."
            ),
            "aura_recommendation": (
                "AURA proposal or ranking that is not a published fact."
            ),
            "needs_verification": (
                "Insufficient evidence has been retrieved or checked."
            ),
            "high_risk": (
                "Evidence is weak, conflicting, safety-sensitive, "
                "or requires expert review."
            ),
            "prohibited_shortcuts": [
                "Do not scrape Google Scholar without authorized access.",
                "Do not claim IEEE full-text access without authorization.",
                "Do not claim global novelty from a small search.",
                "Do not invent citations, datasets, benchmarks or performance.",
            ],
        }

    # =============================================================
    # CLEANING
    # =============================================================

    def _clean_idea(self, idea: str) -> str:
        text = str(idea or "").strip()
        text = re.sub(r"\s+", " ", text)
        return text

    # =============================================================
    # TITLE NORMALIZATION
    # =============================================================

    def _normalize_title(self, idea: str) -> str:
        text = idea.strip()

        if not text:
            return "Untitled AURA Project"

        return text[:1].upper() + text[1:]

    # =============================================================
    # KEYWORD EXTRACTION
    # =============================================================

    def _extract_keywords(self, text: str) -> list[str]:
        normalized = text.lower()

        corrections = {
            "agriculturre": "agriculture",
            "agricuture": "agriculture",
            "agricultre": "agriculture",
            "agriculuture": "agriculture",
            "agri culture": "agriculture",
            "machne": "machine",
            "learining": "learning",
            "inteligence": "intelligence",
            "artifical": "artificial",
            "technlogy": "technology",
            "robotcs": "robotics",
            "cybersecurty": "cybersecurity",
            "healhcare": "healthcare",
            "medcal": "medical",
        }

        for wrong, correct in corrections.items():
            normalized = normalized.replace(wrong, correct)

        stop_words = {
            "the", "and", "for", "with", "using", "from", "into",
            "that", "this", "based", "system", "project", "application",
            "platform", "develop", "development", "design", "designing",
            "create", "creating", "build", "building", "use", "used",
            "can", "will", "through", "within", "which", "their", "our",
            "your", "its", "are", "is", "of", "to", "in", "on", "a",
            "an", "as", "by", "be", "or", "at", "it", "how", "what",
            "why", "where", "when",
        }

        phrases = [
            "artificial intelligence",
            "machine learning",
            "deep learning",
            "computer vision",
            "smart agriculture",
            "precision agriculture",
            "internet of things",
            "natural language processing",
            "data science",
            "data analytics",
            "cloud computing",
            "cyber security",
            "cybersecurity",
            "large language model",
            "generative ai",
            "agentic ai",
            "smart farming",
            "precision farming",
            "medical image analysis",
            "predictive maintenance",
            "renewable energy",
        ]

        found_phrases: list[str] = []

        for phrase in phrases:
            if phrase in normalized:
                found_phrases.append(phrase)

        words = re.findall(r"[a-zA-Z0-9]+", normalized)
        keywords: list[str] = []

        for phrase in found_phrases:
            if phrase not in keywords:
                keywords.append(phrase)

        for word in words:
            if word in stop_words or len(word) <= 2:
                continue

            if word not in keywords:
                keywords.append(word)

        return keywords[:30]

    # =============================================================
    # DOMAIN DETECTION
    # =============================================================

    def _detect_domains(
        self,
        text: str,
        keywords: list[str],
    ) -> list[str]:
        normalized = text.lower()

        domain_keywords: dict[str, list[str]] = {
            "Artificial Intelligence": [
                "ai", "artificial intelligence", "machine learning", "ml",
                "deep learning", "generative ai", "genai",
                "large language model", "llm", "agentic", "agentic ai",
                "neural network", "intelligent", "prediction", "predictive",
            ],
            "Computer Vision": [
                "computer vision", "image processing", "image recognition",
                "image classification", "object detection",
                "object recognition", "video analysis", "yolo", "yolov8",
                "yolov9", "yolov10", "yolov11", "face recognition",
                "visual", "camera", "image",
            ],
            "Internet of Things": [
                "iot", "internet of things", "sensor", "sensors", "esp32",
                "esp8266", "arduino", "raspberry pi", "mqtt", "lorawan",
                "lora", "embedded", "smart device", "connected device",
            ],
            "Robotics": [
                "robot", "robotics", "ros", "ros2", "autonomous robot",
                "mobile robot", "robotic arm", "drone", "uav",
                "unmanned aerial",
            ],
            "Smart Agriculture": [
                "agriculture", "agricultural", "farming", "smart farming",
                "crop", "crops", "plant", "plants", "hydroponic",
                "hydroponics", "irrigation", "greenhouse", "vertical farming",
                "precision agriculture", "precision farming", "soil",
                "fertilizer", "fertilisation", "fertilization", "livestock",
                "farm",
            ],
            "Healthcare": [
                "medical", "healthcare", "health", "disease", "diagnosis",
                "patient", "patients", "clinical", "hospital",
                "medical image", "biomedical", "medicine", "doctor",
                "diagnostic",
            ],
            "Cybersecurity": [
                "cybersecurity", "cyber security", "security", "malware",
                "ransomware", "intrusion", "intrusion detection", "phishing",
                "network attack", "threat detection", "vulnerability",
                "zero trust", "authentication", "encryption",
            ],
            "Data Science": [
                "data science", "data analytics", "analytics", "data analysis",
                "prediction", "classification", "regression", "dataset",
                "datasets", "data mining", "visualization", "statistics",
                "forecasting",
            ],
            "Cloud Computing": [
                "cloud", "cloud computing", "aws", "azure", "google cloud",
                "serverless", "saas", "paas", "iaas", "cloud platform",
            ],
            "Blockchain": [
                "blockchain", "smart contract", "ethereum", "web3",
                "decentralized", "cryptocurrency", "distributed ledger",
            ],
            "Natural Language Processing": [
                "nlp", "natural language processing", "text classification",
                "sentiment analysis", "language model", "text mining",
                "chatbot", "question answering", "text generation", "speech",
            ],
            "Software Engineering": [
                "software", "web application", "mobile application", "website",
                "platform", "api", "backend", "frontend", "database",
                "full stack", "application", "dashboard",
            ],
            "Renewable Energy": [
                "solar", "wind energy", "renewable energy", "renewable",
                "photovoltaic", "battery", "energy storage", "microgrid",
            ],
            "Education Technology": [
                "education", "learning", "e-learning", "elearning", "student",
                "students", "teacher", "teaching", "classroom", "academic",
                "educational",
            ],
        }

        detected: list[str] = []

        for domain, terms in domain_keywords.items():
            if any(term in normalized for term in terms):
                detected.append(domain)

        if not detected:
            detected.append("General Technology")

        return detected

    # =============================================================
    # INTENT
    # =============================================================

    def _detect_intent(self, idea: str) -> str:
        text = idea.lower()

        intent_rules = [
            (
                "Detection / Identification",
                ["detect", "detection", "identify", "recognize"],
            ),
            (
                "Prediction / Forecasting",
                ["predict", "prediction", "forecast", "forecasting"],
            ),
            (
                "Monitoring / Tracking",
                ["monitor", "monitoring", "track", "tracking"],
            ),
            (
                "Optimization",
                [
                    "optimize", "optimise", "optimization",
                    "optimisation",
                ],
            ),
            (
                "Classification",
                ["classify", "classification"],
            ),
            (
                "Recommendation",
                ["recommend", "recommendation"],
            ),
            (
                "Automation",
                ["automate", "automation", "autonomous"],
            ),
            (
                "Solution Development",
                [
                    "build", "develop", "development", "create",
                    "design", "platform", "system",
                ],
            ),
        ]

        for label, terms in intent_rules:
            if any(term in text for term in terms):
                return label

        return "Problem Investigation / Solution Discovery"

    # =============================================================
    # PROJECT TYPE
    # =============================================================

    def _classify_project_type(
        self,
        idea: str,
        domains: list[str],
    ) -> str:
        text = idea.lower()

        if any(
            value in text
            for value in [
                "research", "research study", "research project",
                "novel", "investigation", "experiment",
            ]
        ):
            return "Research Project"

        if any(
            value in text
            for value in [
                "iot", "sensor", "embedded", "hardware",
                "arduino", "esp32",
            ]
        ):
            return "AI / IoT / Embedded Solution"

        if "Robotics" in domains:
            return "Robotics / Autonomous System"

        if "Artificial Intelligence" in domains:
            return "AI-Enabled Software Solution"

        if "Computer Vision" in domains:
            return "Computer Vision System"

        if "Software Engineering" in domains:
            return "Software / Platform Solution"

        if "Smart Agriculture" in domains:
            return "Smart Agriculture Solution"

        return "Technology Solution"

    # =============================================================
    # PROBLEM DEFINITION
    # =============================================================

    def _build_problem_definition(
        self,
        idea: str,
        domains: list[str],
        project_type: str,
    ) -> str:
        domain_text = ", ".join(domains)

        return (
            f"AURA interprets '{idea}' as a {project_type.lower()} "
            f"opportunity within {domain_text}. The initial task is to "
            "establish the real-world problem, current approaches, "
            "evidence-supported limitations, available technologies, "
            "and feasibility before selecting a final solution."
        )

    # =============================================================
    # TARGET CONTEXT
    # =============================================================

    def _identify_target_context(
        self,
        idea: str,
        domains: list[str],
    ) -> str:
        text = idea.lower()
        targets: list[str] = []

        rules = {
            "farmers": [
                "agriculture", "agricultural", "farming", "farm",
                "crop", "cultivation", "hydroponic", "greenhouse",
                "irrigation",
            ],
            "students": [
                "student", "students", "education", "learning",
                "college", "school", "classroom",
            ],
            "researchers": [
                "research", "researcher", "scientist",
                "laboratory", "experiment",
            ],
            "patients": [
                "patient", "patients", "medical", "healthcare",
                "hospital", "diagnosis",
            ],
            "clinicians": [
                "doctor", "clinician", "clinical", "hospital",
                "diagnostic",
            ],
            "industry / organizations": [
                "industry", "industrial", "manufacturing", "factory",
                "enterprise", "organization", "production",
            ],
            "general users": [
                "user", "users", "customer", "consumer", "public",
            ],
        }

        for target, terms in rules.items():
            if any(term in text for term in terms):
                targets.append(target)

        if not targets:
            if "Smart Agriculture" in domains:
                return "Agricultural stakeholders / farmers"

            return (
                "Target users not explicitly specified; "
                "AURA will refine the target context during investigation."
            )

        return ", ".join(dict.fromkeys(targets))

    # =============================================================
    # STAKEHOLDERS
    # =============================================================

    def _identify_stakeholders(
        self,
        idea: str,
        target_context: str,
        domains: list[str],
    ) -> list[str]:
        text = idea.lower()
        stakeholders: list[str] = []

        if any(
            term in text
            for term in [
                "agriculture", "farming", "crop",
                "hydroponic", "irrigation",
            ]
        ):
            stakeholders.extend(
                [
                    "Farmers",
                    "Agricultural practitioners",
                    "Agricultural researchers",
                ]
            )

        if any(
            term in text
            for term in ["student", "education", "learning"]
        ):
            stakeholders.extend(
                [
                    "Students",
                    "Faculty / educators",
                    "Academic institutions",
                ]
            )

        if any(
            term in text
            for term in ["medical", "healthcare", "patient", "hospital"]
        ):
            stakeholders.extend(
                [
                    "Patients",
                    "Healthcare professionals",
                    "Healthcare organizations",
                ]
            )

        if any(
            term in text
            for term in ["industry", "manufacturing", "factory"]
        ):
            stakeholders.extend(
                [
                    "Industry operators",
                    "Technical teams",
                    "Management / decision makers",
                ]
            )

        if "Artificial Intelligence" in domains:
            stakeholders.append("AI / data practitioners")

        if "Internet of Things" in domains:
            stakeholders.append("IoT / embedded-system practitioners")

        if not stakeholders:
            stakeholders.append(
                "End users identified during investigation"
            )

        return list(dict.fromkeys(stakeholders))

    # =============================================================
    # OBJECTIVES
    # =============================================================

    def _generate_objectives(
        self,
        idea: str,
        domains: list[str],
        project_type: str,
        target_context: str,
    ) -> list[str]:
        objectives = [
            "Define the real-world problem and its context.",
            "Investigate existing research, products, methods and solutions.",
            "Compare existing approaches, technologies and evidence.",
            "Identify limitations, unresolved challenges and research gaps.",
            "Determine whether the problem requires improvement of an existing approach or a new solution.",
            "Design a technically feasible and evidence-backed solution.",
            "Develop, test and experimentally evaluate the proposed solution.",
            "Validate the solution against measurable success criteria.",
        ]

        if "Artificial Intelligence" in domains:
            objectives.insert(
                4,
                "Identify suitable AI/ML methods, models and data requirements.",
            )

        if "Internet of Things" in domains:
            objectives.insert(
                4,
                "Identify appropriate sensing, communication and embedded technologies.",
            )

        if "Smart Agriculture" in domains:
            objectives.insert(
                5,
                "Evaluate agricultural applicability, resource constraints and field feasibility.",
            )

        return list(dict.fromkeys(objectives))

    # =============================================================
    # FUNCTIONAL REQUIREMENTS
    # =============================================================

    def _generate_functional_requirements(
        self,
        idea: str,
        domains: list[str],
        project_type: str,
    ) -> list[str]:
        requirements = [
            "Accept the project problem or operational input.",
            "Process the required project inputs and relevant data.",
            "Produce the intended core system functionality.",
            "Provide measurable outputs or decisions.",
            "Record relevant results for evaluation.",
        ]

        if "Artificial Intelligence" in domains:
            requirements.extend(
                [
                    "Support data preprocessing or preparation.",
                    "Support model selection and evaluation.",
                    "Generate predictions, classifications or intelligent decisions where applicable.",
                ]
            )

        if "Computer Vision" in domains:
            requirements.extend(
                [
                    "Accept image or video input where required.",
                    "Perform the required visual analysis.",
                    "Present visual detection/classification results.",
                ]
            )

        if "Internet of Things" in domains:
            requirements.extend(
                [
                    "Collect sensor or device data.",
                    "Transmit or store collected measurements.",
                    "Provide monitoring or control functionality where required.",
                ]
            )

        if "Smart Agriculture" in domains:
            requirements.extend(
                [
                    "Capture relevant agricultural/environmental parameters.",
                    "Support agricultural monitoring, decision making or optimization.",
                    "Provide outputs that can be interpreted by agricultural stakeholders.",
                ]
            )

        return list(dict.fromkeys(requirements))

    # =============================================================
    # TECHNICAL REQUIREMENTS
    # =============================================================

    def _generate_technical_requirements(
        self,
        idea: str,
        domains: list[str],
    ) -> list[str]:
        requirements = [
            "Define suitable software and development environment.",
            "Determine required data sources and data formats.",
            "Determine measurable evaluation metrics.",
            "Maintain reproducible development and experimentation.",
        ]

        if "Artificial Intelligence" in domains:
            requirements.extend(
                [
                    "Identify suitable AI/ML model families.",
                    "Determine training, validation and testing data requirements.",
                    "Define appropriate model evaluation metrics.",
                ]
            )

        if "Internet of Things" in domains:
            requirements.extend(
                [
                    "Determine appropriate sensors/devices.",
                    "Determine communication protocol requirements.",
                    "Determine edge, gateway or cloud processing requirements.",
                ]
            )

        if "Computer Vision" in domains:
            requirements.extend(
                [
                    "Determine image/video data requirements.",
                    "Determine annotation requirements where supervised learning is needed.",
                    "Define computer-vision evaluation metrics.",
                ]
            )

        if "Smart Agriculture" in domains:
            requirements.extend(
                [
                    "Consider environmental variability and field conditions.",
                    "Consider sensor/data reliability and agricultural measurement constraints.",
                    "Consider scalability and practical deployment conditions.",
                ]
            )

        return list(dict.fromkeys(requirements))

    # =============================================================
    # CONSTRAINTS
    # =============================================================

    def _identify_constraints(
        self,
        idea: str,
        domains: list[str],
        project_type: str,
    ) -> list[str]:
        constraints = [
            "Available time and development resources.",
            "Availability and quality of required data.",
            "Hardware/software availability.",
            "Model or computational resource requirements.",
            "Reproducibility of experiments.",
            "Real-world deployment feasibility.",
        ]

        if "Internet of Things" in domains:
            constraints.extend(
                [
                    "Sensor accuracy and calibration.",
                    "Connectivity and power availability.",
                    "Device cost and maintenance.",
                ]
            )

        if "Artificial Intelligence" in domains:
            constraints.extend(
                [
                    "Dataset size and representativeness.",
                    "Model generalization.",
                    "Computational resources for training/inference.",
                ]
            )

        if "Smart Agriculture" in domains:
            constraints.extend(
                [
                    "Seasonal and environmental variability.",
                    "Field conditions and sensor placement.",
                    "Farmer usability and deployment cost.",
                ]
            )

        return list(dict.fromkeys(constraints))

    # =============================================================
    # RESEARCH QUESTIONS
    # =============================================================

    def _generate_research_questions(
        self,
        idea: str,
        domains: list[str],
        problem: str,
    ) -> list[str]:
        questions = [
            f"What existing solutions and research address '{idea}'?",
            "What methods and technologies are currently used?",
            "What datasets, benchmarks or real-world data are available?",
            "What limitations are repeatedly reported?",
            "Which research gaps remain insufficiently addressed?",
            "Which approaches show the strongest evidence?",
            "What would make a proposed solution meaningfully different?",
            "What experiments are required to validate the solution?",
        ]

        if "Artificial Intelligence" in domains:
            questions.append(
                "Which AI/ML models are most suitable for the identified problem, and why?"
            )

        if "Internet of Things" in domains:
            questions.append(
                "Which sensing, communication and edge/cloud technologies are most suitable?"
            )

        if "Smart Agriculture" in domains:
            questions.extend(
                [
                    "Which agricultural parameters are most important for the identified use case?",
                    "How can the solution remain practical, affordable and usable in real agricultural environments?",
                ]
            )

        return questions

    # =============================================================
    # SUCCESS CRITERIA
    # =============================================================

    def _generate_success_criteria(
        self,
        project_type: str,
        domains: list[str],
    ) -> list[str]:
        criteria = [
            "Clear problem definition.",
            "Evidence-backed understanding of existing work.",
            "Identified research or innovation gap.",
            "Technically feasible architecture.",
            "Reproducible implementation.",
            "Measurable experimental evaluation.",
            "Comparison against appropriate baseline or existing approach.",
            "Documented limitations and future improvements.",
        ]

        if "Artificial Intelligence" in domains:
            criteria.extend(
                [
                    "Appropriate model evaluation metrics.",
                    "Validation on representative test data.",
                ]
            )

        if "Internet of Things" in domains:
            criteria.extend(
                [
                    "Reliable sensing/data acquisition.",
                    "Demonstrated end-to-end device/system operation.",
                ]
            )

        return list(dict.fromkeys(criteria))

    # =============================================================
    # INVESTIGATION FOCUS
    # =============================================================

    def _generate_investigation_focus(
        self,
        idea: str,
        domains: list[str],
        problem: str,
    ) -> list[str]:
        focus = [
            "Existing research papers",
            "Existing products and project implementations",
            "Current technologies and methods",
            "Datasets and data sources",
            "Common architectures",
            "Experimental methods",
            "Evaluation metrics",
            "Reported limitations",
            "Research gaps",
            "Emerging trends",
        ]

        if "Artificial Intelligence" in domains:
            focus.append(
                "AI/ML model families and benchmark performance"
            )

        if "Internet of Things" in domains:
            focus.append(
                "Sensors, communication protocols and edge/cloud architectures"
            )

        if "Smart Agriculture" in domains:
            focus.extend(
                [
                    "Smart farming technologies",
                    "Agricultural sensing and monitoring",
                    "Precision agriculture approaches",
                    "Field deployment challenges",
                ]
            )

        return list(dict.fromkeys(focus))

    # =============================================================
    # UNCERTAINTY
    # =============================================================

    def _identify_uncertainties(
        self,
        idea: str,
        domains: list[str],
        project_type: str,
    ) -> list[str]:
        return [
            "Exact research novelty is not yet established.",
            "Existing competing solutions require investigation.",
            "Available datasets and evidence require investigation.",
            "Final technology selection requires comparative analysis.",
            "Final architecture requires feasibility assessment.",
            "Experimental performance cannot be predicted before validation.",
            "The inferred target context may change after evidence retrieval.",
            "The initial problem interpretation may need revision after source analysis.",
        ]

    # =============================================================
    # CONFIDENCE
    # =============================================================

    def _calculate_understanding_confidence(
        self,
        idea: str,
        domains: list[str],
        keywords: list[str],
        target_context: str,
    ) -> int:
        score = 35

        if len(idea.split()) >= 2:
            score += 10

        if len(keywords) >= 2:
            score += 10

        if domains and domains != ["General Technology"]:
            score += 20

        if (
            target_context
            and "not explicitly specified"
            not in target_context.lower()
        ):
            score += 15

        return min(score, 90)


idea_intelligence_agent = IdeaIntelligenceAgent()
