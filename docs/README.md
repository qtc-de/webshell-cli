### webshell-cli Documentation

----

This document contains some development notes about *webshell-cli*. If you are looking
for the specification that webshells need to implement for being compatible with *webshell-cli*,
read the [specification.md](./specification.md) document.


### Command Execution

----

The purpose of a webshell is to obtain a user specified command and to execute it on the application
server. One challenge for the webshell is, that the command to execute is passed as a plain string, but
the shell should handle the contained command line arguments correctly. Depending on the type of the
webshell (server-side technology) this can be more ore less simple.

The preferred solution and initial implementation of *webshell-cli* was using functions that accept
the operating system command in form of an array. This has the advantage that each argument is passed
as a separate array element and there is no need to worry about escaping special shell characters.
Unfortunately, only *JSP* provides this feature with a sufficient backward compatibility. Recent
versions of *PHP* also allow an array for specifying the operating system command when using
[proc_open](https://www.php.net/manual/de/function.proc-open.php), but this is only available for
`PHP >= v7.4.0` and therefore not suitable for a webshell. For *ASPX*, we have basically the same
situation. `System.Diagnostics.Process` generally supports the usage of `ArgumentList`, but not
for `.NET Framework v4.X`.

After noticing these incompatibilities, we changed *webshell-cli* to use the following approach:

* The desired shell command (`/bin/sh -c`, `cmd.exe /c` or user specified) is split on spaces
  and wrapped into a sequence like: `/bin/sh<@:SEP:@>-c<@:SEP:@>echo "This is an Example."`.
* On the server side, the command is split on the `<@:SEP:@>` markers and stored into an array.
* Now the further execution depends on the type of the webshell:
  * Within the *JSP* webshell, we pass the array directly to `ProcessBuilder`
  * Within the *PHP* webshell, we just join the array again with spaces and use `escapeshellarg`
    on the last array item (the actual command to execute).
  * Within the *ASPX* webshell, we use the first array element as the actual program started
    by `System.Diagnostics.Process`. The rest of the array items are joined with spaces and
    passed as argument string.


### Status Codes

----

*webshell-cli* uses status codes in some situations to indicate success or error on the server side.
A probably confusing implementation detail is, that some errors still cause a positive status code.
One example for this situation is, when you attempt to change into an invalid directory. In this case,
*webshell-cli* compatible webshells return the *HTTP* status code `202`.

This was implemented that way, because application servers like *IIS* filter the content of server
responses in case of *HTTP* status codes that indicate an error. Therefore, at least for *ASPX*, we
need to use positive status codes to get our error messages transported.

In general, *webshell-cli* treats each non `200` status code as an error. Webshells can freely decide
which status they want to use to report errors. Only for certain events, like a non accessible directory,
a certain status code is required.


### Changing cwd and env

----

When it comes to changing the current working directory or the processes environment variables, there
are some differences, mainly between *PHP* and *ASPX* or *JSP*. Within the *PHP* webshell, we change
the current working directory and the environment right at the beginning using the `chdir` and `putenv`
functions.

First implementations used a similar approach for *ASPX* using the corresponding `Directory.SetCurrentDirectory`
and `Environment.SetEnvironmentVariable` functions. The problem in the case of *ASPX* is, that these
changes are persistent. Applying persistent configuration changes to the webapplication when using a
webshell is usually not desired and we changed the general approach.

Since *PHP* applies the changes only for the current execution context, we kept the `chdir` and `putenv`
function for *PHP*, which are always applied for each action. The *ASPX* and *JSP* webshells, on the other
hand, do not change the *cwd* or *env* of the process, but only use the specified directory and environment
variables when executing a command. This works by passing the *cwd* or *env* within the corresponding arguments
for `ProcessBuilder` or `System.Diagnostics.Process`.
