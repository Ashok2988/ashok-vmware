"""
Author: ashokb@vmware.com
"""
import time
import requests
import json
import argparse
import getpass
import ipaddress
requests.packages.urllib3.disable_warnings()

class GrpSearch(object):
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

 def find_grp_by_ip(self,ip):
       url="https://%s/policy/api/v1/infra/ip-address-group-associations?ip_address=%s&enforcement_point_path=/infra/sites/default/enforcement-points/default"  % (self.nm,ip)
       resp = requests.get(url, auth=self.auth, headers=self.headers,verify=False)
       newpayload=(resp.json())
       for grp in newpayload['results']:
              print(grp['target_display_name'] )

def get_parse_arguments():
    parser = argparse.ArgumentParser(description='Find IP group membership')
    parser.add_argument('--nsxip',
                        help='nsx manager ip',
                        required=True, default=False)
    parser.add_argument('--nsxuser',
                        help='nsx username',
                        required=True, default=False)
    parser.add_argument('--nsxpwd',
                        help='nsx password',
                         default=False),
    parser.add_argument('--ip',
                   help='ip',
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
    #ecid = args.ecid
    #t1c = int(args.t1c)
    obj=GrpSearch(nm,nu,np)
    if  obj.ver:
       obj.find_grp_by_ip(args.ip)
