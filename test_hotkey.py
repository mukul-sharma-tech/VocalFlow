import keyboard

print("Press any key to see its name. Press Ctrl+C to quit.")
keyboard.hook(lambda e: print(f"  event_type={e.event_type}  name={e.name!r}"))
keyboard.wait()
