# -*- coding: utf-8 -*-
import webapp2,re,json,logging
from google.appengine.api import urlfetch

class TVQuery(webapp2.RequestHandler):
    def handle_result(rpc):
        result = rpc.get_result()
    def get(self):
        obj = {'googlevideos':[]}
        url = "http://search.lib.virginia.edu/catalog.json?f%5Bformat_facet%5D%5B%5D=Online&f%5Bformat_facet%5D%5B%5D=Video&f%5Bformat_facet%5D%5B%5D=Streaming+Video&facet.limit=500"
        resp = urlfetch.fetch(url,deadline=60).content
        catlist = json.loads(resp)['facet_counts']['facet_fields']['digital_collection_facet']
        categories = dict(zip(catlist[0::2], catlist[1::2]))
        temp = {}

        def handle_result(rpc):
            result = rpc.get_result()
            resultset = json.loads(result.content)['response']['docs']
            for doc in resultset:
                for coll in doc['digital_collection_facet']:
                    if coll in temp:
                        kalturaurl = doc['url_display'][0]
                        kalturainfo = {}
                        if ('uiconf' in kalturaurl):
                            m = re.search(".*/wid/_(.*)/uiconf_id/(.*)/entry_id/(.*)", kalturaurl)
                            kalturainfo = {'wid':m.group(1),'uiconfid':m.group(2),'entryid':m.group(3),
                                           'card':'http://cdn.kaltura.com/p/0/thumbnail/entry_id/' + m.group(3) + '/width/80/height/80/type/1/quality/72'}
                        else:
                            m = re.search(".*/wid/_(.*)/entry_id/(.*)\|\|.*", kalturaurl)
                            kalturainfo = {'wid':m.group(1),'entryid':m.group(2),
                                           'card':'http://cdn.kaltura.com/p/0/thumbnail/entry_id/' + m.group(2) + '/width/80/height/80/type/1/quality/72'}
                        item = {'description':doc['date_coverage_display'][0],
                                'sources':['foo.mp4'],
                                'background':'bg.jpg',
                                'title':doc['title_display'][0],
                                'studio':doc['source_facet'][0]}
                        item.update(kalturainfo)
                        temp[coll]['videos'].append(item)

        # Use a helper function to define the scope of the callback.
        def create_callback(rpc):
            return lambda: handle_result(rpc)

        rpcs = []
        #for url in urls:
        for cat, count in categories.iteritems():
            temp[cat] = {"category":cat,"videos":[]}
            rpc = urlfetch.create_rpc()
            rpc.callback = create_callback(rpc)
            url = "http://search.lib.virginia.edu/catalog.json?f%5Bdigital_collection_facet%5D%5B%5D=" 
            url += cat.replace(' ','+')  
            url += "&f%5Bformat_facet%5D%5B%5D=Online&f%5Bformat_facet%5D%5B%5D=Video&f%5Bformat_facet%5D%5B%5D=Streaming+Video&facet.limit=500&search_field=keyword&sort=score+desc%2C+year_multisort_i+desc"
            urlfetch.make_fetch_call(rpc, url)
            rpcs.append(rpc)

        # ...

        # Finish all RPCs, and let callbacks process the results.
        for rpc in rpcs:
            rpc.wait()

        for cat,item in temp.iteritems():
            obj['googlevideos'].append(item)
        #http://search.lib.virginia.edu/catalog.json?f%5Bformat_facet%5D%5B%5D=Online&f%5Bformat_facet%5D%5B%5D=Video&f%5Bformat_facet%5D%5B%5D=Streaming+Video&facet.limit=500
        out = json.dumps(obj)
        #http://search.lib.virginia.edu/catalog.json?f%5Bformat_facet%5D%5B%5D=Online&f%5Bformat_facet%5D%5B%5D=Video&f%5Bformat_facet%5D%5B%5D=Streaming+Video&facet.limit=500
        self.response.out.write(out)

app = webapp2.WSGIApplication([  
    ('/tvquery', TVQuery)
], debug=False)
