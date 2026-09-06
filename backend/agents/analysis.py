from __future__ import annotations

import re
from collections import Counter
from typing import Any

from models.project import AURAProject
from orchestration.contract import AURAStageResult
from orchestration.stages import AURAStage


class AnalysisAgent:
    """AURA Stage 03 — evidence-aware research intelligence analysis."""

    stage = AURAStage.ANALYZE

    async def run(self, project: AURAProject) -> AURAStageResult:
        papers = self._get_papers(project)
        if not papers:
            return AURAStageResult(
                stage=self.stage,
                success=False,
                message="AURA cannot perform research analysis because no literature records were available.",
            )

        idea = self._clean_text(project.original_idea)
        research = project.research if isinstance(project.research, dict) else {}

        corpus = self._build_corpus(papers)
        claim_analysis = self._analyze_claim_register(project, papers)
        themes = self._extract_themes(papers, corpus)
        technologies = self._extract_technologies(papers, corpus)
        methods = self._extract_methods(papers, corpus)
        datasets = self._extract_datasets(papers, corpus)
        application_areas = self._extract_application_areas(papers, corpus)
        limitations = self._extract_limitations(papers, corpus)
        challenges = self._extract_challenges(papers, corpus)
        findings = self._extract_findings(papers)
        trends = self._build_trends(papers)
        source_distribution = self._build_source_distribution(papers, project)
        year_distribution = self._build_year_distribution(papers)
        evidence_quality = self._evaluate_evidence_quality(papers, project, claim_analysis)
        relevance = self._evaluate_relevance(papers, idea)
        research_patterns = self._build_research_patterns(
            themes, technologies, methods, datasets, limitations, challenges, trends
        )
        opportunities = self._build_opportunities(
            themes, technologies, methods, datasets, limitations, challenges, project
        )
        conflicts = self._detect_conflicts(papers)
        evidence_synthesis = self._build_evidence_synthesis(
            claim_analysis, themes, limitations, challenges, opportunities
        )
        analytical_summary = self._build_summary(
            idea, papers, themes, technologies, methods, datasets,
            limitations, challenges, trends, opportunities, conflicts,
            claim_analysis,
        )

        analysis_data: dict[str, Any] = {
            "status": "completed",
            "analysis_type": "evidence_driven_cross_source_research_intelligence",
            "research_question": idea,
            "corpus": {
                "papers_analyzed": len(papers),
                "analysis_scope": "retrieved scholarly metadata and available abstracts",
                "default_window": "2022-2026",
            },
            "summary": analytical_summary,
            "claim_analysis": claim_analysis,
            "evidence_synthesis": evidence_synthesis,
            "themes": themes,
            "technologies": technologies,
            "methods": methods,
            "datasets": datasets,
            "application_areas": application_areas,
            "findings": findings,
            "limitations": limitations,
            "challenges": challenges,
            "trends": trends,
            "research_patterns": research_patterns,
            "opportunities": opportunities,
            "conflicts": conflicts,
            "source_distribution": source_distribution,
            "year_distribution": year_distribution,
            "evidence_quality": evidence_quality,
            "relevance_analysis": relevance,
            "verification_policy": {
                "unsupported_claims": False,
                "global_novelty_claim": False,
                "source_provenance_required": True,
                "claim_to_evidence_trace_required": True,
                "conflicting_evidence_flagged": True,
                "metadata_vs_claim_distinction": True,
                "uncovered_claims_flagged": True,
            },
            "analysis_notes": [
                "AURA separates retrieved evidence from AI synthesis.",
                "Claim coverage is calculated from the INVESTIGATE claim register and evidence map.",
                "Recurring patterns are evidence-derived signals, not proof of scientific truth.",
                "Novelty is not established at ANALYZE and must be evaluated by VERDICT.",
            ],
        }

        if not isinstance(project.analysis, dict):
            project.analysis = {}
        project.analysis["research_intelligence"] = analysis_data
        for key in (
            "themes", "technologies", "methods", "datasets", "limitations",
            "challenges", "trends", "opportunities", "conflicts",
        ):
            project.analysis[key] = analysis_data[key]
        project.analysis["claim_analysis"] = claim_analysis
        project.analysis["evidence_synthesis"] = evidence_synthesis
        # Surface canonical analysis values at the top level so downstream
        # UI, delivery and validation consumers do not have to know the
        # internal research_intelligence nesting.
        project.analysis["findings"] = findings
        project.analysis["canonical_findings"] = findings
        project.analysis["claim_evidence_coverage_percent"] = claim_analysis.get(
            "coverage_percent", 0
        )
        project.analysis["claims_with_evidence"] = claim_analysis.get(
            "claims_with_evidence", 0
        )
        project.analysis["claims_without_evidence"] = claim_analysis.get(
            "claims_without_evidence", 0
        )
        project.analysis["claim_count"] = claim_analysis.get(
            "claim_count", 0
        )

        self._append_analysis_evidence(project, papers, themes, technologies, methods, limitations, opportunities, claim_analysis)
        self._append_memory(project, {
            "type": "research_analysis",
            "stage": "ANALYZE",
            "papers_analyzed": len(papers),
            "claims_analyzed": claim_analysis["claim_count"],
            "claims_with_evidence": claim_analysis["claims_with_evidence"],
            "claims_without_evidence": claim_analysis["claims_without_evidence"],
            "evidence_coverage_percent": claim_analysis["coverage_percent"],
            "dominant_themes": [x.get("theme") for x in themes[:5] if isinstance(x, dict)],
            "key_technologies": [x.get("technology") for x in technologies[:8] if isinstance(x, dict)],
            "major_limitations": [x.get("limitation") for x in limitations[:5] if isinstance(x, dict)],
            "opportunity_count": len(opportunities),
        })

        return AURAStageResult(
            stage=self.stage,
            success=True,
            message="AURA completed evidence-driven cross-source research intelligence analysis.",
            data=analysis_data,
            next_stage=AURAStage.VERDICT,
        )

    # ------------------------------------------------------------------
    # CLAIM + EVIDENCE ANALYSIS
    # ------------------------------------------------------------------

    def _analyze_claim_register(self, project: AURAProject, papers: list[dict[str, Any]]) -> dict[str, Any]:
        research = project.research if isinstance(project.research, dict) else {}
        register = research.get("claim_register", [])
        evidence_map = research.get("claim_evidence_map", {})
        evidence_records = research.get("evidence_records", [])

        if not isinstance(register, list):
            register = []
        if not isinstance(evidence_map, dict):
            evidence_map = {}
        if not isinstance(evidence_records, list):
            evidence_records = []

        normalized_claims: list[dict[str, Any]] = []
        linked = 0
        unlinked = 0
        high = medium = low = 0

        for index, raw in enumerate(register, 1):
            if not isinstance(raw, dict):
                continue
            claim_id = str(raw.get("claim_id") or raw.get("id") or f"CL-{index:03d}")
            text = self._clean_text(raw.get("claim") or raw.get("statement") or raw.get("text"))
            # Resolve evidence links from every supported INVESTIGATE representation.
            # Stage 02 may store links directly on the claim, in the claim-evidence map,
            # or through evidence records / retrieved paper identifiers.
            # INVESTIGATE stores claim/evidence relations as:
            # {"mappings": [{"claim_id": ..., "candidate_supporting_evidence": [...]}, ...]}
            # Older callers may provide a direct {claim_id: [...]} mapping.
            links: list[Any] = []
            raw_links = evidence_map.get(claim_id, [])
            if isinstance(raw_links, list):
                links.extend(raw_links)
            elif raw_links:
                links.append(raw_links)

            mapping_rows = evidence_map.get("mappings", [])
            if isinstance(mapping_rows, list):
                for mapping in mapping_rows:
                    if not isinstance(mapping, dict):
                        continue
                    if str(mapping.get("claim_id", "")) != claim_id:
                        continue
                    candidate_ids = mapping.get("candidate_supporting_evidence", [])
                    if isinstance(candidate_ids, list):
                        links.extend(candidate_ids)
                    supporting = mapping.get("supporting_evidence", [])
                    if isinstance(supporting, list):
                        links.extend(supporting)

            # The enriched legacy claim uses supporting_evidence_ids.
            direct_ids = raw.get("evidence_ids", raw.get("supporting_evidence_ids", []))
            if not isinstance(direct_ids, list):
                direct_ids = [direct_ids] if direct_ids else []

            combined_links = list(links) + list(direct_ids)
            link_ids: list[str] = []
            for item in combined_links:
                if isinstance(item, dict):
                    evidence_id = item.get("evidence_id") or item.get("id") or item.get("paper_id") or item.get("source_id")
                    if evidence_id:
                        link_ids.append(str(evidence_id))
                elif item:
                    link_ids.append(str(item))

            # If the claim points to a retrieved paper ID, recognize that paper as
            # evidence even when a separate evidence_records object is unavailable.
            paper_ids: set[str] = set()
            for paper in papers:
                for key in ("evidence_id", "paper_id", "id", "work_id", "openalex_id", "doi"):
                    value = paper.get(key)
                    if value:
                        paper_ids.add(str(value))

            resolved_ids = []
            seen = set()
            for evidence_id in link_ids:
                if evidence_id and evidence_id != "None" and evidence_id not in seen:
                    seen.add(evidence_id)
                    resolved_ids.append(evidence_id)

            # Preserve the traceability IDs even if their detailed evidence record is
            # not present; the retrieved paper corpus is itself the evidence package.
            supported = bool(resolved_ids)
            link_ids = resolved_ids
            if supported:
                linked += 1
            else:
                unlinked += 1

            confidence = str(raw.get("confidence") or raw.get("verification_status") or "unknown").lower()
            if "high" in confidence or "verified" in confidence:
                high += 1
            elif "medium" in confidence or "partial" in confidence:
                medium += 1
            else:
                low += 1

            normalized_claims.append({
                "claim_id": claim_id,
                "claim": text,
                "source_stage": raw.get("source_stage", "INVESTIGATE"),
                "evidence_ids": link_ids,
                "evidence_count": len(link_ids),
                "evidence_status": "linked" if supported else "uncovered",
                "verification_status": raw.get("verification_status", "requires_review" if not supported else "evidence_linked"),
                "confidence": raw.get("confidence", "unknown"),
                "source_provenance": raw.get("source_provenance", raw.get("provider", "unknown")),
            })

        count = len(normalized_claims)
        coverage = round((linked / count) * 100, 2) if count else 0.0
        evidence_strength = self._claim_evidence_strength(normalized_claims, evidence_records)

        return {
            "status": "analyzed",
            "claim_count": count,
            "claims_with_evidence": linked,
            "claims_without_evidence": unlinked,
            "coverage_percent": coverage,
            "coverage_status": "strong" if coverage >= 85 else "partial" if coverage >= 60 else "limited" if count else "unavailable",
            "high_confidence_claims": high,
            "medium_confidence_claims": medium,
            "low_or_unknown_confidence_claims": low,
            "claims": normalized_claims,
            "evidence_record_count": len(evidence_records),
            "evidence_strength": evidence_strength,
            "uncovered_claim_ids": [x["claim_id"] for x in normalized_claims if x["evidence_status"] == "uncovered"],
            "traceability": "claim → evidence → synthesis",
        }

    def _claim_evidence_strength(self, claims: list[dict[str, Any]], evidence_records: list[dict[str, Any]]) -> dict[str, Any]:
        by_id = {str(x.get("evidence_id")): x for x in evidence_records if isinstance(x, dict) and x.get("evidence_id")}
        scores: list[float] = []
        for claim in claims:
            linked = [by_id.get(str(eid)) for eid in claim.get("evidence_ids", [])]
            linked = [x for x in linked if x]
            if not linked:
                scores.append(0.0)
                continue
            score = 0.0
            for item in linked:
                status = str(item.get("verification_status", "")).lower()
                level = str(item.get("evidence_level", "")).lower()
                if "verified" in status:
                    score += 1.0
                elif "retrieved" in status or "linked" in status:
                    score += 0.8
                else:
                    score += 0.5
                if "metadata" in level:
                    score *= 0.85
            scores.append(min(score / max(len(linked), 1), 1.0) * 100)
        avg = round(sum(scores) / len(scores), 2) if scores else 0.0
        return {
            "average_claim_evidence_strength_percent": avg,
            "interpretation": "Evidence-link strength is a traceability signal, not scientific certainty.",
        }

    def _build_evidence_synthesis(self, claim_analysis: dict[str, Any], themes: list[dict[str, Any]], limitations: list[dict[str, Any]], challenges: list[dict[str, Any]], opportunities: list[dict[str, Any]]) -> dict[str, Any]:
        covered = claim_analysis["claims_with_evidence"]
        total = claim_analysis["claim_count"]
        return {
            "evidence_base": {
                "claims": total,
                "covered_claims": covered,
                "uncovered_claims": claim_analysis["claims_without_evidence"],
                "coverage_percent": claim_analysis["coverage_percent"],
            },
            "supported_patterns": [
                {
                    "pattern": x.get("theme"),
                    "paper_count": x.get("paper_count", 0),
                    "evidence_status": x.get("evidence_status", "metadata_supported"),
                }
                for x in themes[:8]
            ],
            "limitation_signals": [x.get("limitation") for x in limitations[:8]],
            "challenge_signals": [x.get("challenge") for x in challenges[:8]],
            "derived_opportunities": [
                {"opportunity_id": x.get("opportunity_id"), "trigger": x.get("trigger")}
                for x in opportunities[:10]
            ],
            "uncovered_claim_warning": "Claims without linked evidence must not be presented as verified findings.",
        }

    # ------------------------------------------------------------------
    # PAPER / CORPUS
    # ------------------------------------------------------------------

    def _get_papers(self, project: AURAProject) -> list[dict[str, Any]]:
        research = project.research if isinstance(project.research, dict) else {}
        papers = research.get("papers", [])
        return [x for x in papers if isinstance(x, dict)] if isinstance(papers, list) else []

    def _build_corpus(self, papers: list[dict[str, Any]]) -> str:
        parts: list[str] = []
        for paper in papers:
            for key in ("title", "abstract", "keywords", "topics", "concepts", "venue", "journal", "summary", "description"):
                value = paper.get(key)
                if isinstance(value, list):
                    parts.extend(str(item) for item in value)
                elif value is not None:
                    parts.append(str(value))
        return " ".join(parts)

    # ------------------------------------------------------------------
    # EXTRACTION
    # ------------------------------------------------------------------

    def _extract_themes(self, papers: list[dict[str, Any]], corpus: str) -> list[dict[str, Any]]:
        terms = {
            "artificial intelligence": ["artificial intelligence", "machine intelligence"],
            "machine learning": ["machine learning", "ml model", "learning model"],
            "deep learning": ["deep learning", "neural network", "cnn", "transformer"],
            "computer vision": ["computer vision", "image classification", "object detection", "image processing"],
            "iot": ["internet of things", "iot", "sensor network", "smart sensor"],
            "smart agriculture": ["smart agriculture", "precision agriculture", "smart farming", "precision farming"],
            "remote sensing": ["remote sensing", "satellite imagery", "satellite image", "drone imagery"],
            "crop monitoring": ["crop monitoring", "crop health", "plant monitoring", "crop disease"],
            "prediction": ["prediction", "predictive", "forecasting", "forecast"],
            "classification": ["classification", "classifier"],
            "optimization": ["optimization", "optimisation", "optimal"],
            "sustainability": ["sustainable", "sustainability", "resource efficiency"],
        }
        return self._rank_pattern_groups(papers, corpus, terms, "theme")[:15]

    def _extract_technologies(self, papers: list[dict[str, Any]], corpus: str) -> list[dict[str, Any]]:
        return self._rank_terms(papers, corpus, ["Python", "TensorFlow", "PyTorch", "YOLO", "YOLOv8", "CNN", "Transformer", "Random Forest", "XGBoost", "SVM", "Arduino", "ESP32", "Raspberry Pi", "LoRa", "MQTT", "Edge AI", "Cloud Computing", "Computer Vision", "Remote Sensing"], "technology")

    def _extract_methods(self, papers: list[dict[str, Any]], corpus: str) -> list[dict[str, Any]]:
        return self._rank_terms(papers, corpus, ["classification", "regression", "object detection", "image segmentation", "transfer learning", "deep learning", "machine learning", "feature extraction", "time series forecasting", "clustering", "optimization", "anomaly detection", "predictive modeling", "data fusion", "sensor fusion"], "method")

    def _extract_datasets(self, papers: list[dict[str, Any]], corpus: str) -> list[dict[str, Any]]:
        return self._rank_terms(papers, corpus, ["PlantVillage", "ImageNet", "COCO", "CIFAR-10", "CIFAR-100", "Kaggle", "UCI", "Sentinel-2", "Landsat", "MODIS", "custom dataset", "real-world dataset"], "dataset")

    def _extract_application_areas(self, papers: list[dict[str, Any]], corpus: str) -> list[dict[str, Any]]:
        return self._rank_terms(papers, corpus, ["crop monitoring", "crop disease detection", "yield prediction", "irrigation management", "soil monitoring", "weed detection", "pest detection", "plant health", "smart irrigation", "farm automation", "resource optimization", "agricultural decision support"], "application")

    def _extract_limitations(self, papers: list[dict[str, Any]], corpus: str) -> list[dict[str, Any]]:
        return self._rank_phrase_patterns(papers, corpus, ["limited dataset", "small dataset", "limited data", "lack of data", "data scarcity", "limited generalization", "poor generalization", "generalization", "real-world", "field conditions", "environmental conditions", "computational cost", "high computational", "resource constrained", "limited scalability", "scalability", "noise", "data imbalance", "class imbalance", "lighting conditions", "weather conditions", "sensor noise", "future work", "limitation", "limitations"], "limitation")

    def _extract_challenges(self, papers: list[dict[str, Any]], corpus: str) -> list[dict[str, Any]]:
        return self._rank_phrase_patterns(papers, corpus, ["accuracy", "robustness", "generalization", "scalability", "deployment", "interpretability", "explainability", "privacy", "security", "energy consumption", "latency", "data availability", "data quality", "real-time", "real time", "cost", "connectivity"], "challenge")

    def _extract_findings(self, papers: list[dict[str, Any]]) -> list[dict[str, Any]]:
        findings = []
        for index, paper in enumerate(papers[:30], 1):
            title = self._first_value(paper, ["title", "paper_title"])
            abstract = self._first_value(paper, ["abstract", "summary", "description"])
            if not title or not abstract:
                continue
            findings.append({
                "finding_id": f"F-{index:03d}",
                "title": str(title),
                "finding": self._clean_sentence(str(abstract)),
                "source": self._first_value(paper, ["provider", "source"], "Unknown"),
                "year": self._first_value(paper, ["year", "publication_year"]),
                "evidence_status": "abstract_or_metadata_supported",
                "verification_note": "Verify against full text before treating the abstract-derived statement as a definitive scientific finding.",
            })
        return findings

    def _rank_pattern_groups(self, papers: list[dict[str, Any]], corpus: str, groups: dict[str, list[str]], field: str) -> list[dict[str, Any]]:
        out = []
        lower = corpus.lower()
        for name, patterns in groups.items():
            mentions = sum(lower.count(p.lower()) for p in patterns)
            if mentions:
                out.append({field: name, "mention_count": mentions, "paper_count": self._count_papers_matching(papers, patterns), "evidence_status": "metadata_supported"})
        out.sort(key=lambda x: (x["paper_count"], x["mention_count"]), reverse=True)
        return out

    def _rank_terms(self, papers: list[dict[str, Any]], corpus: str, terms: list[str], field_name: str) -> list[dict[str, Any]]:
        lower = corpus.lower()
        out = []
        for term in terms:
            mentions = lower.count(term.lower())
            if mentions:
                out.append({field_name: term, "mention_count": mentions, "paper_count": self._count_papers_matching(papers, [term]), "evidence_status": "metadata_supported"})
        out.sort(key=lambda x: (x["paper_count"], x["mention_count"]), reverse=True)
        return out[:15]

    def _rank_phrase_patterns(self, papers: list[dict[str, Any]], corpus: str, patterns: list[str], field_name: str) -> list[dict[str, Any]]:
        lower = corpus.lower()
        out = []
        for pattern in patterns:
            count = lower.count(pattern.lower())
            if count:
                out.append({field_name: pattern, "mention_count": count, "paper_count": self._count_papers_matching(papers, [pattern]), "evidence_status": "metadata_supported"})
        out.sort(key=lambda x: (x["paper_count"], x["mention_count"]), reverse=True)
        return out[:15]

    def _count_papers_matching(self, papers: list[dict[str, Any]], patterns: list[str]) -> int:
        count = 0
        for paper in papers:
            text = " ".join(str(paper.get(k, "")) for k in ("title", "abstract", "summary", "description", "keywords", "topics", "concepts")).lower()
            if any(p.lower() in text for p in patterns):
                count += 1
        return count

    # ------------------------------------------------------------------
    # TRENDS / SOURCES / QUALITY
    # ------------------------------------------------------------------

    def _build_trends(self, papers: list[dict[str, Any]]) -> dict[str, Any]:
        counts = Counter()
        for paper in papers:
            year = self._first_value(paper, ["year", "publication_year"])
            try:
                counts[int(year)] += 1
            except (TypeError, ValueError):
                pass
        ordered = [{"year": y, "papers": c} for y, c in sorted(counts.items())]
        direction = "insufficient_data"
        if len(ordered) >= 2:
            direction = "increasing" if ordered[-1]["papers"] > ordered[0]["papers"] else "decreasing" if ordered[-1]["papers"] < ordered[0]["papers"] else "stable"
        return {"publication_trend": direction, "year_distribution": ordered, "trend_interpretation": "Retrieval-level publication direction is not a complete measure of research importance."}

    def _build_source_distribution(self, papers: list[dict[str, Any]], project: AURAProject) -> dict[str, Any]:
        counts = Counter(str(self._first_value(p, ["provider", "source"], "Unknown")) for p in papers)
        statuses = []
        research = project.research if isinstance(project.research, dict) else {}
        stats = research.get("provider_stats", [])
        if isinstance(stats, list):
            for item in stats:
                if isinstance(item, dict):
                    statuses.append({"provider": item.get("provider", "Unknown"), "status": item.get("status", "unknown"), "count": item.get("count", 0), "retrieval_mode": item.get("retrieval_mode", "unknown")})
        return {"paper_distribution": [{"provider": p, "papers": c} for p, c in counts.most_common()], "provider_status": statuses}

    def _build_year_distribution(self, papers: list[dict[str, Any]]) -> list[dict[str, Any]]:
        counts = Counter()
        for p in papers:
            try:
                counts[int(self._first_value(p, ["year", "publication_year"]))] += 1
            except (TypeError, ValueError):
                pass
        return [{"year": y, "papers": c} for y, c in sorted(counts.items())]

    def _evaluate_evidence_quality(self, papers: list[dict[str, Any]], project: AURAProject, claim_analysis: dict[str, Any]) -> dict[str, Any]:
        providers = {str(self._first_value(p, ["provider", "source"], "Unknown")) for p in papers}
        dois = sum(bool(self._first_value(p, ["doi", "DOI"])) for p in papers)
        abstracts = sum(bool(self._first_value(p, ["abstract", "summary"])) for p in papers)
        score = 0
        if len(providers) >= 2: score += 20
        if len(providers) >= 4: score += 15
        if dois: score += 20
        if abstracts: score += 20
        if len(papers) >= 10: score += 15
        if claim_analysis["coverage_percent"] >= 80: score += 10
        score = min(score, 100)
        return {
            "score": score,
            "level": "strong" if score >= 80 else "moderate" if score >= 60 else "limited" if score >= 40 else "weak",
            "papers": len(papers),
            "providers": len(providers),
            "records_with_doi": dois,
            "records_with_abstract": abstracts,
            "claim_evidence_coverage_percent": claim_analysis["coverage_percent"],
            "warning": "Metadata and abstract evidence are not equivalent to full-text scientific verification.",
        }

    def _evaluate_relevance(self, papers: list[dict[str, Any]], idea: str) -> dict[str, Any]:
        idea_tokens = set(self._tokenize(idea))
        records = []
        for paper in papers:
            title = self._first_value(paper, ["title", "paper_title"], "")
            abstract = self._first_value(paper, ["abstract", "summary"], "")
            tokens = set(self._tokenize(f"{title} {abstract}"))
            similarity = round(len(idea_tokens & tokens) / len(idea_tokens) * 100, 2) if idea_tokens else 0.0
            records.append({"title": title, "relevance_percent": min(similarity, 100)})
        records.sort(key=lambda x: x["relevance_percent"], reverse=True)
        avg = round(sum(x["relevance_percent"] for x in records) / len(records), 2) if records else 0
        return {"average_relevance_percent": avg, "top_records": records[:10], "method": "transparent token-overlap relevance using available metadata; not semantic proof of relevance"}

    # ------------------------------------------------------------------
    # PATTERNS / OPPORTUNITIES / CONFLICTS
    # ------------------------------------------------------------------

    def _build_research_patterns(self, themes, technologies, methods, datasets, limitations, challenges, trends):
        patterns = []
        for title, values, label in [
            ("Dominant research themes", themes, "theme"),
            ("Technology concentration", technologies, "technology"),
            ("Method concentration", methods, "method"),
            ("Dataset concentration", datasets, "dataset"),
            ("Recurring limitations", limitations, "limitation"),
            ("Recurring challenges", challenges, "challenge"),
        ]:
            if values:
                patterns.append({"pattern": title, "evidence": [x.get(label) for x in values[:8]], "interpretation": "Observed repeatedly in the retrieved metadata corpus."})
        patterns.append({"pattern": "Publication trend", "evidence": trends.get("year_distribution", []), "interpretation": trends.get("trend_interpretation", "")})
        return patterns

    def _build_opportunities(self, themes, technologies, methods, datasets, limitations, challenges, project):
        out = []
        for item in limitations[:8]:
            value = item.get("limitation", "unspecified limitation")
            out.append(self._opportunity(len(out) + 1, value, "limitation"))
        for item in challenges[:7]:
            value = item.get("challenge", "unspecified challenge")
            out.append(self._opportunity(len(out) + 1, value, "challenge"))
        return out[:15]

    def _opportunity(self, index: int, trigger: str, kind: str) -> dict[str, Any]:
        return {
            "opportunity_id": f"OP-{index:03d}",
            "opportunity": f"Investigate approaches that address {trigger}.",
            "trigger": trigger,
            "trigger_type": kind,
            "evidence_status": "derived_from_recurring_metadata_pattern",
            "novelty_status": "not_yet_determined",
            "recommendation_status": "AURA_RECOMMENDATION",
        }

    def _detect_conflicts(self, papers: list[dict[str, Any]]) -> list[dict[str, Any]]:
        values = []
        for paper in papers:
            title = self._first_value(paper, ["title"], "Unknown")
            text = " ".join(str(paper.get(k, "")) for k in ("title", "abstract", "summary", "description"))
            for match in re.findall(r"(\d{1,3}(?:\.\d+)?)\s*%", text):
                try:
                    value = float(match)
                    if 0 <= value <= 100:
                        values.append((str(title), value))
                except ValueError:
                    pass
        if len(values) < 2:
            return []
        return [{
            "type": "performance_value_variation",
            "records": [{"title": t, "percentage": v} for t, v in values[:20]],
            "interpretation": "Different percentages were found in metadata. They cannot be directly compared without checking datasets, metrics and evaluation protocols.",
            "verification_status": "requires_full_text_review",
        }]

    def _build_summary(self, idea, papers, themes, technologies, methods, datasets, limitations, challenges, trends, opportunities, conflicts, claim_analysis):
        return {
            "idea": idea,
            "papers_analyzed": len(papers),
            "claim_count": claim_analysis["claim_count"],
            "claim_evidence_coverage_percent": claim_analysis["coverage_percent"],
            "dominant_themes": [x.get("theme") for x in themes[:5]],
            "dominant_technologies": [x.get("technology") for x in technologies[:8]],
            "dominant_methods": [x.get("method") for x in methods[:8]],
            "observed_datasets": [x.get("dataset") for x in datasets[:8]],
            "recurring_limitations": [x.get("limitation") for x in limitations[:8]],
            "recurring_challenges": [x.get("challenge") for x in challenges[:8]],
            "publication_trend": trends.get("publication_trend", "insufficient_data"),
            "candidate_opportunities": len(opportunities),
            "conflict_groups": len(conflicts),
            "research_landscape_statement": "The retrieved evidence package shows recurring research patterns and traceable claim/evidence relationships. These signals feed AURA VERDICT; they do not independently establish novelty or scientific truth.",
        }

    # ------------------------------------------------------------------
    # EVIDENCE + MEMORY
    # ------------------------------------------------------------------

    def _append_analysis_evidence(self, project, papers, themes, technologies, methods, limitations, opportunities, claim_analysis):
        if not isinstance(project.evidence, list):
            project.evidence = []
        base = len(project.evidence)
        for i, claim in enumerate(claim_analysis.get("claims", [])[:40], 1):
            project.evidence.append({
                "evidence_id": f"ANL-C-{base+i:03d}",
                "type": "claim_analysis",
                "stage": "ANALYZE",
                "claim": claim.get("claim"),
                "support": {"claim_id": claim.get("claim_id"), "evidence_ids": claim.get("evidence_ids", [])},
                "verification_status": claim.get("evidence_status", "uncovered"),
                "evidence_level": "claim_evidence_trace",
            })
        start = len(project.evidence)
        for i, item in enumerate(themes[:10], 1):
            project.evidence.append({"evidence_id": f"ANL-T-{start+i:03d}", "type": "analytical_theme", "stage": "ANALYZE", "claim": f"Recurring research theme: {item.get('theme')}", "support": {"paper_count": item.get("paper_count", 0), "mention_count": item.get("mention_count", 0)}, "verification_status": "metadata_pattern", "evidence_level": "synthesized_metadata"})
        start = len(project.evidence)
        for i, item in enumerate(limitations[:10], 1):
            project.evidence.append({"evidence_id": f"ANL-L-{start+i:03d}", "type": "analytical_limitation", "stage": "ANALYZE", "claim": f"Recurring limitation signal: {item.get('limitation')}", "support": {"paper_count": item.get("paper_count", 0)}, "verification_status": "metadata_pattern", "evidence_level": "synthesized_metadata"})
        start = len(project.evidence)
        for i, item in enumerate(opportunities[:10], 1):
            project.evidence.append({"evidence_id": f"ANL-O-{start+i:03d}", "type": "research_opportunity", "stage": "ANALYZE", "claim": item.get("opportunity"), "support": {"trigger": item.get("trigger")}, "verification_status": "candidate_opportunity", "evidence_level": "ai_synthesis", "novelty_status": "not_yet_determined"})

    def _append_memory(self, project, record):
        if not isinstance(project.memory, list):
            project.memory = []
        project.memory.append(record)

    # ------------------------------------------------------------------
    # HELPERS
    # ------------------------------------------------------------------

    @staticmethod
    def _clean_text(value: Any) -> str:
        return " ".join(str(value or "").strip().split())

    @staticmethod
    def _clean_sentence(value: str) -> str:
        cleaned = " ".join(value.strip().split())
        return cleaned if len(cleaned) <= 700 else cleaned[:697].rstrip() + "..."

    @staticmethod
    def _tokenize(value: str) -> list[str]:
        return re.findall(r"[a-zA-Z0-9]+", value.lower())

    @staticmethod
    def _first_value(data: dict[str, Any], keys: list[str], default: Any = None) -> Any:
        for key in keys:
            value = data.get(key)
            if value is None:
                continue
            if isinstance(value, str):
                if value.strip():
                    return value.strip()
            else:
                return value
        return default


analysis_agent = AnalysisAgent()
