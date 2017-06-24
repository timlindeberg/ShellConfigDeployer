# Shell Configuration Deployer (SCD)
A python program to deploy shell configuration to remote servers. 
The program can be used to automatically deploy your shell configuration to
remote hosts before sshing in to them. This way you can always use your
desired shell configuration no matter where you are.

SCD keeps track of which servers have correct shell configuration by keeping
track of the time of deployment as well as a list of programs that have been
installed. Any files that have since changed or been added will be redeployed
to the server. It can not handle removal of files or programs.

# Usage
Use scd on the command line to deploy your configuration to the desired host:

`scd -p vagrant -P 2222 --verbose 127.0.0.1`

Use ~/.scd/config to specify
what programs should be installed on the remote server and what files should
be deployed. Example:
```json
{
    "username": "vagrant",
    "install_method": "apt-get",
    "server": "127.0.0.1",
    "port": 2222,
    "ignore_files": [
        ".gitignore",
        ".git",
        ".DS_Store"
    ],
    "files": [
        ".oh-my-zsh",
        ".zshrc",
        ".gitconfig"
    ],
    "programs": [
        "zsh",
        "tree"
    ]
}
```
This configuration will deploy the folder .oh-my-zsh and the files .zshrc and
.gitconfig placed in ~ on to the remote server and install zsh and tree.
It will ignore .git folders and .DS_Store files and sign on to the server using
the user 'vagrant' and install programs using apt-get. Server and port can be
specified in the configuration but is normally given as a command line
argument.
