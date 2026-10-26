# Pi To-Do setup guide ♡

For a **Raspberry Pi 4** with the **official 7" touchscreen** and a **personal Microsoft account**. Takes about an hour, and you don't need to know any code. When a step says "type", type it exactly (or copy and paste it), then press Enter.

---

## Part 1 · Put it together (wait until the case arrives)
1. Connect the screen's ribbon cable to the Pi's **DSI** port (the slim connector labelled DISPLAY). Follow the screen's leaflet for power: some screens use 2 jumper wires on the Pi's pins, others power through the ribbon cable.
2. Put it in the case. **Don't plug in the power yet.**

## Part 2 · Set up the memory card (on your laptop)
1. Download **Raspberry Pi Imager** from raspberrypi.com/software and open it.
2. Choose: **Device:** Raspberry Pi 4 → **OS:** Raspberry Pi OS (64-bit), the normal one with desktop → **Storage:** your microSD card.
3. When it asks about **OS customisation**, click **Edit settings** and fill in:
   - a username and password (write these down!)
   - your **wifi name and password**
   - your country (GB) and time zone
4. Click **Write** and wait. Then put the card into the Pi and plug in the power.
5. It'll start up to a desktop. If the picture is sideways: **Pi menu → Preferences → Screen Configuration**, right-click the screen → **Orientation**, choose the landscape option → Apply.
6. Stop the screen switching off: **Pi menu → Preferences → Raspberry Pi Configuration → Display → Screen Blanking: Off**.

## Part 3 · Register with Microsoft (on your laptop, ~15 min)
This gives the Pi permission to read your To Do. It's free.

1. Go to **portal.azure.com** and sign in with your personal Microsoft account.
2. If it says you need a directory or subscription, click **Sign up for Azure free account** and follow the steps. Microsoft may ask for a card to confirm who you are. App registration is free and you won't be charged for this.
3. In the search bar at the top, type **App registrations** and open it → **+ New registration**.
   - **Name:** `Pi To-Do`
   - **Supported account types:** *Accounts in any organizational directory and personal Microsoft accounts*. This also lets you switch to a work account later.
   - **Redirect URI:** leave empty
   - Click **Register**.
4. On the page that opens, copy the **Application (client) ID** (a long code like `1a2b3c4d-…`). Keep it handy.
5. In the left menu click **Authentication** → scroll to **Allow public client flows** → set to **Yes** → **Save**.

## Part 4 · Copy the files to the Pi
1. Download the `pi-todo` folder (zip) from this project and unzip it.
2. Copy the whole **pi-todo** folder onto a USB stick, plug it into the Pi, and drag the folder into the Pi's **Home** folder (in the File Manager).
3. On the Pi, open **pi-todo → config.json** (double-click opens it in the text editor). Replace `PASTE-YOUR-APPLICATION-CLIENT-ID-HERE` with your code from Part 3, keeping the quote marks. Save.

## Part 5 · Install (on the Pi)
Open **Terminal** (the black screen icon at the top) and type:

```
cd ~/pi-todo
bash install.sh
```

It may ask for your Pi password. When it says **All set ♡**, type:

```
sudo reboot
```

## Part 6 · Sign in
After the restart, the pink screen will show a **code** and a web address.
1. On your phone, go to that address (**microsoft.com/link**).
2. Enter the code, sign in, and tap **Accept**.
3. Within a few seconds, your To Do tasks appear ♡

You only do this once.

---

## How it works
- It shows tasks from **all your lists** that aren't done, plus anything you finished today.
- **Importance** in To Do (the star = high): high → *urgent*, normal → *today*, low → *whenever*.
- Ticking a task on the screen ticks it in To Do too. New tasks appear within a minute.

## Change things (in config.json, then restart the Pi)
- **Only some lists:** `"lists": ["Work", "Tasks"]`
- **Only tasks due today or overdue:** `"only_due_today": true`

## Switch to a work account later
In Terminal type `rm ~/pi-todo/token.json`, then `sudo reboot`. The sign-in code appears again. Sign in with your work account. If it says you need admin approval, your IT team has to allow the app.

## If something goes wrong
- **Exit the full-screen display:** plug in a keyboard and press **Alt + F4**.
- **See what the program is saying:** in Terminal type `journalctl -u pi-todo -f`
- **Blank screen or no tasks:** check the wifi icon at the top of the desktop, then restart the Pi.
