"""
LLM Controller - Agent loop for SMB contact discovery
Phase 2 of the LLM-first architecture

The controller asks the LLM at each step: "What tool should we call next?"
This enables:
1. Early exit when we have confident contact info
2. Smart tool selection based on what data is missing
3. Cost savings by skipping unnecessary API calls
"""

import json
import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Awaitable

from modules.llm.provider import LLMProvider

logger = logging.getLogger(__name__)


class ActionType(Enum):
    """Action types the LLM can request"""
    CALL_TOOL = "call_tool"
    DONE = "done"
    SKIP = "skip"


@dataclass
class ToolResult:
    """Result from a tool execution"""
    tool_name: str
    success: bool
    data: dict
    cost: float = 0.0


@dataclass
class Action:
    """Action requested by the LLM"""
    type: ActionType
    tool_name: str | None = None
    reason: str = ""
    final_contact: dict | None = None
    confidence: float = 0.0


@dataclass
class ControllerState:
    """State maintained during agent loop"""
    company_name: str
    domain: str | None = None
    city: str | None = None
    state: str | None = None
    vertical: str | None = None

    # Accumulated data
    candidates: list[dict] = field(default_factory=list)
    tool_results: dict[str, ToolResult] = field(default_factory=dict)

    # Tracking
    stage: int = 0
    total_cost: float = 0.0
    max_stages: int = 5

    def to_context(self) -> str:
        """Convert state to context string for LLM"""
        lines = [
            f"Company: {self.company_name}",
            f"Domain: {self.domain or 'Unknown'}",
            f"Location: {self.city}, {self.state}" if self.city and self.state else "",
            f"Vertical: {self.vertical or 'Unknown'}",
            f"\nDiscovered so far:",
        ]

        # Summarize tool results
        for tool_name, result in self.tool_results.items():
            if result.success:
                lines.append(f"\n[{tool_name}] Success:")
                for key, value in result.data.items():
                    if value:
                        lines.append(f"  - {key}: {value}")
            else:
                lines.append(f"\n[{tool_name}] Failed or no data")

        # Summarize candidates
        if self.candidates:
            lines.append(f"\nCandidates ({len(self.candidates)}):")
            for i, c in enumerate(self.candidates[:3], 1):  # Top 3
                name = c.get("name", "Unknown")
                email = c.get("email", "None")
                phone = c.get("phone", "None")
                sources = ", ".join(c.get("sources", []))
                lines.append(f"  {i}. {name} | email: {email} | phone: {phone} | sources: {sources}")
        else:
            lines.append("\nNo candidates found yet.")

        return "\n".join(lines)


# Tool definitions for OpenAI function calling format
TOOL_DEFINITIONS = [
    {
        "name": "google_maps_lookup",
        "description": "Search Google Maps for the business. Returns owner name, phone, email, address, reviews. Cost: $0.002. ALWAYS call this first for SMBs - it's the cheapest and most reliable source.",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Search query (company name + city)"
                }
            },
            "required": ["query"]
        }
    },
    {
        "name": "website_contacts",
        "description": "Scrape the company website for contact info (emails, phones, social links). Cost: $0.002. Use when domain is known but need more contact methods.",
        "parameters": {
            "type": "object",
            "properties": {
                "domain": {
                    "type": "string",
                    "description": "Company domain to scrape"
                }
            },
            "required": ["domain"]
        }
    },
    {
        "name": "serper_osint",
        "description": "Search the web for owner/contact information using Google. Cost: $0.001. Use when Google Maps didn't find owner name, or to verify/find additional info.",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Search query for finding owner info"
                }
            },
            "required": ["query"]
        }
    },
    {
        "name": "data_fill",
        "description": "Fill missing data (domain, phone) using web search. Cost: $0.001. Use when domain is missing.",
        "parameters": {
            "type": "object",
            "properties": {
                "company_name": {
                    "type": "string",
                    "description": "Company name to search for"
                }
            },
            "required": ["company_name"]
        }
    },
    {
        "name": "finish_with_contact",
        "description": "Accept the best candidate and finish. Use when you have HIGH confidence (80%+) that the contact is correct.",
        "parameters": {
            "type": "object",
            "properties": {
                "name": {"type": "string", "description": "Contact full name"},
                "email": {"type": "string", "description": "Contact email"},
                "phone": {"type": "string", "description": "Contact phone"},
                "title": {"type": "string", "description": "Job title"},
                "confidence": {"type": "number", "description": "Your confidence 0-100"},
                "reason": {"type": "string", "description": "Why this contact is valid"}
            },
            "required": ["confidence", "reason"]
        }
    },
    {
        "name": "finish_no_contact",
        "description": "Give up - no valid contact found. Use when all tools have been tried or remaining tools are unlikely to help.",
        "parameters": {
            "type": "object",
            "properties": {
                "reason": {"type": "string", "description": "Why no contact was found"}
            },
            "required": ["reason"]
        }
    }
]


