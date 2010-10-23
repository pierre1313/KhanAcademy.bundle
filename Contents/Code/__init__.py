from collections import deque

import re

####################################################################################################

VIDEO_PREFIX = "/video/khanacademy"

NAME = L('Title')

ART           = 'art-default.jpg'
ICON          = 'icon-default.png'

BASE          = "http://www.khanacademy.org"

# YouTube
YT_VIDEO_PAGE              = 'http://www.youtube.com/watch?v=%s'
YT_GET_VIDEO_URL           = 'http://www.youtube.com/get_video?video_id=%s&t=%s&fmt=%d&asv=3'
YT_VIDEO_FORMATS           = ['Standard', 'Medium', 'High', '720p', '1080p']
YT_FMT                     = [34, 18, 35, 22, 37]

####################################################################################################

def Start():

    Plugin.AddPrefixHandler(VIDEO_PREFIX, VideoMainMenu, L('Title'), ICON, ART)

    Plugin.AddViewGroup("InfoList", viewMode="InfoList", mediaType="items")
    Plugin.AddViewGroup("List", viewMode="List", mediaType="items")

    MediaContainer.art = R(ART)
    MediaContainer.title1 = NAME
    DirectoryItem.thumb = R(ICON)
    
    HTTP.CacheTime = 3600

def VideoMainMenu():

    dir = MediaContainer(viewGroup="List")

    dir.Append(Function(DirectoryItem(ByCategory,"Browse By Category...",thumb=R(ICON),art=R(ART))))
    dir.Append(Function(DirectoryItem(AllCategories,"All Categories",thumb=R(ICON),art=R(ART))))
    dir.Append(Function(InputDirectoryItem(ParseSearchResults,"Search ...","Search",thumb=R("search.png"),art=R(ART))))

    return dir

def ByCategory(sender, Menu = None ):

    dir = MediaContainer(viewGroup="List")

    if Menu == None:
      Menu = HTML.ElementFromURL('http://www.khanacademy.org/').xpath("//ul[@class='menu']")[0]
    else:
      Menu = HTML.ElementFromString(Menu)

    queue = deque([Menu])
    el = queue.popleft() 
    queue.extend(el) 
    while queue:
      el = queue.popleft()
      if (el.tag == 'li'):
        queue.extend(el)
      else:
        if (el.tag == 'a'):
          if (el.getnext() == None):
            if el.get('href').find('#') >= 0:
              dir.Append(Function(DirectoryItem(Submenu, el.text, thumb=R(ICON), art=R(ART)), category = String.Unquote(el.get('href').replace('#',''))))
            else:
              dir.Append(Function(DirectoryItem(Submenu, el.text, thumb=R(ICON), art=R(ART)), category = String.Unquote(el.get('href')),TestPrep = True))
          else:
            serialized = ''
            els = el
            for e in els.getnext().iterchildren():
              serialized = serialized + (HTML.StringFromElement(e)).strip()
            
            dir.Append(Function(DirectoryItem(ByCategory, el.text, thumb=R(ICON), art=R(ART)), Menu = str(serialized)))

    return dir


def AllCategories(sender ):

    dir = MediaContainer(viewGroup="List")

    Categories = HTML.ElementFromURL('http://www.khanacademy.org/').xpath("//h2[@class='playlist-heading']")

    for cat in Categories:
      dir.Append(Function(DirectoryItem(Submenu,cat.text,thumb=R(ICON),art=R(ART)),category = cat.text))

    return dir


def ParseSearchResults(sender, query=None):

    dir = MediaContainer(viewGroup="InfoList")

    results = HTML.ElementFromURL('http://www.khanacademy.org/search?page_search_query='+query).xpath("//section[@class='videos']//dt/a")

    if results == []:
        return MessageContainer('No Results','No video file could be found for the following query: '+query)

    for video in results:
      dir.Append(Function(VideoItem(PlayVideo,video.text,thumb=R(ICON),art=R(ART)),link = video.get("href")))

    return dir

def GetSummary(sender,link):
    try:
      summary = HTML.ElementFromURL(BASE+link).xpath("//nav[@class='breadcrumbs_nav']")[0].text
    except:
      summary = ""
    return summary

def Submenu(sender, category, TestPrep = False):
    dir = MediaContainer(viewGroup="List")

    if TestPrep == False :
      html = HTTP.Request('http://www.khanacademy.org/').content.replace('></A>','>').replace('<div class="clear"></div>','</A>')
      videolist = HTML.ElementFromString(html).xpath("//a[@name='"+category+"']/ol//a")
    else:
      html = HTTP.Request('http://www.khanacademy.org'+category).content
      if category == '/gmat':
        videolist = HTML.ElementFromString(html).xpath("//center/table[@cellpadding=0]//a[@href!='#']")
      else:
        videolist = HTML.ElementFromString(html).xpath("//div[@id='accordion']//a[@href!='#']")
      
    for video in videolist:
      dir.Append(Function(VideoItem(PlayVideo,video.text,thumb=R(ICON),art=R(ART)),link = video.get("href")))
                 
    return dir

def GetYouTubeVideo(video_id):
  yt_page = HTTP.Request(YT_VIDEO_PAGE % (video_id), cacheTime=1).content

  t = re.findall('&t=([^&]+)', yt_page)[0]
  fmt_list = re.findall('&fmt_list=([^&]+)', yt_page)[0]
  fmt_list = String.Unquote(fmt_list, usePlus=False)
  fmts = re.findall('([0-9]+)[^,]*', fmt_list)

  index = YT_VIDEO_FORMATS.index( Prefs.Get('ytfmt') )
  if YT_FMT[index] in fmts:
    fmt = YT_FMT[index]
  else:
    for i in reversed( range(0, index+1) ):
      if str(YT_FMT[i]) in fmts:
        fmt = YT_FMT[i]
        break
      else:
        fmt = 5

  url = YT_GET_VIDEO_URL % (video_id, t, fmt)
  return url

def PlayVideo(sender,link):
    try:
      ytid = HTML.ElementFromURL(BASE+link).xpath("//option[@selected]")[0].get("value")
      url = GetYouTubeVideo(ytid)
    except:
      url = "http://www.archive.org/download/KhanAcademy_"+link[link.find("playlist=")+9:].replace("%20",'')+"/"+link[link.find("/video/")+7:link.find("?")]+".flv"

    return Redirect(url)

  
