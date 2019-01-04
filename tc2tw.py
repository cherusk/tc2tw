#!/usr/bin/env python

import xml.etree.ElementTree as ET
import collections as cols
import argparse
import subprocess
import datetime


class TW(object):
    def __init__(self, args):
        self.core_cmd = "%s add" % args.tw_path

    def pseudo_API(self, task):

        def compile_due(task):
            fmt = "due:%s"
            t = task.get('duedate')
            if t:
                t = datetime.datetime.strptime(t, '%Y-%m-%d %H:%M:%S')
                t = t.strftime('%Y-%m-%dT%H:%M:%S')
                return fmt % (t)
            else:
                return ""

        def compile_project(task):
            fmt = "project:%s"
            _project = task.get('project')
            _category = task.get('category')

            if _category:
                fmt = fmt % (_category)

            if _project:
                if _category:
                    fmt = fmt + ".%s"

                return fmt % _project
            else:
                return " "

        def compile_content(task):
            content = u'\"%s \n %s\"'
            _task = task.get('subject')
            _description = task.find('description')
            if not _task:
                raise RuntimeError("Task Content Inconsistency")

            if _description is not None:
                content = content % (_task,
                                     _description.text.encode('utf8',
                                                              'replace'))
                return content
            else:
                return "\'%s\'" % (_task)

        _compilers = [str(f(task)) for f in [compile_project,
                                             compile_due,
                                             compile_content]]
        tw_args = " ".join(_compilers)

        return "%s %s" % (self.core_cmd, tw_args)

    def do_import(self, task):
        cmd = self.pseudo_API(task)
        self.run(cmd)

    def run(self, cmd):
        p_exec = subprocess.Popen("%s" % (cmd),
                                  stdout=subprocess.PIPE,
                                  stderr=subprocess.PIPE,
                                  shell=True)
        out, err = p_exec.communicate()

        if p_exec.returncode != 0:
            raise RuntimeError("taskwarrior failure: CMD{%s}  ERR {%s}" % (cmd, err))


class TC(cols.Iterable):

    _data = []

    def __init__(self, args):
        self.state = ET.parse(args.tc_file)
        self.flatten_state()

    def __recursing_categories(self, parent, children, prefix=""):
        fmt = "%s%s"
        if prefix:
            fmt = "%s.%s"

        name = fmt % (prefix, parent.get('subject'))

        categorized_tasks = parent.get('categorizables')
        if categorized_tasks:
            map_shard = {task_id: name for
                         task_id in
                         categorized_tasks.split(' ')}

            self._category_inference_map = dict(self._category_inference_map,
                                                **map_shard)

        for child_category in children:
            self.__recursing_categories(child_category,
                                        child_category.findall("category"),
                                        prefix=name)

        return

    def __recursing_tasks(self, parent, children, prefix=""):
        fmt = "%s%s"
        if prefix:
            fmt = "%s.%s"

        _completed = parent.get('percentageComplete')
        if _completed and int(_completed) == 100:
            return

        full_name = fmt % (prefix, parent.get('subject'))

        _id = parent.get('id')
        category = None
        try:
            category = self._category_inference_map[_id]
            parent.set('category', category)
        except KeyError:
            pass

        if not len(children):
            parent.set('project', prefix)
            self._data.append(parent)
            return
        else:
            for child_task in children:
                self.__recursing_tasks(child_task,
                                       child_task.findall("task"),
                                       prefix=full_name)

    def flatten_state(self):
        """ For becoming iterable more conveniently """

        self._category_inference_map = {}

        for root_category in self.state.findall("category"):
            self.__recursing_categories(root_category,
                                        root_category.findall("category"))

        for root_task in self.state.findall("task"):
            self.__recursing_tasks(root_task,
                                   root_task.findall("task"))

    def __iter__(self):
        for x in self._data:
            yield x


def build_args():
    parser = argparse.ArgumentParser(description="Converter for TaskCoach to Taskwarrior state")
    parser.add_argument('-i', '--tc_file', help='TaskCoach state file')
    parser.add_argument('-t', '--tw_path',
                        help='Taskwarrior binary to use',
                        default="/usr/bin/task")
    args = parser.parse_args()

    return args

if __name__ == "__main__":
    args = build_args()

    taskwarrior = TW(args)
    taskcoach = TC(args)
    for task in taskcoach:
        taskwarrior.do_import(task)
