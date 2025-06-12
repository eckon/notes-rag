# used if no other argument is given to just (needs to stay at the top)
@_default:
  just --list

setup:
  python3 -m venv venv
  ./venv/bin/pip install --upgrade -r requirements.txt
  @echo "\nvenv created. Run 'source venv/bin/activate' to activate it."

[group('ai')]
ask question:
  @python3 src/ai_request.py "{{question}}"
