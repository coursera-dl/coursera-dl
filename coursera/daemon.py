__author__ = 'FinalTheory'


import web
# web.config.debug = False
import threading
import subprocess
from sys import platform
from tempfile import gettempdir, TemporaryFile


log_name = 'Courseradl_log.txt'
Debug = 'win' in platform

urls = (
    '/', 'index',
    '/index', 'index',
    '/delete', 'delete',
)

attr_list = [
    'action',
    'clsname',
    'username',
    'passwd',
    'lang',
    'downloader',
    'overwrite',
    'reverse',
    'fmts',
    'sf',
    'lf',
    'rf'
]


thread_status = {
    0: "Not Started",
    1: "Now Running",
    2: "Successfully Complete",
    3: "Error occured while downloading"
}

class Tools:
    @staticmethod
    def refreshInfo(msg, seconds, url):
        return '%s\n<meta http-equiv="refresh" content="%d; url=%s" />' % (msg, seconds, url)


class workThread(threading.Thread):
    def __init__(self, data, download_dir):
        threading.Thread.__init__(self)
        # The download directory
        self.download_dir = download_dir
        # PIPE object
        self.pipe = None
        # Store the log message
        self.log_fid = TemporaryFile()
        # Record status of current thread
        # 0 for not started, 1 for running,
        # 2 for successfully finished, 3 for error
        self.status = 0
        # Extract all attributes from post data
        for attr in attr_list:
            setattr(self, attr, data.get(attr))

    def getLog(self):
        if self.pipe and self.isAlive():
            if self.pipe.stdout: self.pipe.stdout.flush()
            if self.pipe.stderr: self.pipe.stderr.flush()
        self.log_fid.flush()
        self.log_fid.seek(0)
        return self.log_fid.readlines()

    def run(self):
        self.status = 1
        cmd = []
        cmd.append('python')
        cmd.append('coursera-dl')
        cmd.append('-u')
        cmd.append(self.username)
        cmd.append('-p')
        cmd.append(self.passwd)
        if self.downloader != 'python':
            cmd.append('--%s' % self.downloader)
        cmd.append('--path')
        cmd.append(self.download_dir)
        if self.overwrite == 'yes':
            cmd.append('--overwrite')
        if self.reverse == 'yes':
            cmd.append('--reverse')
        if self.lang != 'en':
            cmd.append('--subtitle')
            cmd.append('"%s"' % self.lang)
        if self.fmts:
            cmd.append('--formats')
            cmd.append('"%s"' % self.fmts)
        if self.sf:
            cmd.append('--section_filter')
            cmd.append('"%s"' % self.sf)
        if self.lf:
            cmd.append('--lecture_filter')
            cmd.append('"%s"' % self.lf)
        if self.rf:
            cmd.append('--resource_filter')
            cmd.append('"%s"' % self.rf)
        cmd.append(self.clsname)
        print ' '.join(cmd)
        if Debug:
            self.status = 2
        else:
            # self.pipe = subprocess.Popen(cmd)
            self.pipe = subprocess.Popen(cmd, stderr=self.log_fid, stdout=self.log_fid)
            return_code = self.pipe.wait()
            if return_code == 0:
                self.status = 2
            else:
                self.status = 3
            # self.log_fid.close()


class daemon:
    def __init__(self):
        self.ThreadPool = []
        # If not specified, all things would be downloaded
        # to TEMP dirs for security reasons
        self.download_dir = gettempdir()

    def set_Parameters(self, port_num, download_dir):
        self.port_num = port_num
        self.download_dir = download_dir

    def add_download(self, data):
        # Check if there are too many threads
        if threading.activeCount() > 20:
            return '<h2 style="color:red">Too many tasks!!!</h2>'
        # Check if the course is already downloading
        for t in self.ThreadPool:
            if t.clsname == data.get('clsname'):
                return '<h2 style="color:red">Current course is already downloading!</h2>'

        # Create a new download thread and then start it
        new_thread = workThread(data, self.download_dir)
        self.ThreadPool.append(new_thread)
        new_thread.start()
        return '<h2 style="color:green">Download task successfully added!</h2>'

    def run_server(self):
        self.app = web.application(urls, globals())
        web.httpserver.runsimple(self.app.wsgifunc(), ("0.0.0.0", int(self.port_num)))


# In debug mode, web.py will load global variable twice,
# so I have to use this trick to avoid this.
if web.config.get('_daemon') is None:
    d = daemon()
    web.config._daemon = d
else:
    d = web.config._daemon


class index:
    def GET(self):
        web.header('content-type', 'text/html')
        return web.template.frender('coursera/index.html')()

    def POST(self):
        web.header('content-type', 'text/html')
        data = web.input()
        # if Debug: print web.data()
        # Try to extract post data
        for attr in attr_list:
            if data.get(attr) is None:
                return Tools.refreshInfo('<h2 style="color:red">%s</h2>'
                                         % ('Attribute "%s" not found!' % attr), 3, '/')
        # Handle this request
        if data['action'] == 'add':
            result = d.add_download(data)
            return Tools.refreshInfo(result, 3, '/')
        elif data['action'] == 'query':
            pos = -1
            for i in range(len(d.ThreadPool)):
                t = d.ThreadPool[i]
                #if t.clsname == data['clsname'] and t.username == data['username'] and t.passwd == data['passwd']:
                if t.clsname == data['clsname']:
                    pos = i
                    break
            # If found this task
            if pos != -1:
                t = d.ThreadPool[pos]
                stat = thread_status.get(t.status, 'Unknown Status')
                page = web.template.frender('coursera/query.html')
                return page(data['clsname'], data['username'], data['passwd'], stat, t.getLog())
            else:
                return Tools.refreshInfo('<h2 style="color:red">Download task not found! '
                                         'Or wrong username/password!</h2>', 3, '/')
        else:
            return Tools.refreshInfo('<h2 style="color:red">Unknown action!</h2>', 3, '/')


class delete:
    def GET(self):
        web.header('content-type', 'text/html')
        return Tools.refreshInfo('<h2 style="color:red">Permission denied!</h2>', 3, '/')

    def POST(self):
        web.header('content-type', 'text/html')
        data = web.input()
        pos = -1
        for i in range(len(d.ThreadPool)):
            t = d.ThreadPool[i]
            if t.clsname == data['clsname'] and t.username == data['username'] and t.passwd == data['passwd']:
                pos = i
                break
        if pos != -1:
            t = d.ThreadPool[pos]
            if t.status == 1:
                if "win" in platform:
                    return Tools.refreshInfo('<h2 style="color:red">Download task is now running!</h2>', 3, '/')
                else:
                    cmd = 'ps aux | grep "%s" | grep -v grep | awk \'{print $2}\' | xargs kill -9' % t.clsname
                    if subprocess.call(cmd, shell=True) != 0:
                        return Tools.refreshInfo('<h2 style="color:red">Failed to kill task!</h2>', 3, '/')
            d.ThreadPool.pop(pos)
            return Tools.refreshInfo('<h2 style="color:blue">Download task removed!</h2>', 3, '/')
        else:
            return Tools.refreshInfo('<h2 style="color:red">Download task not found! '
                                         'Or wrong username/password!</h2>', 3, '/')


def start_daemon(port_num, download_dir=gettempdir()):
    d.set_Parameters(port_num, download_dir)
    d.run_server()


if __name__ == '__main__':
    start_daemon(8082, 'Z:\\')