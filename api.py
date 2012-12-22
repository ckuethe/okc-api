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

  def __read_messages(self, index, page):
    f = self.__request_read(self.base_url + '/messages?folder=' + str(index) + '&low=' + str(page * 30 + 1))
    return BeautifulSoup(f)

  def messages_incoming(self, num_messages=-1):
    page = 0
    message_list = []
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
    return BeautifulSoup(f)

  def readmsg(self, thread_id):
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

  def profile(self, username):
    pass

  def __read_compose(self):
    f = self.__request_read(self.base_url + '/messages?compose=1')
    return BeautifulSoup(f)

  def __get_auth_code(self):
    soup = self.__read_compose()
    return soup.find('input', {'name': 'authcode'})['value']

  def compose(self, username, message):
    auth_code = self.__get_auth_code()
    header = {'Content-type': 'application/x-www-form-urlencoded', 'Accept': 'text/html,application/xhtml+xml,application/xml'}
    data = {'contactflag': 'compose', 'r1': username, 'r2': 'none', 'body': message, 'sendmsg': 'SEND MESSAGE', 'authcode': auth_code}
    request = urllib2.Request('http://www.okcupid.com/mailbox', urllib.urlencode(data), header)
    response = urllib2.urlopen(request)
