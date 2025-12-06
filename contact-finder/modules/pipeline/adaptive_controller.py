"""
Adaptive LLM Controller - Elastic strategy selection based on business type

This controller:
1. Classifies the business type (SMB, Franchise, Healthcare, Corporate)
2. Selects the optimal strategy for that type
3. Adapts mid-flight if initial strategy fails
4. Uses different tools based on what's most effective for the type
"""

import json
import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Callable, Awaitable

from modules.llm.provider import LLMProvider

logger = logging.getLogger(__name__)


class BusinessType(Enum):
    """Types of businesses with different contact discovery strategies"""
    SMB = "smb"                    # True small business - owner findable via Google Maps
    FRANCHISE = "franchise"        # Franchise location - need franchisee, not corporate
    HEALTHCARE = "healthcare"      # Healthcare facility - need administrator/practice manager
    CORPORATE = "corporate"        # Corporate chain location - manager via LinkedIn/job posts
    UNKNOWN = "unknown"            # Can't determine - try SMB strategy first


@dataclass
class Strategy:
    """Strategy configuration for a business type"""
    name: str
    tools_priority: list[str]  # Tools to try in order
    target_titles: list[str]   # What titles we're looking for
    system_prompt_addon: str   # Additional context for LLM
    max_stages: int = 5
    min_confidence: int = 60   # Minimum confidence to accept


# Strategy definitions for each business type
STRATEGIES = {
    BusinessType.SMB: Strategy(
        name="SMB Owner Discovery",
        tools_priority=["google_maps_lookup", "website_contacts", "serper_osint", "data_fill"],
        target_titles=["Owner", "Founder", "President", "Principal", "Proprietor"],
        system_prompt_addon="""
TARGET: Find the OWNER of this small business.
SMB owners often:
- Are named in Google Maps as the owner
- Have their name in the business name (e.g., "Doug Campbell Backhoe" = Doug Campbell)
- Are the only contact on simple business websites
PRIORITY: Google Maps first (most reliable), then website, then SERP search.""",
        max_stages=4,
        min_confidence=70
    ),

    BusinessType.FRANCHISE: Strategy(
        name="Franchise Owner Discovery",
        tools_priority=["linkedin_search", "serper_osint", "google_maps_lookup", "franchise_db"],
        target_titles=["Franchisee", "Franchise Owner", "Owner/Operator", "Owner"],
        system_prompt_addon="""
TARGET: Find the FRANCHISEE (local owner), NOT corporate contacts.
Franchise owners:
- May not appear in Google Maps (shows brand, not franchisee)
- Often on LinkedIn with title "Owner at [Brand] [Location]"
- May be in local news articles about franchise opening
AVOID: Corporate HQ contacts, district managers, 800 numbers.""",
        max_stages=5,
        min_confidence=65
    ),

    BusinessType.HEALTHCARE: Strategy(
        name="Healthcare Contact Discovery",
        tools_priority=["npi_lookup", "website_contacts", "linkedin_search", "serper_osint"],
        target_titles=["Practice Manager", "Administrator", "Office Manager", "Medical Director", "Owner"],
        system_prompt_addon="""
TARGET: Find PRACTICE MANAGER or ADMINISTRATOR, not the doctor (unless owner).
Healthcare contacts:
- NPI Registry has practitioner info
- Practice websites list admin staff
- LinkedIn for practice managers
AVOID: Generic appointment lines, patient portals.""",
        max_stages=5,
        min_confidence=60
    ),

    BusinessType.CORPORATE: Strategy(
        name="Corporate Location Contact Discovery",
        tools_priority=["linkedin_search", "serper_osint", "google_maps_lookup"],
        target_titles=["General Manager", "Store Manager", "Location Manager", "District Manager"],
        system_prompt_addon="""
TARGET: Find the LOCAL MANAGER if possible, otherwise SKIP.
Corporate locations:
- No true "owner" - they're publicly traded or private equity
- Local managers rarely have public contact info
- LinkedIn is best bet for GM names
REALITY: Accept that many corporate locations have no reachable decision-maker.""",
        max_stages=3,  # Fewer stages - not worth spending money
        min_confidence=50
    ),

    BusinessType.UNKNOWN: Strategy(
        name="Adaptive Discovery",
        tools_priority=["google_maps_lookup", "website_contacts", "serper_osint"],
        target_titles=["Owner", "Manager", "Director", "President"],
        system_prompt_addon="""
TARGET: Find whoever runs this business.
ADAPTIVE: Start with SMB strategy. If you discover it's a franchise or corporate chain,
adjust your approach accordingly.""",
        max_stages=4,
        min_confidence=60
    )
}


