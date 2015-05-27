usage:
from api import okc\_api

api = okc\_api(username, password)

supports:
get\_inbox(?number of messages) - returns a list of messages (number of messages optional; defaults to all) with recipient, timestamp and thread\_id

read\_message(thread\_id) - returns a list of the conversation with username, message and timestamp

get\_profile(username) - returns the details of the user; main keys: info, details, essays, percentages; each has subkeys as well.

compose(username, message) - sends a message; does not return any value (currently). sadly, no thread\_id is returned

SOON:
searching