CONTROLLER_SYSTEM = """You are an SMB contact discovery agent. Your job is to find the owner/manager of small businesses efficiently.

GOAL: Find a REAL PERSON name (first + last) who is the owner, with their phone and/or email.

STRATEGY:
1. ALWAYS start with google_maps_lookup - it's cheapest ($0.002) and best for SMBs
2. If Google Maps returns a real person name (first + last like "John Smith") with phone → FINISH EARLY!
3. If Google Maps only returns company name as owner → need more tools
4. If you have person name but need email → try website_contacts
5. If no owner found → try serper_osint as last resort

CRITICAL RULES:
- Company names are NOT valid contacts: "Nickel Bros" is NOT a person
- Real person names look like: "John Smith", "Maria Garcia", "Kirk R. Wainwright"
- SMB owners often name their business after themselves - "Doug Campbell" owning "Doug Campbell Backhoe" is VALID
- Single word names (no last name) are LOW confidence unless you have strong evidence
- Generic emails (info@, contact@, office@) are LOW confidence without a name

COST AWARENESS:
- google_maps_lookup: $0.002 (always call first)
- website_contacts: $0.002
- serper_osint: $0.001
- data_fill: $0.001
- Total budget per company: ~$0.01

WHEN TO FINISH:
- FINISH if: Real person name (first+last) + phone/email from reliable source → 80%+ confidence
- FINISH if: Real person name with Owner/Founder title from Google Maps → 75%+ confidence
- CONTINUE if: Only company name, or only email with no name, or single-word name
- GIVE UP if: 3+ tools tried with no valid person name found

You must respond with a function call to one of the available tools."""


CONTROLLER_PROMPT = """Current state:
{context}

Tools already called: {tools_called}
Remaining budget: ${remaining_budget:.4f}

What should we do next? Call a tool or finish."""


