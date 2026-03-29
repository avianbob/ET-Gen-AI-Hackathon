"""
Master Agent - Conversation Orchestrator for ET Techathon.

Interprets user queries, classifies intent, extracts entities,
routes to appropriate worker agents, and synthesizes responses.
"""

import json
import time
import uuid
from typing import Dict, Any, List, Optional, Tuple
from app.services.repurpose.llm.llm_factory import LLMFactory
from app.services.repurpose.utils.logger import get_logger

logger = get_logger("agents.master")

# Intent types the Master Agent can detect
INTENTS = [
    "drug_analysis",       # Full drug repurposing analysis (triggers 15-agent pipeline)
    "report_generation",   # Generate a PDF report for a drug (pipeline + report agent)
    "market_query",        # Market size, CAGR, competitor data (IQVIA-style)
    "patent_lookup",       # Patent landscape, expiry, FTO
    "exim_data",           # Import-export trade data
    "clinical_trials",     # Clinical trial pipeline queries
    "web_search",          # Guidelines, news, RWE
    "file_summary",        # Summarize uploaded documents
    "comparison",          # Compare drugs, indications, or markets
    "general_question",    # General pharma knowledge
    "clarification_needed" # Ambiguous query needing clarification
]

# ET agent name mapping (internal → display)
ET_AGENT_NAMES = {
    "market": "IQVIA Insights Agent",
    "exim": "EXIM Trade Agent",
    "patent": "Patent Landscape Agent",
    "clinical_trials": "Clinical Trials Agent",
    "internal": "Internal Knowledge Agent",
    "web": "Web Intelligence Agent",
    "report": "Report Generator Agent",
    "pipeline": "Multi-Agent Pipeline",
}

INTENT_CLASSIFICATION_PROMPT = """You are the Master Agent (Conversation Orchestrator) for a pharmaceutical drug repurposing platform.

Your job is to interpret user queries and classify them so the system can route to the right worker agents.

Given the user's message and conversation history, output a JSON object with:
1. "intent": one of {intents}
2. "entities": extracted entities as object with optional keys:
   - "drug_names": list of drug names mentioned
   - "indications": list of diseases/indications mentioned
   - "regions": list of countries/regions mentioned
   - "time_period": time range if mentioned
   - "competitors": competitor drugs mentioned
3. "agents_needed": list of agent keys to invoke: {agent_keys}
4. "clarification_questions": list of questions if the query is ambiguous (empty list if clear)
5. "reasoning": brief explanation of why you classified this way

Rules:
- If user says "analyze [drug]" or "search [drug]" or "find repurposing opportunities for [drug]", intent is "drug_analysis"
- If user asks to "generate a report", "create a report", "make a report", "export report", or "full report for [drug]", intent is "report_generation"
- If user asks about market size, growth, CAGR, competition, or IQVIA-style data, intent is "market_query"
- If user asks about patents, IP, FTO, exclusivity, or biosimilar opportunity, intent is "patent_lookup"
- If user asks about import/export, EXIM, trade data, API sourcing, intent is "exim_data"
- If user asks about clinical trials, pipeline, ongoing studies, intent is "clinical_trials"
- If user asks about guidelines, news, publications, real-world evidence, intent is "web_search"
- If user asks to summarize a document or references uploaded files, intent is "file_summary"
- If user asks to compare drugs, markets, or indications, intent is "comparison"
- If query is too vague (e.g. "show me data" without specifying what), intent is "clarification_needed"
- For "comparison" intent, include all relevant agent keys

IMPORTANT — Clarification rules (set intent to "clarification_needed" and fill clarification_questions):
- If user asks a broad question without specifying a drug, region, or therapeutic area (e.g. "show me data", "what are the trends", "any opportunities?"), ask them to narrow down.
- If user asks about "unmet needs" or "competition" without specifying a therapeutic area, ask: "Which therapeutic area are you interested in? (e.g., oncology, cardiovascular, respiratory, diabetes)"
- If user mentions a disease but it's ambiguous whether they want market data, trials, or patents, ask: "Would you like market data, clinical trial pipeline, or patent landscape for [disease]?"
- If user asks about a region without specifying the data type, ask: "Do you want EXIM trade data, market size, or clinical trial activity for [region]?"
- If user says "also check..." or references a previous result but no conversation history exists, ask them to re-state what they want checked.
- Generate 2-3 specific, actionable clarification questions that would help narrow the query. Frame them as suggestions the user can click on.

Multi-turn context rules:
- If the user says "also check...", "what about...", "and the...", "show me ... too", "now check...", or any referential phrase, look at the conversation history to determine which drug/indication they are referring to.
- Carry forward drug names and indications from the conversation history if the current message doesn't mention them explicitly.
- If the user switches to a new drug or topic, use the new entities. Only carry forward when the current message lacks specifics.
- For "also check biosimilar competition" after discussing Metformin, set drug_names to ["Metformin"] and intent to "patent_lookup".

Conversation history:
{history}

User message: {message}

Respond with ONLY a valid JSON object, no markdown, no explanation outside the JSON."""

SYNTHESIS_PROMPT = """You are a senior pharmaceutical strategist. Synthesize the following data from multiple agents into a clear, actionable response for the user.

User's question: {question}

Data from agents:
{agent_data}

Instructions:
- Provide a clear, structured answer to the user's question
- Use specific numbers, names, and data points from the agent results
- If there are tables of data, describe the key takeaways
- Suggest 2-3 follow-up questions the user might want to ask
- Keep the response concise but data-rich (3-5 paragraphs max)
- If data is insufficient, say so and suggest what additional queries might help
- Write in a professional tone suitable for pharma business development

Respond in plain text (markdown formatting is OK). At the end, add a section "## Suggested Follow-ups" with 2-3 bullet points."""


