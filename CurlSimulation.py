def fire_post_request(http, data):
    import requests
    import os
    os.environ['NO_PROXY'] = '127.0.0.1'
    if not (http.startswith('http://') or http.startswith('https://')):
        http = 'http://' + http
    r = requests.post(http, files=data)
    if r.status_code == 200:
        return r.text
    else:
        print("Error "+str(r.status_code)+" reason:"+r.reason)
        return None