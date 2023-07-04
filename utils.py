import requests
import json

def tag_service:
    url = "https://%s/policy/api/v1/infra/services/%s" % (self.nm, ser)
            resp=requests.get(url, auth=self.auth, headers=self.headers, verify=False)
            payload=json.loads(resp.content)
            if 'tags' in payload.keys():
                if payload['tags'][0]['scope']=='v_origin':
                    payload['tags'][0]['scope']=scope
                    payload['tags'][0]['tag']=tag
                    resp = requests.patch(url, auth=self.auth, headers=self.headers, data=json.dumps(payload), verify=False)
                    if resp.ok:
                       print("tag update ok for service %s" %ser)
                    else:
                        print("tag update failed for service %s" %ser)
