#Configuration Framework
##Method Descriptions


###listener(port: int) -> Listener
Returns a multiplrocessing.Listener object (shortcut without 
having to give an address and authkey)

`port` must be a valid network port number.


###client(port: int) -> Client
Same thing as listener method except with a multiprocessing.Client
object. Does not need the duplicate port check.

`port` must be a valid network port number.


###createconfig(scope) -> dict
Creates dictionary objects that are used to manage/save configuration.

`scope` has two valid options: `"server"` and `"other"`. The `"server"`
option creates a dictionary for a Discord server (guild).
The `"other"` option creates a dictionary for global settings/values, such as
afk statuses, and global bot configuration. The `"server"` option creates a
dictionary for servers, such as anti-raid configuration.


###loadconfig() -> dict
Loads all saved settings and values from the JSON files into a dictionary.

Any data that is not limited to a server is stored inside 
`data/globalconfig.json`, while server (guild) specific data is stored inside
`data/{guild_id_SHA256_hash}/data.json`

**There are no checks to verify the validity/integrity of the data.**


###saveconfig(changes: dict or str) -> None
Receives a dictionary or string and forwards it to the host.

To save settings/values, `changes` must be a dictionary.
`changes` should only be a string when the payload is `"close"`.
This tells all registered listeners and the host listener that
they should close their connection.

When saving settings/values, the structure of changes depends on the value
in question. When it is a global value that is not server (guild) specific,
the syntax is 
```python
{
    "setting.setting.setting.AndSoOn": bool
}
```
When saving a server specific value, the syntax is
```python
{
    "guild.{guild_id_SHA256_hash}.setting.setting.AndSoOn": bool
}
```
If the value type is not a bool, it may have an action you need to specify at
the end of the dictionary key such as
```python
{
    "setting.setting.setting.append": value,
    "setting.setting.setting.add": None
}
```
**There are no checks for syntax/value correctness.**

***This configuration system is still in development. Better documentation, syntax, code, and consistency
will be eventually added. You can still look at the code and figure out the undocumented
parts yourself.***


###host() -> None
Receives data from `saveconfig()`, saves the changed values, and forwards the changes to each\
registered listener. The registered listeners' ports are stored in the global variable `ports`.

**There are no checks for syntax/value correctness.**

***This configuration system is still in development. Better documentation, syntax, code, and consistency
will be eventually added. You can still look at the code and figure out the undocumented
parts yourself.***


###gethash(value) -> str
Returns the SHA256 hash of a given value.

`value` can be any data type.


###_saveconfig(deltas) -> None
Saves the changed settings to their respective JSON files.

`deltas` must be a list or tuple. Only two values are valid in the parameter:
(a) `"globalconfig"`, which pertains to any setting and/or value that is not limited to a server (guild),
and (b) the SHA256 hash of a server (guild) id, which pertains to the settings
and values that only affects the server.