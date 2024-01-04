"""
Author: ashokb@vmware.com
"""
import time
import requests
import json
import argparse
import getpass
import random
from requests.exceptions import HTTPError
requests.packages.urllib3.disable_warnings()

class TagUpdate(object):
 def __init__(self,nm,nu,np):
    self.nm=nm
    self.nu=nu
    self.np=np
    self.auth = (nu, np)
    self.headers={'content-type': 'application/json'}
    self.ver=False
    self.authenticate()

 def authenticate(self):
   url="https://%s/api/v1/transport-zones" % (self.nm)
   resp=requests.get(url, auth=self.auth, headers=self.headers, verify=False)
   if not resp.ok:
      print("Auth failed, Please check creds")
   else:
      self.ver=True



 def update_rule(self,data):
      for r in data:
         url="https://%s/api/v1/firewall/sections/%s/rules/%s" % (self.nm,r['section_id'],r['id'])

         resp=requests.get(url, auth=self.auth, headers=self.headers,verify=False)
         d=(resp.json())
         ind=-1
         s=d['services']
         breaker=False
         for i,j in enumerate(s):
             if 'target_display_name' in j:
               if j['target_display_name']=='HTTP':
                  ind=i
                  breaker=True
                  break
         else:
            s.append({'target_id': '4be6b03c-e190-4011-ad7c-b01cb59845b6', 'target_display_name': 'HTTP', 'target_type': 'NSService', 'is_valid': True})
#         if breaker:
#            del s[ind]
         d['services']=s
         resp=requests.put(url, auth=self.auth, headers=self.headers,data=json.dumps(d),verify=False)
         print(resp.text)






def get_parse_arguments():
    parser = argparse.ArgumentParser(description='Tag update script')
    parser.add_argument('--nsxip',
                        help='nsx manager ip',
                        required=True, default=False)
    parser.add_argument('--nsxuser',
                        help='nsx username',
                        required=True, default=False)
    parser.add_argument('--nsxpwd',
                        help='nsx password',
                         default=False),
    parser.add_argument('--n',
                         help='number of rule to update',
                         default=False)
    return parser.parse_args()


if __name__ == '__main__':
    args=get_parse_arguments()
    if not args.nsxpwd:
       nsxpwd = getpass.getpass("NSX Manager password: ")
    else:
       nsxpwd=args.nsxpwd
    nm = args.nsxip
    nu = args.nsxuser
    np = nsxpwd
    obj=TagUpdate(nm,nu,np)
    tago=True
    if  obj.ver:


         with open('rules.json', 'r') as f:
#               c=(json.load(f))
               c=[i for i in json.load(f)]
               data=[]
               for i in range(int(args.n)):

                   data.append(random.choice(c))

               obj.update_rule(data)
