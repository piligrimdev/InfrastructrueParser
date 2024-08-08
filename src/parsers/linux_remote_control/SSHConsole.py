# -*- coding: utf-8 -*-
import paramiko

# paramiko.common.logging.basicConfig(level=paramiko.common.DEBUG)


class SSHConsole:
    def __init__(self, host: str, user: str, pw: str, p_key: str):
        self.host = host
        self.user = user
        self.pf = pw
        self.key_path = p_key

    def execute_command(self, command: str) -> list[str]:
        key = paramiko.Ed25519Key.from_private_key_file(self.key_path, self.pf)
        with paramiko.SSHClient() as ssh:
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())  # idk
            ssh.connect(self.host, username=self.user, pkey=key)
            return [i.read().decode() for i in ssh.exec_command(command)[1:]]

    def retrieve_file(self, file_path: str, save_path) -> None:
        key = paramiko.Ed25519Key.from_private_key_file(self.key_path, self.pf)
        with paramiko.SSHClient() as ssh:
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ssh.connect(self.host, username=self.user, pkey=key)
            with ssh.open_sftp() as sftp:
                sftp.get(file_path, save_path)


def execute_commands_on_server(console: SSHConsole, commands: list[str]):
    output = []
    try:
        for com in commands:
            output.append(tuple(console.execute_command(com)))
    except Exception as e:
        print(e)
    finally:
        return output


def retrieve_file_on_server(console: SSHConsole, file_on_server: str, path_to_save: str) -> None:
    try:
        console.retrieve_file(file_on_server, path_to_save)
    except Exception as e:
        print(e)
