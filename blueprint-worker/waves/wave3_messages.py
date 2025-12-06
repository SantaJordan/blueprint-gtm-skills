"""
Wave 3: Message Generation + Buyer Critique

Generates PQS and PVP messages for validated segments,
then critiques them from the buyer's perspective.
"""
from typing import Dict, List
import re


class Wave3Messages:
    """Wave 3: Generate and validate messages for each segment."""

    PQS_PROMPT = """Generate a PQS (Pain-Qualified Segment) message for this segment.

SEGMENT: {segment_name}
DESCRIPTION: {segment_description}
DATA SOURCES: {data_sources}
FIELDS: {fields}

TARGET PERSONA: {persona_title}
COMPANY OFFERING: {offering}

PQS MESSAGE FORMAT:
- Subject: 2-4 words only
- Intro: Exact data mirror with specific record numbers, dates, facility names
- Insight: Non-obvious synthesis the persona doesn't already know
- Question: Low-effort question to spark reply
- Length: Under 75 words total

REQUIREMENTS:
- Use SPECIFIC data from the fields listed (not generic placeholders like [X])
- Include record numbers, dates, addresses where applicable
- Every claim must be PROVABLE (trace to specific field)
- Mirror their EXACT situation, don't pitch anything

Generate 2 PQS message variants:

PQS_VARIANT_1:
Subject: [subject]
Body: [full message]

PQS_VARIANT_2:
Subject: [subject]
Body: [full message]"""

    PVP_PROMPT = """Generate a PVP (Permissionless Value Proposition) message for this segment.

SEGMENT: {segment_name}
DESCRIPTION: {segment_description}
DATA SOURCES: {data_sources}
FIELDS: {fields}

TARGET PERSONA: {persona_title}
COMPANY OFFERING: {offering}

PVP MESSAGE FORMAT:
- Subject: Specific value being offered (not a pitch)
- Intro: What you're giving them RIGHT NOW (specific, concrete)
- Insight: Why this matters to them specifically
- Question: Who should receive this? (route to right person)
- Length: Under 100 words total

PVP REQUIREMENTS:
- Must deliver IMMEDIATE usable value (no meeting required)
- Analysis already done, deadlines already pulled, patterns already identified
- Recipient can take action WITHOUT replying
- Include specific numbers, dates, benchmarks

Generate 2 PVP message variants:

PVP_VARIANT_1:
Subject: [subject]
Body: [full message]

PVP_VARIANT_2:
Subject: [subject]
Body: [full message]"""

    CRITIQUE_PROMPT = """Adopt this buyer persona and brutally critique these messages.

PERSONA: {persona_title}
RESPONSIBILITIES: {persona_responsibilities}
KPIs: {persona_kpis}

"I am now {persona_title}. I receive 50+ sales emails per day. I delete 95% without reading.
I only respond to emails that:
1. Mirror an exact situation I'm in RIGHT NOW
2. Contain data I can verify and don't already have
3. Offer a non-obvious insight I haven't considered
4. Require minimal effort to reply

I am NOT a marketer evaluating this message. I AM THE BUYER. Would I reply to this?
If 'maybe'—that's a NO."

MESSAGES TO CRITIQUE:
{messages}

Score each message (0-10 on 5 criteria):
1. Situation Recognition: Does this mirror my EXACT current situation? Generic=0, Hyper-specific=10
2. Data Credibility: Can I verify this data? Is it from trusted source? Assumed=0, Provable=10
3. Insight Value: Is this non-obvious synthesis I don't already know? Obvious=0, Revelation=10
4. Effort to Reply: How easy to respond? High friction=0, One-word answer=10
5. Emotional Resonance: Does this trigger urgency or curiosity? Meh=0, Must investigate=10

Then apply Texada Test for each:
- Hyper-specific: Contains dates, record numbers, specific values? (not "recent", "many", "some")
- Factually grounded: Every claim traces to documented data source?
- Non-obvious synthesis: Insight persona doesn't already have access to?

Output format for EACH message:
MESSAGE: [which one]
SCORES:
- Situation Recognition: [0-10]
- Data Credibility: [0-10]
- Insight Value: [0-10]
- Effort to Reply: [0-10]
- Emotional Resonance: [0-10]
AVERAGE: [calculated average]
TEXADA: [PASS/FAIL for each criterion]
VERDICT: KEEP (≥7.5) / REVISE (6.0-7.4) / DESTROY (<6.0)
FEEDBACK: [what would make me reply]"""

    def __init__(self, claude_client):
        self.claude = claude_client

    async def generate(self, segments: List[Dict], company_context: Dict) -> List[Dict]:
        """
        Generate and critique messages for all segments.

        Args:
            segments: Validated segments from Hard Gates
            company_context: Context from Wave 1

        Returns:
            List of messages with scores, sorted by quality
        """
        all_messages = []

        for segment in segments[:2]:  # Top 2 segments
            # Generate PQS messages
            pqs_messages = await self._generate_pqs(segment, company_context)

            # Generate PVP messages
            pvp_messages = await self._generate_pvp(segment, company_context)

            # Critique all messages
            critiques = await self._critique_messages(
                pqs_messages + pvp_messages,
                company_context
            )

            # Combine messages with critiques
            for i, msg in enumerate(pqs_messages + pvp_messages):
                if i < len(critiques):
                    msg["critique"] = critiques[i]
                    msg["segment"] = segment["name"]
                    msg["type"] = "PQS" if i < len(pqs_messages) else "PVP"
                    all_messages.append(msg)

        # Filter to keep only messages scoring ≥7.0
        passing_messages = [
            m for m in all_messages
            if m.get("critique", {}).get("average", 0) >= 7.0
        ]

        # Sort by score
        passing_messages.sort(
            key=lambda m: m.get("critique", {}).get("average", 0),
            reverse=True
        )

        return passing_messages

    async def _generate_pqs(self, segment: Dict, context: Dict) -> List[Dict]:
        """Generate PQS messages for a segment."""
        prompt = self.PQS_PROMPT.format(
            segment_name=segment.get("name", ""),
            segment_description=segment.get("description", ""),
            data_sources=", ".join(segment.get("data_sources", [])),
            fields=", ".join(segment.get("fields", [])),
            persona_title=context.get("persona_title", ""),
            offering=context.get("offering", "")
        )

        response = await self.claude.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=2048,
            messages=[{"role": "user", "content": prompt}]
        )

        return self._parse_messages(response.content[0].text, "PQS")

    async def _generate_pvp(self, segment: Dict, context: Dict) -> List[Dict]:
        """Generate PVP messages for a segment."""
        prompt = self.PVP_PROMPT.format(
            segment_name=segment.get("name", ""),
            segment_description=segment.get("description", ""),
            data_sources=", ".join(segment.get("data_sources", [])),
            fields=", ".join(segment.get("fields", [])),
            persona_title=context.get("persona_title", ""),
            offering=context.get("offering", "")
        )

        response = await self.claude.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=2048,
            messages=[{"role": "user", "content": prompt}]
        )

        return self._parse_messages(response.content[0].text, "PVP")

    async def _critique_messages(self, messages: List[Dict], context: Dict) -> List[Dict]:
        """Critique all messages from buyer perspective."""
        messages_text = ""
        for i, msg in enumerate(messages, 1):
            messages_text += f"\nMESSAGE {i} ({msg.get('type', 'Unknown')}):\n"
            messages_text += f"Subject: {msg.get('subject', '')}\n"
            messages_text += f"Body: {msg.get('body', '')}\n"

        prompt = self.CRITIQUE_PROMPT.format(
            persona_title=context.get("persona_title", "Decision Maker"),
            persona_responsibilities=context.get("persona", ""),
            persona_kpis=", ".join(context.get("persona_kpis", [])),
            messages=messages_text
        )

        response = await self.claude.messages.create(
            model="claude-opus-4-20250514",  # Use Opus for quality judgment
            max_tokens=4096,
            messages=[{"role": "user", "content": prompt}]
        )

        return self._parse_critiques(response.content[0].text, len(messages))

    def _parse_messages(self, text: str, msg_type: str) -> List[Dict]:
        """Parse generated messages from response."""
        messages = []

        # Find message variants
        pattern = rf'{msg_type}_VARIANT_(\d+)[:\s]+(.+?)(?={msg_type}_VARIANT_|$)'
        matches = re.findall(pattern, text, re.DOTALL | re.IGNORECASE)

        for _, content in matches:
            msg = {"type": msg_type, "subject": "", "body": ""}

            # Extract subject
            subject_match = re.search(r'Subject[:\s]+(.+?)(?=\n|Body|$)', content)
            if subject_match:
                msg["subject"] = subject_match.group(1).strip()

            # Extract body
            body_match = re.search(r'Body[:\s]+(.+?)$', content, re.DOTALL)
            if body_match:
                msg["body"] = body_match.group(1).strip()

            if msg["subject"] or msg["body"]:
                messages.append(msg)

        return messages

    def _parse_critiques(self, text: str, expected_count: int) -> List[Dict]:
        """Parse critique results for each message."""
        critiques = []

        # Split by MESSAGE blocks
        message_blocks = re.split(r'MESSAGE[:\s]*\d*', text, flags=re.IGNORECASE)

        for block in message_blocks[1:expected_count + 1]:  # Skip first empty split
            critique = {
                "scores": {
                    "situation_recognition": 0,
                    "data_credibility": 0,
                    "insight_value": 0,
                    "effort_to_reply": 0,
                    "emotional_resonance": 0
                },
                "average": 0,
                "texada": {
                    "hyper_specific": False,
                    "factually_grounded": False,
                    "non_obvious": False
                },
                "verdict": "DESTROY",
                "feedback": ""
            }

            # Parse scores
            score_patterns = {
                "situation_recognition": r"Situation Recognition[:\s]+(\d+)",
                "data_credibility": r"Data Credibility[:\s]+(\d+)",
                "insight_value": r"Insight Value[:\s]+(\d+)",
                "effort_to_reply": r"Effort to Reply[:\s]+(\d+)",
                "emotional_resonance": r"Emotional Resonance[:\s]+(\d+)"
            }

            total = 0
            for key, pattern in score_patterns.items():
                match = re.search(pattern, block, re.IGNORECASE)
                if match:
                    score = min(10, max(0, int(match.group(1))))
                    critique["scores"][key] = score
                    total += score

            critique["average"] = total / 5 if total > 0 else 0

            # Parse average if explicitly stated
            avg_match = re.search(r"AVERAGE[:\s]+(\d+(?:\.\d+)?)", block, re.IGNORECASE)
            if avg_match:
                critique["average"] = float(avg_match.group(1))

            # Parse Texada
            texada_match = re.search(r"TEXADA[:\s]+(.+?)(?=VERDICT|FEEDBACK|$)", block, re.DOTALL | re.IGNORECASE)
            if texada_match:
                texada_text = texada_match.group(1).lower()
                critique["texada"]["hyper_specific"] = "pass" in texada_text and "specific" in texada_text
                critique["texada"]["factually_grounded"] = "pass" in texada_text and "grounded" in texada_text
                critique["texada"]["non_obvious"] = "pass" in texada_text and "obvious" in texada_text

            # Parse verdict
            verdict_match = re.search(r"VERDICT[:\s]+(KEEP|REVISE|DESTROY)", block, re.IGNORECASE)
            if verdict_match:
                critique["verdict"] = verdict_match.group(1).upper()

            # Parse feedback
            feedback_match = re.search(r"FEEDBACK[:\s]+(.+?)$", block, re.DOTALL)
            if feedback_match:
                critique["feedback"] = feedback_match.group(1).strip()[:300]

            critiques.append(critique)

        return critiques
