#!/usr/bin/env python2.7
# -*- coding: utf-8 -*-

import urllib2
import time
import argparse
import ConfigParser
import os
import logging

def as_utf8(string):
	return u'%s' % unicode(string, 'utf-8')

def as_ascii(string):
	return '%s' % string.decode('ascii', 'ignore')

def format_date(time_value):
	if (config.has_section('settings') and config.has_option('settings', 'date_pattern')):
		pattern = config.get('settings', 'date_pattern', '%Y-%m-%d_%H-%M-%S')
	else:
		pattern = '%Y-%m-%d_%H-%M-%S'

	if (type(time_value).__name__ == 'float'):
		time_value = time.localtime(time_value)
	elif (type(time_value).__name__ == 'struct_time'):
		pass
	else:
		raise TypeError('time_value has to be a struct_time or a float. "%s" given.' % time_value)
	return time.strftime(pattern, time_value)

class Recorder:
	log = None

	def __init__(self, url, show_title, episode_title = ''):
		logging.basicConfig(
			filename = os.path.expanduser('~/.capturadio/log'),
			level = logging.DEBUG,
		)
		self.log = logging.getLogger('capturadio')

		self.stream_url = stream_url
		self.episode_title = episode_title
		self.show_title = show_title
		self.destination = os.getcwd()
		self.station_name = None
		self.station_logo = None
		self.file_name = None
		self.start_time = None

	def set_destination(self, destination):
		if (destination is not None and os.path.exists(destination) and os.path.isdir(destination)):
			if (destination.startswith(u'./')):
			    destination = destination[2:]
			if (not os.path.isabs(destination)):
			    destination = os.path.join(os.getcwd(), destination)

			self.destination = as_ascii(destination)

	def set_station_details(self, name, logo = None):
		self.station_name = name
		self.station_logo = logo

	def capture(self, duration):
		self.log.info(u'capture "%s" from "%s" for %s seconds to %s' % \
				(self.episode_title, self.station_name, duration, self.destination))
		import tempfile
		self.start_time = time.time()
		self.file_name = u"%s/capturadio_%s.mp3" % (tempfile.gettempdir(), os.getpid())
		self._write_stream_to_file()
		self._copy_file_to_destination()
		self._add_metadata()

	def _write_stream_to_file(self):
		not_ready = True
		try:
			file = open(self.file_name, 'w+b')
			stream = urllib2.urlopen(self.stream_url);
			while not_ready:
				file.write(stream.read(10240));
				if ((time.time() - self.start_time) > duration):
					not_ready = False
			file.close
		except Exception as e:
			mesage= "Could not complete capturing, because an exception occured.", e
			self.log.error(message, e)
			print message
			os.remove(self.file_name)
			self.file_name = None

	def _copy_file_to_destination(self):
		import shutil, re

		time_string = format_date(time.localtime(self.start_time))
		target_file = u"%s/%s/%s/%s_%s.mp3" % \
			(self.destination,
			 as_ascii(self.station_name if self.station_name is not None else self.station_nick),
			 as_ascii(self.show_title),
			 as_ascii(self.episode_title),
			 time_string)
		target_file = re.compile(u'[^\w\d._/ -]').sub('', target_file)
		if (not os.path.isdir(os.path.dirname(target_file))):
			os.makedirs(os.path.dirname(target_file))
		shutil.copy2(self.file_name, target_file)

		self.file_name = target_file

	def _add_metadata(self):
		if self.file_name is None:
			raise "file_name is not set - you cannot add metadata to None"

		from mutagen.mp3 import MP3
		import mutagen.id3
		show_title = as_utf8(self.show_title)
		title = as_utf8(self.episode_title)
		station_name = as_utf8(self.station_name)
		date = time.strftime('%Y', time.localtime(self.start_time))
		comment = u'Show: %s\nEpisode: %s\nCopyright: %s %s' % (show_title, title, date, station_name)

		audio = MP3(self.file_name)
		# See http://www.id3.org/id3v2.3.0 for details about the ID3 tags
		audio["TIT2"] = mutagen.id3.TIT2(encoding=2, text=[title])
		audio["TDRC"] = mutagen.id3.TDRC(encoding=2, text=[format_date(self.start_time)])
		audio["TCON"] = mutagen.id3.TCON(encoding=2, text=[u'Podcast'])
		audio["TALB"] = mutagen.id3.TALB(encoding=2, text=[show_title])
		audio["TLEN"] = mutagen.id3.TLEN(encoding=2, text=[duration * 1000])
		audio["TPE1"] = mutagen.id3.TPE1(encoding=2, text=[station_name])
		audio["TCOP"] = mutagen.id3.TCOP(encoding=2, text=[station_name])
		audio["COMM"] = mutagen.id3.COMM(encoding=2, text=[comment])
		self._add_logo(audio)
		audio.save()

	def _add_logo(self, audio):
		from mutagen.id3 import APIC
		# APIC part taken from http://mamu.backmeister.name/praxis-tipps/pythonmutagen-audiodateien-mit-bildern-versehen/
		if self.station_logo is not None:
			request = urllib2.Request(self.station_logo)
			request.get_method = lambda : 'HEAD'
			try:
				response = urllib2.urlopen(request)
				logo_type = response.info().gettype()

				if logo_type in ['image/jpeg', 'image/png']:
					img_data  = urllib2.urlopen(self.station_logo).read()
					img = APIC(
						encoding = 3, # 3 is for utf-8
						mime = logo_type,
						type = 3, # 3 is for the cover image
						desc = u'Station logo',
						data = img_data
					)
					audio.tags.add(img)
			except urllib2.HTTPError, e:
				mesage= "Error during capturing"
				self.log.error(message, e)
				print message, e


