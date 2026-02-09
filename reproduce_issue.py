
import json
import re
import sys
import os

# Mock utils
def get_section_slug(section_name):
    return section_name.lower().replace(" ", "_").replace("&", "and")

# Mock functions from playbook_utils.py (copy-pasted for isolation)
def parse_playbook_line(line):
    pattern = r'\[([^\]]+)\]\s*helpful=(\d+)\s*harmful=(\d+)\s*::\s*(.*)'
    match = re.match(pattern, line.strip())
    if match:
        return {
            'id': match.group(1),
            'helpful': int(match.group(2)),
            'harmful': int(match.group(3)),
            'content': match.group(4),
            'raw_line': line
        }
    return None

def format_playbook_line(bullet_id, helpful, harmful, content):
    return f"[{bullet_id}] helpful={helpful} harmful={harmful} :: {content}"

def apply_curator_operations(playbook_text, operations, next_id):
    lines = playbook_text.strip().split('\n')
    sections = {}
    current_section = "general"
    
    for i, line in enumerate(lines):
        if line.strip().startswith('##'):
            section_header = line.strip()[2:].strip()
            current_section = section_header.lower().replace(' ', '_').replace('&', 'and')
            if current_section not in sections:
                sections[current_section] = []
        elif line.strip():
            sections[current_section].append((i, line))
    
    bullets_to_add = []
    
    for op in operations:
        op_type = op['type']
        if op_type == 'ADD':
            section_raw = op.get('section', 'general')
            section = section_raw.lower().replace(' ', '_').replace('&', 'and')
            
            if section not in sections and section != 'general':
                print(f"Warning: Section '{section_raw}' not found, adding to OTHERS")
                section = 'others'
            
            slug = get_section_slug(section)
            new_id = f"{slug}-{next_id:05d}"
            next_id += 1
            
            content = op.get('content', '')
            new_line = format_playbook_line(new_id, 0, 0, content)
            bullets_to_add.append((section, new_line))
            print(f"  Added bullet {new_id} to section {section}")

    new_lines = []
    for line in lines:
        new_lines.append(line)
    
    final_lines = []
    current_section = None
    
    for line in new_lines:
        if line.strip().startswith('##'):
            if current_section:
                section_adds = [b for s, b in bullets_to_add if s == current_section]
                final_lines.extend(section_adds)
                bullets_to_add = [(s, b) for s, b in bullets_to_add if s != current_section]
            
            section_header = line.strip()[2:].strip()
            current_section = section_header.lower().replace(' ', '_').replace('&', 'and')
        final_lines.append(line)
    
    if current_section:
        section_adds = [b for s, b in bullets_to_add if s == current_section]
        final_lines.extend(section_adds)
        bullets_to_add = [(s, b) for s, b in bullets_to_add if s != current_section]
    
    if bullets_to_add:
        print(f"Warning: {len(bullets_to_add)} bullets have no matching section, adding to OTHERS")
        others_bullets = [b for s, b in bullets_to_add]
        others_idx = -1
        for i, line in enumerate(final_lines):
            if line.strip() == "## OTHERS":
                others_idx = i
                break
        
        if others_idx >= 0:
            for i, bullet in enumerate(others_bullets):
                final_lines.insert(others_idx + 1 + i, bullet)
        else:
            final_lines.extend(others_bullets)
    
    return '\n'.join(final_lines), next_id

def extract_json_from_text(text, json_key=None):
    try:
        try:
            result = json.loads(text.strip())
            return result
        except json.JSONDecodeError:
            pass
        
        json_pattern = r'```json\s*(.*?)\s*```'
        matches = re.findall(json_pattern, text, re.DOTALL | re.IGNORECASE)
        
        if matches:
            for match in matches:
                try:
                    json_str = match.strip()
                    result = json.loads(json_str)
                    return result
                except json.JSONDecodeError:
                    continue
        
        return None 
    except Exception as e:
        print(f"Failed to extract JSON: {e}")
    return None

def _extract_and_validate_operations(response):
    operations_info = extract_json_from_text(response, "operations")
    if not operations_info:
        raise ValueError("Failed to extract valid JSON from curator response")
    if "operations" not in operations_info:
        raise ValueError("JSON missing required 'operations' field")
    return operations_info

