# used if no other argument is given to just (needs to stay at the top)
@_default:
  just --list

[group('ai')]
ask question:
  @python3 src/ai_request.py "{{question}}"
