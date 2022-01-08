# Administration


## ./admin
Change global settings.
### ./admin bot enable/disable/restart
Enables or disables all bot functions. Also restart the bot.

### ./admin someoneping enable/disable
Enables or disables the someoneping `@someone` feature.

### ./admin greetings enable/disable
Enables or disables the greeting feature.

### ./admin blacklist add/remove/reset (broken - see GitHub issues)
Add or remove someone from the bot's blacklist. **You must send
the user's ID** for this to work. Also resets the blacklist to empty if 
needed.

`./admin blacklist add/remove 0123456789`

### ./admin afk reset (broken - see same GitHub issue as ./admin blacklist)
Resets the AFK members list.

### ./admin settings reset
Resets **all settings** for Omni.

### ./admin analytics
Shows bot log (soon to be deprecated) and error log.

### ./admin exec [code]
Executes Python code using the `exec()` builtin.

The Python code must be inside a code block.


## ./update
Install bot updates.

### ./update generatekey
Generates a new encryption key for the update.

### ./update new
Install an update.

It is strongly recommended that you create an update package
with the `update_packer.py` script.

The update must be encrypted with the same encryption key
and with the `cryptography` Python module.

In its decrypted state, the update must be a zip file that the
`zipfile` library can open. It must not be password protected.

There is an option to run a `setup.py` file before the update is installed
This will be run inside the `temp/` directory. If you want to run a `setup.py`
script, you must include it inside the update zip.

If a restart is needed to complete the update, the update handler will
write `True` to `data/isupdate.json` and `False` to `data/updatesuccess.json`.
This is so that the updated instance knows this is an update and for the
update success verification system.

The update handler then starts the updated instance and waits for up to 10 seconds
for `data/updatesuccess.json` to contain a `True` value. If it reads `True`,
It will shut down, leaving only the updated instance running. If the value remains
`False` after 10 seconds, it will try to terminate the updated instance and will start
the update rollback process.

### ./update rollback
Rolls back to the previous version if possible.

**No compatibility checks are performed**