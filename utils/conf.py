# import the necessary packages
from json_minify import json_minify
import json

"""
Original Attribution:

PyImageSearch.com
My first exposure to this class was through the following blog post:
https://www.pyimagesearch.com/2019/03/25/building-a-raspberry-pi-security-camera-with-opencv/

I have extended this original implementation to take either a single confPath or a list of confPath.
Also added a keys() method.


"""

class Conf:
	def __init__(self, confPath):
		"""

		:param confPath: either a single path or a list of paths
		:type confPath:
		"""
		if isinstance(confPath, list):
			for cp in confPath:
				# load and store the configuration and update the object's dictionary
				conf = json.loads(json_minify(open(cp).read()))
				self.__dict__.update(conf)
		else:
			# load and store the configuration and update the object's dictionary
			conf = json.loads(json_minify(open(confPath).read()))
			self.__dict__.update(conf)

	def __getitem__(self, k):
		# return the value associated with the supplied key
		return self.__dict__.get(k, None)

	def keys(self):
		return self.__dict__.keys()

	def to_dict(self):
		return self.__dict__