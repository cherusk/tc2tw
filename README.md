# tc2tw
---
Converter for TaskCoach to Taskwarrior state.

This is calling the Taskwarrior CLI (as API) directly,
so no need for any intermediary migration state.

```
usage: tc2tw.py [-h] [-i TC_FILE] [-t TW_PATH]

Converter for TaskCoach to Taskwarrior state

optional arguments:
  -h, --help            show this help message and exit
    -i TC_FILE, --tc_file TC_FILE
                            TaskCoach state file
                              -t TW_PATH, --tw_path TW_PATH
                                                      Taskwarrior binary to use
```

