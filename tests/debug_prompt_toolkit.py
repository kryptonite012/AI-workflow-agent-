"""
Simple debug test for prompt_toolkit autocomplete.
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).resolve().parents[1]
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))


import sys
from pathlib import Path


print("="*50)
print("  PROMPT_TOOLKIT DEBUG TEST")
print("="*50)

# Step 1: Register commands
print("\nStep 1: Register commands...")
from src.slash_commands.on_run_time_register import OnRunTimeRegistry
from src.slash_commands.protocol import SlashCommand

registry = OnRunTimeRegistry()
print(f"  Initial registry size: {len(registry)}")

cmds = [
    SlashCommand(command="help", options=None, requirements=None, description="Show help", handler=None),
    SlashCommand(command="agent", options=None, requirements=None, description="Run agent", handler=None),
    SlashCommand(command="clear", options=None, requirements=None, description="Clear chat", handler=None),
    SlashCommand(command="exit", options=None, requirements=None, description="Exit app", handler=None),
]

for c in cmds:
    try:
        registry.register(c)
        print(f"  + Registered: /{c.command}")
    except Exception as e:
        print(f"  * Already exists: /{c.command}")

print(f"  Final registry size: {len(registry)}")

# Step 2: Test completer
print("\nStep 2: Test ChatCompleter...")
from src.ui.chatInputHandler import ChatCompleter
from prompt_toolkit.document import Document

completer = ChatCompleter()

test_inputs = ["/", "/h", "/he", "/a"]
for inp in test_inputs:
    doc = Document(text=inp, cursor_position=len(inp))
    completions = list(completer.get_completions(doc, None))
    print(f"  Input '{inp}' -> {len(completions)} completions")
    for c in completions[:3]:
        print(f"      {c.text}")

# Step 3: Interactive test
print("\nStep 3: Interactive test...")
print("  Type / to see dropdown, /exit to quit\n")

from prompt_toolkit import PromptSession

session = PromptSession(
    completer=completer,
    complete_while_typing=True,
    reserve_space_for_menu=8,
)

while True:
    try:
        result = session.prompt("test> ")
        print(f"  You typed: {result}")
        if result == "/exit":
            break
    except KeyboardInterrupt:
        print("\n  Bye!")
        break
