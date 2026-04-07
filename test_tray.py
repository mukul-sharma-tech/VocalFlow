from PIL import Image, ImageDraw
import pystray

img = Image.new("RGB", (64, 64), color=(255, 0, 0))
d = ImageDraw.Draw(img)
d.rectangle([10, 10, 54, 54], fill=(255, 255, 255))

icon = pystray.Icon("test", img, "Test Icon", menu=pystray.Menu(
    pystray.MenuItem("Quit", lambda i, item: i.stop())
))
print("Running tray icon — check system tray (expand ^ arrow near clock)")
icon.run()
print("Done")
