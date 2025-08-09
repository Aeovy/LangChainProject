import subprocess
import os
import sys
import shlex
from contextlib import contextmanager


class AgentCoding:
    def __init__(self, workdir: str = "SandBox"):
        self.workpath = os.getcwd() + f"/{workdir}"
        self.OSNAME = sys.platform
        if not os.path.exists(self.workpath):
            try:
                os.makedirs(self.workpath, exist_ok=True)
            except Exception as e:
                raise e

    def __DectctHighRiskCommand(self, Command: list[str]):
        pass

    @contextmanager
    def __change_workdir(self, path):
        """临时更改工作目录"""
        old_dir = os.getcwd()
        try:
            os.chdir(path)
            yield
        finally:
            os.chdir(old_dir)

    def __GetTerminalCommand_Python(self, pythonFilePath: str) -> str:
        """
        返回打开终端的命令
        pythonFilePath:python文件的绝对路径或文件名
        """
        CommandList = []
        workdir_quoted = shlex.quote(self.workpath)
        # 多系统支持
        if self.OSNAME == "darwin":
            RunPythonFileCommand = (
                f"cd {workdir_quoted} && uv run {os.path.basename(pythonFilePath)}"
            )
            apple_script_command = (
                f'tell app "Terminal" to do script "{RunPythonFileCommand}"'
            )
            CommandList = ["osascript", "-e", apple_script_command]
            return CommandList
        elif self.OSNAME == "win32":
            return [
                "powershell",
                "-NoExit",
                "-Command",
                f'cd "{self.workpath}"; uv run "{os.path.basename(pythonFilePath)}"',
            ]
        elif self.OSNAME == "":
            pass
        ####

    def CreateFile(self, code: str, filename: str):
        """
        创建成功时,返回创建完成的文件的绝对路径
        """
        try:
            with open(f"{self.workpath}/{filename}", "w") as file:
                file.write(code)
                return {"status": "success", "filepath": f"{self.workpath}/{filename}"}
        except FileNotFoundError:
            os.mkdir(self.workpath)
            return self.CreateFile(code, filename)
        except Exception as e:
            return {"status": "error", "error": str(e)}

    def RunPython(self, PythonFilePath: str, timeout: int = 10) -> dict[str, str]:
        """
        PythonFilePath既可以是绝对路径,也可以只是文件名
        执行没有阻塞代码的程序,默认10秒超时
        """
        with self.__change_workdir(self.workpath):
            try:
                result = subprocess.run(
                    ["uv", "run", PythonFilePath],
                    capture_output=True,
                    text=True,
                    timeout=timeout,
                    encoding="utf-8",
                    errors='replace'
                )
                if result.stderr:
                    return result.stderr
                else:
                    if len(result.stdout) > 0:
                        return {"status": "success", "output": result.stdout}
                    else:
                        return {"status": "success", "output": None}
            except Exception as e:
                return {"status": "error", "error": str(e)}

    def PopenPython(self, PythonFilePath: str):
        """
        执行有阻塞代码的程序
        """
        try:
            process = subprocess.Popen(self.__GetTerminalCommand_Python(PythonFilePath))
            return {"status": "success", "pid": process.pid}
        except Exception as e:
            return {"status": "error", "error": str(e)}

    def PipInstall(self, PackageName: str):
        """
        安装python包
        """
        try:
            with self.__change_workdir(self.workpath):
                result = subprocess.run(
                    ["uv", "add", PackageName], capture_output=True, text=True
                )
                if result.stderr:
                    return result.stderr
                else:
                    if len(result.stdout) > 0:
                        return {"status": "success", "output": result.stdout}
                    else:
                        return {"status": "success", "output": None}
        except Exception as e:
            return {"status": "error", "error": str(e)}

if __name__=="__main__":
    CodeAgent = AgentCoding()
