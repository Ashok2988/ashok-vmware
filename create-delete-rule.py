"""
Author: ashokb@vmware.com
"""
import time
import requests
import json
import argparse
import getpass
from requests.exceptions import HTTPError
requests.packages.urllib3.disable_warnings()

class TagUpdate(object):
 def __init__(self,nm,nu,np,prefix):
    self.nm=nm
    self.nu=nu
    self.np=np
    self.auth = (nu, np)
    self.headers={'content-type': 'application/json'}
    self.ver=False
    self.authenticate()
    self.prefix=prefix
    self.id=[]
    self.count=1
 def authenticate(self):
   url="https://%s/api/v1/transport-zones" % (self.nm)
   resp=requests.get(url, auth=self.auth, headers=self.headers, verify=False)
   if not resp.ok:
      print("Auth failed, Please check creds")
   else:
      self.ver=True



 def create_rule(self,sec):
      d= {
          "destinations" : [ {
           "target_id" : "349cd367-7767-4c40-8a29-bde74022909a",
      "target_display_name" : "aa",
      "target_type" : "NSGroup",
      "is_valid" : True
        } ],
      "sources" : [ {
      "target_id" : "349cd367-7767-4c40-8a29-bde74022909a",
      "target_display_name" : "aa",
      "target_type" : "NSGroup",
      "is_valid" : True
       } ],
      "ip_protocol": "IPV4",
      "logged": False,
      "action": "ALLOW",



      "disabled": False,
      "direction": "IN_OUT",
       "display_name": "crud"
        }
      url="https://%s/api/v1/firewall/sections/%s/rules" % (self.nm,sec)

      resp=requests.post(url, auth=self.auth, headers=self.headers,data=json.dumps(d),verify=False)
      resp=(resp.json())
      self.id.append(resp['id'])

 def delete_rule(self,sec):
     while self.id:
        url="https://%s/api/v1/firewall/sections/%s/rules/%s" % (self.nm,sec,self.id.pop())
        resp=requests.delete(url, auth=self.auth, headers=self.headers,verify=False)
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
    parser.add_argument('--prefix',
                        help='vm prefix',
                         default=False,required=False)
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
    obj=TagUpdate(nm,nu,np,args.prefix)
    tago=True
    if  obj.ver:

       while True:
          if not obj.id:
             print("creating rule iter %d" %obj.count)
             for i in range(5):
                obj.create_rule("976a05d4-d302-4fd0-b0b1-d22e43af2da1")
          else:
             print("deleting rule iter %d" %obj.count)

             obj.delete_rule("976a05d4-d302-4fd0-b0b1-d22e43af2da1")
             obj.count+=1
          time.sleep(200)
