### webshell-cli Specification

----

This document specifies the requirements a webshell needs to implement to be compatible
with *webshell-cli*.


### chdir

----

Requests dispatched by *webshell-cli* can generally contain the `chdir` parameter. If the
parameter was specified, it contains a base64 encoded file system path. Webshells need to
verify whether this path is accessible and return a `202` status code if this is not the
case. The corresponding *HTTP* response should contain a base64 encoded reason, why the
change was not possible or at least a generic error message.


### b64_env

----

Requests dispatched by *webshell-cli* can generally contain the `b64_env` parameter. If the
parameter was specified, it contains base64 encoded environment variable pairs, each separated
by `:`. The pairs itself are of the format `key=value`.


### Responses

----

*HTTP* responses for *webshell-cli* are usually base64 encoded. If multiple values need to be
returned, their base64 contents are separated by a colon. Each successful server response should
contain the currently active path as the last item. This should be the path that results after
the `chdir` parameter was applied. This is used to get the actual names of client specified
paths like: `.`. The server response should return the resolved path in this case.


### Actions

----

*webshell-cli* uses the `action` parameter to instruct the webshell what kind of operation
it should perform. The action is passed as a plain string and does not need to be specified.
The following values for the `action` parameter are possible:

#### init

Available parameters:

* `action` - set to `init`

The `init` action is used by *webshell-cli* to obtain some general information about the application
server. The webshell needs to respond with the following base64 encoded items, all separated by a
colon:

* The directory separator used by the system
* The webshell type (e.g. `PHP` or `JSP`)
* The associated user name of the current process
* The hostname of the application server

#### cmd

Available parameters:

* `action` - set to `cmd`
* `b64_cmd` - contains the base64 encoded command
* `back` - boolean. Specifies whether the command is executed as background command
* `chdir` - directory to execute the command in
* `b64_env` - environment to use during the command execution

The `cmd` action is specified together with the `b64_cmd` parameter, which contains a base64 encoded
command that should be executed. During execution, the webshell should respect the current `chdir` and
`b64_env` settings. The output of the command should be returned as base64.

#### eval

Available parameters:

* `action` - set to `eval`
* `chdir` - directory to evaluate in
* `b64_env` - environment to use during evaluation
* `b64_upload` - content to evaluate on the server side

If the `eval` action was used, the request also contains the `b64_upload` parameter that contains the
contents of a file that should be evaluated. Whether this is possible depends on the server-side
webshell technology. So far, this function is only implemented for the *PHP* webshell. This action should
return no response (apart from the *cwd* response mentioned above).

#### upload

Available parameters:

* `action` - set to `upload`
* `chdir` - current directory specification
* `b64_orig` - the original filename of the file being uploaded
* `b64_upload` - the file content to be uploaded
* `b64_filename` - the filename to upload to

When the `upload` action is used, the parameter `b64_upload` contains the base64 encoded contents of a
file that should be uploaded. The parameter `b64_filename` contains a base64 encoded desired filename,
where the file should be saved. If the targeted filename is a directory, webshells should use the
`b64_orig` parameter that contains the base64 encoded original name of the file to upload. The webshell
should save the file under this name in the directory specified by `b64_filename`. This action should
return no response (apart from the *cwd* response mentioned above).

#### download

Available parameters:

* `action` - set to `download`
* `chdir` - current directory specification
* `b64_filename` - the filename to download

When the `download` action is used, the parameter `b64_filename` contains the base64 encoded name
of a file that should be downloaded. The server should simply return the content of the file as
base64.
