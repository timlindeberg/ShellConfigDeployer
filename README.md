# Shell Configuration Deployer (SCD)
A Python program to deploy shell configuration to remote servers. 
The program can be used to automatically deploy your shell configuration to
remote hosts before sshing in to them. This way you can always use your
desired shell configuration no matter where you are. See sshops.sh for an 
example of how it can be used.

SCD keeps track of which servers have correct shell configuration by keeping
track of the time of deployment as well as a list of programs that have been
installed. Any files that have since changed or been added will be redeployed
to the server. It can not handle removal of files or programs.

## Usage
Use scd on the command line to deploy your configuration to the desired host:

`scd -p vagrant -P 2222 --verbose 127.0.0.1`

Use ~/.scd/config to specify
what programs should be installed on the remote server and what files should
be deployed. Example:
```json
{
    "user": "vagrant",
    "shell": "zsh",
    "ignored_files": [
        ".git",
        ".DS_Store"
    ],
    "files": [
        ".oh-my-zsh",
        ".zshrc",
        ".gitconfig"
    ],
    "programs": [
        "unzip",
        "tree"
    ]
}
```

This configuration will deploy the folder `.oh-my-zsh` and the files `.zshrc` 
and `.gitconfig` placed in ~ on to the remote host and install `unzip` and 
`tree`. It will ignore `.git` folders and `.DS_Store` files and sign on to the
server using the user `vagrant` and install programs using `apt-get`.
It will also install `zsh` and use it as the default login shell for the user.

##### NOTE:

Not all Unix systems come with `unzip` already installed. `unzip` is needed by SCD
to deploy the configuration files. By adding `unzip` to the programs list you can
make sure that it is installed before deploying the files.

## Configuration options

#### "shell"
Specifies a shell to use on the remote server. If specified, the selected shell
will be installed together with the other specified programs and the default
login shell will be changed to this shell. 

#### "programs"
Specifies a list of program to install on the remote host.

#### "files"
Specifies a list of files and directories to deploy to the remote host. The
files are relative to the home folder and will be deployed to the home folder
of the selected user on the remote host. Example:

`"files": [ ".oh-my-zsh" ]`

Will deploy the folder `~/.oh-my-zsh` to `/home/<USER>/.oh-my-zsh` on the
remote host.

#### "ignored_files"
Specifies a list of files and directories that will be ignored when looking
for files to deploy.

#### "user"
Selects which user to authenticate against the host with. Can also be specified
with the flag `--user` (`-u) if you use different user names for different hosts.
The user needs sudo rights in order to install programs.

#### "host"
Selects which host to deploy the configuration to. Normally this would be given
as a command line argument but if you usually connect to the same host you can 
specify it in the config file.

#### "port"
Selects which port to connect through. Can also be specified using the flags 
`--port` (`-P). Defaults to 22.