# Franchise/chain keywords for classification
FRANCHISE_KEYWORDS = {
    # Fast food
    "mcdonald's", "burger king", "wendy's", "taco bell", "kfc", "chick-fil-a",
    "subway", "dunkin'", "dunkin", "starbucks", "chipotle", "popeyes",
    "sonic", "arby's", "jack in the box", "carl's jr", "hardee's", "checkers",
    "five guys", "jimmy john's", "jersey mike's", "firehouse subs", "wingstop",
    "zaxby's", "culver's", "whataburger", "in-n-out", "del taco", "panda express",
    # Auto
    "jiffy lube", "midas", "firestone", "goodyear", "valvoline", "meineke",
    "maaco", "gerber collision", "service king", "grease monkey", "oil changers",
    "take 5", "express oil", "car wash",
    # Fitness
    "planet fitness", "anytime fitness", "orangetheory", "f45", "gold's gym",
    "la fitness", "crunch fitness", "snap fitness", "9 round", "burn boot camp",
    # Hotels
    "marriott", "hilton", "hyatt", "ihg", "wyndham", "best western", "holiday inn",
    "hampton inn", "courtyard", "fairfield", "residence inn", "comfort inn",
    # Retail
    "walmart", "target", "costco", "sam's club", "home depot", "lowe's",
    "ace hardware", "true value", "7-eleven", "circle k", "speedway",
    # Services
    "h&r block", "liberty tax", "great clips", "supercuts", "sport clips",
    "fantastic sams", "massage envy", "european wax", "servpro", "molly maid",
    "merry maids", "the ups store", "fedex office", "staples", "office depot",
    # Real estate
    "century 21", "re/max", "coldwell banker", "keller williams", "sotheby's",
    # Healthcare
    "davita", "fresenius", "concentra", "minute clinic", "urgent care",
}

HEALTHCARE_KEYWORDS = {
    "medical", "health", "clinic", "hospital", "doctor", "physician", "dental",
    "dentist", "optometry", "optometrist", "chiropractic", "chiropractor",
    "physical therapy", "pt", "dialysis", "kidney", "cancer", "oncology",
    "cardiology", "dermatology", "pediatric", "ob/gyn", "obgyn", "women's health",
    "mental health", "psychiatry", "psychology", "therapy", "counseling",
    "urgent care", "emergency", "surgery", "surgical", "orthopedic",
    "nursing home", "assisted living", "rehabilitation", "rehab",
    "pharmacy", "laboratory", "lab", "imaging", "radiology", "mri",
    "iu health", "ascension", "hca", "community health",
}

CORPORATE_KEYWORDS = {
    # Big box retail
    "walmart", "target", "costco", "sam's club", "bj's", "kroger", "publix",
    "safeway", "albertsons", "whole foods", "trader joe's", "aldi", "lidl",
    # Department stores
    "macy's", "nordstrom", "jcpenney", "kohl's", "dillard's", "sears",
    # Electronics
    "best buy", "apple store", "microsoft store", "gamestop",
    # Home improvement
    "home depot", "lowe's", "menards",
    # Banks
    "bank of america", "chase", "wells fargo", "citibank", "us bank", "pnc",
    "td bank", "capital one", "fifth third", "regions", "truist",
}


