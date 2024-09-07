import openai

gpt_model = "gpt-4o-mini"

def _gpt_replay(content, prompt):
    return openai.ChatCompletion.create(
        model = gpt_model,
        messages = [
            {"role": "system", "content": prompt},
            {"role": "user", "content": content}
        ]
    )["choices"][0]["message"]["content"].lower()

def gpt_porn(content):
    return "true" in _gpt_replay(
        f"Does the following text contain any adult or explicit content?\n\nText: {content}\n\nAnswer with True or False.",
        "You are a content safety assistant."
    )

def gpt_ad(content, need_at=True):
    if need_at:
        return ("true" in _gpt_replay(
            f"Does the following text contain any promotional or advertisement content, including content that attempts to redirect users to websites, homepages, or encourages watching videos?\n\nText: {content}\n\nAnswer with True or False.",
            "You are a content safety assistant."
        )) if "@" in content else False
    else:
        return "true" in _gpt_replay(
            f"Does the following text contain any promotional or advertisement content?\n\nText: {content}\n\nAnswer with True or False.",
            "You are a content safety assistant."
        )

