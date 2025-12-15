# Log Parser CLI

Your log analysis tool works well for batch processing, but the operations team needs to interact with it throughout the day. Your task is to add an interactive CLI that allows users to query robot states, filter alerts, and trigger manual checks.

## Commands to Implement

### Status Commands
- `status all` - Shows a summary of all robot statuses
- `status <robot-id>` - Shows detailed status for a specific robot

### Performance Commands
- `perf all` - Shows the pick success ratio of the last 10 minutes for all robots
- `perf <robot-id>` - Shows the pick success ratio of the last 10 minutes for a specific robot

### Help and Exit
- `help` - Shows available commands
- `exit` - Exits the application

## Implementation Notes

- The robot status should show the current usage of all reported resources plus if the robot had made any picks in the last 5 minutes
- Use a simple command loop for user input
- Store results in memory (no need for persistence between sessions)
- Focus on functionality over presentation
- Re-use your existing parsing and analysis code