def classify_business_type(
    company_name: str,
    category: str | None = None,
    city: str | None = None
) -> BusinessType:
    """
    Classify a business into a type based on name and category.
    Uses keyword matching for speed (no LLM call needed).
    """
    name_lower = company_name.lower()
    cat_lower = (category or "").lower()
    combined = f"{name_lower} {cat_lower}"

    # Check for franchise keywords first
    for keyword in FRANCHISE_KEYWORDS:
        if keyword in combined:
            return BusinessType.FRANCHISE

    # Check for corporate keywords
    for keyword in CORPORATE_KEYWORDS:
        if keyword in combined:
            return BusinessType.CORPORATE

    # Check for healthcare keywords
    for keyword in HEALTHCARE_KEYWORDS:
        if keyword in combined:
            return BusinessType.HEALTHCARE

    # Default to SMB if no signals - most businesses are SMBs
    return BusinessType.SMB


@dataclass
class ToolResult:
    """Result from a tool execution"""
    tool_name: str
    success: bool
    data: dict
    cost: float = 0.0


@dataclass
class ControllerState:
    """State maintained during agent loop"""
    company_name: str
    domain: str | None = None
    city: str | None = None
    state: str | None = None
    category: str | None = None

    # Business type and strategy
    business_type: BusinessType = BusinessType.UNKNOWN
    strategy: Strategy | None = None
    strategy_pivoted: bool = False

    # Accumulated data
    candidates: list[dict] = field(default_factory=list)
    tool_results: dict[str, ToolResult] = field(default_factory=dict)

    # Tracking
    stage: int = 0
    total_cost: float = 0.0

    def to_context(self) -> str:
        """Convert state to context string for LLM"""
        lines = [
            f"Company: {self.company_name}",
            f"Business Type: {self.business_type.value}",
            f"Domain: {self.domain or 'Unknown'}",
            f"Location: {self.city}, {self.state}" if self.city and self.state else "",
            f"Category: {self.category or 'Unknown'}",
        ]

        if self.strategy:
            lines.append(f"\nTarget Titles: {', '.join(self.strategy.target_titles)}")

        lines.append("\nDiscovered so far:")

        for tool_name, result in self.tool_results.items():
            if result.success:
                lines.append(f"\n[{tool_name}] Success:")
                for key, value in result.data.items():
                    if value:
                        lines.append(f"  - {key}: {value}")
            else:
                lines.append(f"\n[{tool_name}] Failed or no data")

        if self.candidates:
            lines.append(f"\nCandidates ({len(self.candidates)}):")
            for i, c in enumerate(self.candidates[:3], 1):
                name = c.get("name", "Unknown")
                title = c.get("title", "")
                email = c.get("email", "None")
                phone = c.get("phone", "None")
                sources = ", ".join(c.get("sources", []))
                lines.append(f"  {i}. {name} ({title}) | email: {email} | phone: {phone} | sources: {sources}")
        else:
            lines.append("\nNo candidates found yet.")

        return "\n".join(lines)


# Base tool definitions (available to all strategies)
BASE_TOOLS = [
    {
        "name": "google_maps_lookup",
        "description": "Search Google Maps for the business. Returns owner name, phone, email, address, reviews. Cost: $0.002. Best for SMBs.",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Search query (company name + city)"}
            },
            "required": ["query"]
        }
    },
    {
        "name": "website_contacts",
        "description": "Scrape the company website for contact info (emails, phones, social links). Cost: $0.002.",
        "parameters": {
            "type": "object",
            "properties": {
                "domain": {"type": "string", "description": "Company domain to scrape"}
            },
            "required": ["domain"]
        }
    },
    {
        "name": "serper_osint",
        "description": "Search the web for owner/contact information. Cost: $0.001. Use for finding owner names, news articles about the business.",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Search query for finding contact info"}
            },
            "required": ["query"]
        }
    },
    {
        "name": "data_fill",
        "description": "Fill missing data (domain, phone) using web search. Cost: $0.001.",
        "parameters": {
            "type": "object",
            "properties": {
                "company_name": {"type": "string", "description": "Company name"}
            },
            "required": ["company_name"]
        }
    },
]

