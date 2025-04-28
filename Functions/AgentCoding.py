import subprocess
import os
import sys
import shlex 
class AgentCoding:
    def __init__(self, workdir:str="AgentCode"):
        self.workpath = os.getcwd()+f"/{workdir}"
        self.OSNAME = sys.platform
        if not os.path.exists(self.workpath):
            try:
                os.makedirs(self.workpath, exist_ok=True)
            except Exception as e:
                raise e
    def __DectctHighRiskCommand__(self,Command:list[str]):
        pass
    def __GetTerminalCommand_Python__(self,pythonFilePath:str)->str:
        """
        返回打开终端的命令
        pythonFilePath:python文件的绝对路径
        """
        #多系统支持
        if self.OSNAME != "darwin":
            pass
        elif self.OSNAME == "":
            pass
        elif self.OSNAME == "":
            pass
        ####
        RunPythonFileCommand=f"python3 {pythonFilePath}"
        apple_script_command = f'tell app "Terminal" to do script "{RunPythonFileCommand}"'
        CommandList=["osascript", "-e", apple_script_command]
        return CommandList
    def CreateFile(self,code:str,filename:str):
        """
        创建成功时,返回创建完成的文件的绝对路径
        """
        try:
            with open(f"{self.workpath}/{filename}", "w") as file:
                file.write(code)
                return {"filepath":f"{self.workpath}/{filename}"}
        except FileNotFoundError:
            os.mkdir(self.workpath)
            return self.CreateFile(code,filename,self.workpath)
        except Exception as e:
            return e
    def RunPython(self,PythonFilePath:str):
        """
        执行没有阻塞代码的程序
        """
        try:
            result=subprocess.run(["python3",PythonFilePath], capture_output=True, text=True)
            if result.stderr:
                return result.stderr
            else:
                if(len(result.stdout)>0):
                    return result.stdout
                else:
                    return "程序执行成功,但没有输出"
        except Exception as e:
            return e
    def PopenPython(self,PythonFilePath:str):
        """
        执行有阻塞代码的程序
        """
        try:
            process=subprocess.Popen(self.__GetTerminalCommand_Python__(PythonFilePath))
        except Exception as e:
            return e
        
CodeAgent=AgentCoding()