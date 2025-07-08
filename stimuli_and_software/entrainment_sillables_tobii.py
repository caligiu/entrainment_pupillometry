import csv
import random
import time
from psychopy import visual, core, event
from psychopy.iohub import launchHubServer
import subprocess

# Disable notifications during experiment
subprocess.run([
    'powershell', '-Command',
    "powershell -ExecutionPolicy Bypass -Command \"&{Set-ItemProperty -Path 'HKCU:\\Software\\Microsoft\\Windows\\CurrentVersion\\Notifications\\Settings' -Name 'NOC_GLOBAL_SETTING_TOASTS_ENABLED' -Value 0}\""
], shell=True)

# Setup the window
win = visual.Window(size=[1920, 1080], color=[-0.7, -0.7, -0.7], fullscr=True, checkTiming=True, units='pix')
win.mouseVisible = False

# Create text stimuli
syllable_stim = visual.TextStim(win, text='', color='white', height=50, anchorHoriz='left', alignText='left')
instruction_stim = visual.TextStim(win, text='', color='white', pos=(0, 0), height=30)
feedback_stim = visual.TextStim(win, text='', color='white', pos=(0, -200), height=30)
task_stim = visual.TextStim(win, text='', color='white', pos=(0, -100), height=50)

# Function to get participant number
def get_participant_number():
    instruction_stim.text = "Please type your participant number and press Enter (or press 'Y' to exit):"
    instruction_stim.draw()
    win.flip()

    participant_id_keys = event.waitKeys(keyList=['0', '1', '2', '3', '4', '5', '6', '7', '8', '9', 'return', 'y'], clearEvents=False)
    participant_id = ''
    while 'return' not in participant_id_keys:
        for key in participant_id_keys:
            if key == 'y':
                core.quit()
            if key != 'return':
                participant_id += key
        instruction_stim.text = f"Please type your participant number and press Enter (or press 'Y' to exit):\n{participant_id}"
        instruction_stim.draw()
        win.flip()
        participant_id_keys = event.waitKeys(keyList=['0', '1', '2', '3', '4', '5', '6', '7', '8', '9', 'return', 'y'], clearEvents=False)
    return int(participant_id)

def show_instructions(participant_id):
    if participant_id % 2 == 0:
        instruction_text = (
            "Benvenut*!\n\n"
            "Presta attenzione a quello che vedrai sullo schermo. "
            "Alla fine di ogni blocco ti verrà chiesto se hai visto una specifica parola formata da due sillabe.\n\n"
            "Premi 'M' per SI e 'Z' per NO.\n\n"
            "Premi qualsiasi tasto per iniziare"
        )
    else:
        instruction_text = (
            "Benvenut*!\n\n"
            "Presta attenzione a quello che vedrai sullo schermo. "
            "Alla fine di ogni blocco ti verrà chiesto se hai visto una specifica parola formata da due sillabe.\n\n"
            "Premi 'Z' per SI e 'M' per NO.\n\n"
            "Premi qualsiasi tasto per iniziare"
        )
    instruction_stim.text = instruction_text
    instruction_stim.draw()
    win.flip()
    keys = event.waitKeys()
    if 'y' in keys:
        core.quit()

def show_pause():
    instruction_text = "Premi la barra spaziatrice per il prossimo blocco"
    instruction_stim.text = instruction_text
    instruction_stim.draw()
    win.flip()
    keys = event.waitKeys()
    if 'y' in keys:
        core.quit()

def getList(listname):
    with open(f'./blocks/{listname}.txt') as fp:
        line = fp.readlines()
    return line[0].split()

def read_syllables_from_csv(filename):
    syllables_info = []
    with open(filename, newline='', mode="r", encoding="utf-8") as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            syllables_info.append(row)
    return syllables_info

def show_block(block, seq):
    eyetracker.setRecordingState(True)
    eyetracker.sendMessage(f"BLOCK_START_{block}")
    core.wait(1)

    info = []
    t0 = time.time()
    for syllable_info in seq:
        syllable_stim.text = syllable_info.get('SYLL', 'N/A')
        syllable_stim.draw()
        core.wait(0.225 - time.time() + t0)
        win.flip()
        t0 = time.time()
        syllable_info.update([('timestamp', time.time())])
        eyetracker.sendMessage(f"SYLLABLE_{syllable_info['SYLL']} @ {syllable_info['timestamp']}")
        info.append(syllable_info)
        core.wait(0.125 - time.time() + t0)
        win.flip()

    core.wait(1)
    eyetracker.sendMessage(f"BLOCK_END_{block}")
    eyetracker.setRecordingState(False)

    percent_complete = (progress / totalblocks) * 100
    target = syllable_info.get('TARGET', 'N/A')
    present = syllable_info.get('PRESENT', 'N/A')
    resp = show_task(target=target, isyes=present, progress=int(percent_complete), participant_id=participant_id)
    log_event(logfile, info, block, target, correct=resp[0], RT=resp[1])

