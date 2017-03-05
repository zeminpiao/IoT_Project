import os, re

# execute command, and return the output  
def execCmd():  
    
    cmd = "avahi-browse -rtp _http._tcp"
    r = os.popen(cmd)  
    text = r.read()
    print(text)
    pat = "=;[\w-]+;[\w-]+;[\w-]+;Web Site;[\w-]+;[\w-]+.[\w-]+;([\.\d]+);[\d]+;\"/test\""
    IP = re.findall(pat, text)[0]
    print(IP)

if __name__ == "__main__":
    execCmd()
