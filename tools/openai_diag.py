import os, sys

key = os.getenv('OPENAI_API_KEY')
print('OPENAI_KEY_PRESENT:', bool(key))
if not key:
    print('No OPENAI_API_KEY found in environment for this process.')
    sys.exit(2)

try:
    import openai
    openai.api_key = key
    model = os.getenv('OPENAI_MODEL', 'gpt-4o-mini')
    resp = openai.ChatCompletion.create(
        model=model,
        messages=[{'role': 'user', 'content': 'Provide a one-line test confirmation: AI OK.'}],
        max_tokens=20,
        temperature=0
    )
    text = ''
    if resp and resp.get('choices'):
        ch = resp['choices'][0]
        msg = ch.get('message') or ch.get('text') or ''
        if isinstance(msg, dict):
            text = msg.get('content', '')
        else:
            text = str(msg)
    print('AI_RESPONSE:', text.strip())
    sys.exit(0)
except Exception as e:
    print('AI_ERROR:', str(e))
    sys.exit(1)
