# Cogs
## Loading a cog
In `main.py`, in the `if __name__ == "__main__"` block, write the following
```python
bot.load_extension("path.to.cog")
```
## syncdata()
This function receives and processes changes to the bot's configuration. It receives
the changes from the `host()` function in `config_framework.py` and changes the values within
its cog.