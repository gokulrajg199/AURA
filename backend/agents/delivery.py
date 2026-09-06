from __future__ import annotations

from typing import Any

from models.project import AURAProject
from orchestration.contract import AURAStageResult
from orchestration.stages import AURAStage


class DeliveryAgent:
    """
    AURA — Final Delivery Intelligence Engine

    Converts the complete AURA project journey into structured,
    evidence-aware delivery outputs.

    Important:
        Generated plans/drafts are not equivalent to verified results.
        AURA never fabricates citations, experimental results,
        implementation status or novelty claims.
    """

    stage = AURAStage.DELIVER

    async def run(
        self,
        project: AURAProject,
    ) -> AURAStageResult:

        try:
            deliverables = self._build_delivery_package(project)

            project.deliverables = deliverables
            project.analysis["delivery"] = deliverables

            self._store_memory(project, deliverables)
            self._store_evidence(project, deliverables)

            return AURAStageResult(
                stage=self.stage,
                success=True,
                message=(
                    "AURA completed the final evidence-aware "
                    "project delivery package."
                ),
                data={
                    "deliverables": deliverables,
                },
                next_stage=None,
            )

        except Exception as error:
            return AURAStageResult(
                stage=self.stage,
                success=False,
                message=f"Delivery generation failed: {error}",
            )

    # ================================================================
    # MAIN DELIVERY PACKAGE
    # ================================================================

    def _build_delivery_package(
        self,
        project: AURAProject,
    ) -> dict[str, Any]:

        research = self._as_dict(project.research)

        analysis = self._as_dict(
            project.analysis.get(
                "research_intelligence",
                {},
            )
        )

        verdict = self._as_dict(
            project.analysis.get(
                "verdict",
                {},
            )
        )

        innovation = self._as_dict(
            project.innovation
        )

        solution = self._as_dict(
            project.solution
        )

        architecture = self._as_dict(
            project.architecture
        )

        development = self._as_dict(
            project.development
        )

        experiments = self._as_dict(
            project.experiments
        )

        validation = self._as_dict(
            project.validation
        )

        evidence = [
            item
            for item in project.evidence
            if isinstance(item, dict)
        ]

        claims = self._extract_claims(
            research,
            analysis,
        )

        evidence_summary = self._build_evidence_summary(
            project=project,
            research=research,
            analysis=analysis,
            validation=validation,
            evidence=evidence,
        )

        project_summary = self._build_project_summary(
            project=project,
            verdict=verdict,
            innovation=innovation,
            solution=solution,
            evidence_summary=evidence_summary,
        )

        report = self._build_project_report(
            project=project,
            research=research,
            analysis=analysis,
            verdict=verdict,
            innovation=innovation,
            solution=solution,
            architecture=architecture,
            development=development,
            experiments=experiments,
            validation=validation,
        )

        research_paper = self._build_research_paper(
            project=project,
            research=research,
            analysis=analysis,
            verdict=verdict,
            innovation=innovation,
            solution=solution,
            experiments=experiments,
            validation=validation,
            claims=claims,
        )

        presentation = self._build_presentation(
            project=project,
            summary=project_summary,
            verdict=verdict,
            innovation=innovation,
            solution=solution,
            architecture=architecture,
            development=development,
            experiments=experiments,
            validation=validation,
        )

        sih_pitch = self._build_sih_pitch(
            project=project,
            verdict=verdict,
            innovation=innovation,
            solution=solution,
            validation=validation,
            evidence_summary=evidence_summary,
        )

        demo_plan = self._build_demo_plan(
            project=project,
            solution=solution,
            architecture=architecture,
            development=development,
            validation=validation,
        )

        viva = self._build_viva_package(
            project=project,
            analysis=analysis,
            verdict=verdict,
            innovation=innovation,
            solution=solution,
            validation=validation,
            evidence_summary=evidence_summary,
        )

        implementation_documentation = (
            self._build_implementation_documentation(
                project=project,
                architecture=architecture,
                development=development,
                experiments=experiments,
                validation=validation,
            )
        )

        claim_evidence_matrix = (
            self._build_claim_evidence_matrix(
                project=project,
                claims=claims,
                analysis=analysis,
                research=research,
            )
        )

        citation_package = self._build_citation_package(
            project=project,
            research=research,
        )

        execution_summary = self._build_execution_summary(
            project=project,
            experiments=experiments,
            validation=validation,
        )

        final_snapshot = self._build_final_snapshot(
            project=project,
            research=research,
            analysis=analysis,
            verdict=verdict,
            innovation=innovation,
            solution=solution,
            architecture=architecture,
            development=development,
            experiments=experiments,
            validation=validation,
            evidence_summary=evidence_summary,
        )

        delivery_status = {
            "status": "READY_FOR_GENERATION",

            "content_package_generated": True,

            "documents_generated": False,

            "research_results_verified": False,

            "experimental_results_verified": False,

            "implementation_execution_verified": False,

            "citations_verified": bool(
                citation_package.get(
                    "references"
                )
            ),

            "human_review_required": True,

            "actual_file_generation": {
                "docx": False,
                "pdf": False,
                "pptx": False,
                "zip": False,
            },

            "next_generation_targets": [
                "DOCX project report",
                "PDF project report",
                "Research paper draft",
                "PPTX presentation",
                "SIH/hackathon submission",
                "Viva preparation document",
                "Implementation guide",
                "Evidence/reference appendix",
                "Demo script",
            ],

            "note": (
                "AURA has generated structured delivery-ready "
                "content. Actual documents and verified results "
                "must be produced from the appropriate project "
                "artifacts and executed evidence."
            ),
        }

        project_blueprint = self._build_complete_project_blueprint(
            project=project,
            research=research,
            analysis=analysis,
            verdict=verdict,
            innovation=innovation,
            solution=solution,
            architecture=architecture,
            development=development,
            experiments=experiments,
            validation=validation,
            evidence_summary=evidence_summary,
            claim_evidence_matrix=claim_evidence_matrix,
        )

        return {
            "stage": "DELIVER",
            "status": "completed",

            "project_summary": project_summary,

            "complete_project_blueprint": project_blueprint,

            "project_report": report,

            "research_paper": research_paper,

            "presentation": presentation,

            "sih_hackathon_pitch": sih_pitch,

            "demo_plan": demo_plan,

            "viva_package": viva,

            "implementation_documentation": (
                implementation_documentation
            ),

            "evidence_summary": evidence_summary,

            "claim_evidence_matrix": (
                claim_evidence_matrix
            ),

            "citation_package": citation_package,

            "execution_summary": execution_summary,

            "final_project_snapshot": final_snapshot,

            "delivery_status": delivery_status,

            "output_policy": {
                "fabricate_results": False,
                "fabricate_citations": False,
                "fabricate_sources": False,
                "fabricate_implementation": False,
                "claim_unverified_novelty": False,
                "convert_plans_to_results": False,
                "convert_expected_results_to_observed_results": False,
                "preserve_provenance": True,
                "preserve_source_identifiers": True,
                "mark_ai_generated_recommendations": True,
                "mark_unverified_claims": True,
                "require_human_review": True,
            },

            "traceability": {
                "idea": bool(
                    project.original_idea
                ),
                "research": bool(research),
                "analysis": bool(analysis),
                "verdict": bool(verdict),
                "innovation": bool(innovation),
                "solution": bool(solution),
                "architecture": bool(architecture),
                "development": bool(development),
                "experiments": bool(experiments),
                "validation": bool(validation),
                "claims": len(claims),
                "evidence_records": len(evidence),
                "claim_evidence_links": len(
                    claim_evidence_matrix
                ),
            },
        }

    # ================================================================
    # PROJECT SUMMARY
    # ================================================================

    def _build_project_summary(
        self,
        project: AURAProject,
        verdict: dict[str, Any],
        innovation: dict[str, Any],
        solution: dict[str, Any],
        evidence_summary: dict[str, Any],
    ) -> dict[str, Any]:

        recommendation = (
            verdict.get("recommendation")
            or verdict.get("recommended_action")
            or "INVESTIGATE_FURTHER"
        )

        selected = (
            innovation.get("recommended_direction")
            or innovation.get("recommended_innovation")
            or innovation.get("selected_direction")
            or ""
        )

        solution_concept = (
            solution.get("solution_concept")
            or solution.get("concept")
            or solution.get("solution")
            or ""
        )

        return {
            "project_name": project.project_name,

            "original_idea": project.original_idea,

            "domain": list(project.domain),

            "objectives": list(project.objectives),

            "recommendation": str(
                recommendation
            ),

            "recommended_innovation": (
                self._safe_text(selected)
            ),

            "solution_concept": (
                self._safe_text(solution_concept)
            ),

            "current_stage": project.current_stage,

            "status": project.status,

            "research_evidence": {
                "papers": evidence_summary.get(
                    "research_records",
                    0,
                ),
                "evidence_records": evidence_summary.get(
                    "total_evidence_records",
                    0,
                ),
                "claim_coverage_percent": (
                    evidence_summary.get(
                        "claim_evidence_coverage_percent",
                        0,
                    )
                ),
            },
        }

    # ================================================================
    # COMPLETE PROJECT BLUEPRINT
    # ================================================================

    def _build_complete_project_blueprint(
        self,
        project: AURAProject,
        research: dict[str, Any],
        analysis: dict[str, Any],
        verdict: dict[str, Any],
        innovation: dict[str, Any],
        solution: dict[str, Any],
        architecture: dict[str, Any],
        development: dict[str, Any],
        experiments: dict[str, Any],
        validation: dict[str, Any],
        evidence_summary: dict[str, Any],
        claim_evidence_matrix: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """Aggregate every detailed stage into one build-ready blueprint.

        This is intentionally a structured aggregation, not a replacement for
        the individual stage outputs. It gives the frontend/API one authoritative
        object for exporting or rendering the complete project.
        """
        return {
            "project": {
                "project_id": project.project_id,
                "project_name": project.project_name,
                "original_idea": project.original_idea,
                "domain": list(project.domain),
                "objectives": list(project.objectives),
                "requirements": list(project.requirements),
                "constraints": list(project.constraints),
            },
            "research_package": {
                "literature": research,
                "evidence": evidence_summary,
                "claim_evidence_matrix": claim_evidence_matrix,
            },
            "analysis_package": analysis,
            "decision_package": {
                "verdict": verdict,
                "innovation": innovation,
            },
            "engineering_package": {
                "solution": solution,
                "architecture": architecture,
                "development": development,
            },
            "evaluation_package": {
                "experiments": experiments,
                "validation": validation,
            },
            "delivery_package": {
                "report": "project_report",
                "research_paper": "research_paper",
                "presentation": "presentation",
                "sih_hackathon": "sih_hackathon_pitch",
                "demo": "demo_plan",
                "viva": "viva_package",
                "implementation_documentation": "implementation_documentation",
            },
            "execution_boundary": {
                "research_retrieved": bool(research),
                "solution_designed": bool(solution),
                "architecture_designed": bool(architecture),
                "implementation_planned": bool(development),
                "experiments_designed": bool(experiments),
                "validation_designed": bool(validation),
                "implementation_executed": False,
                "experiments_executed": self._execution_flag(experiments, "experiments_executed"),
                "results_verified": self._execution_flag(validation, "results_verified"),
                "deployment_verified": False,
            },
            "next_actions": [
                "Review the selected solution and architecture.",
                "Generate or implement the repository modules defined by BUILD.",
                "Execute the experiment plan on the specified datasets.",
                "Record observed metrics and result artifacts.",
                "Run validation and reproducibility checks.",
                "Generate final documents from verified artifacts.",
            ],
        }

    @staticmethod
    def _execution_flag(data: dict[str, Any], key: str) -> bool:
        """Read a boolean execution flag from a stage package safely."""
        value = data.get(key) if isinstance(data, dict) else False
        return value is True

    # ================================================================
    # PROJECT REPORT
    # ================================================================

    def _build_project_report(
        self,
        project: AURAProject,
        research: dict[str, Any],
        analysis: dict[str, Any],
        verdict: dict[str, Any],
        innovation: dict[str, Any],
        solution: dict[str, Any],
        architecture: dict[str, Any],
        development: dict[str, Any],
        experiments: dict[str, Any],
        validation: dict[str, Any],
    ) -> dict[str, Any]:

        return {
            "title": project.project_name,

            "document_type": (
                "Complete Research + Engineering Project Report"
            ),

            "sections": [
                {
                    "section": 1,
                    "title": "Abstract",
                    "purpose": (
                        "Problem, proposed solution, methodology "
                        "and verified contribution."
                    ),
                    "source": (
                        "UNDERSTAND + SOLUTION + VALIDATE"
                    ),
                    "status": "READY_FOR_DRAFTING",
                },
                {
                    "section": 2,
                    "title": "Introduction",
                    "purpose": (
                        "Problem context, motivation, stakeholders "
                        "and objectives."
                    ),
                    "source": "UNDERSTAND",
                    "status": "READY",
                },
                {
                    "section": 3,
                    "title": "Problem Definition",
                    "purpose": (
                        "Formal research and engineering problem."
                    ),
                    "source": "UNDERSTAND",
                    "status": "READY",
                },
                {
                    "section": 4,
                    "title": "Existing Work",
                    "purpose": (
                        "Relevant research, technologies, projects "
                        "and existing approaches."
                    ),
                    "source": "INVESTIGATE + ANALYZE",
                    "status": (
                        "READY"
                        if research or analysis
                        else "PENDING"
                    ),
                },
                {
                    "section": 5,
                    "title": "Research Analysis",
                    "purpose": (
                        "Themes, methods, technologies, limitations, "
                        "challenges and opportunities."
                    ),
                    "source": "ANALYZE",
                    "status": (
                        "READY"
                        if analysis
                        else "PENDING"
                    ),
                },
                {
                    "section": 6,
                    "title": "Research Gap",
                    "purpose": (
                        "Evidence-supported limitations and "
                        "opportunity areas."
                    ),
                    "source": "VERDICT",
                    "status": (
                        "READY"
                        if verdict
                        else "PENDING"
                    ),
                },
                {
                    "section": 7,
                    "title": "Proposed Innovation",
                    "purpose": (
                        "Selected research-backed innovation."
                    ),
                    "source": "INNOVATE",
                    "status": (
                        "READY"
                        if innovation
                        else "PENDING"
                    ),
                },
                {
                    "section": 8,
                    "title": "Proposed Solution",
                    "purpose": (
                        "Complete proposed solution."
                    ),
                    "source": "SOLUTION",
                    "status": (
                        "READY"
                        if solution
                        else "PENDING"
                    ),
                },
                {
                    "section": 9,
                    "title": "System Architecture",
                    "purpose": (
                        "Components, interfaces, data flow "
                        "and AI architecture."
                    ),
                    "source": "ARCHITECT",
                    "status": (
                        "READY"
                        if architecture
                        else "PENDING"
                    ),
                },
                {
                    "section": 10,
                    "title": "Implementation",
                    "purpose": (
                        "Development modules, technology stack "
                        "and implementation workflow."
                    ),
                    "source": "BUILD",
                    "status": (
                        "READY"
                        if development
                        else "PENDING"
                    ),
                },
                {
                    "section": 11,
                    "title": "Experimental Methodology",
                    "purpose": (
                        "Dataset, baseline, experiments, metrics "
                        "and evaluation protocol."
                    ),
                    "source": "EXPERIMENT",
                    "status": (
                        "READY"
                        if experiments
                        else "PENDING"
                    ),
                },
                {
                    "section": 12,
                    "title": "Validation Framework",
                    "purpose": (
                        "Technical, functional, robustness, "
                        "reproducibility and acceptance validation."
                    ),
                    "source": "VALIDATE",
                    "status": (
                        "READY"
                        if validation
                        else "PENDING"
                    ),
                },
                {
                    "section": 13,
                    "title": "Results",
                    "purpose": (
                        "Only actual executed and verified results."
                    ),
                    "status": "REQUIRES_EXECUTED_RESULTS",
                },
                {
                    "section": 14,
                    "title": "Discussion",
                    "purpose": (
                        "Interpret verified results against "
                        "existing research."
                    ),
                    "status": "REQUIRES_EXECUTED_RESULTS",
                },
                {
                    "section": 15,
                    "title": "Limitations",
                    "purpose": (
                        "Evidence limitations, technical limitations "
                        "and validation limitations."
                    ),
                    "source": (
                        "ANALYZE + VALIDATE"
                    ),
                    "status": "READY_FOR_DRAFTING",
                },
                {
                    "section": 16,
                    "title": "Conclusion",
                    "purpose": (
                        "Evidence-bounded final conclusions."
                    ),
                    "status": "READY_FOR_DRAFTING",
                },
                {
                    "section": 17,
                    "title": "References",
                    "purpose": (
                        "References generated from AURA provenance."
                    ),
                    "status": (
                        "READY"
                        if research
                        else "PENDING"
                    ),
                },
            ],

            "content_sources": {
                "research_records": len(
                    self._extract_papers(project)
                ),
                "research_analysis": bool(
                    analysis
                ),
                "verdict": bool(verdict),
                "innovation": bool(innovation),
                "solution": bool(solution),
                "architecture": bool(architecture),
                "development": bool(development),
                "experiments": bool(experiments),
                "validation": bool(validation),
            },

            "result_integrity": {
                "results_available": False,
                "verified_results_available": False,
                "rule": (
                    "Results sections remain placeholders until "
                    "actual experiment outputs are supplied."
                ),
            },
        }

    # ================================================================
    # RESEARCH PAPER
    # ================================================================

    def _build_research_paper(
        self,
        project: AURAProject,
        research: dict[str, Any],
        analysis: dict[str, Any],
        verdict: dict[str, Any],
        innovation: dict[str, Any],
        solution: dict[str, Any],
        experiments: dict[str, Any],
        validation: dict[str, Any],
        claims: list[dict[str, Any]],
    ) -> dict[str, Any]:

        return {
            "title": project.project_name,

            "paper_type": (
                "Research / Applied AI & Engineering"
            ),

            "sections": [
                "Title",
                "Abstract",
                "Keywords",
                "Introduction",
                "Related Work",
                "Research Gap",
                "Research Questions",
                "Proposed Method",
                "System Architecture",
                "Implementation",
                "Experimental Setup",
                "Baseline",
                "Evaluation Metrics",
                "Results",
                "Discussion",
                "Limitations",
                "Conclusion",
                "References",
            ],

            "research_question_source": (
                "UNDERSTAND"
            ),

            "related_work_source": (
                "INVESTIGATE + ANALYZE"
            ),

            "gap_source": (
                "VERDICT"
            ),

            "method_source": (
                "INNOVATE + SOLUTION + ARCHITECT"
            ),

            "validation_source": (
                "EXPERIMENT + VALIDATE"
            ),

            "claim_count": len(claims),

            "results_policy": {
                "status": (
                    "NOT_AVAILABLE_UNLESS_EXECUTED"
                ),
                "rule": (
                    "No numerical experimental results may be "
                    "invented by the delivery engine."
                ),
            },

            "citation_policy": {
                "use_source_metadata": True,
                "preserve_doi": True,
                "preserve_source_url": True,
                "preserve_provider": True,
                "avoid_fabricated_references": True,
                "verify_reference_details": True,
            },

            "available_evidence": {
                "papers": len(
                    self._extract_papers(project)
                ),
                "analysis_available": bool(
                    analysis
                ),
                "verdict_available": bool(
                    verdict
                ),
                "innovation_available": bool(
                    innovation
                ),
                "solution_available": bool(
                    solution
                ),
                "experiments_available": bool(
                    experiments
                ),
                "validation_available": bool(
                    validation
                ),
            },
        }

    # ================================================================
    # PRESENTATION
    # ================================================================

    def _build_presentation(
        self,
        project: AURAProject,
        summary: dict[str, Any],
        verdict: dict[str, Any],
        innovation: dict[str, Any],
        solution: dict[str, Any],
        architecture: dict[str, Any],
        development: dict[str, Any],
        experiments: dict[str, Any],
        validation: dict[str, Any],
    ) -> dict[str, Any]:

        slides = [
            ("Project Title", "Project identity"),
            ("Problem", "Why the problem matters"),
            ("Target Users", "Who experiences the problem"),
            ("Existing Solutions", "Current approaches"),
            ("Research Evidence", "Evidence from literature"),
            ("Research Gap", "Identified opportunity"),
            ("AURA Verdict", "Evidence-aware decision"),
            ("Innovation", "Proposed differentiation"),
            ("Solution", "How the system works"),
            ("Architecture", "System architecture"),
            ("Technology Stack", "Hardware/software/AI/data"),
            ("Development", "Implementation roadmap"),
            ("Experiments", "Evaluation methodology"),
            ("Validation", "Verification framework"),
            ("Results", "Verified results only"),
            ("Impact", "Expected/practical contribution"),
            ("Demo", "Live demonstration"),
            ("Future Work", "Future research"),
            ("Conclusion", "Final message"),
        ]

        formatted_slides = []

        for index, item in enumerate(
            slides,
            start=1,
        ):
            formatted_slides.append(
                {
                    "slide": index,
                    "title": item[0],
                    "purpose": item[1],
                }
            )

        return {
            "presentation_title": project.project_name,

            "recommended_slide_count": len(
                formatted_slides
            ),

            "slides": formatted_slides,

            "design_direction": (
                "Clean cinematic research presentation with "
                "evidence cards, architecture visuals, "
                "experiment dashboards and source traceability."
            ),

            "result_policy": (
                "The Results slide must contain only executed "
                "and verified results."
            ),

            "content_status": {
                "summary": bool(summary),
                "verdict": bool(verdict),
                "innovation": bool(innovation),
                "solution": bool(solution),
                "architecture": bool(architecture),
                "development": bool(development),
                "experiments": bool(experiments),
                "validation": bool(validation),
            },
        }

    # ================================================================
    # SIH / HACKATHON
    # ================================================================

    def _build_sih_pitch(
        self,
        project: AURAProject,
        verdict: dict[str, Any],
        innovation: dict[str, Any],
        solution: dict[str, Any],
        validation: dict[str, Any],
        evidence_summary: dict[str, Any],
    ) -> dict[str, Any]:

        recommendation = (
            verdict.get("recommendation")
            or verdict.get("recommended_action")
            or "INVESTIGATE_FURTHER"
        )

        return {
            "title": project.project_name,

            "pitch_structure": [
                "Problem",
                "Who is affected",
                "Current solution limitations",
                "Research evidence",
                "Research gap",
                "Our innovation",
                "Solution",
                "Technology",
                "Implementation",
                "Validation",
                "Expected impact",
                "Scalability",
                "Future roadmap",
            ],

            "one_line_pitch": (
                f"{project.project_name} addresses a defined "
                "problem using an evidence-informed technology solution."
            ),

            "recommendation": recommendation,

            "evidence_context": {
                "research_records": evidence_summary.get(
                    "research_records",
                    0,
                ),
                "claim_coverage_percent": evidence_summary.get(
                    "claim_evidence_coverage_percent",
                    0,
                ),
            },

            "innovation_available": bool(
                innovation
            ),

            "solution_available": bool(
                solution
            ),

            "validation_status": (
                validation.get(
                    "validation_verdict",
                    {},
                )
                if validation
                else {}
            ),

            "claim_policy": (
                "Do not claim guaranteed impact, global novelty "
                "or proven superiority without verification."
            ),
        }

    # ================================================================
    # DEMO PLAN
    # ================================================================

    def _build_demo_plan(
        self,
        project: AURAProject,
        solution: dict[str, Any],
        architecture: dict[str, Any],
        development: dict[str, Any],
        validation: dict[str, Any],
    ) -> dict[str, Any]:

        return {
            "demo_title": (
                f"{project.project_name} — Live Demonstration"
            ),

            "flow": [
                {
                    "step": 1,
                    "title": "Input",
                    "action": (
                        "Provide representative real or controlled input."
                    ),
                },
                {
                    "step": 2,
                    "title": "Processing",
                    "action": (
                        "Show the data-processing pipeline."
                    ),
                },
                {
                    "step": 3,
                    "title": "AI / Intelligence",
                    "action": (
                        "Show model or intelligence processing."
                    ),
                },
                {
                    "step": 4,
                    "title": "Decision",
                    "action": (
                        "Display system prediction or decision."
                    ),
                },
                {
                    "step": 5,
                    "title": "Action",
                    "action": (
                        "Demonstrate the system response."
                    ),
                },
                {
                    "step": 6,
                    "title": "Monitoring",
                    "action": (
                        "Show logs, metrics or dashboard."
                    ),
                },
                {
                    "step": 7,
                    "title": "Validation",
                    "action": (
                        "Show measurable verification evidence."
                    ),
                },
            ],

            "demo_requirements": [
                "Working prototype",
                "Representative test data",
                "Stable environment",
                "Fallback demo dataset",
                "Monitoring/logging",
                "Pre-recorded backup demonstration",
            ],

            "solution_available": bool(
                solution
            ),

            "architecture_available": bool(
                architecture
            ),

            "development_available": bool(
                development
            ),

            "validation_available": bool(
                validation
            ),

            "result_integrity": (
                "A demo is not proof of scientific superiority. "
                "Quantitative claims require formal evaluation."
            ),
        }

    # ================================================================
    # VIVA
    # ================================================================

    def _build_viva_package(
        self,
        project: AURAProject,
        analysis: dict[str, Any],
        verdict: dict[str, Any],
        innovation: dict[str, Any],
        solution: dict[str, Any],
        validation: dict[str, Any],
        evidence_summary: dict[str, Any],
    ) -> dict[str, Any]:

        questions = [
            (
                "What problem does your project solve?",
                "UNDERSTAND",
            ),
            (
                "Why is this problem important?",
                "UNDERSTAND + RESEARCH",
            ),
            (
                "What existing solutions already exist?",
                "INVESTIGATE",
            ),
            (
                "What did AURA discover from the literature?",
                "ANALYZE",
            ),
            (
                "What is the research gap?",
                "VERDICT",
            ),
            (
                "What is different about your approach?",
                "INNOVATE",
            ),
            (
                "Why did you select this solution?",
                "SOLUTION",
            ),
            (
                "Why did you select this architecture?",
                "ARCHITECT",
            ),
            (
                "How does the system work?",
                "BUILD",
            ),
            (
                "How will you evaluate it?",
                "EXPERIMENT",
            ),
            (
                "What is your baseline?",
                "EXPERIMENT",
            ),
            (
                "How will you prove that it works?",
                "VALIDATE",
            ),
            (
                "What evidence supports your research claims?",
                "EVIDENCE",
            ),
            (
                "What are the limitations?",
                "ANALYZE + VALIDATE",
            ),
            (
                "What would you improve in future work?",
                "VALIDATE + DELIVER",
            ),
        ]

        formatted_questions = []

        for index, item in enumerate(
            questions,
            start=1,
        ):
            formatted_questions.append(
                {
                    "question_id": f"VIVA-{index:02d}",
                    "question": item[0],
                    "source_stage": item[1],
                }
            )

        return {
            "question_count": len(
                formatted_questions
            ),

            "questions": formatted_questions,

            "answer_policy": (
                "Answers should be generated from project evidence "
                "and clearly distinguish verified findings from "
                "planned or recommended work."
            ),

            "evidence_context": {
                "research_records": evidence_summary.get(
                    "research_records",
                    0,
                ),
                "claim_coverage_percent": evidence_summary.get(
                    "claim_evidence_coverage_percent",
                    0,
                ),
            },

            "context_available": {
                "analysis": bool(analysis),
                "verdict": bool(verdict),
                "innovation": bool(innovation),
                "solution": bool(solution),
                "validation": bool(validation),
            },
        }

    # ================================================================
    # IMPLEMENTATION DOCUMENTATION
    # ================================================================

    def _build_implementation_documentation(
        self,
        project: AURAProject,
        architecture: dict[str, Any],
        development: dict[str, Any],
        experiments: dict[str, Any],
        validation: dict[str, Any],
    ) -> dict[str, Any]:

        return {
            "title": (
                f"{project.project_name} — Implementation Guide"
            ),

            "sections": [
                "System Overview",
                "Prerequisites",
                "Technology Stack",
                "Repository Structure",
                "Environment Setup",
                "Configuration",
                "Database Setup",
                "Data Pipeline",
                "AI/ML Pipeline",
                "Backend Implementation",
                "Frontend Implementation",
                "Hardware Integration",
                "API Integration",
                "Testing",
                "Experiment Execution",
                "Validation",
                "Deployment",
                "Monitoring",
                "Troubleshooting",
            ],

            "source_availability": {
                "architecture": bool(
                    architecture
                ),
                "development": bool(
                    development
                ),
                "experiments": bool(
                    experiments
                ),
                "validation": bool(
                    validation
                ),
            },

            "execution_warning": (
                "This documentation describes the defined or "
                "planned implementation. It does not prove that "
                "every component has already been implemented."
            ),
        }

    # ================================================================
    # EVIDENCE SUMMARY
    # ================================================================

    def _build_evidence_summary(
        self,
        project: AURAProject,
        research: dict[str, Any],
        analysis: dict[str, Any],
        validation: dict[str, Any],
        evidence: list[dict[str, Any]],
    ) -> dict[str, Any]:

        verified = 0
        synthesis = 0
        recommendations = 0
        pending = 0

        for item in evidence:

            status = str(
                item.get(
                    "status",
                    item.get(
                        "verification_status",
                        "",
                    ),
                )
            ).upper()

            if (
                "VERIFIED" in status
                or status == "PASS"
            ):
                verified += 1

            elif (
                "SYNTHESIS" in status
                or "AI_SYNTHESIS" in status
            ):
                synthesis += 1

            elif "RECOMMENDATION" in status:
                recommendations += 1

            elif (
                "PENDING" in status
                or "REQUIRES" in status
                or "NOT_VERIFIED" in status
            ):
                pending += 1

        papers = self._extract_papers(project)

        claims = self._extract_claims(
            research,
            analysis,
        )

        claims_with_evidence = sum(
            1
            for claim in claims
            if self._extract_evidence_ids(
                claim
            )
        )

        claim_coverage = (
            round(
                claims_with_evidence
                / len(claims)
                * 100,
                1,
            )
            if claims
            else 0.0
        )

        references = []

        for paper in papers:

            references.append(
                {
                    "title": paper.get(
                        "title"
                    ),
                    "authors": paper.get(
                        "authors"
                    ),
                    "year": (
                        paper.get("year")
                        or paper.get("publication_year")
                    ),
                    "doi": paper.get(
                        "doi"
                    ),
                    "url": (
                        paper.get("url")
                        or paper.get(
                            "landing_page_url"
                        )
                    ),
                    "source": (
                        paper.get("source")
                        or paper.get(
                            "provider"
                        )
                    ),
                    "paper_id": (
                        paper.get("paper_id")
                        or paper.get(
                            "work_id"
                        )
                        or paper.get(
                            "openalex_id"
                        )
                    ),
                }
            )

        return {
            "total_evidence_records": len(
                evidence
            ),

            "verified_records": verified,

            "ai_synthesis_records": synthesis,

            "recommendation_records": recommendations,

            "pending_records": pending,

            "research_records": len(
                papers
            ),

            "claims_total": len(
                claims
            ),

            "claims_with_evidence": (
                claims_with_evidence
            ),

            "claims_without_evidence": max(
                0,
                len(claims)
                - claims_with_evidence,
            ),

            "claim_evidence_coverage_percent": (
                claim_coverage
            ),

            "references": references,

            "validation_context": {
                "available": bool(
                    validation
                ),
                "results_verified": (
                    validation
                    .get(
                        "execution_status",
                        {},
                    )
                    .get(
                        "results_verified",
                        False,
                    )
                    if validation
                    else False
                ),
            },

            "provenance_rule": (
                "Every major factual claim should be traceable "
                "to supporting evidence or explicitly marked as "
                "AI synthesis or AURA recommendation."
            ),
        }

    # ================================================================
    # CLAIM → EVIDENCE MATRIX
    # ================================================================

    def _build_claim_evidence_matrix(
        self,
        project: AURAProject,
        claims: list[dict[str, Any]],
        analysis: dict[str, Any],
        research: dict[str, Any],
    ) -> list[dict[str, Any]]:

        evidence_records = [
            item
            for item in project.evidence
            if isinstance(item, dict)
        ]

        available_ids = set()

        for item in evidence_records:

            for key in [
                "evidence_id",
                "id",
                "paper_id",
                "source_id",
            ]:

                value = item.get(key)

                if value:
                    available_ids.add(
                        str(value)
                    )

        paper_ids = set()

        for paper in self._extract_papers(
            project
        ):

            for key in [
                "evidence_id",
                "paper_id",
                "id",
                "work_id",
                "openalex_id",
                "doi",
            ]:

                value = paper.get(key)

                if value:
                    paper_ids.add(
                        str(value)
                    )

        matrix = []

        for index, claim in enumerate(
            claims,
            start=1,
        ):

            claim_id = (
                claim.get("claim_id")
                or claim.get("id")
                or f"CLAIM-{index:03d}"
            )

            evidence_ids = (
                self._extract_evidence_ids(
                    claim
                )
            )

            resolved_ids = []

            for evidence_id in evidence_ids:

                evidence_id = str(
                    evidence_id
                )

                if (
                    evidence_id
                    not in resolved_ids
                ):
                    resolved_ids.append(
                        evidence_id
                    )

            verified_links = [
                evidence_id
                for evidence_id in resolved_ids
                if (
                    evidence_id
                    in available_ids
                    or evidence_id
                    in paper_ids
                )
            ]

            matrix.append(
                {
                    "claim_id": str(
                        claim_id
                    ),

                    "claim": self._safe_text(
                        claim.get(
                            "claim"
                        )
                        or claim.get(
                            "statement"
                        )
                    ),

                    "evidence_ids": (
                        resolved_ids
                    ),

                    "resolved_evidence_ids": (
                        verified_links
                    ),

                    "evidence_status": (
                        "SUPPORTED"
                        if resolved_ids
                        else "UNSUPPORTED"
                    ),

                    "delivery_status": (
                        "TRACEABLE"
                        if verified_links
                        else (
                            "MAPPED_BUT_UNRESOLVED"
                            if resolved_ids
                            else "NEEDS_EVIDENCE"
                        )
                    ),

                    "citation_required": True,

                    "verification_warning": (
                        None
                        if verified_links
                        else (
                            "Claim should not be presented "
                            "as strongly verified until "
                            "supporting evidence is resolved."
                        )
                    ),
                }
            )

        return matrix

    # ================================================================
    # CITATION PACKAGE
    # ================================================================

    def _build_citation_package(
        self,
        project: AURAProject,
        research: dict[str, Any],
    ) -> dict[str, Any]:

        references = []

        for index, paper in enumerate(
            self._extract_papers(project),
            start=1,
        ):

            title = self._safe_text(
                paper.get("title")
            )

            if not title:
                continue

            references.append(
                {
                    "reference_id": (
                        f"REF-{index:03d}"
                    ),

                    "title": title,

                    "authors": paper.get(
                        "authors"
                    ),

                    "year": paper.get(
                        "year"
                    ),

                    "journal": (
                        paper.get("journal")
                        or paper.get(
                            "venue"
                        )
                    ),

                    "doi": paper.get(
                        "doi"
                    ),

                    "url": (
                        paper.get("url")
                        or paper.get(
                            "landing_page_url"
                        )
                    ),

                    "source": (
                        paper.get("source")
                        or paper.get(
                            "provider"
                        )
                    ),

                    "identifier": (
                        paper.get("paper_id")
                        or paper.get(
                            "work_id"
                        )
                        or paper.get(
                            "openalex_id"
                        )
                    ),

                    "citation_status": (
                        "METADATA_AVAILABLE"
                    ),
                }
            )

        return {
            "reference_count": len(
                references
            ),

            "references": references,

            "citation_policy": {
                "fabricate_citations": False,
                "preserve_doi": True,
                "preserve_source": True,
                "preserve_url": True,
                "verify_metadata": True,
                "full_text_verified_by_default": False,
            },

            "important_note": (
                "Metadata availability does not mean that "
                "the full paper has been independently verified."
            ),
        }

    # ================================================================
    # EXECUTION SUMMARY
    # ================================================================

    def _build_execution_summary(
        self,
        project: AURAProject,
        experiments: dict[str, Any],
        validation: dict[str, Any],
    ) -> dict[str, Any]:

        experiment_list = self._extract_list(
            experiments,
            [
                "experiments",
                "experiment_plan",
                "planned_experiments",
            ],
        )

        validation_status = self._as_dict(
            validation.get(
                "execution_status",
                {},
            )
        )

        return {
            "experiment_count": len(
                experiment_list
            ),

            "experiments_executed": bool(
                validation_status.get(
                    "experiments_executed",
                    False,
                )
            ),

            "results_available": bool(
                validation_status.get(
                    "results_available",
                    False,
                )
            ),

            "results_verified": bool(
                validation_status.get(
                    "results_verified",
                    False,
                )
            ),

            "implementation_verified": False,

            "deployment_verified": False,

            "execution_state": (
                "PLANNED"
                if not validation_status.get(
                    "results_verified",
                    False,
                )
                else "VERIFIED"
            ),

            "rule": (
                "AURA cannot convert an experiment design "
                "into an observed result."
            ),
        }

    # ================================================================
    # FINAL SNAPSHOT
    # ================================================================

    def _build_final_snapshot(
        self,
        project: AURAProject,
        research: dict[str, Any],
        analysis: dict[str, Any],
        verdict: dict[str, Any],
        innovation: dict[str, Any],
        solution: dict[str, Any],
        architecture: dict[str, Any],
        development: dict[str, Any],
        experiments: dict[str, Any],
        validation: dict[str, Any],
        evidence_summary: dict[str, Any],
    ) -> dict[str, Any]:

        validation_verdict = (
            validation.get(
                "validation_verdict",
                {},
            )
            if validation
            else {}
        )

        stages = [
            (
                "UNDERSTAND",
                bool(project.analysis),
            ),
            (
                "INVESTIGATE",
                bool(research),
            ),
            (
                "ANALYZE",
                bool(analysis),
            ),
            (
                "VERDICT",
                bool(verdict),
            ),
            (
                "INNOVATE",
                bool(innovation),
            ),
            (
                "SOLUTION",
                bool(solution),
            ),
            (
                "ARCHITECT",
                bool(architecture),
            ),
            (
                "BUILD",
                bool(development),
            ),
            (
                "EXPERIMENT",
                bool(experiments),
            ),
            (
                "VALIDATE",
                bool(validation),
            ),
            (
                "DELIVER",
                True,
            ),
        ]

        pipeline = []

        for name, available in stages:
            pipeline.append(
                {
                    "stage": name,
                    "status": (
                        "completed"
                        if available
                        else "pending"
                    ),
                    "available": available,
                }
            )

        return {
            "project_name": project.project_name,

            "original_idea": project.original_idea,

            "pipeline": pipeline,

            "validation_readiness": (
                validation_verdict
            ),

            "evidence": {
                "research_records": (
                    evidence_summary.get(
                        "research_records",
                        0,
                    )
                ),
                "evidence_records": (
                    evidence_summary.get(
                        "total_evidence_records",
                        0,
                    )
                ),
                "claim_evidence_coverage": (
                    evidence_summary.get(
                        "claim_evidence_coverage_percent",
                        0,
                    )
                ),
            },

            "project_memory_records": len(
                project.memory
            ),

            "final_state": {
                "research_completed": bool(
                    research
                ),
                "research_analysis_completed": bool(
                    analysis
                ),
                "verdict_generated": bool(
                    verdict
                ),
                "innovation_defined": bool(
                    innovation
                ),
                "solution_defined": bool(
                    solution
                ),
                "architecture_defined": bool(
                    architecture
                ),
                "development_plan_defined": bool(
                    development
                ),
                "experiments_defined": bool(
                    experiments
                ),
                "validation_framework_defined": bool(
                    validation
                ),
                "delivery_package_defined": True,
                "actual_results_verified": False,
                "human_review_required": True,
            },

            "aura_statement": (
                "AURA has transformed the original idea into "
                "a connected research, innovation, engineering, "
                "experimentation, validation and delivery workflow. "
                "Final claims and experimental results remain "
                "evidence-bounded and require verification."
            ),
        }

    # ================================================================
    # MEMORY
    # ================================================================

    def _store_memory(
        self,
        project: AURAProject,
        deliverables: dict[str, Any],
    ) -> None:

        snapshot = self._as_dict(
            deliverables.get(
                "final_project_snapshot",
                {},
            )
        )

        final_state = self._as_dict(
            snapshot.get(
                "final_state",
                {},
            )
        )

        project.memory.append(
            {
                "stage": "DELIVER",

                "type": "delivery_package",

                "status": "completed",

                "event": (
                    "AURA generated final delivery package."
                ),

                "evidence_records": len(
                    project.evidence
                ),

                "memory_records": len(
                    project.memory
                ),

                "actual_results_verified": (
                    final_state.get(
                        "actual_results_verified",
                        False,
                    )
                ),

                "human_review_required": True,
            }
        )

    # ================================================================
    # EVIDENCE
    # ================================================================

    def _store_evidence(
        self,
        project: AURAProject,
        deliverables: dict[str, Any],
    ) -> None:

        evidence_summary = self._as_dict(
            deliverables.get(
                "evidence_summary",
                {},
            )
        )

        project.evidence.append(
            {
                "stage": "DELIVER",

                "type": "delivery_package",

                "status": "AURA_RECOMMENDATION",

                "claim": (
                    "AURA generated a structured delivery package "
                    "covering project documentation, research paper, "
                    "presentation, hackathon pitch, demonstration, "
                    "viva, implementation documentation and "
                    "evidence traceability."
                ),

                "support": {
                    "research_records": (
                        evidence_summary.get(
                            "research_records",
                            0,
                        )
                    ),
                    "evidence_records": (
                        evidence_summary.get(
                            "total_evidence_records",
                            0,
                        )
                    ),
                    "claim_coverage": (
                        evidence_summary.get(
                            "claim_evidence_coverage_percent",
                            0,
                        )
                    ),
                },

                "verification_required": True,

                "execution_status": "NOT_EXECUTED",

                "note": (
                    "The delivery package describes available "
                    "project information and planned outputs. "
                    "It is not evidence of experimental success."
                ),
            }
        )

    # ================================================================
    # CLAIM EXTRACTION
    # ================================================================

    def _extract_claims(
        self,
        research: dict[str, Any],
        analysis: dict[str, Any],
    ) -> list[dict[str, Any]]:

        claim_analysis = self._as_dict(
            analysis.get(
                "claim_analysis",
                {},
            )
        )

        claims = claim_analysis.get(
            "claims",
            [],
        )

        if isinstance(claims, list):
            return [
                claim
                for claim in claims
                if isinstance(claim, dict)
            ]

        research_claims = research.get(
            "claims",
            [],
        )

        if isinstance(research_claims, list):
            return [
                claim
                for claim in research_claims
                if isinstance(claim, dict)
            ]

        return []

    # ================================================================
    # EVIDENCE IDS
    # ================================================================

    def _extract_evidence_ids(
        self,
        claim: dict[str, Any],
    ) -> list[str]:

        values: list[Any] = []

        for key in [
            "evidence_ids",
            "supporting_evidence",
            "supporting_evidence_ids",
            "source_ids",
        ]:

            value = claim.get(key)

            if isinstance(value, list):
                values.extend(value)

        ids = []

        for value in values:

            if isinstance(value, dict):

                identifier = (
                    value.get(
                        "evidence_id"
                    )
                    or value.get(
                        "id"
                    )
                    or value.get(
                        "paper_id"
                    )
                    or value.get(
                        "source_id"
                    )
                )

            else:
                identifier = value

            if identifier is None:
                continue

            identifier = str(
                identifier
            )

            if (
                identifier
                and identifier not in ids
            ):
                ids.append(
                    identifier
                )

        return ids

    # ================================================================
    # PAPERS
    # ================================================================

    def _extract_papers(
        self,
        project: AURAProject,
    ) -> list[dict[str, Any]]:

        research = self._as_dict(
            project.research
        )

        papers = research.get(
            "papers",
            [],
        )

        if isinstance(papers, list):
            return [
                paper
                for paper in papers
                if isinstance(paper, dict)
            ]

        return []

    # ================================================================
    # LIST
    # ================================================================

    def _extract_list(
        self,
        data: dict[str, Any],
        keys: list[str],
    ) -> list[Any]:

        for key in keys:

            value = data.get(
                key
            )

            if isinstance(value, list):
                return value

        return []

    # ================================================================
    # DICT
    # ================================================================

    def _as_dict(
        self,
        value: Any,
    ) -> dict[str, Any]:

        if hasattr(
            value,
            "model_dump",
        ):

            result = value.model_dump()

            if isinstance(
                result,
                dict,
            ):
                return result

            return {}

        if isinstance(
            value,
            dict,
        ):
            return value

        return {}

    # ================================================================
    # TEXT
    # ================================================================

    def _safe_text(
        self,
        value: Any,
    ) -> str:

        if value is None:
            return ""

        if isinstance(
            value,
            str,
        ):
            return value.strip()

        return str(value).strip()


delivery_agent = DeliveryAgent()