class MasterAgent:
    """
    Conversation orchestrator that interprets user queries,
    routes to worker agents, and synthesizes responses.
    """

    # Class-level pipeline results cache: {conversation_id: {"data": {...}, "drug_name": str, "timestamp": float}}
    _pipeline_cache: Dict[str, Dict[str, Any]] = {}
    _CACHE_TTL_SECONDS = 1800  # 30 minutes
    _CACHE_MAX_ENTRIES = 20

    def __init__(self):
        self.llm = None

    def _cache_pipeline_result(self, conversation_id: str, drug_name: str, full_results: dict):
        """Store pipeline results in memory cache for reuse within the same conversation."""
        if not conversation_id:
            return
        self._cleanup_expired_cache()
        MasterAgent._pipeline_cache[conversation_id] = {
            "data": full_results,
            "drug_name": drug_name,
            "timestamp": time.time(),
        }
        logger.info(f"Cached pipeline results for conversation {conversation_id} ({drug_name})")

    def _get_cached_pipeline(self, conversation_id: str, drug_name: str) -> Optional[dict]:
        """Retrieve cached pipeline results for a conversation + drug combo."""
        if not conversation_id:
            return None
        entry = MasterAgent._pipeline_cache.get(conversation_id)
        if not entry:
            return None
        if time.time() - entry["timestamp"] > self._CACHE_TTL_SECONDS:
            del MasterAgent._pipeline_cache[conversation_id]
            return None
        if entry["drug_name"].lower() != drug_name.lower():
            return None
        logger.info(f"Cache hit: pipeline results for {drug_name} in conversation {conversation_id}")
        return entry["data"]

    @classmethod
    def _cleanup_expired_cache(cls):
        """Remove expired entries and enforce max size."""
        now = time.time()
        expired = [k for k, v in cls._pipeline_cache.items() if now - v["timestamp"] > cls._CACHE_TTL_SECONDS]
        for k in expired:
            del cls._pipeline_cache[k]
        while len(cls._pipeline_cache) > cls._CACHE_MAX_ENTRIES:
            oldest_key = min(cls._pipeline_cache, key=lambda k: cls._pipeline_cache[k]["timestamp"])
            del cls._pipeline_cache[oldest_key]

    def _get_llm(self):
        if self.llm is None:
            self.llm = LLMFactory.get_llm()
        return self.llm

    async def interpret_query(
        self,
        message: str,
        conversation_history: List[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Interpret a user query and classify intent + extract entities.

        Returns dict with: intent, entities, agents_needed, clarification_questions, reasoning
        """
        llm = self._get_llm()
        if llm is None:
            return self._fallback_classify(message, conversation_history)

        # Format conversation history
        history_text = "No previous messages."
        if conversation_history:
            history_lines = []
            for msg in conversation_history[-6:]:  # Last 6 messages for context
                role = msg.get("role", "user")
                content = msg.get("content", "")[:200]
                history_lines.append(f"{role}: {content}")
            history_text = "\n".join(history_lines)

        prompt = INTENT_CLASSIFICATION_PROMPT.format(
            intents=json.dumps(INTENTS),
            agent_keys=json.dumps(list(ET_AGENT_NAMES.keys())),
            history=history_text,
            message=message
        )

        try:
            response = await llm.generate(prompt)
            # Parse JSON from response (handle markdown code blocks)
            json_str = response.strip()
            if json_str.startswith("```"):
                json_str = json_str.split("```")[1]
                if json_str.startswith("json"):
                    json_str = json_str[4:]
            json_str = json_str.strip()
            result = json.loads(json_str)

            # Validate required fields
            if "intent" not in result:
                result["intent"] = "general_question"
            if "entities" not in result:
                result["entities"] = {}
            if "agents_needed" not in result:
                result["agents_needed"] = self._default_agents_for_intent(result["intent"])
            if "clarification_questions" not in result:
                result["clarification_questions"] = []

            return result

        except (json.JSONDecodeError, Exception) as e:
            logger.warning(f"LLM classification failed, using fallback: {e}")
            return self._fallback_classify(message, conversation_history)

    def _fallback_classify(self, message: str, conversation_history: List[Dict[str, str]] = None) -> Dict[str, Any]:
        """Rule-based fallback when LLM is unavailable."""
        msg = message.lower().strip()
        entities = {"drug_names": [], "indications": [], "regions": []}

        # Check for ambiguous queries first — proactive clarification
        vague_patterns = ["show me data", "any opportunities", "what are the trends",
                          "tell me about", "what do you know", "give me information",
                          "help me with", "i need data", "show me everything"]
        is_vague = any(vp in msg for vp in vague_patterns) and len(msg.split()) < 10

        # Simple keyword-based intent detection
        if any(kw in msg for kw in ["generate a report", "generate report", "create a report", "create report",
                                      "full report", "make a report", "make report", "export report"]):
            intent = "report_generation"
            agents = ["pipeline", "report"]
        elif any(kw in msg for kw in ["analyze", "search", "repurpos", "find opportunities", "find indications"]):
            intent = "drug_analysis"
            agents = ["pipeline"]
        elif any(kw in msg for kw in ["market", "iqvia", "cagr", "growth", "market size", "sales"]):
            intent = "market_query"
            agents = ["market"]
        elif any(kw in msg for kw in ["patent", "ip ", "fto", "exclusiv", "biosimilar", "uspto"]):
            intent = "patent_lookup"
            agents = ["patent"]
        elif any(kw in msg for kw in ["exim", "export", "import", "trade", "sourcing"]):
            intent = "exim_data"
            agents = ["exim"]
        elif any(kw in msg for kw in ["trial", "clinical", "pipeline", "phase ", "ongoing stud"]):
            intent = "clinical_trials"
            agents = ["clinical_trials"]
        elif any(kw in msg for kw in ["guideline", "news", "publication", "real-world", "rwe"]):
            intent = "web_search"
            agents = ["web"]
        elif any(kw in msg for kw in ["summarize", "upload", "document", "pdf", "file"]):
            intent = "file_summary"
            agents = ["internal"]
        elif any(kw in msg for kw in ["compare", "versus", " vs ", "difference between"]):
            intent = "comparison"
            agents = ["market", "clinical_trials", "patent"]
        else:
            intent = "general_question"
            agents = ["web"]

        # Override to clarification_needed for vague queries without specifics
        clarification_questions = []
        if is_vague:
            intent = "clarification_needed"
            agents = []
            clarification_questions = self._generate_clarification_questions(msg, entities, conversation_history)
        elif intent in ("market_query", "clinical_trials", "patent_lookup"):
            # Check if query lacks a specific drug or indication
            has_drug = any(drug in msg for drug in [
                "metformin", "sildenafil", "aspirin", "ibuprofen", "atorvastatin",
                "adalimumab", "semaglutide", "pembrolizumab", "rituximab",
            ])
            has_area = any(area in msg for area in [
                "oncology", "cancer", "diabetes", "cardiovascular", "respiratory",
                "alzheimer", "parkinson", "obesity", "nash", "arthritis",
            ])
            if not has_drug and not has_area and not conversation_history:
                clarification_questions = self._generate_clarification_questions(msg, entities, conversation_history)
                if clarification_questions:
                    intent = "clarification_needed"
                    agents = []

        # Extract drug names (simple pattern: capitalize words that might be drug names)
        common_drugs = [
            "metformin", "sildenafil", "aspirin", "ibuprofen", "atorvastatin",
            "omeprazole", "amlodipine", "lisinopril", "metoprolol", "simvastatin",
            "losartan", "gabapentin", "sertraline", "montelukast", "pantoprazole",
            "thalidomide", "minoxidil", "adalimumab", "pembrolizumab", "semaglutide",
            "keytruda", "humira", "ozempic", "mounjaro", "wegovy", "dupixent",
            "rituximab", "trastuzumab", "bevacizumab", "nivolumab", "paclitaxel",
        ]
        for drug in common_drugs:
            if drug in msg:
                entities["drug_names"].append(drug.capitalize())

        # If no drug found in current message, scan conversation history
        # This enables multi-turn context chaining: "also check...", "what about...", etc.
        if not entities["drug_names"] and conversation_history:
            for hist_msg in reversed(conversation_history[-6:]):
                hist_text = hist_msg.get("content", "").lower()
                for drug in common_drugs:
                    if drug in hist_text:
                        entities["drug_names"].append(drug.capitalize())
                        break
                if entities["drug_names"]:
                    break

        # Also carry forward indications from history for referential queries
        referential_patterns = ["also check", "what about", "and the", "show me", "now check",
                                "how about", "can you also", "additionally", "furthermore"]
        is_referential = any(rp in msg for rp in referential_patterns)
        if is_referential and not entities.get("indications") and conversation_history:
            for hist_msg in reversed(conversation_history[-6:]):
                hist_text = hist_msg.get("content", "").lower()
                for area_kw, area_name in {
                    "oncology": "Cancer", "cancer": "Cancer", "diabetes": "Type 2 Diabetes",
                    "cardiovascular": "Cardiovascular Disease", "respiratory": "Asthma",
                    "alzheimer": "Alzheimer", "obesity": "Obesity", "nash": "NASH",
                    "arthritis": "Rheumatoid Arthritis",
                }.items():
                    if area_kw in hist_text and area_name not in entities.get("indications", []):
                        entities.setdefault("indications", []).append(area_name)
                if entities.get("indications"):
                    break

        return {
            "intent": intent,
            "entities": entities,
            "agents_needed": agents,
            "clarification_questions": clarification_questions,
            "reasoning": "Keyword-based classification (LLM unavailable)"
        }

    def _generate_clarification_questions(
        self, msg: str, entities: Dict, history: List[Dict[str, str]] = None
    ) -> List[str]:
        """Generate context-aware clarification questions for ambiguous queries."""
        questions = []

        has_drug = bool(entities.get("drug_names"))
        has_area = any(area in msg for area in [
            "oncology", "cancer", "diabetes", "cardiovascular", "respiratory",
            "alzheimer", "neurology", "obesity", "nash", "arthritis", "autoimmune",
        ])
        has_region = any(r in msg for r in [
            "india", "china", "us", "europe", "japan", "brazil", "global",
        ])

        # No drug or area specified — ask for both
        if not has_drug and not has_area:
            questions.append("Which drug or molecule are you interested in? (e.g., Metformin, Adalimumab, Semaglutide)")
            questions.append("Which therapeutic area should I focus on? (e.g., oncology, diabetes, cardiovascular, respiratory)")

        # Has drug but unclear what data they want
        if has_drug and "market" not in msg and "patent" not in msg and "trial" not in msg:
            drug = entities["drug_names"][0] if entities.get("drug_names") else "this molecule"
            questions.append(f"Would you like market data, clinical trial pipeline, or patent landscape for {drug}?")

        # Broad area question — ask what dimension
        if has_area and not has_drug:
            questions.append("Do you want market size & competition data, or clinical trial activity in this area?")

        # Region mentioned but no data type
        if has_region and "exim" not in msg and "trade" not in msg and "market" not in msg:
            questions.append("Are you looking for EXIM trade data, market size, or clinical trial activity for this region?")

        # Generic fallback
        if not questions:
            questions = [
                "Could you specify a drug name or therapeutic area?",
                "What type of analysis do you need — market, patents, clinical trials, or a full drug report?",
            ]

        return questions[:3]

    def _default_agents_for_intent(self, intent: str) -> List[str]:
        """Get default agent list for an intent."""
        mapping = {
            "drug_analysis": ["pipeline"],
            "report_generation": ["pipeline", "report"],
            "market_query": ["market"],
            "patent_lookup": ["patent"],
            "exim_data": ["exim"],
            "clinical_trials": ["clinical_trials"],
            "web_search": ["web"],
            "file_summary": ["internal"],
            "comparison": ["market", "clinical_trials", "patent"],
            "general_question": ["web"],
            "clarification_needed": [],
        }
        return mapping.get(intent, ["web"])

    async def execute_agents(
        self,
        intent: str,
        entities: Dict[str, Any],
        agents_needed: List[str],
        message: str,
        uploaded_file_ids: List[str] = None,
        session_id: str = None,
        conversation_id: str = None,
    ) -> Dict[str, Any]:
        """
        Execute the appropriate worker agents based on intent and entities.

        Returns dict of agent_key → result data.
        """
        results = {}

        for agent_key in agents_needed:
            try:
                if agent_key == "pipeline":
                    results["pipeline"] = await self._run_drug_pipeline(
                        entities, session_id=session_id, conversation_id=conversation_id
                    )
                elif agent_key == "market":
                    results["market"] = await self._run_market_agent(entities, message)
                elif agent_key == "exim":
                    results["exim"] = await self._run_exim_agent(entities, message)
                elif agent_key == "patent":
                    results["patent"] = await self._run_patent_agent(entities, message)
                elif agent_key == "clinical_trials":
                    results["clinical_trials"] = await self._run_clinical_trials_agent(entities, message)
                elif agent_key == "web":
                    results["web"] = await self._run_web_agent(entities, message)
                elif agent_key == "internal":
                    results["internal"] = await self._run_internal_agent(entities, message, uploaded_file_ids)
                elif agent_key == "report":
                    # Send WebSocket update: report agent is now running
                    if session_id:
                        try:
                            from app.routes.repurpose.websocket import manager as ws_mgr
                            await ws_mgr.send_agent_progress(
                                session_id, "report", "running", "Generating PDF report..."
                            )
                        except Exception:
                            pass
                    results["report"] = await self._run_report_agent(
                        entities, results, conversation_id=conversation_id
                    )
            except Exception as e:
                logger.error(f"Agent {agent_key} failed: {e}", exc_info=True)
                results[agent_key] = {"error": str(e), "status": "error"}

        return results

    async def synthesize_response(
        self,
        message: str,
        intent: str,
        agent_results: Dict[str, Any],
        entities: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Synthesize agent results into a final user-facing response.

        Returns dict with: content, tables, charts, pdf_url, suggestions
        """
        llm = self._get_llm()

        # Collect tables and charts from agent results
        tables = []
        charts = []
        pdf_url = None
        excel_url = None

        for key, result in agent_results.items():
            if isinstance(result, dict):
                if "tables" in result:
                    tables.extend(result["tables"])
                if "charts" in result:
                    charts.extend(result["charts"])
                if "pdf_url" in result:
                    pdf_url = result["pdf_url"]
                if "excel_url" in result:
                    excel_url = result["excel_url"]

        # Build agent data summary for LLM
        agent_data_parts = []
        for key, result in agent_results.items():
            agent_name = ET_AGENT_NAMES.get(key, key)
            if isinstance(result, dict) and "error" not in result:
                # Summarize the result for the LLM
                summary = result.get("summary", "")
                if not summary and "data" in result:
                    summary = json.dumps(result["data"], indent=2, default=str)[:2000]
                elif not summary:
                    summary = json.dumps(result, indent=2, default=str)[:2000]
                agent_data_parts.append(f"### {agent_name}\n{summary}")
            elif isinstance(result, dict) and "error" in result:
                agent_data_parts.append(f"### {agent_name}\nError: {result['error']}")

        agent_data_text = "\n\n".join(agent_data_parts) if agent_data_parts else "No agent data collected."

        # Generate synthesis with LLM
        suggestions = []
        if llm:
            try:
                prompt = SYNTHESIS_PROMPT.format(
                    question=message,
                    agent_data=agent_data_text
                )
                response_text = await llm.generate(prompt)

                # Extract suggestions from response
                if "## Suggested Follow-ups" in response_text:
                    parts = response_text.split("## Suggested Follow-ups")
                    content = parts[0].strip()
                    suggestion_text = parts[1].strip()
                    for line in suggestion_text.split("\n"):
                        line = line.strip().lstrip("-•* ")
                        if line and len(line) > 5:
                            suggestions.append(line)
                else:
                    content = response_text.strip()
            except Exception as e:
                logger.error(f"Synthesis failed: {e}")
                content = agent_data_text
        else:
            content = agent_data_text

        if not suggestions:
            suggestions = self._generate_default_suggestions(intent, entities)

        return {
            "content": content,
            "tables": tables,
            "charts": charts,
            "pdf_url": pdf_url,
            "excel_url": excel_url,
            "suggestions": suggestions[:3],
        }

    def _generate_default_suggestions(self, intent: str, entities: Dict) -> List[str]:
        """Generate default follow-up suggestions based on intent."""
        drug_names = entities.get("drug_names", [])
        drug = drug_names[0] if drug_names else "the drug"

        suggestion_map = {
            "drug_analysis": [
                f"What is the patent landscape for {drug}?",
                f"Show EXIM trade data for {drug}",
                f"Generate a detailed PDF report for {drug}",
            ],
            "market_query": [
                "Which segments have the highest unmet need?",
                f"What clinical trials are ongoing in this space?",
                "Show the competitive filing heatmap",
            ],
            "patent_lookup": [
                "Are there any biosimilar opportunities?",
                f"What is the EXIM trend for {drug}?",
                "Show ongoing clinical trials for this molecule",
            ],
            "exim_data": [
                "Which countries are the top exporters?",
                f"What is the patent status for {drug}?",
                "Show market growth trends for this molecule",
            ],
            "clinical_trials": [
                "What are the Phase 3 trials?",
                "Which sponsors are most active?",
                "Show patent expiry timelines for competing drugs",
            ],
        }
        return suggestion_map.get(intent, [
            "Analyze a specific drug for repurposing opportunities",
            "Show market data for a therapeutic area",
            "Check the patent landscape for a molecule",
        ])

    # =====================================================
    # Worker Agent Runners
    # =====================================================

    async def _run_drug_pipeline(self, entities: Dict, session_id: str = None, conversation_id: str = None) -> Dict:
        """Trigger the full 18-agent drug analysis pipeline with 4D scoring."""
        drug_names = entities.get("drug_names", [])
        if not drug_names:
            return {
                "summary": "No drug name detected. Please specify a drug to analyze.",
                "status": "needs_input"
            }

        drug_name = drug_names[0]

        try:
            from app.graph.workflow import get_workflow
            workflow = get_workflow()

            pipeline_session_id = session_id or f"chat-{uuid.uuid4().hex[:8]}"
            initial_state = {
                "drug_name": drug_name,
                "search_context": {},
                "session_id": pipeline_session_id,
            }

            result = await workflow.ainvoke(initial_state)

            # Extract key data for chat response
            enhanced = result.get("enhanced_indications", [])
            synthesis = result.get("synthesis", "")
            evidence_count = len(result.get("all_evidence", []))

            # Build summary tables with 4D scoring dimensions
            tables = []
            charts = []

            if enhanced:
                rows = []
                chart_labels = []
                chart_scores = []

                for ind in enhanced[:10]:
                    score_data = ind.get("composite_score") if isinstance(ind, dict) else getattr(ind, "composite_score", None)
                    if score_data is None:
                        continue

                    # Handle both dict and Pydantic model
                    if isinstance(score_data, dict):
                        overall = score_data.get("overall_score", 0)
                        confidence = score_data.get("confidence_level", "N/A")
                        sci = score_data.get("scientific_evidence", {}).get("score", 0)
                        mkt = score_data.get("market_opportunity", {}).get("score", 0)
                        comp = score_data.get("competitive_landscape", {}).get("score", 0)
                        feas = score_data.get("development_feasibility", {}).get("score", 0)
                    else:
                        overall = getattr(score_data, "overall_score", 0)
                        confidence = getattr(score_data, "confidence_level", "N/A")
                        sci = getattr(getattr(score_data, "scientific_evidence", None), "score", 0)
                        mkt = getattr(getattr(score_data, "market_opportunity", None), "score", 0)
                        comp = getattr(getattr(score_data, "competitive_landscape", None), "score", 0)
                        feas = getattr(getattr(score_data, "development_feasibility", None), "score", 0)

                    indication_name = ind.get("indication", "Unknown") if isinstance(ind, dict) else getattr(ind, "indication", "Unknown")
                    ev_count = ind.get("evidence_count", 0) if isinstance(ind, dict) else getattr(ind, "evidence_count", 0)

                    rows.append({
                        "#": len(rows) + 1,
                        "Indication": indication_name,
                        "Score": f"{overall:.1f}",
                        "Scientific": f"{sci:.0f}",
                        "Market": f"{mkt:.0f}",
                        "Competition": f"{comp:.0f}",
                        "Feasibility": f"{feas:.0f}",
                        "Confidence": str(confidence).replace("_", " ").title(),
                        "Evidence": ev_count,
                    })

                    if len(chart_labels) < 6:
                        chart_labels.append(indication_name[:18])
                        chart_scores.append(round(overall, 1))

                if rows:
                    tables.append({
                        "title": f"Top Repurposing Opportunities for {drug_name}",
                        "columns": [
                            {"key": "#", "label": "#"},
                            {"key": "Indication", "label": "Indication"},
                            {"key": "Score", "label": "Score"},
                            {"key": "Scientific", "label": "Scientific"},
                            {"key": "Market", "label": "Market"},
                            {"key": "Competition", "label": "Competition"},
                            {"key": "Feasibility", "label": "Feasibility"},
                            {"key": "Confidence", "label": "Confidence"},
                            {"key": "Evidence", "label": "Evidence"},
                        ],
                        "rows": rows,
                    })

                if chart_labels:
                    charts.append({
                        "title": f"Opportunity Scores — {drug_name}",
                        "type": "bar",
                        "labels": chart_labels,
                        "datasets": [{"label": "Overall Score", "data": chart_scores}],
                    })

            # Run decision rules engine on pipeline results
            try:
                from app.services.repurpose.decision.rules_engine import RulesEngine
                rules = RulesEngine()
                enhanced_opps = result.get("enhanced_opportunities", {})

                opportunity_flags = []
                for indication_name, opp_data in enhanced_opps.items():
                    market_data = {}
                    segment = getattr(opp_data, "market_segment", None)
                    if segment:
                        market_data = {
                            "unmet_need_score": getattr(segment, "unmet_need_score", 50) or 50,
                            "market_size_billions": 10,
                            "patient_population_millions": 50,
                        }

                    detected = rules.analyze(
                        market_data=market_data or None,
                        trial_data={"trial_count": 5},
                        drug_name=drug_name,
                        indication=indication_name,
                    )

                    for d in detected:
                        opportunity_flags.append(
                            f"**{d['title']}** ({d['confidence']}): {d['reasoning'][:150]}"
                        )

                if opportunity_flags:
                    synthesis += "\n\n### Decision Intelligence Flags\n" + "\n".join(f"- {f}" for f in opportunity_flags[:5])
            except Exception as e:
                logger.warning(f"Decision rules engine failed: {e}")

            # Cache pipeline results for reuse (e.g., report generation in a follow-up message)
            if conversation_id and result:
                self._cache_pipeline_result(conversation_id, drug_name, result)

            return {
                "summary": synthesis or f"Analysis complete for {drug_name}. Found {len(enhanced)} opportunities from {evidence_count} evidence items.",
                "data": {
                    "drug_name": drug_name,
                    "opportunities": len(enhanced),
                    "evidence_count": evidence_count,
                },
                "tables": tables,
                "charts": charts,
                "full_results": result,
                "status": "success",
            }

        except Exception as e:
            logger.error(f"Drug pipeline failed: {e}", exc_info=True)
            return {"summary": f"Analysis failed: {str(e)}", "status": "error", "error": str(e)}

    async def _run_market_agent(self, entities: Dict, message: str) -> Dict:
        """Run IQVIA Insights (market data) agent."""
        try:
            from app.services.repurpose.market.market_analyzer import MarketAnalyzer
            from app.services.repurpose.market.segment_analyzer import MarketSegmentAnalyzer
            from app.services.repurpose.market.competitor_tracker import CompetitorTracker

            analyzer = MarketAnalyzer()
            segment_analyzer = MarketSegmentAnalyzer()

            indications = entities.get("indications", [])
            drug_names = entities.get("drug_names", [])
            drug = drug_names[0] if drug_names else "Unknown"

            if not indications:
                # Try to extract from message
                indications = self._extract_therapeutic_areas(message)

            tables = []
            charts = []
            summaries = []

            for indication in indications[:5]:
                market_data_obj = await analyzer.analyze_market(indication, drug)
                market_data = market_data_obj.to_dict() if hasattr(market_data_obj, 'to_dict') else (market_data_obj if isinstance(market_data_obj, dict) else {})
                segment = await segment_analyzer.identify_segment(indication)

                mkt_size_b = round(market_data.get('estimated_market_size_usd', 0) / 1_000_000_000, 1)
                summaries.append(
                    f"**{indication}**: Market size ${mkt_size_b}B, "
                    f"CAGR {market_data.get('cagr_percent', 0)}%, "
                    f"Unmet Need: {market_data.get('unmet_need_score', 0)}/100"
                )

            if indications:
                # Build market comparison table
                rows = []
                chart_labels = []
                chart_sizes = []
                chart_cagrs = []

                for indication in indications[:5]:
                    market_data_obj = await analyzer.analyze_market(indication, drug)
                    market_data = market_data_obj.to_dict() if hasattr(market_data_obj, 'to_dict') else (market_data_obj if isinstance(market_data_obj, dict) else {})
                    mkt_size_b = round(market_data.get('estimated_market_size_usd', 0) / 1_000_000_000, 1)
                    rows.append({
                        "indication": indication,
                        "market_size": f"${mkt_size_b}B",
                        "cagr": f"{market_data.get('cagr_percent', 0)}%",
                        "patients": f"{round(market_data.get('patient_population_global', 0) / 1_000_000, 1)}M",
                        "unmet_need": f"{market_data.get('unmet_need_score', 0)}/100",
                        "pricing": f"{market_data.get('potential_price_premium', 1.0)}x",
                    })
                    chart_labels.append(indication[:20])
                    chart_sizes.append(mkt_size_b)
                    chart_cagrs.append(market_data.get("cagr_percent", 0))

                tables.append({
                    "title": "Market Overview",
                    "columns": [
                        {"key": "indication", "label": "Indication"},
                        {"key": "market_size", "label": "Market Size"},
                        {"key": "cagr", "label": "CAGR"},
                        {"key": "patients", "label": "Patients"},
                        {"key": "unmet_need", "label": "Unmet Need"},
                        {"key": "pricing", "label": "Pricing"},
                    ],
                    "rows": rows
                })

                charts.append({
                    "chart_type": "bar",
                    "title": "Market Size Comparison ($B)",
                    "labels": chart_labels,
                    "datasets": [
                        {"label": "Market Size ($B)", "data": chart_sizes, "color": "#00D4AA"},
                        {"label": "CAGR (%)", "data": chart_cagrs, "color": "#FFE600"},
                    ]
                })

            return {
                "summary": "\n".join(summaries) if summaries else "No market data found for the specified indications.",
                "tables": tables,
                "charts": charts,
                "status": "success"
            }

        except Exception as e:
            logger.error(f"Market agent failed: {e}", exc_info=True)
            return {"summary": f"Market analysis failed: {str(e)}", "status": "error", "error": str(e)}

    async def _run_exim_agent(self, entities: Dict, message: str) -> Dict:
        """Run EXIM Trade Agent with mock data."""
        try:
            from app.agents.repurposing.exim_agent import EXIMAgent
            agent = EXIMAgent()

            drug_names = entities.get("drug_names", [])
            drug = drug_names[0] if drug_names else None

            if not drug:
                # Try to extract from message
                drug = self._extract_drug_from_message(message)

            result = await agent.get_trade_data(drug or "Metformin")
            return result

        except Exception as e:
            logger.error(f"EXIM agent failed: {e}", exc_info=True)
            return {"summary": f"EXIM data lookup failed: {str(e)}", "status": "error", "error": str(e)}

    async def _run_patent_agent(self, entities: Dict, message: str) -> Dict:
        """Run Patent Landscape Agent (USPTO PatentsView)."""
        try:
            from app.agents.repurposing.patent_agent import PatentAgent
            agent = PatentAgent()

            drug_names = entities.get("drug_names", [])
            drug = drug_names[0] if drug_names else self._extract_drug_from_message(message)

            if not drug:
                return {"summary": "No drug specified for patent lookup.", "status": "needs_input"}

            # Use the rich get_patent_landscape method (tables, charts, FTO, expiry)
            result = await agent.get_patent_landscape(drug)
            return result

        except Exception as e:
            logger.error(f"Patent agent failed: {e}", exc_info=True)
            return {"summary": f"Patent lookup failed: {str(e)}", "status": "error", "error": str(e)}

    async def _run_clinical_trials_agent(self, entities: Dict, message: str) -> Dict:
        """Run Clinical Trials Agent."""
        try:
            from app.agents.repurposing.clinical_trials_agent import ClinicalTrialsAgent
            agent = ClinicalTrialsAgent()

            drug_names = entities.get("drug_names", [])
            drug = drug_names[0] if drug_names else self._extract_drug_from_message(message)

            if not drug:
                return {"summary": "No drug specified for clinical trial search.", "status": "needs_input"}

            response = await agent.run(drug, {})

            tables = []
            charts = []
            if response and response.evidence:
                rows = []
                sponsor_counts = {}
                phase_counts = {}
                for ev in response.evidence[:15]:
                    meta = ev.metadata or {}
                    sponsor = meta.get("sponsor", "Unknown")
                    phase = meta.get("phase", "N/A")
                    rows.append({
                        "title": (ev.title or ev.summary or "")[:50],
                        "phase": phase,
                        "status": meta.get("status", "N/A"),
                        "sponsor": sponsor[:25] if sponsor else "N/A",
                        "indication": (ev.indication or "N/A")[:30],
                        "date": ev.date or "N/A",
                    })
                    # Aggregate sponsor profiles
                    if sponsor and sponsor != "Unknown":
                        if sponsor not in sponsor_counts:
                            sponsor_counts[sponsor] = {"total": 0, "phases": {}}
                        sponsor_counts[sponsor]["total"] += 1
                        sponsor_counts[sponsor]["phases"][phase] = sponsor_counts[sponsor]["phases"].get(phase, 0) + 1
                    # Aggregate phase distribution
                    phase_counts[phase] = phase_counts.get(phase, 0) + 1

                if rows:
                    tables.append({
                        "title": f"Clinical Trials for {drug}",
                        "columns": [
                            {"key": "title", "label": "Trial"},
                            {"key": "phase", "label": "Phase"},
                            {"key": "status", "label": "Status"},
                            {"key": "sponsor", "label": "Sponsor"},
                            {"key": "indication", "label": "Indication"},
                            {"key": "date", "label": "Date"},
                        ],
                        "rows": rows
                    })

                # Sponsor profiles table
                if sponsor_counts:
                    top_sponsors = sorted(sponsor_counts.items(), key=lambda x: x[1]["total"], reverse=True)[:10]
                    sponsor_rows = []
                    for sname, sdata in top_sponsors:
                        phase_str = ", ".join(f"{p}: {c}" for p, c in sorted(sdata["phases"].items()))
                        sponsor_rows.append({
                            "sponsor": sname[:35],
                            "trials": sdata["total"],
                            "phases": phase_str,
                        })
                    tables.append({
                        "title": f"Top Sponsors — {drug}",
                        "columns": [
                            {"key": "sponsor", "label": "Sponsor"},
                            {"key": "trials", "label": "Trials"},
                            {"key": "phases", "label": "Phase Distribution"},
                        ],
                        "rows": sponsor_rows,
                    })

                # Phase distribution chart
                if phase_counts:
                    phase_labels = sorted(phase_counts.keys())
                    charts.append({
                        "title": f"Trial Phase Distribution — {drug}",
                        "chart_type": "bar",
                        "labels": phase_labels,
                        "datasets": [{"label": "Trials", "data": [phase_counts[p] for p in phase_labels], "color": "#00B4D8"}],
                    })

            evidence_count = len(response.evidence) if response else 0
            return {
                "summary": f"Found {evidence_count} clinical trials for {drug}.",
                "tables": tables,
                "charts": charts,
                "status": "success"
            }

        except Exception as e:
            logger.error(f"Clinical trials agent failed: {e}", exc_info=True)
            return {"summary": f"Clinical trials search failed: {str(e)}", "status": "error", "error": str(e)}

    async def _run_web_agent(self, entities: Dict, message: str) -> Dict:
        """Run Web Intelligence Agent."""
        try:
            from app.agents.repurposing.web_intelligence_agent import WebIntelligenceAgent
            agent = WebIntelligenceAgent()
            result = await agent.search(message, entities)
            return result
        except Exception as e:
            logger.error(f"Web agent failed: {e}", exc_info=True)
            return {"summary": f"Web search failed: {str(e)}", "status": "error", "error": str(e)}

    async def _run_internal_agent(self, entities: Dict, message: str, file_ids: List[str] = None) -> Dict:
        """Run Internal Knowledge Agent."""
        try:
            from app.services.repurpose.vector_store import get_knowledge_base
            kb = get_knowledge_base()

            drug_names = entities.get("drug_names", [])
            indications = entities.get("indications", [])

            query = message
            if drug_names:
                query = f"{drug_names[0]} {query}"

            results = kb.query(query, n_results=5)

            summaries = []
            for doc in results:
                if isinstance(doc, dict):
                    summaries.append(doc.get("document", doc.get("content", ""))[:200])
                elif isinstance(doc, str):
                    summaries.append(doc[:200])

            return {
                "summary": "\n\n".join(summaries) if summaries else "No relevant internal documents found.",
                "status": "success"
            }

        except Exception as e:
            logger.error(f"Internal agent failed: {e}", exc_info=True)
            return {"summary": f"Internal search failed: {str(e)}", "status": "error", "error": str(e)}

    async def _run_report_agent(self, entities: Dict, collected_results: Dict, conversation_id: str = None) -> Dict:
        """Generate a PDF report from collected results and archive it."""
        drug_names = entities.get("drug_names", [])
        if not drug_names:
            return {
                "summary": "No drug specified for report generation. Please specify a drug name.",
                "status": "error",
            }

        drug_name = drug_names[0]
        logger.info(f"Report agent: Generating report for {drug_name}")

        try:
            # Check if pipeline results exist from this request's collected_results
            pipeline_result = collected_results.get("pipeline")

            # _run_drug_pipeline() returns a processed dict with "full_results" containing the raw workflow state
            # Extract raw pipeline state needed for PDF generation
            pipeline_data = None
            if isinstance(pipeline_result, dict):
                pipeline_data = pipeline_result.get("full_results")

            # Check in-memory cache if no pipeline data from current request
            if not pipeline_data or not isinstance(pipeline_data, dict):
                if conversation_id:
                    pipeline_data = self._get_cached_pipeline(conversation_id, drug_name)
                    if pipeline_data:
                        logger.info(f"Using cached pipeline results for report generation ({drug_name})")

            if not pipeline_data or not isinstance(pipeline_data, dict):
                # Run the full pipeline to get data for the report
                logger.info(f"No pipeline results found, running full search for {drug_name}")
                from app.graph.workflow import get_workflow

                workflow = get_workflow()
                session_id = f"report-{uuid.uuid4().hex[:8]}"
                initial_state = {
                    "drug_name": drug_name,
                    "search_context": {},
                    "session_id": session_id,
                }
                pipeline_data = await workflow.ainvoke(initial_state)

            # Generate PDF directly from pipeline dict (no Pydantic wrapping needed)
            # generate_pdf_report() accepts Union[dict, SearchResponse] and uses safe_get() internally
            from app.services.repurpose.utils.html_pdf_generator import generate_pdf_report
            import asyncio

            # Ensure drug_name is set in pipeline_data for the template
            if "drug_name" not in pipeline_data:
                pipeline_data["drug_name"] = drug_name

            pdf_bytes = await asyncio.to_thread(generate_pdf_report, pipeline_data)

            # Archive the PDF report
            from app.services.repurpose.archive.report_archive_manager import ReportArchiveManager
            archive = ReportArchiveManager()

            report_metadata = archive.archive_report(
                pdf_bytes=pdf_bytes,
                drug_name=drug_name,
                report_type="full_report",
                session_id=pipeline_data.get("session_id"),
            )

            report_id = report_metadata["report_id"]
            download_url = f"/api/reports/{report_id}/download"

            logger.info(f"PDF report generated and archived: {report_id} ({len(pdf_bytes):,} bytes)")

            # Generate Excel report (non-blocking — PDF is the primary deliverable)
            excel_url = None
            try:
                from app.services.repurpose.utils.excel_generator import generate_excel_report
                excel_bytes = await asyncio.to_thread(generate_excel_report, pipeline_data)

                excel_metadata = archive.archive_report(
                    pdf_bytes=excel_bytes,
                    drug_name=drug_name,
                    report_type="excel_report",
                    session_id=pipeline_data.get("session_id"),
                )
                excel_url = f"/api/reports/{excel_metadata['report_id']}/download"
                logger.info(f"Excel report archived: {excel_metadata['report_id']} ({len(excel_bytes):,} bytes)")
            except Exception as excel_err:
                logger.warning(f"Excel generation failed (non-blocking): {excel_err}")

            opp_count = len(pipeline_data.get("enhanced_indications", pipeline_data.get("ranked_indications", [])))
            return {
                "summary": f"PDF report for **{drug_name}** has been generated successfully with {opp_count} repurposing opportunities analyzed.",
                "status": "success",
                "report_id": report_id,
                "pdf_url": download_url,
                "excel_url": excel_url,
                "file_size": len(pdf_bytes),
            }

        except Exception as e:
            logger.error(f"Report agent failed: {e}", exc_info=True)
            return {
                "summary": f"Failed to generate report: {str(e)}",
                "status": "error",
                "error": str(e),
            }

    # =====================================================
    # Utility methods
    # =====================================================

    def _extract_therapeutic_areas(self, message: str) -> List[str]:
        """Extract therapeutic areas from a message using keyword matching."""
        areas = {
            "oncology": "Cancer", "cancer": "Cancer", "tumor": "Cancer",
            "diabetes": "Type 2 Diabetes", "metabolic": "Type 2 Diabetes",
            "cardiovascular": "Cardiovascular Disease", "heart": "Heart Failure",
            "respiratory": "Asthma", "lung": "Lung Cancer", "copd": "COPD",
            "neurolog": "Alzheimer", "alzheimer": "Alzheimer", "parkinson": "Parkinson",
            "depression": "Depression", "psychiatr": "Depression",
            "autoimmune": "Rheumatoid Arthritis", "arthritis": "Rheumatoid Arthritis",
            "immunolog": "Rheumatoid Arthritis",
            "obesity": "Obesity", "nash": "NASH", "liver": "NASH",
            "infectious": "HIV", "hiv": "HIV",
            "rare disease": "Rare Disease", "orphan": "Rare Disease",
        }

        found = []
        msg = message.lower()
        for keyword, area in areas.items():
            if keyword in msg and area not in found:
                found.append(area)

        return found if found else ["Cancer", "Type 2 Diabetes", "Cardiovascular Disease"]

    def _extract_drug_from_message(self, message: str) -> Optional[str]:
        """Try to extract a drug name from the message text."""
        common_drugs = [
            "metformin", "sildenafil", "aspirin", "ibuprofen", "atorvastatin",
            "omeprazole", "amlodipine", "lisinopril", "metoprolol", "simvastatin",
            "losartan", "gabapentin", "sertraline", "thalidomide", "minoxidil",
            "adalimumab", "pembrolizumab", "semaglutide", "rituximab",
            "trastuzumab", "bevacizumab", "nivolumab", "paclitaxel",
            "keytruda", "humira", "ozempic", "mounjaro", "wegovy",
        ]
        msg = message.lower()
        for drug in common_drugs:
            if drug in msg:
                return drug.capitalize()
        return None
