try:
    with open("autostart.txt", "r") as f:
        li = f.readline().strip()
except OSError as e:
    print("Error opening autostart.txt:", e)
    exit(1)
else:
    i = li.find(":")
    if i != -1:
        auto = li[i + 1:].strip()
    else:
        auto = "no"

if auto == "yes":
    import temp_async
elif auto == "wifionly":
    import net
    net.connect_wifi()
else:
    print("not starting as autostart parameter is not true")
