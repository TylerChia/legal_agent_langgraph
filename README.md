# LangGraph Contract Analysis Workflow

## Complete Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                        START: Contract Upload                    │
│                    (PDF → Text Extraction)                       │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
                  ┌──────────────────────┐
                  │  1. Extract Company  │
                  │                      │
                  │  • LLM extraction    │
                  │  • Regex fallback    │
                  │  • For email subject │
                  └──────────┬───────────┘
                             │
                             ▼
                  ┌──────────────────────┐
                  │  2. Parse Contract   │
                  │                      │
                  │  • Extract clauses   │
                  │  • Deliverables      │
                  │  • Payment terms     │
                  │  • Legal flags       │
                  └──────────┬───────────┘
                             │
                             ▼
                  ┌──────────────────────┐
                  │  3. Analyze Risks    │
                  │                      │
                  │  • Content ownership │
                  │  • Exclusivity       │
                  │  • Usage rights      │
                  │  • Risk scoring      │
                  └──────────┬───────────┘
                             │
                             ▼
                  ┌──────────────────────┐
                  │  4. Research Terms   │  ← NEW STEP!
                  │                      │
                  │  • Detect unclear    │
                  │    legal terms       │
                  │  • Web search        │
                  │  • Summarize results │
                  │  • Add context       │
                  └──────────┬───────────┘
                             │
                             ▼
              ┌──────────────┴──────────────┐
              │                             │
              ▼ (creator mode)              ▼ (legal mode)
   ┌──────────────────────┐                │
   │ 5a. Extract          │                │
   │     Deliverables     │                │
   │                      │                │
   │ • Due dates          │                │
   │ • Times & timezones  │                │
   │ • Calendar format    │                │
   └──────────┬───────────┘                │
              │                             │
              └──────────────┬──────────────┘
                             │
                             ▼
                  ┌──────────────────────┐
                  │  6. Write Summary    │
                  │                      │
                  │  • Friendly language │
                  │  • Include research  │  ← Research included!
                  │  • Markdown format   │
                  │  • Risk highlights   │
                  └──────────┬───────────┘
                             │
                             ▼
                  ┌──────────────────────┐
                  │  7. Send             │
                  │     Notifications    │
                  │                      │
                  │  • Email summary     │
                  │  • Calendar invites  │
                  │    (creator mode)    │
                  └──────────┬───────────┘
                             │
                             ▼
                  ┌──────────────────────┐
                  │         END          │
                  │                      │
                  │  ✅ Analysis         │
                  │     Complete         │
                  └──────────────────────┘
```

## Mode Differences

### Legal Mode
```
extract_company → parse_contract → analyze_risks 
→ research_terms → write_summary → send_notifications
```
- Basic contract analysis
- No deliverables extraction
- No calendar integration
- Research included (if unclear terms found)

### Creator Mode
```
extract_company → parse_contract → analyze_risks 
→ research_terms → extract_deliverables 
→ write_summary → send_notifications
```
- Brand deal focused
- Deliverables extraction
- Calendar invites sent
- Research included (if unclear terms found)

