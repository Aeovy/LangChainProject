import subprocess
import os
class AgentCoding:
    def __init__(self, workdir:str="AgentCode"):
        self.workpath = os.getcwd()+f"/{workdir}"
        if not os.path.exists(self.workpath):
            try:
                os.makedirs(self.workpath, exist_ok=True)
            except Exception as e:
                raise e
    def __DectctHighRiskCommand(self,Command:list[str]):
        pass
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
        不推荐写入阻塞代码
        """
        try:
            result=subprocess.run(["python3",PythonFilePath], capture_output=True, text=True)
            if result.stderr:
                return result.stderr
            else:
                return result.stdout
        except Exception as e:
            return e
CodeAgent=AgentCoding()