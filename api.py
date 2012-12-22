import urllib, urllib2, httplib
from datetime import datetime
from BeautifulSoup import BeautifulSoup, NavigableString

class okc_api:
  base_url = 'https://www.okcupid.com'

  def __init__(self, username, password):
    self.username = username
    opener = urllib2.build_opener(urllib2.HTTPCookieProcessor())
    urllib2.install_opener(opener)
    params = urllib.urlencode(dict(username=username, password=password))
    f = opener.open(self.base_url + '/login', params)
    f.close()

  def __request_read(self, url):
    return urllib2.urlopen(url).read()

  def __soupify(self, page):
    m = {'&gt;': '>', '&lt;': '<'}
    for k in m:
      page = page.replace(k, m[k])
    return BeautifulSoup(page)

  def __read_messages(self, index, page):
    f = self.__request_read(self.base_url + '/messages?folder=' + str(index) + '&low=' + str(page * 30 + 1))
    return self.__soupify(f)

  def get_inbox(self, num_messages=-1):
    message_list = []
    page = 0
    while (True):
      soup = self.__read_messages(1, page)
      messages = soup.find('ul', {'id': 'messages'}).findAll('li')
      for message in messages:
        recipient = str(message.find('a', {'class': 'subject'}).contents[0])
        timestamp = datetime.strptime(message.find('span', {'class': 'fancydate'}).contents[0], "%b %d, %Y")
        thread_id = str(message.find('input', {'type': 'checkbox'})['value'])
        message_list.append({'recipient': recipient, 'timestamp': timestamp, 'thread_id': thread_id})
        if len(message_list) == num_messages:
          return message_list
      if len(messages) < 30:
        break
      page += 1
    return message_list

  def __read_messages_readmsg(self, thread_id):
    f = self.__request_read(self.base_url + '/messages?readmsg=true&threadid=' + str(thread_id))
    return self.__soupify(f)

  def read_message(self, thread_id):
    message_thread = []
    soup = self.__read_messages_readmsg(thread_id)
    soup = soup.find('ul', {'id': 'thread'})
    users = soup.findAll('a', {'class': 'photo'})
    messages = soup.findAll('div', {'class': 'message_body'})
    dates = soup.findAll('span', {'class': 'fancydate'})
    zipped = zip(users, messages, dates)
    for message in zipped:
      user = str(message[0]['title'])
      msg = str(message[1].contents[0])
      date = datetime.strptime(message[2].contents[0], "%b %d, %Y &ndash; %I:%M%p")
      message_thread.append({'username': user, 'message': msg, 'timestamp': date})
    return message_thread

  def __read_profile(self, username):
    f = self.__request_read(self.base_url + "/profile/" + str(username))
    return self.__soupify(f)

  def __strip(self, string):
    string = str(string).replace('\xe2\x80\x99', '\'')
    return string.lstrip().rstrip()

  def __find(self, soup, attribute, key, mapping = {}):
    details = self.__strip(soup.find(attribute, {'id': key}).contents[0])
    mapping['&mdash;'] = '-'
    mapping['&ndash;'] = '-'
    mapping['&rsquo;'] = '\''
    for k in mapping:
      details = details.replace(k, mapping[k])
    return details

  def __parse_my_details(self, soup, key, mapping = {}):
    return self.__find(soup, 'span', key, mapping)

  def __parse_details(self, soup, key, mapping = {}):
    """given a profile_detail soup, returns the ajax_(key) using replace on the mappings"""
    return self.__find(soup, 'dd', key, mapping)

  def __get_info(self, soup):
    userinfo = soup.find('div', {'class': 'userinfo'})
    if userinfo == None:
      age = self.__parse_my_details(soup, 'ajax_age')
      gender = self.__parse_my_details(soup, 'ajax_gender')
      orientation = self.__parse_my_details(soup, 'ajax_orientation')
      status = self.__parse_my_details(soup, 'ajax_status')
      location = self.__parse_my_details(soup, 'ajax_location')
    else:
      info = userinfo.find('p', {'class': 'info'}).contents[0].split('/')
      age = self.__strip(info[0])
      gender = self.__strip(info[1])
      orientation = self.__strip(info[2])
      status = self.__strip(info[3])
      location = self.__strip(info[4])
    info = {'age': age, 'gender': gender, 'orientation': orientation, 'status': status, 'location': location}
    return info

  def __get_details(self, soup):
    details = soup.find('div', {'id': 'skinny_wrap'})
    profile_details = details.find('div', {'id': 'profile_details'})
    online = str(profile_details.find('dl').find('dd').contents[0].lstrip().rstrip())
    if online == "Online now!":
      pass
    else:
      pass
    ethnicity = self.__parse_details(profile_details, 'ajax_ethnicities')
    height = self.__parse_details(profile_details, 'ajax_height', {'&prime;': '\'', '&Prime;': '\"'})
    body_type = self.__parse_details(profile_details, 'ajax_bodytype')
    diet = self.__parse_details(profile_details, 'ajax_diet')
    smokes = self.__parse_details(profile_details, 'ajax_smoking')
    drinks = self.__parse_details(profile_details, 'ajax_drinking')
    drugs = self.__parse_details(profile_details, 'ajax_drugs')
    religion = self.__parse_details(profile_details, 'ajax_religion')
    education = self.__parse_details(profile_details, 'ajax_education')
    job = self.__parse_details(profile_details, 'ajax_job')
    income = self.__parse_details(profile_details, 'ajax_income')
    children = self.__parse_details(profile_details, 'ajax_children')
    pets = self.__parse_details(profile_details, 'ajax_pets')
    languages = self.__parse_details(profile_details, 'ajax_languages')
    profile_details = {'ethnicity': ethnicity, 'height': height, 'body_type': body_type, 'diet': diet, 'smokes': smokes,
                       'drinks': drinks, 'drugs': drugs, 'religion': religion, 'education': education, 'job': job,
                       'income': income, 'children': children, 'pets': pets, 'languages': languages}
    return profile_details

  def __get_essays(self, soup):
    essays = {}
    for i in range(1,10):
      essay = soup.find('div', {'id': 'essay_' + str(i)})
      if essay != None:
        title = self.__strip(essay.find('a', {'class': 'essay_title'}).contents[0])
        body = self.__strip(essay.find('div', {'id': 'essay_text_' + str(i)}).contents[0])
        essays[title] = body
    return essays

  def get_profile(self, username):
    profile = {}
    soup = self.__read_profile(username)
    info = self.__get_info(soup)
    details = self.__get_details(soup)
    essays = self.__get_essays(soup)
    profile['profile_info'] = info
    profile['profile_details'] = details
    profile['profile_essays'] = essays
    print profile

  def __read_compose(self):
    f = self.__request_read(self.base_url + '/messages?compose=1')
    return self.__soupify(f)

  def __get_auth_code(self):
    soup = self.__read_compose()
    return soup.find('input', {'name': 'authcode'})['value']

  def compose(self, username, message):
    auth_code = self.__get_auth_code()
    header = {'Content-type': 'application/x-www-form-urlencoded', 'Accept': 'text/html,application/xhtml+xml,application/xml'}
    data = {'contactflag': 'compose', 'r1': username, 'r2': 'none', 'body': message, 'sendmsg': 'SEND MESSAGE', 'authcode': auth_code}
    request = urllib2.Request('http://www.okcupid.com/mailbox', urllib.urlencode(data), header)
    response = urllib2.urlopen(request)
