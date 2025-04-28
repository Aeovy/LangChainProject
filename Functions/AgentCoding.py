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
                return {"status":"success","filepath":f"{self.workpath}/{filename}"}
        except FileNotFoundError:
            os.mkdir(self.workpath)
            return self.CreateFile(code,filename)
        except Exception as e:
            return {"status":"error","error":str(e)}
    def RunPython(self,PythonFilePath:str):
        """
        执行没有阻塞代码的程序,10秒超时
        """
        os.chdir(self.workpath)
        try:
            result=subprocess.run(["python3",PythonFilePath], capture_output=True, text=True,timeout=10)
            if result.stderr:
                return result.stderr
            else:
                if(len(result.stdout)>0):
                    return {"status":"success","output":result.stdout}
                else:
                    return {"status":"success","output":None}
        except Exception as e:
            return {"status":"error","error":str(e)}
    def PopenPython(self,PythonFilePath:str):
        """
        执行有阻塞代码的程序
        """
        os.chdir(self.workpath)
        try:
            process=subprocess.Popen(self.__GetTerminalCommand_Python__(PythonFilePath))
            return {"status":"success","pid":process.pid}
        except Exception as e:
            return {"status":"error","error":str(e)}
        
CodeAgent=AgentCoding()