if __name__ == "__main__":

	config = ConfigParser.ConfigParser()
	config.read([os.path.expanduser('~/.capturadio/capturadiorc'), os.path.expanduser('~/.capturadiorc')])

	parser = argparse.ArgumentParser(
		description='Capture internet radio programs broadcasted in mp3 encoding format.',
		epilog = "Here is a list of defined radio stations: %s" % config.options('stations')
	)
	parser.add_argument('-l', metavar='length', type=int, required=True, help='Length of recording in seconds')
	parser.add_argument('-s', metavar='station', required=True, help='Name of the station, defined in ~/.capturadio/capturadiorc.')
	parser.add_argument('-b', metavar='broadcast', required=True, help='Title of the broadcast')
	parser.add_argument('-t', metavar='title', required=False, help='Title of the recording')
	parser.add_argument('-d', metavar='destination', required=False, help='Destination directory')

	args = parser.parse_args()

	duration = args.l
	if (duration < 1):
	    print "Length of '%d' is not a valid recording duration. Use a value greater 1." % duration
	    exit(1)

	station = args.s
	if (not config.has_option('stations', station)):
	    print "Station '%s' is unknown. Use one of these: %s." % (station, config.options('stations'))
	    exit(1)
	else:
		stream_url = config.get('stations', station)

	show_title = args.b
	title = args.t if (args.t is not None) else show_title

	if args.d is not None:
		destination = os.path.expanduser(args.d)
	elif(config.has_section('settings') and config.has_option('settings', 'destination')):
		destination = os.path.expanduser(config.get('settings', 'destination'))
	else:
		destination = os.getcwd()

	recorder = Recorder(url = stream_url, show_title = show_title, episode_title = title)
	recorder.set_destination(destination)


	if (config.has_section(station)):
		station_name = station_logo = None
		if (config.has_option(station, 'name')):
			station_name = config.get(station, 'name')
		if (config.has_option(station, 'logo')):
			station_logo = config.get(station, 'logo')
		recorder.set_station_details(name = station_name, logo = station_logo)

	recorder.capture(duration)
