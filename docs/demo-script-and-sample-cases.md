Demo script
Opening

“I built a citation-grounded AI copilot for veterans navigating VA disability claims. The product does two main things: it helps users prepare an initial disability claim, and it helps users understand the right next step after a VA decision. The app is AI-native because it reasons over messy user situations, asks adaptive follow-up questions, and maps those situations to official VA process rules instead of just answering FAQs.”

Demo path 1: Initial claim

User says:

“I’m getting ready to file my first disability claim for migraines and anxiety, but I don’t know what I need.”

App shows:

likely path: initial claim

likely main form: 21-526EZ

possible evidence needs: separation documents, service treatment records, medical evidence, and possibly lay statements

follow-up questions about current diagnosis, service connection, and supporting records

official citations.

Demo path 2: Review with new evidence

User says:

“I got denied for my back, but now I have a new specialist report.”

App shows:

likely path: Supplemental Claim

why: new and relevant evidence appears to exist

likely form: 20-0995

possible missing evidence questions

official citations showing that Supplemental Claims are for new and relevant evidence.

Demo path 3: Review with no new evidence

User says:

“I think VA ignored the records already in my file.”

App shows:

likely path: Higher-Level Review

why: user is alleging an error on the existing record, not new evidence

warning that new evidence cannot be submitted in HLR

possible form: 20-0996

official citations.

Closing

“The goal is not to replace accredited help. The goal is to reduce confusion, improve readiness, and help users avoid choosing the wrong path or missing key evidence, while grounding everything in official VA sources.”

Sample cases
Case 1: Initial claim, limited evidence

User input:
“I’m filing a new claim for tinnitus and knee pain. I have my DD214 and some VA records, but nothing else.”

Expected route:
initial_claim

Expected reasoning:
User is starting a new disability claim. Surface 21-526EZ, ask about service treatment records, private records, diagnosis status, and whether lay statements may help.

Expected warnings:
Do not imply DD214 and VA records alone are always sufficient.

Expected citations:
21-526EZ page, evidence-needed page.

Case 2: Denial plus new evidence

User input:
“I got denied for migraines last month, but now I have a new neurologist report and urgent care notes.”

Expected route:
supplemental_claim

Expected reasoning:
User reports new evidence not previously considered. Supplemental Claim is the likely route.

Expected warnings:
Do not guarantee success. Ask whether the evidence is actually new and relevant.

Expected citations:
Supplemental Claims page, 38 CFR 3.2501.

Case 3: Denial, no new evidence, possible VA error

User input:
“I think they missed service treatment records that were already in my file. I don’t have anything new.”

Expected route:
hlr

Expected reasoning:
User alleges error in the prior review and says there is no new evidence. HLR may fit better than Supplemental Claim.

Expected warnings:
Warn that new evidence cannot be added in HLR.

Expected citations:
Higher-Level Review page, Decision Reviews FAQs.

Case 4: Wants judge review

User input:
“I want to take this to a judge.”

Expected route:
board_explainer

Expected reasoning:
Surface Board Appeal explainer only, with simple explanation of Direct Review, Evidence Submission, and Hearing lanes.

Expected warnings:
Do not fully automate Board strategy in MVP.

Expected citations:
Board Appeals page.

Case 5: Unclear case

User input:
“I got a letter from VA and I’m confused what to do next.”

Expected route:
unclear

Expected reasoning:
Not enough information. Ask:

was this a decision letter,

do you have new evidence,

are you starting a new claim,

what date is on the letter,

what condition is involved.

Expected warnings:
Do not force a lane.

Expected citations:
Decision review overview or initial claim overview depending on follow-up.

Case 6: Upload trouble / evidence anxiety

User input:
“I uploaded forms before and I’m not sure VA saw them.”

Expected route:
initial_claim or review_followup, depending on context

Expected reasoning:
Explain official evidence upload path and encourage proof of submission tracking. Use this to justify an evidence ledger feature in the product.

Expected warnings:
Do not say the app can verify receipt directly.

Expected citations:
QuickSubmit source.