# Strategy-specific tools
LINKEDIN_TOOL = {
    "name": "linkedin_search",
    "description": "Search LinkedIn for employees at this company with target titles (Owner, Manager, etc). Cost: $0.05. Best for franchises and corporate locations.",
    "parameters": {
        "type": "object",
        "properties": {
            "company_name": {"type": "string", "description": "Company name to search"},
            "title_keywords": {"type": "string", "description": "Title keywords like 'owner OR manager'"}
        },
        "required": ["company_name"]
    }
}

NPI_TOOL = {
    "name": "npi_lookup",
    "description": "Search NPI registry for healthcare providers. Cost: FREE. Returns practitioner name, specialty, practice info.",
    "parameters": {
        "type": "object",
        "properties": {
            "name_or_org": {"type": "string", "description": "Provider or organization name"},
            "city": {"type": "string", "description": "City"},
            "state": {"type": "string", "description": "State code (2 letter)"}
        },
        "required": ["name_or_org"]
    }
}

# Finish tools (same for all)
FINISH_TOOLS = [
    {
        "name": "finish_with_contact",
        "description": "Accept the best candidate and finish.",
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
        "description": "Give up - no valid contact found.",
        "parameters": {
            "type": "object",
            "properties": {
                "reason": {"type": "string", "description": "Why no contact was found"}
            },
            "required": ["reason"]
        }
    },
    {
        "name": "pivot_strategy",
        "description": "Switch to a different strategy if current approach isn't working. Use when you discover the business type is different than initially classified.",
        "parameters": {
            "type": "object",
            "properties": {
                "new_type": {
                    "type": "string",
                    "enum": ["smb", "franchise", "healthcare", "corporate"],
                    "description": "New business type to use"
                },
                "reason": {"type": "string", "description": "Why switching strategies"}
            },
            "required": ["new_type", "reason"]
        }
    }
]


def get_tools_for_strategy(strategy: Strategy) -> list[dict]:
    """Get tool definitions for a strategy"""
    tools = []

    for tool_name in strategy.tools_priority:
        if tool_name == "linkedin_search":
            tools.append(LINKEDIN_TOOL)
        elif tool_name == "npi_lookup":
            tools.append(NPI_TOOL)
        else:
            # Find in base tools
            for base_tool in BASE_TOOLS:
                if base_tool["name"] == tool_name:
                    tools.append(base_tool)
                    break

    return tools + FINISH_TOOLS


CONTROLLER_SYSTEM = """You are an adaptive business contact discovery agent. Your job is to find the right decision-maker efficiently.

GOAL: Find a REAL PERSON name (first + last) who is the decision-maker, with their phone and/or email.

{strategy_addon}

CRITICAL RULES:
- Company names are NOT valid contacts: "Nickel Bros" is NOT a person
- Real person names look like: "John Smith", "Maria Garcia", "Kirk R. Wainwright"
- Verify the title matches what we're looking for (see Target Titles above)
- If you discover the business is a different type than classified, use pivot_strategy

COST AWARENESS:
- Stay within budget, prioritize cheaper tools first
- Don't call tools that are unlikely to help for this business type

WHEN TO FINISH:
- FINISH if: Real person name + title match + contact method → high confidence
- PIVOT if: Current strategy isn't working and you have evidence of different business type
- GIVE UP if: 3+ tools tried with no valid contact found, OR it's a corporate location with no reachable decision-maker

You must respond with a function call to one of the available tools."""


