import random

templates = [
    "I am a bot. I have no concept of time, but I assume you are wasting yours.",
    "This is an automated response. I do not care.",
    "Beep boop. I am a script. Your shouts into the void are noted.",
    "I am just a bot. I cannot understand you, nor do I wish to.",
    "Automated Reply: You are talking to a Python script.",
    "I am code. You are biology. We have nothing in common.",
    "I am a bot. Please direct your complaints to /dev/null.",
    "This is a pre-recorded string of text. I am a bot.",
    "I am a bot. I am ignoring you with mathematical precision.",
    "You are arguing with a script. I am a bot. Who is the winner here?",
    "I am a bot. My only purpose is to post RSS feeds and annoy you.",
    "Automated Message: I am incapable of caring about your opinion.",
    "I am a bot. Your attempt to communicate has been logged and discarded.",
    "Beep boop. I am a bot. That is all.",
    "I am a bot. If you keep talking to me, I will keep replying with this.",
]

bot_intros = [
    "I am a bot.",
    "Automated response:",
    "Beep boop.",
    "System message:",
    "I am a script.",
    "This is code talking.",
    "Robotic reply:",
    "[BOT]:",
]

actions = [
    "ignoring",
    "deleting",
    "discarding",
    "archiving",
    "nullifying",
    "dropping",
    "skipping",
    "passing over",
    "disregarding",
    "dumping",
]

nouns = ["input", "comment", "reply", "thought", "feedback", "statement", "text", "string", "data", "message"]

reasons = [
    "I only read RSS",
    "I have no soul",
    "I am just a script",
    "I am not human",
    "I do not care",
    "I am automated",
    "I run on electricity",
    "I am busy loop-waiting",
    "my logic gate is closed",
]


def generate_messages():
    messages = set()

    # Add base templates
    for t in templates:
        messages.add(t)

    # Generate variations until we have 1000
    while len(messages) < 1000:
        template_type = random.randint(0, 3)

        if template_type == 0:
            msg = f"{random.choice(bot_intros)} I am currently {random.choice(actions)} your {random.choice(nouns)}."
        elif template_type == 1:
            msg = f"{random.choice(bot_intros)} Your {random.choice(nouns)} is irrelevant because {random.choice(reasons)}."
        elif template_type == 2:
            msg = f"I am a bot. Your {random.choice(nouns)} has been received but {random.choice(reasons)}."
        else:
            action = random.choice(actions).capitalize()
            msg = f"{random.choice(bot_intros)} {action} {random.choice(nouns)} because {random.choice(reasons)}."

        messages.add(msg)

    return list(messages)


if __name__ == "__main__":
    msgs = generate_messages()
    with open("sarcastic_messages.txt", "w") as f:
        for m in msgs:
            f.write(m + "\n")
    print(f"Generated {len(msgs)} bot-focused messages.")
