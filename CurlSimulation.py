def fire_post_request(http, data):
    import requests
    r = requests.post(http, data=data)
    if r.status_code == 200:
        return r.text
    else:
        print("Error "+str(r.status_code)+" reason:"+r.reason)
        return None