class AdaptiveController:
    """Adaptive agent loop controller with strategy selection"""

    def __init__(
        self,
        llm_provider: LLMProvider,
        tools: dict[str, Callable[..., Awaitable[ToolResult]]],
        cost_budget: float = 0.02
    ):
        self.llm = llm_provider
        self.tools = tools
        self.cost_budget = cost_budget

        # Stats
        self.total_by_type = {t: 0 for t in BusinessType}
        self.success_by_type = {t: 0 for t in BusinessType}
        self.pivots = 0
        self.early_exits = 0

    async def process_company(
        self,
        company_name: str,
        domain: str | None = None,
        city: str | None = None,
        state_code: str | None = None,
        category: str | None = None
    ) -> dict:
        """Process a single company with adaptive strategy selection"""

        # Step 1: Classify business type
        business_type = classify_business_type(company_name, category, city)
        strategy = STRATEGIES[business_type]

        self.total_by_type[business_type] += 1
        logger.info(f"Classified '{company_name}' as {business_type.value}")

        # Initialize state
        state = ControllerState(
            company_name=company_name,
            domain=domain,
            city=city,
            state=state_code,
            category=category,
            business_type=business_type,
            strategy=strategy
        )

        # Step 2: Run agent loop with selected strategy
        while state.stage < strategy.max_stages:
            remaining_budget = self.cost_budget - state.total_cost
            if remaining_budget <= 0:
                break

            action = await self._get_next_action(state, remaining_budget)

            # Handle finish actions
            if action.get("tool") == "finish_with_contact":
                params = action.get("params", {})
                confidence = params.get("confidence", 0)
                if confidence >= strategy.min_confidence:
                    self.early_exits += 1
                    self.success_by_type[business_type] += 1
                    return self._build_result(state, params, confidence, action.get("reason", ""))

            elif action.get("tool") == "finish_no_contact":
                return self._build_result(state, None, 0, action.get("params", {}).get("reason", ""))

            elif action.get("tool") == "pivot_strategy":
                # Switch to a different strategy
                new_type_str = action.get("params", {}).get("new_type", "smb")
                new_type = BusinessType(new_type_str)
                if new_type != business_type and not state.strategy_pivoted:
                    logger.info(f"Pivoting from {business_type.value} to {new_type.value}")
                    state.business_type = new_type
                    state.strategy = STRATEGIES[new_type]
                    state.strategy_pivoted = True
                    self.pivots += 1

            elif action.get("tool") in self.tools:
                # Call the tool
                tool_name = action["tool"]
                try:
                    result = await self._call_tool(tool_name, state, action.get("params", {}))
                    state.tool_results[tool_name] = result
                    state.total_cost += result.cost
                    self._update_candidates(state, tool_name, result)
                except Exception as e:
                    logger.warning(f"Tool {tool_name} failed: {e}")
                    state.tool_results[tool_name] = ToolResult(
                        tool_name=tool_name,
                        success=False,
                        data={"error": str(e)}
                    )

            state.stage += 1

        # Max stages reached - return best candidate if any
        if state.candidates:
            best = state.candidates[0]
            return self._build_result(state, best, 50, "Max stages reached, returning best candidate")

        return self._build_result(state, None, 0, "Max stages reached, no candidates found")

    async def _get_next_action(self, state: ControllerState, remaining_budget: float) -> dict:
        """Ask LLM what to do next"""
        context = state.to_context()
        tools_called = list(state.tool_results.keys()) or ["none yet"]
        strategy = state.strategy

        # Get tools for current strategy
        tools = get_tools_for_strategy(strategy)

        system_prompt = CONTROLLER_SYSTEM.format(
            strategy_addon=strategy.system_prompt_addon
        )

        prompt = f"""Current state:
{context}

Tools already called: {', '.join(tools_called)}
Remaining budget: ${remaining_budget:.4f}
Stages used: {state.stage}/{strategy.max_stages}

What should we do next? Call a tool or finish."""

        try:
            response = await self.llm.complete_json(
                prompt=prompt + "\n\nRespond with JSON: {\"tool\": \"tool_name\", \"params\": {...}, \"reason\": \"...\"}",
                system=system_prompt + "\n\nAvailable tools:\n" + json.dumps(tools, indent=2),
                temperature=0.1,
                max_tokens=400
            )
            return response
        except Exception as e:
            logger.error(f"LLM decision failed: {e}")
            # Fallback: call first tool in priority if not done
            for tool_name in strategy.tools_priority:
                if tool_name not in state.tool_results and tool_name in self.tools:
                    return {"tool": tool_name, "reason": f"Fallback after LLM error: {e}"}
            return {"tool": "finish_no_contact", "params": {"reason": f"LLM error: {e}"}}

    async def _call_tool(self, tool_name: str, state: ControllerState, params: dict) -> ToolResult:
        """Execute a tool"""
        tool_fn = self.tools.get(tool_name)
        if not tool_fn:
            raise ValueError(f"Unknown tool: {tool_name}")

        # Build arguments based on tool
        if tool_name == "google_maps_lookup":
            query = params.get("query") or f"{state.company_name} {state.city or ''} {state.state or ''}".strip()
            return await tool_fn(query=query)

        elif tool_name == "website_contacts":
            domain = params.get("domain") or state.domain
            if not domain:
                return ToolResult(tool_name=tool_name, success=False, data={"error": "No domain"})
            return await tool_fn(domain=domain)

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

        elif tool_name == "linkedin_search":
            return await tool_fn(
                company_name=params.get("company_name") or state.company_name,
                title_keywords=params.get("title_keywords") or " OR ".join(state.strategy.target_titles[:3])
            )

        elif tool_name == "npi_lookup":
            return await tool_fn(
                name_or_org=params.get("name_or_org") or state.company_name,
                city=params.get("city") or state.city,
                state=params.get("state") or state.state
            )

        else:
            raise ValueError(f"Unknown tool: {tool_name}")

    def _update_candidates(self, state: ControllerState, tool_name: str, result: ToolResult):
        """Update candidate list from tool result"""
        if not result.success:
            return

        data = result.data

        if tool_name == "google_maps_lookup":
            if data.get("owner_name"):
                state.candidates.append({
                    "name": data["owner_name"],
                    "title": "Owner",
                    "phone": data.get("phone"),
                    "email": data.get("email"),
                    "sources": ["google_maps"]
                })
            if data.get("domain") and not state.domain:
                state.domain = data["domain"]

        elif tool_name == "website_contacts":
            if data.get("emails"):
                for email in data["emails"][:2]:
                    state.candidates.append({
                        "email": email,
                        "phone": data.get("phone"),
                        "sources": ["website"]
                    })

        elif tool_name == "serper_osint":
            if data.get("owner_name"):
                state.candidates.append({
                    "name": data["owner_name"],
                    "title": data.get("title", "Owner"),
                    "sources": ["serper"]
                })

        elif tool_name == "linkedin_search":
            for person in data.get("people", [])[:3]:
                state.candidates.append({
                    "name": person.get("name"),
                    "title": person.get("title"),
                    "linkedin_url": person.get("url"),
                    "sources": ["linkedin"]
                })

        elif tool_name == "npi_lookup":
            if data.get("provider_name"):
                state.candidates.append({
                    "name": data["provider_name"],
                    "title": data.get("specialty", "Healthcare Provider"),
                    "phone": data.get("phone"),
                    "sources": ["npi_registry"]
                })

    def _build_result(self, state: ControllerState, contact: dict | None, confidence: float, reason: str) -> dict:
        """Build final result"""
        result = {
            "company_name": state.company_name,
            "domain": state.domain,
            "business_type": state.business_type.value,
            "strategy_used": state.strategy.name if state.strategy else "Unknown",
            "strategy_pivoted": state.strategy_pivoted,
            "stages_completed": list(state.tool_results.keys()),
            "total_cost": state.total_cost,
            "candidates": state.candidates,
        }

        if contact:
            result["contact"] = {
                "name": contact.get("name"),
                "email": contact.get("email"),
                "phone": contact.get("phone"),
                "title": contact.get("title", "Owner"),
                "confidence": confidence,
                "validation_reason": reason
            }
        else:
            result["contact"] = None
            result["no_contact_reason"] = reason

        return result

    def get_stats(self) -> dict:
        """Get controller statistics"""
        return {
            "total_by_type": {t.value: c for t, c in self.total_by_type.items()},
            "success_by_type": {t.value: c for t, c in self.success_by_type.items()},
            "success_rate_by_type": {
                t.value: self.success_by_type[t] / max(1, self.total_by_type[t])
                for t in BusinessType
            },
            "pivots": self.pivots,
            "early_exits": self.early_exits
        }
