from beets.plugins import BeetsPlugin
from beets.autotag.hooks import AlbumInfo, TrackInfo, Distance
from lxml import html
import logging
import urllib
import requests
import re

log = logging.getLogger('beets')

class BeatportError(Exception):
    pass

class BeatportPlugin(BeetsPlugin):

	def __init__(self):
		super(BeatportPlugin, self).__init__()
		
	def track_distance(self, item, track_info):
		dist = Distance()
		if track_info.data_source == 'Beatport':
			dist.add('source', '0.5')
		return dist
	
	def item_candidates(self, item, artist, title):
		query = artist + " " + title
		return self._search(query)

	def _format(self, data_list):
		data_list.pop(0)
		tmp = []
		for i in data_list:
			tmp.append(re.sub(' +', ' ', i.text_content()))
		return [re.sub(r'[\t\n\r]', '', i) for i in tmp]
		
	def _search(self, query):
		track_list = []

		try:
			response = requests.get('http://classic.beatport.com/search?&perPage=30&facets[]=fieldType:track&query=%s' % urllib.quote_plus(query))
		except Exception as e:
			raise BeatportError("Error connection to Beatport: {}".format(e.message))
		if not response:
			raise BeatportError("Error {0.status_code} for '{0.request.path_url}".format(response))

		tree = html.fromstring(response.content)

		HREF   = tree.xpath('/html/body/div[1]/div[5]/div/div[3]/table/tr[*]/td[3]/a/@href')
		TITLE  = tree.xpath('/html/body/div[1]/div[5]/div/div[3]/table/tr[*]/td[3]/a/text()')
		ARTIST = self._format(tree.xpath('/html/body/div[1]/div[5]/div/div[3]/table/tr[*]/td[4]'))
		RMXER  = self._format(tree.xpath('/html/body/div[1]/div[5]/div/div[3]/table/tr[*]/td[5]'))
		LABEL  = self._format(tree.xpath('/html/body/div[1]/div[5]/div/div[3]/table/tr[*]/td[6]'))
		GENRE  = self._format(tree.xpath('/html/body/div[1]/div[5]/div/div[3]/table/tr[*]/td[7]'))
		RLDATE = self._format(tree.xpath('/html/body/div[1]/div[5]/div/div[3]/table/tr[*]/td[8]'))

		for i, value in enumerate(HREF):
			track = TrackInfo(title=unicode(TITLE[i]), artist=unicode(ARTIST[i]), track_id=None)
			track_list.append(track)
		
		return track_list
		
	def _get_track_page_infos(href):
		page = requests.get(href)
		tree = html.fromstring(page.content)

		BPM    = tree.xpath('/html/body/div[1]/div[5]/div[1]/ul[1]/li[5]/div[2]/ul/li[3]/span[2]/text()')
		KEY    = tree.xpath('/html/body/div[1]/div[5]/div[1]/ul[1]/li[5]/div[2]/ul/li[4]/span[2]/span/text()')
		ALBUM  = tree.xpath('/html/body/div[1]/div[5]/div[1]/ul[1]/li[4]/ul/li/span[2]/a/text()')
		LENGTH = tree.xpath('/html/body/div[1]/div[5]/div[1]/ul[1]/li[5]/div[2]/ul/li[1]/span[2]/text()')
		
		return [ALBUM, BPM, KEY, LENGTH]



