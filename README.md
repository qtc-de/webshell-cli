### webshell-cli

----

*webshell-cli* is a python script that allows accessing its associated webshells in a commandline
fashion. *webshell-cli* supports changing the current working directory, setting environment
variables and allows easy uploads and downloads of files.

![](https://github.com/qtc-de/webshell-cli/workflows/main%20Python%20CI/badge.svg?branch=main)
![](https://github.com/qtc-de/webshell-cli/workflows/develop%20Python%20CI/badge.svg?branch=develop)
[![](https://img.shields.io/badge/version-1.0.0-blue)](https://github.com/qtc-de/webshell-cli/releases)
![](https://img.shields.io/badge/python-9%2b-blue)
[![](https://img.shields.io/badge/license-GPL%20v3.0-blue)](https://github.com/qtc-de/container-arsenal/blob/master/LICENSE)



https://user-images.githubusercontent.com/49147108/165632033-efe925fe-63ce-445f-9570-78fadec4e09a.mp4



### Installation

----

*webshell-cli* is just a python script. After installing the requirements, you should be able
to run it:

```console
[qtc@devbox ~]$ git clone https://github.com/qtc-de/webshell-cli
[qtc@devbox ~]$ cd webshell-cli
[qtc@devbox webshell-cli]$ pip3 install --user -r requirements.txt
[qtc@devbox webshell-cli]$ python3 webshell-cli.py 
usage: webshell-cli.py [-h] [-m] [-f FILE_HISTORY] [-s SHELL] url
webshell-cli.py: error: the following arguments are required: url
```


### Supported Webshells

----

*webshell-cli* only works with webshells that were specifically build for this project. You can
find the supported webshells within the [webshells directory](/webshells/). Currently, the following
server-side technologies are supported:

* [PHP](/webshells/webshell.php)
* [JSP](/webshells/webshell.jsp)
* [ASPX](/webshells/webshell.aspx)

Additionally, the webshells directory contains a [build script](/webshells/build_war.sh) for building
`.war` archives.


### Special Commands

----

*webshell-cli* supports some special commands that can be invoked by using an exclamation
mark as the first character on a command line. Below you can find the list of currently supported
special commands:

*  `!background <cmd>`          execute the specified command in the background
*  `!download <rfile> <lfile>`  download a remote file from the server
*  `!upload <lfile> <rfile>`    upload a local file to the server
*  `!eval <lfile>`              evaluate a local file on the server (only available for php)
*  `!env <var>=<val>`           set an environment variable
*  `!help`                      show this help menu

When using the `!env` command without specifying a variable, it outputs a list containing the currently
set variables. When `!env clear` was specified, all manually added environment variables get deleted.


### Custom Shell Command

----

You can use a custom shell command for each shell by using the `--shell` option. The default shell commands
are `/bin/sh -c` for Unix and `cmd.exe /c` for Windows. How about a `base64` shell? No problem:

```console
[qtc@devbox ~]$ webshell-cli 172.18.0.2/webshell.php --shell base64
[nobody@efd0355fda4c /var/www/html/public]$ /etc/issue
V2VsY29tZSB0byBBbHBpbmUgTGludXggMy4xNQpLZXJuZWwgXHIgb24gYW4gXG0gKFxsKQoK
```


### Command History

----

By default, *webshell-cli* uses the history file `~/.webshell_cli_history` to provide you a command line history
for your latest commands. You can use the `-f` option to specify a different location for storing the history file
or use the `-m` option to use an in-memory command history instead.


### Final Remarks

----

Contributions to this project are always welcome. The [docs](/docs) folder contains a specification that lists
the requirements for webshells to be consumable by *webshell-cli*. Furthermore, the documentation lists some
design decisions, as certain things were not that straight forward to implement.

This project is meant to be used only for *CTF* challenges and educational purposes. As plenty of webshells
are available on the internet and the shells from this repository do not even implement obfuscation or encryption,
they won't be useful for real world attacks anyway.