# --- TEST DATA ---
response_text = """{
  "reasoning": "The model applied an overbroad heuristic (\\"Level 3 => fair value\\") that led to mis-mapping amounts presented in VIE/balance-note lines as DebtInstrumentFairValue instead of DebtInstrumentCarryingAmount. The playbook lacks an atomic, high-precision rule that (1) treats 'Level X' as a modifier that only indicates fair-value hierarchy when explicit fair-value measurement language is present, and (2) prefers carrying/balance tags when amounts are shown as point-in-time balances ('as of', 'at [date]', 'at September 30, 2017', 'balance', 'include', 'comprised of', 'for the period ended') or when the note context lists VIE balances. A delta rule must add exact lexical cues, association windows, precedence, ambiguity handling, unit-tests, and logging to prevent this specific failure class.",
  "operations": [
    {
      "type": "ADD",
      "section": "context_clues_and_indicators",
      "content": "Atomic heuristic: Distinguish 'Level X' mentions from explicit fair-value measurements; prefer carrying/balance tags for point-in-time VIE/note balances.\\n- Purpose: avoid mis-mapping numeric tokens adjacent to 'Level 3' (or Level 1/2) to DebtInstrumentFairValue unless the sentence explicitly states a fair-value measurement. Prefer DebtInstrumentCarryingAmount when amounts are presented as balances, as-of/date snapshots, or VIE/note balance listings.\\n- Exact lexical cues (case-insensitive):\\n  - Fair-value explicit cues (require one to justify DebtInstrumentFairValue): /fair value\\\\b/, /measured at fair value\\\\b/, /carried at fair value\\\\b/, /estimated fair value\\\\b/, /fair-value measurement\\\\b/, /at fair value\\\\b/.\\n  - Level-hierarchy cues (do NOT by themselves imply fair value): /level\\\\s*[123]\\\\b/, /level\\\\s+3\\\\b/, /level\\\\s+1\\\\b/, /level\\\\s+2\\\\b/.\\n  - Balance / carrying cues (favor DebtInstrumentCarryingAmount): /as of\\\\s+[A-Za-z0-9,]+/, /at\\\\s+(?:December|September|June|March|March|\\\\d{1,2},\\\\s*\\\\d{4})/, /at\\\\s+[A-Za-z0-9\\\\-]+\\\\b/, /at\\\\s+September\\\\s+30,?\\\\s+\\\\d{4}/i, /the\\\\s+balance(s)?\\\\s+as\\\\s+of\\\\b/, /included\\\\s+at\\\\s+/, /comprised\\\\s+of\\\\b/, /carrying\\\\s+amount\\\\b/, /carried\\\\s+amount\\\\b/, /balance\\\\s+sheet\\\\s+balance\\\\b/, /at\\\\s+the\\\\s+end\\\\s+of\\\\s+the\\\\s+period\\\\b/.\\n  - VIE / note-listing cues (favor CarryingAmount when present): /variable\\\\s+interest\\\\s+entity\\\\b/, /VIE\\\\b/, /vies?\\\\b/, /consolidated\\\\s+v?ie\\\\b/, /nonconsolidated\\\\s+v?ie\\\\b/, /the\\\\s+following\\\\s+table\\\\s+shows\\\\b/, /the\\\\s+following\\\\s+balances\\\\b/, /included\\\\s+in\\\\s+the\\\\s+consolidated\\\\s+balance\\\\s+sheet\\\\b/.\\n- Association & token-window policy:\\n  - Require existence of an explicit fair-value cue within ±8 tokens of the numeric token (same sentence) to map to DebtInstrumentFairValue when a Level-X cue also appears; Level-X alone must NOT trigger fair-value mapping.\\n  - If a balance/date cue or a VIE/note-listing cue appears in the same sentence or within the immediately preceding sentence (±1 sentence antecedent resolution allowed, span <= 40 tokens), then treat the numeric token as a carrying/balance amount and map to DebtInstrumentCarryingAmount.\\n  - If both fair-value explicit cue and carrying/date/VIE-listing cue co-occur, prefer explicit fair-value language for DebtInstrumentFairValue, but log as 'fairvalue-vs-carrying-conflict' (include spans).\\n- Precedence (apply in order):\\n  1) If fair-value explicit cue present (±8 tokens) -> DebtInstrumentFairValue.\\n  2) Else if balance/date cue OR VIE/note-listing cue present (same sentence OR previous sentence antecedent within span limit) -> DebtInstrumentCarryingAmount.\\n  3) Else if only Level-X present without fair-value explicit cue -> DO NOT map to DebtInstrumentFairValue; mark as 'level-only-ambiguous' and either map conservatively to DebtInstrumentCarryingAmount if other carrying-structure words exist (e.g., 'balances', 'as of') or flag for human review.\\n- Ambiguity handling & logging:\\n  - Any mapping decision where 'Level' appears but no explicit fair-value cue should be logged with label 'level-only-ambiguous' including numeric span, 'Level' span, and surrounding sentence for QA and training.\\n  - Any mapping where both explicit fair-value cues and balance/date cues appear must be logged as 'fairvalue-vs-carrying-conflict' with spans.\\n- Unit-tests / minimal examples to add (atomic):\\n  - \\\"At September 30, 2017, the variable interest entity had assets of $297 and $305 included in 'Level 3 instruments'.\\\" -> $297, $305 = DebtInstrumentCarryingAmount (note-listing + as-of date cues), NOT DebtInstrumentFairValue.\\n  - \\\"The fair value of the instruments, which are Level 3, was $297 at September 30, 2017.\\\" -> $297 = DebtInstrumentFairValue (explicit 'fair value' present).\\n  - \\\"Level 3 instruments included amounts of $10 and $12.\\\" -> flag 'level-only-ambiguous' for review (do not auto-assign DebtInstrumentFairValue); if surrounding sentence shows 'included in the balance sheet as of' map to CarryingAmount.\\n  - \\\"For VIEs, carrying amounts as of December 31 were $X and $Y\\\" -> map to DebtInstrumentCarryingAmount.\\n- Implementation notes: place this rule before any blanket 'Level X -> fair value' fallback; ensure classifier/regression tests penalize mapping to DebtInstrumentFairValue unless explicit fair-value cues are present. Record all 'level-only-ambiguous' examples into a retraining dataset.\"\n    },
    {
      "type": "ADD",
      "section": "common_mistakes_to_avoid",
      "content": "[err-XXXXX] helpful=0 harmful=0 :: Anti-pattern: mapping any mention of 'Level 3' (or fair-value hierarchy) to DebtInstrumentFairValue without verifying explicit fair-value language or balance/date/VIE-listing context. Prevention checklist (atomic):\\n1) Do NOT assign DebtInstrumentFairValue solely because the phrase 'Level 3' or 'Level 2' appears. Require an explicit fair-value cue ('fair value', 'measured at fair value', 'at fair value') within ±8 tokens to justify a fair-value tag.\\n2) If numeric amounts are shown with date anchors ('as of', 'at [date]') or in table/note listing context or adjacent to 'VIE'/'variable interest entity' language, prefer DebtInstrumentCarryingAmount unless explicit fair-value language is present.\\n3) If 'Level X' and 'fair value' both appear, map to DebtInstrumentFairValue; if 'Level X' appears with 'as of'/'included'/'carrying' map to DebtInstrumentCarryingAmount; if both classes of cues are present, log and flag for human review under 'fairvalue-vs-carrying-conflict'.\\n4) Add unit-tests covering each anti-pattern and expected mapping (include the $297/$305 VIE example). 5) Log all 'level-only-ambiguous' mappings for manual QA and include them in retraining batches.\"\n    }
  ],
  "prompt_time": 0.0,
  "response_time": 29.908950328826904,
  "total_time": 29.908950328826904,
  "call_time": 29.908950328826904,
  "prompt_length": 42924,
  "response_length": 6686,
  "prompt_num_tokens": 10124,
  "response_num_tokens": 2475,
  "timestamp": "20260209_143401_425",
  "datetime": "2026-02-09T14:34:01.425290"
}"""

playbook_content = """## STRATEGIES & INSIGHTS

## FORMULAS & CALCULATIONS

## CODE SNIPPETS & TEMPLATES

## COMMON MISTAKES TO AVOID

## PROBLEM-SOLVING HEURISTICS

## CONTEXT CLUES & INDICATORS

## OTHERS"""

print("Testing extraction...")
try:
    ops = _extract_and_validate_operations(response_text)
    print("Operations extracted:", len(ops["operations"]))
except Exception as e:
    print("Extraction failed:", e)

print("\nTesting application...")
try:
    new_pb, next_id = apply_curator_operations(playbook_content, ops["operations"], 100)
    print("New playbook length:", len(new_pb))
    if "Level 3" in new_pb:
        print("SUCCESS: Rule found in playbook")
    else:
        print("FAILURE: Rule NOT found in playbook")
except Exception as e:
    print("Application failed:", e)
