import sublime
import sublime_plugin

import os
import os.path
import subprocess
import tempfile
import re

__PLUGIN_NAME__ = 'P4Explorer'

PERFORCE_PATH_REGEX = r'//[- .\w]+(?:/[- .\w]+)*(?:[#@]\d+)?'
REV_REGEX = re.compile(r'.*(#\d+)$')


class P4Explorer(sublime_plugin.WindowCommand):

    def run(self):
        active_view = self.window.active_view()

        selection = active_view.sel()

        for region in selection:
            if region.empty():
                P4Explorer.logInfo(
                    'No selection, looking for a Perforce path ...')
                region = self.findPerforcePath(region)
                if not region:
                    P4Explorer.logError(
                        'No Perforce path found at current position.')
                    continue

            perforce_path = active_view.substr(region).strip()
            P4Explorer.logInfo('perforce_path - ' + perforce_path)

            tmp_path = self.getTmpFilePath(perforce_path)
            P4Explorer.logInfo('tmp_path - ' + tmp_path)

            if self.fetchPeforceFile(perforce_path, tmp_path):
                self.window.open_file(tmp_path)

    def findPerforcePath(self, region):
        active_view = self.window.active_view()
        start_point = active_view.line(region).begin()

        while True:
            perforce_path = active_view.find(PERFORCE_PATH_REGEX, start_point)
            if not perforce_path or perforce_path.contains(region):
                return perforce_path
            else:
                start_point = perforce_path.end()

    def getTmpFilePath(self, perforcePath):
        tmp_dir = tempfile.gettempdir()
        tmp_file_name = self.getTmpFileName(perforcePath)
        return os.path.abspath(os.path.join(tmp_dir, __PLUGIN_NAME__, tmp_file_name))

    def getTmpFileName(self, perforcePath):
        tmp_file_name = perforcePath

        match = re.match(REV_REGEX, perforcePath)
        if match:
            tmp_file_name = self.flipRevisionExtension(
                perforcePath, match.group(1))
        else:
            head_rev = self.getHeadRevision(perforcePath)
            if head_rev:
                match = re.match(REV_REGEX, head_rev)
                if match:
                    tmp_file_name = self.flipRevisionExtension(
                        head_rev, match.group(1))

        return tmp_file_name.lstrip('/')

    def flipRevisionExtension(self, perforcePath, rev):
        root, ext = os.path.splitext(perforcePath)
        if ext:
            rearranged_ext = rev + ext[:-len(rev)]
            return root + rearranged_ext

        return perforcePath

    def fetchPeforceFile(self, perforcePath, tmpPath):
        if not os.path.isfile(tmpPath):
            perforce_command = 'p4 print -q -o "{0}" "{1}"'.format(
                tmpPath, perforcePath)
            p = subprocess.Popen(perforce_command, stdout=subprocess.PIPE,
                                 stderr=subprocess.PIPE, shell=True)
            stdout, stderr = p.communicate(timeout=60)
            if stderr:
                P4Explorer.logError(stderr.decode())
                return False

        return True

    def getHeadRevision(self, perforcePath):
        perforce_command = 'p4 files -e "{0}"'.format(perforcePath)
        p = subprocess.Popen(perforce_command, stdout=subprocess.PIPE,
                             stderr=subprocess.PIPE, shell=True)
        stdout, stderr = p.communicate(timeout=60)
        if stderr:
            P4Explorer.logError(stderr.decode())
            return None

        if stdout:
            match = re.search(PERFORCE_PATH_REGEX, stdout.decode())
            if match:
                return match.group()

        return None

    @staticmethod
    def logInfo(message):
        P4Explorer.log('Info', message)

    @staticmethod
    def logError(message):
        P4Explorer.log('Error', message)

    @staticmethod
    def log(level, message):
        log_message = "[{0}] {1}: {2}".format(__PLUGIN_NAME__, level, message)
        print(log_message)
        sublime.status_message(log_message)
