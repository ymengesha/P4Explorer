import sublime
import sublime_plugin

import os
import os.path
import subprocess
import tempfile

__PLUGIN_NAME__='P4Explorer'

class P4Explorer(sublime_plugin.WindowCommand):
	def run(self):
		active_view = self.window.active_view()

		selection = active_view.sel()

		for region in selection:
			if region.empty():
				P4Explorer.log('Info', 'Region is empty.')
				# TO-DO: consider detection of Perforce paths when there is no selection
				P4Explorer.log('Info', active_view.substr(active_view.word(region)))
				continue
			else:
				perforce_path = active_view.substr(region).strip()

			# TO-DO: consider doing sanity checks on the selected region
			tmp_path = self.getTmpFilePath(perforce_path)

			if self.fetchPeforceFile(perforce_path, tmp_path):
				self.window.open_file(tmp_path)
			# TO-DO: maybe consider syntax setting for the opened file

	def getTmpFilePath(self, perforcePath):
		tmp_dir = tempfile.gettempdir()
		# TO-DO: consider the path extension of the tmp file ?
		tmp_file_name = perforcePath.lstrip('/')
		return os.path.abspath(os.path.join(tmp_dir, __PLUGIN_NAME__, tmp_file_name))

	def fetchPeforceFile(self, perforcePath, tmpPath):
		perforce_command = 'p4 print -q -o {0} {1}'.format(tmpPath, perforcePath)

		if not os.path.isfile(tmpPath):
			p = subprocess.Popen(perforce_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
			stdout, stderr = p.communicate(timeout=120)
			if(stderr):
				P4Explorer.log('Error', stderr)
				return False
		return True

	@staticmethod
	def log(level, message):
		log_message = "[{0}] {1}: {2}".format(__PLUGIN_NAME__, level, message)
		print(log_message)
		sublime.status_message(log_message)




