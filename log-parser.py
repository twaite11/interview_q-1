import re
from datetime import datetime


def analyze_robot_logs(file_path):
    # setup regex patterns
    timestamp_pattern = re.compile(r"^(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z)")
    log_pattern = re.compile(r"^(\S+) (\S+) \S+ (\S+) (.*)$")
    res_pattern = re.compile(r"CPU: ([\d.]+)%, RAM: ([\d.]+)%, DISK: ([\d.]+)%")
    pick_pattern = re.compile(r"Attempts: (\d+), Successful: (\d+)")

    # state tracking
    robots = {}
    last_log_time = None

    print(f"processing {file_path}...")

    # part 1: parsing (buffer logic handles the multi-line log entries)
    raw_entries = []
    current_buffer = ""

    with open(file_path, 'r') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue

            # if line starts with timestamp, it's a new entry
            if timestamp_pattern.match(line):
                if current_buffer:
                    raw_entries.append(current_buffer)
                current_buffer = line
            else:
                # otherwise it's part of the previous line (broken formatting)
                current_buffer += " " + line

        if current_buffer:
            raw_entries.append(current_buffer)

    # part 2: analysis

    for entry in raw_entries:
        match = log_pattern.match(entry)
        if not match:
            continue

        ts_str, r_id, comp, msg = match.groups()

        try:
            curr_time = datetime.strptime(ts_str, "%Y-%m-%dT%H:%M:%SZ")
        except ValueError:
            continue

        # track latest global time for gap detection
        if last_log_time is None or curr_time > last_log_time:
            last_log_time = curr_time

        # init bot state if new
        if r_id not in robots:
            robots[r_id] = {
                'last_seen': curr_time,
                'res_streak': 0,
                'pick_streak': 0,
                'alerts': set()
            }

        bot = robots[r_id]
        bot['last_seen'] = curr_time

        # [cite_start]check 1: resource overuse [cite: 16]
        if comp.upper() == 'RESOURCES':
            res = res_pattern.search(msg)
            if res:
                cpu, ram, disk = map(float, res.groups())
                if cpu > 85 or ram > 85 or disk > 85:
                    bot['res_streak'] += 1
                    if bot['res_streak'] >= 3:
                        bot['alerts'].add("resource overuse (cpu/ram/disk > 85%)")
                else:
                    bot['res_streak'] = 0

        # [cite_start]check 2: pick failures [cite: 17]
        elif comp.upper() == 'PICKS':
            pick = pick_pattern.search(msg)
            if pick:
                attempts, successful = map(int, pick.groups())

                # failure = tried at least once, succeeded zero times
                if attempts > 0 and successful == 0:
                    bot['pick_streak'] += 1
                    if bot['pick_streak'] >= 5:
                        bot['alerts'].add("pick failures (> 5 consecutive failing reports)")
                else:
                    # reset on any success or if idle
                    bot['pick_streak'] = 0

    # part 3: output
    print(f"\n{'ROBOT ID':<15} | {'STATUS':<10} | {'ALERTS'}")
    print("-" * 65)

    found_issues = False

    for r_id in sorted(robots.keys()):
        bot = robots[r_id]

        # convert set to list so we can append gaps if needed
        active_alerts = list(bot['alerts'])

        # [cite_start]check 3: reporting gaps [cite: 14, 15]
        # logic: current time - last seen > 30 mins
        time_since_last = (last_log_time - bot['last_seen']).total_seconds() / 60
        if time_since_last > 30:
            active_alerts.append(f"reporting gap (silent for {int(time_since_last)}m)")

        if active_alerts:
            found_issues = True
            # sort specific errors to keep output clean/deterministic
            active_alerts.sort()

            # loop through all errors for this robot (handling multiple)
            for i, alert in enumerate(active_alerts):
                # only print robot id on the first line
                prefix = r_id if i == 0 else ""
                status = "ALERT" if i == 0 else ""
                print(f"{prefix:<15} | {status:<10} | {alert}")
        else:
            print(f"{r_id:<15} | {'OK':<10} | nominal")

    if not found_issues:
        print("\nno active issues detected.")
    return robots

def run_cli(ROBOTS: dict):
    while True:
        try:
            user_input = input("log-cli> ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            print("exiting...")
            break

        parts = user_input.split()

        cmd = parts[0]
        args = parts[1] if len(parts) > 1 else None

        if cmd == 'exit':
            print("exiting...")
            break\

        elif cmd == 'status':
            if args == 'all':
                print(f"\n{'ROBOT ID':<15} | {'STATUS':<10} | {'ALERTS'}")
                print("-" * 65)
                for r_id in sorted(ROBOTS.keys()):
                    bots = ROBOTS[r_id]
                    alerts = bots['alerts'] if bots['alerts'] else "nominal"
                    print(f"{r_id:<15} | {'OK':<10} | {alerts}")
            elif args.upper() in ROBOTS:
                bots = ROBOTS[args.upper()]
                alerts = bots['alerts'] if bots['alerts'] else "nominal"
                print(f"{r_id:<15} | {'OK':<10} | {alerts}")
            else:
                print('error in id')
                print(args)

if __name__ == "__main__":

    robots = analyze_robot_logs('robot_logs.txt')
    run_cli(robots)
