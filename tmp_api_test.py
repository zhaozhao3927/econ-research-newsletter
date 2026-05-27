import os
import anthropic

key = os.environ.get("ANTHROPIC_API_KEY")
print("key_present:", bool(key), "prefix:", (key or "")[:7], "len:", len(key or ""))

client = anthropic.Anthropic(api_key=key)
resp = client.messages.create(
    model="claude-sonnet-4-6",
    max_tokens=20,
    messages=[{"role":"user","content":"Say OK"}],
)
print(resp.content[0].text)
