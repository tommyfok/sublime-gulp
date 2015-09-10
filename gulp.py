import sublime, sublime_plugin, subprocess, re, os

class EventListener(sublime_plugin.EventListener):
    # 每个类都有个__init__方法
    # 感觉是构造函数来的
    def __init__(self):
        self.done = False
        self.count = 0
        self.cp = None
        self.tasks = ['build-all','build','gopro','godev','golocal']

    # 成员方法的首参是self，代表类本身
    # 调用时只需从第二个参数开始传入
    def on_pre_save(self, view):
        self.done = False
        self.count = 0

    def rightAfterSave(self, view):
        path = self.getGulpRoot(sublime.View.file_name(view))
        if not self.done:
            # 120 * 250 = 10000 = 30秒
            if self.count > 120:
                if not self.cp == None:
                    self.cp.kill()
                    # 匿名函数：lambda: ...
                    sublime.set_timeout(lambda: sublime.status_message('命令执行失败，子进程被kill'), 125)
                else:
                    sublime.status_message('命令执行失败')
                self.count = 0
            else:
                sublime.set_timeout(lambda: self.rightAfterSave(view), 250)
                self.count = self.count + 1
        else:
            if self.gulpTask == '':
                sublime.status_message('没有执行任何gulp任务')
            else:
                sublime.status_message('成功在' + path + '运行 gulp ' + self.gulpTask + ' | 耗时 ' + str(self.count * 250 / 1000) + 's')

    def on_post_save_async(self, view):
        # sublime将会打开子进程A，异步执行以下操作
        def execGulpTask(index):
            if not index == -1:
                self.gulpTask = self.tasks[index]
                sublime.status_message('正在执行gulp ' + self.gulpTask + '任务')
                # 打开A的子进程B
                self.cp = subprocess.Popen(['gulp', self.gulpTask], shell=True, cwd=path, stdout=subprocess.PIPE)
                # 阻塞A，等待B
                self.cp.wait()
            else:
                self.gulpTask = ''
            self.done = True
        path = self.getGulpRoot(sublime.View.file_name(view))
        if not path:
            sublime.status_message('非Gulp项目，无需执行Gulp命令')
        else:
            self.rightAfterSave(view)
            gflines = open(path + '/gulpfile.js', encoding='utf8').readlines()
            arr = []
            for line in gflines:
                result = re.match(r".*task.'([^']*)'", line)
                if result:
                    arr.append(result.group(1))
            self.tasks = arr

            sublime.Window.show_quick_panel(sublime.active_window(), self.tasks, execGulpTask)
            # sublime.Window.show_input_panel(sublime.active_window(), '请输入要执行的gulp命令', 'build-all', execGulpTask, None, None)

    def getGulpRoot(self, path):
        # os.path.isdir 判断是否目录
        # os.path.dirname 返回当前路径所在的目录
        #   1.如果路径是文件，则返回文件所在的目录
        #   2.如果路径是目录，则返回上一级目录
        #   3.如果路径是根目录，则返回其本身
        _dir = os.path.isdir(path) and path or os.path.dirname(path)
        # os.listdir 列出当前目录下的所有文件
        # a in b 判断a是否在数组b内
        if 'gulpfile.js' in os.listdir(_dir):
            return _dir
        else:
            # 如果到达根目录，则表明不包含gulpfile.js，无法执行gulp命令
            if _dir == os.path.dirname(_dir):
                return False
            else:
                # 递归处理上一级目录
                return self.getGulpRoot(os.path.dirname(_dir))