def show_task(target, isyes, progress, participant_id):
    yes_key = 'm' if participant_id % 2 == 0 else 'z'
    no_key = 'z' if participant_id % 2 == 0 else 'm'

    task_stim.text = f"Hai visto questa parola?\n\n{target}\n\nPremi '{yes_key.upper()}' per SI o '{no_key.upper()}' per NO"
    task_stim.draw()
    win.flip()
    start = time.time()
    keys = event.waitKeys(keyList=['m', 'z', 'y'])
    if 'y' in keys:
        core.quit()
    else:
        rt = time.time() - start

    response = keys[0]
    correct = (response == yes_key) if bool(int(isyes)) else (response == no_key)
    feedback_text = "Corretto!" if correct else "Sbagliato!"
    feedback_stim.text = f"{feedback_text}\n\nProgress: {progress}% completato" if progress > 0 else f"{feedback_text}\n\n"
    feedback_stim.draw()
    win.flip()
    core.wait(3)
    return correct, rt

def log_event(logfile, infos, block, target, correct=None, RT=None):
    fieldnames = ['timestamp', 'syllable', 'wp', 'type', 'order', 'block', 'target', 'correct', 'RT']
    for info in infos:
        row = {
            'timestamp': info.get('timestamp', 'N/A'),
            'syllable': info.get('SYLL', 'N/A'),
            'wp': info.get('WP', 'N/A'),
            'type': info.get('TYPE', 'N/A'),
            'order': info.get('ORDER', 'N/A'),
            'block': block,
            'target': target,
            'correct': correct,
            'RT': RT
        }
        with open(logfile, mode='a', newline='') as file:
            writer = csv.DictWriter(file, fieldnames=fieldnames)
            writer.writerow(row)

# === Start Experiment ===

participant_id = get_participant_number()

# Init Tobii eye tracker via iohub
io_config = {
    'eyetracker.hw.tobii.EyeTracker': {
        'name': 'tracker',
        'model_name': 'Tobii TX300',  # <-- Change to match your model
        'runtime_settings': {
            'sampling_rate': 120  # Adjust if your device supports other rates (e.g., 60, 300, 600)
        }
    }
}
iohub_tracker = launchHubServer(**io_config)
eyetracker = iohub_tracker.getDevice('tracker')

# Calibration (optional but recommended)
eyetracker.runSetupProcedure()

# Log file setup
logfile = f"logs/sj{participant_id:03d}.csv"
fieldnames = ['timestamp', 'syllable', 'wp', 'type', 'order', 'block', 'target', 'correct', 'RT']
with open(logfile, mode='w', newline='') as file:
    writer = csv.DictWriter(file, fieldnames=fieldnames)
    writer.writeheader()

show_instructions(participant_id)

# Practice
plist = getList('pract')
progress = 0
totalblocks = 40

for pb in plist:
    syllables = read_syllables_from_csv(f'./blocks/p{pb}.csv')
    show_pause()
    show_block(pb, syllables)

show_instructions(participant_id)

# Experimental blocks
oo = ['D', 'A', 'B', 'C']
l = oo[participant_id % 4]
elist = getList(f'list{l}')

for eb in elist:
    progress += 1
    syllables = read_syllables_from_csv(f'./blocks/b{eb}.csv')
    show_pause()
    show_block(eb, syllables)

# End of experiment
instruction_stim.text = "L'esperimento è terminato. Grazie per la tua partecipazione!"
instruction_stim.draw()
win.flip()
event.waitKeys()

# Shutdown
eyetracker.setRecordingState(False)
iohub_tracker.quit()
win.close()
core.quit()

# Restore notifications
subprocess.run([
    'powershell', '-Command',
    "powershell -ExecutionPolicy Bypass -Command \"&{Set-ItemProperty -Path 'HKCU:\\Software\\Microsoft\\Windows\\CurrentVersion\\Notifications\\Settings' -Name 'NOC_GLOBAL_SETTING_TOASTS_ENABLED' -Value 1}\""
], shell=True)

