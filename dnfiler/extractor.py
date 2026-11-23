"""Send a scanned PDF to Claude and get back the delivery note details."""
from __future__ import annotations

import base64
import json
from dataclasses import dataclass
from pathlib import Path

import anthropic

SCHEMA = {
    "type": "object",
    "properties": {
        "documents": {
            "type": "array",
            "description": "One entry per separate document found in the PDF, in page order.",
            "items": {
                "type": "object",
                "properties": {
                    "is_delivery_note": {"type": "boolean"},
                    "page_start": {"type": "integer", "description": "1-based first page"},
                    "page_end": {"type": "integer", "description": "1-based last page (inclusive)"},
                    "dn_number": {"type": "string", "description": "Delivery note / DO number, or empty"},
                    "date": {"type": "string", "description": "Delivery note date as YYYY-MM-DD, or empty"},
                    "date_as_printed": {"type": "string"},
                    "customer_name": {"type": "string", "description": "Customer exactly as printed, or empty"},
                    "matched_known_customer": {
                        "type": "string",
                        "description": "Exact name from the known customer list if it is the same company, else empty",
                    },
                    "confidence": {"type": "string", "enum": ["high", "medium", "low"]},
                    "notes": {"type": "string", "description": "Anything unclear, in one short sentence"},
                },
                "required": [
                    "is_delivery_note", "page_start", "page_end", "dn_number", "date",
                    "date_as_printed", "customer_name", "matched_known_customer", "confidence", "notes",
                ],
                "additionalProperties": False,
            },
        }
    },
    "required": ["documents"],
    "additionalProperties": False,
}

SYSTEM = """You read scanned delivery notes (also called DO / delivery orders) for a filing system.
Layouts vary because they come from different templates. For each PDF, return the documents it contains.

Rules:
- A PDF can hold one delivery note or several scanned together. Give each its page range.
  A delivery note that runs over several pages is one document.
- date: the delivery note's own date (not a PO date, due date, or print timestamp). Output YYYY-MM-DD.
  Printed dates are in {date_order_words} order unless the month is written as a word.
- customer_name: the company the goods are delivered to / billed to (labels such as "Deliver To",
  "Ship To", "Customer", "Bill To", "Sold To", "M/s"). Never the company that issued the note.
  {own_company_rule}
- matched_known_customer: if the customer is the same company as one in the known list (ignore
  differences such as "Sdn. Bhd." vs "Sdn Bhd", capitals, punctuation, or a branch name), copy that list
  entry exactly. Otherwise leave it empty. Do not match different companies with similar names.
- If a value cannot be read, leave it empty and lower the confidence. Never guess a date or a customer.
- confidence: high only if the date and customer are both clearly printed and unambiguous."""


class ExtractionError(Exception):
    """Worth retrying later.

    file_specific=False means the problem is not this file (internet down, bad API key, rate limit):
    the file waits in the inbox and the attempt is not counted against it.
    """

    def __init__(self, message: str, file_specific: bool = False):
        super().__init__(message)
        self.file_specific = file_specific


class ExtractionRefused(Exception):
    """The model declined. Not worth retrying; send the file to review."""


@dataclass
class DocumentInfo:
    is_delivery_note: bool
    page_start: int
    page_end: int
    dn_number: str
    date: str
    date_as_printed: str
    customer_name: str
    matched_known_customer: str
    confidence: str
    notes: str
    customer_reg: str = ""  # company reg. no.; only the BHPetrol reader fills it


class ClaudeExtractor:
    def __init__(self, model: str, date_order: str, own_company_names: list[str]):
        self.client = anthropic.Anthropic(max_retries=3)
        self.model = model
        words = {"DMY": "day/month/year", "MDY": "month/day/year", "YMD": "year/month/day"}
        own_rule = (
            "These names are the issuing company and are never the customer: "
            + ", ".join(own_company_names) + "."
            if own_company_names else ""
        )
        self.system = SYSTEM.format(date_order_words=words.get(date_order, date_order), own_company_rule=own_rule)

    def extract(self, pdf_path: Path, known_customers: list[str]) -> list[DocumentInfo]:
        data = base64.standard_b64encode(pdf_path.read_bytes()).decode("ascii")
        known = "\n".join(f"- {name}" for name in sorted(known_customers)) or "(none yet)"
        try:
            response = self.client.beta.messages.create(
                model=self.model,
                max_tokens=16000,
                betas=["server-side-fallback-2026-07-01"],
                fallbacks="default",
                system=self.system,
                output_config={
                    "effort": "medium",
                    "format": {"type": "json_schema", "schema": SCHEMA},
                },
                messages=[{
                    "role": "user",
                    "content": [
                        {"type": "document", "source": {"type": "base64", "media_type": "application/pdf", "data": data}},
                        {"type": "text", "text": f"Known customers:\n{known}\n\nRead this scanned PDF."},
                    ],
                }],
            )
        except (anthropic.AuthenticationError, anthropic.PermissionDeniedError) as e:
            raise ExtractionError(f"API key problem: {e.message}") from e
        except anthropic.BadRequestError as e:
            # e.g. corrupt or oversized PDF: retrying won't help
            raise ExtractionRefused(f"API rejected the file: {e.message}") from e
        except anthropic.RateLimitError as e:
            raise ExtractionError("Rate limited by the API") from e
        except anthropic.APIStatusError as e:
            raise ExtractionError(f"API error {e.status_code}: {e.message}") from e
        except anthropic.APIConnectionError as e:
            raise ExtractionError("No connection to the API (internet down?)") from e

        if response.stop_reason == "refusal":
            raise ExtractionRefused("The model declined to read this file")
        if response.stop_reason == "max_tokens":
            raise ExtractionError("Response was cut off", file_specific=True)
        text = next((b.text for b in response.content if b.type == "text"), "")
        try:
            docs = json.loads(text)["documents"]
            return [DocumentInfo(**d) for d in docs]
        except (ValueError, KeyError, TypeError) as e:
            raise ExtractionError(f"Could not parse the response: {e}", file_specific=True) from e