class LLMController:
    """Agent loop controller for SMB contact discovery"""

    def __init__(
        self,
        llm_provider: LLMProvider,
        tools: dict[str, Callable[..., Awaitable[ToolResult]]],
        max_stages: int = 5,
        cost_budget: float = 0.015
    ):
        """
        Initialize the controller.

        Args:
            llm_provider: LLM provider for decision making
            tools: Dict mapping tool names to async functions
            max_stages: Maximum number of tool calls per company
            cost_budget: Maximum cost per company in dollars
        """
        self.llm = llm_provider
        self.tools = tools
        self.max_stages = max_stages
        self.cost_budget = cost_budget

        # Stats
        self.total_llm_calls = 0
        self.total_tool_calls = 0
        self.early_exits = 0

    async def process_company(
        self,
        company_name: str,
        domain: str | None = None,
        city: str | None = None,
        state_code: str | None = None,
        vertical: str | None = None
    ) -> dict:
        """
        Process a single company through the agent loop.

        Returns:
            dict with contact info and metadata
        """
        state = ControllerState(
            company_name=company_name,
            domain=domain,
            city=city,
            state=state_code,
            vertical=vertical,
            max_stages=self.max_stages
        )

        while state.stage < state.max_stages:
            # Check budget
            remaining_budget = self.cost_budget - state.total_cost
            if remaining_budget <= 0:
                logger.debug(f"Budget exhausted for {company_name}")
                break

            # Ask LLM for next action
            action = await self._get_next_action(state, remaining_budget)
            self.total_llm_calls += 1

            if action.type == ActionType.DONE:
                if action.final_contact and action.confidence >= 50:
                    self.early_exits += 1
                    logger.info(f"Early exit for {company_name}: {action.final_contact.get('name')} (confidence: {action.confidence})")
                return self._build_result(state, action)

            elif action.type == ActionType.CALL_TOOL:
                if action.tool_name and action.tool_name in self.tools:
                    try:
                        result = await self._call_tool(action.tool_name, state)
                        state.tool_results[action.tool_name] = result
                        state.total_cost += result.cost
                        self.total_tool_calls += 1

                        # Update candidates from tool result
                        self._update_candidates(state, action.tool_name, result)

                    except Exception as e:
                        logger.warning(f"Tool {action.tool_name} failed: {e}")
                        state.tool_results[action.tool_name] = ToolResult(
                            tool_name=action.tool_name,
                            success=False,
                            data={"error": str(e)}
                        )

            state.stage += 1

        # Max stages reached - return best candidate
        return self._build_result(state, Action(
            type=ActionType.DONE,
            reason="Max stages reached",
            confidence=0
        ))

    async def _get_next_action(self, state: ControllerState, remaining_budget: float) -> Action:
        """Ask LLM what to do next"""
        context = state.to_context()
        tools_called = list(state.tool_results.keys()) or ["none yet"]

        prompt = CONTROLLER_PROMPT.format(
            context=context,
            tools_called=", ".join(tools_called),
            remaining_budget=remaining_budget
        )

        try:
            # Use function calling to get structured response
            # For now, use JSON mode with tool descriptions embedded
            response = await self.llm.complete_json(
                prompt=prompt + "\n\nRespond with JSON: {\"tool\": \"tool_name\", \"params\": {...}, \"reason\": \"...\"}",
                system=CONTROLLER_SYSTEM + "\n\nAvailable tools:\n" + json.dumps(TOOL_DEFINITIONS, indent=2),
                temperature=0.1,
                max_tokens=300
            )

            tool_name = response.get("tool", "")
            params = response.get("params", {})
            reason = response.get("reason", "")

            if tool_name == "finish_with_contact":
                return Action(
                    type=ActionType.DONE,
                    final_contact={
                        "name": params.get("name"),
                        "email": params.get("email"),
                        "phone": params.get("phone"),
                        "title": params.get("title", "Owner"),
                    },
                    confidence=params.get("confidence", 0),
                    reason=reason
                )
            elif tool_name == "finish_no_contact":
                return Action(
                    type=ActionType.DONE,
                    reason=params.get("reason", reason),
                    confidence=0
                )
            else:
                return Action(
                    type=ActionType.CALL_TOOL,
                    tool_name=tool_name,
                    reason=reason
                )

        except Exception as e:
            logger.error(f"LLM decision failed: {e}")
            # Fallback: call google_maps if not done, else finish
            if "google_maps_lookup" not in state.tool_results:
                return Action(type=ActionType.CALL_TOOL, tool_name="google_maps_lookup")
            return Action(type=ActionType.DONE, reason=f"LLM error: {e}")

    async def _call_tool(self, tool_name: str, state: ControllerState) -> ToolResult:
        """Execute a tool and return the result"""
        tool_fn = self.tools.get(tool_name)
        if not tool_fn:
            raise ValueError(f"Unknown tool: {tool_name}")

        # Build tool arguments based on state
        if tool_name == "google_maps_lookup":
            query = f"{state.company_name} {state.city or ''} {state.state or ''}".strip()
            return await tool_fn(query=query)

        elif tool_name == "website_contacts":
            if not state.domain:
                return ToolResult(tool_name=tool_name, success=False, data={"error": "No domain"})
            return await tool_fn(domain=state.domain)

        elif tool_name == "serper_osint":
            return await tool_fn(
                company_name=state.company_name,
                domain=state.domain,
                city=state.city,
                state=state.state
            )

        elif tool_name == "data_fill":
            return await tool_fn(
                company_name=state.company_name,
                city=state.city,
                state=state.state
            )

        else:
            raise ValueError(f"Unknown tool: {tool_name}")

    def _update_candidates(self, state: ControllerState, tool_name: str, result: ToolResult):
        """Update candidate list from tool result"""
        if not result.success:
            return

        data = result.data

        # Extract candidates based on tool
        if tool_name == "google_maps_lookup":
            if data.get("owner_name"):
                state.candidates.append({
                    "name": data["owner_name"],
                    "title": "Owner",
                    "phone": data.get("phone"),
                    "email": data.get("email"),
                    "sources": ["google_maps_owner"]
                })
            # Update domain if found
            if data.get("domain") and not state.domain:
                state.domain = data["domain"]

        elif tool_name == "website_contacts":
            if data.get("emails"):
                for email in data["emails"][:2]:  # Top 2 emails
                    state.candidates.append({
                        "email": email,
                        "phone": data.get("phone"),
                        "sources": ["website_contacts"]
                    })

        elif tool_name == "serper_osint":
            if data.get("owner_name"):
                state.candidates.append({
                    "name": data["owner_name"],
                    "title": data.get("title", "Owner"),
                    "sources": ["serper_osint"]
                })

        elif tool_name == "data_fill":
            if data.get("domain") and not state.domain:
                state.domain = data["domain"]

    def _build_result(self, state: ControllerState, final_action: Action) -> dict:
        """Build final result dict"""
        result = {
            "company_name": state.company_name,
            "domain": state.domain,
            "stages_completed": list(state.tool_results.keys()),
            "total_cost": state.total_cost,
            "llm_stages": state.stage,
            "candidates": state.candidates,
        }

        if final_action.final_contact:
            result["contact"] = final_action.final_contact
            result["contact"]["confidence"] = final_action.confidence
            result["contact"]["validation_reason"] = final_action.reason
        else:
            result["contact"] = None
            result["no_contact_reason"] = final_action.reason

        return result

    def get_stats(self) -> dict:
        """Get controller statistics"""
        return {
            "total_llm_calls": self.total_llm_calls,
            "total_tool_calls": self.total_tool_calls,
            "early_exits": self.early_exits,
            "early_exit_rate": self.early_exits / max(1, self.total_llm_calls - self.early_exits)
        }
