Agentic Workflow Spec
Workflow name

Decision Letter to Next-Step Packet

Goal

Turn an uploaded VA decision letter plus a short user explanation into a structured, citation-backed next-step packet.

Why this workflow exists

This workflow demonstrates the AI-native part of the app. Instead of just answering a question, the system:

reads a real document,

extracts structured case facts,

checks those facts against official VA rules,

asks clarifying questions if needed,

and generates a usable output artifact.

Input

Uploaded decision letter PDF or pasted decision text

Short user statement, such as:

“I got denied and now I have new evidence.”

“I think they missed records already in my file.”

“I want to appeal.”

Workflow steps
Step 1: Document extraction

Extract raw text from the uploaded document.
Output:

raw_text

ocr_used true/false

parse_confidence

Step 2: Case-state extraction

Use AI to identify likely structured facts:

decision date

issue names / claimed conditions

whether this appears to be a denial or post-decision context

whether the text appears to mention favorable findings

phrases that suggest missing evidence, nexus issues, or lane context

Output:

decision_date

issues[]

possible_denial_signals[]

possible_favorable_findings[]

parse_notes

Step 3: User-situation merge

Merge extracted facts with user-stated facts:

whether the user says they have new evidence

whether they believe VA missed existing evidence

whether they want a judge review

Output:

user_case_profile

Step 4: Rules check

Compare the profile against the MVP rules matrix:

if new evidence exists, consider Supplemental Claim logic

if no new evidence and user alleges error on the record, consider HLR logic

if the user wants judge review, surface Board explainer

if unclear, ask follow-up questions

Output:

candidate_paths[]

rule_hits[]

follow_up_questions[]

Step 5: Response generation

Generate a structured next-step packet:

likely pathway

why it appears to fit

possible forms

possible missing evidence

warnings

manual verification items

official citations

safety note

Output:

next_step_packet

Step 6: Optional human-reviewed export

Optional n8n or app-side review step:

approve packet

export as markdown/PDF

save for demo

add timestamp/log

Output artifact

The final packet should include:

case summary

likely path

evidence/readiness checklist

likely forms

warnings

official sources

escalation note to accredited help if needed

Failure and fallback behavior

If parsing confidence is low:

tell the user the document could not be confidently read

fall back to conversational intake

ask the user to summarize the decision in plain language

If route is unclear:

do not force a lane

ask targeted follow-up questions

show “possible paths” instead of a hard answer

If no official source is available for a statement:

omit the statement

or phrase it as a question for the user to verify

Human review point

If the app prepares an exportable packet, a human review step can approve it before export. This is especially useful if using n8n as a post-processing workflow.

Why this satisfies the AI-native requirement

The workflow is not just retrieval. It is:

document understanding,

state extraction,

multi-step reasoning,

rules-plus-LLM orchestration,

and structured output generation.